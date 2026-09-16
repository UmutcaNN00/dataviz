import os
import io
import csv
import logging
import pandas as pd
import numpy as np
import json
from scipy import stats as sp_stats
from flask import Flask, request, jsonify, render_template, send_file, session

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

import uuid
from flask import session

app.secret_key = 'dataviz_secret_super_key'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

def safe_float(val, default=None):
    """NaN, Infinity ve -Infinity değerlerini JSON uyumlu hale getirir."""
    try:
        if val is None or pd.isna(val) or np.isinf(val):
            return default
        f = float(val)
        return f if np.isfinite(f) else default
    except Exception:
        return default


DATA_STORE = {}

def get_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']

def get_df(ds_index=1):
    uid = get_user_id()
    return DATA_STORE.get(uid, {}).get(ds_index)

def set_df(df, ds_index=1):
    uid = get_user_id()
    if uid not in DATA_STORE:
        DATA_STORE[uid] = {1: None, 2: None, 'excel_file': None, 'sheet_names': []}
    DATA_STORE[uid][ds_index] = df

def get_excel_data():
    uid = get_user_id()
    if uid not in DATA_STORE:
        return None, []
    return DATA_STORE[uid].get('excel_file'), DATA_STORE[uid].get('sheet_names', [])

def set_excel_data(excel_file, sheet_names):
    uid = get_user_id()
    if uid not in DATA_STORE:
        DATA_STORE[uid] = {1: None, 2: None, 'excel_file': None, 'sheet_names': []}
    DATA_STORE[uid]['excel_file'] = excel_file
    DATA_STORE[uid]['sheet_names'] = sheet_names

def clean_dataframe(df):
    """
    DataFrame'i temizler:
    - Tamamen boş satır ve sütunları temizler.
    - Başlık ofseti veya boş başlık satırlarını tespit edip gerçek başlığı çıkarır.
    - Sütun isimlerindeki boşlukları ve BOM karakterini temizler.
    - İsimsiz (Unnamed:) veya boş sütun isimlerini 'Sütun_X' olarak düzeltir.
    - Mükerrer sütun isimlerini tekilleştirir.
    - Excel formül hatalarını (#VALUE!, #DIV/0! vb.) NaN yapar.
    """
    if df is None or df.empty:
        return df

    # 1. Tamamen boş satır ve sütunları kaldır
    df = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
    if df.empty:
        return df

    # 2. Formül hata metinlerini NaN'a dönüştür
    excel_error_strings = {'#VALUE!', '#REF!', '#DIV/0!', '#NAME?', '#NUM!', '#NULL!', '#N/A', '#N/A N/A'}
    df = df.replace(list(excel_error_strings), np.nan)

    # 3. Başlık satırının veri içinde kalıp kalmadığını (header offset) kontrol et
    cols = [str(c).replace('\ufeff', '').strip() for c in df.columns]
    unnamed_count = sum(1 for c in cols if not c or c.startswith('Unnamed:') or c.lower() == 'nan')
    
    # Eğer sütunların yarısından fazlası 'Unnamed' ise gerçek başlık ilk satırlarda olabilir
    if unnamed_count >= len(cols) / 2 and len(df) > 0:
        header_candidate_idx = None
        for r_idx in range(min(10, len(df))):
            row_vals = df.iloc[r_idx]
            valid_headers = [
                v for v in row_vals 
                if pd.notna(v) and str(v).strip() != '' and not str(v).lower().startswith('unnamed:') and str(v).lower() != 'nan'
            ]
            if len(valid_headers) >= max(2, len(cols) * 0.5):
                header_candidate_idx = r_idx
                break
        
        if header_candidate_idx is not None:
            new_cols = []
            header_row = df.iloc[header_candidate_idx]
            for i, val in enumerate(header_row):
                val_str = str(val).replace('\ufeff', '').strip() if pd.notna(val) else ''
                if val_str and val_str.lower() != 'nan':
                    new_cols.append(val_str)
                else:
                    new_cols.append(f'Sütun_{i+1}')
            df = df.iloc[header_candidate_idx + 1:].copy()
            df.columns = new_cols

    # 4. Sütun isimlerini normalize et ve tekilleştir
    cleaned_cols = []
    seen = {}
    for i, col in enumerate(df.columns):
        col_str = str(col).replace('\ufeff', '').strip()
        if not col_str or col_str.startswith('Unnamed:') or col_str.lower() == 'nan':
            col_str = f'Sütun_{i+1}'
        if col_str in seen:
            seen[col_str] += 1
            col_str = f'{col_str}_{seen[col_str]}'
        else:
            seen[col_str] = 0
        cleaned_cols.append(col_str)
    df.columns = cleaned_cols

    # 5. Başlık temizliği sonrası tamamen boşalan sütunları tekrar filtrele
    df = df.dropna(how='all', axis=1)
    df = df.reset_index(drop=True)
    return df

