"""
File Service - Safe and fast file reading with Polars & Pandas
Supports CSV, Excel (.xlsx, .xls), and Parquet (.parquet) formats.
"""

import os
import io
import csv
import logging
import pandas as pd
import numpy as np
import polars as pl
import pyarrow

logger = logging.getLogger(__name__)


def _deduplicate_columns(columns):
    """Normalizes BOM/whitespace, replaces blank/Unnamed headers, and guarantees unique column names."""
    cleaned_cols = []
    seen_counts = {}
    used_names = set()
    for i, col in enumerate(columns):
        col_str = str(col).replace("\ufeff", "").strip()
        if not col_str or col_str.startswith("Unnamed:") or col_str.lower() == "nan":
            col_str = f"Sütun_{i + 1}"
        base_name = col_str
        if base_name in used_names:
            idx = seen_counts.get(base_name, 0) + 1
            while f"{base_name}_{idx}" in used_names:
                idx += 1
            seen_counts[base_name] = idx
            col_str = f"{base_name}_{idx}"
        else:
            seen_counts[base_name] = 0
        used_names.add(col_str)
        cleaned_cols.append(col_str)
    return cleaned_cols


def clean_dataframe(df):
    """
    Cleans a pandas DataFrame:
    - Removes completely empty rows and columns.
    - Detects header offset if headers are trapped inside row values, and re-infers column dtypes.
    - Strips whitespace and BOM characters from column names.
    - Fixes unnamed (Unnamed:) or blank column names as 'Sütun_X'.
    - Deduplicates column names without collision.
    - Replaces Excel formula error strings (#VALUE!, #DIV/0!, etc.) with NaN (<300k rows).
    """
    if df is None or df.empty:
        return df

    # 1. Drop completely empty rows and columns
    df = df.dropna(how="all", axis=0).dropna(how="all", axis=1)
    if df.empty:
        return df

    # 2. Convert Excel formula error strings to NaN for object/string columns
    excel_error_strings = {
        "#VALUE!",
        "#REF!",
        "#DIV/0!",
        "#NAME?",
        "#NUM!",
        "#NULL!",
        "#N/A",
        "#N/A N/A",
    }
    str_cols = df.select_dtypes(include=["object", "string"]).columns
    if len(str_cols) > 0 and len(df) < 300000:
        df[str_cols] = df[str_cols].replace(list(excel_error_strings), np.nan)

    # 3. Detect header offset (if header was pushed into rows)
    cols = [str(c).replace("\ufeff", "").strip() for c in df.columns]
    unnamed_count = sum(
        1 for c in cols if not c or c.startswith("Unnamed:") or c.lower() == "nan"
    )

    if unnamed_count >= len(cols) / 2 and len(df) > 1:
        header_candidate_idx = None
        for r_idx in range(min(10, len(df) - 1)):
            row_vals = df.iloc[r_idx]
            valid_headers = []
            text_header_count = 0
            for v in row_vals:
                if pd.notna(v):
                    s_v = str(v).strip()
                    if (
                        s_v != ""
                        and not s_v.lower().startswith("unnamed:")
                        and s_v.lower() != "nan"
                    ):
                        valid_headers.append(s_v)
                        if (
                            not s_v.replace(".", "", 1)
                            .replace(",", "", 1)
                            .lstrip("-+")
                            .isdigit()
                        ):
                            text_header_count += 1
            if len(valid_headers) >= max(
                2, len(cols) * 0.5
            ) and text_header_count >= max(1, len(valid_headers) * 0.5):
                header_candidate_idx = r_idx
                break

        if header_candidate_idx is not None:
            new_cols = []
            header_row = df.iloc[header_candidate_idx]
            for i, val in enumerate(header_row):
                val_str = (
                    str(val).replace("\ufeff", "").strip() if pd.notna(val) else ""
                )
                if val_str and val_str.lower() != "nan":
                    new_cols.append(val_str)
                else:
                    new_cols.append(f"Sütun_{i + 1}")
            df = df.iloc[header_candidate_idx + 1 :].copy()
            df.columns = new_cols
            # Re-infer numeric types for columns that became object only because the header row was inside data
            for c in df.columns:
                if df[c].dtype == object:
                    non_null = df[c].dropna()
                    if len(non_null) > 0:
                        converted = pd.to_numeric(non_null, errors="coerce")
                        if converted.notna().sum() == len(non_null):
                            df[c] = pd.to_numeric(df[c], errors="coerce")

    # 4. Normalize and deduplicate column names
    df.columns = _deduplicate_columns(df.columns)

    # 5. Re-check for empty columns after column normalization
    df = df.dropna(how="all", axis=1)
    df = df.reset_index(drop=True)
    return df


