/**
 * DataViz Pro — Regression & Correlation Studio Module
 * Comprehensive Scatter, Fitted Curves, Confidence Intervals, and Heatmap Matrix
 */

(function () {
  let regCurrentData = null;
  let regCurrentMatrix = null;
  let isRegInitialized = false;

  function initRegressionStudio() {
    populateRegColumnSelects();
    bindRegEvents();
    isRegInitialized = true;
  }

  function populateRegColumnSelects() {
    const selX = document.getElementById('regSelectX');
    const selY = document.getElementById('regSelectY');
    if (!selX || !selY) return;

    const numCols = window.numericColumns && window.numericColumns.length > 0 
      ? window.numericColumns 
      : (window.columns || []);

    selX.innerHTML = '';
    selY.innerHTML = '';

    numCols.forEach(col => {
      const optX = document.createElement('option');
      optX.value = col;
      optX.textContent = col;
      selX.appendChild(optX);

      const optY = document.createElement('option');
      optY.value = col;
      optY.textContent = col;
      selY.appendChild(optY);
    });

    // Smart default selection
    const curX = window.axisConfig?.x;
    const curY = window.axisConfig?.y?.[0];

    if (curX && numCols.includes(curX)) {
      selX.value = curX;
    } else if (numCols.length > 0) {
      selX.value = numCols[0];
    }

    if (curY && numCols.includes(curY) && curY !== selX.value) {
      selY.value = curY;
    } else if (numCols.length > 1) {
      selY.value = numCols[1];
    } else if (numCols.length > 0) {
      selY.value = numCols[0];
    }
  }

  function bindRegEvents() {
    document.getElementById('btnRunRegStudio')?.addEventListener('click', () => {
      fetchAndRenderRegressionStudio();
    });

    document.getElementById('regSelectX')?.addEventListener('change', () => {
      fetchAndRenderRegressionStudio();
    });

    document.getElementById('regSelectY')?.addEventListener('change', () => {
      fetchAndRenderRegressionStudio();
    });

    document.getElementById('regSelectModel')?.addEventListener('change', () => {
      fetchAndRenderRegressionStudio();
    });

    document.getElementById('regSelectCorrMethod')?.addEventListener('change', () => {
      fetchAndRenderRegressionStudio();
    });

    document.getElementById('regToggleCiBand')?.addEventListener('change', () => {
      if (regCurrentData) renderRegressionScatterPlot(regCurrentData);
    });

    document.getElementById('btnPinRegChart')?.addEventListener('click', pinRegressionToDashboard);

    document.getElementById('btnDownloadRegPng')?.addEventListener('click', () => {
      const chartEl = document.getElementById('regScatterPlotArea');
      if (chartEl && window.Plotly) {
        Plotly.downloadImage(chartEl, {
          format: 'png',
          filename: `Regresyon_${document.getElementById('regSelectX')?.value}_vs_${document.getElementById('regSelectY')?.value}`,
          height: 600,
          width: 900
        });
      }
    });
  }

  async function fetchAndRenderRegressionStudio() {
    const selX = document.getElementById('regSelectX');
    const selY = document.getElementById('regSelectY');
    if (!selX || !selY) return;

    let xCol = selX.value;
    let yCol = selY.value;

    if (!xCol || !yCol) {
      populateRegColumnSelects();
      xCol = selX.value;
      yCol = selY.value;
    }

    if (!xCol || !yCol) return;

    const modelType = document.getElementById('regSelectModel')?.value || 'linear';
    const corrMethod = document.getElementById('regSelectCorrMethod')?.value || 'pearson';
    const filters = window.activeFilters || [];

    // Loading indicator
    const scatterArea = document.getElementById('regScatterPlotArea');
    if (scatterArea) {
      scatterArea.innerHTML = '<div style="display:flex; height:100%; align-items:center; justify-content:center; color:var(--muted);"><div class="spinner" style="margin-right:12px;"></div> Model hesaplanıyor...</div>';
    }

    try {
      // Parallel fetch for regression curve & correlation matrix
      const [regRes, matRes] = await Promise.all([
        fetch('/get_regression_studio_data', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            x_col: xCol,
            y_col: yCol,
            model_type: modelType,
            corr_method: corrMethod,
            filters: filters,
            max_scatter: 3000
          })
        }),
        fetch('/get_correlation_matrix', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            method: corrMethod,
            filters: filters
          })
        })
      ]);

      let regData = {};
      try {
        regData = await regRes.json();
      } catch (e) {
        regData = { error: `Sunucu yanıtı okunamadı (${regRes.status})` };
      }

      let matData = {};
      try {
        matData = await matRes.json();
      } catch (e) {
        matData = { error: `Matris yanıtı okunamadı (${matRes.status})` };
      }

      if (regRes.ok && regData.success) {
        regCurrentData = regData;
        updateRegDiagnosticBadges(regData);
        renderRegressionScatterPlot(regData);
        renderRegAiInsight(regData);
      } else {
        if (scatterArea) {
          scatterArea.innerHTML = `<div style="display:flex; height:100%; align-items:center; justify-content:center; color:var(--red); padding:20px; text-align:center;">Hata: ${regData.error || 'Regresyon modeli hesaplanamadı.'}</div>`;
        }
      }

      if (matRes.ok && matData.matrix) {
        regCurrentMatrix = matData;
        renderCorrelationHeatmap(matData);
      }
    } catch (err) {
      console.error('fetchAndRenderRegressionStudio hatası:', err);
      if (scatterArea) {
        scatterArea.innerHTML = `<div style="display:flex; height:100%; align-items:center; justify-content:center; color:var(--red); padding:20px; text-align:center;">Bağlantı hatası: ${err.message}</div>`;
      }
    }
  }

  function updateRegDiagnosticBadges(data) {
    const corr = data.correlation || {};
    const reg = data.regression || {};

    const methodSymbol = data.corr_method === 'spearman' ? 'ρ' : (data.corr_method === 'kendall' ? 'τ' : 'r');
    const lblCorr = document.getElementById('regMetricCorrLabel');
    if (lblCorr) lblCorr.textContent = methodSymbol;

    const valCorr = document.getElementById('regValCorr');
    if (valCorr) {
      valCorr.textContent = corr.coef != null ? `${methodSymbol} = ${corr.coef.toFixed(4)}` : '-';
    }

    const valCorrInterp = document.getElementById('regValCorrInterp');
    if (valCorrInterp) {
      valCorrInterp.textContent = corr.interpretation || 'İlişki Gücü';
    }

    const valR2 = document.getElementById('regValR2');
    if (valR2) {
      const r2 = reg.r_squared != null ? (reg.r_squared * 100).toFixed(1) : 0;
      valR2.textContent = `%${r2}`;
    }

    const valP = document.getElementById('regValP');
    const valPBadge = document.getElementById('regValPBadge');
    if (valP) {
      const p = reg.p_value != null ? reg.p_value : corr.p_value;
      if (p != null) {
        valP.textContent = p < 0.0001 ? '< 0.0001' : p.toFixed(4);
        if (valPBadge) valPBadge.textContent = p < 0.05 ? 'p < 0.05 (Güvenilir)' : 'p ≥ 0.05 (Anlamsız)';
      } else {
        valP.textContent = '-';
        if (valPBadge) valPBadge.textContent = 'p değeri yok';
      }
    }

    const valSe = document.getElementById('regValSe');
    if (valSe) {
      valSe.textContent = reg.se != null ? `±${reg.se.toFixed(4)}` : '±0.000';
    }

    const valEq = document.getElementById('regValEquation');
    if (valEq) {
      valEq.textContent = reg.equation || 'y = mx + c';
    }

    const badgeSample = document.getElementById('regScatterSampleBadge');
    if (badgeSample) {
      badgeSample.textContent = `${(data.total_valid || 0).toLocaleString()} Veriden ${data.scatter_sample_count || 0} Nokta`;
    }
  }

  function renderRegressionScatterPlot(data) {
    const container = document.getElementById('regScatterPlotArea');
    if (!container || !window.Plotly) return;

    const traces = [];
    const showCi = document.getElementById('regToggleCiBand')?.checked;

    // 1. Scatter Points Trace (Standard SVG scatter for universal cross-browser reliability)
    traces.push({
      x: data.scatter_x,
      y: data.scatter_y,
      mode: 'markers',
      type: 'scatter',
      name: 'Örneklem Verisi',
      marker: {
        color: '#38bdf8',
        size: 5,
        opacity: 0.55,
        line: { color: 'rgba(255,255,255,0.2)', width: 0.5 }
      },
      hovertemplate: `<b>${data.x_col}:</b> %{x}<br><b>${data.y_col}:</b> %{y}<extra></extra>`
    });

    const reg = data.regression || {};

    // 2. 95% Confidence Interval Band (if available & toggled)
    if (showCi && reg.ci_lower && reg.ci_upper && reg.ci_lower.length > 0) {
      // Lower bound
      traces.push({
        x: reg.trend_x,
        y: reg.ci_lower,
        mode: 'lines',
        type: 'scatter',
        line: { color: 'rgba(56, 189, 248, 0)', width: 0 },
        showlegend: false,
        hoverinfo: 'skip'
      });

      // Upper bound with fill
      traces.push({
        x: reg.trend_x,
        y: reg.ci_upper,
        mode: 'lines',
        type: 'scatter',
        fill: 'tonexty',
        fillcolor: 'rgba(56, 189, 248, 0.12)',
        line: { color: 'rgba(56, 189, 248, 0)', width: 0 },
        name: '%95 Güven Aralığı',
        hoverinfo: 'skip'
      });
    }

    // 3. Fitted Regression Curve
    if (reg.trend_x && reg.trend_y && reg.trend_x.length > 0) {
      traces.push({
        x: reg.trend_x,
        y: reg.trend_y,
        mode: 'lines',
        type: 'scatter',
        name: `Model: ${reg.model_type?.toUpperCase() || 'TREND'}`,
        line: {
          color: '#f59e0b',
          width: 3.5
        },
        hovertemplate: `<b>Tahmin (${data.y_col}):</b> %{y:.2f}<extra></extra>`
      });
    }

    const layout = {
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      margin: { l: 60, r: 25, t: 25, b: 50 },
      font: {
        family: 'Inter, system-ui, sans-serif',
        color: '#94a3b8',
        size: 11
      },
      xaxis: {
        title: { text: data.x_col, font: { size: 12, color: '#f1f5f9' } },
        gridcolor: 'rgba(255, 255, 255, 0.06)',
        zerolinecolor: 'rgba(255, 255, 255, 0.12)',
        tickfont: { color: '#94a3b8' }
      },
      yaxis: {
        title: { text: data.y_col, font: { size: 12, color: '#f1f5f9' } },
        gridcolor: 'rgba(255, 255, 255, 0.06)',
        zerolinecolor: 'rgba(255, 255, 255, 0.12)',
        tickfont: { color: '#94a3b8' }
      },
      legend: {
        orientation: 'h',
        x: 0,
        y: 1.08,
        font: { size: 11, color: '#cbd5e1' },
        bgcolor: 'transparent'
      },
      hovermode: 'closest',
      annotations: [
        {
          x: 0.98,
          y: 0.04,
          xref: 'paper',
          yref: 'paper',
          text: `<b>${reg.equation || ''}</b><br>R² = ${(reg.r_squared || 0).toFixed(4)}`,
          showarrow: false,
          font: { family: 'JetBrains Mono, monospace', size: 11, color: '#fbbf24' },
          bgcolor: 'rgba(15, 23, 42, 0.85)',
          bordercolor: 'rgba(245, 158, 11, 0.3)',
          borderwidth: 1,
          borderpad: 6,
          align: 'right'
        }
      ]
    };

    const config = {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['lasso2d', 'select2d']
    };

    container.innerHTML = '';
    try {
      Plotly.newPlot(container, traces, layout, config);
    } catch (err) {
      console.error('Plotly draw error:', err);
      container.innerHTML = `<div style="display:flex; height:100%; align-items:center; justify-content:center; color:var(--red); padding:20px; text-align:center;">Grafik çizilemedi: ${err.message}</div>`;
    }
  }

  function renderCorrelationHeatmap(data) {
    const container = document.getElementById('regHeatmapPlotArea');
    if (!container || !window.Plotly || !data.columns || data.columns.length < 2) {
      if (container) {
        container.innerHTML = '<div style="display:flex; height:100%; align-items:center; justify-content:center; color:var(--muted); font-size:0.8rem;">En az 2 sayısal sütun gereklidir.</div>';
      }
      return;
    }

    const cols = data.columns;
    const zValues = data.matrix;

    // Text matrix annotations for each cell
    const textValues = zValues.map(row => row.map(v => (v != null ? v.toFixed(2) : '0.00')));

    const trace = {
      z: zValues,
      x: cols,
      y: cols,
      type: 'heatmap',
      colorscale: [
        [0.0, '#f43f5e'],   // Strong negative (red/pink)
        [0.5, '#0f172a'],   // Zero (dark navy)
        [1.0, '#38bdf8']    // Strong positive (cyan/sky)
      ],
      zmin: -1.0,
      zmax: 1.0,
      text: textValues,
      texttemplate: '%{text}',
      textfont: {
        family: 'JetBrains Mono, monospace',
        size: cols.length > 8 ? 9 : 11,
        color: '#ffffff'
      },
      showscale: true,
      colorbar: {
        len: 0.85,
        thickness: 10,
        tickfont: { size: 9, color: '#94a3b8' }
      },
      hovertemplate: '<b>%{y}</b> ↔ <b>%{x}</b><br>Korelasyon: <b>%{z:.4f}</b><extra></extra>'
    };

    const layout = {
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      margin: { l: 80, r: 20, t: 15, b: 60 },
      font: {
        family: 'Inter, system-ui, sans-serif',
        color: '#94a3b8',
        size: 10
      },
      xaxis: {
        tickangle: -35,
        tickfont: { size: 10, color: '#cbd5e1' }
      },
      yaxis: {
        autorange: 'reversed',
        tickfont: { size: 10, color: '#cbd5e1' }
      }
    };

    const config = {
      responsive: true,
      displayModeBar: false
    };

    Plotly.react('regHeatmapPlotArea', [trace], layout, config);

    // Interactive Click: Change X and Y variables when user clicks on a heatmap cell
    container.removeAllListeners && container.removeAllListeners('plotly_click');
    container.on('plotly_click', d => {
      if (d && d.points && d.points[0]) {
        const pt = d.points[0];
        const clickedX = pt.x;
        const clickedY = pt.y;

        const selX = document.getElementById('regSelectX');
        const selY = document.getElementById('regSelectY');
        if (selX && selY && clickedX && clickedY && clickedX !== clickedY) {
          selX.value = clickedX;
          selY.value = clickedY;
          fetchAndRenderRegressionStudio();
        }
      }
    });
  }

  function renderRegAiInsight(data) {
    const box = document.getElementById('regAiInsightText');
    if (!box) return;

    const insight = data.insight || {};
    const corr = data.correlation || {};
    const reg = data.regression || {};

    let html = `<p style="margin: 0 0 10px 0; font-size: 0.85rem; line-height: 1.55;">${insight.text || 'İstatistiksel model oluşturuldu.'}</p>`;

    if (insight.key_findings && insight.key_findings.length > 0) {
      html += '<ul style="margin: 0; padding-left: 18px; display: flex; flex-direction: column; gap: 4px;">';
      insight.key_findings.forEach(kf => {
        html += `<li style="font-size: 0.8rem; color: #cbd5e1;">${kf}</li>`;
      });
      html += '</ul>';
    } else {
      const strength = corr.interpretation || 'belirli';
      const r2Pct = ((reg.r_squared || 0) * 100).toFixed(1);
      html += `
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 10px; margin-top: 6px;">
          <div style="color: #38bdf8; font-weight: 700; margin-bottom: 2px;">📈 Yönetici Özeti:</div>
          <div style="color: #cbd5e1; font-size: 0.78rem;">
            <strong>${data.x_col}</strong> ile <strong>${data.y_col}</strong> değişkenleri arasında <strong>${strength}</strong> bir ilişki gözlenmiştir.
            Kurulan regresyon modeli <strong>${reg.equation}</strong> bağımlı değişkendeki varyansın <strong>%${r2Pct}</strong>'lik kısmını başarıyla açıklamaktadır.
          </div>
        </div>
      `;
    }

    box.innerHTML = html;
  }

  function pinRegressionToDashboard() {
    if (!regCurrentData) {
      alert('Lütfen önce bir regresyon modeli hesaplayın.');
      return;
    }

    const reg = regCurrentData.regression || {};
    const corr = regCurrentData.correlation || {};
    const title = `${regCurrentData.x_col} & ${regCurrentData.y_col} Regresyon Analizi`;

    if (typeof window.addChartToDashboard === 'function') {
      window.addChartToDashboard({
        title: title,
        type: 'scatter',
        xCol: regCurrentData.x_col,
        yCol: regCurrentData.y_col,
        data: {
          x: regCurrentData.scatter_x,
          y: regCurrentData.scatter_y,
          trend_x: reg.trend_x,
          trend_y: reg.trend_y,
          equation: reg.equation,
          r_squared: reg.r_squared,
          corr: corr.coef
        },
        isCustomRegression: true
      });

      alert(`📌 "${title}" başarıyla Çoklu Gösterge Panosuna eklendi!`);
    } else {
      alert('Panoya ekleme fonksiyonu bulunamadı.');
    }
  }

  function openRegressionStudioWithVars(xCol, yCol, modelType = 'linear') {
    if (typeof window.goToStep3 === 'function') {
      window.goToStep3();
    }

    // Switch to regression tab
    const regTabBtn = document.getElementById('tabBtnRegression');
    if (regTabBtn) {
      regTabBtn.click();
    }

    setTimeout(() => {
      populateRegColumnSelects();
      const selX = document.getElementById('regSelectX');
      const selY = document.getElementById('regSelectY');
      const selM = document.getElementById('regSelectModel');

      if (selX && xCol) selX.value = xCol;
      if (selY && yCol) selY.value = yCol;
      if (selM && modelType) selM.value = modelType;

      fetchAndRenderRegressionStudio();
    }, 200);
  }

  // Global exports
  window.initRegressionStudio = initRegressionStudio;
  window.fetchAndRenderRegressionStudio = fetchAndRenderRegressionStudio;
  window.populateRegColumnSelects = populateRegColumnSelects;
  window.openRegressionStudioWithVars = openRegressionStudioWithVars;
})();
