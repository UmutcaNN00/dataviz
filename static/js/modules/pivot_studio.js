/* ════════════════════════════════════════════════════════════
   DATAVIZ PRO V6 — PIVOT MATRIX STUDIO MODULE
   Bağımsız Pivot Matris Stüdyosu Motoru
════════════════════════════════════════════════════════════ */

var pivotConfig = {
  rows: [],
  cols: [],
  values: [],
  agg_func: "sum",
};
var currentPivotData = null;
var currentPivotPoolSearch = "";
var currentPivotPoolFilter = "all";

function initPivotStudio() {
  const pivotPool = document.getElementById("pivotColPool");
  if (!pivotPool) return;

  // Otomatik akıllı ilk varsayılanlar (Asla boş ve uyarı ile açılmasın)
  if (pivotConfig.rows.length === 0) {
    const defRow =
      categoricalColumns.find((c) => /bolge|sehir|kategori|segment/i.test(c)) ||
      categoricalColumns[0] ||
      globalColumns[0];
    if (defRow) pivotConfig.rows = [defRow];
  }
  if (pivotConfig.cols.length === 0 && categoricalColumns.length > 1) {
    const defCol =
      categoricalColumns.find(
        (c) =>
          !pivotConfig.rows.includes(c) &&
          /odeme|kategori|tip|tur|yil/i.test(c),
      ) || categoricalColumns.find((c) => !pivotConfig.rows.includes(c));
    if (defCol) pivotConfig.cols = [defCol];
  }
  if (pivotConfig.values.length === 0) {
    const defVal =
      numericColumns.find((c) => /tutar|ciro|kar|satis|fiyat/i.test(c)) ||
      numericColumns[0];
    if (defVal) pivotConfig.values = [defVal];
  }

  renderPivotPoolStructured();
  renderPivotDropZones();
  refreshPivotStudio();
}

function renderPivotPoolStructured() {
  const pool = document.getElementById("pivotColPool");
  if (!pool) return;
  pool.innerHTML = "";

  const countBadge = document.getElementById("pivotPoolCountBadge");
  if (countBadge) countBadge.textContent = `${globalColumns.length} Sütun`;

  // Filtre sayaçları
  const catCount = categoricalColumns.length;
  const numCount = numericColumns.length;
  const joinedCount = joinedColumns.length;

  const elAll = document.getElementById("pfcPivotAllCount");
  const elCat = document.getElementById("pfcPivotCatCount");
  const elNum = document.getElementById("pfcPivotNumCount");
  const elJoined = document.getElementById("pfcPivotJoinedCount");
  const elJoinedBtn = document.getElementById("pfcPivotJoinedBtn");

  if (elAll) elAll.textContent = globalColumns.length;
  if (elCat) elCat.textContent = catCount;
  if (elNum) elNum.textContent = numCount;
  if (elJoinedBtn) {
    if (joinedCount > 0) {
      elJoinedBtn.classList.remove("hidden");
      if (elJoined) elJoined.textContent = joinedCount;
    } else {
      elJoinedBtn.classList.add("hidden");
    }
  }

  const file1Cols = globalColumns.filter(
    (c) => !joinedColumns.includes(c) && !calculatedColumns.includes(c),
  );
  const joinedCols = globalColumns.filter((c) => joinedColumns.includes(c));
  const calcCols = globalColumns.filter((c) => calculatedColumns.includes(c));

  renderPivotPoolSection(
    pool,
    "📁 1. Dosya Sütunları",
    file1Cols,
    "section_pivot_file1",
  );
  if (joinedCols.length > 0) {
    renderPivotPoolSection(
      pool,
      "🔗 2. Dosya Sütunları (Birleştirilen)",
      joinedCols,
      "section_pivot_joined",
    );
  }
  if (calcCols.length > 0) {
    renderPivotPoolSection(
      pool,
      "🧮 Hesaplanmış Formül Sütunları",
      calcCols,
      "section_pivot_calc",
    );
  }

  applyPivotPoolFilterAndSearch();
}

