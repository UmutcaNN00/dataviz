"""
Main Routes Blueprint - Landing Page, Studio, Health, and Sample Data
"""

import os
import logging
import numpy as np
import pandas as pd
from flask import Blueprint, render_template, jsonify

from core.config import BASE_DIR
from core.store import get_df, set_df, set_excel_data
from services.file_service import clean_dataframe, read_csv_safely, read_excel_safely

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)


@main_bp.route('/', methods=['GET'])
def index():
    """Renders the landing page."""
    return render_template('landing.html')


@main_bp.route('/analysis', methods=['GET'])
def analysis():
    """Renders the primary data analysis studio."""
    return render_template('analysis.html')


@main_bp.route('/a4-demo', methods=['GET'])
def a4_demo():
    """Renders the A4 report demo preview."""
    return render_template('a4_demo.html')


@main_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint indicating server and engine status."""
    return jsonify({'status': 'ok', 'service': 'DataViz', 'engine': 'Polars'}), 200


@main_bp.route('/load_sample', methods=['GET', 'POST'])
def load_sample():
    """Loads a demo sample dataset or generates a synthetic academic dataset."""
    try:
        sample_path = None
        candidates = ['ornek_veri_seti.xlsx', '1_Satis_Islemleri_Devasa.xlsx', 'test_satislar.csv', 'test.csv']
        
        for candidate in candidates:
            for p in [candidate, os.path.join(BASE_DIR, candidate)]:
                if os.path.exists(p):
                    sample_path = p
                    break
            if sample_path:
                break

        sheet_names = []
        active_sheet = None

        if sample_path and sample_path.endswith('.xlsx'):
            with open(sample_path, 'rb') as f:
                df, sheets_dict, sheet_names, active_sheet = read_excel_safely(f)
            set_df(df, 1)
            set_excel_data(sheets_dict, sheet_names)
        elif sample_path and sample_path.endswith('.csv'):
            with open(sample_path, 'rb') as f:
                df = read_csv_safely(f)
            set_df(df, 1)
            set_excel_data(None, [])
        else:
            np.random.seed(42)
            categories = ['Elektronik', 'Mobilya', 'Giyim', 'Gıda', 'Kırtasiye', 'Kozmetik']
            regions = ['Marmara', 'Ege', 'İç Anadolu', 'Akdeniz', 'Karadeniz']
            months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos']
            n = 120
            df = pd.DataFrame({
                'Kategori': np.random.choice(categories, n),
                'Bölge': np.random.choice(regions, n),
                'Dönem': np.random.choice(months, n),
                'Satış_Tutarı': np.random.randint(1000, 50000, n),
                'Kar': np.random.randint(200, 15000, n),
                'Maliyet': np.random.randint(800, 35000, n),
                'Müşteri_Memnuniyeti': np.random.uniform(3.0, 5.0, n).round(2),
                'İşlem_Adedi': np.random.randint(1, 20, n)
            })
            df = clean_dataframe(df)
            set_df(df, 1)
            set_excel_data(None, [])

        df = get_df(1)
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category', 'bool', 'string']).columns.tolist()

        return jsonify({
            'success': True,
            'file_name': 'Akademik_Ornek_Veri_Seti.xlsx',
            'total_rows': len(df),
            'total_cols': len(df.columns),
            'sheet_names': sheet_names,
            'active_sheet': active_sheet or (sheet_names[0] if sheet_names else None),
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols
        })
    except Exception as e:
        logger.exception(f"Örnek veri yükleme hatası: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/concept1', methods=['GET'])
def concept1():
    return render_template('landing_concept1.html')

@main_bp.route('/concept2', methods=['GET'])
def concept2():
    return render_template('landing_concept2.html')

@main_bp.route('/concept3', methods=['GET'])
def concept3():
    return render_template('landing_concept3.html')
