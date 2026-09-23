<div align="center">

# 📊 DataViz
**Milyonlarca Satırlık Büyük Veriyi Saniyeler İçinde Keşfedin, Onarın ve Raporlayın**

<p align="center">
  Geleneksel tablo yazılımlarının sınırlarını aşın! <strong>DataViz</strong>; Excel, CSV ve Apache Parquet dosyalarınızı sürükleyip bırakarak anında analiz etmenizi sağlayan yeni nesil bir veri görselleştirme ve iş zekası (BI) platformudur. <br><br>
  <strong>Polars</strong> destekli hızlandırılmış veri motoru sayesinde devasa verileri milisaniyeler içinde işlerken, modern tasarımıyla kusursuz bir kullanıcı deneyimi sunar. Tüm işlemler <strong>%100 yerel bilgisayarınızda</strong> gerçekleşir; verileriniz asla dışarı çıkmaz!
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Veri_Motoru-Polars_Hızlandırılmış-38bdf8?style=for-the-badge&logo=polars&logoColor=white" alt="Polars">
  <img src="https://img.shields.io/badge/Grafikler-Plotly_50+_Motoru-3b82f6?style=for-the-badge&logo=plotly&logoColor=white" alt="Plotly">
  <img src="https://img.shields.io/badge/İstatistik-SciPy_Tabanlı-10b981?style=for-the-badge&logo=scipy&logoColor=white" alt="SciPy">
  <img src="https://img.shields.io/badge/Gizlilik-100%25_Yerel_Çalışma-ff4500?style=for-the-badge&logo=shield&logoColor=white" alt="Local">
</p>
</div>

<br>

<p align='center'>
  <img src='docs/images/landing.png' alt='DataViz Karşılama Ekranı' width='800'>
</p>
<p align='center'>
  <img src='docs/images/analysis.png' alt='DataViz Analiz Stüdyosu' width='800'>
</p>

---

## 🌟 Öne Çıkan Özellikler

### 🚀 1 Milyon+ Satır — Polars Hızı
Pandas'ın darboğazlarını geride bırakın! Rust temelli Polars motoru ile devasa veri setleri saniyeler içinde belleğe yüklenir, filtrelenir ve işlenir. %80'e varan daha az RAM tüketimi ile bilgisayarınızı yormadan büyük veri analizi yapın.

### 🧠 Akıllı Grafik Öneri Motoru (50+ Grafik)
Sıradan çubuk grafiklerin ötesine geçin! DataViz, analiz stüdyosuna sürüklediğiniz X ve Y eksenlerinin **veri tiplerine (Tarih, Kategorik, Sayısal)** ve sayısına göre 50'den fazla Plotly.js grafiği arasından en mantıklı olanları size otomatik önerir. Yanlış grafik kullanımını engeller ve analizi hızlandırır. (Candlestick, Sankey, Sunburst, Scatter3D dahil!)

### 🩺 Data Healer (Veri Sağlığı Onarıcı)
Bozuk veya kirli verilerle uğraşmaya son! Sayısal alanlara karışmış `₺5,200`, `Yok`, `NaN`, `—` gibi karakter bazlı sapmaları sistem otomatik algılar. "Data Healer" ile tek tıkla veri kaybı yaşamadan tüm anomaliler saf sayısal formatlara dönüştürülür.

### 🪄 Gelişmiş Formül Sihirbazı & Veri Birleştirme (Join)
- **Formül Sihirbazı:** Hiçbir kod yazmadan Excel benzeri basit arayüzle yeni metrikler türetin. Örn: `KDV Dahil Satış = (Satış Tutarı - Maliyet) * 1.20`. 
- **Tablo Birleştirme:** Sisteme ikinci bir dosya yükleyip (CSV/Excel) mevcut veri setinizle "Ortak Sütunlar" üzerinden LEFT JOIN veya INNER JOIN mantığıyla birleştirin.

### 📄 Etkileşimli A4 PDF Rapor Stüdyosu
Oluşturduğunuz tüm grafikleri bir A4 rapor formatına sürükleyip dizin. Grafikler arasına metin blokları ve akademik yorumlarınızı ekleyerek profesyonel, çok sayfalı raporlar (PDF) çıktı alın.

---

## 🔒 Akademik Güvenilirlik ve Tam Gizlilik

- **Yapay Zeka Halüsinasyonu Yok:** Veri analizindeki t-test, tek yönlü ANOVA ve Pearson korelasyon hesaplamaları tamamen **`scipy.stats`** üzerinden yapılır. P-değerleri, F-istatistikleri kural tabanlı, deterministik şablonlarla yorumlanır.
- **Sıfır Bulut İletişimi:** Verileriniz, sunuculara veya yapay zeka modellerine ASLA gönderilmez. Uygulama sadece kendi bilgisayarınızda (`127.0.0.1`) çalışır ve tüm hesaplamalar donanımınızın CPU/RAM'i kullanılarak yapılır. Tam kurumsal gizlilik sağlanır.

---

## ⚙️ Hızlı Kurulum Adımları (1 Dakikada Hazır)

Sisteminizde **Python 3.10+** kurulu olması yeterlidir.

### Seçenek 1: 🖱️ Windows Tek Tıkla Başlatıcı (En Kolayı)
Proje dizinindeki **`DEMO_BASLAT.bat`** dosyasına çift tıklayın. Her şey otomatik kurulur ve tarayıcınızda açılır!

### Seçenek 2: 💻 `uv` veya `pip` ile Kurulum (Geliştiriciler İçin)
```bash
# Projeyi klonlayın
git clone https://github.com/UmutcaNN00/dataviz.git
cd dataviz

# Sanal ortam oluşturun ve aktif edin
python -m venv .venv
# Windows: .venv\Scripts\activate | Mac/Linux: source .venv/bin/activate

# Gerekli paketleri kurun ve çalıştırın
pip install -r requirements.txt
python app.py
```
Ardından tarayıcınızdan **`http://127.0.0.1:5000`** adresine gidin.

### Seçenek 3: 🐳 Docker ile Kurulum
```bash
docker-compose up -d
```

---

## 🏗️ Mimari ve Teknolojiler

DataViz, sürdürülebilirlik ilkelerine uygun olarak **Flask Blueprints** ve **Modern ES6 JavaScript** modülleriyle inşa edilmiştir:

* **Büyük Veri İşleme:** `Polars`, `PyArrow`
* **Backend API Katmanı:** `Python 3.10+`, `Flask 3.0+`
* **Görselleştirme:** `Plotly.js 2.27.0` (50+ Dinamik Grafik)
* **İstatistik Engine:** `SciPy 1.11+`

---

## 👨‍💻 Geliştirici

Bu proje, veri bilimi ve büyük veri analitiğine tutkuyla bağlı olan **Umutcan** ([@UmutcaNN00](https://github.com/UmutcaNN00)) tarafından geliştirilmiştir.

<div align="center">
  <sub>Gelişmiş Veri Analizi ve İş Zekası Sistemleri İçin Yeniden Tanımlandı — <b>DataViz</b> 2026</sub>
</div>