function renderPivotPoolSection(parentContainer, titleText, cols, sectionId) {
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
  parentContainer.appendChild(group);

  const pillsBox = group.querySelector(`#pills_${sectionId}`);

  cols.forEach((col) => {
    const isNum = numericColumns.includes(col);
    const isJoined = joinedColumns.includes(col);
    const isCalc = calculatedColumns.includes(col);
    const isUsed =
      pivotConfig.rows.includes(col) ||
      pivotConfig.cols.includes(col) ||
      pivotConfig.values.includes(col);

    const pill = document.createElement("div");
    pill.className = `col-pill ${isJoined ? "joined-pill" : ""} ${isCalc ? "calc-pill" : ""} ${isUsed ? "in-zone" : ""}`;
    pill.draggable = true;
    pill.dataset.col = col;
    pill.dataset.type = isNum ? "num" : "cat";
    pill.dataset.origin = isJoined ? "joined" : isCalc ? "calc" : "main";

    const tagHtml = isNum
      ? `<span class="col-pill-tag num" title="Sayısal Sütun">#</span>`
      : `<span class="col-pill-tag cat" title="Kategorik / Metin Sütun">T</span>`;

    const joinBadge = isJoined
      ? `<span class="join-tag-badge">🔗 Dosya 2</span>`
      : "";
    const calcBadge = isCalc
      ? `<span class="join-tag-badge" style="background:rgba(245,158,11,0.2); color:#fbbf24; border-color:rgba(245,158,11,0.4);">🧮 fx</span>`
      : "";

    pill.innerHTML = `${tagHtml} <span class="col-pill-name">${col}</span> ${joinBadge} ${calcBadge}`;

    // Drag start
    pill.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", col);
      e.dataTransfer.effectAllowed = "copyMove";
    });

    // Click to add / assign
    pill.addEventListener("click", () => {
      if (pivotConfig.rows.includes(col)) {
        pivotConfig.rows = pivotConfig.rows.filter((x) => x !== col);
        pivotConfig.cols.push(col);
      } else if (pivotConfig.cols.includes(col)) {
        pivotConfig.cols = pivotConfig.cols.filter((x) => x !== col);
      } else if (pivotConfig.values.includes(col)) {
        if (pivotConfig.values.length > 1)
          pivotConfig.values = pivotConfig.values.filter((x) => x !== col);
      } else {
        if (isNum) pivotConfig.values.push(col);
        else if (pivotConfig.rows.length === 0) pivotConfig.rows.push(col);
        else if (pivotConfig.cols.length === 0) pivotConfig.cols.push(col);
        else pivotConfig.rows.push(col);
      }
      renderPivotPoolStructured();
      renderPivotDropZones();
      refreshPivotStudio();
    });

    pillsBox.appendChild(pill);
  });
}

function applyPivotPoolFilterAndSearch() {
  document.querySelectorAll("#pivotColPool .col-pill").forEach((pill) => {
    const colName = pill.dataset.col.toLowerCase();
    const colType = pill.dataset.type;
    const origin = pill.dataset.origin;

    const matchesSearch =
      !currentPivotPoolSearch || colName.includes(currentPivotPoolSearch);

    let matchesFilter = true;
    if (currentPivotPoolFilter === "cat") matchesFilter = colType === "cat";
    else if (currentPivotPoolFilter === "num")
      matchesFilter = colType === "num";
    else if (currentPivotPoolFilter === "joined")
      matchesFilter = origin === "joined";

    pill.style.display =
      matchesSearch && matchesFilter ? "inline-flex" : "none";
  });

  document
    .querySelectorAll("#pivotColPool .pool-section-group")
    .forEach((group) => {
      const allPills = group.querySelectorAll(".col-pill");
      let hasVisible = false;
      allPills.forEach((p) => {
        if (p.style.display !== "none") hasVisible = true;
      });
      group.style.display = hasVisible ? "block" : "none";
    });
}

