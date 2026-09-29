<div align="center">

# 📊 DataViz — Büyük Veri, Görselleştirme, AI Güven Skoru ve İstatistik Analiz Stüdyosu

**100 Milyon+ Satırlık Veriyi Saniyeler İçinde Yükleyin, Güven Skorunu Ölçün, Onarın, Görselleştirin ve Raporlayın**

<p align="center">
  Geleneksel tablo yazılımlarının satır sınırlarını ve karmaşık kodlama süreçlerini geride bırakın.<br>
  <strong>DataViz</strong>; Excel (<code>.xlsx</code>), CSV, Apache Parquet (<code>.parquet</code>) dosyalarınızı ve <strong>SQL veritabanlarınızı</strong> sürükleyip bırakarak anında analiz etmenizi sağlayan, <strong>Polars</strong>, <strong>PyArrow</strong>, <strong>SciPy</strong> ve <strong>Scikit-Learn</strong> tabanlı yeni nesil bir kurumsal BI, veri kalitesi ve bilimsel istatistik platformudur.<br><br>
  PyArrow <em>Zero-Copy</em> bellek mimarisi, sütun izdüşümü (<em>Column Projection</em>), <strong>AI Veri Güvenilirlik Stüdyosu</strong> ve vektörize <strong>Data Healer</strong> motoru sayesinde <strong>5M – 100M+ satırlık</strong> devasa veri setlerini saniyeler içinde işler. Tüm analizler <strong>%100 yerel bilgisayarınızda</strong> çalışır — verileriniz asla buluta veya üçüncü parti sunuculara gönderilmez.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Veri_Motoru-Polars_%2B_PyArrow-38bdf8?style=for-the-badge&logo=polars&logoColor=white" alt="Polars">
  <img src="https://img.shields.io/badge/AI_Kalite-Güven_Skoru_Stüdyosu-10b981?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="AI Trust Score">
  <img src="https://img.shields.io/badge/Grafikler-Plotly_50%2B_Tür-3b82f6?style=for-the-badge&logo=plotly&logoColor=white" alt="Plotly">
  <img src="https://img.shields.io/badge/İstatistik-SciPy_1.11%2B-8b5cf6?style=for-the-badge&logo=scipy&logoColor=white" alt="SciPy">
  <img src="https://img.shields.io/badge/Testler-25%2F25_E2E_Başarılı-22c55e?style=for-the-badge&logo=pytest&logoColor=white" alt="Tests">
  <img src="https://img.shields.io/badge/Gizlilik-100%25_Yerel_Çalışma-ff4500?style=for-the-badge&logo=shield&logoColor=white" alt="Local">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Lisans-MIT-yellow?style=for-the-badge" alt="MIT">
</p>

</div>

---

## 🖼️ Ekran Görüntüleri (v3.2 Güncel Sürüm)

### 1. Karşılama Ekranı ve Canlı İstatistik Önizlemesi
<p align="center">
  <img src="docs/images/landing.png" alt="DataViz Karşılama Ekranı" width="920">
</p>

### 2. Aşamalı Canlı Yükleme & İşlem Çubuğu (`DataVizProgress`)
> Dosya yükleme, PyArrow tablo ayrıştırma, veri sağlığı taraması ve sütun onarımı sırasında adım adım ilerleme yüzdesini (`%`), aktif aşamayı ve geçen süreyi canlı gösterir.
<p align="center">
  <img src="docs/images/upload_progress.png" alt="DataViz Aşamalı Yükleme Barı" width="920">
</p>

### 3. Veri Sağlığı & Akıllı Tip Onarıcı (`Data Healer`)
> Sayısal sütunlara karışmış `₺14.250,50`, `4.2 kg`, `1.9 lt`, `binikiyüz`, `Bilinmiyor`, `Boş`, `Yok` gibi sözel/bozuk hücreleri otomatik tespit eder ve milyonlarca satırlık veri setlerinde bile tek tıkla sayısal tipe onarır.
<p align="center">
  <img src="docs/images/data_healer.png" alt="DataViz Veri Sağlığı ve Akıllı Tip Onarıcı" width="920">
