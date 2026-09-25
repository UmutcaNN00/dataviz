/* ════════════════════════════════════════════════════════════
   DATAVIZ PRO V6 — APPLICATION COORDINATOR (app.js)
   Screen Transitions, Upload Handlers, Navigation & Shortcuts
════════════════════════════════════════════════════════════ */

var isUploading = false;

// ── SCREEN TRANSITIONS COORDINATOR ──
function showScreen(num) {
  const ids = [
    "step1-upload",
    "step2-config",
    "step3-dashboard",
    "screen-pivot-studio",
  ];
  const screens = ids.map((id) => document.getElementById(id));
  screens.forEach(
    (s) => s && (s.classList.add("hidden"), s.classList.remove("active")),
  );

  const activeIdx = num === "pivot" || num === 4 ? 3 : num - 1;
  const target = screens[activeIdx];
  if (target) {
    target.classList.remove("hidden");
    target.classList.add("active");
  }

  if ((num === 4 || num === "pivot") && typeof initPivotStudio === "function") {
    initPivotStudio();
    if (typeof refreshPivotStudio === "function") refreshPivotStudio();
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

  if (typeof updateDashboardBadge === "function") updateDashboardBadge();
  if (typeof renderActiveFilterChips === "function") renderActiveFilterChips();
  renderSheetTabs(sheetNames, data.active_sheet);

  const s2 = document.getElementById("s2FileName");
  if (s2) s2.textContent = activeFileName;
  const pv = document.getElementById("pivotFileName");
  if (pv) pv.textContent = activeFileName;

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

    const s2 = document.getElementById("s2FileName");
    if (s2 && activeFileName)
      s2.textContent = `${activeFileName} (${sheetName})`;
    const pv = document.getElementById("pivotFileName");
    if (pv && activeFileName)
      pv.textContent = `${activeFileName} (${sheetName})`;

    if (typeof renderActiveFilterChips === "function")
      renderActiveFilterChips();
    renderSheetTabs(sheetNames, sheetName);
    if (typeof initDragDropPool === "function") initDragDropPool();
    if (typeof renderChartGrid === "function") renderChartGrid("all");
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
          window.fetchAndRenderRegressionStudio();
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
