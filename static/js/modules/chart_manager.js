/* ════════════════════════════════════════════════════════════
   DATAVIZ PRO V6 — CHART MANAGER MODULE
   Drag & Drop Pool, Chart Grid, Evaluation Engine,
   Filters (Slicers), Dashboard Canvas, Stats & Inspector
════════════════════════════════════════════════════════════ */

var currentPoolFilter = "all";
var currentPoolSearch = "";

/* ── 1. DRAG & DROP POOL (STEP 2) ── */
function initDragDropPool(preserveAxes = false) {
  const pool = document.getElementById("colPool");
  if (!pool) return;

  const prevX = preserveAxes && axisConfig ? axisConfig.x : null;
  const prevY =
    preserveAxes && axisConfig && Array.isArray(axisConfig.y)
      ? [...axisConfig.y]
      : [];

  // Create a grid layout for split view (X and Y)
  pool.innerHTML = `
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; width: 100%;">
      <div id="poolLeftCat"></div>
      <div id="poolRightNum"></div>
    </div>
  `;

  const poolLeft = document.getElementById("poolLeftCat");
  const poolRight = document.getElementById("poolRightNum");

  axisConfig = { x: null, y: [] };
  window.axisConfig = axisConfig;

  const xZone = document.getElementById("xZone");
  const yZone = document.getElementById("yZone");
  if (xZone) xZone.innerHTML = "Sütunu Buraya Bırakın";
  if (yZone) yZone.innerHTML = "Sütunları Buraya Bırakın";

  updatePoolCounts();

  const catCols = globalColumns.filter((c) => !numericColumns.includes(c));
  const numCols = globalColumns.filter((c) => numericColumns.includes(c));

  // Render Categorical (X) side
  renderPoolSection(
    poolLeft,
    "🔤 Metin / Kategori (Genellikle X)",
    catCols,
    "section_cat",
  );

  // Render Numeric (Y) side
  renderPoolSection(
    poolRight,
    "🔢 Sayısal Değer (Genellikle Y)",
    numCols,
    "section_num",
  );

  if (preserveAxes) {
    if (prevX && globalColumns.includes(prevX)) {
      assignPillToZone(prevX, "xZone");
    }
    prevY.forEach((yc) => {
      if (globalColumns.includes(yc)) {
        assignPillToZone(yc, "yZone");
      }
    });
  }
}

function renderPoolSection(parentContainer, titleText, cols, sectionId) {
  if (!cols.length) return;

  const group = document.createElement("div");
  group.className = "pool-section-group";
  group.id = sectionId;

  group.innerHTML = `
    <div class="pool-section-title">
      <span>${titleText}</span>
      <span style="font-size:0.7rem; font-weight:700; color:var(--muted);">${cols.length} Sütun</span>
    </div>
    <div class="pool-section-pills" id="pills_${sectionId}"></div>
  `;

  const pillsBox = group.querySelector(".pool-section-pills");

  // Kategorik önce, Sayısal sonra sırala
  const sorted = [...cols].sort((a, b) => {
    const aNum = numericColumns.includes(a) ? 1 : 0;
    const bNum = numericColumns.includes(b) ? 1 : 0;
    return aNum - bNum;
  });

  sorted.forEach((col) => {
    const isNum = numericColumns.includes(col);
    const isCalc = calculatedColumns.includes(col);
    const isJoin = joinedColumns.includes(col);

    const pill = document.createElement("div");
    pill.className = `col-pill ${isCalc ? "calc-pill" : ""} ${isJoin ? "join-pill" : ""}`;
    pill.draggable = true;
    pill.dataset.col = col;
    pill.dataset.type = isNum ? "num" : "cat";
    pill.dataset.origin = isJoin ? "joined" : isCalc ? "calc" : "file1";
    pill.dataset.section = `pills_${sectionId}`;

    let typeTag = isNum ? "#" : "T";
    let tagBadge = "";
    if (isJoin) {
      tagBadge = `<span class="join-tag-badge">🔗 Dosya 2</span>`;
    } else if (isCalc) {
      tagBadge = `<span style="color:var(--purple); font-weight:800; font-size:0.75rem; margin-right:2px;">fx</span>`;
    }

    pill.innerHTML = `${tagBadge}<span style="opacity:0.65; font-size:0.75rem; font-weight:800;">${typeTag}</span> <span>${col}</span>
                      <div class="pill-remove">×</div>`;

    pill.addEventListener("dragstart", (e) => {
      pill.classList.add("dragging");
      e.dataTransfer.setData("text/plain", col);
    });
    pill.addEventListener("dragend", () => pill.classList.remove("dragging"));

    // Tıklama ile hızlı atama
    pill.addEventListener("click", () => {
      if (pill.classList.contains("in-zone")) return;

      const xZone = document.getElementById("xZone");
      if (xZone && !xZone.querySelector(".col-pill")) {
        assignPillToZone(col, "xZone");
      } else {
        assignPillToZone(col, "yZone");
      }
    });

    pill.querySelector(".pill-remove")?.addEventListener("click", (e) => {
      e.stopPropagation();
      const parentZone = pill.parentElement;
      returnPillToPool(pill);
      updateAxisConfig();
      if (parentZone) restoreZonePlaceholder(parentZone);
    });

    pillsBox?.appendChild(pill);
  });

  parentContainer.appendChild(group);
}

function updatePoolCounts() {
  const total = globalColumns.length;
  const catCount = categoricalColumns.length;
  const numCount = numericColumns.length;
  const joinedCount = joinedColumns.length;

  const b = document.getElementById("poolCountBadge");
  if (b) b.textContent = `${total} Sütun`;
  const pAll = document.getElementById("pfcAllCount");
  if (pAll) pAll.textContent = total;
  const pCat = document.getElementById("pfcCatCount");
  if (pCat) pCat.textContent = catCount;
  const pNum = document.getElementById("pfcNumCount");
  if (pNum) pNum.textContent = numCount;

  const jBtn = document.getElementById("pfcJoinedBtn");
  if (jBtn) {
    if (joinedCount > 0) {
      jBtn.classList.remove("hidden");
      const jCnt = document.getElementById("pfcJoinedCount");
      if (jCnt) jCnt.textContent = joinedCount;
    } else {
      jBtn.classList.add("hidden");
    }
  }
}

function applyPoolFilterAndSearch() {
  document.querySelectorAll("#colPool .col-pill").forEach((pill) => {
    if (pill.classList.contains("in-zone")) return;

    const colName = pill.dataset.col.toLowerCase();
    const colType = pill.dataset.type;
    const origin = pill.dataset.origin;

    const matchesSearch =
      !currentPoolSearch || colName.includes(currentPoolSearch);

    let matchesFilter = true;
    if (currentPoolFilter === "cat") matchesFilter = colType === "cat";
    else if (currentPoolFilter === "num") matchesFilter = colType === "num";
    else if (currentPoolFilter === "joined")
      matchesFilter = origin === "joined";

    pill.style.display =
      matchesSearch && matchesFilter ? "inline-flex" : "none";
  });

  document.querySelectorAll("#colPool .pool-section-group").forEach((group) => {
    const allPills = group.querySelectorAll(".col-pill:not(.in-zone)");
    let hasVisible = false;
    allPills.forEach((p) => {
      if (p.style.display !== "none") hasVisible = true;
    });
    group.style.display = hasVisible ? "block" : "none";
  });
}

