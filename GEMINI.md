# DataViz Proje Kuralları

## Dil ve İsimlendirme
- Tüm UI metinleri, kod yorumları, commit mesajları ve değişken isimleri **Türkçe** olmalıdır.
- Commit mesajları İngilizce Conventional Commits formatında yazılır (feat:, fix:, chore:, docs:, refactor:).

## Git Yapılandırması
- Git executable yolu: `C:\Users\umutc\AppData\Local\GitHubDesktop\app-3.6.5\resources\app\git\cmd\git.exe`
- Remote: `https://github.com/UmutcaNN00/dataviz.git`

## Python Ortamı
- Sanal ortam: `dataviz\.venv` (Python 3.14, Windows)
- Bağımlılıklar: `dataviz\requirements.txt`
- Flask uygulaması: `dataviz\app.py`

## Windows Encoding Sorunları
- Python 3.14 Windows'ta varsayılan encoding `cp1254`'tür. Unicode karakter yazdıran scriptlerde **mutlaka** `sys.stdout.reconfigure(encoding='utf-8')` kullan, yoksa `UnicodeEncodeError` alırsın.

## ReportLab PDF Üretimi
- Windows Arial fontu Unicode alt simge (U+2080–U+209F) ve üst simge (U+2070–U+207F) karakterlerini **desteklemez**.
- Bunlar yerine ReportLab HTML tag'leri kullan: `<sub>0</sub>`, `<sup>2</sup>`.
- Font kayıt: `pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))`.

## VS Code IDE Diagnostikleri
- VS Code hot-exit özelliği eski dosya sürümlerini `C:\Users\umutc\AppData\Roaming\Code\Backups` altında cache'ler.
- Pylance/Ruff bu stale dosyaları okuyarak sahte hatalar gösterebilir. Gerçek hata durumu için önce `ruff check` çalıştır.
- `.ruff_cache` klasörü `.gitignore`'a eklenmiştir.

## Dosya Sistemi Notları
- Google Drive sync `.tmp.drivedownload` ve `.tmp.driveupload` gizli klasörleri oluşturabilir — bunlar göz ardı edilmeli.
