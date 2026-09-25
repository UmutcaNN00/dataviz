---
name: tubitak-2209a-report
description: >-
  TÜBİTAK 2209-A Üniversite Öğrencileri Araştırma Projeleri başvurusu hazırlanırken,
  akademik rapor üretilirken veya TÜBİTAK ile ilgili bilgi istendiğinde bu skill
  kullanılır. ReportLab PDF üretimi, başvuru yapısı ve doğrulama adımlarını içerir.
---

# TÜBİTAK 2209-A Rapor Üretimi

## Program Bilgisi

- **Program:** TÜBİTAK 2209-A Üniversite Öğrencileri Araştırma Projeleri Destekleme Programı
- **Hedef:** Lisans öğrencilerinin araştırma projelerini desteklemek
- **Başvuru sistemi:** ARBİS + TYBS (Türkiye Yükseköğretim Bilgi Sistemi)
- **Bütçe:** Proje başına belirli bir üst limit (güncel rehberden kontrol edilmeli)

## PDF Motoru: ReportLab

### Font Kayıt
```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFont(TTFont('Consolas', 'C:/Windows/Fonts/consola.ttf'))
```

### Dinamik Sayfa Numaralandırma (İki Geçişli)
`NumberedCanvas` sınıfı kullanılır:
1. İlk geçiş: Tüm sayfaları oluştur, toplam sayfa sayısını kaydet
2. İkinci geçiş: Her sayfaya "Sayfa X / Y" yaz

### Sayfa Bütçesi
- **Kağıt:** A4 (595.27 × 841.89 pt)
- **Kenar boşlukları:** 48pt her yönde
- **Kullanılabilir yükseklik:** ~745.9 pt
- **Sayfa başına içerik:** 350–500pt (taşma kontrolü yapılmalı)

## Font Uyarıları

> **KRİTİK:** Windows Arial fontu aşağıdaki Unicode aralıklarını **DESTEKLEMEZ**:
> - Alt simgeler: U+2080–U+209F (₀₁₂₃...)
> - Üst simgeler: U+2070–U+207F (⁰¹²³...)
> - Modifier harfler: U+1D40 vb.
>
> Bunlar yerine ReportLab HTML tag'leri kullan:
> - `H<sub>0</sub>` → H₀
> - `R<sup>2</sup>` → R²

## Rapor İçerik Yapısı (2209-A)

1. **Kapak Sayfası** — Proje adı, yürütücü bilgileri, danışman, üniversite
2. **Özet** — 200–300 kelimelik Türkçe özet
3. **Projenin Özgün Değeri** — Mevcut çözümlerden farkı
4. **Amaç ve Hipotezler** — H₀ ve H₁ hipotezleri
5. **SMART Hedefler** — Spesifik, Ölçülebilir, Ulaşılabilir, İlgili, Zamanlı
6. **Yöntem** — Teknik mimari, kullanılan teknolojiler
7. **İş Paketleri** — 6 iş paketi, sorumlu kişiler, süre
8. **Gantt Şeması** — 12 aylık zaman çizelgesi
9. **Risk Analizi ve B Planı** — Risk matrisi, önleme/hafifletme stratejileri
10. **Sürdürülebilir Kalkınma Amaçları (SKA)** — SKA 4 ve SKA 9
11. **Bütçe Tablosu** — Kalem bazlı bütçe dağılımı
12. **Kaynakça** — APA formatında referanslar
13. **Savunma Rehberi** — 12 olası jüri sorusu ve yanıtları

## Otomatik Doğrulama

Rapor oluşturulduktan sonra şu kontroller yapılmalıdır:

```python
# 32 zorunlu anahtar kelime kontrolü
zorunlu_kelimeler = ['TÜBİTAK', '2209-A', 'hipotez', 'SMART', 'SKA', 
                      'iş paketi', 'Gantt', 'risk', 'bütçe', ...]

# Türkçe karakter testi
turkce_karakterler = ['ş', 'ç', 'ğ', 'ı', 'ö', 'ü', 'İ', 'Ş', 'Ç', 'Ğ', 'Ö', 'Ü']

# Sayfa sayısı kontrolü (12-15 sayfa hedef)
# Görsel sayısı kontrolü
```