def read_csv_safely(file_input):
    """
    Safely reads CSV files with auto-encoding detection (utf-8, utf-8-sig, windows-1254, iso-8859-9, latin1)
    and delimiter detection (;, ,, \\t, |). Uses multi-core Polars as primary engine with Pandas fallback.
    Preserves dirty string columns so Data Healer can inspect and repair them.
    """
    if isinstance(file_input, (str, os.PathLike)):
        with open(file_input, "rb") as f:
            raw_bytes = f.read()
    elif hasattr(file_input, "read"):
        raw_bytes = file_input.read()
    elif isinstance(file_input, bytes):
        raw_bytes = file_input
    else:
        raise ValueError("Geçersiz dosya nesnesi.")

    if not raw_bytes or not raw_bytes.strip():
        raise pd.errors.EmptyDataError("CSV dosyası tamamen boş.")

    # 1. Encoding sequence: BOM detection first
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        encodings = ["utf-8-sig", "utf-8", "windows-1254", "iso-8859-9", "latin1"]
    else:
        encodings = ["utf-8", "utf-8-sig", "windows-1254", "iso-8859-9", "latin1"]

    decoded_text = None
    successful_enc = None
    for enc in encodings:
        try:
            text = raw_bytes.decode(enc)
            if "\x00" in text:
                continue
            decoded_text = text
            successful_enc = enc
            break
        except UnicodeDecodeError:
            continue

    if decoded_text is None:
        raise UnicodeDecodeError(
            "unknown",
            raw_bytes,
            0,
            1,
            f"Dosya karakter kodlaması çözülemedi. Denediğimiz kodlamalar: {', '.join(encodings)}",
        )

    # Free raw_bytes immediately to reduce peak RAM usage on large uploads
    del raw_bytes
    logger.info(f"CSV başarıyla çözümlendi. Kodlama: {successful_enc}")

    # 2. Delimiter detection from first 25 lines without splitting entire multi-million line string
    sample_lines = []
    for line in io.StringIO(decoded_text):
        if line.strip():
            sample_lines.append(line.rstrip("\r\n"))
        if len(sample_lines) >= 25:
            break

    detected_delim = None
    if sample_lines:
        header_line = sample_lines[0]
        counts = {d: header_line.count(d) for d in [";", ",", "\t", "|"]}
        if any(c > 0 for c in counts.values()):
            try:
                sniffer = csv.Sniffer()
                detected_delim = sniffer.sniff(
                    "\n".join(sample_lines), delimiters=";,\t|"
                ).delimiter
            except Exception:
                detected_delim = max(counts, key=counts.get)
        else:
            detected_delim = ","

    # 3. Polars fast multi-core engine (without ignore_errors=True so dirty numeric strings are preserved as Utf8 for Data Healer)
    df = None
    errors = []

    if detected_delim:
        try:
            pldf = pl.read_csv(
                io.StringIO(decoded_text),
                separator=detected_delim,
                infer_schema_length=10000,
                ignore_errors=False,
            )
            df = pldf.to_pandas()
            del pldf
            logger.info("CSV Polars hızlı motoru ile ayrıştırıldı.")
        except Exception as e_pl:
            logger.debug(
                f"Polars strict CSV fallback (karma tipli sütunlar korunuyor): {e_pl}"
            )
            try:
                df = pd.read_csv(
                    io.StringIO(decoded_text), sep=detected_delim, low_memory=False
                )
            except Exception as e_pd:
                try:
                    df = pd.read_csv(
                        io.StringIO(decoded_text), sep=detected_delim, engine="python"
                    )
                except Exception as e:
                    errors.append(e)

    if df is None:
        try:
            df = pd.read_csv(io.StringIO(decoded_text), sep=None, engine="python")
        except Exception as e:
            errors.append(e)

    if df is None:
        for fallback_sep in [";", ",", "\t"]:
            try:
                df = pd.read_csv(
                    io.StringIO(decoded_text), sep=fallback_sep, low_memory=False
                )
                break
            except Exception as e:
                errors.append(e)

    del decoded_text

    if df is None:
        raise ValueError(
            f"CSV içeriği tablolanamadı: {errors[-1] if errors else 'Bilinmeyen hata'}"
        )

    return clean_dataframe(df)


