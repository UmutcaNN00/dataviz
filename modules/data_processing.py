import pandas as pd
import re


def clean_currency_and_numbers(val):
    if isinstance(val, str):
        val = re.sub(r'[^\d.,-]', '', val)
        if '.' in val and ',' in val:
            val = val.replace('.', '').replace(',', '.')
        elif ',' in val and '.' not in val:
            val = val.replace(',', '.')
    return val


def clean_data(df):
    df.columns = df.columns.str.strip()
    df.dropna(how='all', inplace=True)
    df.dropna(axis=1, how='all', inplace=True)

    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                df[col] = pd.to_datetime(df[col])
                continue
            except (ValueError, TypeError):
                pass

            cleaned_col = df[col].apply(clean_currency_and_numbers)
            try:
                df_numeric = pd.to_numeric(cleaned_col, errors='coerce')
                if df_numeric.notna().sum() / max(len(df_numeric), 1) > 0.7:
                    df[col] = df_numeric
            except Exception:
                pass

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(0)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            pass
        else:
            df[col] = df[col].fillna('Bilinmiyor')

    return df


def classify_columns(df):
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = df.select_dtypes(
        include=['object', 'datetime64', 'category']
    ).columns.tolist()
    return categorical_cols, numeric_cols


# ─── SINGLE-Y groupby (eski uyumluluk) ───────────────────────────────────────
def aggregate_data(df, x_col, y_col, agg_func):
    if not x_col:
        return df

    if not y_col or y_col in ('', 'Yok'):
        summary_df = df[x_col].value_counts(dropna=False).reset_index()
        summary_df.columns = [x_col, 'count']
    else:
        summary_df = (
            df.groupby(x_col, dropna=False, as_index=False)[y_col].agg(agg_func)
        )

    return summary_df


# ─── MULTI-Y groupby (yeni) ───────────────────────────────────────────────────
def aggregate_data_multi(df, x_col, y_cols, agg_func):
    """
    x_col    : str  – grup sütunu
    y_cols   : list – toplanacak sayısal sütunlar (boş → sadece sayım)
    agg_func : str  – 'sum' | 'mean' | 'count' | 'min' | 'max' | 'median'
    Döner    : dict – { x_col: [...], y1: [...], y2: [...], ... }
    """
    if not x_col:
        return {}

    if not y_cols:
        counts = df[x_col].value_counts(dropna=False).reset_index()
        counts.columns = [x_col, 'count']
        return {
            '__x__': counts[x_col].fillna('Boş Değer').astype(str).tolist(),
            'count': counts['count'].fillna(0).tolist()
        }

    func = agg_func if agg_func != 'median' else 'median'
    grouped = df.groupby(x_col, dropna=False, as_index=False)

    result = {}
    x_vals = None

    for y_col in y_cols:
        if y_col not in df.columns:
            continue
        agg_df = grouped[y_col].agg(func)
        if x_vals is None:
            x_vals = agg_df[x_col].fillna('Boş Değer').astype(str).tolist()
        result[y_col] = [round(v, 4) if isinstance(v, float) else v
                         for v in agg_df[y_col].fillna(0).tolist()]

    result['__x__'] = x_vals or []
    return result


# ─── RAW SAMPLE (Histogram / Box / Violin için) ───────────────────────────────
def get_raw_sample(df, columns, max_rows=5000):
    """
    Histogram, box, violin için ham değerleri örnekleyerek döner.
    columns : list[str]
    Döner   : dict { col: [val, ...] }
    """
    sample = df if len(df) <= max_rows else df.sample(max_rows, random_state=42)
    result = {}
    for col in columns:
        if col in df.columns:
            result[col] = sample[col].dropna().tolist()
    return result


# ─── KORELASYON MATRİSİ (Heatmap) ────────────────────────────────────────────
def get_correlation(df, columns):
    """
    Seçilen sayısal sütunlar arasındaki korelasyon matrisini döner.
    Döner : { 'labels': [...], 'matrix': [[...], ...] }
    """
    valid = [c for c in columns if c in df.columns and
             pd.api.types.is_numeric_dtype(df[c])]
    if len(valid) < 2:
        return {'labels': valid, 'matrix': []}

    corr = df[valid].corr().round(3)
    return {
        'labels': valid,
        'matrix': corr.values.tolist()
    }


# ─── İSTATİSTİKSEL ÖZET ──────────────────────────────────────────────────────
def get_statistics(df, columns):
    """
    Seçilen sayısal sütunlar için kapsamlı betimsel istatistik döner.
    Döner : { col: { mean, median, mode, std, var, min, max, q1, q3,
                     skewness, kurtosis, count, missing } }
    """
    result = {}
    for col in columns:
        if col not in df.columns:
            continue
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue

        s = df[col].dropna()
        if s.empty:
            continue

        modes = s.mode()
        result[col] = {
            'count':    int(s.count()),
            'missing':  int(df[col].isna().sum()),
            'mean':     _r(s.mean()),
            'median':   _r(s.median()),
            'mode':     _r(modes.iloc[0]) if not modes.empty else None,
            'std':      _r(s.std()),
            'variance': _r(s.var()),
            'min':      _r(s.min()),
            'max':      _r(s.max()),
            'q1':       _r(s.quantile(0.25)),
            'q3':       _r(s.quantile(0.75)),
            'iqr':      _r(s.quantile(0.75) - s.quantile(0.25)),
            'skewness': _r(s.skew()),
            'kurtosis': _r(s.kurtosis()),
            'range':    _r(s.max() - s.min()),
        }
    return result


def _r(val, decimals=4):
    """Güvenli yuvarlama yardımcısı."""
    try:
        return round(float(val), decimals)
    except Exception:
        return None
