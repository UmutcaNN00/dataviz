/* ════════════════════════════════════════════════════════════
   DATAVIZ PRO V6 — DASHBOARD & KPI STUDIO MODULE
   Executive KPI Tiles, Multi-Chart Dashboard Grid & Pivot Widgets
════════════════════════════════════════════════════════════ */

/* ── 1. EXECUTIVE KPI ÖZETLERİ ── */
async function fetchKpis() {
  try {
    const res = await fetch("/get_kpi_summary", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        x: axisConfig.x,
        x_col: axisConfig.x,
        y: axisConfig.y,
        y_cols: axisConfig.y,
        filters: activeFilters,
      }),
    });
    const data = await res.json();
    if (res.ok && data.kpis) {
      currentKpis = data.kpis;
      window.currentKpis = currentKpis;
      renderKpiTiles("chartKpiStrip", currentKpis);
      renderKpiTiles("dashboardKpiGrid", currentKpis);
      renderKpiTiles("kpiTilesRow", currentKpis);
    }
  } catch (e) {
    console.error("KPI fetch error:", e);
  }
}

function renderKpiTiles(targetId, kpiList) {
  const container = document.getElementById(targetId);
  if (!container || !kpiList || kpiList.length === 0) return;
  container.innerHTML = "";

  kpiList.forEach((k) => {
    const tile = document.createElement("div");
    tile.className = `kpi-tile-card ${k.color || "blue"}`;
    tile.innerHTML = `
      <div class="kpi-tile-header">
        <span class="kpi-tile-title">${k.title || k.label || ""}</span>
        <span class="kpi-tile-icon">${k.icon || "📌"}</span>
      </div>
      <div class="kpi-tile-val">${k.value || ""}</div>
      <div class="kpi-tile-sub">${k.sub || k.change || ""}</div>
    `;
    container.appendChild(tile);
  });
}

/* ── 2. ÇOKLU PANO (DASHBOARD CANVAS) SİSTEMİ ── */
function updateDashboardBadge() {
  ["dashBadgeCount", "dashItemCount"].forEach((id) => {
    const badge = document.getElementById(id);
    if (!badge) return;
    badge.textContent = dashboardCharts.length;
    if (id === "dashItemCount") {
      if (dashboardCharts.length > 0) {
        badge.classList.remove("hidden");
      } else {
        badge.classList.add("hidden");
      }
    }
  });
}

function addChartToDashboard(chartItem) {
  if (!chartItem) return null;
  const item = {
    id:
      chartItem.id ||
      "dash_" + Date.now() + "_" + Math.floor(Math.random() * 1000),
    title: chartItem.title || "Grafik",
    chartType: chartItem.chartType || chartItem.type || "scatter",
    chartData: chartItem.chartData || null,
    pivotData: chartItem.pivotData || null,
    isCustomRegression: !!chartItem.isCustomRegression,
    regData: chartItem.data || chartItem.regData || null,
    plotlyTraces: chartItem.plotlyTraces || null,
    plotlyLayout: chartItem.plotlyLayout || null,
    xCol: chartItem.xCol || null,
    yCol: chartItem.yCol || null,
    filtersCount: activeFilters ? activeFilters.length : 0,
  };
  dashboardCharts.push(item);
  window.dashboardCharts = dashboardCharts;
  updateDashboardBadge();
  renderDashboardGrid();
  return item;
}