</p>

### 4. 🤖 AI Veri Güvenilirlik ve Kalite Stüdyosu (`Trust Studio`)
> **Temizlenmemiş (Ham) Veri Seti** ile **Temizlenmiş / Onarılmış Veri Seti** güven skorlarını (`0–100`) yan yana karşılaştırır; 4 boyutlu ağırlıklı kalite kırılımını (`Eksiksizlik %35`, `Tip Doğruluğu %30`, `Aykırı Değer %20`, `Tekillik %15`) ve **Sütun Bazlı Güven Karnesini** tam ekran stüdyoda sunar.
<p align="center">
  <img src="docs/images/trust_studio.png" alt="DataViz AI Veri Güvenilirlik ve Kalite Stüdyosu" width="920">
</p>

### 5. Sürükle-Bırak Veri Havuzu ve Akıllı Grafik Öneri Motoru (50+ Grafik Türü)
<p align="center">
  <img src="docs/images/analysis.png" alt="DataViz Eksen Seçimi ve 50+ Grafik Galerisi" width="920">
</p>

### 6. İnteraktif Grafik ve Özelleştirme Stüdyosu
<p align="center">
  <img src="docs/images/studio_step3.png" alt="DataViz Grafik Stüdyosu" width="920">
</p>

### 7. Yatay İstatistik Kartları, Hipotez Testleri (ANOVA / T-Testi) & Akademik Yorumlayıcı
> Tam genişlikli yatay istatistik kartları ile merkezi eğilim metriklerini, Tek Yönlü ANOVA / T-Testi sonuçlarını ve sadeleştirilmiş yönetici özetini tek bakışta sunar.
<p align="center">
  <img src="docs/images/stats_horizontal.png" alt="DataViz Yatay İstatistik ve Hipotez Analizi" width="920">
</p>

### 8. Bilimsel Korelasyon & Regresyon Laboratuvarı
> Doğrusal, Polinom, Logaritmik ve Üstel regresyon eğrilerini **%95 Güven Aralığı Bandı**, korelasyon ısı haritası matrisi ve sadeleştirilmiş yatay model özeti ile birlikte görselleştirir.
<p align="center">
  <img src="docs/images/regression.png" alt="DataViz Korelasyon ve Regresyon Stüdyosu" width="920">
</p>

### 9. Sürükle-Bırak Pivot Matris & Isı Haritası Stüdyosu
<p align="center">
  <img src="docs/images/pivot_studio.png" alt="DataViz Pivot Matris Stüdyosu" width="920">
</p>

---

## 🎯 DataViz Nedir ve Nasıl Çalışır?

DataViz, teknik veya kodlama bilgisi gerektirmeden **3 basit adımda** uçtan uca veri analizi ve veri kalitesi denetimi yapmanızı sağlar:

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  1️⃣ YÜKLE & GÜVEN ÖLÇ     2️⃣ YAPILANDIR & KEŞFET       3️⃣ ANALİZ & RAPORLA │
│                                                                            │
│  • CSV / Excel / Parquet  • Sütunları X/Y Eksenine     • 50+ İnteraktif    │
│    veya SQL sorgusu çekin   sürükleyip bırakın           Grafik & Çoklu    │
│  • AI Güven Skoru ile     • Akıllı Öneri Motoru en       Pano (Dashboard)  │
│    Ham vs Temizlenmiş       uygun grafikleri önerir    • Yatay İstatistik  │
│    veri kalitesini görün  • Dinamik Dilimleyiciler,      Kartları, ANOVA,  │
│  • Data Healer ile tüm      Formül Sihirbazı ve          T-Testi, Regresyon│
│    bozulmaları onarın       Çoklu Tablo Birleştirme    • A4 PDF & Parquet  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Temel Özellikler