function renderPivotDropZones() {
  const rowZone = document.getElementById("pivotRowZone");
  const colZone = document.getElementById("pivotColZone");
  const valZone = document.getElementById("pivotValZone");
  if (!rowZone || !colZone || !valZone) return;

  rowZone.innerHTML = "";
  colZone.innerHTML = "";
  valZone.innerHTML = "";

  if (pivotConfig.rows.length === 0)
    rowZone.innerHTML =
      '<span style="opacity:0.6; font-size:0.85rem;">Sütunları Buraya Bırakın veya Havuzdan Tıklayın</span>';
  if (pivotConfig.cols.length === 0)
    colZone.innerHTML =
      '<span style="opacity:0.6; font-size:0.85rem;">Sütunları Buraya Bırakın (Opsiyonel)</span>';
  if (pivotConfig.values.length === 0)
    valZone.innerHTML =
      '<span style="opacity:0.6; font-size:0.85rem;">Sayısal Sütunları Buraya Bırakın</span>';

  // Rows
  pivotConfig.rows.forEach((col) => {
    const pill = createPivotZonePill(col, "cat", () => {
      pivotConfig.rows = pivotConfig.rows.filter((x) => x !== col);
      renderPivotPoolStructured();
      renderPivotDropZones();
      refreshPivotStudio();
    });
    rowZone.appendChild(pill);
  });

  // Columns
  pivotConfig.cols.forEach((col) => {
    const pill = createPivotZonePill(col, "cat", () => {
      pivotConfig.cols = pivotConfig.cols.filter((x) => x !== col);
      renderPivotPoolStructured();
      renderPivotDropZones();
      refreshPivotStudio();
    });
    colZone.appendChild(pill);
  });

  // Values
  pivotConfig.values.forEach((col) => {
    const pill = createPivotZonePill(col, "num", () => {
      if (pivotConfig.values.length > 1) {
        pivotConfig.values = pivotConfig.values.filter((x) => x !== col);
        renderPivotPoolStructured();
        renderPivotDropZones();
        refreshPivotStudio();
      }
    });
    valZone.appendChild(pill);
  });
}

function createPivotZonePill(col, type, onRemove) {
  const isNum = type === "num" || numericColumns.includes(col);
  const pill = document.createElement("div");
  pill.className = "col-pill";
  pill.dataset.col = col;
  pill.dataset.type = isNum ? "num" : "cat";

  const tagHtml = isNum
    ? `<span class="col-pill-tag num">#</span>`
    : `<span class="col-pill-tag cat">T</span>`;
  pill.innerHTML = `${tagHtml} <span>${col}</span> <span class="col-pill-remove" title="Kaldır">×</span>`;

  pill.querySelector(".col-pill-remove")?.addEventListener("click", (e) => {
    e.stopPropagation();
    onRemove();
  });
  pill.addEventListener("click", onRemove);
  return pill;
}

