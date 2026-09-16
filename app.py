import os
import io
import pandas as pd
import numpy as np
import json
from scipy import stats as sp_stats
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

import uuid
from flask import session

app.secret_key = 'dataviz_secret_super_key'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

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


app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

hf_pipeline = None  # Lazy loading için global model değişkeni

def apply_filters(df, filters):
    global_df = get_df(1)
    global_df_2 = get_df(2)

    """Verilen filtre listesini DataFrame'e uygular."""
    if not filters or not isinstance(filters, list):
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
            if min_val is not None:
                filtered_df = filtered_df[filtered_df[col] >= float(min_val)]
            if max_val is not None:
                filtered_df = filtered_df[filtered_df[col] <= float(max_val)]
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

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return jsonify({'error': 'Dosya bulunamadı'}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({'error': 'Dosya seçilmedi'}), 400

    try:
        sheet_names = []
        if file.filename.endswith('.csv'): 
            df = pd.read_csv(file)
            set_df(df, 1)
            set_excel_data(None, [])
        elif file.filename.endswith(('.xls', '.xlsx')): 
            file_bytes = file.read()
            excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
            sheet_names = excel_file.sheet_names
            df = excel_file.parse(sheet_names[0])
            set_df(df, 1)
            set_excel_data(excel_file, sheet_names)
        else: 
            return jsonify({'error': 'Desteklenmeyen dosya formatı'}), 400
        
        df = get_df(1)
        df.columns = df.columns.astype(str).str.strip()
        set_df(df, 1)
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
        
        return jsonify({
            'success': True,
            'total_rows': len(df),
            'total_cols': len(df.columns),
            'sheet_names': sheet_names,
            'active_sheet': sheet_names[0] if sheet_names else None,
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols
        })
    except pd.errors.EmptyDataError:
        return jsonify({'error': 'Dosya boş veya okunamadı'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ═════════ 1. ÇOKLU EXCEL SEKME GEÇİŞİ (Multi-Sheet) ═════════
@app.route('/switch_sheet', methods=['POST'])
def switch_sheet():
    excel_file, sheet_names = get_excel_data()
    
    if excel_file is None:
        return jsonify({'error': 'Yüklü bir Excel dosyası bulunamadı'}), 400
    
    sheet_name = request.json.get('sheet_name')
    if not sheet_name or sheet_name not in sheet_names:
        return jsonify({'error': 'Geçersiz sayfa adı'}), 400
    
    try:
        df = excel_file.parse(sheet_name)
        df.columns = df.columns.astype(str).str.strip()
        set_df(df, 1)
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

        return jsonify({
            'success': True,
            'active_sheet': sheet_name,
            'total_rows': len(df),
            'total_cols': len(df.columns),
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        if file2.filename.endswith('.csv'): 
            try:
                df2 = pd.read_csv(file2)
            except UnicodeDecodeError:
                file2.seek(0)
                df2 = pd.read_csv(file2, encoding='latin1')
        elif file2.filename.endswith(('.xls', '.xlsx')): 
            df2 = pd.read_excel(file2)
        else: 
            return jsonify({'error': 'Desteklenmeyen dosya formatı'}), 400

        df2.columns = df2.columns.astype(str).str.strip()
        
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
        if file2.filename.endswith('.csv'): 
            try:
                df2 = pd.read_csv(file2)
            except UnicodeDecodeError:
                file2.seek(0)
                df2 = pd.read_csv(file2, encoding='latin1')
        elif file2.filename.endswith(('.xls', '.xlsx')): 
            df2 = pd.read_excel(file2)
        else: 
            return jsonify({'error': 'Desteklenmeyen dosya formatı'}), 400

        df2.columns = df2.columns.astype(str).str.strip()

        if key1 not in global_df.columns:
            return jsonify({'error': f'1. tabloda "{key1}" sütunu bulunamadı'}), 400
        if key2 not in df2.columns:
            return jsonify({'error': f'2. tabloda "{key2}" sütunu bulunamadı'}), 400

        global_df_temp = global_df.copy()
        df2_temp = df2.copy()
        
        global_df_temp['_merge_key_'] = global_df_temp[key1].astype(str).str.strip()
        df2_temp['_merge_key_'] = df2_temp[key2].astype(str).str.strip()

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
            global_df[num_cols] = global_df[num_cols].fillna(global_df[num_cols].mean())
            cat_cols = global_df.select_dtypes(include=['object', 'category']).columns
            global_df[cat_cols] = global_df[cat_cols].fillna('Bilinmiyor')
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
        top_cat_name = str(active_df[main_cat].value_counts().index[0])
        top_cat_count = int(active_df[main_cat].value_counts().iloc[0])
        pct = (top_cat_count / len(active_df)) * 100
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
            
            hf_pipeline = pipeline("text-generation", model="Qwen/Qwen2.5-1.5B-Instruct")

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

# ═════════ 8. GET CHART DATA + GELECEK TAHMİNİ (FORECASTING) ═════════
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
    forecast_steps = int(data.get('forecast_steps', 0))

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
                    if agg_func in ['sum', 'mean'] and y_cols: grouped = grouped.sort_values(by=y_cols[0], ascending=False).head(100)
                    else: grouped = grouped.head(100)
                        
                agg_dict = {'__x__': [str(x) for x in grouped.index.tolist()]}
                for y in y_cols:
                    if y in grouped.columns: agg_dict[y] = grouped[y].astype(object).fillna(0).tolist()
                response_data['agg'] = agg_dict

                # 🔮 GELECEK TAHMİNİ (FORECASTING) HESAPLAMA
                if forecast_steps > 0 and y_cols and len(grouped) >= 3:
                    try:
                        primary_y = y_cols[0]
                        y_vals = np.array(agg_dict[primary_y], dtype=float)
                        x_indices = np.arange(len(y_vals))
                        
                        slope, intercept, r_value, p_value, std_err = sp_stats.linregress(x_indices, y_vals)
                        
                        future_indices = np.arange(len(y_vals), len(y_vals) + forecast_steps)
                        forecast_y = (slope * future_indices + intercept).tolist()
                        
                        if pd.isna(std_err) or np.isinf(std_err):
                            ci = np.zeros(len(future_indices))
                        else:
                            ci = 1.96 * std_err * np.sqrt(1 + 1/len(y_vals) + (future_indices - np.mean(x_indices))**2 / np.sum((x_indices - np.mean(x_indices))**2))
                        
                        future_x = [f"+{i+1}. Dönem" for i in range(forecast_steps)]
                        
                        response_data['forecast'] = {
                            'target_y': primary_y,
                            'x': [agg_dict['__x__'][-1]] + future_x,
                            'y': [float(y_vals[-1])] + [float(max(0, val)) for val in forecast_y],
                            'upper': [float(y_vals[-1])] + [float(max(0, val + err)) for val, err in zip(forecast_y, ci)],
                            'lower': [float(y_vals[-1])] + [float(max(0, val - err)) for val, err in zip(forecast_y, ci)],
                            'r2': float(r_value**2)
                        }
                    except Exception as fe:
                        print("Tahmin hatası:", fe)

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
                        adv_info['correlation'] = float(r_value)
                        adv_info['r_squared'] = float(r_value**2)
                        adv_info['regression'] = f"y = {slope:.4f}x + {intercept:.4f}"
                        adv_info['p_value'] = float(p_value)
                        adv_info['type'] = 'numeric'
                    except Exception:
                        pass
                else:
                    groups = [group[y_col].values for name, group in valid_df.groupby(x_col) if len(group) > 0]
                    if len(groups) == 2:
                        try:
                            t_stat, p_val = sp_stats.ttest_ind(groups[0], groups[1], equal_var=False)
                            adv_info['t_test_stat'] = float(t_stat) if pd.notnull(t_stat) else None
                            adv_info['p_value'] = float(p_val) if pd.notnull(p_val) else None
                            adv_info['type'] = 'categorical_2'
                        except Exception:
                            pass
                    elif len(groups) > 2:
                        try:
                            f_stat, p_val = sp_stats.f_oneway(*groups)
                            adv_info['anova_f'] = float(f_stat) if pd.notnull(f_stat) else None
                            adv_info['p_value'] = float(p_val) if pd.notnull(p_val) else None
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
    valid_rows = [r for r in rows if r in active_df.columns]
    valid_cols = [c for c in cols if c in active_df.columns]
    valid_values = [v for v in values if v in active_df.columns and pd.api.types.is_numeric_dtype(active_df[v])]

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


if __name__ == '__main__':
    app.run(debug=True)