| Modül | Özellik | Ne İşe Yarar? |
|---|---|---|
| 🚀 **Büyük Veri Motoru** | **Polars + PyArrow Zero-Copy & Sütun İzdüşümü** | 5 GB'a kadar dosya yükleme desteği; PyArrow zero-copy ile **5M satırı ~0.66 saniyede**, **100M satırı ~62 saniyede** yükler. Yalnızca seçili X/Y sütunlarını işleyerek belleği optimize eder. |
| 🛡️ **AI Güven Skoru Stüdyosu** | **Ham vs Temizlenmiş Veri Karşılaştırması & Sütun Karnesi** | Veri setinin ilk yüklenen **Ham (Temizlenmemiş)** hali ile **Temizlenmiş** halini 4 boyutlu ağırlıklı formülle (`0–100`) yan yana kıyaslar; sütun bazlı karne ve *Isolation Forest* tabanlı satır bazlı anomali skoru üretir. |
| ⚡ **Aşamalı İlerleme Barı** | **Canlı İşlem Takibi (`DataVizProgress`)** | Veri yükleme, tip onarımı, grafik çizimi ve regresyon hesaplamalarında canlı yüzde (`%`), aktif alt aşama rozetleri ve geçen süre sayacı sunar. |
| 🩺 **Data Healer** | **Akıllı Veri ve Tip Onarıcı** | Sayısal sütunlara karışmış `₺5.200`, `1.250.000`, `120kg`, `1.9 lt`, `binikiyüz`, `Boş`, `Yok`, `N/A` gibi ifadeleri tespit eder ve tek geçişli NumPy lookup ile anında sayısal tipe dönüştürür. |
| 🗄️ **SQL Bağlantısı** | **Canlı Veritabanı Sorgulama (`SQLAlchemy`)** | PostgreSQL, MySQL, SQLite ve SQL Server veritabanlarına doğrudan bağlanarak `SELECT` sorgularını tek tıkla analiz stüdyosuna aktarır. |
| 📊 **Grafik Stüdyosu** | **50+ İnteraktif Plotly.js Grafiği** | Çubuk, Çizgi, Alan, Dağılım (Scatter), Kutu (Box), Keman (Violin), Halter (Dumbbell), Lolipop, Kadran (Gauge), Radyal Çubuk, Sunburst, Treemap, 3D Yüzey ve Finans (Mum/OHLC) grafikleri. |
| 📈 **İstatistik Laboratuvarı** | **Yatay İstatistik Kartları & Hipotez Testleri** | Tek Yönlü ANOVA ($F$-testi), Bağımsız Örneklem T-Testi ($p$-değeri), çeyreklikler (IQR), standart sapma ve sadeleştirilmiş Akademik Yorumlayıcı. |
| 🔬 **Regresyon Stüdyosu** | **Korelasyon & Regresyon Analizi** | Pearson ($r$), Spearman ($\rho$) ve Kendall ($\tau$) korelasyon matrisi; Doğrusal, Polinom (2. ve 3. derece), Logaritmik ve Üstel regresyon modelleri + **%95 Güven Aralığı Bandı**. |
| 🔀 **Pivot Stüdyosu** | **Dinamik Matris & Isı Haritası** | Excel benzeri sürükle-bırak Satır/Sütun/Değer pivot tablo oluşturucu, çakışan boyut koruması, koşullu ısı haritası (Heatmap) renklendirmesi ve tek tıkla Excel çıktısı. |
| 🧮 **Formül Sihirbazı** | **Hesaplanmış Sütunlar** | Mevcut sütunlar arasında dört işlem (`+`, `-`, `*`, `/`) veya sabit katsayı (ör. KDV hesaplama) ile anında yeni sütunlar üretir. |
| 🔗 **Veri Birleştirme** | **Çoklu Tablo Birleştirme (SQL Join)** | İkinci bir Excel/CSV/Parquet dosyasını ortak anahtar sütun üzerinden `Inner`, `Left`, `Right` veya `Outer` Join (anahtar koruma ve sütun tekilleştirme destekli) ile ana veriye bağlar. |
| 📄 **A4 PDF & Dışa Aktarma** | **Kurumsal Raporlama** | Panoya sabitlenen (Pin) grafikleri ve yönetici özetlerini sayfa bölünme korumalı **A4 PDF** raporuna dönüştürür; veriyi `.parquet`, `.xlsx` veya `.csv` olarak indirir. |

