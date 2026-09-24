<div align="center">

# 📊 DataViz — Büyük Veri Analiz Stüdyosu

**Milyonlarca Satırlık Veriyi Saniyeler İçinde Keşfedin, Onarın ve Raporlayın**

<p align="center">
  Geleneksel tablo yazılımlarının sınırlarını aşın! <strong>DataViz</strong>; Excel, CSV ve Apache Parquet dosyalarınızı sürükleyip bırakarak anında analiz etmenizi sağlayan yeni nesil bir veri görselleştirme ve iş zekası (BI) platformudur.<br><br>
  <strong>Polars</strong> destekli hızlandırılmış veri motoru sayesinde 10 milyon satırlık devasa verileri milisaniyeler içinde işler. Tüm işlemler <strong>%100 yerel bilgisayarınızda</strong> gerçekleşir — verileriniz asla dışarı çıkmaz!
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Veri_Motoru-Polars_Hızlandırılmış-38bdf8?style=for-the-badge&logo=polars&logoColor=white" alt="Polars">
  <img src="https://img.shields.io/badge/Grafikler-Plotly_50+_Tür-3b82f6?style=for-the-badge&logo=plotly&logoColor=white" alt="Plotly">
  <img src="https://img.shields.io/badge/İstatistik-SciPy_Tabanlı-10b981?style=for-the-badge&logo=scipy&logoColor=white" alt="SciPy">
  <img src="https://img.shields.io/badge/Gizlilik-100%25_Yerel_Çalışma-ff4500?style=for-the-badge&logo=shield&logoColor=white" alt="Local">
  <img src="https://img.shields.io/badge/Lisans-MIT-yellow?style=for-the-badge" alt="MIT">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.x-black?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
</p>

</div>

<br>

<p align="center">
  <img src="docs/images/landing.png" alt="DataViz Karşılama Ekranı" width="800">
</p>
<p align="center">
  <img src="docs/images/analysis.png" alt="DataViz Analiz Stüdyosu" width="800">
</p>

---

## ✨ Öne Çıkan Özellikler

> 3 Adımda veri analizi: **Yükle → Yapılandır → Raporla**

| # | Özellik | Açıklama |
|---|---------|----------|
| 🚀 | **Polars + PyArrow Büyük Veri Motoru** | 10M+ satırlık CSV ve Parquet dosyalarını saniyeler içinde açar, bellek dostu Polars ile anında filtreler |
| 📊 | **50+ İnteraktif Plotly.js Grafiği** | Bar, Scatter, Heatmap, Sunburst, Treemap, 3D Yüzey, Candlestick ve daha fazlası |
| 🩺 | **Akıllı Veri Onarıcı (Data Healer)** | Sayısal sütunlardaki "TL", "₺", "Yok", "N/A" gibi bozuk değerleri otomatik tespit edip tek tıkla onarır |
| 🔬 | **Korelasyon & Regresyon Stüdyosu** | Pearson/Spearman/Kendall korelasyonu, Doğrusal/Polinom/Logaritmik/Üstel regresyon, %95 güven bandı |
| 🪄 | **Formül Sihirbazı** | Mevcut sütunlardan matematiksel ifadelerle yeni hesaplanmış sütunlar oluşturur |
| 🔗 | **Dosya Birleştirme (SQL Join)** | İki farklı veri seti arasında Inner/Left/Right/Outer join işlemi |
| 🔀 | **Dinamik Pivot Tablo Stüdyosu** | Excel benzeri sürükle-bırak pivot, Sum/Mean/Count/Min/Max toplamları ve ısı haritası renklendirmesi |
| 📋 | **Çoklu Gösterge Panosu** | Grafikleri ve pivot tabloları panoya sabitleyin (Pin), tek sayfada tüm yönetim |
| 📈 | **İleri Düzey İstatistik Laboratuvarı** | ANOVA (F-testi), Bağımsız Örneklem T-Testi, korelasyon matrisi, regresyon modelleri |
| 📄 | **Etkileşimli A4 PDF Rapor Stüdyosu** | html2pdf.js ile sayfa bölme korumalı, düzenlenebilir kurumsal PDF çıktısı |
| 📤 | **Çoklu Format Dışa Aktarma** | CSV, Excel (.xlsx) ve Parquet formatlarında filtrelenmiş veri indirme |
| 🤖 | **Yapay Zeka Yorumlayıcı** | İstatistik sonuçlarına akademik ve yönetici dostu otomatik yorum üretir |

---

