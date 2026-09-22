# Güncelleme Notları (Changelog)

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