---

## 🛡️ AI Veri Güven Skoru Nasıl Hesaplanır?

DataViz içindeki **🤖 AI Güven Skoru Stüdyosu**, veri setinizi 4 temel veri kalitesi boyutunda inceler ve **Temizlenmemiş (Ham)** veri seti ile **Temizlenmiş** veri seti arasındaki kalite farkını şeffaf biçimde raporlar:

| Kalite Boyutu | Ağırlık | Neyi Ölçer? | Onarım / Temizlik Etkisi |
|---|---|---|---|
| **📊 Eksiksizlik (Completeness)** | **%35** | Hücre ve satır bazında boş (`NaN` / `Null`) veri yoğunluğu ve eksik veri içeren sütun oranı | Sütun bazlı veya tüm tablo genelinde Ortalama / Medyan / Mod / Sıfır ikamesi ile **%100**'e ulaşır |
| **🔤 Tip Doğruluğu (Type Validity)** | **%30** | Sayısal sütunlara karışmış sözel/bozuk ifadeler (`"binikiyüz"`, `"1500 TL"`, `"yok"`, `"belirsiz"`) | **Data Healer** (`smart_heal`) ile tüm sözel ekler ve yazılı sayılar temizlenerek **%100**'e ulaşır |
| **📈 İstatistiksel Tutarlılık (Outlier)** | **%20** | Sayısal sütunlarda `IQR` ($Q_1 - 1.5 \times \text{IQR}$ ve $Q_3 + 1.5 \times \text{IQR}$) dışına taşan uç değer oranı | Veri dağılımındaki aşırı sapmaları sütun bazında raporlar + *Isolation Forest* ile satır bazlı skorlar |
| **🧬 Tekillik (Uniqueness)** | **%15** | Veri setindeki birebir kopya (mükerrer) satır oranı | Global temizlik veya tek tıkla onarım sırasında mükerrer kayıtlar kaldırılarak **%100**'e ulaşır |

---

## 🩺 Akıllı Veri Onarıcı (Data Healer) Neleri Düzeltebilir?

Ham Excel, CSV veya Parquet dosyalarındaki kirli verileri analiz öncesinde otomatik olarak temizler:

| Bozuk Veri Türü | Ham Örnek | Onarım Sonrası |
|---|---|---|
| **Para Birimi & Semboller** | `₺14.250,50`, `$1,250.50`, `€800`, `8.900 TL` | `14250.5`, `1250.5`, `800.0`, `8900.0` |
| **Ağırlık, Hacim & Ölçü Birimleri** | `4.2 kg`, `1.9 lt`, `850 gr`, `45 adet`, `300m²` | `4.2`, `1.9`, `850.0`, `45.0`, `300.0` |
| **Binlik ve Ondalık Ayraçlar** | `1.250.000` veya `1.250,75` | `1250000.0` / `1250.75` |
| **Yazıyla Yazılmış Sayılar & Yüzdeler** | `binikiyüz`, `üçbin`, `sıfır`, `%85`, `42%` | `1200.0`, `3000.0`, `0.0`, `85.0`, `42.0` |
| **Sözel Eksik Değerler** | `Boş`, `Yok`, `Bilinmiyor`, `Belirtilmemiş`, `N/A`, `-` | `NaN` (Ortalama/Medyan/Sıfır ile anında ikame edilir) |

---

## ⚡ Hızlı Başlangıç (Kurulum)

### Seçenek 1: Windows'ta Tek Tıkla Başlatma (Önerilen)

Proje ana dizinindeki [`DEMO_BASLAT.bat`](DEMO_BASLAT.bat) dosyasına çift tıklayın. Sunucu otomatik olarak başlayacak ve tarayıcınızda `http://127.0.0.1:5000` adresini açacaktır.