## 🎯 3 Adımda Nasıl Çalışır?

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  1️⃣  YÜKLE & ONAR     2️⃣  YAPILANDIR & KEŞFET    3️⃣  RAPORLA  │
│                                                             │
│  CSV / Excel /  →→→   Sütun Seç, Filtre,  →→→  PDF / Excel │
│  Parquet Yükle        50+ Grafik, İstatistik    Dışa Aktar  │
│  Data Healer ile                                            │
│  Hataları Onar                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚡ Hızlı Başlangıç

### Windows (Tek Tıkla)

```
DEMO_BASLAT.bat dosyasına çift tıklayın → Tarayıcı otomatik açılır!
```

### Manuel Kurulum

```bash
# 1. Depoyu klonlayın
git clone https://github.com/kullaniciadi/dataviz.git
cd dataviz

# 2. Bağımlılıkları yükleyin (uv önerilir)
pip install uv
uv sync

# 3. Sunucuyu başlatın
uv run python app.py

# 4. Tarayıcıda açın
# http://127.0.0.1:5000
```

### Docker ile

```bash
docker compose up -d
# http://localhost:5000
```

---

## 🏗️ Mimari

```
dataviz/
│
├── app.py                        # Flask uygulama giriş noktası
│
├── core/
│   ├── config.py                 # Yapılandırma sabitleri
│   └── store.py                  # Oturum tabanlı bellek içi veri deposu
│
├── routes/                       # Flask Blueprint'leri
│   ├── main_routes.py            # GET / ve /analysis
│   ├── upload_routes.py          # POST /upload, /select_sheet
│   ├── data_routes.py            # /check_health, /repair_column_anomalies, /clean_data, /join_datasets
│   ├── chart_routes.py           # POST /get_chart_data, /get_column_unique_values
│   ├── stats_routes.py           # POST /get_stats, /get_kpi_summary, /get_correlation_matrix, /get_regression_studio_data
│   └── export_routes.py          # POST /export_data, /export_pivot
│
├── services/                     # İş Mantığı Katmanı
│   ├── file_service.py           # Polars/Pandas ile güvenli dosya okuma
│   ├── data_healer.py            # Anomali tespiti ve akıllı onarım
│   ├── stats_service.py          # ANOVA, T-Test, Korelasyon, Regresyon
│   ├── ai_service.py             # AI yorumlayıcı (kural tabanlı + LLM)
│   └── export_service.py         # Parquet, Excel, CSV dışa aktarma
│
├── static/
│   ├── css/
│   │   ├── analysis.css          # Ana analiz stüdyosu stilleri
│   │   └── landing.css           # Karşılama sayfası stilleri
│   └── js/
│       ├── modules/
│       │   ├── globals.js        # Paylaşılan durum ve global değişkenler
│       │   ├── charts_config.js  # 50+ grafik tanımları ve drawMegaPlotly()
│       │   ├── chart_manager.js  # Grafik grid, öneri motoru, eksen sürükle-bırak
│       │   ├── data_prep.js      # Data Healer modalı ve veri temizleme
│       │   ├── pivot_studio.js   # Pivot tablo stüdyosu
│       │   ├── pdf_studio.js     # A4 PDF önizleme ve dışa aktarma
│       │   ├── join_modal.js     # İkinci veri seti birleştirme modalı
│       │   └── regression_studio.js # Korelasyon & Regresyon Stüdyosu
│       └── app.js                # Ana koordinatör (~200 satır)
│
├── templates/
│   ├── landing.html              # Karşılama sayfası
│   └── analysis.html             # Analiz stüdyosu
│
├── uploads/                      # Yüklenen dosyalar (geçici)
├── docs/images/                  # README görselleri
├── DEMO_BASLAT.bat               # Windows tek tıkla başlatıcı
└── requirements.txt              # Python bağımlılıkları
```

---

## 📊 Desteklenen Grafik Türleri

<details>
<summary>Tüm 50+ grafik türünü görüntüle</summary>

**Trend & Karşılaştırma**
- Sütun Grafik, Çubuk Grafik, Çizgi Grafik, Alan Grafik, Çoklu Çizgi, Aşamalı Çizgi

**Dağılım & İlişki**
- Scatter Plot, Kabarcık Grafik, Yoğunluk Haritası, 2D Histogram

**İlişki Matrisi**
- Korelasyon Isı Haritası, Paralel Koordinatlar, Radar Grafik

**Parça-Bütün**
- Pasta Grafik, Halka Grafik, Treemap, Sunburst, Huni Grafik, Şelale Grafik

**İstatistiksel**
- Kutu Grafik (Box Plot), Keman Grafik (Violin), Histogram, ECDF

**3D & Bilimsel**
- 3D Scatter, 3D Yüzey, 3D Çizgi, Kontur Grafik, Çarpıklık Grafiği