function returnPillToPool(pill) {
  if (!pill) return;
  pill.classList.remove("in-zone");
  const section = pill.dataset.section
    ? document.getElementById(pill.dataset.section)
    : null;
  if (section) section.appendChild(pill);
  else document.getElementById("colPool")?.appendChild(pill);
}

function restoreZonePlaceholder(zone) {
  if (zone.id === "xZone" && !zone.querySelector(".col-pill")) {
    zone.innerHTML =
      '<span class="zone-placeholder">Kategori sütununu buraya bırakın</span>';
  } else if (zone.id === "yZone" && !zone.querySelector(".col-pill")) {
    zone.innerHTML =
      '<span class="zone-placeholder">Değer sütunlarını buraya bırakın</span>';
  }
}

function assignPillToZone(colName, zoneId) {
  const pill = document.querySelector(`.col-pill[data-col="${colName}"]`);
  if (!pill) return;
  const zone = document.getElementById(zoneId);
  if (!zone) return;

  if (zoneId === "xZone") {
    const existing = zone.querySelector(".col-pill");
    if (existing) returnPillToPool(existing);
    zone.innerHTML = "";
  }

  if (zone.innerText.includes("Bırakın") || zone.innerText.includes("bırakın"))
    zone.innerHTML = "";
  zone.appendChild(pill);
  pill.classList.add("in-zone");
  updateAxisConfig();
}

function handleDropX(colName) {
  assignPillToZone(colName, "xZone");
}

function handleDropY(colName) {
  assignPillToZone(colName, "yZone");
}

function updateAxisConfig() {
  const xPill = document.getElementById("xZone")?.querySelector(".col-pill");
  axisConfig.x = xPill ? xPill.dataset.col : null;

  const yPills = document
    .getElementById("yZone")
    ?.querySelectorAll(".col-pill");
  axisConfig.y = yPills ? Array.from(yPills).map((p) => p.dataset.col) : [];

  window.axisConfig = axisConfig;
  evaluateCharts();
}

/* ── 2. CHART GRID & RECOMMENDATION ENGINE ── */
function renderChartGrid(filterCat = "all") {
  const grid = document.getElementById("s2ChartGrid");
  if (!grid) return;
  grid.innerHTML = "";

  const chartList =
    window.CHARTS || (typeof CHARTS !== "undefined" ? CHARTS : []);

  chartList.forEach((ch) => {
    if (filterCat !== "all" && ch.cat !== filterCat) return;
    const card = document.createElement("div");
    card.className = "chart-card disabled";
    card.tabIndex = 0;
    card.role = "button";
    card.dataset.id = ch.id;
    card.innerHTML = `
      <div class="cc-badge">✨ ÖNERİLEN</div>
      <div class="cc-front">
        <div class="cc-icon">${ch.icon}</div>
        <div class="cc-title">${ch.name}</div>
      </div>
      <div class="cc-hover">
        <h4>${ch.name}</h4>
        <p>${ch.desc}</p>
        <div class="cc-usecase">Tıklayarak Çiz</div>
      </div>
    `;
    card.addEventListener("click", () => {
      if (card.classList.contains("disabled")) return;
      if (typeof goToStep3 === "function") {
        goToStep3(ch.id, ch.name);
      } else if (typeof window.goToStep3 === "function") {
        window.goToStep3(ch.id, ch.name);
      }
    });
    card.addEventListener("keydown", (e) => {
      if (
        !card.classList.contains("disabled") &&
        (e.key === "Enter" || e.key === " ")
      ) {
        e.preventDefault();
        if (typeof goToStep3 === "function") {
          goToStep3(ch.id, ch.name);
        } else if (typeof window.goToStep3 === "function") {
          window.goToStep3(ch.id, ch.name);
        }
      }
    });
    grid.appendChild(card);
  });
  evaluateCharts();
}

function evaluateCharts() {
  const hasX = !!axisConfig.x;
  const yCount = axisConfig.y.length;
  const yAllNum = axisConfig.y.every((col) => numericColumns.includes(col));
  const warning = document.getElementById("axisWarning");
  if (warning) warning.classList.add("hidden");

  if (!hasX && yCount === 0) {
    document
      .querySelectorAll(".chart-card")
      .forEach((c) => (c.className = "chart-card disabled"));
    return;
  }

  let rec = [],
    dis = [];

  const isXDate = hasX && /tarih|date|zaman|ay|yıl|gün/i.test(axisConfig.x);
  const isXNum = hasX && numericColumns.includes(axisConfig.x);
  const hasFinance = globalColumns.some((c) =>
    /open|açılış|high|yüksek|low|düşük|close|kapanış|fiyat/i.test(c),
  );

  if (hasX) {
    if (yCount === 0) {
      if (isXNum) {
        rec = ["histogram", "box", "violin", "strip"];
        dis = [
          "scatter3d",
          "surface",
          "candlestick",
          "ohlc",
          "bubble",
          "line3d",
        ];
      } else {
        rec = ["bar", "horizontalbar", "pie", "donut", "treemap"];
        dis = [
          "scatter3d",
          "surface",
          "candlestick",
          "ohlc",
          "bubble",
          "line3d",
        ];
      }
    } else if (yCount === 1) {
      if (isXDate) {
        rec = ["line", "spline", "step", "area", "bar", "waterfall"];
        if (hasFinance) rec.push("candlestick", "ohlc");
        dis = ["pie", "donut", "sunburst", "radar", "scatter3d", "ternary"];
      } else if (isXNum) {
        rec = [
          "scatter",
          "bubble",
          "line",
          "bar",
          "histogram",
          "density2d",
          "histogram2d",
        ];
        dis = [
          "pie",
          "donut",
          "sunburst",
          "treemap",
          "funnel",
          "candlestick",
          "ohlc",
        ];
      } else {
        rec = [
          "bar",
          "horizontalbar",
          "pie",
          "donut",
          "radar",
          "treemap",
          "sunburst",
          "funnel",
          "dotplot",
          "waterfall",
          "bullet",
          "errorbar",
        ];
        dis = [
          "line3d",
          "surface",
          "candlestick",
          "ohlc",
          "scatter3d",
          "ternary",
        ];
      }
    } else if (yCount >= 2) {
      if (isXDate) {
        rec = [
          "line",
          "spline",
          "stackedarea",
          "groupedbar",
          "stackedbar",
          "candlestick",
          "ohlc",
        ];
        dis = ["pie", "donut", "funnelarea", "ternary"];
      } else if (isXNum) {
        if (1 + yCount === 3) {
          rec = [
            "scatter",
            "bubble",
            "scatter3d",
            "line3d",
            "surface",
            "contour",
            "ternary",
          ];
        } else {
          rec = ["scattermatrix", "parcoords", "heatmap", "surface", "contour"];
        }
        dis = ["pie", "donut", "sunburst", "funnel"];
      } else {
        rec = [
          "groupedbar",
          "stackedbar",
          "radar",
          "heatmap",
          "parcats",
          "sunburst",
          "icicle",
          "sankey",
        ];
        dis = ["line3d", "surface", "candlestick", "ohlc", "scatter3d"];
      }
    }
  } else {
    if (yCount === 1) {
      rec = ["histogram", "box", "violin", "strip", "rug", "bullet"];
      dis = [
        "pie",
        "donut",
        "sunburst",
        "treemap",
        "scatter3d",
        "surface",
        "candlestick",
        "ohlc",
      ];
    } else if (yCount >= 2) {
      rec = [
        "scatter",
        "bubble",
        "density2d",
        "histogram2d",
        "heatmap",
        "scattermatrix",
        "parcoords",
        "box",
        "violin",
      ];
      dis = ["pie", "donut", "funnelarea", "candlestick", "ohlc"];
    }
  }

  document.querySelectorAll(".chart-card").forEach((card) => {
    const id = card.dataset.id;
    card.className = "chart-card";
    card.tabIndex = 0;
    card.role = "button";
    if (dis.includes(id)) card.classList.add("disabled");
    else if (rec.includes(id)) card.classList.add("recommended");
  });

  if (!yAllNum && yCount > 0 && warning) {
    warning.textContent =
      "Uyarı: Y Ekseninde Metinsel (Kategorik) sütun seçtiniz. Sayısal grafikler otomatik adet sayımı ile gösterilebilir.";
    warning.classList.remove("hidden");
  }
}

