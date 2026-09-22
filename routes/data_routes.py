"""
Data Routes Blueprint - Data Health, Anomaly Healing, Cleaning, Dataset Joins, and Calculated Columns
"""

import logging
import numpy as np
import pandas as pd
from flask import Blueprint, request, jsonify

from core.store import get_df, set_df
from services.file_service import (
    clean_dataframe,
    read_csv_safely,
    read_excel_safely,
    read_parquet_safely,
)
from services.data_healer import (
    detect_column_anomalies,
    repair_column_data,
    clean_missing_data,
)

logger = logging.getLogger(__name__)

data_bp = Blueprint('data', __name__)


@data_bp.route('/check_health', methods=['GET'])
def check_health():
    """Inspects dataset health: missing values, NaN count, and column type anomalies."""
    global_df = get_df(1)
    if global_df is None or len(global_df) == 0:
        return jsonify({'error': 'Aktif veri seti bulunamadı. Lütfen önce bir dosya yükleyin.'}), 400

    try:
        missing_count = int(global_df.isnull().sum().sum())
        missing_rows = int(global_df.isnull().any(axis=1).sum())
        anomalies = detect_column_anomalies(global_df)

        resp = jsonify({
            'success': True,
            'has_issues': missing_rows > 0 or len(anomalies) > 0,
            'missing_cells': missing_count,
            'missing_rows': missing_rows,
            'total_rows': len(global_df),
            'anomalies': anomalies,
            'has_anomalies': len(anomalies) > 0
        })
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return resp
    except Exception as e:
        logger.exception(f"check_health hatası: {e}")
        return jsonify({'error': f"Veri sağlığı kontrol edilirken bir hata oluştu: {str(e)}"}), 500


@data_bp.route('/repair_column_anomalies', methods=['POST'])
def repair_column_anomalies():
    """Executes smart repair or conversion on anomalous columns."""
    global_df = get_df(1)
    if global_df is None or global_df.empty:
        return jsonify({'error': 'Aktif veri seti bulunamadı.'}), 400

    data = request.get_json(silent=True) or {}
    target_column = data.get('column', '__all__')
    repair_mode = data.get('repair_mode', 'smart_heal')

    try:
        repaired_df, cols_to_repair = repair_column_data(
            global_df,
            target_column=target_column,
            repair_mode=repair_mode
        )
        set_df(repaired_df, 1)

        numeric_cols = repaired_df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = repaired_df.select_dtypes(include=['object', 'category', 'bool', 'string']).columns.tolist()
        remaining = detect_column_anomalies(repaired_df)

        return jsonify({
            'success': True,
            'repaired_columns': cols_to_repair,
            'repair_mode': repair_mode,
            'total_rows': len(repaired_df),
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols,
            'remaining_anomalies': remaining
        })
    except Exception as e:
        logger.error(f"Sütun onarma hatası: {e}")
        return jsonify({'error': f'Onarma işlemi sırasında hata: {str(e)}'}), 500


@data_bp.route('/clean_data', methods=['POST'])
def clean_data():
    """Cleans missing data via dropping or mean/median/zero/mode imputation."""
    global_df = get_df(1)
    if global_df is None:
        return jsonify({'error': 'Veri yok'}), 400

    data = request.get_json(silent=True) or {}
    action = data.get('action', 'drop')
    try:
        cleaned_df = clean_missing_data(global_df, action=action)
        set_df(cleaned_df, 1)

        numeric_cols = cleaned_df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = cleaned_df.select_dtypes(include=['object', 'category', 'bool', 'string']).columns.tolist()

        return jsonify({
            'success': True,
            'total_rows': len(cleaned_df),
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols
        })
    except Exception as e:
        logger.exception(f"clean_data hatası: {e}")
        return jsonify({'error': str(e)}), 500


