/* ════════════════════════════════════════════════════════════
   DATAVIZ PRO V6 — CHARTS CONFIGURATION & PLOTLY ENGINE
   40+ Chart Types Definitions, buildLayout & drawMegaPlotly
════════════════════════════════════════════════════════════ */

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

function buildLayout(bg, sGrid, sLeg, isMini = false) {
  const gc = sGrid ? 'rgba(255,255,255,0.08)' : 'transparent';
  const tc = '#94a3b8';
  return {
    autosize: true, paper_bgcolor: 'transparent', plot_bgcolor: bg, font: { family: 'Inter', color: tc }, showlegend: sLeg,
    legend: { bgcolor: 'transparent' }, margin: isMini ? { t:15, r:15, b:25, l:35 } : { t:30, r:30, b:50, l:50 },
    xaxis: { gridcolor: gc, zeroline: false, title: { text:'' } }, yaxis: { gridcolor: gc, zeroline: false, title: { text:'' } },
    polar: { angularaxis: { gridcolor: gc }, radialaxis: { gridcolor: gc } },
    ternary: { aaxis: { gridcolor: gc, linecolor: gc }, baxis: { gridcolor: gc, linecolor: gc }, caxis: { gridcolor: gc, linecolor: gc }, bgcolor: 'transparent' }
  };
}

