# DataViz Katkı Rehberi (Contributing Guide)

Öncelikle DataViz projesine katkı sağlamak istediğiniz için teşekkür ederiz! DataViz, **T.C. Sanayi ve Teknoloji Bakanlığı & TÜBİTAK 2209-A** programı kapsamında geliştirilen, açık kaynaklı ve kodlama gerektirmeyen bir büyük veri analitiği platformudur.

Bu dokümanda projenin kodlama standartları, geliştirme ortamı kurulumu ve Pull Request (PR) süreci anlatılmaktadır.

---

## 🛠️ Yerel Geliştirme Ortamı Kurulumu

### 1. Depoyu Klonlayın
```bash
git clone https://github.com/UmutcaNN00/dataviz.git
cd dataviz
```

### 2. Sanal Ortamı (Virtual Environment) Oluşturun
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Bağımlılıkları Yükleyin
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Geliştirme Sunucusunu Başlatın
```bash
python app.py
```
Tarayıcınızda `http://127.0.0.1:5000` adresine gidin.

---

## 🧪 Testleri Çalıştırma

DataViz, tüm birim, uç durum ve entegrasyon testlerini tek komutla koşmanızı sağlayan birleşik bir test çalıştırıcıya sahiptir:

```bash
python run_tests.py
```

Bu komut şu 7 aşamayı ardışık olarak denetler:
1. Python dosyaları sözdizimi derleme denetimi (`py_compile`)
2. Birim testleri (`test_audit_fixes.py`, `test_spss_reader.py`)
3. Uç durum ve sıfır bölme korumaları (`test_edge_cases.py`)
4. Veri ikame ve bellek downcasting testleri (`test_new_prep_features.py`)
5. SIMD Pushdown, Veri Sözleşmeleri ve Ensemble anomali testleri (`test_nextgen_integration.py`)
6. Flask REST API rotaları ve parametre denetimleri (`test_routes_api.py`)
7. ANOVA, Bayes Faktörü ve ReportLab PDF testleri (`test_stats_and_reporting.py`)

> **Önemli:** Pull Request açmadan önce `python run_tests.py` komutunun hatasız (`0 failed`) sonuçlandığından emin olun.

---

## 📝 Kodlama ve İsimlendirme Kuralları

- **Dil:** Kullanıcı arayüzü (UI) metinleri, değişken isimleri ve kod içi yorumlar **Türkçe** olmalıdır.
- **Commit Mesajları:** İngilizce **Conventional Commits** formatında yazılmalıdır:
  - `feat:` Yeni bir kullanıcı özelliği (örn: `feat: add time-series forecasting studio`)
  - `fix:` Hata düzeltmesi (örn: `fix: prevent reportlab crash on raw html entities`)
  - `docs:` Dokümantasyon değişiklikleri (örn: `docs: update contributing guide`)
  - `test:` Yeni test eklenmesi veya test güncellemesi (örn: `test: add tests for polars arrow engine`)
  - `refactor:` Fonksiyonellik değiştirmeyen kod iyileştirmeleri (örn: `refactor: optimize store session locking`)
- **Windows Encoding:** Python 3.14 Windows'ta `sys.stdout.reconfigure(encoding='utf-8')` ile çalıştırılmalıdır.
- **ReportLab PDF:** Arial fontu Unicode alt/üst simgeleri desteklemediğinden, her zaman ReportLab HTML tag'leri (`<sub>`, `<sup>`) kullanılmalıdır.

---

## 🔀 Git İş Akışı & Pull Request (PR)

1. `main` dalından yeni bir özellik dalı açın:
   ```bash
   git checkout -b feat/yeni-analitik-ozellik
   ```
2. Değişikliklerinizi yapın ve testleri çalıştırın (`python run_tests.py`).
3. Değişikliklerinizi commitleyin:
   ```bash
   git commit -m "feat: implement fast percentile approximation"
   ```
4. Dalınızı kendi çatalınıza (fork) gönderin ve GitHub üzerinden `main` dalına Pull Request açın.
5. GitHub Actions CI iş akışı testlerinizi otomatik olarak koşacaktır.

---

## 💬 İletişim & Sorular
Sorularınız veya önerileriniz için [GitHub Discussions](https://github.com/UmutcaNN00/dataviz/discussions) veya [Issues](https://github.com/UmutcaNN00/dataviz/issues) sekmelerini kullanabilirsiniz.