@data_bp.route('/preview_second_file', methods=['POST'])
def preview_second_file():
    """Parses a second dataset file for key discovery and merge preparation."""
    global_df = get_df(1)
    if global_df is None:
        return jsonify({'error': 'Önce 1. dosyayı yükleyin'}), 400
    if 'file2' not in request.files:
        return jsonify({'error': '2. dosya bulunamadı'}), 400
    file2 = request.files['file2']
    if file2.filename == '':
        return jsonify({'error': 'Dosya seçilmedi'}), 400

    try:
        filename2 = file2.filename.lower()
        if filename2.endswith('.parquet'):
            df2 = read_parquet_safely(file2)
        elif filename2.endswith('.csv'):
            df2 = read_csv_safely(file2)
        elif filename2.endswith(('.xls', '.xlsx')):
            df2, _, _, _ = read_excel_safely(file2)
        else:
            return jsonify({'error': 'Desteklenmeyen dosya formatı. Lütfen .parquet, .csv veya .xlsx dosyası yükleyin.'}), 400

        df2.columns = [str(c).replace('\ufeff', '').strip() for c in df2.columns]
        set_df(df2, 2)

        cols1 = global_df.columns.tolist()
        cols2 = df2.columns.tolist()

        auto_key1 = None
        auto_key2 = None

        # 1. Exact match (case insensitive)
        for c1 in cols1:
            for c2 in cols2:
                if c1.lower() == c2.lower():
                    auto_key1 = c1
                    auto_key2 = c2
                    break
            if auto_key1:
                break

        # 2. Key words match
        if not auto_key1:
            for c1 in cols1:
                if any(w in c1.lower() for w in ['id', 'kod', 'no', 'numara', 'tc', 'key', 'sehir', 'bolge', 'tarih']):
                    for c2 in cols2:
                        if any(w in c2.lower() for w in ['id', 'kod', 'no', 'numara', 'tc', 'key', 'sehir', 'bolge', 'tarih']):
                            auto_key1 = c1
                            auto_key2 = c2
                            break
                    if auto_key1:
                        break

        return jsonify({
            'success': True,
            'file2_name': file2.filename,
            'file2_rows': len(df2),
            'cols1': cols1,
            'cols2': cols2,
            'auto_key1': auto_key1,
            'auto_key2': auto_key2
        })
    except Exception as e:
        logger.exception(f"preview_second_file hatası: {e}")
        return jsonify({'error': str(e)}), 500


@data_bp.route('/join_datasets', methods=['POST'])
@data_bp.route('/merge_datasets', methods=['POST'])
def join_datasets():
    """Merges the active dataset with a second dataset using specified keys and join type."""
    global_df = get_df(1)
    if global_df is None:
        return jsonify({'error': 'Önce 1. dosyayı yükleyin'}), 400

    df2 = None
    if 'file2' in request.files and request.files['file2'].filename != '':
        file2 = request.files['file2']
        filename2 = file2.filename.lower()
        try:
            if filename2.endswith('.parquet'):
                df2 = read_parquet_safely(file2)
            elif filename2.endswith('.csv'):
                df2 = read_csv_safely(file2)
            elif filename2.endswith(('.xls', '.xlsx')):
                df2, _, _, _ = read_excel_safely(file2)
            else:
                return jsonify({'error': 'Desteklenmeyen dosya formatı. Lütfen .parquet, .csv veya .xlsx dosyası yükleyin.'}), 400
        except Exception as e:
            return jsonify({'error': f'2. dosya okunamadı: {str(e)}'}), 400
    else:
        df2 = get_df(2)

    if df2 is None or df2.empty:
        return jsonify({'error': '2. dosya bulunamadı veya boş'}), 400

    req_json = request.get_json(silent=True) or {}
    key1 = request.form.get('key1') or req_json.get('key1')
    key2 = request.form.get('key2') or req_json.get('key2')
    join_type = request.form.get('join_type') or req_json.get('join_type', 'left')

    if not key1 or not key2:
        return jsonify({'error': 'Birleştirme anahtarları (ortak sütunlar) seçilmelidir.'}), 400

    df2.columns = [str(c).replace('\ufeff', '').strip() for c in df2.columns]

    if key1 not in global_df.columns:
        return jsonify({'error': f'1. tabloda "{key1}" sütunu bulunamadı'}), 400
    if key2 not in df2.columns:
        return jsonify({'error': f'2. tabloda "{key2}" sütunu bulunamadı'}), 400

    try:
        global_df_temp = global_df.copy()
        df2_temp = df2.copy()

        def normalize_merge_series(series):
            def _clean(val):
                if pd.isna(val):
                    return None
                s_val = str(val).strip()
                if s_val == '' or s_val.lower() in ['nan', 'none', 'null', '<na>']:
                    return None
                try:
                    f = float(s_val)
                    if f.is_integer():
                        return str(int(f))
                    return str(f)
                except (ValueError, TypeError):
                    return s_val
            return series.apply(_clean)

        k1_norm = normalize_merge_series(global_df_temp[key1])
        k2_norm = normalize_merge_series(df2_temp[key2])

        global_df_temp['_merge_key_'] = [v if v is not None else f'__null_left_{i}__' for i, v in enumerate(k1_norm)]
        df2_temp['_merge_key_'] = [v if v is not None else f'__null_right_{i}__' for i, v in enumerate(k2_norm)]

        merged = pd.merge(
            global_df_temp,
            df2_temp,
            on='_merge_key_',
            how=join_type,
            suffixes=('', '_2')
        )
        merged.drop(columns=['_merge_key_'], inplace=True)

        if key2 + '_2' in merged.columns:
            merged.drop(columns=[key2 + '_2'], inplace=True)

        old_cols = set(global_df.columns)
        new_cols = [c for c in merged.columns if c not in old_cols]

        global_df = merged
        set_df(global_df, 1)

        numeric_cols = global_df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = global_df.select_dtypes(include=['object', 'category', 'bool', 'string']).columns.tolist()

        return jsonify({
            'success': True,
            'total_rows': len(global_df),
            'total_cols': len(global_df.columns),
            'new_joined_columns': new_cols,
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols
        })
    except Exception as e:
        logger.exception(f"join_datasets hatası: {e}")
        return jsonify({'error': f'Birleştirme hatası: {str(e)}'}), 500


