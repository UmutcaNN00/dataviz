"""
Export Service - High-performance export streams for Parquet, Excel, and CSV formats.
"""

import io
import logging
import pandas as pd
import polars as pl

logger = logging.getLogger(__name__)


def export_dataframe(df, export_format='csv', file_name=None):
    """
    Exports a DataFrame into an in-memory BytesIO stream in Parquet, Excel, or CSV format.
    
    Args:
        df (pd.DataFrame): Data to export.
        export_format (str): 'csv', 'xlsx'/'excel', or 'parquet'.
        file_name (str, optional): Base name for the downloaded file.
        
    Returns:
        tuple (io.BytesIO, str, str): (buffer, mimetype, download_name)
    """
    if df is None or df.empty:
        raise ValueError("Dışa aktarılacak aktif veri seti bulunamadı veya boş.")

    output = io.BytesIO()
    fmt = str(export_format).lower().strip()
    base_name = file_name or 'Aktarilan_Veri'

    if fmt in ['xlsx', 'excel']:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Veri_Seti')
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        download_name = f"{base_name}.xlsx"

    elif fmt in ['parquet']:
        try:
            pl_df = pl.from_pandas(df)
            pl_df.write_parquet(output, compression='snappy')
        except Exception as e_pl:
            logger.warning(f"Polars parquet yazma hatası, pandas deneniyor: {e_pl}")
            df.to_parquet(output, engine='pyarrow', compression='snappy')
        mimetype = 'application/octet-stream'
        download_name = f"{base_name}.parquet"

    else:  # Default to CSV with UTF-8 BOM
        csv_str = df.to_csv(index=False, encoding='utf-8-sig')
        output.write(csv_str.encode('utf-8-sig'))
        mimetype = 'text/csv; charset=utf-8'
        download_name = f"{base_name}.csv"

    output.seek(0)
    return output, mimetype, download_name


def export_pivot_to_excel(active_df, rows, cols, values, agg_func='sum', file_name='Ozet_Pivot_Raporu'):
    """
    Generates an Excel workbook containing a formatted pivot table from active filtered data.
    
    Returns:
        tuple (io.BytesIO, str, str): (buffer, mimetype, download_name)
    """
    if active_df is None or active_df.empty:
        raise ValueError("Dışa aktarılacak veri bulunamadı.")

    valid_rows = [r for r in rows if r in active_df.columns]
    valid_cols = [c for c in cols if c in active_df.columns]
    valid_values = [v for v in values if v in active_df.columns and pd.api.types.is_numeric_dtype(active_df[v])]

    if not valid_rows and not valid_cols:
        raise ValueError("En az bir Satır veya Sütun boyutu seçilmelidir.")
    if not valid_values:
        raise ValueError("En az bir sayısal değer metriği seçilmelidir.")

    pt = pd.pivot_table(
        active_df,
        index=valid_rows if valid_rows else None,
        columns=valid_cols if valid_cols else None,
        values=valid_values,
        aggfunc=agg_func,
        fill_value=0,
        margins=True,
        margins_name='Genel Toplam'
    )

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pt.to_excel(writer, sheet_name='Ozet_Tablo_Pivot')
    output.seek(0)

    mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    download_name = f"{file_name}.xlsx"

    return output, mimetype, download_name