### Seçenek 2: Terminal / Manuel Kurulum

```bash
# 1. Depoyu klonlayın ve klasöre girin
git clone https://github.com/UmutcaNN00/dataviz.git
cd dataviz

# 2. Sanal ortam oluşturun ve bağımlılıkları yükleyin (uv veya pip ile)
pip install -r requirements.txt

# 3. Uygulamayı başlatın
python app.py

# 4. Tarayıcınızda açın:
# http://127.0.0.1:5000
```

### Seçenek 3: Docker ile Çalıştırma

```bash
docker compose up -d --build
# Tarayıcıda: http://localhost:5000
```

---

## 🏗️ Proje Mimarisi

```text
dataviz/
│
├── app.py                          # Flask uygulama fabrikası ve JSON serileştirici (NaN/Inf korumalı)
├── requirements.txt                # Python bağımlılıkları (Flask, Polars, PyArrow, SciPy, Scikit-Learn, SQLAlchemy)
├── DEMO_BASLAT.bat                 # Windows için tek tıkla başlatıcı
├── Dockerfile                      # Docker konteyner tanımı
├── docker-compose.yml              # Docker Compose servis yapılandırması
├── test_system_connectivity.py     # 25 adımlı uçtan uca (E2E) master entegrasyon test paketi
├── generate_100m_dataset.py        # 100M satır × 22 sütun gerçekçi kirli Parquet veri seti üreteci
│
├── core/                           # Çekirdek Yapılandırma ve Bellek Yönetimi
│   ├── config.py                   # Yükleme limitleri (5 GB), örnekleme eşikleri ve dizin ayarları
│   └── store.py                    # Oturum (Session) bazlı LRU bellek içi veri deposu ve baseline güven durumu
│
├── routes/                         # Modüler Flask Blueprint Uç Noktaları
│   ├── main_routes.py              # GET / (Karşılama), /analysis (Stüdyo), /health, POST /load_sample
│   ├── upload_routes.py            # POST /upload (CSV/Excel/Parquet), /switch_sheet, /fetch_sql (SQLAlchemy)
│   ├── data_routes.py              # /check_health, /repair_column_anomalies, /clean_data, /merge_datasets,
│   │                               # /get_trust_report, /auto_heal_all_trust, /calculate_risk_score
│   ├── chart_routes.py             # POST /get_chart_data (Sütun izdüşümlü), /get_column_unique_values
│   ├── stats_routes.py             # /get_stats, /get_kpi_summary, /get_correlation_matrix, /get_regression_studio_data
│   └── export_routes.py            # /export_data (CSV/Excel/Parquet), /export_pivot_excel
│
├── services/                       # İş Mantığı ve Veri İşleme Katmanı
│   ├── file_service.py             # Polars/PyArrow destekli hızlı dosya okuma, sayfa izolasyonu ve tip optimizasyonu
│   ├── data_healer.py              # Bozuk sayısal sütun tespiti, birim/para birimi temizleme ve sütun bazlı NaN onarımı
│   ├── stats_service.py            # SciPy tabanlı ANOVA, T-Testi, Korelasyon, Regresyon (%95 CI) ve Pivot motoru
│   ├── ai_service.py               # İstatistiksel bulguları sade ve anlaşılır yönetici diline çeviren yorumlayıcı
│   └── export_service.py           # Polars/PyArrow hızlandırmalı Parquet, Excel ve CSV dışa aktarma servisi
│
├── static/                         # İstemci (Frontend) Dosyaları
│   ├── css/
│   │   ├── landing.css             # Karşılama sayfası stilleri
│   │   └── analysis.css            # Analiz stüdyosu, yatay istatistik kartları ve aşamalı yükleme barı stilleri
│   └── js/
│       ├── app.js                  # Ana uygulama koordinatörü, AI Güven Stüdyosu, SQL bağlantı ve XHR yükleme takibi
│       └── modules/
│           ├── globals.js          # Paylaşılan uygulama durumu (State) ve DataVizProgress yükleme barı motoru
│           ├── charts_config.js    # 50+ Plotly grafik şablonu ve drawMegaPlotly() çizim motoru
│           ├── chart_manager.js    # Sürükle-bırak eksen havuzu, yatay istatistik kartları ve öneri motoru
│           ├── dashboard_studio.js # KPI kartları, Çoklu Pano (Dashboard Grid) ve sabitlenen grafikler
│           ├── data_prep.js        # Data Healer arayüzü, tip onarımı ve eksik veri temizleme modalı
│           ├── pivot_studio.js     # Sürükle-bırak Pivot Matris Stüdyosu
│           ├── regression_studio.js# Korelasyon matrisi ve Regresyon Stüdyosu kontrolcüsü
│           ├── join_modal.js       # İkinci dosya önizleme ve SQL Join birleştirme modalı
│           └── pdf_studio.js       # Etkileşimli A4 PDF Rapor Stüdyosu
│
├── templates/                      # HTML Şablonları
│   ├── landing.html                # Karşılama ve canlı istatistik tanıtım sayfası
│   └── analysis.html               # Çok ekranlı Analiz, Pivot ve AI Güven Skoru Stüdyosu
│
└── docs/images/                    # Güncel uygulama ekran görüntüleri (9 adet)
```