function renderDashboardGrid() {
  const grid =
    document.getElementById("dashboardGrid") ||
    document.getElementById("dashboardChartsGrid");
  if (!grid) return;
  grid.innerHTML = "";

  if (dashboardCharts.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; padding: 40px; text-align: center; color: var(--muted); border: 2px dashed rgba(255,255,255,0.08); border-radius: 12px;">
        Panoda henüz kaydedilmiş grafik yok. Üst kısımdaki <strong>"📌 Panoya Ekle"</strong> butonunu kullanarak grafikleri panoya ekleyebilirsiniz.
      </div>
    `;
    return;
  }

  dashboardCharts.forEach((item, idx) => {
    const card = document.createElement("div");
    card.className = "dash-card";
    card.dataset.id = item.id;

    if (item.chartType === "pivot") {
      card.innerHTML = `
        <div class="dash-card-header">
          <div class="dash-card-title" contenteditable="true" data-idx="${idx}">${item.title}</div>
          <div class="dash-card-actions">
            <button class="dash-act-btn btn-dash-del" data-idx="${idx}" title="Kaldır">✕</button>
          </div>
        </div>
        <div class="dash-card-plot" id="plot_${item.id}" style="overflow-x: auto; padding: 10px;"></div>
      `;
      grid.appendChild(card);
      renderDashboardPivotTable(`plot_${item.id}`, item.pivotData);
    } else if (item.isCustomRegression && (item.plotlyTraces || item.regData)) {
      card.innerHTML = `
        <div class="dash-card-header">
          <div class="dash-card-title" contenteditable="true" data-idx="${idx}">${item.title}</div>
          <div class="dash-card-actions">
            <button class="dash-act-btn btn-dash-del" data-idx="${idx}" title="Kaldır">✕</button>
          </div>
        </div>
        <div class="dash-card-plot" id="plot_${item.id}"></div>
      `;
      grid.appendChild(card);
      const plotEl = document.getElementById(`plot_${item.id}`);
      if (plotEl && window.Plotly) {
        let traces = item.plotlyTraces;
        let layout = item.plotlyLayout;
        if (!traces && item.regData) {
          const rd = item.regData;
          traces = [
            {
              x: rd.x || [],
              y: rd.y || [],
              mode: "markers",
              type: "scatter",
              name: "Örneklem",
              marker: { color: "#38bdf8", size: 4, opacity: 0.6 },
            },
          ];
          if (rd.trend_x && rd.trend_y) {
            traces.push({
              x: rd.trend_x,
              y: rd.trend_y,
              mode: "lines",
              type: "scatter",
              name: rd.equation || "Regresyon",
              line: { color: "#f59e0b", width: 2.5 },
            });
          }
        }
        if (!layout) {
          layout = {
            autosize: true,
            paper_bgcolor: "transparent",
            plot_bgcolor: "#070711",
            font: { family: "Inter", color: "#94a3b8", size: 10 },
            margin: { t: 15, r: 15, b: 35, l: 45 },
            showlegend: false,
            xaxis: {
              title: { text: item.xCol || "" },
              gridcolor: "rgba(255,255,255,0.08)",
              zeroline: false,
            },
            yaxis: {
              title: { text: item.yCol || "" },
              gridcolor: "rgba(255,255,255,0.08)",
              zeroline: false,
            },
          };
        }
        Plotly.newPlot(plotEl, traces, layout, {
          responsive: true,
          displayModeBar: false,
          displaylogo: false,
        });
      }
    } else {
      card.innerHTML = `
        <div class="dash-card-header">
          <div class="dash-card-title" contenteditable="true" data-idx="${idx}">${item.title}</div>
          <div class="dash-card-actions">
            <button class="dash-act-btn btn-dash-del" data-idx="${idx}" title="Kaldır">✕</button>
          </div>
        </div>
        <div class="dash-card-plot" id="plot_${item.id}"></div>
      `;
      grid.appendChild(card);
      if (typeof drawMegaPlotly === "function") {
        drawMegaPlotly(`plot_${item.id}`, item.chartData, item.chartType, true);
      } else if (typeof window.drawMegaPlotly === "function") {
        window.drawMegaPlotly(
          `plot_${item.id}`,
          item.chartData,
          item.chartType,
          true,
        );
      }
    }
  });

  setupDashboardEvents();
}

function renderDashboardPivotTable(containerId, data) {
  const container = document.getElementById(containerId);
  if (!container || !data) return;

  let html = `<table class="pivot-matrix-table" style="font-size: 0.78rem;">`;
  html += `<thead><tr>`;
  (data.index_names || []).forEach((name) => {
    html += `<th class="pmt-corner">${name}</th>`;
  });
  (data.column_headers || []).forEach((h) => {
    html += `<th class="pmt-col-header">${h}</th>`;
  });
  html += `</tr></thead><tbody>`;

  (data.rows || []).forEach((r) => {
    html += `<tr>`;
    (r.row_labels || []).forEach((lbl) => {
      html += `<td class="pmt-row-header">${lbl}</td>`;
    });
    (r.cells || []).forEach((val) => {
      let formattedVal = val.toLocaleString("tr-TR", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
      });
      html += `<td class="pmt-val-cell">${formattedVal}</td>`;
    });
    html += `</tr>`;
  });

  html += `</tbody></table>`;
  container.innerHTML = html;
}

function setupDashboardEvents() {
  document.querySelectorAll(".btn-dash-del").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const idx = parseInt(e.currentTarget.dataset.idx);
      dashboardCharts.splice(idx, 1);
      window.dashboardCharts = dashboardCharts;
      updateDashboardBadge();
      renderDashboardGrid();
    });
  });
  document
    .querySelectorAll('.dash-card-title[contenteditable="true"]')
    .forEach((titleEl) => {
      titleEl.addEventListener("blur", (e) => {
        const idx = parseInt(e.currentTarget.dataset.idx);
        if (dashboardCharts[idx]) {
          dashboardCharts[idx].title =
            e.currentTarget.textContent.trim() || dashboardCharts[idx].title;
        }
      });
    });
}

// Window export
window.fetchKpis = fetchKpis;
window.renderKpiTiles = renderKpiTiles;
window.updateDashboardBadge = updateDashboardBadge;
window.addChartToDashboard = addChartToDashboard;
window.renderDashboardGrid = renderDashboardGrid;
window.renderDashboardPivotTable = renderDashboardPivotTable;
window.setupDashboardEvents = setupDashboardEvents;
