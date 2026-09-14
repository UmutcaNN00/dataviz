const CHARTS = [
  // 📈 TREND
  { id: 'line', name: 'Çizgi', cat: 'trend', icon: '📈', desc: 'Zaman/Kategori trendi.' },
  { id: 'spline', name: 'Yumuşak Çizgi', cat: 'trend', icon: '〰', desc: 'Kıvrımlı, pürüzsüz trend.' },
  { id: 'step', name: 'Basamak', cat: 'trend', icon: '🪜', desc: 'Sıçramalı değişimler.' },
  { id: 'area', name: 'Alan', cat: 'trend', icon: '🌊', desc: 'Altı dolu çizgi.' },
  { id: 'stackedarea', name: 'Yığılmış Alan', cat: 'trend', icon: '📚', desc: 'Kümülatif alan toplamı.' },
  { id: 'waterfall', name: 'Şelale', cat: 'trend', icon: '📉', desc: 'Artış/Azalış etkileri.' },
  { id: 'candlestick', name: 'Mum (Finance)', cat: 'trend', icon: '🕯️', desc: 'Finansal O/H/L/C.' },
  { id: 'ohlc', name: 'OHLC', cat: 'trend', icon: '📊', desc: 'Finansal çubuk.' },
  
  // 📊 KIYASLAMA
  { id: 'bar', name: 'Çubuk', cat: 'comp', icon: '📊', desc: 'Basit kıyaslama.' },
  { id: 'horizontalbar', name: 'Yatay Çubuk', cat: 'comp', icon: '☰', desc: 'Uzun isimli kategoriler.' },
  { id: 'groupedbar', name: 'Gruplu Çubuk', cat: 'comp', icon: '⏸', desc: 'Çoklu metrik kıyası.' },
  { id: 'stackedbar', name: 'Yığılmış Çubuk', cat: 'comp', icon: '🧱', desc: 'Parça/Bütün kıyası.' },
  { id: 'funnel', name: 'Huni', cat: 'comp', icon: '🔽', desc: 'Dönüşüm aşamaları.' },
  { id: 'radar', name: 'Radar (Örümcek)', cat: 'comp', icon: '🕸️', desc: 'Çoklu eksen profili.' },
  { id: 'dotplot', name: 'Nokta Kıyas', cat: 'comp', icon: '⏺', desc: 'Hafif kıyaslama.' },
  { id: 'bullet', name: 'Bullet / KPI', cat: 'comp', icon: '🌡️', desc: 'Hedef takibi.' },

  // 📉 DAĞILIM
  { id: 'histogram', name: 'Histogram', cat: 'dist', icon: '📉', desc: 'Frekans dağılımı.' },
  { id: 'histogram2d', name: '2D Histogram', cat: 'dist', icon: '🔲', desc: 'Matris yoğunluğu.' },
  { id: 'box', name: 'Kutu (Box)', cat: 'dist', icon: '📦', desc: 'Medyan ve çeyreklikler.' },
  { id: 'violin', name: 'Keman (Violin)', cat: 'dist', icon: '🎻', desc: 'Yoğunluk ve kutu.' },
  { id: 'strip', name: 'Şerit (Strip)', cat: 'dist', icon: '📏', desc: 'Nokta yoğunluğu.' },
  { id: 'rug', name: 'Halı (Rug)', cat: 'dist', icon: '||', desc: 'Eksen üstü dağılım.' },
  { id: 'density2d', name: '2D Yoğunluk', cat: 'dist', icon: '☁️', desc: 'Kontur yoğunluğu.' },
  { id: 'errorbar', name: 'Hata Çubuğu', cat: 'dist', icon: '↹', desc: 'Varyans/Hata payı.' },

  // 🔵 İLİŞKİ
  { id: 'scatter', name: 'Dağılım (Scatter)', cat: 'rel', icon: '🔵', desc: 'Korelasyon.' },
  { id: 'bubble', name: 'Balon (Bubble)', cat: 'rel', icon: '🫧', desc: '3. boyut olarak büyüklük.' },
  { id: 'scattermatrix', name: 'Scatter Matris', cat: 'rel', icon: '⚄', desc: 'Tüm sütunların çarprazı.' },
  { id: 'heatmap', name: 'Isı Haritası', cat: 'rel', icon: '🌡️', desc: 'Korelasyon matrisi.' },
  { id: 'parcoords', name: 'Paralel Koor.', cat: 'rel', icon: '🎛', desc: 'Sürekli çoklu ilişki.' },
  { id: 'parcats', name: 'Paralel Kateg.', cat: 'rel', icon: '🔀', desc: 'Kategorik çoklu ilişki.' },

  // 🥧 PARÇA-BÜTÜN
  { id: 'pie', name: 'Pasta', cat: 'part', icon: '🥧', desc: 'Bütünün parçaları.' },
  { id: 'donut', name: 'Donut', cat: 'part', icon: '⭕', desc: 'Ortası boş pasta.' },
  { id: 'sunburst', name: 'Sunburst', cat: 'part', icon: '☀️', desc: 'Hiyerarşik pasta.' },
  { id: 'treemap', name: 'Ağaç (Treemap)', cat: 'part', icon: '🌳', desc: 'Hiyerarşik kareler.' },
  { id: 'funnelarea', name: 'Huni Alanı', cat: 'part', icon: '📐', desc: 'Oransal dilimler.' },
  { id: 'icicle', name: 'Sarkıt (Icicle)', cat: 'part', icon: '🧊', desc: 'Yukarıdan aşağı hiyerarşi.' },

  // 🌌 3D & BİLİMSEL
  { id: 'scatter3d', name: '3D Scatter', cat: 'sci', icon: '🎲', desc: 'Uzaysal korelasyon.' },
  { id: 'line3d', name: '3D Çizgi', cat: 'sci', icon: '🎢', desc: 'Uzayda yol.' },
  { id: 'surface', name: '3D Yüzey', cat: 'sci', icon: '🏞', desc: 'Topolojik yüzey.' },
  { id: 'contour', name: 'Kontur', cat: 'sci', icon: '🗺', desc: 'Eş-yükselti haritası.' },
  { id: 'polarbar', name: 'Polar Çubuk', cat: 'sci', icon: '🧭', desc: 'Dairesel çubuk.' },
  { id: 'polarscatter', name: 'Polar Scatter', cat: 'sci', icon: '🎯', desc: 'Kutupsal nokta.' },
  { id: 'windrose', name: 'Rüzgar Gülü', cat: 'sci', icon: '🎏', desc: 'Yönsel frekans.' },
  { id: 'ternary', name: 'Ternary', cat: 'sci', icon: '◬', desc: '3 eksenli üçgen.' },
  { id: 'carpet', name: 'Halı (Carpet)', cat: 'sci', icon: '🧻', desc: 'Eğrisel koordinatlar.' },
  
  // Yedekler
  { id: 'scattergeo', name: 'Harita (Geo)', cat: 'sci', icon: '🌍', desc: 'Coğrafi noktalar.' },
  { id: 'sankey', name: 'Akış (Sankey)', cat: 'part', icon: '〰️', desc: 'A\'dan B\'ye akış.' }
];