async function drawMegaPlotly(targetElementId, data, type, isMini = false) {
  const targetEl = document.getElementById(targetElementId);
  if (targetEl) {
    targetEl.querySelectorAll('.spinner, .chart-loading-spinner').forEach(s => s.remove());
  }
  const preLoader = document.getElementById('megaChartLoader');
  if (preLoader) preLoader.remove();

  const mainColor = document.getElementById('chartColor')?.value || '#a78bfa';
  const bg = document.getElementById('chartBgColor')?.value || '#070711';
  const sGrid = document.getElementById('showGrid')?.checked ?? true;
  const sLeg = isMini ? false : (document.getElementById('showLegend')?.checked ?? true);
  const sz = parseInt(document.getElementById('traceSize')?.value || '5');

  let traces = [];
  const layout = buildLayout(bg, sGrid, sLeg, isMini);
  if (!isMini) {
    if (layout.xaxis && layout.xaxis.title) {
      layout.xaxis.title.text = document.getElementById('customXTitle')?.value || axisConfig.x || '';
    }
    if (layout.yaxis && layout.yaxis.title) {
      layout.yaxis.title.text = document.getElementById('customYTitle')?.value || (axisConfig.y.length ? axisConfig.y.join(', ') : '');
    }
  }

  const raw = data.raw || {}, agg = data.agg || {}, corr = data.corr || {};

  try {
    // ════════ 1. RAW DATA CHARTS ════════
    if (data.raw) {
      const keys = Object.keys(raw).filter(k => k !== '__x__');
      const xVals = raw['__x__'] || [];

      // 3D Çizgiler & Noktalar
      if (type === 'scatter3d' || type === 'line3d') {
        const zKey = keys[1] || keys[0];
        traces.push({
          type: 'scatter3d', mode: type === 'line3d' ? 'lines' : 'markers',
          x: xVals.length ? xVals : raw[keys[0]],
          y: raw[keys[0]] || xVals,
          z: raw[zKey] || raw[keys[0]],
          marker: { size: sz * 1.5, color: PALETTE },
          line: { width: sz, color: mainColor }
        });
      }
      // SPLOM / Scatter Matrix
      else if (type === 'scattermatrix') {
        traces.push({
          type: 'splom',
          dimensions: keys.map(k => ({ label: k, values: raw[k] })),
          marker: { color: mainColor, size: isMini ? 3 : 5 }
        });
      }
      // Parallel Coordinates & Categories
      else if (type === 'parcoords') {
        const numKeys = keys.filter(k => numericColumns.includes(k));
        const targetKeys = numKeys.length >= 2 ? numKeys : keys;
        traces.push({
          type: 'parcoords',
          dimensions: targetKeys.map(k => ({
            label: k,
            values: (raw[k] || []).map(v => Number(v) || 0)
          }))
        });
      }
      else if (type === 'parcats') {
        const allDimKeys = xVals.length ? ['__x__', ...keys] : keys;
        traces.push({
          type: 'parcats',
          dimensions: allDimKeys.map(k => ({
            label: k === '__x__' ? (axisConfig.x || 'Kategori') : k,
            values: k === '__x__' ? xVals : raw[k]
          }))
        });
      }
      // Finansal: Candlestick & OHLC
      else if (type === 'candlestick' || type === 'ohlc') {
        const y0 = keys[0] ? raw[keys[0]] : [];
        if (!y0 || y0.length === 0) {
          const el = document.getElementById(targetElementId);
          if (el) el.innerHTML = '<div style="color:var(--orange); padding:40px; text-align:center;">⚠️ Mum grafiği için en az bir sayısal fiyat sütunu seçiniz.</div>';
          return;
        }
        const openVals = keys[1] ? raw[keys[1]] : y0.map(v => v * 0.98);
        const highVals = keys[2] ? raw[keys[2]] : y0.map(v => v * 1.03);
        const lowVals = keys[3] ? raw[keys[3]] : y0.map(v => v * 0.95);
        const closeVals = y0;

        traces.push({
          type: type,
          x: xVals.length ? xVals : Array.from({length: y0.length}, (_, i) => i + 1),
          open: openVals, high: highVals, low: lowVals, close: closeVals
        });
        if (layout.xaxis) layout.xaxis.rangeslider = { visible: false };
      }
      // Ternary
      else if (type === 'ternary') {
        traces.push({
          type: 'scatterternary', mode: 'markers',
          a: raw[keys[0]] || [],
          b: raw[keys[1]] || raw[keys[0]] || [],
          c: raw[keys[2]] || raw[keys[0]] || [],
          marker: { color: mainColor, size: sz * 2 }
        });
      }
      // Scattergeo Coğrafi Harita
      else if (type === 'scattergeo') {
        keys.forEach((k, i) => {
          traces.push({
            type: 'scattergeo', mode: 'markers', name: k,
            lat: xVals.length ? xVals : raw[keys[0]],
            lon: raw[keys[1] || keys[0]],
            marker: { color: keys.length === 1 ? mainColor : PALETTE[i % 10], size: isMini ? sz * 2 : sz * 3, opacity: 0.8 }
          });
        });
        layout.geo = { bgcolor: 'transparent', showcoastlines: true, coastlinecolor: 'rgba(255,255,255,0.2)', showland: true, landcolor: 'rgba(255,255,255,0.05)' };
      }
      // Scatter & Bubble
      else if (['scatter', 'bubble'].includes(type)) {
        keys.forEach((k, i) => {
          traces.push({
            type: 'scatter', mode: 'markers', name: k,
            x: xVals.length ? xVals : undefined, y: raw[k],
            marker: { color: keys.length === 1 ? mainColor : PALETTE[i % 10], size: type === 'bubble' ? sz * 4 : (isMini ? sz * 2 : sz * 3), opacity: 0.75 }
          });
        });
      }
      // Histogram, Box, Violin, Strip, Rug
      else if (['histogram', 'box', 'violin', 'strip', 'rug'].includes(type)) {
        keys.forEach((k, i) => {
          let tr = {
            type: type === 'strip' || type === 'rug' ? 'scatter' : type,
            name: k,
            x: xVals.length && type !== 'histogram' ? xVals : undefined,
            y: raw[k],
            marker: { color: keys.length === 1 ? mainColor : PALETTE[i % 10] }
          };
          if (type === 'strip') { tr.mode = 'markers'; tr.marker.size = sz * 2; tr.marker.opacity = 0.6; }
          if (type === 'rug') { tr.mode = 'markers'; tr.marker.symbol = 'line-ns'; tr.marker.size = 14; }
          if (type === 'box') { tr.boxpoints = 'outliers'; }
          if (type === 'violin') { tr.points = 'none'; tr.box = { visible: true }; }
          traces.push(tr);
        });
        if (type === 'histogram') layout.barmode = 'overlay';
      }
      // 2D Density & 2D Histogram
      else if (type === 'histogram2d' || type === 'density2d') {
        if (keys.length > 0) {
          traces.push({
            type: type === 'density2d' ? 'histogram2dcontour' : 'histogram2d',
            x: xVals.length ? xVals : raw[keys[0]],
            y: raw[keys[0]],
            colorscale: 'Viridis'
          });
        }
      }
      else {
        keys.forEach(k => traces.push({ type: 'box', name: k, y: raw[k], marker: { color: mainColor } }));
      }
    }

    // ════════ 2. CORRELATION / MATRIX CHARTS ════════
    else if (data.corr) {
      traces.push({
        type: type === 'surface' ? 'surface' : (type === 'contour' || type === 'carpet' ? 'contour' : 'heatmap'),
        x: corr.labels, y: corr.labels, z: corr.matrix,
        colorscale: 'Blues', showscale: !isMini
      });
      if (['heatmap', 'contour', 'carpet'].includes(type)) {
        layout.xaxis.showgrid = false; layout.yaxis.showgrid = false;
      }
    }

    // ════════ 3. AGGREGATED CHARTS ════════
    else if (data.agg) {
      const keys = Object.keys(agg).filter(k => k !== '__x__');
      const xVals = agg['__x__'] || [];

      // Pie, Donut, Sunburst, Treemap, FunnelArea, Icicle, Sankey
      if (['pie', 'donut', 'funnelarea', 'sunburst', 'treemap', 'icicle', 'sankey'].includes(type)) {
        if (type === 'sankey') {
          let nodeLabels = [...xVals, ...keys];
          let source = [];
          let target = [];
          let value = [];
          
          keys.forEach((k, kIdx) => {
            let targetIdx = xVals.length + kIdx;
            xVals.forEach((x, xIdx) => {
              const val = Number(agg[k]?.[xIdx]) || 0;
              if (val > 0) {
                source.push(xIdx);
                target.push(targetIdx);
                value.push(val);
              }
            });
          });
          
          if (value.length === 0) {
            const el = document.getElementById(targetElementId);
            if (el) el.innerHTML = '<div style="color:var(--orange); padding:40px; text-align:center;">⚠️ Sankey akışı için en az bir pozitif sayısal değer ve kategori seçiniz.</div>';
            return;
          }
          
          traces.push({
            type: 'sankey', orientation: 'h',
            node: { pad: 15, thickness: 20, line: { color: 'black', width: 0.5 }, label: nodeLabels, color: PALETTE },
            link: { source: source, target: target, value: value }
          });
        } else {
          const k = keys[0];
          if (k) {
            let _labels = xVals;
            let _parents = ['sunburst', 'treemap', 'icicle'].includes(type) ? xVals.map(() => "") : undefined;
            let _values = agg[k];
            
            if (['sunburst', 'treemap', 'icicle'].includes(type)) {
               const cleanVals = (agg[k] || []).map(v => Math.max(0, Number(v) || 0));
               const totalVal = cleanVals.reduce((a, b) => a + b, 0);
               const rootLabel = 'Toplam';
               const safeLabels = xVals.map((x, idx) => {
                   let s = String(x || `Kategori ${idx + 1}`).trim();
                   return s === rootLabel ? s + ' ' : s;
               });
               _labels = [...safeLabels, rootLabel];
               _parents = [...safeLabels.map(() => rootLabel), ""];
               _values = [...cleanVals, totalVal];
            }
            
            traces.push({
              type: ['sunburst', 'treemap', 'icicle'].includes(type) ? type : (type === 'funnelarea' ? 'funnelarea' : 'pie'),
              labels: _labels,
              parents: _parents,
              [type === 'funnelarea' ? 'text' : 'labels']: _labels,
              values: _values,
              hole: type === 'donut' ? 0.5 : 0,
              marker: { colors: PALETTE }
            });
            if (layout.xaxis) layout.xaxis.visible = false;
            if (layout.yaxis) layout.yaxis.visible = false;
          }
        }
      }
      // Bullet / Indicator
      else if (type === 'bullet') {
        const k = keys[0] || 'Değer';
        const val = agg[k] ? agg[k][0] : 0;
        traces.push({
          type: 'indicator', mode: 'number+gauge+delta',
          value: val,
          title: { text: k, font: { size: 16 } },
          gauge: {
            shape: 'bullet',
            axis: { range: [0, val * 1.3] },
            bar: { color: mainColor },
            threshold: { line: { color: "#f87171", width: 3 }, thickness: 0.75, value: val * 0.9 }
          }
        });
      }
      // Polar Bar, Polar Scatter, Windrose
      else if (['polarbar', 'polarscatter', 'windrose'].includes(type)) {
        const k = keys[0];
        if (k) {
          traces.push({
            type: type === 'polarscatter' ? 'scatterpolar' : 'barpolar',
            mode: type === 'polarscatter' ? 'markers' : undefined,
            r: agg[k], theta: xVals,
            marker: { color: PALETTE, size: sz * 2.5 }
          });
        }
      }
      // Bars, Funnel, Waterfall, Radar, Dotplot, Errorbar
      else if (['bar', 'horizontalbar', 'groupedbar', 'stackedbar', 'funnel', 'waterfall', 'radar', 'dotplot', 'errorbar'].includes(type)) {
        keys.forEach((k, i) => {
          let tr = {};
          if (type === 'radar') {
            tr = { type: 'scatterpolar', name: k, r: agg[k], theta: xVals, fill: 'toself', marker: { color: keys.length === 1 ? mainColor : PALETTE[i % 10] } };
          } else if (type === 'funnel') {
            tr = { type: 'funnel', name: k, y: xVals, x: agg[k], marker: { color: keys.length === 1 ? mainColor : PALETTE[i % 10] } };
          } else if (type === 'waterfall') {
            tr = { type: 'waterfall', name: k, x: xVals, y: agg[k], marker: { color: keys.length === 1 ? mainColor : PALETTE[i % 10] } };
          } else if (type === 'dotplot') {
            tr = { type: 'scatter', mode: 'markers', name: k, x: xVals, y: agg[k], marker: { size: sz * 3.5, color: keys.length === 1 ? mainColor : PALETTE[i % 10] } };
          } else if (type === 'errorbar') {
            tr = { type: 'bar', name: k, x: xVals, y: agg[k], error_y: { type: 'data', array: agg[k].map(v => v * 0.08), visible: true }, marker: { color: keys.length === 1 ? mainColor : PALETTE[i % 10] } };
          } else {
            tr = { type: 'bar', name: k, [type === 'horizontalbar' ? 'y' : 'x']: xVals, [type === 'horizontalbar' ? 'x' : 'y']: agg[k], marker: { color: keys.length === 1 ? mainColor : PALETTE[i % 10] } };
            if (type === 'horizontalbar') tr.orientation = 'h';
          }
          traces.push(tr);
        });
        if (type === 'groupedbar') layout.barmode = 'group';
        if (type === 'stackedbar') layout.barmode = 'stack';
      }
      // Lines & Areas (Line, Spline, Step, Area, StackedArea)
      else {
        keys.forEach((k, i) => {
          let tr = {
            type: 'scatter', mode: 'lines+markers', name: k, x: xVals, y: agg[k],
            line: { color: keys.length === 1 ? mainColor : PALETTE[i % 10], width: sz },
            marker: { size: sz + 3, color: keys.length === 1 ? mainColor : PALETTE[i % 10] }
          };
          if (type === 'spline') tr.line.shape = 'spline';
          if (type === 'step') tr.line.shape = 'vhv';
          if (type === 'area' || type === 'stackedarea') tr.fill = i === 0 ? 'tozeroy' : (type === 'stackedarea' ? 'tonexty' : 'tozeroy');
          traces.push(tr);
        });
      }
    }

    // ════════ 4. CANLI TRENDLINE & KORELASYON OVERLAY ════════
    if (!isMini && targetElementId === 'chartArea') {
      const isXNum = axisConfig.x && numericColumns.includes(axisConfig.x);
      const firstY = axisConfig.y && axisConfig.y.length > 0 ? axisConfig.y[0] : null;
      const isYNum = firstY && numericColumns.includes(firstY);
      const badgeEl = document.getElementById('chartStatsBadge');
      const showTrend = document.getElementById('showTrendline')?.checked ?? false;
      const regModel = document.getElementById('regModelSelect')?.value || 'linear';
      const corrMethod = document.getElementById('corrMethodSelect')?.value || 'pearson';

      if (isXNum && isYNum) {
        try {
          const regRes = await fetch('/get_regression_curve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              x_col: axisConfig.x,
              y_col: firstY,
              model_type: regModel,
              corr_method: corrMethod,
              filters: activeFilters
            })
          });
          const regData = await regRes.json();
          if (regData.success && regData.regression && regData.correlation) {
            const reg = regData.regression;
            const corr = regData.correlation;

            // 1. Canlı İstatistik Sonuç Kartını Güncelle (Inspector)
            const corrSymbol = corrMethod === 'spearman' ? 'ρ' : (corrMethod === 'kendall' ? 'τ' : 'r');
            
            const corrMetricNameEl = document.getElementById('corrMetricName');
            if (corrMetricNameEl) corrMetricNameEl.textContent = corrSymbol;
            
            const statCorrValEl = document.getElementById('statCorrVal');
            if (statCorrValEl) statCorrValEl.textContent = corr.coef != null ? corr.coef.toFixed(4) : '-';
            
            const statInterpretationEl = document.getElementById('statInterpretation');
            if (statInterpretationEl) statInterpretationEl.textContent = corr.interpretation || '';

            const statR2ValEl = document.getElementById('statR2Val');
            if (statR2ValEl) statR2ValEl.textContent = reg.r_squared != null ? reg.r_squared.toFixed(4) : '-';

            const statEquationValEl = document.getElementById('statEquationVal');
            if (statEquationValEl) statEquationValEl.textContent = reg.equation || '-';

            const statPValEl = document.getElementById('statPVal');
            if (statPValEl) {
              if (corr.p_value != null) {
                statPValEl.textContent = corr.p_value < 0.0001 ? '< 0.0001' : corr.p_value.toFixed(4);
              } else {
                statPValEl.textContent = '-';
              }
            }

            const statSigBadgeEl = document.getElementById('statSignificanceBadge');
            if (statSigBadgeEl) {
              if (corr.p_value != null && corr.p_value < 0.05) {
                statSigBadgeEl.textContent = 'Anlamlı (p < 0.05)';
                statSigBadgeEl.style.background = 'rgba(52, 211, 153, 0.15)';
                statSigBadgeEl.style.color = '#34d399';
              } else if (corr.p_value != null) {
                statSigBadgeEl.textContent = 'Anlamsız (p ≥ 0.05)';
                statSigBadgeEl.style.background = 'rgba(251, 191, 36, 0.15)';
                statSigBadgeEl.style.color = '#fbbf24';
              } else {
                statSigBadgeEl.textContent = '-';
              }
            }

            // 2. Trendline Çizgisi Ekle (Eğer Kullanıcı İstemişse)
            if (showTrend && reg.trend_x && reg.trend_x.length > 0) {
              traces.push({
                type: 'scatter',
                mode: 'lines',
                name: `Trend: ${reg.equation}`,
                x: reg.trend_x,
                y: reg.trend_y,
                line: {
                  color: '#f59e0b',
                  width: 3,
                  dash: 'dash'
                },
                hoverinfo: 'x+y+name'
              });

              // Rozeti Göster ve Doldur
              if (badgeEl) {
                badgeEl.classList.remove('hidden');
                const csbEquation = document.getElementById('csbEquation');
                const csbR2 = document.getElementById('csbR2');
                const csbCorrName = document.getElementById('csbCorrName');
                const csbCorr = document.getElementById('csbCorr');

                if (csbEquation) csbEquation.textContent = reg.equation;
                if (csbR2) csbR2.textContent = reg.r_squared != null ? reg.r_squared.toFixed(4) : '-';
                if (csbCorrName) csbCorrName.textContent = corrSymbol;
                if (csbCorr) csbCorr.textContent = corr.coef != null ? corr.coef.toFixed(4) : '-';
              }
            } else {
              if (badgeEl) badgeEl.classList.add('hidden');
            }
          }
        } catch (regErr) {
          console.warn('Regresyon eğrisi yüklenirken hata:', regErr);
          if (badgeEl) badgeEl.classList.add('hidden');
        }
      } else {
        if (badgeEl) badgeEl.classList.add('hidden');
        const statInterpretationEl = document.getElementById('statInterpretation');
        if (statInterpretationEl) statInterpretationEl.textContent = 'Korelasyon ve regresyon için X ve Y eksenlerinin her ikisinin de sayısal olması gerekir.';
        const statEquationValEl = document.getElementById('statEquationVal');
        if (statEquationValEl) statEquationValEl.textContent = 'Sayısal değişken seçilmedi';
        const statCorrValEl = document.getElementById('statCorrVal');
        if (statCorrValEl) statCorrValEl.textContent = '-';
        const statR2ValEl = document.getElementById('statR2Val');
        if (statR2ValEl) statR2ValEl.textContent = '-';
        const statPValEl = document.getElementById('statPVal');
        if (statPValEl) statPValEl.textContent = '-';
      }
    }

    if (targetEl) {
      targetEl.querySelectorAll('.spinner, .chart-loading-spinner').forEach(s => s.remove());
    }
    const midLoader = document.getElementById('megaChartLoader');
    if (midLoader) midLoader.remove();

    await Plotly.newPlot(targetElementId, traces, layout, { responsive: true, displayModeBar: !isMini, displaylogo: false });

    const postLoader = document.getElementById('megaChartLoader');
    if (postLoader) postLoader.remove();
    if (targetEl) {
      targetEl.querySelectorAll('.spinner, .chart-loading-spinner').forEach(s => s.remove());
    }

  } catch(err) {
    const postLoader = document.getElementById('megaChartLoader');
    if (postLoader) postLoader.remove();
    const el = document.getElementById(targetElementId);
    if (el) el.innerHTML = `<div style="color:var(--red); padding:20px; font-size:0.85rem;">❌ Çizim Hatası: ${err.message}</div>`;
  }
}

// Window export
window.CHARTS = CHARTS;
window.buildLayout = buildLayout;
window.drawMegaPlotly = drawMegaPlotly;