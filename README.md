<div align="center">

# DataViz Pro

### Interaktif Excel Veri Analizi Platformu

<p align="center">
  <strong>Ham Excel ve CSV verilerini suruklele-birak yontemiyle 50+ interaktif grafige, ileri duzey istatistiksel analizlere ve duzenlenebilir akademik PDF raporlara donusturun.</strong>
</p>

<p align="center">
  <a href="#ozellikler"><img src="https://img.shields.io/badge/50%2B-Grafik%20T%C3%BCr%C3%BC-8b5cf6?style=for-the-badge" alt="Charts"></a>
  <a href="#istatistiksel-analiz"><img src="https://img.shields.io/badge/ANOVA-Regresyon%20%26%20T--Test-3b82f6?style=for-the-badge" alt="Stats"></a>
  <a href="#pdf-rapor-studyosu"><img src="https://img.shields.io/badge/PDF-Rapor%20St%C3%BCdyosu-10b981?style=for-the-badge" alt="PDF"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.x-000?logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/Plotly.js-Charts-3F4F75?logo=plotly&logoColor=white" alt="Plotly">
  <img src="https://img.shields.io/badge/SciPy-Statistics-8CAAE6?logo=scipy&logoColor=white" alt="SciPy">
  <img src="https://img.shields.io/badge/License-Academic-yellow" alt="License">
</p>

<br>

> **GPU veya agir yapay zeka modeli gerektirmez.**
> Tamamen algoritmik ve istatistiksel analiz motoruna dayanir.

</div>

---

## Ozellikler

<table>
<tr>
<td width="50%">

### Veri Yonetimi
- **Suruklele-Birak Yukleme** — Excel (.xlsx) ve CSV dosyalarini aninda yukleyin
- **Akilli Sutun Algilama** — Sayisal ve kategorik sutunlari otomatik tanir
- **Veri Temizleme** — Eksik verileri doldurma, aykiri degerleri tespit etme
- **Veri Birlestirme (Join)** — Iki farkli tabloyu ortak sutunla birlestirin
- **Formul Motoru** — Yeni hesaplanmis sutunlar uretin

</td>
<td width="50%">

### Gorsellestirme
- **50+ Grafik Turu** — Bar, Cizgi, Pasta, Scatter, Histogram, Box Plot, Heatmap, Treemap
- **Akilli Grafik Oneri Motoru** — Veri turlerine gore en uygun grafikleri onerir
- **Sihirli Sablonlar** — Tek tikla hazir analiz sablonlari
- **Coklu Pano (Dashboard)** — Grafikleri sabitleyin, tek ekranda izleyin
- **Suruklenebilir Ekran Bolucu** — Sol/sag paneli kendinize gore ayarlayin

</td>
</tr>
</table>

---

### Istatistiksel Analiz

| Analiz | Aciklama |
|--------|----------|
| **Temel Istatistikler** | Ortalama, Medyan, Min, Max, Standart Sapma, Eksik Veri |
| **ANOVA** | Tek Yonlu Varyans Analizi — Kategorik gruplar arasi fark testi |
| **Bagimsiz Orneklem T-Testi** | Iki grup ortalamasi karsilastirmasi |
| **Pearson Korelasyon** | Degiskenler arasi dogrusal iliski katsayisi |
| **Lineer Regresyon** | Bagimli degisken tahmini ve R-squared degeri |
| **Akademik Yorumlayici** | Tum sonuclari akademik dilde ozetler |

---

### PDF Rapor Studyosu

<table>
<tr>
<td>

**A4 Onizleme Tuvali** — Raporunuzu indirmeden once A4 kagidinda gorun

**Suruklele-Sirala** — Grafiklerin sirasini yukari/asagi butonlariyla degistirin

**Metin Ekleme** — Grafikler arasina kendi yorumlarinizi yazin

**Cok Sayfali PDF** — 10+ grafik bile otomatik sayfalanir

**Tek Grafik PDF/PNG** — Istediginiz grafigi ayri ayri indirin

</td>
</tr>
</table>

---

## Hizli Baslangic

### Gereksinimler
- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python paket yoneticisi)

### Kurulum

```bash
# Repoyu klonlayin
git clone https://github.com/UmutcaNN00/dataviz-pro-demo.git
cd dataviz-pro-demo

# Bagimliliklari yukleyin
uv venv
uv pip install -r requirements.txt

# Sunucuyu baslatin
uv run python app.py
```

Tarayicinizda **http://127.0.0.1:5000** adresine gidin.

### Windows — Tek Tikla Baslatma

> ```DEMO_BASLAT.bat``` dosyasina cift tiklayin. Sunucu otomatik baslar ve tarayiciniz acilir.

---

## Proje Yapisi

```
dataviz-pro-demo/
|-- app.py                  # Flask sunucusu ve API endpoint'leri
|-- requirements.txt        # Python bagimliliklari
|-- DEMO_BASLAT.bat         # Windows tek tikla baslatici
|-- modules/
|   +-- data_processing.py  # Veri isleme yardimci fonksiyonlari
|-- templates/
|   |-- landing.html        # Karsilama sayfasi
|   |-- analysis.html       # Ana analiz arayuzu
|   +-- index.html          # Yonlendirme sayfasi
+-- static/
    |-- css/                # Stiller (Dark Mode, Glassmorphism)
    +-- js/                 # Uygulama mantigi, grafik config
```

---

## Teknoloji Yigini

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas">
  <img src="https://img.shields.io/badge/SciPy-8CAAE6?style=for-the-badge&logo=scipy&logoColor=white" alt="SciPy">
  <img src="https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white" alt="Plotly">
  <img src="https://img.shields.io/badge/Three.js-000000?style=for-the-badge&logo=three.js&logoColor=white" alt="Three.js">
  <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5">
  <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3">
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JS">
</p>

| Katman | Teknoloji | Amac |
|--------|-----------|------|
| Backend | Python, Flask, Pandas | Veri isleme ve API |
| Istatistik | SciPy (scipy.stats) | ANOVA, T-Test, Regresyon |
| Gorsellestirme | Plotly.js | 50+ interaktif grafik |
| 3D Efektler | Three.js | Karsilama sayfasi animasyonlari |
| PDF | html2pdf.js, html2canvas | Cok sayfali rapor olusturma |
| Tema | Custom CSS | Dark Mode, Glassmorphism |

---

<div align="center">

### Gelistirici

**Umutcan** — [@UmutcaNN00](https://github.com/UmutcaNN00)

Bu proje akademik sunum amaciyla gelistirilmistir.

<br>

<img src="https://img.shields.io/badge/Made%20with-%E2%9D%A4%EF%B8%8F-red?style=for-the-badge" alt="Made with love">

</div>