def read_csv_safely(file_input):
    """
    CSV dosyalarını farklı encoding (utf-8, utf-8-sig, windows-1254, iso-8859-9, latin1)
    ve ayraçlar (;, ,, \\t, |) ile güvenle okur.
    """
    if hasattr(file_input, 'read'):
        raw_bytes = file_input.read()
    elif isinstance(file_input, bytes):
        raw_bytes = file_input
    else:
        raise ValueError("Geçersiz dosya nesnesi.")

    if not raw_bytes or not raw_bytes.strip():
        raise pd.errors.EmptyDataError("CSV dosyası tamamen boş.")

    # 1. Encodings sırası: UTF-8 BOM varsa önce utf-8-sig, yoksa utf-8, sonra Türkçe ve latin1
    if raw_bytes.startswith(b'\xef\xbb\xbf'):
        encodings = ['utf-8-sig', 'utf-8', 'windows-1254', 'iso-8859-9', 'latin1']
    else:
        encodings = ['utf-8', 'utf-8-sig', 'windows-1254', 'iso-8859-9', 'latin1']

    decoded_text = None
    successful_enc = None
    for enc in encodings:
        try:
            text = raw_bytes.decode(enc)
            if '\x00' in text:
                continue
            decoded_text = text
            successful_enc = enc
            break
        except UnicodeDecodeError:
            continue

    if decoded_text is None:
        raise UnicodeDecodeError(
            'unknown', raw_bytes, 0, 1, 
            f"Dosya karakter kodlaması çözülemedi. Denediğimiz kodlamalar: {', '.join(encodings)}"
        )

    logger.info(f"CSV başarıyla çözümlendi. Kodlama: {successful_enc}")

    # 2. Ayraç (delimiter) tespiti
    sample_lines = [l for l in decoded_text.splitlines() if l.strip()][:25]
    detected_delim = None
    if sample_lines:
        header_line = sample_lines[0]
        counts = {d: header_line.count(d) for d in [';', ',', '\t', '|']}
        if any(c > 0 for c in counts.values()):
            try:
                sniffer = csv.Sniffer()
                detected_delim = sniffer.sniff('\n'.join(sample_lines), delimiters=';,\t|').delimiter
            except Exception:
                detected_delim = max(counts, key=counts.get)
        else:
            detected_delim = ','

    # 3. Pandas ile ayrıştırma
    df = None
    errors = []

    if detected_delim:
        try:
            df = pd.read_csv(io.StringIO(decoded_text), sep=detected_delim, engine='python')
        except Exception as e:
            errors.append(e)

    if df is None:
        try:
            df = pd.read_csv(io.StringIO(decoded_text), sep=None, engine='python')
        except Exception as e:
            errors.append(e)

    if df is None:
        for fallback_sep in [';', ',', '\t']:
            try:
                df = pd.read_csv(io.StringIO(decoded_text), sep=fallback_sep)
                break
            except Exception as e:
                errors.append(e)

    if df is None:
        raise ValueError(f"CSV içeriği tablolanamadı: {errors[-1] if errors else 'Bilinmeyen hata'}")

    return clean_dataframe(df)

def read_excel_safely(file_input):
    """
    .xlsx ve .xls dosyalarını pd.read_excel(sheet_name=None) ile okur,
    tüm sayfaları temizleyip bir sözlük ve sayfa listesi olarak döner.
    """
    if hasattr(file_input, 'read'):
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
        if 'xlrd' in err_msg.lower():
            raise ValueError("Eski Excel (.xls) dosyalarını okumak için 'xlrd' kütüphanesi gereklidir. Lütfen dosyanızı .xlsx formatına dönüştürüp yükleyin.")
        elif 'zip' in err_msg.lower() or 'corrupt' in err_msg.lower():
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
        all_empty = all(df.empty or len(df.columns) == 0 for df in cleaned_sheets.values())
        if all_empty:
            raise ValueError("Excel dosyasındaki tüm sayfalar boş veya geçerli veri içermiyor.")

    return active_df, cleaned_sheets, valid_sheet_names, active_sheet_name


app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

hf_pipeline = None  # Lazy loading için global model değişkeni

def apply_filters(df, filters):
    """Verilen filtre listesini DataFrame'e uygular."""
    if df is None or df.empty or not filters or not isinstance(filters, list):
        return df
    filtered_df = df.copy()
    for f in filters:
        col = f.get('column')
        if not col or col not in filtered_df.columns:
            continue
        ftype = f.get('type')
        if ftype == 'cat':
            selected_vals = f.get('values', [])
            if selected_vals and len(selected_vals) > 0:
                filtered_df = filtered_df[filtered_df[col].astype(str).isin([str(v) for v in selected_vals])]
        elif ftype == 'num':
            min_val = f.get('min')
            max_val = f.get('max')
            col_num = pd.to_numeric(filtered_df[col], errors='coerce')
            if min_val is not None and str(min_val).strip() != '':
                try:
                    filtered_df = filtered_df[col_num >= float(min_val)]
                except (ValueError, TypeError):
                    pass
            if max_val is not None and str(max_val).strip() != '':
                try:
                    filtered_df = filtered_df[col_num <= float(max_val)]
                except (ValueError, TypeError):
                    pass
    return filtered_df

@app.route('/')
def index():
    global_df = get_df(1)
    global_df_2 = get_df(2)

    return render_template('landing.html')

@app.route('/analysis')
def analysis():
    global_df = get_df(1)
    global_df_2 = get_df(2)

    return render_template('analysis.html')

@app.route('/a4-demo')
def a4_demo():
    return render_template('a4_demo.html')