**Zaman Serisi & Finans**
- Mum Grafiği (Candlestick), OHLC, Şelale Grafik

**Coğrafi & Diğer**
- Choropleth, Sankey Akış Diyagramı, Streamgraph, Beeswarm

</details>

---

## 🔬 Korelasyon & Regresyon Stüdyosu

Analiz stüdyosundaki **🔬 Korelasyon & Regresyon** sekmesinde:

- **Korelasyon Yöntemleri:** Pearson (r), Spearman (ρ), Kendall (τ)
- **Regresyon Modelleri:** Doğrusal, 2. Derece Polinom, 3. Derece Polinom, Logaritmik, Üstel
- **%95 Güven Bandı** ile scatter plot üzerinde regresyon eğrisi
- **Korelasyon Isı Haritası:** Tüm sayısal sütunlar arası matris (tıkla → anında X/Y seç)
- **Bento Metrik Şeridi:** r, R², p-değeri, Standart Hata, Denklem
- **PNG İndirme** ve **Panoya Sabitleme (Pin)**
- **Klavye Kısayolu:** `R` tuşu ile hızlı erişim

---

## 🩺 Akıllı Veri Onarıcı (Data Healer)

Veri sağlığı sorunlarını otomatik tespit eder:

| Sorun Türü | Örnek | Çözüm |
|-----------|-------|-------|
| Para birimi ifadeleri | `₺5.200`, `$1,000` | Otomatik sayıya dönüştür |
| Türkçe sözel değerler | `Yok`, `Bilinmiyor`, `N/A` | NaN'a dönüştür |
| Binlik ayraç | `1.000.000` | Sayıya dönüştür |
| Yüzde ifadeleri | `%85` | 0.85'e dönüştür |
| Boşluklu sayılar | `1 500` | Temizle ve dönüştür |

---

## 📈 API Endpoint Referansı

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/upload` | CSV, Excel, Parquet yükle |
| POST | `/select_sheet` | Excel sayfa seçimi |
| GET | `/check_health` | Anomali ve NaN tespiti |
| POST | `/repair_column_anomalies` | Akıllı sütun onarımı |
| POST | `/clean_data` | NaN temizleme (fill/drop) |
| POST | `/join_datasets` | İki veri seti birleştirme |
| POST | `/get_chart_data` | Grafik verisi üretme |
| POST | `/get_stats` | ANOVA, T-Test, Korelasyon, Regresyon |
| POST | `/get_kpi_summary` | KPI özet metrikleri |
| POST | `/get_correlation_matrix` | Korelasyon matrisi |
| POST | `/get_regression_studio_data` | Regresyon stüdyosu (scatter + eğri + CI) |
| POST | `/generate_interpretation` | AI yorumu |
| POST | `/export_data` | CSV/Excel/Parquet indirme |
| POST | `/export_pivot` | Pivot tabloyu Excel'e aktar |
| POST | `/create_calculated_column` | Formül sihirbazı |

---

## 🛠️ Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| **Web Framework** | Flask 3.x + Blueprints |
| **Büyük Veri Motoru** | Polars + PyArrow (Parquet) |
| **Veri İşleme** | Pandas + NumPy |
| **İstatistik** | SciPy (ANOVA, T-Test, Regresyon) |
| **Görselleştirme** | Plotly.js 2.x (50+ grafik) |
| **PDF** | html2pdf.js + jsPDF + html2canvas |
| **Stil** | Glassmorphism (Inter + JetBrains Mono) |
| **Paket Yöneticisi** | uv (önerilen) veya pip |

---

## 🖥️ Sistem Gereksinimleri

- **Python:** 3.10 veya üzeri
- **İşletim Sistemi:** Windows 10/11, macOS, Linux
- **RAM:** En az 4 GB (10M+ satır için 8 GB önerilir)
- **Tarayıcı:** Chrome, Edge, Brave, Firefox (güncel sürüm)
- **Disk:** Yaklaşık 500 MB (bağımlılıklar dahil)

---

## 🔒 Gizlilik & Güvenlik

- ✅ Tüm veriler **100% yerel bilgisayarınızda** işlenir
- ✅ Hiçbir veri buluta veya harici sunucuya gönderilmez
- ✅ Flask oturumları Flask-Session ile sunucu tarafında yönetilir
- ✅ Yüklenen dosyalar `uploads/` klasöründe geçici olarak saklanır

---

## 📝 Lisans

Bu proje [MIT Lisansı](LICENSE) altında dağıtılmaktadır.

---

<div align="center">

**Geliştirici:** Umutcan &copy; 2026 — DataViz Analiz Stüdyosu

*Polars ⚡ + SciPy 🔬 + Plotly.js 📊 ile güçlendirilmiştir*

</div>
