<div align="center">

# 📊 DataViz — Büyük Veri ve İstatistik Analiz Stüdyosu

**Milyonlarca Satırlık Veriyi Saniyeler İçinde Keşfedin, Onarın, Görselleştirin ve Raporlayın**

<p align="center">
  Geleneksel tablo yazılımlarının satır sınırlarını ve karmaşık kodlama süreçlerini geride bırakın.<br>
  <strong>DataViz</strong>; Excel (<code>.xlsx</code>), CSV ve Apache Parquet (<code>.parquet</code>) dosyalarınızı sürükleyip bırakarak anında analiz etmenizi sağlayan, <strong>Polars</strong> ve <strong>SciPy</strong> tabanlı yeni nesil bir veri görselleştirme ve bilimsel istatistik platformudur.<br><br>
  Sütun izdüşümü (<em>Column Projection</em>) ve vektörize Polars motoru sayesinde <strong>10M – 100M+ satırlık</strong> devasa veri setlerini saniyeler içinde işler. Tüm analizler <strong>%100 yerel bilgisayarınızda</strong> çalışır — verileriniz asla buluta veya üçüncü parti sunuculara gönderilmez.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Veri_Motoru-Polars_%2B_PyArrow-38bdf8?style=for-the-badge&logo=polars&logoColor=white" alt="Polars">
  <img src="https://img.shields.io/badge/Grafikler-Plotly_50%2B_Tür-3b82f6?style=for-the-badge&logo=plotly&logoColor=white" alt="Plotly">
  <img src="https://img.shields.io/badge/İstatistik-SciPy_1.11%2B-10b981?style=for-the-badge&logo=scipy&logoColor=white" alt="SciPy">
  <img src="https://img.shields.io/badge/Gizlilik-100%25_Yerel_Çalışma-ff4500?style=for-the-badge&logo=shield&logoColor=white" alt="Local">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.x-black?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/Lisans-MIT-yellow?style=for-the-badge" alt="MIT">
  <img src="https://img.shields.io/badge/TÜBİTAK-2209--A_Projesi-e11d48?style=for-the-badge" alt="TÜBİTAK 2209-A">
</p>

</div>

---

## 🖼️ Ekran Görüntüleri (Güncel Sürüm)

### 1. Karşılama Ekranı ve Canlı İstatistik Önizlemesi
<p align="center">
  <img src="docs/images/landing.png" alt="DataViz Karşılama Ekranı" width="900">
</p>

### 2. Sürükle-Bırak Veri Havuzu ve Akıllı Grafik Öneri Motoru (50+ Grafik Türü)
<p align="center">
  <img src="docs/images/analysis.png" alt="DataViz Eksen Seçimi ve 50+ Grafik Galerisi" width="900">
</p>

### 3. İnteraktif Grafik ve Özelleştirme Stüdyosu
<p align="center">
  <img src="docs/images/studio_step3.png" alt="DataViz Grafik Stüdyosu" width="900">
</p>

### 4. Bilimsel Korelasyon & Regresyon Laboratuvarı
<p align="center">
  <img src="docs/images/regression.png" alt="DataViz Korelasyon ve Regresyon Stüdyosu" width="900">
</p>

---

## 🎯 DataViz Nedir ve Nasıl Çalışır?

DataViz, teknik veya kodlama bilgisi gerektirmeden **3 basit adımda** uçtan uca veri analizi yapmanızı sağlar:

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  1️⃣ YÜKLE & ONAR          2️⃣ YAPILANDIR & KEŞFET       3️⃣ ANALİZ & RAPORLA │
│                                                                            │
│  • CSV / Excel / Parquet  • Sütunları X/Y Eksenine     • 50+ İnteraktif    │
│    dosyanızı bırakın        sürükleyip bırakın           Grafik & Çoklu    │
│  • Data Healer ile bozuk  • Akıllı Öneri Motoru en       Pano (Dashboard)  │
│    sayıları ve eksik        uygun grafikleri önerir    • ANOVA, T-Testi,   │
│    verileri tek tıkla     • Dinamik Dilimleyiciler       Regresyon & R²    │
│    onarın                   ve Formül Sihirbazı        • A4 PDF & Parquet  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Temel Özellikler