@app.route('/load_sample', methods=['GET', 'POST'])
def load_sample():
    try:
        sample_path = None
        for candidate in ['ornek_veri_seti.xlsx', '1_Satis_Islemleri_Devasa.xlsx', 'test_satislar.csv', 'test.csv']:
            if os.path.exists(candidate):
                sample_path = candidate
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
        categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

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
        logger.exception(f"Örnek veri hatası: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'İstekte dosya bulunamadı. Lütfen bir dosya seçin.'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Herhangi bir dosya seçilmedi.'}), 400

    filename = file.filename.lower()
    logger.info(f"Dosya yükleme isteği alındı: {file.filename}")

    try:
        sheet_names = []
        active_sheet = None

        if filename.endswith('.csv'):
            df = read_csv_safely(file)
            set_df(df, 1)
            set_excel_data(None, [])
        elif filename.endswith(('.xls', '.xlsx')):
            df, sheets_dict, sheet_names, active_sheet = read_excel_safely(file)
            set_df(df, 1)
            set_excel_data(sheets_dict, sheet_names)
        else:
            return jsonify({
                'error': 'Desteklenmeyen dosya formatı. Lütfen sadece .csv, .xlsx veya .xls uzantılı dosyalar yükleyin.'
            }), 400

        if df is None or df.empty or len(df.columns) == 0:
            return jsonify({'error': 'Yüklenen dosyada geçerli veri veya sütun bulunamadı.'}), 400

        # Sütun isimlerindeki boşlukları ve BOM karakterlerini temizle
        df.columns = [str(c).replace('\ufeff', '').strip() for c in df.columns]
        set_df(df, 1)

        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

        logger.info(f"Yükleme başarılı: {file.filename} -> {len(df)} satır, {len(df.columns)} sütun")

        return jsonify({
            'success': True,
            'total_rows': len(df),
            'total_cols': len(df.columns),
            'sheet_names': sheet_names,
            'active_sheet': active_sheet or (sheet_names[0] if sheet_names else None),
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols
        })
    except pd.errors.EmptyDataError:
        logger.warning(f"Boş dosya yüklendi: {file.filename}")
        return jsonify({'error': 'Yüklenen dosya tamamen boş veya veri içermiyor.'}), 400
    except UnicodeDecodeError as e:
        logger.error(f"Kodlama hatası ({file.filename}): {e}")
        return jsonify({
            'error': 'Dosya karakter kodlaması çözülemedi. Lütfen dosyanın UTF-8 veya Windows-1254 (Türkçe) formatında olduğundan emin olun.'
        }), 400
    except ValueError as e:
        logger.error(f"Doğrulama hatası ({file.filename}): {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.exception(f"Dosya yükleme hatası ({file.filename}): {e}")
        return jsonify({'error': f'Dosya işlenirken bir hata oluştu: {str(e)}'}), 400

# ═════════ 1. ÇOKLU EXCEL SEKME GEÇİŞİ (Multi-Sheet) ═════════
@app.route('/switch_sheet', methods=['POST'])
def switch_sheet():
    excel_file, sheet_names = get_excel_data()
    
    if not excel_file:
        return jsonify({'error': 'Yüklü bir Excel dosyası bulunamadı.'}), 400
    
    req_json = request.get_json(silent=True) or {}
    sheet_name = req_json.get('sheet_name')
    if not sheet_name or sheet_name not in sheet_names:
        return jsonify({'error': f"Geçersiz sayfa adı: '{sheet_name}'. Mevcut sayfalar: {', '.join(sheet_names)}"}), 400
    
    try:
        if isinstance(excel_file, dict):
            df = excel_file.get(sheet_name)
            if df is not None:
                df = df.copy()
        elif hasattr(excel_file, 'parse'):
            df = excel_file.parse(sheet_name)
        else:
            return jsonify({'error': 'Excel sayfa verisi okunamadı.'}), 400

        if df is None or df.empty:
            return jsonify({'error': f"'{sheet_name}' sayfası boş veya veri içermiyor."}), 400

        df = clean_dataframe(df)
        df.columns = [str(c).replace('\ufeff', '').strip() for c in df.columns]
        set_df(df, 1)
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

        logger.info(f"Excel sayfası değiştirildi: {sheet_name} ({len(df)} satır, {len(df.columns)} sütun)")

        return jsonify({
            'success': True,
            'active_sheet': sheet_name,
            'total_rows': len(df),
            'total_cols': len(df.columns),
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols
        })
    except Exception as e:
        logger.exception(f"Sayfa değiştirme hatası: {e}")
        return jsonify({'error': f'Sayfa değiştirilirken bir hata oluştu: {str(e)}'}), 400

# ═════════ 2. AKILLI VERİ BİRLEŞTİRİCİ (Data Merge & Join) ═════════
@app.route('/preview_second_file', methods=['POST'])
def preview_second_file():
    global_df = get_df(1)
    global_df_2 = get_df(2)
    if global_df is None: return jsonify({'error': 'Önce 1. dosyayı yükleyin'}), 400
    if 'file2' not in request.files: return jsonify({'error': '2. dosya bulunamadı'}), 400
    file2 = request.files['file2']
    if file2.filename == '': return jsonify({'error': 'Dosya seçilmedi'}), 400

    try:
        filename2 = file2.filename.lower()
        if filename2.endswith('.csv'): 
            df2 = read_csv_safely(file2)
        elif filename2.endswith(('.xls', '.xlsx')): 
            df2, _, _, _ = read_excel_safely(file2)
        else: 
            return jsonify({'error': 'Desteklenmeyen dosya formatı'}), 400

        df2.columns = [str(c).replace('\ufeff', '').strip() for c in df2.columns]
        
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
            if auto_key1: break

        # 2. Key words match
        if not auto_key1:
            for c1 in cols1:
                if any(w in c1.lower() for w in ['id', 'kod', 'no', 'numara', 'tc', 'key', 'sehir', 'bolge', 'tarih']):
                    for c2 in cols2:
                        if any(w in c2.lower() for w in ['id', 'kod', 'no', 'numara', 'tc', 'key', 'sehir', 'bolge', 'tarih']):
                            auto_key1 = c1
                            auto_key2 = c2
                            break
                    if auto_key1: break

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
        return jsonify({'error': str(e)}), 500

@app.route('/merge_datasets', methods=['POST'])
def merge_datasets():
    global_df = get_df(1)
    global_df_2 = get_df(2)
    if global_df is None: return jsonify({'error': 'Önce 1. dosyayı yükleyin'}), 400
    if 'file2' not in request.files: return jsonify({'error': '2. dosya bulunamadı'}), 400
    
    file2 = request.files['file2']
    key1 = request.form.get('key1')
    key2 = request.form.get('key2')
    join_type = request.form.get('join_type', 'left')

    if not key1 or not key2:
        return jsonify({'error': 'Birleştirme anahtarları (ortak sütunlar) seçilmelidir.'}), 400

    try:
        filename2 = file2.filename.lower()
        if filename2.endswith('.csv'): 
            df2 = read_csv_safely(file2)
        elif filename2.endswith(('.xls', '.xlsx')): 
            df2, _, _, _ = read_excel_safely(file2)
        else: 
            return jsonify({'error': 'Desteklenmeyen dosya formatı'}), 400

        df2.columns = [str(c).replace('\ufeff', '').strip() for c in df2.columns]

        if key1 not in global_df.columns:
            return jsonify({'error': f'1. tabloda "{key1}" sütunu bulunamadı'}), 400
        if key2 not in df2.columns:
            return jsonify({'error': f'2. tabloda "{key2}" sütunu bulunamadı'}), 400

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

        # NaN anahtarların birbiriyle eşleşip sahte kartezyen patlama yapmasını engelle:
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
        
        # Eğer 2. tablodan gelen key sütunu '_2' eki aldıysa veya gereksiz tekrar ediyorsa temizle
        if key2 + '_2' in merged.columns:
            merged.drop(columns=[key2 + '_2'], inplace=True)
        elif key1 == key2 and key2 in merged.columns:
            # Tek bir kopya kalması yeterli
            pass

        old_cols = set(global_df.columns)
        new_cols = [c for c in merged.columns if c not in old_cols]

        global_df = merged
        set_df(global_df, 1)

        numeric_cols = global_df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = global_df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

        return jsonify({
            'success': True,
            'total_rows': len(global_df),
            'total_cols': len(global_df.columns),
            'new_joined_columns': new_cols,
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols
        })
    except Exception as e:
        return jsonify({'error': f'Birleştirme hatası: {str(e)}'}), 500

# ═════════ 3. FORMÜL & YENİ SÜTUN ÜRETİCİ (Calculated Fields) ═════════
@app.route('/create_calculated_column', methods=['POST'])
def create_calculated_column():
    global_df = get_df(1)
    global_df_2 = get_df(2)
    if global_df is None: return jsonify({'error': 'Veri yok'}), 400
    
    data = request.json
    new_col = data.get('new_column_name', '').strip()
    col1 = data.get('col1')
    op = data.get('operator')
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
            set_df(global_df, 1)
        elif op == '-': 
            global_df[new_col] = s1 - s2
            set_df(global_df, 1)
        elif op == '*': 
            global_df[new_col] = s1 * s2
            set_df(global_df, 1)
        elif op == '/': 
            global_df[new_col] = np.where(s2 != 0, s1 / s2, 0)
            global_df[new_col] = pd.Series(global_df[new_col]).replace([np.inf, -np.inf], 0)
            set_df(global_df, 1)
        else: return jsonify({'error': 'Geçersiz işlem operatörü.'}), 400

        numeric_cols = global_df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = global_df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

        return jsonify({
            'success': True,
            'new_column': new_col,
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols
        })
    except Exception as e:
        return jsonify({'error': f'Hesaplama hatası: {str(e)}'}), 500

# ═════════ 4. VERİ SAĞLIĞI (Data Prep) ═════════
@app.route('/check_health', methods=['GET'])
def check_health():
    global_df = get_df(1)
    global_df_2 = get_df(2)
    if global_df is None: return jsonify({'error': 'Veri yok'}), 400
    
    missing_count = int(global_df.isnull().sum().sum())
    missing_rows = int(global_df.isnull().any(axis=1).sum())
    
    return jsonify({
        'has_issues': missing_rows > 0,
        'missing_cells': missing_count,
        'missing_rows': missing_rows,
        'total_rows': len(global_df)
    })

@app.route('/clean_data', methods=['POST'])
def clean_data():
    global_df = get_df(1)
    global_df_2 = get_df(2)
    if global_df is None: return jsonify({'error': 'Veri yok'}), 400
    
    action = request.json.get('action', 'drop')
    try:
        if action == 'drop':
            global_df = global_df.dropna()
            set_df(global_df, 1)
        elif action == 'fill_mean':
            num_cols = global_df.select_dtypes(include=['number']).columns
            means = global_df[num_cols].mean()
            global_df[num_cols] = global_df[num_cols].fillna(means).fillna(0)
            for c in global_df.select_dtypes(include=['object', 'category']).columns:
                if pd.api.types.is_categorical_dtype(global_df[c]):
                    if 'Bilinmiyor' not in global_df[c].cat.categories:
                        global_df[c] = global_df[c].cat.add_categories(['Bilinmiyor'])
                global_df[c] = global_df[c].fillna('Bilinmiyor')
            set_df(global_df, 1)
        elif action == 'fill_zero':
            num_cols = global_df.select_dtypes(include=['number']).columns
            global_df[num_cols] = global_df[num_cols].fillna(0)
            for c in global_df.select_dtypes(include=['object', 'category']).columns:
                if pd.api.types.is_categorical_dtype(global_df[c]):
                    if 'Bilinmiyor' not in global_df[c].cat.categories:
                        global_df[c] = global_df[c].cat.add_categories(['Bilinmiyor'])
                global_df[c] = global_df[c].fillna('Bilinmiyor')
            set_df(global_df, 1)
            
        numeric_cols = global_df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = global_df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

        return jsonify({
            'success': True,
            'total_rows': len(global_df),
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ═════════ 5. DİLİMLEYİCİLER / SÜTUN DETAYLARI ═════════
@app.route('/get_column_details', methods=['POST'])
def get_column_details():
    global_df = get_df(1)
    global_df_2 = get_df(2)
    if global_df is None: return jsonify({'error': 'Veri yok'}), 400
    col = request.json.get('column')
    if not col or col not in global_df.columns:
        return jsonify({'error': 'Sütun bulunamadı'}), 400
    
    series = global_df[col]
    is_num = pd.api.types.is_numeric_dtype(series)
    
    if is_num:
        min_v = float(series.min()) if pd.notnull(series.min()) else 0.0
        max_v = float(series.max()) if pd.notnull(series.max()) else 100.0
        return jsonify({
            'column': col,
            'type': 'num',
            'min': min_v,
            'max': max_v,
            'count': int(series.count())
        })
    else:
        val_counts = series.astype(str).value_counts().head(100)
        categories = [{'value': str(k), 'count': int(v)} for k, v in val_counts.items()]
        return jsonify({
            'column': col,
            'type': 'cat',
            'categories': categories,
            'total_unique': int(series.nunique())
        })

# ═════════ 6. ÜST DÜZEY KPI ÖZET KARTLARI (Executive KPI Tiles) ═════════
@app.route('/get_kpi_summary', methods=['POST'])
def get_kpi_summary():
    global_df = get_df(1)
    global_df_2 = get_df(2)
    if global_df is None: return jsonify({'error': 'Veri yok'}), 400
    
    filters = request.json.get('filters', [])
    active_df = apply_filters(global_df, filters)
    if active_df.empty:
        return jsonify({'kpis': []})
    
    num_cols = active_df.select_dtypes(include=['number']).columns.tolist()
    cat_cols = active_df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    kpis = []
    
    # 1. Toplam Kayıt Sayısı
    kpis.append({
        'title': 'Toplam Kayıt',
        'value': f"{len(active_df):,}".replace(',', '.'),
        'sub': f"Toplam {len(global_df):,} satırdan",
        'icon': '📋',
        'color': 'blue'
    })
    
    # 2. Ana Sayısal Toplam
    if num_cols:
        main_num = num_cols[0]
        total_val = float(active_df[main_num].sum())
        mean_val = float(active_df[main_num].mean())
        
        val_str = f"{total_val:,.1f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        if total_val >= 1_000_000:
            val_str = f"₺{total_val/1_000_000:.2f}M"
        elif total_val >= 1_000:
            val_str = f"₺{total_val/1_000:.1f}K"

        kpis.append({
            'title': f'Toplam {main_num}',
            'value': val_str,
            'sub': f"Ort: {mean_val:,.1f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'icon': '💰',
            'color': 'green'
        })
        
        # 3. İkinci Sayısal veya Ortalama
        if len(num_cols) > 1:
            sec_num = num_cols[1]
            sec_total = float(active_df[sec_num].sum())
            kpis.append({
                'title': f'Toplam {sec_num}',
                'value': f"{sec_total:,.1f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                'sub': f"Maks: {active_df[sec_num].max():,.1f}",
                'icon': '📈',
                'color': 'purple'
            })
    
    # 4. Lider Kategori
    if cat_cols:
        main_cat = cat_cols[0]
        vc = active_df[main_cat].dropna().value_counts()
        if not vc.empty:
            top_cat_name = str(vc.index[0])
            top_cat_count = int(vc.iloc[0])
            pct = (top_cat_count / len(active_df)) * 100 if len(active_df) > 0 else 0
            kpis.append({
                'title': f'Lider {main_cat}',
                'value': top_cat_name[:15],
                'sub': f"%{pct:.1f} pay ({top_cat_count} adet)",
                'icon': '🏆',
                'color': 'orange'
            })

    return jsonify({'kpis': kpis, 'total_active_rows': len(active_df)})

# ═════════ 7. AI INSIGHT (Local Hugging Face - Qwen2.5-0.5B) ═════════
@app.route('/generate_insight', methods=['POST'])
def generate_insight():
    global_df = get_df(1)
    global_df_2 = get_df(2)

    global hf_pipeline
    data = request.json
    stats = data.get('stats', {})
    chart = data.get('chart_type', 'Grafik')
    x_col = data.get('x_col', 'Bilinmiyor')
    y_cols = data.get('y_cols', [])
    
    prompt = f"""Şu istatistikleri (Grafik: {chart}, X: {x_col}, Y: {', '.join(y_cols)}) teknik olmayan birinin anlayacağı basitlikte, Türkçe olarak kısaca yorumla: {json.dumps(stats, ensure_ascii=False)}"""

    try:
        if hf_pipeline is None:
            try:
                from transformers import pipeline
                hf_pipeline = pipeline("text-generation", model="Qwen/Qwen2.5-1.5B-Instruct")
            except Exception:
                hf_pipeline = False
        if not hf_pipeline:
            raise RuntimeError("HuggingFace pipeline mevcut değil, yerel kural motoruna geçiliyor.")

        messages = [
            {"role": "system", "content": "Sen bir akademi profesörü ve istatistik uzmanısın. Amacın, sana gönderilen verileri bilimsel bir titizlikle, nesnel ve profesyonel bir akademik dil kullanarak analiz etmektir. Yanıtlarını Türkçe ver. Sadece verideki istatistiksel eğilimleri (trend), varyans farklılıklarını ve en önemli bulguları 3-4 madde halinde özetle. Akademik sunumlara uygun, resmi bir istatistiksel özet dili (ör. 'harika veriler' yerine 'anlamlı istatistiksel dağılım') kullan. Okunabilirliği artırmak için Markdown kullan."},
            {"role": "user", "content": prompt}
        ]
        
        response = hf_pipeline(messages, max_new_tokens=400, temperature=0.3)
        reply = response[0]['generated_text'][-1]['content']
        return jsonify({"insight": reply})
    except Exception as e:
        # Akıllı İstatistiksel Yedek Yorumlayıcı (Local Rule-based Executive Fallback)
        items = [f"### 📊 Akademik Veri Analizi Raporu ({chart.upper()})"]
        items.append(f"**Değişkenler:** Bağımsız Değişken (X): `{x_col}`, Bağımlı Değişkenler (Y): `{', '.join(y_cols) if y_cols else 'Genel Dağılım'}`")
        
        if stats and isinstance(stats, dict):
            for col, s in stats.items():
                mean = s.get('mean')
                med = s.get('median')
                min_v = s.get('min')
                max_v = s.get('max')
                std_v = s.get('std')
                
                col_notes = [f"#### 🔹 **{col} İstatistiksel Analizi:**"]
                if mean is not None and med is not None:
                    skew = "simetrik ve normal dağılıma yakın"
                    if mean > med * 1.15: skew = "sağa çarpık (pozitif çarpıklık) dağılım yönünde"
                    elif mean < med * 0.85: skew = "sola çarpık (negatif çarpıklık) dağılım yönünde"
                    col_notes.append(f"- **Merkezi Eğilim Ölçüleri:** Ortalama: **{mean:,.2f}**, Medyan: **{med:,.2f}**. Dağılım *{skew}* bir yapı göstermektedir.")
                
                if min_v is not None and max_v is not None:
                    col_notes.append(f"- **Dağılım Aralığı:** Minimum **{min_v:,.2f}**, Maksimum **{max_v:,.2f}** (Aralık: **{max_v - min_v:,.2f}**).")
                
                if std_v is not None and mean and mean != 0:
                    cv = (std_v / abs(mean)) * 100
                    col_notes.append(f"- **Dağılım Ölçüleri:** Standart Sapma: **{std_v:,.2f}** (Varyasyon Katsayısı: %{cv:.1f}).")
                
                items.append("\n".join(col_notes))
        else:
            items.append("- Belirtilen değişkenler üzerinde tanımlayıcı istatistikler incelenmiştir.")
            items.append("- Veri setindeki temel gözlemlerin dağılımı analiz edilmiştir.")

        items.append("\n💡 **Akademik Sonuç:** Elde edilen bulgular doğrultusunda, temel metriklerdeki varyans farklılıklarının ve yapısal etkenlerin ileri istatistiksel yöntemlerle araştırılması önerilmektedir.")
        
        return jsonify({"insight": "\n\n".join(items), "fallback": True})

# ═════════ 8. GET CHART DATA ═════════
@app.route('/get_chart_data', methods=['POST'])
def get_chart_data():
    global_df = get_df(1)
    global_df_2 = get_df(2)
    if global_df is None: return jsonify({'error': 'Önce dosya yükleyin'}), 400
    data = request.json
    x_col = data.get('x_col')
    y_cols = data.get('y_cols', [])
    agg_func = data.get('agg_func', 'sum')
    chart_type = data.get('chart_type', 'bar')
    filters = data.get('filters', [])

    if isinstance(y_cols, str): y_cols = [y_cols]
    
    active_df = apply_filters(global_df, filters)
    active_df = active_df.replace([np.inf, -np.inf, np.nan], 0)
    if active_df.empty:
        return jsonify({'error': 'Uygulanan filtreler sonucunda görüntülenecek veri kalmadı.'}), 400

    available_cols = active_df.columns.tolist()
    if x_col and x_col not in available_cols: x_col = None
    y_cols = [y for y in y_cols if y in available_cols]
    raw_charts = ['histogram', 'histogram2d', 'box', 'violin', 'scatter', 'bubble', 'scatter3d', 'line3d', 'scattergeo', 'scattermatrix', 'density2d', 'rug', 'strip', 'parcoords', 'parcats', 'candlestick', 'ohlc', 'dumbbell', 'ternary']
    corr_charts = ['heatmap', 'surface', 'contour', 'carpet', 'contourcarpet']
    response_data = {'chart_type': chart_type, 'total_active_rows': len(active_df)}

    try:
        if chart_type in raw_charts:
            df_sample = active_df.head(5000)
            raw_dict = {}
            if x_col: raw_dict['__x__'] = df_sample[x_col].fillna('N/A').tolist()
            for y in y_cols: raw_dict[y] = df_sample[y].astype(object).fillna(0).tolist()
            response_data['raw'] = raw_dict
        elif chart_type in corr_charts:
            # Eğer 2'den az sayısal seçildiyse, mevcut sayısal sütunlardan otomatik tamamla
            num_cols = active_df.select_dtypes(include=['number']).columns.tolist()
            calc_cols = y_cols if len(y_cols) >= 2 else (num_cols[:6] if len(num_cols) >= 2 else y_cols)
            if len(calc_cols) < 2:
                # 2 sayısal yoksa agg chart fallback
                agg_dict = {'__x__': ['Tümü']}
                for y in y_cols: agg_dict[y] = [float(active_df[y].sum()) if pd.notnull(active_df[y].sum()) else 0]
                response_data['agg'] = agg_dict
            else:
                corr_matrix = active_df[calc_cols].corr()
                response_data['corr'] = {'labels': calc_cols, 'matrix': corr_matrix.fillna(0).values.tolist()}
        else:
            if not x_col:
                agg_dict = {'__x__': ['Tümü']}
                for y in y_cols:
                    if agg_func == 'sum': val = active_df[y].sum()
                    elif agg_func == 'mean': val = active_df[y].mean()
                    elif agg_func == 'median': val = active_df[y].median()
                    elif agg_func == 'min': val = active_df[y].min()
                    elif agg_func == 'max': val = active_df[y].max()
                    else: val = active_df[y].count()
                    agg_dict[y] = [float(val) if pd.notnull(val) else 0]
                response_data['agg'] = agg_dict
            else:
                grouped = active_df.groupby(x_col)
                if agg_func == 'sum': grouped = grouped.sum(numeric_only=True)
                elif agg_func == 'mean': grouped = grouped.mean(numeric_only=True)
                elif agg_func == 'median': grouped = grouped.median(numeric_only=True)
                elif agg_func == 'min': grouped = grouped.min(numeric_only=True)
                elif agg_func == 'max': grouped = grouped.max(numeric_only=True)
                else: grouped = grouped.count()
                
                if len(grouped) > 100:
                    if agg_func in ['sum', 'mean'] and y_cols and y_cols[0] in grouped.columns:
                        grouped = grouped.sort_values(by=y_cols[0], ascending=False).head(100)
                    else:
                        grouped = grouped.head(100)
                        
                agg_dict = {'__x__': [str(x) for x in grouped.index.tolist()]}
                for y in y_cols:
                    if y in grouped.columns: agg_dict[y] = grouped[y].astype(object).fillna(0).tolist()
                response_data['agg'] = agg_dict

        return jsonify(response_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_stats', methods=['POST'])
def get_stats():
    global_df = get_df(1)
    global_df_2 = get_df(2)
    if global_df is None: return jsonify({'error': 'Veri yok'}), 400
    data = request.json
    cols = data.get('columns', [])
    filters = data.get('filters', [])
    x_col = data.get('x_col')
    
    active_df = apply_filters(global_df, filters)
    active_df = active_df.replace([np.inf, -np.inf, np.nan], 0)
    if not cols or active_df.empty: return jsonify({'stats': {}, 'advanced': {}, 'total_active_rows': len(active_df)})
    
    stats = {}
    for col in cols:
        if col in active_df.columns and pd.api.types.is_numeric_dtype(active_df[col]):
            s = active_df[col]
            stats[col] = {
                'count': int(s.count()), 'missing': int(s.isna().sum()),
                'mean': float(s.mean()) if pd.notnull(s.mean()) else None,
                'median': float(s.median()) if pd.notnull(s.median()) else None,
                'min': float(s.min()) if pd.notnull(s.min()) else None,
                'max': float(s.max()) if pd.notnull(s.max()) else None,
                'std': float(s.std()) if pd.notnull(s.std()) else None
            }
            
    advanced = {}
    if x_col and x_col in active_df.columns:
        x_series = active_df[x_col]
        is_x_num = pd.api.types.is_numeric_dtype(x_series)
        
        for y_col in cols:
            if y_col not in active_df.columns or not pd.api.types.is_numeric_dtype(active_df[y_col]): continue
            
            adv_info = {}
            valid_df = active_df[[x_col, y_col]].dropna()
            
            if len(valid_df) > 2:
                if is_x_num:
                    x_vals = valid_df[x_col].values
                    y_vals = valid_df[y_col].values
                    try:
                        slope, intercept, r_value, p_value, std_err = sp_stats.linregress(x_vals, y_vals)
                        r_clean = safe_float(r_value, 0.0)
                        adv_info['correlation'] = r_clean
                        adv_info['r_squared'] = safe_float(r_clean**2, 0.0)
                        adv_info['regression'] = f"y = {slope:.4f}x + {intercept:.4f}" if np.isfinite(slope) and np.isfinite(intercept) else "Hesaplanan regresyon tanımsız"
                        adv_info['p_value'] = safe_float(p_value, None)
                        adv_info['type'] = 'numeric'
                    except Exception:
                        pass
                else:
                    groups = [group[y_col].values for name, group in valid_df.groupby(x_col) if len(group) > 0]
                    if len(groups) == 2:
                        try:
                            t_stat, p_val = sp_stats.ttest_ind(groups[0], groups[1], equal_var=False)
                            adv_info['t_test_stat'] = safe_float(t_stat, None)
                            adv_info['p_value'] = safe_float(p_val, None)
                            adv_info['type'] = 'categorical_2'
                        except Exception:
                            pass
                    elif len(groups) > 2:
                        try:
                            f_stat, p_val = sp_stats.f_oneway(*groups)
                            adv_info['anova_f'] = safe_float(f_stat, None)
                            adv_info['p_value'] = safe_float(p_val, None)
                            adv_info['type'] = 'categorical_n'
                        except Exception:
                            pass
            advanced[y_col] = adv_info

    return jsonify({'stats': stats, 'advanced': advanced, 'total_active_rows': len(active_df)})

# ═════════ 9. CANLI PIVOT TABLO (EXCEL-STYLE PIVOT MATRIX) ═════════
@app.route('/get_pivot_data', methods=['POST'])
def get_pivot_data():
    global_df = get_df(1)
    global_df_2 = get_df(2)
    if global_df is None:
        return jsonify({'error': 'Lütfen önce bir veri seti yükleyin.'}), 400

    data = request.json or {}
    rows = data.get('rows', [])
    cols = data.get('cols', [])
    values = data.get('values', [])
    agg_func = data.get('agg_func', 'sum')
    filters = data.get('filters', [])

    if not rows and not cols:
        return jsonify({'error': 'En az bir Satır veya Sütun boyutu seçmelisiniz.'}), 400
    if not values:
        return jsonify({'error': 'Lütfen hesaplanacak en az bir Değer (Metrik) seçin.'}), 400

    active_df = apply_filters(global_df, filters)
    if active_df.empty:
        return jsonify({'error': 'Uygulanan filtreler sonucunda veri kalmadı.'}), 400

    valid_rows = [r for r in rows if r in active_df.columns]
    valid_cols = [c for c in cols if c in active_df.columns]
    valid_values = [v for v in values if v in active_df.columns and pd.api.types.is_numeric_dtype(active_df[v])]

    if len(valid_rows) == 0 and len(valid_cols) == 0:
        return jsonify({'error': 'Geçerli boyut seçilmedi'}), 400

    if not valid_values:
        return jsonify({'error': 'Seçilen değer sütunları sayısal olmalıdır.'}), 400

    try:
        agg_map = {
            'sum': 'sum',
            'mean': 'mean',
            'count': 'count',
            'min': 'min',
            'max': 'max',
            'median': 'median'
        }
        chosen_agg = agg_map.get(agg_func, 'sum')

        pt = pd.pivot_table(
            active_df,
            index=valid_rows if valid_rows else None,
            columns=valid_cols if valid_cols else None,
            values=valid_values,
            aggfunc=chosen_agg,
            fill_value=0,
            margins=True,
            margins_name='Genel Toplam'
        )

        table_headers = []
        if isinstance(pt.columns, pd.MultiIndex):
            raw_headers = pt.columns.tolist()
            flattened_cols = []
            for item in raw_headers:
                flattened_cols.append(" | ".join([str(x) for x in item if str(x) != '']))
            table_headers = flattened_cols
        else:
            table_headers = [str(c) for c in pt.columns.tolist()]

        table_rows = []
        raw_values_all = []

        if isinstance(pt.index, pd.MultiIndex):
            index_names = [str(n) if n else f"Seviye {i+1}" for i, n in enumerate(pt.index.names)]
            for idx_val, row_series in pt.iterrows():
                row_labels = [str(x) for x in idx_val]
                row_vals = [float(v) if pd.notnull(v) else 0 for v in row_series.tolist()]
                if 'Genel Toplam' not in row_labels:
                    raw_values_all.extend(row_vals[:-1] if 'Genel Toplam' in table_headers else row_vals)
                table_rows.append({
                    'row_labels': row_labels,
                    'cells': row_vals,
                    'is_grand_total': 'Genel Toplam' in row_labels
                })
        else:
            index_names = [str(pt.index.name) if pt.index.name else (valid_rows[0] if valid_rows else 'Boyut')]
            for idx_val, row_series in pt.iterrows():
                row_labels = [str(idx_val)]
                row_vals = [float(v) if pd.notnull(v) else 0 for v in row_series.tolist()]
                if str(idx_val) != 'Genel Toplam':
                    raw_values_all.extend(row_vals[:-1] if 'Genel Toplam' in table_headers else row_vals)
                table_rows.append({
                    'row_labels': row_labels,
                    'cells': row_vals,
                    'is_grand_total': str(idx_val) == 'Genel Toplam'
                })

        min_val = float(min(raw_values_all)) if raw_values_all else 0
        max_val = float(max(raw_values_all)) if raw_values_all else 0

        return jsonify({
            'index_names': index_names,
            'column_headers': table_headers,
            'rows': table_rows,
            'min_value': min_val,
            'max_value': max_val,
            'total_data_rows': len(active_df),
            'row_dimensions': valid_rows,
            'col_dimensions': valid_cols,
            'value_metrics': valid_values,
            'agg_func': agg_func
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Pivot tablosu hesaplanırken hata oluştu: {str(e)}'}), 500


@app.route('/export_pivot_excel', methods=['POST'])
def export_pivot_excel():
    global_df = get_df(1)
    global_df_2 = get_df(2)
    if global_df is None:
        return jsonify({'error': 'Veri yok'}), 400

    data = request.json or {}
    rows = data.get('rows', [])
    cols = data.get('cols', [])
    values = data.get('values', [])
    agg_func = data.get('agg_func', 'sum')
    filters = data.get('filters', [])

    active_df = apply_filters(global_df, filters)
    if active_df is None or active_df.empty:
        return jsonify({'error': 'Uygulanan filtreler sonucunda dışa aktarılacak veri kalmadı.'}), 400

    valid_rows = [r for r in rows if r in active_df.columns]
    valid_cols = [c for c in cols if c in active_df.columns]
    valid_values = [v for v in values if v in active_df.columns and pd.api.types.is_numeric_dtype(active_df[v])]

    if not valid_rows and not valid_cols:
        return jsonify({'error': 'En az bir Satır veya Sütun boyutu seçilmelidir.'}), 400
    if not valid_values:
        return jsonify({'error': 'En az bir sayısal değer metriği seçilmelidir.'}), 400

    try:
        import io
        from flask import send_file

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

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='Ozet_Pivot_Raporu.xlsx'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500




# ═════════ 10. AKTİF VERİ DIŞA AKTARMA (CSV / EXCEL) ═════════
@app.route('/export_data', methods=['POST'])
def export_data():
    global_df = get_df(1)
    if global_df is None or global_df.empty:
        return jsonify({'error': 'Dışa aktarılacak aktif veri seti bulunamadı.'}), 400
    
    data = request.get_json(silent=True) or {}
    export_format = data.get('format', 'csv').lower()
    filters = data.get('filters', [])
    
    active_df = apply_filters(global_df, filters)
    if active_df is None or active_df.empty:
        return jsonify({'error': 'Filtreler sonucunda dışa aktarılacak veri kalmadı.'}), 400

    output = io.BytesIO()
    if export_format in ['xlsx', 'excel']:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            active_df.to_excel(writer, index=False, sheet_name='Veri_Seti')
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        download_name = 'Aktarilan_Veri.xlsx'
    else:
        csv_str = active_df.to_csv(index=False, encoding='utf-8-sig')
        output.write(csv_str.encode('utf-8-sig'))
        mimetype = 'text/csv; charset=utf-8'
        download_name = 'Aktarilan_Veri.csv'

    output.seek(0)
    return send_file(output, mimetype=mimetype, as_attachment=True, download_name=download_name)


if __name__ == '__main__':
    app.run(debug=True)