/* ── 3. STEP 3 & ACTIVE CHART REFRESH ── */
async function refreshActiveChart() {
  const chartArea = document.getElementById("chartArea");
  if (!chartArea) return;

  chartArea
    .querySelectorAll(".spinner, .chart-loading-spinner")
    .forEach((s) => s.remove());

  const container = document.getElementById("chartAreaContainer");
  let loader = document.getElementById("megaChartLoader");
  if (!loader && container) {
    container.insertAdjacentHTML(
      "beforeend",
      '<div id="megaChartLoader" class="chart-loading-spinner" style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); z-index:15; width:92%; max-width:480px; pointer-events:none;"></div>',
    );
  }

  const targetType = currentPlotType;
  const chartLabel =
    document.getElementById("currentChartTypeName")?.textContent ||
    targetType.toUpperCase();
  const prog = window.DataVizProgress?.start({
    icon: "📊",
    title: `${chartLabel} Oluşturuluyor`,
    containerId: "megaChartLoader",
    showHud: false,
    stages: [
      {
        at: 0,
        short: "Veri Sorgusu",
        label: "Eksen verileri ve aktif filtreler sorgulanıyor...",
      },
      {
        at: 45,
        short: "Agregasyon",
        label: "İstatistiksel seri ve gruplama hesaplanıyor...",
      },
      {
        at: 80,
        short: "Çizim Motoru",
        label: "Plotly grafik katmanı ekrana çiziliyor...",
      },
    ],
  });

  const is3D = ["scatter3d", "line3d", "surface"].includes(targetType);
  const aggVal = document.getElementById("s2AggFunc")?.value || "sum";

  try {
    const res = await fetch("/get_chart_data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        x: axisConfig.x,
        x_col: axisConfig.x,
        y: axisConfig.y,
        y_cols: axisConfig.y,
        agg_func: aggVal,
        chart_type: targetType,
        is_3d: is3D,
        filters: activeFilters,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Veri çekilemedi");

    prog?.set(85, "Plotly grafik katmanı ekrana çiziliyor...");

    currentChartData = data;
    window.currentChartData = data;

    if (typeof drawMegaPlotly === "function") {
      await drawMegaPlotly("chartArea", data, targetType, false);
    } else if (typeof window.drawMegaPlotly === "function") {
      await window.drawMegaPlotly("chartArea", data, targetType, false);
    }

    prog?.complete("Grafik başarıyla oluşturuldu!");
    const l = document.getElementById("megaChartLoader");
    if (l) l.remove();
    chartArea
      .querySelectorAll(".spinner, .chart-loading-spinner")
      .forEach((s) => s.remove());

    fetchKpis();
    let statCols = axisConfig.y.filter((c) => numericColumns.includes(c));
    if (!statCols.length) statCols = numericColumns.slice(0, 6);
    fetchStats(statCols);
  } catch (err) {
    prog?.stop();
    const l = document.getElementById("megaChartLoader");
    if (l) l.remove();
    chartArea.innerHTML = `<div style="color:var(--red); padding:40px; text-align:center;">❌ Hata:<br>${err.message}</div>`;
  }
}

/* ── 4. AKILLI FİLTRELEME / SLICERS SİSTEMİ ── */
function openFilterModal() {
  const filterModal = document.getElementById("filterModal");
  const filterColumnSelect = document.getElementById("filterColumnSelect");
  if (!filterModal || !filterColumnSelect) return;

  filterColumnSelect.innerHTML =
    '<option value="">-- Bir Sütun Seçin --</option>';
  globalColumns.forEach((col) => {
    const isNum = numericColumns.includes(col);
    filterColumnSelect.innerHTML += `<option value="${col}">${isNum ? "#" : "T"} ${col}</option>`;
  });

  const dynContainer = document.getElementById("filterDynamicContainer");
  if (dynContainer) dynContainer.classList.add("hidden");
  filterModal.classList.remove("hidden");
}

function renderCatCheckboxes(col, values) {
  const catCheckboxesList = document.getElementById("catCheckboxesList");
  if (!catCheckboxesList) return;
  catCheckboxesList.innerHTML = "";

  values.forEach((val) => {
    const safeVal = String(val).replaceAll('"', "&quot;");
    const item = document.createElement("label");
    item.className = "cat-checkbox-item";
    item.innerHTML = `
      <input type="checkbox" value="${safeVal}" checked>
      <span>${val}</span>
    `;
    catCheckboxesList.appendChild(item);
  });
}

function syncFilteredViews() {
  if (currentChartData && currentPlotType) refreshActiveChart();
  const pivotScreen = document.getElementById("screen-pivot-studio");
  if (
    pivotScreen &&
    (pivotScreen.classList.contains("active") ||
      !pivotScreen.classList.contains("hidden")) &&
    typeof refreshPivotStudio === "function"
  ) {
    refreshPivotStudio();
  }
  const regPane = document.getElementById("tabRegression");
  if (
    regPane &&
    !regPane.classList.contains("hidden") &&
    typeof fetchAndRenderRegressionStudio === "function"
  ) {
    fetchAndRenderRegressionStudio();
  }
}

function renderActiveFilterChips() {
  const targets = [
    {
      bar: document.getElementById("s2FilterBar"),
      list: document.getElementById("s2ActiveFiltersList"),
      isGlobalBar: true,
    },
    {
      bar: document.getElementById("s3FilterBar"),
      list: document.getElementById("s3ActiveFiltersList"),
      isGlobalBar: true,
    },
    {
      bar: document.getElementById("pivotFilterBar"),
      list: document.getElementById("pivotActiveFiltersList"),
      isGlobalBar: true,
    },
  ];

  targets.forEach(({ bar, list, isGlobalBar }) => {
    if (!list && !bar) return;
    if (bar) {
      if (activeFilters.length > 0) {
        bar.classList.remove("hidden");
      } else if (!isGlobalBar) {
        bar.classList.add("hidden");
      }
    }
    if (!list) return;
    list.innerHTML = "";

    if (activeFilters.length === 0) {
      if (isGlobalBar) {
        list.innerHTML =
          '<span class="no-filter-hint">Filtre uygulanmadı (Tüm veri aktif)</span>';
      }
      return;
    }

    activeFilters.forEach((f, idx) => {
      const chip = document.createElement("div");
      chip.className = "filter-chip";

      const fType = f.filter_type || f.type;
      const vals = f.selected_values || f.values || [];
      let desc = "";
      if (fType === "categorical" || fType === "cat") {
        desc = `${f.column}: ${vals.length} değer`;
      } else if (fType === "numeric_range" || fType === "num") {
        desc = `${f.column}: ${f.min ?? "-"} - ${f.max ?? "-"}`;
      } else if (fType === "date_range") {
        desc = `${f.column}: ${f.start} / ${f.end}`;
      } else {
        desc = `${f.column}`;
      }

      chip.innerHTML = `
        <span>${desc}</span>
        <span class="remove-chip" data-idx="${idx}">×</span>
      `;
      list.appendChild(chip);
    });

    list.querySelectorAll(".remove-chip").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const idx = parseInt(e.target.dataset.idx);
        activeFilters.splice(idx, 1);
        window.activeFilters = activeFilters;
        renderActiveFilterChips();
        syncFilteredViews();
      });
    });
  });
}

