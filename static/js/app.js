/* ════════════════════════════════════════════════════════════
   DATAVIZ PRO V6 — APPLICATION COORDINATOR (app.js)
   Screen Transitions, Upload Handlers, Navigation & Shortcuts
════════════════════════════════════════════════════════════ */

var isUploading = false;
var lastScreenBeforeTrust = 2;

// ── SCREEN TRANSITIONS COORDINATOR ──
function showScreen(num) {
  const ids = [
    "step1-upload",
    "step2-config",
    "step3-dashboard",
    "screen-pivot-studio",
    "screen-trust-studio",
  ];
  const screens = ids.map((id) => document.getElementById(id));
  screens.forEach(
    (s) => s && (s.classList.add("hidden"), s.classList.remove("active")),
  );

  let activeIdx = 0;
  if (num === "pivot" || num === 4) {
    activeIdx = 3;
  } else if (num === "trust" || num === 5) {
    activeIdx = 4;
  } else {
    activeIdx = num - 1;
    lastScreenBeforeTrust = num;
  }

  const target = screens[activeIdx];
  if (target) {
    target.classList.remove("hidden");
    target.classList.add("active");
  }

  if ((num === 4 || num === "pivot") && typeof initPivotStudio === "function") {
    initPivotStudio();
  }
}

function proceedToStep2() {
  if (typeof initDragDropPool === "function") initDragDropPool();
  if (typeof renderChartGrid === "function") renderChartGrid("all");
  showScreen(2);
}

async function goToStep3(chartId, chartName) {
  currentPlotType = window.currentPlotType = chartId;
  const titleEl = document.getElementById("currentChartTypeName");
  if (titleEl && chartName) titleEl.textContent = chartName;
  showScreen(3);
  if (typeof refreshActiveChart === "function") await refreshActiveChart();
}

// ── DATASET INGESTION & HEALTH HELPERS ──
function setUploadZoneVisibility(visible) {
  const dz = document.getElementById("mainDropZone");
  const actions = document.querySelector("#step1-upload .upload-actions");
  if (dz) dz.style.display = visible ? "" : "none";
  if (actions) actions.style.display = visible ? "" : "none";
}

function setUploadStatus(html, isError = false) {
  const el = document.getElementById("mainUploadStatus");
  if (!el) return;
  if (!html) {
    el.classList.add("hidden");
    el.style.display = "none";
    el.innerHTML = "";
    return;
  }
  el.className = `status-msg ${isError ? "error" : "loading"}`;
  el.style.padding = "";
  el.style.background = "";
  el.style.border = "";
  el.innerHTML = html;
  el.style.display = "block";
}

function applyUploadedDataset(data) {
  if (data.file_name) {
    activeFileName = window.activeFileName = data.file_name;
  }
  numericColumns = window.numericColumns = data.numeric_columns || [];
  categoricalColumns = window.categoricalColumns =
    data.categorical_columns || [];
  globalColumns = window.globalColumns = [
    ...categoricalColumns,
    ...numericColumns,
  ];
  calculatedColumns = window.calculatedColumns = [];
  joinedColumns = window.joinedColumns = [];
  activeFilters = window.activeFilters = [];
  dashboardCharts = window.dashboardCharts = [];
  sheetNames = window.sheetNames = data.sheet_names || [];
  if (window.pivotConfig) {
    window.pivotConfig.rows = [];
    window.pivotConfig.cols = [];
    window.pivotConfig.values = [];
  }

  if (typeof updateDashboardBadge === "function") updateDashboardBadge();
  if (typeof renderActiveFilterChips === "function") renderActiveFilterChips();
  renderSheetTabs(sheetNames, data.active_sheet);

  const s2 = document.getElementById("s2FileName");
  if (s2) s2.textContent = activeFileName;
  const pv = document.getElementById("pivotFileName");
  if (pv) pv.textContent = activeFileName;
  const tr = document.getElementById("trustFileName");
  if (tr) tr.textContent = activeFileName;

  setUploadStatus(null);
  setUploadZoneVisibility(true);
  proceedToStep2();
  checkDataHealthAsync();
}

async function checkDataHealthAsync() {
  try {
    const res = await fetch("/check_health", { cache: "no-store" });
    const health = await res.json();
    if (typeof updateAnomalyBadges === "function") updateAnomalyBadges(health);
    const modal = document.getElementById("dataPrepModal");
    const isModalOpen = modal && !modal.classList.contains("hidden");
    if (
      health?.has_issues &&
      typeof openDataPrepModal === "function" &&
      !window.isDataPrepBusy &&
      !isModalOpen
    ) {
      openDataPrepModal(null, health);
    }
  } catch (err) {
    console.warn("Veri kontrol uyarısı:", err);
  }
}