async function refreshPivotStudio() {
  const container = document.getElementById("pmsTableContainer");
  const badge = document.getElementById("pmsStatsBadge");
  if (!container) return;

  if (pivotConfig.rows.length === 0 && pivotConfig.cols.length === 0) {
    container.innerHTML =
      '<div class="pivot-loading-msg">⚠️ Lütfen en az 1 Satır veya Sütun seçin.</div>';
    if (badge) badge.textContent = "0 Boyut";
    return;
  }
  if (pivotConfig.values.length === 0) {
    container.innerHTML =
      '<div class="pivot-loading-msg">⚠️ Lütfen en az 1 Sayısal Değer seçin.</div>';
    if (badge) badge.textContent = "0 Metrik";
    return;
  }

  const prog = window.DataVizProgress?.start({
    icon: "🧮",
    title: "Pivot Matrisi Hesaplanıyor",
    containerId: "pmsTableContainer",
    showHud: false,
    stages: [
      {
        at: 0,
        short: "Gruplama",
        label: "Satır ve sütun kırılımları gruplanıyor...",
      },
      {
        at: 50,
        short: "Agregasyon",
        label: "Hücre değerleri ve genel toplamlar hesaplanıyor...",
      },
      {
        at: 85,
        short: "Isı Haritası",
        label: "Koşullu biçimlendirme uygulanıyor...",
      },
    ],
  });
  pivotConfig.agg_func =
    document.getElementById("pivotAggSelect")?.value || "sum";

  try {
    const res = await fetch("/get_pivot_data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        rows: pivotConfig.rows,
        cols: pivotConfig.cols,
        values: pivotConfig.values,
        agg_func: pivotConfig.agg_func,
        filters: activeFilters,
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Pivot verisi alınamadı");

    prog?.complete("Pivot tablosu hazır!");
    currentPivotData = data;
    renderPivotMatrixStage(data);

    if (badge) {
      badge.textContent = `${data.rows.length} Satır x ${data.column_headers.length} Sütun (${data.total_data_rows.toLocaleString("tr-TR")} Kayıt)`;
    }
  } catch (err) {
    prog?.stop();
    container.innerHTML = `<div class="pivot-loading-msg" style="color:var(--red);">❌ ${err.message}</div>`;
    if (badge) badge.textContent = "Hata";
  }
}

function renderPivotMatrixStage(data) {
  const container = document.getElementById("pmsTableContainer");
  if (!container) return;

  const useHeatmap =
    document.getElementById("pmsHeatmapToggle")?.checked ?? true;
  const minVal = data.min_value;
  const maxVal = data.max_value;
  const valRange = maxVal - minVal || 1;

  let html = `<table class="pivot-matrix-table" id="pmsLiveTable">`;

  // 1. Header
  html += `<thead><tr>`;
  data.index_names.forEach((name) => {
    html += `<th class="pmt-corner">${name}</th>`;
  });
  data.column_headers.forEach((h) => {
    const isGrand = h.includes("Genel Toplam");
    html += `<th class="${isGrand ? "pmt-grand-total-th" : "pmt-col-header"}">${h}</th>`;
  });
  html += `</tr></thead>`;

  // 2. Body
  html += `<tbody>`;
  data.rows.forEach((r) => {
    const isRowGrand = r.is_grand_total;
    html += `<tr class="${isRowGrand ? "pmt-grand-total-row" : ""}">`;

    // Row labels
    r.row_labels.forEach((lbl) => {
      html += `<td class="pmt-row-header">${lbl}</td>`;
    });

    // Cell values
    r.cells.forEach((val, cIdx) => {
      const isColGrand = (data.column_headers[cIdx] || "").includes(
        "Genel Toplam",
      );
      let bgStyle = "";

      if (useHeatmap && !isRowGrand && !isColGrand && val > 0) {
        const ratio = Math.min(1, Math.max(0, (val - minVal) / valRange));
        const alpha = 0.08 + ratio * 0.45;
        bgStyle = `background: rgba(52, 211, 153, ${alpha.toFixed(3)});`;
      }

      let formattedVal = val.toLocaleString("tr-TR", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
      });
      if (val >= 1000)
        formattedVal = val.toLocaleString("tr-TR", {
          maximumFractionDigits: 0,
        });

      const cellClass = `pmt-val-cell ${isColGrand ? "pmt-grand-total-cell" : ""} ${useHeatmap ? "has-heatmap" : ""}`;
      html += `<td class="${cellClass}" style="${bgStyle}">${formattedVal}</td>`;
    });

    html += `</tr>`;
  });
  html += `</tbody></table>`;

  container.innerHTML = html;
}