/* ── 5. İSTATİSTİK, AKADEMİK YORUMLAYICI & EXPORT ── */
async function fetchStats(cols = null) {
  if (!cols || !cols.length) {
    cols = axisConfig.y.filter((c) => numericColumns.includes(c));
    if (!cols.length) cols = numericColumns.slice(0, 6);
  }
  if (!cols.length && !axisConfig.x) return;

  const statsContainer = document.getElementById("statsGrid");
  const isStatsTabVisible = !document
    .getElementById("tabStats")
    ?.classList.contains("hidden");
  let prog = null;
  if (statsContainer && isStatsTabVisible) {
    prog = window.DataVizProgress?.start({
      icon: "📐",
      title: "İstatistiksel Testler Hesaplanıyor",
      containerId: "statsGrid",
      showHud: false,
      stages: [
        {
          at: 0,
          short: "Betimsel Ölçüler",
          label: "Ortalama, medyan ve standart sapma hesaplanıyor...",
        },
        {
          at: 50,
          short: "Hipotez Testleri",
          label: "ANOVA / T-Testi ve korelasyon modelleri çalıştırılıyor...",
        },
        {
          at: 85,
          short: "Kart Oluşturma",
          label: "İstatistik kartları hazırlanıyor...",
        },
      ],
    });
  }

  try {
    const res = await fetch("/get_stats", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        columns: cols,
        y: cols,
        y_cols: cols,
        x: axisConfig.x,
        x_col: axisConfig.x,
        filters: activeFilters,
      }),
    });
    const data = await res.json();
    if (res.ok) {
      prog?.complete("İstatistikler hazır!");
      currentStats = data.stats;
      window.currentStats = data.stats;
      window.currentAdvancedStats = data.advanced;
      if (statsContainer) {
        statsContainer.innerHTML = renderStatsCards(data);
      }
    } else if (statsContainer) {
      prog?.stop();
      statsContainer.innerHTML = `<div style="grid-column: 1 / -1; color: var(--red); padding: 20px;">İstatistik alınamadı: ${data.error}</div>`;
    }
  } catch (e) {
    prog?.stop();
    if (statsContainer) {
      statsContainer.innerHTML = `<div style="grid-column: 1 / -1; color: var(--red); padding: 20px;">Hata: ${e.message}</div>`;
    }
  }
}