@data_bp.route('/create_calculated_column', methods=['POST'])
@data_bp.route('/add_calculated_column', methods=['POST'])
def create_calculated_column():
    """Generates a calculated column based on arithmetic operations between columns/scalars."""
    global_df = get_df(1)
    if global_df is None:
        return jsonify({'error': 'Veri yok'}), 400

    data = request.get_json(silent=True) or {}
    new_col = (data.get('new_col_name') or data.get('new_column_name') or '').strip()
    col1 = data.get('col1')
    op = data.get('op') or data.get('operator')
    col2 = data.get('col2')
    scalar = data.get('scalar')

    if not new_col:
        return jsonify({'error': 'Yeni sütun adı belirtilmelidir.'}), 400
    if col1 not in global_df.columns:
        return jsonify({'error': '1. sütun bulunamadı.'}), 400

    try:
        s1 = pd.to_numeric(global_df[col1], errors='coerce').fillna(0)

        if col2 and col2 in global_df.columns:
            s2 = pd.to_numeric(global_df[col2], errors='coerce').fillna(0)
        elif scalar is not None:
            s2 = float(scalar)
        else:
            return jsonify({'error': '2. değişken veya sayısal değer belirtilmelidir.'}), 400

        if op == '+':
            global_df[new_col] = s1 + s2
        elif op == '-':
            global_df[new_col] = s1 - s2
        elif op == '*':
            global_df[new_col] = s1 * s2
        elif op == '/':
            global_df[new_col] = np.where(s2 != 0, s1 / s2, 0)
            global_df[new_col] = pd.Series(global_df[new_col]).replace([np.inf, -np.inf], 0)
        else:
            return jsonify({'error': 'Geçersiz işlem operatörü.'}), 400

        set_df(global_df, 1)

        numeric_cols = global_df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = global_df.select_dtypes(include=['object', 'category', 'bool', 'string']).columns.tolist()

        return jsonify({
            'success': True,
            'new_column': new_col,
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols
        })
    except Exception as e:
        logger.exception(f"create_calculated_column hatası: {e}")
        return jsonify({'error': f'Hesaplama hatası: {str(e)}'}), 500