def read_excel_safely(file_input):
    """
    Reads .xlsx and .xls files using pd.read_excel(sheet_name=None),
    cleans all sheets, and returns active DataFrame, sheets dictionary, sheet list, and active sheet name.
    """
    if isinstance(file_input, (str, os.PathLike)):
        with open(file_input, "rb") as f:
            file_bytes = f.read()
    elif hasattr(file_input, "read"):
        file_bytes = file_input.read()
    elif isinstance(file_input, bytes):
        file_bytes = file_input
    else:
        raise ValueError("Geçersiz dosya nesnesi.")

    if not file_bytes:
        raise pd.errors.EmptyDataError("Excel dosyası tamamen boş.")

    try:
        sheets_dict = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None)
    except Exception as e:
        err_msg = str(e)
        logger.error(f"Excel okuma hatası: {err_msg}")
        if "xlrd" in err_msg.lower():
            raise ValueError(
                "Eski Excel (.xls) dosyalarını okumak için 'xlrd' kütüphanesi gereklidir. Lütfen dosyanızı .xlsx formatına dönüştürüp yükleyin."
            )
        elif "zip" in err_msg.lower() or "corrupt" in err_msg.lower():
            raise ValueError("Excel dosyası bozuk veya geçersiz bir formatta.")
        else:
            raise ValueError(f"Excel dosyası açılamadı: {err_msg}")

    if not sheets_dict:
        raise ValueError("Excel dosyasında herhangi bir çalışma sayfası bulunamadı.")

    cleaned_sheets = {}
    valid_sheet_names = []
    for s_name, s_df in sheets_dict.items():
        cleaned_df = clean_dataframe(s_df)
        cleaned_sheets[s_name] = cleaned_df
        valid_sheet_names.append(s_name)

    active_sheet_name = valid_sheet_names[0]
    for s_name in valid_sheet_names:
        if not cleaned_sheets[s_name].empty and len(cleaned_sheets[s_name].columns) > 0:
            active_sheet_name = s_name
            break

    active_df = cleaned_sheets[active_sheet_name]
    if active_df.empty or len(active_df.columns) == 0:
        all_empty = all(d.empty or len(d.columns) == 0 for d in cleaned_sheets.values())
        if all_empty:
            raise ValueError(
                "Excel dosyasındaki tüm sayfalar boş veya geçerli veri içermiyor."
            )

    return active_df, cleaned_sheets, valid_sheet_names, active_sheet_name


def read_parquet_safely(file_input):
    """
    Reads Apache Parquet (.parquet) files using PyArrow / Polars multi-threaded engine,
    preserving dictionary-encoded columns as memory-efficient Pandas Categoricals
    (allowing 100M+ rows x 22 cols to fit in ~6.3 GB RAM without duplicating buffers).
    """
    import pyarrow.parquet as pq

    source = file_input
    if not isinstance(file_input, (str, os.PathLike)):
        if hasattr(file_input, "stream") and hasattr(file_input.stream, "seek"):
            file_input.stream.seek(0)
            source = file_input.stream
        elif hasattr(file_input, "seek") and hasattr(file_input, "read"):
            file_input.seek(0)
            source = file_input
        elif hasattr(file_input, "read"):
            file_bytes = file_input.read()
            if not file_bytes:
                raise pd.errors.EmptyDataError("Parquet dosyası tamamen boş.")
            source = io.BytesIO(file_bytes)
        elif isinstance(file_input, bytes):
            if not file_input:
                raise pd.errors.EmptyDataError("Parquet dosyası tamamen boş.")
            source = io.BytesIO(file_input)
        else:
            raise ValueError("Geçersiz dosya nesnesi.")

    try:
        pa_table = pq.read_table(source, use_threads=True)
        df = pa_table.to_pandas(split_blocks=True, self_destruct=True)
        del pa_table
        logger.info(
            f"Parquet dosyası PyArrow Zero-Copy motoru ile okundu: {len(df)} satır, {len(df.columns)} sütun"
        )
    except Exception as e_pa:
        logger.warning(f"PyArrow doğrudan parquet okuma fallback (Polars deneniyor): {e_pa}")
        try:
            if hasattr(source, "seek"):
                source.seek(0)
            pldf = pl.read_parquet(source)
            df = pldf.to_pandas()
            del pldf
            logger.info(
                f"Parquet dosyası Polars ile okundu: {len(df)} satır, {len(df.columns)} sütun"
            )
        except Exception as e_pl:
            raise ValueError(f"Parquet dosyası açılamadı: {e_pl}")

    df.columns = _deduplicate_columns(df.columns)
    return df