---

## 🧪 Test Paketi (25/25 Master Entegrasyon Testi)

Tüm backend uç noktalarının, AI Güven Skoru hesaplamalarının, çoklu sayfa bellek izolasyonunun, `Outer/Right` Join anahtar korumasının ve modüller arası veri sözleşmelerinin sağlamlığını doğrulamak için **25 adımlı** entegrasyon test paketini çalıştırabilirsiniz:

```bash
python test_system_connectivity.py
```

---

## 🏎️ Performans Benchmark (5 Milyon & 100 Milyon Satır)

DataViz, PyArrow zero-copy ve tek geçişli kategorik NumPy indeksleme ile hem orta-büyük (5M) hem de ekstrem (100M) veri setlerini yüksek hızda işler:

| Metrik | 5 Milyon Satır × 20 Sütun | 100 Milyon Satır × 22 Sütun |
|---|---|---|
| **Toplam Hücre Sayısı** | 100.000.000 hücre | 2.200.000.000 hücre |
| **Parquet Boyutu (ZSTD)** | **145.18 MB** | **4.20 GB** |
| **PyArrow Zero-Copy Okuma Süresi** | **~0.66 saniye** | **~62.5 saniye** |
| **AI Güven Skoru & Karne Hesabı** | **~0.79 saniye** | **~1.15 saniye** (Akıllı Örnekleme) |
| **Tam Veri Seti Onarım & Temizlik** | **~2.08 saniye** | **~0.09 sn / kategorik sütun** (`float32` lookup) |

> 💡 [`generate_100m_dataset.py`](generate_100m_dataset.py) betiği ile kendi 100M satırlık test veri setinizi üretebilirsiniz.

---

## 🔒 Gizlilik & Sistem Gereksinimleri

- **%100 Yerel Mimari:** Yüklediğiniz hiçbir veri seti internet üzerinden herhangi bir sunucuya gönderilmez.
- **Python Sürümü:** Python `3.10+` (`3.14` dahil tam uyumlu)
- **Önerilen Bellek (RAM):** Standart dosyalar ve 5M satırlık Parquet setleri için 4 GB RAM; 50M–100M+ satırlık `.parquet` dosyaları için 8–16 GB RAM önerilir.

---

## 📜 Lisans

Bu proje **MIT Lisansı** altında lisanslanmıştır.

<div align="center">
  <br>
  <b>Geliştirici:</b> <a href="https://github.com/UmutcaNN00">Umutcan</a> &copy; 2026 — <b>DataViz Analiz Stüdyosu</b><br>
  <i>Polars ⚡ + PyArrow 🏹 + SciPy 🔬 + Scikit-Learn 🤖 + Plotly.js 📊 ile güçlendirilmiştir.</i>
</div>