function renderStatsCards(data) {
  if (!data || !data.stats || Object.keys(data.stats).length === 0) {
    return '<div class="bento-loading" style="grid-column: 1 / -1; width: 100%; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 24px; text-align: center; color: var(--muted);">İstatistik bulunamadı veya hesaplanamadı.</div>';
  }

  let html = "";

  Object.keys(data.stats).forEach((col) => {
    const m = data.stats[col];
    const adv = data.advanced && data.advanced[col] ? data.advanced[col] : null;

    let advHtml = "";
    let headerTestBadge = "";

    if (adv) {
      const pValRaw = adv.p_value;
      const isSignificant =
        pValRaw !== null && pValRaw !== undefined && Number(pValRaw) < 0.05;
      const sigBadge =
        pValRaw !== null && pValRaw !== undefined
          ? isSignificant
            ? '<span style="font-size: 0.72rem; background: rgba(52, 211, 153, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); padding: 2px 8px; border-radius: 999px; font-weight: 600;">p &lt; 0.05 (Anlamlı Fark)</span>'
            : '<span style="font-size: 0.72rem; background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.25); padding: 2px 8px; border-radius: 999px; font-weight: 600;">p ≥ 0.05 (Anlamlı Fark Yok)</span>'
          : "";

      if (adv.type === "numeric") {
        const corrMethodName =
          adv.corr_method === "spearman"
            ? "Spearman (ρ)"
            : adv.corr_method === "kendall"
              ? "Kendall Tau (τ)"
              : "Pearson (r)";
        const regModelName =
          adv.reg_model === "poly2"
            ? "2. Derece Polinom"
            : adv.reg_model === "poly3"
              ? "3. Derece Polinom"
              : adv.reg_model === "log"
                ? "Logaritmik"
                : adv.reg_model === "exp"
                  ? "Üstel"
                  : "Doğrusal";

        headerTestBadge = `<span style="font-size: 0.75rem; background: rgba(167, 139, 250, 0.15); color: #c4b5fd; border: 1px solid rgba(167, 139, 250, 0.3); padding: 4px 10px; border-radius: 6px; font-weight: 600;">Korelasyon &amp; Regresyon (${regModelName})</span>`;

        advHtml = `
          <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.08);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 12px;">
              <div style="display: flex; align-items: center; gap: 10px;">
                <h4 style="font-size: 0.92rem; color: #a78bfa; margin: 0; font-weight: 700;">📈 Korelasyon &amp; Regresyon Analizi</h4>
                ${sigBadge}
              </div>
              <span style="font-size: 0.75rem; background: rgba(167, 139, 250, 0.15); color: #a78bfa; padding: 3px 8px; border-radius: 4px; font-weight: 600;">Model: ${regModelName}</span>
            </div>
            <div class="b-stat-body" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; align-items: stretch;">
              <div class="b-metric" style="background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;">
                <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">${corrMethodName}</span>
                <strong style="color: #60a5fa; font-size: 1.08rem; font-family: 'JetBrains Mono', monospace;">${adv.correlation !== null && adv.correlation !== undefined ? Number(adv.correlation).toFixed(4) : "-"}</strong>
              </div>
              <div class="b-metric" style="background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;">
                <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">Belirlilik (R²)</span>
                <strong style="color: #34d399; font-size: 1.08rem; font-family: 'JetBrains Mono', monospace;">${adv.r_squared !== null && adv.r_squared !== undefined ? Number(adv.r_squared).toFixed(4) : "-"}</strong>
              </div>
              <div class="b-metric" style="background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;">
                <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">P Değeri</span>
                <strong style="font-size: 1.08rem; font-family: 'JetBrains Mono', monospace;">${adv.p_value !== null && adv.p_value !== undefined ? (adv.p_value < 0.0001 ? "< 0.0001" : Number(adv.p_value).toFixed(4)) : "-"}</strong>
              </div>
              <div class="b-metric" style="background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;">
                <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">İlişki Gücü</span>
                <strong style="font-size: 0.92rem; color: #fbbf24;">${adv.interpretation || "-"}</strong>
              </div>
              <div class="b-metric" style="grid-column: span 2; background: rgba(167, 139, 250, 0.08); border: 1px solid rgba(167, 139, 250, 0.22); padding: 12px 14px; border-radius: 10px; display: flex; flex-direction: column; gap: 4px;">
                <span style="font-size: 0.75rem; color: #c4b5fd; text-transform: uppercase;">Model Denklemi</span>
                <strong style="color: #fbbf24; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; word-break: break-all;">${adv.regression || "-"}</strong>
              </div>
            </div>
          </div>
        `;
      } else if (adv.type === "categorical_2") {
        headerTestBadge = `<span style="font-size: 0.75rem; background: rgba(52, 211, 153, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); padding: 4px 10px; border-radius: 6px; font-weight: 600;">Bağımsız Örneklem T-Testi</span>`;
        const bestGroupHtml =
          adv.best_group !== undefined && adv.best_group !== null
            ? `<div class="b-metric" style="background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;">
                <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">En Yüksek Grup (Ort.)</span>
                <strong style="color: #34d399; font-size: 0.98rem;">${adv.best_group} ${adv.best_val !== undefined && adv.best_val !== null ? `(${Number(adv.best_val).toFixed(2)})` : ""}</strong>
              </div>`
            : "";
        const worstGroupHtml =
          adv.worst_group !== undefined && adv.worst_group !== null
            ? `<div class="b-metric" style="background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;">
                <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">En Düşük Grup (Ort.)</span>
                <strong style="color: #f87171; font-size: 0.98rem;">${adv.worst_group} ${adv.worst_val !== undefined && adv.worst_val !== null ? `(${Number(adv.worst_val).toFixed(2)})` : ""}</strong>
              </div>`
            : "";

        advHtml = `
          <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.08);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 12px;">
              <div style="display: flex; align-items: center; gap: 10px;">
                <h4 style="font-size: 0.92rem; color: #34d399; margin: 0; font-weight: 700;">⚖️ Bağımsız Örneklem T-Testi</h4>
                ${sigBadge}
              </div>
            </div>
            <div class="b-stat-body" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;">
              <div class="b-metric" style="background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;">
                <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">T İstatistiği</span>
                <strong style="color: #60a5fa; font-size: 1.08rem; font-family: 'JetBrains Mono', monospace;">${adv.t_test_stat !== null && adv.t_test_stat !== undefined ? Number(adv.t_test_stat).toFixed(3) : "-"}</strong>
              </div>
              <div class="b-metric" style="background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;">
                <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">P Değeri</span>
                <strong style="font-size: 1.08rem; font-family: 'JetBrains Mono', monospace;">${adv.p_value !== null && adv.p_value !== undefined ? Number(adv.p_value).toExponential(2) : "-"}</strong>
              </div>
              ${bestGroupHtml}
              ${worstGroupHtml}
            </div>
          </div>
        `;
      } else if (adv.type === "categorical_n") {
        headerTestBadge = `<span style="font-size: 0.75rem; background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); padding: 4px 10px; border-radius: 6px; font-weight: 600;">Tek Yönlü ANOVA</span>`;
        const bestGroupHtml =
          adv.best_group !== undefined && adv.best_group !== null
            ? `<div class="b-metric" style="background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;">
                <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">En Yüksek Grup (Ort.)</span>
                <strong style="color: #34d399; font-size: 0.98rem;">${adv.best_group} ${adv.best_val !== undefined && adv.best_val !== null ? `(${Number(adv.best_val).toFixed(2)})` : ""}</strong>
              </div>`
            : "";
        const worstGroupHtml =
          adv.worst_group !== undefined && adv.worst_group !== null
            ? `<div class="b-metric" style="background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;">
                <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">En Düşük Grup (Ort.)</span>
                <strong style="color: #f87171; font-size: 0.98rem;">${adv.worst_group} ${adv.worst_val !== undefined && adv.worst_val !== null ? `(${Number(adv.worst_val).toFixed(2)})` : ""}</strong>
              </div>`
            : "";

        advHtml = `
          <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.08);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 12px;">
              <div style="display: flex; align-items: center; gap: 10px;">
                <h4 style="font-size: 0.92rem; color: #fbbf24; margin: 0; font-weight: 700;">📊 Tek Yönlü ANOVA</h4>
                ${sigBadge}
              </div>
            </div>
            <div class="b-stat-body" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;">
              <div class="b-metric" style="background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;">
                <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">F İstatistiği</span>
                <strong style="color: #fbbf24; font-size: 1.08rem; font-family: 'JetBrains Mono', monospace;">${adv.anova_f !== null && adv.anova_f !== undefined ? Number(adv.anova_f).toFixed(3) : "-"}</strong>
              </div>
              <div class="b-metric" style="background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;">
                <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">P Değeri</span>
                <strong style="font-size: 1.08rem; font-family: 'JetBrains Mono', monospace;">${adv.p_value !== null && adv.p_value !== undefined ? Number(adv.p_value).toExponential(2) : "-"}</strong>
              </div>
              ${bestGroupHtml}
              ${worstGroupHtml}
            </div>
          </div>
        `;
      }
    }

    html += `
      <div class="stat-card" style="grid-column: 1 / -1; width: 100%; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 24px; display: flex; flex-direction: column;">
        <div class="b-stat-header" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 16px;">
          <div style="display: flex; align-items: center; gap: 10px;">
            <div class="b-stat-name" style="font-weight: 800; font-size: 1.15rem; color: var(--text);">${col}</div>
            <div class="b-stat-badge" style="font-size: 0.75rem; background: rgba(255,255,255,0.1); padding: 4px 10px; border-radius: 6px; font-weight: 600;">Sayısal</div>
            ${m.count !== undefined && m.count !== null ? `<div style="font-size: 0.75rem; background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.25); padding: 4px 10px; border-radius: 6px; font-weight: 600;">Gözlem (N): ${m.count}</div>` : ""}
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            ${headerTestBadge}
          </div>
        </div>

        <div class="b-stat-body" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px;">
          <div class="b-metric primary" style="background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;">
            <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">Ortalama</span>
            <strong style="color: #60a5fa; font-size: 1.15rem; font-family: 'JetBrains Mono', monospace;">${m.mean !== null && m.mean !== undefined ? Number(m.mean).toFixed(2) : "-"}</strong>
          </div>
          <div class="b-metric" style="background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;">
            <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">Medyan</span>
            <strong style="font-size: 1.15rem; font-family: 'JetBrains Mono', monospace;">${m.median !== null && m.median !== undefined ? Number(m.median).toFixed(2) : "-"}</strong>
          </div>
          <div class="b-metric danger" style="background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;">
            <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">Min</span>
            <strong style="color: #f87171; font-size: 1.15rem; font-family: 'JetBrains Mono', monospace;">${m.min !== null && m.min !== undefined ? Number(m.min).toFixed(2) : "-"}</strong>
          </div>
          <div class="b-metric success" style="background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;">
            <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">Max</span>
            <strong style="color: #34d399; font-size: 1.15rem; font-family: 'JetBrains Mono', monospace;">${m.max !== null && m.max !== undefined ? Number(m.max).toFixed(2) : "-"}</strong>
          </div>
          <div class="b-metric" style="background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;">
            <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">Std. Sapma</span>
            <strong style="font-size: 1.15rem; font-family: 'JetBrains Mono', monospace;">${m.std !== null && m.std !== undefined ? Number(m.std).toFixed(2) : "-"}</strong>
          </div>
          <div class="b-metric" style="background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;">
            <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">Eksik Veri</span>
            <strong style="font-size: 1.15rem; font-family: 'JetBrains Mono', monospace; color: ${m.missing > 0 ? "#fbbf24" : "var(--text)"};">${m.missing !== null && m.missing !== undefined ? m.missing : "-"}</strong>
          </div>
        </div>

        ${advHtml}
      </div>
    `;
  });
  return html;
}