// ── UPLOAD & SAMPLE DATASET LOADERS ──
async function handleLoadSampleData() {
  if (isUploading) return;
  isUploading = true;
  activeFileName = window.activeFileName = "Akademik_Ornek_Veri_Seti.xlsx";
  setUploadZoneVisibility(false);

  const prog = window.DataVizProgress?.start({
    icon: "📂",
    title: "Örnek Veri Seti Yükleniyor",
    containerId: "mainUploadStatus",
    showHud: false,
    stages: [
      {
        at: 0,
        short: "Dosya Okuma",
        label: "Hazır örnek veri seti belleğe aktarılıyor...",
      },
      {
        at: 45,
        short: "Ayrıştırma",
        label: "Satır ve sütun tipleri ayrıştırılıyor...",
      },
      {
        at: 80,
        short: "Sağlık Kontrolü",
        label: "Veri kalitesi ve eksen havuzu hazırlanıyor...",
      },
    ],
  });

  try {
    const res = await fetch("/load_sample", { method: "POST" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Örnek veri yüklenemedi");
    prog?.complete("Örnek veri seti başarıyla yüklendi!");
    setTimeout(() => applyUploadedDataset(data), 240);
  } catch (err) {
    prog?.stop();
    setUploadZoneVisibility(true);
    alert("Örnek veri yüklenemedi: " + err.message);
    setUploadStatus(null);
  } finally {
    isUploading = false;
  }
}

async function handleFileUpload(file) {
  if (!file || isUploading) return;
  isUploading = true;
  activeFileName = window.activeFileName = file.name;
  setUploadZoneVisibility(false);

  const prog = window.DataVizProgress?.start({
    icon: "🚀",
    title: `${file.name} Yükleniyor`,
    containerId: "mainUploadStatus",
    showHud: false,
    autoAdvance: false,
    initialPct: 6,
    stages: [
      {
        at: 0,
        short: "Sunucuya Aktarım",
        label: "Dosya sunucuya gönderiliyor...",
      },
      {
        at: 45,
        short: "Tablo Ayrıştırma",
        label: "Veri motoru tabloyu ayrıştırıyor...",
      },
      {
        at: 78,
        short: "Tip & Anomali Analizi",
        label: "Sütun tipleri ve veri sağlığı taranıyor...",
      },
    ],
  });

  const fd = new FormData();
  fd.append("file", file);

  let parseTimer = null;
  const startParsePhase = () => {
    if (parseTimer) return;
    let cur = 48;
    prog?.set(cur, "Veri motoru tabloyu ayrıştırıyor...");
    parseTimer = setInterval(() => {
      if (cur < 88) {
        cur += Math.max(0.45, (90 - cur) * 0.06);
        prog?.set(
          cur,
          cur < 78
            ? "Veri motoru tabloyu ayrıştırıyor..."
            : "Sütun tipleri ve veri sağlığı taranıyor...",
        );
      } else {
        prog?.set(cur, "Sütun tipleri ve veri sağlığı taranıyor...");
      }
    }, 220);
  };

  try {
    const data = await new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", "/upload", true);

      xhr.upload.onprogress = (evt) => {
        if (evt.lengthComputable && evt.total > 0) {
          const uploadRatio = evt.loaded / evt.total;
          const mappedPct = Math.min(
            45,
            Math.max(6, Math.round(uploadRatio * 45)),
          );
          prog?.set(
            mappedPct,
            `Dosya sunucuya aktarılıyor (%${Math.round(uploadRatio * 100)})...`,
          );
          if (uploadRatio >= 0.98) {
            startParsePhase();
          }
        }
      };

      xhr.upload.onload = () => {
        startParsePhase();
      };

      xhr.onload = () => {
        if (parseTimer) clearInterval(parseTimer);
        let parsed = {};
        try {
          parsed = JSON.parse(xhr.responseText || "{}");
        } catch (e) {
          return reject(new Error("Sunucu yanıtı okunamadı."));
        }
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(parsed);
        } else {
          reject(new Error(parsed.error || "Dosya yüklenemedi"));
        }
      };

      xhr.onerror = () => {
        if (parseTimer) clearInterval(parseTimer);
        reject(new Error("Ağ bağlantısı sırasında hata oluştu."));
      };

      xhr.send(fd);
    });

    prog?.complete("Veri seti hazır! Analiz ekranına geçiliyor...");
    setTimeout(() => applyUploadedDataset(data), 240);
  } catch (err) {
    if (parseTimer) clearInterval(parseTimer);
    prog?.stop();
    setUploadZoneVisibility(true);
    const errMsg = err.message || "Dosya okunamadı veya biçim desteklenmiyor.";
    setUploadStatus(
      `⚠️ <strong>Dosya Yükleme Hatası:</strong> ${errMsg}`,
      true,
    );
    alert(`⚠️ Dosya Yüklenemedi:\n\n${errMsg}`);
  } finally {
    isUploading = false;
    const fin = document.getElementById("mainFileInput");
    if (fin) fin.value = "";
  }
}

function renderSheetTabs(sheets, activeSheet) {
  const bar = document.getElementById("sheetTabsBar"),
    list = document.getElementById("sheetTabsList");
  const pBar = document.getElementById("pivotSheetTabsBar"),
    pList = document.getElementById("pivotSheetTabsList");
  if (!sheets || sheets.length <= 1) {
    bar?.classList.add("hidden");
    pBar?.classList.add("hidden");
    return;
  }
  [bar, pBar].forEach((b) => b?.classList.remove("hidden"));
  [list, pList].forEach((l) => {
    if (l) l.innerHTML = "";
  });

  sheets.forEach((s) => {
    [list, pList].forEach((c) => {
      if (!c) return;
      const btn = document.createElement("button");
      btn.className = `sheet-tab-btn ${s === activeSheet ? "active" : ""}`;
      btn.textContent = s;
      btn.onclick = () => switchSheet(s);
      c.appendChild(btn);
    });
  });
}

async function switchSheet(sheetName) {
  const prog = window.DataVizProgress?.start({
    icon: "📑",
    title: `"${sheetName}" Sayfasına Geçiliyor`,
    showHud: true,
    stages: [
      {
        at: 0,
        short: "Sayfa Okuma",
        label: "Excel çalışma sayfası okunuyor...",
      },
      {
        at: 50,
        short: "Sütun Analizi",
        label: "Sütun tipleri güncelleniyor...",
      },
      { at: 85, short: "Arayüz", label: "Veri havuzu yenileniyor..." },
    ],
  });
  try {
    const res = await fetch("/switch_sheet", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sheet_name: sheetName }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    numericColumns = window.numericColumns = data.numeric_columns || [];
    categoricalColumns = window.categoricalColumns =
      data.categorical_columns || [];
    globalColumns = window.globalColumns = [
      ...categoricalColumns,
      ...numericColumns,
    ];
    calculatedColumns = window.calculatedColumns = [];
    joinedColumns = window.joinedColumns = [];
    activeFilters = window.activeFilters = [];
    currentChartData = window.currentChartData = null;
    currentStats = window.currentStats = {};
    if (window.pivotConfig) {
      window.pivotConfig.rows = [];
      window.pivotConfig.cols = [];
      window.pivotConfig.values = [];
    }

    const s2 = document.getElementById("s2FileName");
    if (s2 && activeFileName)
      s2.textContent = `${activeFileName} (${sheetName})`;
    const pv = document.getElementById("pivotFileName");
    if (pv && activeFileName)
      pv.textContent = `${activeFileName} (${sheetName})`;
    const tr = document.getElementById("trustFileName");
    if (tr && activeFileName)
      tr.textContent = `${activeFileName} (${sheetName})`;

    if (typeof renderActiveFilterChips === "function")
      renderActiveFilterChips();
    renderSheetTabs(sheetNames, sheetName);
    if (typeof initDragDropPool === "function") initDragDropPool();
    if (typeof renderChartGrid === "function") renderChartGrid("all");
    if (typeof window.populateRegColumnSelects === "function")
      window.populateRegColumnSelects();
    const pivotScreen = document.getElementById("screen-pivot-studio");
    if (
      pivotScreen &&
      !pivotScreen.classList.contains("hidden") &&
      typeof initPivotStudio === "function"
    ) {
      initPivotStudio();
    }
    const trustScreen = document.getElementById("screen-trust-studio");
    if (
      trustScreen &&
      !trustScreen.classList.contains("hidden") &&
      typeof fetchAndRenderTrustReport === "function"
    ) {
      fetchAndRenderTrustReport().catch(() => {});
    }
    prog?.complete(`"${sheetName}" sayfası yüklendi!`);
    if (typeof checkDataHealthAsync === "function") checkDataHealthAsync();
  } catch (err) {
    prog?.stop();
    alert("Sayfa değiştirme hatası: " + err.message);
  }
}