| Modül | Özellik | Ne İşe Yarar? |
|---|---|---|
| 🚀 **Büyük Veri Motoru** | **Polars + PyArrow Zero-Copy & Sütun İzdüşümü** | 5 GB'a kadar dosya yükleme desteği; PyArrow zero-copy ile **100M satırı ~62 saniyede** yükler. Yalnızca seçili X/Y sütunlarını işleyerek belleği optimize eder. |
| 🩺 **Data Healer** | **Akıllı Veri ve Tip Onarıcı** | Sayısal sütunlara karışmış `₺5.200`, `1.250.000`, `120kg`, `%85`, `Yok`, `N/A` gibi bozuk ifadeleri otomatik tespit eder ve tek tıkla gerçek sayısal tipe dönüştürür. |
| 📊 **Grafik Stüdyosu** | **50+ İnteraktif Plotly.js Grafiği** | Çubuk, Çizgi, Alan, Dağılım (Scatter), Kutu (Box), Keman (Violin), Halter (Dumbbell), Lolipop, Kadran (Gauge), Radyal Çubuk, Sunburst, Treemap, 3D Yüzey ve Finans (Mum/OHLC) grafikleri. |
| 🔬 **Regresyon Stüdyosu** | **Korelasyon & Regresyon Analizi** | Pearson ($r$), Spearman ($\rho$) ve Kendall ($\tau$) korelasyon matrisi; Doğrusal, Polinom (2. ve 3. derece), Logaritmik ve Üstel regresyon modelleri + **%95 Güven Aralığı Bandı**. |
| 📈 **İstatistik Laboratuvarı** | **Hipotez Testleri & KPI Özeti** | Tek Yönlü ANOVA ($F$-testi), Bağımsız Örneklem T-Testi ($p$-değeri), çeyreklikler (IQR), çarpıklık ve standart sapma analizleri. |
| 🔀 **Pivot Stüdyosu** | **Dinamik Matris & Isı Haritası** | Excel benzeri sürükle-bırak Satır/Sütun/Değer pivot tablo oluşturucu, koşullu ısı haritası (Heatmap) renklendirmesi ve tek tıkla Excel çıktısı. |
| 🧮 **Formül Sihirbazı** | **Hesaplanmış Sütunlar** | Mevcut sütunlar arasında dört işlem (`+`, `-`, `*`, `/`) veya sabit katsayı (ör. KDV hesaplama) ile anında yeni sütunlar üretir. |
| 🔗 **Veri Birleştirme** | **Çoklu Tablo Birleştirme (SQL Join)** | İkinci bir Excel/CSV/Parquet dosyasını ortak anahtar sütun üzerinden `Inner`, `Left`, `Right` veya `Outer` Join ile ana veriye bağlar. |
| 📄 **A4 PDF & Dışa Aktarma** | **Kurumsal Raporlama** | Panoya sabitlenen (Pin) grafikleri ve yönetici özetlerini sayfa bölünme korumalı **A4 PDF** raporuna dönüştürür; veriyi `.parquet`, `.xlsx` veya `.csv` olarak indirir. |

---

## ⚡ Hızlı Başlangıç (Kurulum)

### Seçenek 1: Windows'ta Tek Tıkla Başlatma (Önerilen)