async function exportPivotExcel() {
  const btn = document.getElementById("btnPmsExportExcel");
  const orig = btn ? btn.innerHTML : "";
  if (btn) {
    btn.innerHTML = "⏳ İndiriliyor...";
    btn.disabled = true;
  }

  try {
    const res = await fetch("/export_pivot_excel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        rows: pivotConfig.rows,
        cols: pivotConfig.cols,
        values: pivotConfig.values,
        agg_func: pivotConfig.agg_func,
        filters: activeFilters,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Excel indirilemedi");
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `DataViz_Ozet_Pivot_${Date.now()}.xlsx`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  } catch (err) {
    alert("Excel indirme hatası: " + err.message);
  } finally {
    if (btn) {
      btn.innerHTML = orig;
      btn.disabled = false;
    }
  }
}

function initPivotStudioListeners() {
  // Setup Drag & Drop for Pivot Zones
  ["pivotRowZone", "pivotColZone", "pivotValZone"].forEach((zoneId) => {
    const zone = document.getElementById(zoneId);
    if (!zone) return;

    zone.addEventListener("dragover", (e) => {
      e.preventDefault();
      zone.classList.add("dragover");
    });
    zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
    zone.addEventListener("drop", (e) => {
      e.preventDefault();
      zone.classList.remove("dragover");
      const colName = e.dataTransfer.getData("text/plain");
      if (!colName || !globalColumns.includes(colName)) return;

      const pZone = zone.dataset.pivotZone;
      // Remove from everywhere first to prevent desync
      pivotConfig.rows = pivotConfig.rows.filter((x) => x !== colName);
      pivotConfig.cols = pivotConfig.cols.filter((x) => x !== colName);
      pivotConfig.values = pivotConfig.values.filter((x) => x !== colName);

      if (pZone === "row") {
        pivotConfig.rows.push(colName);
      } else if (pZone === "col") {
        pivotConfig.cols.push(colName);
      } else if (pZone === "val") {
        pivotConfig.values.push(colName);
      }

      renderPivotPoolStructured();
      renderPivotDropZones();
      refreshPivotStudio();
    });
  });

  // Pivot Pool Search & Filter Buttons
  document
    .getElementById("pivotPoolSearchInput")
    ?.addEventListener("input", (e) => {
      currentPivotPoolSearch = e.target.value.toLowerCase().trim();
      applyPivotPoolFilterAndSearch();
    });

  document.querySelectorAll("[data-pivotfilter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document
        .querySelectorAll("[data-pivotfilter]")
        .forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentPivotPoolFilter = btn.dataset.pivotfilter;
      applyPivotPoolFilterAndSearch();
    });
  });

  // Modals in Pivot Studio
  document
    .getElementById("btnOpenCalcModalPivot")
    ?.addEventListener("click", () => {
      document.getElementById("btnOpenCalcModal")?.click();
    });
  document
    .getElementById("btnOpenMergeModalPivot")
    ?.addEventListener("click", () => {
      document.getElementById("btnOpenMergeModal")?.click();
    });

  // Aggregation Function Select
  document.getElementById("pivotAggSelect")?.addEventListener("change", (e) => {
    pivotConfig.agg_func = e.target.value;
    refreshPivotStudio();
  });

  // Heatmap Değişimi
  document
    .getElementById("pmsHeatmapToggle")
    ?.addEventListener("change", () => {
      if (currentPivotData) renderPivotMatrixStage(currentPivotData);
    });

  // Excel Olarak İndir (.xlsx)
  document
    .getElementById("btnPmsExportExcel")
    ?.addEventListener("click", exportPivotExcel);

  // Tabloyu Kopyala (TSV Formatında Panoya)
  document.getElementById("btnPmsCopyTable")?.addEventListener("click", () => {
    const table = document.getElementById("pmsLiveTable");
    if (!table) return;

    let tsv = [];
    table.querySelectorAll("tr").forEach((row) => {
      let rowData = [];
      row.querySelectorAll("th, td").forEach((cell) => {
        rowData.push(cell.innerText.trim().replace(/\n/g, " "));
      });
      tsv.push(rowData.join("\t"));
    });

    const tsvText = tsv.join("\n");
    navigator.clipboard
      .writeText(tsvText)
      .then(() => {
        const btn = document.getElementById("btnPmsCopyTable");
        if (btn) {
          const orig = btn.innerHTML;
          btn.innerHTML = "✓ Kopyalandı!";
          setTimeout(() => (btn.innerHTML = orig), 2000);
        }
      })
      .catch((err) => {
        alert("Kopyalama başarısız: " + err.message);
      });
  });

  // Panoya Ekle (Dashboard Widget)
  document
    .getElementById("btnPmsPinDashboard")
    ?.addEventListener("click", () => {
      if (!currentPivotData) return;

      const rowName = pivotConfig.rows.join(" & ") || "Tümü";
      const colName = pivotConfig.cols.join(" & ");
      const valName = pivotConfig.values.join(", ");
      const title = `${rowName} ${colName ? "x " + colName : ""} Özet Pivot (${valName})`;

      const dashItem = {
        id: "dash_pivot_" + Date.now(),
        title: title,
        chartType: "pivot",
        pivotData: JSON.parse(JSON.stringify(currentPivotData)),
        filtersCount: activeFilters.length,
      };

      dashboardCharts.push(dashItem);
      if (typeof updateDashboardBadge === "function") updateDashboardBadge();
      if (typeof renderDashboardGrid === "function") renderDashboardGrid();

      const btn = document.getElementById("btnPmsPinDashboard");
      if (btn) {
        btn.innerHTML = "<span>✓</span> Panoya Eklendi!";
        setTimeout(() => {
          btn.innerHTML = "<span>📌</span> Panoya Ekle";
        }, 2000);
      }
    });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initPivotStudioListeners);
} else {
  initPivotStudioListeners();
}

// Window export
window.pivotConfig = pivotConfig;
window.initPivotStudio = initPivotStudio;
window.renderPivotPoolStructured = renderPivotPoolStructured;
window.refreshPivotStudio = refreshPivotStudio;
window.renderPivotMatrixStage = renderPivotMatrixStage;
window.exportPivotExcel = exportPivotExcel;