// ── DOM BOOTSTRAP & NAVIGATION LISTENERS ──
document.addEventListener("DOMContentLoaded", () => {
  // Modal kapatıcılar (Escape & Backdrop)
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape")
      document
        .querySelectorAll(".modal-overlay:not(.hidden)")
        .forEach((m) => m.classList.add("hidden"));
  });
  document.querySelectorAll(".modal-overlay").forEach((modal) => {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.add("hidden");
    });
  });

  window.addEventListener("dragover", (e) => e.preventDefault(), false);
  window.addEventListener("drop", (e) => e.preventDefault(), false);

  const dropZone = document.getElementById("mainDropZone"),
    fileInput = document.getElementById("mainFileInput");
  ["dragenter", "dragover"].forEach((n) =>
    dropZone?.addEventListener(n, (e) => {
      e.preventDefault();
      dropZone.classList.add("dragover");
    }),
  );
  ["dragleave", "dragend"].forEach((n) =>
    dropZone?.addEventListener(n, (e) => {
      e.preventDefault();
      dropZone.classList.remove("dragover");
    }),
  );
  dropZone?.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer?.files?.length)
      handleFileUpload(e.dataTransfer.files[0]);
  });
  dropZone?.addEventListener("click", (e) => {
    if (!e.target.closest("#btnLoadSampleData")) fileInput?.click();
  });
  document.getElementById("btnBrowseFile")?.addEventListener("click", (e) => {
    e.preventDefault();
    fileInput?.click();
  });
  document
    .getElementById("btnLoadSampleData")
    ?.addEventListener("click", (e) => {
      e.preventDefault();
      handleLoadSampleData();
    });
  fileInput?.addEventListener("change", (e) => {
    if (e.target.files?.length) handleFileUpload(e.target.files[0]);
  });

  // Navigasyon butonları
  document
    .getElementById("btnCancelStep2")
    ?.addEventListener("click", () => showScreen(1));
  document
    .getElementById("btnBackToStep2")
    ?.addEventListener("click", () => showScreen(2));
  const resetToUpload = () => {
    if (fileInput) fileInput.value = "";
    setUploadStatus(null);
    showScreen(1);
  };
  document
    .getElementById("btnNewFile")
    ?.addEventListener("click", resetToUpload);
  document
    .getElementById("btnPivotNewFile")
    ?.addEventListener("click", resetToUpload);

  document
    .getElementById("btnModeChartsS2")
    ?.addEventListener("click", () => showScreen(2));
  document
    .getElementById("btnModeChartsS3")
    ?.addEventListener("click", () => showScreen(3));
  document
    .getElementById("btnPivotBackToCharts")
    ?.addEventListener("click", () => {
      if (axisConfig.x || axisConfig.y.length) showScreen(3);
      else showScreen(2);
    });

  ["btnOpenPivotStudioS2", "btnOpenPivotStudioS3", "btnPivotStudioTop"].forEach(
    (id) => {
      document
        .getElementById(id)
        ?.addEventListener("click", () => showScreen(4));
    },
  );

  ["topbarHelp", "btnShortcutsHelp"].forEach((id) => {
    document.getElementById(id)?.addEventListener("click", () => {
      alert(
        "⌨️ Kısayollar:\n\nG → Grafik sekmesi\nS → İstatistik sekmesi\nR → Regresyon sekmesi\nD → Dashboard sekmesi\nP → Panoya ekle\n? → Bu yardım\nEsc → Açık pencereleri kapat",
      );
    });
  });

  // Step 3 Tab Bar
  document.querySelectorAll("#mainTabsBar .tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document
        .querySelectorAll("#mainTabsBar .tab-btn")
        .forEach((b) => b.classList.remove("active"));
      document
        .querySelectorAll(".tab-pane")
        .forEach((p) => p.classList.add("hidden"));
      btn.classList.add("active");
      const tabName = btn.dataset.tab;
      if (tabName === "chart") {
        document.getElementById("tabChart")?.classList.remove("hidden");
        try {
          Plotly.Plots.resize("chartArea");
        } catch (e) {}
      } else if (tabName === "stats") {
        document.getElementById("tabStats")?.classList.remove("hidden");
        if (typeof fetchStats === "function") fetchStats();
      } else if (tabName === "regression") {
        document.getElementById("tabRegression")?.classList.remove("hidden");
        if (typeof window.initRegressionStudio === "function") {
          window.initRegressionStudio();
          window.fetchAndRenderRegressionStudio().catch(() => {});
        }
        try {
          Plotly.Plots.resize("regScatterPlotArea");
          Plotly.Plots.resize("regHeatmapPlotArea");
        } catch (e) {}
      } else if (tabName === "dashboard") {
        document.getElementById("tabDashboard")?.classList.remove("hidden");
        if (typeof renderDashboardGrid === "function") renderDashboardGrid();
        if (typeof fetchKpis === "function") fetchKpis();
      }
    });
  });

  // Inspector Tabs Logic (Stil & Eksen)
  document.querySelectorAll(".inspector-tabs .i-tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      document
        .querySelectorAll(".inspector-tabs .i-tab")
        .forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".inspector-body .i-pane").forEach((p) => {
        p.classList.add("hidden");
        p.classList.remove("active");
        p.style.display = "none";
      });
      btn.classList.add("active");
      const tabName = btn.dataset.itab;
      const targetPane = document.getElementById("itab-" + tabName);
      if (targetPane) {
        targetPane.classList.remove("hidden");
        targetPane.classList.add("active");
        targetPane.style.display = "flex";
      }
    });
  });

  // Klavye kısayolları
  document.addEventListener("keydown", (e) => {
    if (["INPUT", "TEXTAREA", "SELECT"].includes(e.target.tagName)) return;
    const key = e.key.toLowerCase();
    if (key === "g")
      document
        .querySelector('#mainTabsBar .tab-btn[data-tab="chart"]')
        ?.click();
    else if (key === "s")
      document
        .querySelector('#mainTabsBar .tab-btn[data-tab="stats"]')
        ?.click();
    else if (key === "r")
      document
        .querySelector('#mainTabsBar .tab-btn[data-tab="regression"]')
        ?.click();
    else if (key === "d")
      document
        .querySelector('#mainTabsBar .tab-btn[data-tab="dashboard"]')
        ?.click();
    else if (key === "p") document.getElementById("btnPinToDashboard")?.click();
    else if (key === "?") document.getElementById("topbarHelp")?.click();
  });
});

// Window export
Object.assign(window, {
  showScreen,
  proceedToStep2,
  goToStep3,
  handleFileUpload,
  handleLoadSampleData,
  loadSampleDataset: handleLoadSampleData,
  renderSheetTabs,
  switchSheet,
});