async function exportActiveDataset(format, triggerBtnId = null) {
  const btnId =
    triggerBtnId ||
    (format === "csv"
      ? "downloadCsvBtn"
      : format === "parquet"
        ? "downloadParquetBtn"
        : "downloadExcelBtn");
  const btn = document.getElementById(btnId);
  const orig = btn ? btn.innerHTML : "";
  if (btn) {
    btn.innerHTML = "⏳ İndiriliyor...";
    btn.disabled = true;
  }

  try {
    const res = await fetch("/export_data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        format: format,
        filters: activeFilters,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Dışa aktarma başarısız");
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `DataViz_Aktif_Veri_${Date.now()}.${format === "excel" ? "xlsx" : format}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  } catch (err) {
    alert("Dışa aktarma hatası: " + err.message);
  } finally {
    if (btn) {
      btn.innerHTML = orig;
      btn.disabled = false;
    }
  }
}

/* ── 8. EVENT LISTENERS INITIALIZATION ── */
function initChartManagerListeners() {
  // Pool search & filter
  document.getElementById("poolSearchInput")?.addEventListener("input", (e) => {
    currentPoolSearch = e.target.value.toLowerCase().trim();
    applyPoolFilterAndSearch();
  });

  document.querySelectorAll(".pfc-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document
        .querySelectorAll(".pfc-btn")
        .forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentPoolFilter = btn.dataset.pfilter;
      applyPoolFilterAndSearch();
    });
  });

  // Drag & drop zones for axis
  document.querySelectorAll(".dd-zone").forEach((zone) => {
    zone.addEventListener("dragover", (e) => {
      e.preventDefault();
      zone.classList.add("dragover");
    });
    zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
    zone.addEventListener("drop", (e) => {
      e.preventDefault();
      zone.classList.remove("dragover");
      const colName = e.dataTransfer.getData("text/plain");
      if (!colName) return;
      if (zone.id === "xZone") handleDropX(colName);
      else if (zone.id === "yZone") handleDropY(colName);
      else assignPillToZone(colName, zone.id);
    });
  });

  // Chart filters click
  const chartFilters = document.getElementById("chartFilters");
  chartFilters?.addEventListener("click", (e) => {
    if (e.target.tagName !== "BUTTON") return;
    chartFilters
      .querySelectorAll("button")
      .forEach((b) => b.classList.remove("active"));
    e.target.classList.add("active");
    renderChartGrid(e.target.dataset.filter);
  });

  // Magic templates
  document.querySelectorAll(".magic-btn[data-tpl]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const tpl = e.currentTarget.dataset.tpl;
      initDragDropPool();

      let xMatch = null;
      let yMatch = null;

      if (tpl === "sales") {
        xMatch =
          globalColumns.find((c) => /tarih|date|zaman|ay|yıl|gün/i.test(c)) ||
          categoricalColumns[0];
        yMatch =
          globalColumns.find((c) =>
            /satış|tutar|fiyat|gelir|price|sales/i.test(c),
          ) || numericColumns[0];
      } else if (tpl === "hr") {
        xMatch =
          globalColumns.find((c) =>
            /departman|bölüm|pozisyon|unvan|dept/i.test(c),
          ) || categoricalColumns[0];
        yMatch =
          globalColumns.find((c) => /maaş|ücret|çalışan|salary|pay/i.test(c)) ||
          numericColumns[0];
      } else if (tpl === "finance") {
        xMatch =
          globalColumns.find((c) => /tarih|date|zaman/i.test(c)) ||
          categoricalColumns[0];
        yMatch =
          globalColumns.find((c) =>
            /kapanış|açılış|fiyat|close|open/i.test(c),
          ) || numericColumns[0];
      }

      if (xMatch) assignPillToZone(xMatch, "xZone");
      if (yMatch) assignPillToZone(yMatch, "yZone");

      if (xMatch && yMatch) {
        setTimeout(() => {
          if (
            tpl === "finance" &&
            document.querySelector('.chart-card[data-id="candlestick"]')
          ) {
            if (typeof goToStep3 === "function") goToStep3("line", "Çizgi");
          } else {
            if (typeof goToStep3 === "function") goToStep3("bar", "Çubuk");
          }
        }, 600);
      }
    });
  });

  // Formula wizard (Calculated Columns)
  const calcColModal = document.getElementById("calcColModal");
  const calcCol1Select = document.getElementById("calcCol1Select");
  const calcCol2Select = document.getElementById("calcCol2Select");
  const calcScalarInput = document.getElementById("calcScalarInput");
  const calcUseScalar = document.getElementById("calcUseScalar");
  const calcNewColName = document.getElementById("calcNewColName");
  let selectedCalcOp = "+";

  ["btnOpenCalcModal", "btnOpenCalcModalS2"].forEach((id) => {
    document.getElementById(id)?.addEventListener("click", () => {
      if (calcCol1Select) calcCol1Select.innerHTML = "";
      if (calcCol2Select) calcCol2Select.innerHTML = "";
      numericColumns.forEach((c) => {
        if (calcCol1Select)
          calcCol1Select.innerHTML += `<option value="${c}">${c}</option>`;
        if (calcCol2Select)
          calcCol2Select.innerHTML += `<option value="${c}">${c}</option>`;
      });
      if (calcNewColName) calcNewColName.value = "";
      calcColModal?.classList.remove("hidden");
    });
  });

  calcUseScalar?.addEventListener("change", (e) => {
    const isScalar = e.target.checked;
    const col2Box = document.getElementById("calcCol2Box");
    const scalarBox = document.getElementById("calcScalarBox");
    if (col2Box) {
      col2Box.classList.toggle("hidden", isScalar);
      col2Box.style.display = isScalar ? "none" : "block";
    }
    if (scalarBox) {
      scalarBox.classList.toggle("hidden", !isScalar);
      scalarBox.style.display = isScalar ? "block" : "none";
    }
  });

  document.querySelectorAll(".calc-op-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document
        .querySelectorAll(".calc-op-btn")
        .forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      selectedCalcOp = btn.dataset.op;
    });
  });

  document
    .getElementById("btnCancelCalcCol")
    ?.addEventListener("click", () => calcColModal?.classList.add("hidden"));
  document
    .getElementById("btnCloseCalcColModal")
    ?.addEventListener("click", () => calcColModal?.classList.add("hidden"));

  document
    .getElementById("btnApplyCalcCol")
    ?.addEventListener("click", async () => {
      const col1 = calcCol1Select?.value;
      const isScalar = calcUseScalar?.checked ?? false;
      const col2 = isScalar ? null : calcCol2Select?.value;
      const scalarVal = isScalar ? parseFloat(calcScalarInput?.value) : null;
      let newCol = calcNewColName?.value?.trim();

      if (!col1) {
        alert("Lütfen 1. sütunu seçin.");
        return;
      }
      if (isScalar && (isNaN(scalarVal) || scalarVal === null)) {
        alert("Lütfen geçerli bir sabit sayı girin.");
        return;
      }
      if (!newCol) {
        newCol = isScalar
          ? `${col1}_${selectedCalcOp}_${scalarVal}`
          : `${col1}_${selectedCalcOp}_${col2}`;
      }

      try {
        const res = await fetch("/add_calculated_column", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            col1: col1,
            op: selectedCalcOp,
            col2: col2,
            scalar: scalarVal,
            new_col_name: newCol,
          }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);

        numericColumns = data.numeric_columns || [];
        categoricalColumns = data.categorical_columns || [];
        globalColumns = [...categoricalColumns, ...numericColumns];
        if (!calculatedColumns.includes(newCol)) calculatedColumns.push(newCol);

        window.numericColumns = numericColumns;
        window.categoricalColumns = categoricalColumns;
        window.globalColumns = globalColumns;
        window.calculatedColumns = calculatedColumns;

        calcColModal?.classList.add("hidden");
        initDragDropPool(true);
        if (typeof renderPivotPoolStructured === "function") {
          renderPivotPoolStructured();
        }
      } catch (err) {
        alert("Hesaplama başarısız: " + err.message);
      }
    });

  // Filter Modal Controls
  [
    "btnOpenFilterModal",
    "btnOpenFilterModalS2",
    "btnOpenFilterModalS3",
    "btnOpenFilterModalPivot",
  ].forEach((id) => {
    document.getElementById(id)?.addEventListener("click", openFilterModal);
  });
  ["btnCloseFilterModal", "btnCancelFilter"].forEach((id) => {
    document.getElementById(id)?.addEventListener("click", () => {
      document.getElementById("filterModal")?.classList.add("hidden");
    });
  });

  document.getElementById("catSearchInput")?.addEventListener("input", (e) => {
    const q = e.target.value.toLowerCase().trim();
    document
      .querySelectorAll(
        "#catCheckboxesList .cat-checkbox-item, #catCheckboxesList label",
      )
      .forEach((item) => {
        const text = item.textContent.toLowerCase();
        item.style.display = !q || text.includes(q) ? "" : "none";
      });
  });

  document.getElementById("btnSelectAllCat")?.addEventListener("click", () => {
    document
      .querySelectorAll("#catCheckboxesList .cat-checkbox-item")
      .forEach((item) => {
        if (item.style.display !== "none") {
          const cb = item.querySelector("input[type='checkbox']");
          if (cb) cb.checked = true;
        }
      });
  });

  document.getElementById("btnClearAllCat")?.addEventListener("click", () => {
    document
      .querySelectorAll("#catCheckboxesList .cat-checkbox-item")
      .forEach((item) => {
        if (item.style.display !== "none") {
          const cb = item.querySelector("input[type='checkbox']");
          if (cb) cb.checked = false;
        }
      });
  });

  const filterColumnSelect = document.getElementById("filterColumnSelect");
  filterColumnSelect?.addEventListener("change", async (e) => {
    const col = e.target.value;
    const dynContainer = document.getElementById("filterDynamicContainer");
    const catArea = document.getElementById("catFilterArea");
    const numArea = document.getElementById("numFilterArea");
    const catSearch = document.getElementById("catSearchInput");
    if (catSearch) catSearch.value = "";
    if (!col) {
      dynContainer?.classList.add("hidden");
      return;
    }

    dynContainer?.classList.remove("hidden");
    const isNum = numericColumns.includes(col);

    if (isNum) {
      if (catArea) catArea.classList.add("hidden");
      if (numArea) numArea.classList.remove("hidden");
      try {
        const res = await fetch(
          `/get_column_unique_values?column=${encodeURIComponent(col)}`,
        );
        const data = await res.json();
        if (data.min != null && data.max != null) {
          const minIn = document.getElementById("numFilterMin");
          const maxIn = document.getElementById("numFilterMax");
          if (minIn) {
            minIn.value = data.min;
            minIn.placeholder = `Min: ${data.min}`;
          }
          if (maxIn) {
            maxIn.value = data.max;
            maxIn.placeholder = `Max: ${data.max}`;
          }
        }
      } catch (err) {
        console.error(err);
      }
    } else {
      if (numArea) numArea.classList.add("hidden");
      if (catArea) catArea.classList.remove("hidden");
      try {
        const res = await fetch(
          `/get_column_unique_values?column=${encodeURIComponent(col)}`,
        );
        const data = await res.json();
        renderCatCheckboxes(col, data.values || []);
      } catch (err) {
        console.error(err);
      }
    }
  });

  document.getElementById("btnApplyFilter")?.addEventListener("click", () => {
    const col = filterColumnSelect?.value;
    if (!col) return;
    const isNum = numericColumns.includes(col);

    if (isNum) {
      const minRaw = parseFloat(document.getElementById("numFilterMin")?.value);
      const maxRaw = parseFloat(document.getElementById("numFilterMax")?.value);
      const minVal = isNaN(minRaw) ? null : minRaw;
      const maxVal = isNaN(maxRaw) ? null : maxRaw;
      if (minVal !== null || maxVal !== null) {
        activeFilters = activeFilters.filter((f) => f.column !== col);
        activeFilters.push({
          column: col,
          type: "num",
          filter_type: "numeric_range",
          min: minVal,
          max: maxVal,
        });
      }
    } else {
      const checkedBoxes = document.querySelectorAll(
        '#catCheckboxesList input[type="checkbox"]:checked',
      );
      const selectedVals = Array.from(checkedBoxes).map((cb) => cb.value);
      activeFilters = activeFilters.filter((f) => f.column !== col);
      if (selectedVals.length > 0) {
        activeFilters.push({
          column: col,
          type: "cat",
          filter_type: "categorical",
          values: selectedVals,
          selected_values: selectedVals,
        });
      }
    }

    window.activeFilters = activeFilters;
    document.getElementById("filterModal")?.classList.add("hidden");
    renderActiveFilterChips();
    syncFilteredViews();
  });

  ["btnResetFilters", "btnResetFilter"].forEach((id) => {
    document.getElementById(id)?.addEventListener("click", () => {
      activeFilters = [];
      window.activeFilters = activeFilters;
      document.getElementById("filterModal")?.classList.add("hidden");
      renderActiveFilterChips();
      syncFilteredViews();
    });
  });

  // Aggregation Function Change
  document.getElementById("s2AggFunc")?.addEventListener("change", () => {
    if (currentChartData && currentPlotType) refreshActiveChart();
  });

  // Trace Size Slider Display
  document.getElementById("traceSize")?.addEventListener("input", (e) => {
    const valEl = document.getElementById("traceSizeVal");
    if (valEl) valEl.textContent = e.target.value + "px";
  });

  // Pin To Dashboard
  document
    .getElementById("btnPinToDashboard")
    ?.addEventListener("click", () => {
      if (!currentChartData || !currentPlotType) return;
      const xName = axisConfig.x || "Endeks";
      const yName = axisConfig.y.join(", ") || "Değerler";
      const title = `${currentPlotType.toUpperCase()} — ${xName} vs ${yName}`;

      addChartToDashboard({
        id: "dash_" + Date.now(),
        title: title,
        chartType: currentPlotType,
        chartData: JSON.parse(JSON.stringify(currentChartData)),
      });

      const btn = document.getElementById("btnPinToDashboard");
      if (btn) {
        btn.innerHTML = "<span>✓</span> Panoya Eklendi!";
        setTimeout(() => {
          btn.innerHTML = "<span>📌</span> Panoya Ekle";
        }, 2000);
      }
    });

  document
    .getElementById("btnClearDashboard")
    ?.addEventListener("click", () => {
      if (
        confirm("Panodaki tüm grafikleri temizlemek istediğinize emin misiniz?")
      ) {
        dashboardCharts = [];
        window.dashboardCharts = dashboardCharts;
        updateDashboardBadge();
        renderDashboardGrid();
      }
    });

  document.getElementById("applyCustomsBtn")?.addEventListener("click", () => {
    if (currentChartData && currentPlotType) {
      if (typeof drawMegaPlotly === "function") {
        drawMegaPlotly("chartArea", currentChartData, currentPlotType, false);
      } else if (typeof window.drawMegaPlotly === "function") {
        window.drawMegaPlotly(
          "chartArea",
          currentChartData,
          currentPlotType,
          false,
        );
      }
    }
  });

  // Export buttons
  document
    .getElementById("downloadCsvBtn")
    ?.addEventListener("click", () => exportActiveDataset("csv"));
  document
    .getElementById("downloadExcelBtn")
    ?.addEventListener("click", () => exportActiveDataset("excel"));
  document
    .getElementById("downloadParquetBtn")
    ?.addEventListener("click", () => exportActiveDataset("parquet"));
  document
    .getElementById("btnQuickExportParquet")
    ?.addEventListener("click", () =>
      exportActiveDataset("parquet", "btnQuickExportParquet"),
    );

  // Step 3 resize observer
  const chartAreaContainerEl = document.getElementById("chartAreaContainer");
  if (chartAreaContainerEl && window.ResizeObserver) {
    const ro = new ResizeObserver(() => {
      const step3 = document.getElementById("step3-dashboard");
      if (step3 && step3.classList.contains("active")) {
        try {
          Plotly.Plots.resize("chartArea");
        } catch (e) {}
      }
    });
    ro.observe(chartAreaContainerEl);
  }

  // Refresh stats button
  document.getElementById("refreshStatsBtn")?.addEventListener("click", () => {
    let statCols = axisConfig.y.filter((c) => numericColumns.includes(c));
    if (!statCols.length) statCols = numericColumns.slice(0, 6);
    fetchStats(statCols);
  });

  // Statistical & Academic Interpretation Generator
  document
    .getElementById("btnGenerateInsight")
    ?.addEventListener("click", async () => {
      const btn = document.getElementById("btnGenerateInsight");
      const container = document.getElementById("aiResponseContainer");
      const content = document.getElementById("aiResponseContent");
      if (!btn || !container || !content) return;

      btn.disabled = true;
      btn.innerHTML = "🔄 Analiz Ediliyor...";
      container.classList.add("hidden");

      try {
        const res = await fetch("/generate_insight", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            stats: currentStats,
            advanced_stats: window.currentAdvancedStats || {},
            chart_type:
              document.getElementById("currentChartTypeName")?.textContent ||
              "Grafik",
            x_col: axisConfig.x,
            y_cols: axisConfig.y,
          }),
        });
        const data = await res.json();
        if (!res.ok)
          throw new Error(data.error || "İstatistiksel yorum alınamadı");

        const rawText = data.insight || "";
        const lines = rawText
          .split("\n")
          .map((l) => l.trim())
          .filter((l) => l.length > 0 && l !== "---" && !l.startsWith("#"));

        let html =
          '<div style="display: flex; flex-direction: column; gap: 10px;">';
        lines.forEach((line) => {
          const formattedLine = line
            .replace(/^- /, "")
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\*(.*?)\*/g, "<em>$1</em>")
            .replace(
              /`(.*?)`/g,
              "<code style=\"background: rgba(255,255,255,0.08); padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;\">$1</code>",
            );
          html += `
            <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-left: 3px solid var(--pink); border-radius: 8px; padding: 10px 14px; font-size: 0.9rem; line-height: 1.55; color: #f1f5f9;">
              ${formattedLine}
            </div>
          `;
        });
        html += "</div>";

        currentAiInsight = html;
        window.currentAiInsight = html;
        content.innerHTML = html;
        container.classList.remove("hidden");
      } catch (err) {
        content.innerHTML = `<div style="color:var(--red);">${err.message}</div>`;
        container.classList.remove("hidden");
      } finally {
        btn.disabled = false;
        btn.innerHTML = "Veriyi Yorumla";
      }
    });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initChartManagerListeners);
} else {
  initChartManagerListeners();
}

// Window export
window.initDragDropPool = initDragDropPool;
window.renderPoolSection = renderPoolSection;
window.updatePoolCounts = updatePoolCounts;
window.applyPoolFilterAndSearch = applyPoolFilterAndSearch;
window.returnPillToPool = returnPillToPool;
window.restoreZonePlaceholder = restoreZonePlaceholder;
window.assignPillToZone = assignPillToZone;
window.handleDropX = handleDropX;
window.handleDropY = handleDropY;
window.updateAxisConfig = updateAxisConfig;
window.renderChartGrid = renderChartGrid;
window.evaluateCharts = evaluateCharts;
window.refreshActiveChart = refreshActiveChart;
window.syncFilteredViews = syncFilteredViews;
window.openFilterModal = openFilterModal;
window.renderCatCheckboxes = renderCatCheckboxes;
window.renderActiveFilterChips = renderActiveFilterChips;
window.fetchStats = fetchStats;
window.renderStatsCards = renderStatsCards;
window.exportActiveDataset = exportActiveDataset;