Proje ana dizinindeki [`UYGULAMAYI_BASLAT.bat`](UYGULAMAYI_BASLAT.bat) veya `dataviz/` içindeki [`DEMO_BASLAT.bat`](DEMO_BASLAT.bat) dosyasına çift tıklayın. Sunucu otomatik olarak başlayacak ve tarayıcınızda `http://127.0.0.1:5000` adresini açacaktır.

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
├── app.py                          # Flask uygulama giriş noktası ve JSON serileştirici (NaN/Inf korumalı)
├── requirements.txt                # Python bağımlılıkları (Flask, Polars, PyArrow, SciPy, Pandas, NumPy)
├── DEMO_BASLAT.bat                 # Windows için tek tıkla başlatıcı
├── Dockerfile                      # Docker konteyner tanımı
├── docker-compose.yml              # Docker Compose çoklu servis yapılandırması
├── test_system_connectivity.py     # 19 adımlı uçtan uca (E2E) entegrasyon test paketi
├── generate_100m_dataset.py        # 100M satır × 22 sütun gerçekçi kirli Parquet veri seti üreteci
├── generate_academic_tubitak_report.py  # 14 sayfalık TÜBİTAK 2209-A akademik PDF rapor üreteci
├── pyrightconfig.json              # Pylance/Pyright tip denetimi yapılandırması
├── GEMINI.md                       # AI asistan çalışma alanı kuralları
│
├── .agents/skills/                 # Yeniden Kullanılabilir AI Skill Tanımları
│   ├── dataviz-architecture/       # Proje mimarisi ve konvansiyonlar
│   ├── massive-dataset-optimization/  # 100M+ satır PyArrow/Parquet optimizasyonu
│   ├── tubitak-2209a-report/       # TÜBİTAK 2209-A PDF rapor üretim rehberi
│   └── vscode-ide-diagnostics/     # VS Code Pylance/Ruff diagnostik çözümleri
│
├── core/                           # Çekirdek Yapılandırma ve Bellek Yönetimi
│   ├── config.py                   # Yükleme limitleri (5 GB), izin verilen uzantılar ve dizin ayarları
│   └── store.py                    # Oturum (Session) bazlı LRU bellek içi veri deposu ve GC yönetimi
│
├── routes/                         # Modüler Flask Blueprint Uç Noktaları
│   ├── main_routes.py              # GET / (Karşılama), /analysis (Stüdyo), /health, POST /load_sample
│   ├── upload_routes.py            # POST /upload (CSV/Excel/Parquet), /select_sheet
│   ├── data_routes.py              # /check_health, /repair_column_anomalies, /clean_data, /merge_datasets
│   ├── chart_routes.py             # POST /get_chart_data (Sütun izdüşümlü), /get_column_unique_values
│   ├── stats_routes.py             # /get_stats, /get_kpi_summary, /get_correlation_matrix, /get_regression_studio_data
│   └── export_routes.py            # /export_data (CSV/Excel/Parquet), /export_pivot_excel
│
├── services/                       # İş Mantığı ve Veri İşleme Katmanı
│   ├── file_service.py             # Polars/PyArrow destekli hızlı dosya okuma ve tip optimizasyonu
│   ├── data_healer.py              # Bozuk sayısal sütun tespiti, birim/para birimi temizleme ve NaN onarımı
│   ├── stats_service.py            # SciPy tabanlı ANOVA, T-Testi, Korelasyon, Regresyon (%95 CI) ve Pivot motoru
│   ├── ai_service.py               # İstatistiksel bulguları akademik ve yönetici diline çeviren hibrit yorumlayıcı
│   └── export_service.py           # Polars/PyArrow hızlandırmalı Parquet, Excel ve CSV dışa aktarma servisi
│
├── static/                         # İstemci (Frontend) Dosyaları
│   ├── css/
│   │   └── analysis.css            # Analiz stüdyosu, Pivot ve PDF stüdyosu stilleri
│   └── js/
│       ├── app.js                  # Ana uygulama koordinatörü, dosya yükleme ve kısayol yöneticisi
│       └── modules/
│           ├── globals.js          # Paylaşılan uygulama durumu (State)
│           ├── charts_config.js    # 50+ Plotly grafik şablonu ve drawMegaPlotly() çizim motoru
│           ├── chart_manager.js    # Sürükle-bırak eksen havuzu, filtreler ve öneri motoru
│           ├── dashboard_studio.js # KPI kartları, Çoklu Pano (Dashboard Grid) ve sabitlenen grafikler
│           ├── data_prep.js        # Data Healer arayüzü, dilimleyiciler ve formül sihirbazı
│           ├── pivot_studio.js     # Sürükle-bırak Pivot Matris Stüdyosu
│           ├── regression_studio.js# Korelasyon matrisi ve Regresyon Stüdyosu kontrolcüsü
│           ├── join_modal.js       # İkinci dosya önizleme ve SQL Join birleştirme modalı
│           └── pdf_studio.js       # Etkileşimli A4 PDF Rapor Stüdyosu
│
├── templates/                      # HTML Şablonları
│   ├── landing.html                # Karşılama ve canlı istatistik tanıtım sayfası
│   └── analysis.html               # 3 adımlı ana Analiz Stüdyosu
│
└── docs/images/                    # README ekran görüntüleri
```

---

## 🩺 Akıllı Veri Onarıcı (Data Healer) Neleri Düzeltebilir?

Ham Excel veya CSV dosyalarındaki kirli verileri analiz öncesinde otomatik olarak temizler:

| Bozuk Veri Türü | Ham Örnek | Onarım Sonrası |
|---|---|---|
| **Para Birimi & Semboller** | `₺5.200`, `$1,250.50`, `€800` | `5200.0`, `1250.5`, `800.0` |
| **Bitişik Ölçü Birimleri** | `120kg`, `45 adet`, `300m²` | `120.0`, `45.0`, `300.0` |
| **Binlik ve Ondalık Ayraçlar** | `1.250.000` veya `1.250,75` | `1250000.0` / `1250.75` |
| **Yüzde İfadeleri** | `%85`, `42%` | `85.0`, `42.0` |
| **Sözel Eksik Değerler** | `Yok`, `Bilinmiyor`, `Belirtilmemiş`, `N/A`, `-` | `NaN` (Ortalama/Medyan/Mod ile doldurulabilir) |

---

## 🧪 Test Paketi

Tüm backend uç noktalarının ve modüller arası veri sözleşmelerinin sağlamlığını doğrulamak için entegrasyon test paketini çalıştırabilirsiniz:

```bash
python test_system_connectivity.py
```

---

## 🏎️ Performans Benchmark: 100 Milyon Satır

DataViz, PyArrow zero-copy ve kategorik sütun optimizasyonu ile devasa veri setlerini verimli biçimde işler:

| Metrik | Değer |
|--------|-------|
| **Veri Seti** | 100.000.000 satır × 22 sütun (2.2 milyar hücre) |
| **Parquet Boyutu** | 4.20 GB (ZSTD sıkıştırma) |
| **Yükleme Süresi** | ~62.5 saniye |
| **RAM Kullanımı** | ~6.35 GB |
| **Data Healer Hızlanması** | Kategorik sütun parse: ~1000x (`apply()` yerine NumPy indexing) |

> 💡 `generate_100m_dataset.py` betiği ile kendi 100M satırlık test veri setinizi üretebilirsiniz.

---

## 🎓 TÜBİTAK 2209-A Akademik Proje

DataViz, **TÜBİTAK 2209-A Üniversite Öğrencileri Araştırma Projeleri Destekleme Programı** kapsamında geliştirilmektedir.

Proje deposunda bulunan `generate_academic_tubitak_report.py` betiği ile **14 sayfalık akademik kalitede PDF rapor** otomatik olarak üretilebilir. Rapor içeriği:

- 📋 Projenin Özgün Değeri ve Literatür Karşılaştırması
- 🔬 Hipotezler (H₀ / H₁) ve SMART Hedefler
- 🏗️ 4 Katmanlı Teknik Mimari Açıklaması
- 📊 100M Satır Benchmark Sonuçları
- 📅 6 İş Paketi ve 12 Aylık Gantt Şeması
- ⚠️ Risk Analizi ve B Planı
- 🌍 Sürdürülebilir Kalkınma Amaçları (SKA 4 ve SKA 9)
- 💰 Kalem Bazlı Bütçe Tablosu
- 🎤 12 Soruluk Jüri Savunma Rehberi

---

## 🔒 Gizlilik & Sistem Gereksinimleri

- **%100 Yerel Mimari:** Yüklediğiniz hiçbir veri seti internet üzerinden herhangi bir sunucuya gönderilmez.
- **Python Sürümü:** Python `3.10+`
- **Önerilen Bellek (RAM):** Standart dosyalar için 4 GB RAM; 10M+ satırlık `.parquet` dosyaları için 8–16 GB RAM önerilir.

---

## 📜 Lisans

Bu proje **MIT Lisansı** altında lisanslanmıştır.

<div align="center">
  <br>
  <b>Geliştirici:</b> <a href="https://github.com/UmutcaNN00">Umutcan</a> &copy; 2026 — <b>DataViz Analiz Stüdyosu</b><br>
  <i>Polars ⚡ + PyArrow 🏹 + SciPy 🔬 + Plotly.js 📊 ile güçlendirilmiştir.</i>
</div>