function escapeHtmlSafe(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

window.showToast = function (message, type = "info", title = "") {
  const container =
    document.getElementById("toastContainer") || createToastContainer();
  const toast = document.createElement("div");
  toast.className = "toast toast-" + type;
  let icon = "ℹ️";
  if (type === "success") icon = "✅";
  if (type === "error") icon = "❌";
  if (type === "warning") icon = "⚠️";
  if (!title) {
    if (type === "success") title = "Başarılı";
    if (type === "error") title = "Hata";
    if (type === "warning") title = "Uyarı";
    if (type === "info") title = "Bilgi";
  }
  const safeTitle = escapeHtmlSafe(title);
  const safeMsg = escapeHtmlSafe(message).replace(/\n/g, "<br>");
  toast.innerHTML = `<div class="toast-icon">${icon}</div><div class="toast-content"><div class="toast-title">${safeTitle}</div><div class="toast-message">${safeMsg}</div></div><button class="toast-close">&times;</button>`;
  container.appendChild(toast);
  const closeBtn = toast.querySelector(".toast-close");
  const removeToast = () => {
    toast.classList.add("fade-out");
    setTimeout(() => toast.remove(), 300);
  };
  closeBtn.addEventListener("click", removeToast);
  setTimeout(removeToast, 5000);
};

function createToastContainer() {
  const container = document.createElement("div");
  container.id = "toastContainer";
  container.className = "toast-container";
  document.body.appendChild(container);
  return container;
}

window.alert = function (msg) {
  if (!msg) return;
  const msgStr = msg.toString().toLowerCase();
  if (
    msgStr.includes("hata") ||
    msgStr.includes("başarısız") ||
    msgStr.includes("bulunamadı") ||
    msgStr.includes("geçersiz")
  ) {
    showToast(msg, "error");
  } else if (
    msgStr.includes("uyarı") ||
    msgStr.includes("⚠️") ||
    msgStr.includes("yok") ||
    msgStr.includes("boş") ||
    msgStr.includes("önce")
  ) {
    showToast(msg, "warning");
  } else if (
    msgStr.includes("✓") ||
    msgStr.includes("🎉") ||
    msgStr.includes("📌") ||
    msgStr.includes("başarıyla")
  ) {
    showToast(msg.toString().replace("✓ ", ""), "success");
  } else {
    showToast(msg, "info");
  }
};

// ==========================================
// RESIZER LOGIC
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
  const resizer = document.getElementById("s2-resizer");
  const leftPane = document.getElementById("s2-left-pane");

  if (resizer && leftPane) {
    let isResizing = false;

    resizer.addEventListener("mousedown", (e) => {
      isResizing = true;
      document.body.style.cursor = "col-resize";
      e.preventDefault();
    });

    document.addEventListener("mousemove", (e) => {
      if (!isResizing) return;

      const container = leftPane.parentElement;
      if (!container) return;
      const containerRect = container.getBoundingClientRect();
      let newWidth = e.clientX - containerRect.left;

      // Enforce min and max widths
      if (newWidth < 300) newWidth = 300;
      if (newWidth > containerRect.width - 400)
        newWidth = containerRect.width - 400;

      leftPane.style.width = `${newWidth}px`;
      leftPane.style.flex = "none";
    });

    document.addEventListener("mouseup", () => {
      if (isResizing) {
        isResizing = false;
        document.body.style.cursor = "default";
      }
    });
  }
});

// ==========================================
// CHART EXPORT & CUSTOMIZATION HANDLERS
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
  // Download Chart Buttons (PNG & PDF)
  document.getElementById("downloadPngBtn")?.addEventListener("click", () => {
    const mainChart = document.getElementById("chartArea");
    if (mainChart && mainChart.data) {
      Plotly.downloadImage(mainChart, {
        format: "png",
        filename: "dataviz_grafik",
      });
    } else {
      if (typeof showToast === "function")
        showToast("Lütfen önce bir grafik çizin", "error");
    }
  });

  document
    .getElementById("downloadPdfBtn")
    ?.addEventListener("click", async () => {
      const mainChart = document.getElementById("chartArea");
      if (mainChart && mainChart.data) {
        if (typeof showToast === "function")
          showToast("PDF raporu hazırlanıyor...", "info");
        try {
          const imgData = await Plotly.toImage(mainChart, {
            format: "png",
            width: 1000,
            height: 600,
          });
          if (typeof html2pdf === "function") {
            const wrapper = document.createElement("div");
            wrapper.style.padding = "24px";
            wrapper.style.background = "#ffffff";
            wrapper.style.color = "#0f172a";
            wrapper.style.fontFamily = "Inter, sans-serif";
            const titleText =
              document.getElementById("customChartTitle")?.value ||
              document.getElementById("currentChartTypeName")?.textContent ||
              "DataViz Grafik Raporu";
            wrapper.innerHTML = `<h2 style="margin:0 0 12px 0; color:#0f172a;">${escapeHtmlSafe(titleText)}</h2><p style="margin:0 0 16px 0; font-size:12px; color:#64748b;">Tarih: ${new Date().toLocaleDateString("tr-TR")}</p><img src="${imgData}" style="width:100%; height:auto; border-radius:8px;" />`;
            await html2pdf()
              .set({
                margin: 10,
                filename: "dataviz_grafik.pdf",
                image: { type: "jpeg", quality: 0.98 },
                html2canvas: { scale: 2, useCORS: true },
                jsPDF: { unit: "mm", format: "a4", orientation: "landscape" },
              })
              .from(wrapper)
              .save();
          } else if (window.jspdf && window.jspdf.jsPDF) {
            const doc = new window.jspdf.jsPDF({
              orientation: "landscape",
              unit: "mm",
              format: "a4",
            });
            doc.addImage(imgData, "PNG", 15, 20, 267, 160);
            doc.save("dataviz_grafik.pdf");
          } else if (
            typeof window.openPdfPreviewStudio === "function" &&
            window.dashboardCharts &&
            window.dashboardCharts.length > 0
          ) {
            window.openPdfPreviewStudio();
          } else {
            const win = window.open("");
            if (win) {
              win.document.write(
                `<html><head><title>DataViz Grafik Çıktısı</title></head><body style="margin:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#0f172a;color:white;font-family:sans-serif;"><h2 style="margin-top:20px;">${escapeHtmlSafe(window.currentPlotType || "Grafik")}</h2><img src="${imgData}" style="max-width:90%;border-radius:8px;"/><script>window.onload=function(){window.print();}<\/script></body></html>`,
              );
              win.document.close();
            }
          }
        } catch (err) {
          if (typeof showToast === "function")
            showToast("PDF oluşturulamadı: " + err.message, "error");
        }
      } else if (
        typeof window.openPdfPreviewStudio === "function" &&
        window.dashboardCharts &&
        window.dashboardCharts.length > 0
      ) {
        window.openPdfPreviewStudio();
      } else {
        if (typeof showToast === "function")
          showToast("Lütfen önce bir grafik çizin", "error");
      }
    });
});

