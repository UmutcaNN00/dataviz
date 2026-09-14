# DataViz Pro — İnteraktif Excel Veri Analizi Platformu

Ham Excel ve CSV verilerini **sürükle-bırak** yöntemiyle **50+ interaktif grafiğe**, ileri düzey **istatistiksel analizlere** (ANOVA, Regresyon, T-Test) ve düzenlenebilir **akademik PDF raporlara** dönüştüren hafif ve hızlı bir web tabanlı Veri Analizi platformudur.

> Ağır yapay zeka modelleri veya GPU gerektirmez. Tamamen algoritmik ve istatistiksel analiz motoruna dayanır.

---

## Özellikler

### Veri Yönetimi
- **Sürükle-Bırak Yükleme** — Excel (.xlsx) ve CSV dosyalarını anında yükleyin
- **Akıllı Sütun Algılama** — Sayısal ve kategorik sütunları otomatik tanır
- **Veri Temizleme** — Eksik verileri doldurma, aykırı değerleri tespit etme
- **Veri Birleştirme (Join)** — İki farklı tabloyu ortak sütunla birleştirin
- **Formül Motoru** — Yeni hesaplanmış sütunlar üretin (Toplama, Çıkarma, Bölme, Çarpma)

### Görselleştirme
- **50+ Grafik Türü** — Bar, Çizgi, Pasta, Scatter, Histogram, Box Plot, Heatmap, Treemap ve daha fazlası
- **Akıllı Grafik Öneri Motoru** — Veri türlerine göre en uygun grafikleri önerir
- **Sihirli Şablonlar** — Tek tıkla hazır analiz şablonları
- **Çoklu Pano (Dashboard)** — Grafikleri sabitleyin, tek ekranda izleyin
- **Sürüklenebilir Ekran Bölücü (Splitter)** — Sol/sağ paneli kendinize göre ayarlayın

### İstatistiksel Analiz
- **Temel İstatistikler** — Ortalama, Medyan, Min, Max, Standart Sapma
- **ANOVA (Tek Yönlü Varyans Analizi)** — Kategorik gruplar arası fark testi
- **Bağımsız Örneklem T-Testi** — İki grup ortalaması karşılaştırması
- **Pearson Korelasyon & Lineer Regresyon** — Değişkenler arası ilişki ve denklem
- **Akademik İstatistiksel Yorumlayıcı** — İstatistik sonuçlarını akademik dille özetler

### PDF Rapor Stüdyosu
- **A4 Önizleme** — Raporunuzu indirmeden önce A4 kağıdında görün
- **Sürükle-Sırala** — Grafiklerin sırasını yukarı/aşağı butonlarıyla değiştirin
- **Metin Ekleme** — Grafikler arasına kendi yorumlarınızı yazın
- **Çok Sayfalı PDF** — 10+ grafik bile otomatik sayfalanır
- **Tek Grafik PDF/PNG** — İstediğiniz grafiği ayrı ayrı indirin

---

## Hızlı Başlangıç

### Gereksinimler
- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python paket yöneticisi)

### Kurulum

```bash
# Repoyu klonlayın
git clone https://github.com/UmutcaNN00/dataviz-pro-demo.git
cd dataviz-pro-demo

# Bağımlılıkları yükleyin
uv venv
uv pip install -r requirements.txt

# Sunucuyu başlatın
uv run python app.py
```

Tarayıcınızda **http://127.0.0.1:5000** adresine gidin.

### Windows — Tek Tıkla Başlatma
```DEMO_BASLAT.bat``` dosyasına çift tıklayın. Sunucu otomatik başlar ve tarayıcınız açılır.

---

## Proje Yapısı

```
dataviz-pro-demo/
├── app.py                  # Flask sunucusu ve API endpoint'leri
├── requirements.txt        # Python bağımlılıkları
├── DEMO_BASLAT.bat         # Windows tek tıkla başlatıcı
├── modules/
│   └── data_processing.py  # Veri işleme yardımcı fonksiyonları
├── templates/
│   ├── landing.html        # Karşılama sayfası
│   ├── analysis.html       # Ana analiz arayüzü
│   └── index.html          # Yönlendirme sayfası
└── static/
    ├── css/
    │   ├── analysis.css    # Analiz sayfası stilleri
    │   ├── landing.css     # Karşılama sayfası stilleri
    │   └── style.css       # Genel stiller
    └── js/
        ├── app.js          # Ana uygulama mantığı
        ├── landing.js      # Karşılama sayfası animasyonları
        ├── three_scene.js  # 3D arka plan efektleri
        └── modules/
            ├── charts_config.js  # Grafik konfigürasyonları
            └── globals.js        # Global değişkenler
```

---

## Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Backend | Python, Flask, Pandas, SciPy |
| Frontend | Vanilla JS, Plotly.js, Three.js |
| İstatistik | scipy.stats (ANOVA, T-Test, Regresyon) |
| PDF | html2pdf.js, html2canvas |
| Tema | Custom CSS, Glassmorphism, Dark Mode |

---

## Ekran Görüntüleri

> Uygulamayı başlattıktan sonra kendi verilerinizi yükleyerek keşfedebilirsiniz.

---

## Lisans

Bu proje akademik sunum amaçlı geliştirilmiştir.

## Geliştirici

**Umutcan** — [@UmutcaNN00](https://github.com/UmutcaNN00)
