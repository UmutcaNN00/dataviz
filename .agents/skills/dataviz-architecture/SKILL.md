---
name: dataviz-architecture
description: >-
  DataViz projesinde kod yazarken, yeni route/service/modül eklerken veya mevcut
  mimariyi anlamak gerektiğinde bu skill kullanılır. Flask Blueprint yapısı,
  4 katmanlı mimari, JS modül haritası ve temel konvansiyonları içerir.
---

# DataViz Proje Mimarisi

## 4 Katmanlı Mimari

```
dataviz/
├── core/           → Oturum yönetimi (LRU store, RLock)
├── routes/         → Flask Blueprints (6 adet)
├── services/       → İş mantığı servisleri
└── static/js/modules/ → ES6 modüler frontend
```

## Core Katmanı

### `core/store.py`
- `threading.RLock()` ile thread-safe LRU oturum yönetimi
- `MAX_ACTIVE_SESSIONS = 5` — en fazla 5 aktif oturum, fazlası GC ile silinir
- Her oturum bir `session_id` ile tanımlanır, DataFrame + metadata saklar

## Routes Katmanı (Flask Blueprints)

| Blueprint | Dosya | Sorumluluk |
|-----------|-------|------------|
| `upload` | `routes/upload_routes.py` | Dosya yükleme (CSV, Excel, Parquet, JSON) |
| `data` | `routes/data_routes.py` | Veri ön işleme, sağlık kontrolü, sütun işlemleri |
| `viz` | `routes/viz_routes.py` | Grafik oluşturma, Plotly JSON üretimi |
| `export` | `routes/export_routes.py` | Pivot ve veri dışa aktarma |
| `ai` | `routes/ai_routes.py` | AI destekli analiz ve öneriler |
| `join` | `routes/join_routes.py` | Çoklu veri seti birleştirme |

## Services Katmanı

| Servis | Sorumluluk |
|--------|------------|
| `file_service.py` | Dosya okuma, format algılama, PyArrow Parquet optimizasyonu |
| `data_healer.py` | Otomatik veri temizleme, tip onarımı, NaN yönetimi |
| `stats_service.py` | İstatistiksel hesaplamalar (regresyon, korelasyon, CI band) |
| `ai_service.py` | Transformers tabanlı AI analiz (opsiyonel) |
| `export_service.py` | Dışa aktarma format dönüşümleri |

## Frontend (Vanilla JS + Plotly)

**Framework yok** — React, Vue, Angular kullanılmaz. Pure ES6 modüller:

| Modül | Sorumluluk |
|-------|------------|
| `data_prep.js` | Veri ön işleme UI, sütun seçimi |
| `chart_manager.js` | Plotly grafik oluşturma ve yönetimi |
| `dashboard_studio.js` | KPI kartları ve Dashboard Grid |
| `join_modal.js` | Çoklu veri seti birleştirme modal'ı |
| `pivot_studio.js` | Pivot tablo oluşturucu |
| `ai_panel.js` | AI analiz paneli |
| `export.js` | Dışa aktarma işlemleri |
| `upload.js` | Dosya yükleme arayüzü |
| `utils.js` | Yardımcı fonksiyonlar |

## Temel Konvansiyonlar

- **`app.py` → `NumpyJSONProvider`:** NaN ve Inf değerlerini JSON `null` olarak serileştirir
- **Session bazlı veri:** Her kullanıcı oturumu bağımsız DataFrame tutar
- **Hata yönetimi:** Route'larda try-except ile JSON error response döndürülür
- **Type-safety:** `file.filename` gibi optional değerlerde `assert` veya `if` guard kullanılır