/// --- SQL Bağlantı ve AI Güven Skoru Modülleri ---
document.addEventListener("DOMContentLoaded", () => {
  // SQL Modal Elements
  const btnOpenSqlModal = document.getElementById("btnOpenSqlModal");
  const sqlConnectModal = document.getElementById("sqlConnectModal");
  const btnCloseSqlModal = document.getElementById("btnCloseSqlModal");
  const btnCancelSqlModal = document.getElementById("btnCancelSqlModal");
  const btnExecuteSql = document.getElementById("btnExecuteSql");
  const sqlUriInput = document.getElementById("sqlUriInput");
  const sqlQueryInput = document.getElementById("sqlQueryInput");

  if (btnOpenSqlModal && sqlConnectModal) {
    btnOpenSqlModal.addEventListener("click", () => {
      sqlConnectModal.classList.remove("hidden");
    });
  }
  if (btnCloseSqlModal && sqlConnectModal) {
    btnCloseSqlModal.addEventListener("click", () =>
      sqlConnectModal.classList.add("hidden"),
    );
  }
  if (btnCancelSqlModal && sqlConnectModal) {
    btnCancelSqlModal.addEventListener("click", () =>
      sqlConnectModal.classList.add("hidden"),
    );
  }

  if (btnExecuteSql) {
    btnExecuteSql.addEventListener("click", async () => {
      const db_uri = sqlUriInput ? sqlUriInput.value.trim() : "";
      const query = sqlQueryInput ? sqlQueryInput.value.trim() : "";
      if (!db_uri || !query) {
        showToast(
          "Lütfen Veritabanı Bağlantı URI ve SQL Sorgusunu girin.",
          "warning",
          "Eksik Bilgi",
        );
        return;
      }

      const originalBtnText = btnExecuteSql.innerHTML;
      btnExecuteSql.innerHTML = "⏳ Çekiliyor...";
      btnExecuteSql.disabled = true;

      const prog = window.DataVizProgress?.start({
        icon: "🗄️",
        title: "SQL Veritabanından Veri Çekiliyor",
        showHud: true,
        stages: [
          {
            at: 0,
            short: "Bağlantı",
            label: "Veritabanı sunucusuna bağlanılıyor...",
          },
          {
            at: 45,
            short: "Sorgu",
            label: "SQL sorgusu çalıştırılıyor ve satırlar okunuyor...",
          },
          {
            at: 80,
            short: "Aktarım",
            label: "Sütun tipleri analiz stüdyosuna aktarılıyor...",
          },
        ],
      });

      try {
        const res = await fetch("/fetch_sql", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ db_uri, query }),
        });
        const data = await res.json();

        if (!res.ok) throw new Error(data.error || "SQL bağlantı hatası.");

        prog?.complete("SQL verisi başarıyla yüklendi!");
        sqlConnectModal?.classList.add("hidden");
        activeFileName = window.activeFileName = "SQL_Sorgu_Sonucu";
        applyUploadedDataset(data);
        showToast(
          `${data.total_rows} satır ve ${data.total_cols} sütun başarıyla çekildi.`,
          "success",
          "SQL Bağlantısı Başarılı",
        );
      } catch (err) {
        prog?.stop();
        showToast(err.message, "error", "SQL Bağlantı Hatası");
      } finally {
        btnExecuteSql.innerHTML = originalBtnText;
        btnExecuteSql.disabled = false;
      }
    });
  }

  // ── AI VERİ GÜVEN SKORU STÜDYOSU (TAM EKRAN) ──
  // ── AI VERİ GÜVEN SKORU STÜDYOSU (TAM EKRAN) ──
  function getScoreTheme(score) {
    const s = Number(score) || 0;
    const isLight =
      document.documentElement.getAttribute("data-theme") === "light";
    if (s >= 85) {
      return {
        color: isLight ? "#059669" : "#30d158",
        border: isLight ? "#059669" : "#30d158",
        bg: isLight ? "rgba(5, 150, 105, 0.1)" : "rgba(48, 209, 88, 0.14)",
        label: "Yüksek Güven",
      };
    }
    if (s >= 65) {
      return {
        color: isLight ? "#d97706" : "#ff9f0a",
        border: isLight ? "#d97706" : "#ff9f0a",
        bg: isLight ? "rgba(217, 119, 6, 0.1)" : "rgba(255, 159, 10, 0.14)",
        label: "Orta Güven (Onarım Önerilir)",
      };
    }
    return {
      color: isLight ? "#dc2626" : "#ff453a",
      border: isLight ? "#dc2626" : "#ff453a",
      bg: isLight ? "rgba(220, 38, 38, 0.1)" : "rgba(255, 69, 58, 0.15)",
      label: "Riskli Veri (Temizlik Şart)",
    };
  }

  function renderTrustStudio(data) {
    if (!data || !data.raw_report || !data.cleaned_report) return;
    const raw = data.raw_report;
    const clean = data.cleaned_report;
    const current = data.current_report || (data.is_cleaned ? clean : raw);
    const isCleaned = Boolean(data.is_cleaned);
    const hasCleaningHistory = Boolean(data.has_cleaning_history || isCleaned);
    const delta = Number(data.score_delta || 0);

    // Üst durum rozeti
    const globalChip = document.getElementById("trustGlobalStatusChip");
    if (globalChip) {
      globalChip.style.background = "";
      globalChip.style.color = "";
      globalChip.style.borderColor = "";
      if (isCleaned) {
        globalChip.textContent = "✓ Veri Seti Temizlendi ve Onarıldı";
        globalChip.className = "trust-status-chip clean";
      } else if (hasCleaningHistory) {
        globalChip.textContent =
          "🔧 Kısmi Temizleme Uygulandı — Kalan Sorunlar Mevcut";
        globalChip.className = "trust-status-chip info";
      } else if (
        raw.missing_cells > 0 ||
        raw.invalid_cells > 0 ||
        raw.duplicate_rows > 0
      ) {
        globalChip.textContent =
          "⚠️ Ham Veri Setinde Kalite Sorunları Tespit Edildi";
        globalChip.className = "trust-status-chip warning";
      } else {
        globalChip.textContent = "✓ Veri Seti Doğal Olarak Temiz";
        globalChip.className = "trust-status-chip clean";
      }
    }

    // 1. SOL KART (TEMİZLENMEMİŞ / HAM VERİ SETİ)
    const rawTheme = getScoreTheme(raw.overall_score);
    const rawScoreEl = document.getElementById("trustRawOverallScore");
    if (rawScoreEl) {
      rawScoreEl.textContent = Number(raw.overall_score).toFixed(1);
      rawScoreEl.style.color = rawTheme.color;
    }
    const rawCircle = document.getElementById("trustRawScoreCircle");
    if (rawCircle) {
      rawCircle.style.borderColor = rawTheme.border;
      rawCircle.style.background = rawTheme.bg;
    }
    const rawGrade = document.getElementById("trustRawGradeBadge");
    if (rawGrade) {
      rawGrade.textContent = rawTheme.label;
      rawGrade.style.color = rawTheme.color;
      rawGrade.style.borderColor = rawTheme.border;
      rawGrade.style.background = rawTheme.bg;
    }

    const setBar = (valId, barId, scoreVal) => {
      const vEl = document.getElementById(valId);
      const bEl = document.getElementById(barId);
      const pct = Math.max(0, Math.min(100, Number(scoreVal) || 0));
      if (vEl) vEl.textContent = `${pct.toFixed(1)}%`;
      if (bEl) bEl.style.width = `${pct}%`;
    };

    setBar(
      "trustRawCompletenessVal",
      "trustRawCompletenessBar",
      raw.completeness_score,
    );
    setBar("trustRawTypeVal", "trustRawTypeBar", raw.type_validity_score);
    setBar("trustRawOutlierVal", "trustRawOutlierBar", raw.outlier_score);
    setBar("trustRawUniqueVal", "trustRawUniqueBar", raw.uniqueness_score);

    const fmtNum = (n) => Number(n || 0).toLocaleString("tr-TR");
    const rawMissEl = document.getElementById("trustRawMissingCount");
    if (rawMissEl) {
      rawMissEl.textContent = `${fmtNum(raw.missing_cells)} Hücre (%${raw.missing_pct})`;
    }
    const rawInvEl = document.getElementById("trustRawInvalidCount");
    if (rawInvEl) {
      rawInvEl.textContent = `${fmtNum(raw.invalid_cells)} Hücre (${raw.anomalous_cols_count} Sütun)`;
    }
    const rawOutEl = document.getElementById("trustRawOutlierCount");
    if (rawOutEl) {
      rawOutEl.textContent = `${fmtNum(raw.outlier_cells)} Hücre (%${raw.outlier_pct})`;
    }
    const rawDupEl = document.getElementById("trustRawDupCount");
    if (rawDupEl) {
      rawDupEl.textContent = `${fmtNum(raw.duplicate_rows)} Satır (%${raw.duplicate_pct})`;
    }

    // 2. SAĞ KART (TEMİZLENMİŞ VERİ SETİ)
    const cleanStateBadge = document.getElementById("trustCleanStateBadge");
    const cleanSubtitle = document.getElementById("trustCleanSubtitle");
    if (cleanStateBadge) {
      cleanStateBadge.style.background = "";
      cleanStateBadge.style.color = "";
      if (isCleaned) {
        cleanStateBadge.textContent =
          "✅ TEMİZLENMİŞ AKTİF VERİ SETİ (UYGULANDI)";
        cleanStateBadge.className = "trust-state-badge trust-badge-clean";
      } else if (hasCleaningHistory) {
        cleanStateBadge.textContent =
          "🔄 KISMİ ONARIM UYGULANDI (TAM TEMİZLİK HEDEFİ)";
        cleanStateBadge.className = "trust-state-badge trust-badge-history";
      } else {
        cleanStateBadge.textContent =
          "✨ TEMİZLENMİŞ VERİ SETİ (ONARIM SONRASI HEDEF)";
        cleanStateBadge.className = "trust-state-badge trust-badge-target";
      }
    }
    if (cleanSubtitle) {
      cleanSubtitle.textContent = isCleaned
        ? "Veri setinizdeki boş hücreler ve sözel bozulmalar temizlendi. Grafikleriniz şu an bu güvenilir veriyle çiziliyor."
        : hasCleaningHistory
          ? `Bazı sütunlar onarıldı (Mevcut aktif skor: ${Number(current.overall_score).toFixed(1)}). Kalan tüm sorunlar giderildiğinde ulaşılacak hedef skor:`
          : "Boş hücreler doldurulup sözel bozulmalar onarıldığında veri setinizin ulaşacağı güvenilirlik skoru:";
    }

    const cleanScoreEl = document.getElementById("trustCleanOverallScore");
    if (cleanScoreEl) {
      cleanScoreEl.textContent = Number(clean.overall_score).toFixed(1);
    }
    const deltaBadge = document.getElementById("trustScoreDeltaBadge");
    if (deltaBadge) {
      deltaBadge.style.background = "";
      deltaBadge.style.color = "";
      if (delta > 0) {
        deltaBadge.textContent = `+${delta.toFixed(1)} Puan Artış ↑`;
        deltaBadge.className = "trust-delta-badge positive";
      } else {
        deltaBadge.textContent = "Maksimum Güven ✓";
        deltaBadge.className = "trust-delta-badge max";
      }
    }

    setBar(
      "trustCleanCompletenessVal",
      "trustCleanCompletenessBar",
      clean.completeness_score,
    );
    setBar("trustCleanTypeVal", "trustCleanTypeBar", clean.type_validity_score);
    setBar("trustCleanOutlierVal", "trustCleanOutlierBar", clean.outlier_score);
    setBar(
      "trustCleanUniqueVal",
      "trustCleanUniqueBar",
      clean.uniqueness_score,
    );

    const cleanMissEl = document.getElementById("trustCleanMissingCount");
    if (cleanMissEl) {
      cleanMissEl.textContent = `${fmtNum(clean.missing_cells)} Hücre (%${clean.missing_pct})`;
    }
    const cleanInvEl = document.getElementById("trustCleanInvalidCount");
    if (cleanInvEl) {
      cleanInvEl.textContent = `${fmtNum(clean.invalid_cells)} Hücre (${clean.anomalous_cols_count} Sütun)`;
    }
    const cleanOutEl = document.getElementById("trustCleanOutlierCount");
    if (cleanOutEl) {
      cleanOutEl.textContent = `${fmtNum(clean.outlier_cells)} Hücre (%${clean.outlier_pct})`;
    }
    const cleanDupEl = document.getElementById("trustCleanDupCount");
    if (cleanDupEl) {
      cleanDupEl.textContent = `${fmtNum(clean.duplicate_rows)} Satır (%${clean.duplicate_pct})`;
    }

    const hasPendingIssues =
      current.missing_cells > 0 ||
      current.invalid_cells > 0 ||
      current.duplicate_rows > 0;
    const cleanFooter = document.getElementById("trustCleanCardFooter");
    const topHealBtn = document.getElementById("btnTrustAutoHealAll");
    if (topHealBtn) {
      topHealBtn.innerHTML = !hasPendingIssues
        ? "✓ Tüm Veri Seti Temizlendi"
        : "🪄 Tüm Sorunları Tek Tıkla Onar & Temizle";
    }
    if (cleanFooter) {
      if (hasPendingIssues) {
        const dupPart =
          current.duplicate_rows > 0
            ? ` ve <strong>${fmtNum(current.duplicate_rows)} mükerrer satır</strong>`
            : "";
        cleanFooter.innerHTML = `
          <div class="trust-heal-prompt-box">
            <div class="trust-heal-prompt-text">
              💡 <strong>${fmtNum(current.missing_cells)} boş hücre</strong>, <strong>${fmtNum(current.invalid_cells)} hatalı/sözel hücre</strong>${dupPart} tek tıkla onarılabilir.
            </div>
            <button type="button" id="btnTrustCardQuickHeal" class="btn-primary btn-trust-card-heal">
              ⚡ Şimdi Onar ve Skoru ${Number(clean.overall_score).toFixed(1)}'e Yükselt
            </button>
          </div>
        `;
        document
          .getElementById("btnTrustCardQuickHeal")
          ?.addEventListener("click", autoHealFromTrustStudio);
      } else {
        cleanFooter.innerHTML = `
          <div class="trust-clean-success-box">
            🎉 Veri setinizdeki tüm eksik ve hatalı veriler giderildi! Analiz ve grafikleriniz en yüksek doğrulukla çalışıyor.
          </div>
        `;
      }
    }

    // 3. ALT TABLO: SÜTUN BAZLI GÜVEN KARNESİ
    const tbody = document.getElementById("trustColumnsTableBody");
    if (tbody) {
      const cols = current.columns || [];
      if (cols.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="trust-table-empty">Sütun bulunamadı.</td></tr>`;
      } else {
        tbody.innerHTML = cols
          .map((c) => {
            const cTheme = getScoreTheme(c.trust_score);
            const samplesHtml =
              c.sample_invalid_values && c.sample_invalid_values.length > 0
                ? `<div class="trust-sample-values">Örn: ${c.sample_invalid_values.map((v) => `<span class="trust-sample-tag">"${escapeHtmlSafe(String(v))}"</span>`).join(" ")}</div>`
                : "";
            let actionHtml = `<span class="trust-safe-badge">✅ Güvenli</span>`;
            if (c.has_anomaly) {
              actionHtml = `<button type="button" class="btn-trust-col-repair" data-col="${escapeHtmlSafe(c.column)}">🪄 Sütunu Onar</button>`;
            } else if (c.missing_count > 0) {
              actionHtml = `<button type="button" class="btn-trust-col-clean" data-col="${escapeHtmlSafe(c.column)}">🧹 Boşları Doldur</button>`;
            }
            const typeClass = c.has_anomaly
              ? "anomaly"
              : c.is_numeric
                ? "numeric"
                : "categorical";
            return `
              <tr class="trust-col-row">
                <td class="trust-col-name-cell">${escapeHtmlSafe(c.column)}</td>
                <td class="trust-col-type-cell">
                  <span class="trust-type-badge ${typeClass}">
                    ${escapeHtmlSafe(c.dtype_label)}
                  </span>
                </td>
                <td class="trust-score-cell">
                  <div class="trust-score-bar-wrap">
                    <div class="trust-score-track">
                      <div class="trust-score-fill" style="width: ${Math.max(0, Math.min(100, c.trust_score))}%; background: ${cTheme.border};"></div>
                    </div>
                    <strong class="trust-score-num" style="color: ${cTheme.color};">${Number(c.trust_score).toFixed(1)}</strong>
                  </div>
                </td>
                <td class="trust-missing-cell ${c.missing_count > 0 ? "has-issue" : ""}">
                  ${c.missing_count > 0 ? `${fmtNum(c.missing_count)} (%${c.missing_pct})` : "0 (Tam)"}
                </td>
                <td class="trust-invalid-cell ${c.invalid_count > 0 ? "has-issue" : ""}">
                  ${c.invalid_count > 0 ? `${fmtNum(c.invalid_count)} (%${c.invalid_pct})` : "0 (Temiz)"}
                  ${samplesHtml}
                </td>
                <td class="trust-outlier-cell ${c.outlier_count > 0 ? "has-outlier" : ""}">
                  ${c.is_numeric ? (c.outlier_count > 0 ? `${fmtNum(c.outlier_count)} (%${c.outlier_pct})` : "0 (Normal)") : "—"}
                </td>
                <td class="trust-action-cell">${actionHtml}</td>
              </tr>
            `;
          })
          .join("");

        tbody.querySelectorAll(".btn-trust-col-repair").forEach((btn) => {
          btn.addEventListener("click", async () => {
            const colName = btn.getAttribute("data-col");
            if (!colName) return;
            btn.disabled = true;
            btn.textContent = "⏳ Onarılıyor...";
            try {
              const res = await fetch("/repair_column_anomalies", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  column: colName,
                  repair_mode: "smart_heal",
                }),
              });
              const rData = await res.json();
              if (!res.ok) throw new Error(rData.error || "Onarım hatası");
              numericColumns = window.numericColumns =
                rData.numeric_columns || [];
              categoricalColumns = window.categoricalColumns =
                rData.categorical_columns || [];
              globalColumns = window.globalColumns = [
                ...categoricalColumns,
                ...numericColumns,
              ];
              if (typeof initDragDropPool === "function")
                initDragDropPool(true);
              if (typeof renderPivotPoolStructured === "function")
                renderPivotPoolStructured();
              if (typeof window.populateRegColumnSelects === "function")
                window.populateRegColumnSelects();
              if (typeof updateAnomalyBadges === "function" && rData.health)
                updateAnomalyBadges(rData.health);
              showToast(`"${colName}" sütunu başarıyla onarıldı!`, "success");
              await fetchAndRenderTrustReport().catch(() => {});
            } catch (e) {
              showToast(e.message, "error");
              btn.disabled = false;
              btn.textContent = "🪄 Sütunu Onar";
            }
          });
        });

        tbody.querySelectorAll(".btn-trust-col-clean").forEach((btn) => {
          btn.addEventListener("click", async () => {
            const colName = btn.getAttribute("data-col");
            if (!colName) return;
            btn.disabled = true;
            btn.textContent = "⏳ Dolduruluyor...";
            try {
              const res = await fetch("/clean_data", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  action: "fill_mean",
                  column: colName,
                }),
              });
              const cData = await res.json();
              if (!res.ok) throw new Error(cData.error || "Temizleme hatası");
              numericColumns = window.numericColumns =
                cData.numeric_columns || [];
              categoricalColumns = window.categoricalColumns =
                cData.categorical_columns || [];
              globalColumns = window.globalColumns = [
                ...categoricalColumns,
                ...numericColumns,
              ];
              if (typeof initDragDropPool === "function")
                initDragDropPool(true);
              if (typeof renderPivotPoolStructured === "function")
                renderPivotPoolStructured();
              if (typeof window.populateRegColumnSelects === "function")
                window.populateRegColumnSelects();
              if (typeof updateAnomalyBadges === "function" && cData.health)
                updateAnomalyBadges(cData.health);
              showToast(
                `"${colName}" sütunundaki boş hücreler dolduruldu!`,
                "success",
              );
              await fetchAndRenderTrustReport().catch(() => {});
            } catch (e) {
              showToast(e.message, "error");
              btn.disabled = false;
              btn.textContent = "🧹 Boşları Doldur";
            }
          });
        });
      }
    }
  }

  async function fetchAndRenderTrustReport() {
    const res = await fetch("/get_trust_report");
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Güven raporu alınamadı.");
    renderTrustStudio(data);
    return data;
  }
  window.fetchAndRenderTrustReport = fetchAndRenderTrustReport;

  async function openTrustStudio() {
    const s3 = document.getElementById("step3-dashboard");
    const pv = document.getElementById("screen-pivot-studio");
    if (s3 && !s3.classList.contains("hidden")) {
      lastScreenBeforeTrust = 3;
    } else if (pv && !pv.classList.contains("hidden")) {
      lastScreenBeforeTrust = "pivot";
    } else {
      lastScreenBeforeTrust = 2;
    }
    const trFile = document.getElementById("trustFileName");
    if (trFile) trFile.textContent = window.activeFileName || "veri.xlsx";

    showScreen("trust");
    try {
      await fetchAndRenderTrustReport().catch(() => {});
    } catch (err) {
      showToast(err.message, "error", "Güven Skoru Hatası");
    }
  }

  async function autoHealFromTrustStudio() {
    const btn = document.getElementById("btnTrustAutoHealAll");
    const origHtml = btn ? btn.innerHTML : "";
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = "⏳ Tüm Veri Seti Onarılıyor...";
    }

    const prog = window.DataVizProgress?.start({
      icon: "🪄",
      title: "Veri Seti Temizleniyor ve Güven Skoru Yükseltiliyor",
      showHud: true,
      stages: [
        {
          at: 0,
          short: "Tip Onarımı",
          label: "Sözel ve hatalı hücreler sayısal formata dönüştürülüyor...",
        },
        {
          at: 45,
          short: "Boş Veri",
          label:
            "Eksik (NaN) hücreler istatistiksel ortalamalarla dolduruluyor...",
        },
        {
          at: 80,
          short: "Skor Hesabı",
          label: "Temizlenmiş veri seti güven karnesi güncelleniyor...",
        },
      ],
    });

    try {
      const res = await fetch("/auto_heal_all_trust", { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Otomatik onarım başarısız.");

      numericColumns = window.numericColumns = data.numeric_columns || [];
      categoricalColumns = window.categoricalColumns =
        data.categorical_columns || [];
      globalColumns = window.globalColumns = [
        ...categoricalColumns,
        ...numericColumns,
      ];

      if (typeof initDragDropPool === "function") initDragDropPool(true);
      if (typeof renderPivotPoolStructured === "function")
        renderPivotPoolStructured();
      if (typeof window.populateRegColumnSelects === "function")
        window.populateRegColumnSelects();
      if (typeof renderChartGrid === "function") renderChartGrid("all");
      if (typeof evaluateCharts === "function") evaluateCharts();
      if (typeof updateAnomalyBadges === "function" && data.health) {
        updateAnomalyBadges(data.health);
      }

      renderTrustStudio(data);
      prog?.complete("Veri seti temizlendi ve güven skoru güncellendi!");
      showToast(
        `🎉 Veri setiniz temizlendi! Güven Skoru ${Number(data.raw_report.overall_score).toFixed(1)} puandan ${Number(data.cleaned_report.overall_score).toFixed(1)} puana yükseldi.`,
        "success",
        "Veri Güvenliği Yükseltildi",
      );
    } catch (err) {
      prog?.stop();
      if (btn) btn.innerHTML = origHtml;
      showToast(err.message, "error", "Onarım Hatası");
    } finally {
      if (btn) {
        btn.disabled = false;
      }
    }
  }

  document
    .getElementById("btnCalculateRiskScore")
    ?.addEventListener("click", openTrustStudio);
  document
    .getElementById("btnOpenTrustStudioS3")
    ?.addEventListener("click", openTrustStudio);

  document
    .getElementById("btnTrustBackToStudio")
    ?.addEventListener("click", async () => {
      const targetScreen =
        lastScreenBeforeTrust === 3 || lastScreenBeforeTrust === "pivot"
          ? lastScreenBeforeTrust
          : 2;
      showScreen(targetScreen);
      if (targetScreen === 3) {
        if (typeof refreshActiveChart === "function") {
          await refreshActiveChart();
        }
        const regPane = document.getElementById("tabRegression");
        if (
          regPane &&
          !regPane.classList.contains("hidden") &&
          typeof window.fetchAndRenderRegressionStudio === "function"
        ) {
          window.fetchAndRenderRegressionStudio().catch(() => {});
        }
      }
    });

  document
    .getElementById("btnTrustAutoHealAll")
    ?.addEventListener("click", autoHealFromTrustStudio);

  document
    .getElementById("btnTrustOpenDetailedPrep")
    ?.addEventListener("click", () => {
      if (typeof window.openDataPrepModal === "function") {
        window.openDataPrepModal();
      }
    });

  ["btnCloseDataPrepModal", "dpSkipBtn"].forEach((id) => {
    document.getElementById(id)?.addEventListener("click", () => {
      const ts = document.getElementById("screen-trust-studio");
      if (ts && !ts.classList.contains("hidden")) {
        fetchAndRenderTrustReport().catch(() => {});
      }
    });
  });

  // İsteğe bağlı: Satır bazlı Guven_Skoru_AI (Isolation Forest) sütununu veri havuzuna ekleme butonu
  const btnAddRowRiskColumn = document.getElementById("btnAddRowRiskColumn");
  if (btnAddRowRiskColumn) {
    btnAddRowRiskColumn.addEventListener("click", async () => {
      if (btnAddRowRiskColumn.disabled) return;
      const origHtml = btnAddRowRiskColumn.innerHTML;
      btnAddRowRiskColumn.disabled = true;
      btnAddRowRiskColumn.innerHTML = "⏳ Hesaplanıyor...";

      try {
        const res = await fetch("/calculate_risk_score", { method: "POST" });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Skor hesaplama hatası.");

        const newCol = data.new_column || "Guven_Skoru_AI";
        numericColumns = window.numericColumns = data.numeric_columns || [];
        categoricalColumns = window.categoricalColumns =
          data.categorical_columns || [];
        globalColumns = window.globalColumns = [
          ...categoricalColumns,
          ...numericColumns,
        ];
        if (!calculatedColumns.includes(newCol)) {
          calculatedColumns.push(newCol);
        }
        window.calculatedColumns = calculatedColumns;
        if (typeof initDragDropPool === "function") initDragDropPool(true);

        showToast(
          `✨ "${newCol}" sütunu üretildi ve Veri Havuzuna eklendi! (Ortalama Skor: ${data.mean_score ?? "-"})`,
          "success",
          "Satır Bazlı AI Skoru Eklendi",
        );
        btnAddRowRiskColumn.innerHTML = "✓ Guven_Skoru_AI Sütunu Eklendi";
      } catch (err) {
        showToast(err.message, "error", "AI Güven Skoru Hatası");
        btnAddRowRiskColumn.innerHTML = origHtml;
      } finally {
        btnAddRowRiskColumn.disabled = false;
      }
    });
  }

  // 🌓 UNIFIED THEME SYSTEM (Apple Pro Dark <-> Clean Corporate Light)
  window.applyTheme = function (theme) {
    document.documentElement.setAttribute("data-theme", theme);
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    localStorage.setItem("dataviz-theme", theme);

    // Update active Plotly chart with theme colors if rendered
    try {
      const chartBox = document.getElementById("mainMegaChart");
      if (chartBox && chartBox.data && window.Plotly) {
        const isLight = theme === "light";
        const bg = isLight ? "#ffffff" : "transparent";
        const tc = isLight ? "#0f172a" : "#f5f5f7";
        const gc = isLight
          ? "rgba(15, 23, 42, 0.08)"
          : "rgba(255, 255, 255, 0.08)";
        window.Plotly.relayout(chartBox, {
          plot_bgcolor: bg,
          paper_bgcolor: "transparent",
          "font.color": tc,
          "xaxis.gridcolor": gc,
          "yaxis.gridcolor": gc,
        });
      }
    } catch (e) {
      console.warn("Theme chart relayout warning:", e);
    }
  };

  // Initialize theme from storage
  const savedTheme = localStorage.getItem("dataviz-theme") || "dark";
  window.applyTheme(savedTheme);

  // Bind all theme toggle buttons (.theme-toggle-trigger or .theme-toggle-btn)
  document
    .querySelectorAll(".theme-toggle-trigger, .theme-toggle-btn")
    .forEach((btn) => {
      btn.addEventListener("click", () => {
        const current =
          document.documentElement.getAttribute("data-theme") || "dark";
        const next = current === "dark" ? "light" : "dark";
        window.applyTheme(next);
      });
    });
});
