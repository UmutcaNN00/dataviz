# Güncelleme Notları (Changelog)

## [v3.0.0] - 100M+ Büyük Veri Motoru, Korelasyon & Regresyon Stüdyosu ve Modüler Mimari (25.09.2026)

Bu ana sürümde büyük veri işleme motoru 100 milyon satır ölçeğine yükseltilmiş, bilimsel Korelasyon & Regresyon Stüdyosu eklenmiş ve istemci/sunucu mimarisi tam modüler yapıya kavuşturulmuştur.

### 🚀 Yeni Özellikler ve Büyük Veri Optimizasyonları

- **PyArrow Zero-Copy & 100M+ Satır Parquet Motoru (`file_service.py`):**
  - `pq.read_table(..., use_threads=True).to_pandas(split_blocks=True, self_destruct=True)` mimarisiyle 100.000.000 satır × 22 sütunluk (4.20 GB ZSTD) Parquet veri setleri ~62.5 saniyede ve yalnızca ~6.35 GB RAM ile belleğe alınmaktadır.
  - Sütun izdüşümü (*Column Projection*) ile grafik ve istatistik uç noktalarında tüm tablo kopyalanmadan yalnızca seçili X/Y sütunları işlenmektedir.

- **Vektörize Kategorik Data Healer (`data_healer.py`):**
  - Sayısal sütunlara karışmış para birimi (`₺`, `$`, `€`), birim (`kg`, `lt`, `adet`), yüzde (`%`) ve sözel eksik değerlerin (`Yok`, `Bilinmiyor`, `N/A`) onarımı için kategorik sözlük indeksleme (`_parse_series_fast`) eklendi (~1000x hız artışı).
  - Büyük veri setlerinde (>1M satır) sığ kopya (`deep=False`), `float32` tip dönüşümü ve sütun bazlı eksik veri doldurma ile bellek tüketimi minimize edildi.

- **Bilimsel Korelasyon & Regresyon Laboratuvarı (`regression_studio.js`, `stats_service.py`):**
  - Pearson ($r$), Spearman ($\rho$) ve Kendall ($\tau$) korelasyon ısı haritası matrisi eklendi.
  - Doğrusal, Polinom (2. ve 3. derece), Logaritmik ve Üstel regresyon modelleri ile **%95 Güven Aralığı Bandı (CI Band)** görselleştirmesi eklendi.

- **Modüler Çoklu Pano (`dashboard_studio.js`) ve Çekirdek İyileştirmeler (`app.py`, `store.py`):**
  - KPI kartları ve Çoklu Pano (Dashboard Grid) yönetimi bağımsız `dashboard_studio.js` modülüne ayrıştırıldı.
  - `NumpyJSONProvider` ile `NaN`, `Inf`, `float32` ve `int64` değerlerin JSON serileştirme hataları tamamen giderildi.
  - `threading.RLock()` tabanlı LRU oturum yönetimi (`MAX_ACTIVE_SESSIONS = 5`) ve otomatik bellek temizliği (`gc.collect()`) devreye alındı.
  - 19 adımlı uçtan uca entegrasyon test paketi (`test_system_connectivity.py`) ve 100M satırlık gerçekçi kirli veri üreteci (`generate_100m_dataset.py`) eklendi.

---

## [v2.1.0] - Gelişmiş Grafik Motoru & Kararlılık Güncellemesi (22.09.2026)

Bu sürümde arka planda çalışan analiz motorunu ve grafik öneri sistemini tamamen elden geçirdik. Arayüzün orjinalliğini koruyarak yeteneklerini çok daha üst bir seviyeye taşıdık.

### 🚀 Yeni Özellikler ve Geliştirmeler

- **Akıllı Grafik Öneri Motoru (`evaluateCharts` Revizyonu):**
  - X ve Y eksenine sürüklenen verilerin tipine (Kategorik, Sayısal, Tarihsel) ve sayısına (tekli, çoklu) göre tam **50+ Plotly grafiğinin** hangisinin mantıklı olduğunu tespit eden algoritma baştan yazıldı.
  - Yanlış veya mantıksız grafiklerin (örn. çoklu kategorik veride line3d) seçilmesi engellendi, doğru grafikler ise otomatik tavsiye edilecek (Recommendation) şekilde ayarlandı.

- **Eksik Grafik Türlerinin Render Desteği:**
  - Eskiden sadece adı olup çizdirilemeyen **Sankey, Sunburst, Treemap, Icicle** gibi hiyerarşik ve karmaşık grafiklerin Plotly render fonksiyonları (`drawMegaPlotly` içinde) eklendi ve iyileştirildi.
  - Özellikle Sunburst ve Treemap grafiklerindeki "Root (Kök) düğüm eksikliği" hataları giderilerek Plotly uyarıları susturuldu.

- **Data Healer & Veri Temizleme Desteği:**
  - İçine harf ya da para birimi sembolü (`₺5,200`, `NaN`, `Yok`) karışmış sayısal kolonların otomatik düzeltilmesi ve analizi çökertmemesi için arka plan bağlantıları (`app.js` üzerinden) sağlandı.

- **Formül Sihirbazı & Slicers (Dilimleyiciler):**
  - Butonlar arası bağlantı kopuklukları (`btnSelectAllCat`, `btnClearAllCat`, vb.) giderildi. 
  - Hızlı veri dışa aktarma (Export) butonları için gerekli Event Listener'lar aktif hale getirildi.

### ♻️ Geri Alınan / Düzeltilen Kısımlar

- **Karşılama Sayfası (Landing Page) Orijinalliği:**
  - Test amaçlı eklenen yoğun animasyonlu ve yapısı değiştirilmiş sayfa tasarımları (Concept 1, 2, 3) projeden izole edildi. 
  - Github'daki **orijinal karşılama sayfası (`landing.html` ve `landing.css`)** geri yüklenerek `/analysis` stüdyosuna olan tüm entegrasyonlar kusursuz hale getirildi.
