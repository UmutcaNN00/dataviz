/* ════════════════════════════════════════════════════════════
   DATAVIZ PRO V6 — GLOBAL STATE & REACTIVE STORE
   Shared reactive state & Modern Single-Instance Progress Bar
════════════════════════════════════════════════════════════ */

var globalColumns = [];
var numericColumns = [];
var categoricalColumns = [];
var calculatedColumns = []; // Kullanıcının ürettiği özel formül sütunları
var joinedColumns = []; // 2. dosyadan birleştirilen sütunlar
var sheetNames = [];
var currentChartData = null;
var currentStats = null;
var currentKpis = [];
var currentAiInsight = "";
var activeFileName = "";
var currentPlotType = "";

// Seçim Durumu (Eksenler)
var axisConfig = { x: null, y: [] };

// 🔍 Aktif Filtreler (Slicers)
var activeFilters = [];

// 🎛️ Çoklu Pano (Dashboard Canvas) Listesi
var dashboardCharts = [];

var PALETTE = [
  "#a78bfa",
  "#60a5fa",
  "#34d399",
  "#f472b6",
  "#fb923c",
  "#fbbf24",
  "#38bdf8",
  "#4ade80",
  "#c084fc",
  "#f97316",
];

/* ── MODERN SINGLE-INSTANCE PROGRESS BAR SYSTEM ── */
var DataVizProgress = (function () {
  let activeTimer = null;
  let hideTimer = null;
  let currentPct = 0;
  let startTimeMs = 0;
  let currentConfig = null;
  let activePrefix = "dvInline";

  function ensureHudNode() {
    const oldLaser = document.getElementById("dvTopLaserBar");
    if (oldLaser) oldLaser.remove();

    if (!document.getElementById("dvFloatingHud")) {
      const hud = document.createElement("div");
      hud.id = "dvFloatingHud";
      hud.className = "dv-floating-hud";
      document.body.appendChild(hud);
    }
  }

  function buildCardMarkup(prefix, cfg, pct, stageText, activeStageIdx) {
    const safePct = Math.max(0, Math.min(100, Math.round(pct)));
    const stages = cfg.stages || [];
    let pillsHtml = "";
    if (stages.length > 0) {
      pillsHtml = `<div class="dv-progress-steps-pills" id="${prefix}_pills">`;
      stages.forEach((s, idx) => {
        const stateClass =
          safePct >= 100 || idx < activeStageIdx
            ? "done"
            : idx === activeStageIdx
              ? "active"
              : "";
        const checkPrefix =
          safePct >= 100 || idx < activeStageIdx ? "✓ " : `${idx + 1}. `;
        pillsHtml += `<span class="dv-step-pill ${stateClass}">${checkPrefix}${s.short || s.label}</span>`;
      });
      pillsHtml += `</div>`;
    }

    return `
      <div class="dv-progress-card" id="${prefix}_card">
        <div class="dv-progress-header">
          <div class="dv-progress-title-wrap">
            <div class="dv-progress-icon" id="${prefix}_icon">${cfg.icon || "⚡"}</div>
            <div class="dv-progress-title" id="${prefix}_title">${cfg.title || "İşlem Yürütülüyor..."}</div>
          </div>
          <div style="display: flex; align-items: center; gap: 8px; flex-shrink: 0;">
            <span id="${prefix}_elapsed" style="font-family: 'JetBrains Mono', monospace; font-size: 0.74rem; color: #94a3b8;">0.1 sn</span>
            <div class="dv-progress-pct" id="${prefix}_pct">%${safePct}</div>
          </div>
        </div>
        <div
          class="dv-progress-track"
          role="progressbar"
          aria-valuenow="${safePct}"
          aria-valuemin="0"
          aria-valuemax="100"
          aria-label="${cfg.title || "İşlem durumu"}"
          id="${prefix}_track"
        >
          <div class="dv-progress-fill" id="${prefix}_fill" style="width: ${safePct}%;"></div>
        </div>
        <div class="dv-progress-stage">
          <div class="dv-progress-stage-text" id="${prefix}_stage">
            <span class="dv-progress-stage-dot"></span>
            <span id="${prefix}_stage_lbl">${stageText || "Hazırlanıyor..."}</span>
          </div>
        </div>
        ${pillsHtml}
      </div>
    `;
  }

  function resolveStage(stages, pct) {
    if (!stages || !stages.length) {
      return { idx: 0, label: "İşlem devam ediyor..." };
    }
    let chosenIdx = 0;
    for (let i = 0; i < stages.length; i++) {
      if (pct >= (stages[i].at || 0)) {
        chosenIdx = i;
      }
    }
    return { idx: chosenIdx, label: stages[chosenIdx].label };
  }

  function updateTargets(pct, customLabel = null) {
    if (!currentConfig) return;
    currentPct = Math.max(0, Math.min(100, pct));
    const safePct = Math.round(currentPct);
    const stageInfo = resolveStage(currentConfig.stages, safePct);
    const stageText = customLabel || stageInfo.label;
    const elapsedSec = Math.max(0.1, (Date.now() - startTimeMs) / 1000).toFixed(
      1,
    );

    const prefix = activePrefix;
    const pctEl = document.getElementById(`${prefix}_pct`);
    const elapsedEl = document.getElementById(`${prefix}_elapsed`);
    const fillEl = document.getElementById(`${prefix}_fill`);
    const trackEl = document.getElementById(`${prefix}_track`);
    const lblEl = document.getElementById(`${prefix}_stage_lbl`);
    const pillsEl = document.getElementById(`${prefix}_pills`);

    if (pctEl) pctEl.textContent = `%${safePct}`;
    if (elapsedEl) elapsedEl.textContent = `${elapsedSec} sn`;
    if (fillEl) fillEl.style.width = `${safePct}%`;
    if (trackEl) trackEl.setAttribute("aria-valuenow", String(safePct));
    if (lblEl) lblEl.textContent = stageText;

    if (pillsEl && currentConfig.stages) {
      const spans = pillsEl.querySelectorAll(".dv-step-pill");
      spans.forEach((sp, idx) => {
        const s = currentConfig.stages[idx];
        if (!s) return;
        const isDone = safePct >= 100 || idx < stageInfo.idx;
        const isActive = safePct < 100 && idx === stageInfo.idx;
        sp.className = `dv-step-pill ${isDone ? "done" : isActive ? "active" : ""}`;
        sp.textContent = `${isDone ? "✓ " : idx + 1 + ". "}${s.short || s.label}`;
      });
    }
  }

  function start(options = {}) {
    ensureHudNode();
    if (activeTimer) clearInterval(activeTimer);
    if (hideTimer) clearTimeout(hideTimer);

    startTimeMs = Date.now();
    currentConfig = {
      icon: options.icon || "⚡",
      title: options.title || "İşlem Yürütülüyor...",
      stages: options.stages || [
        { at: 0, short: "Hazırlık", label: "Veri hazırlanıyor..." },
        {
          at: 40,
          short: "Hesaplama",
          label: "İstatistiksel motor çalışıyor...",
        },
        { at: 75, short: "Görselleştirme", label: "Arayüz güncelleniyor..." },
      ],
      containerId: options.containerId || null,
      autoAdvance:
        options.autoAdvance !== undefined ? options.autoAdvance : true,
    };

    currentPct = options.initialPct !== undefined ? options.initialPct : 6;
    const initStage = resolveStage(currentConfig.stages, currentPct);

    const hud = document.getElementById("dvFloatingHud");
    const container = currentConfig.containerId
      ? document.getElementById(currentConfig.containerId)
      : null;

    // Strictly render ONLY ONE progress bar: inline if container exists, otherwise HUD
    if (container) {
      activePrefix = "dvInline";
      if (hud) {
        hud.classList.remove("visible");
        hud.innerHTML = "";
      }
      container.classList.remove("hidden", "loading", "error", "success");
      container.style.display = "block";
      container.style.background = "transparent";
      container.style.border = "none";
      container.style.padding = "0";
      container.innerHTML = buildCardMarkup(
        "dvInline",
        currentConfig,
        currentPct,
        initStage.label,
        initStage.idx,
      );
    } else if (hud) {
      activePrefix = "dvHud";
      hud.innerHTML = buildCardMarkup(
        "dvHud",
        currentConfig,
        currentPct,
        initStage.label,
        initStage.idx,
      );
      hud.classList.add("visible");
    }

    updateTargets(currentPct);

    if (currentConfig.autoAdvance) {
      // Smooth asymptotic curve so long 100M-row tasks never race to 92% prematurely
      activeTimer = setInterval(() => {
        if (currentPct < 88) {
          const remaining = 90 - currentPct;
          const delta = Math.max(0.4, remaining * 0.055);
          updateTargets(Math.min(88, currentPct + delta));
        } else {
          // Keep updating elapsed timer even if holding at 88%
          updateTargets(currentPct);
        }
      }, 220);
    }

    return {
      set: (pct, customLabel) => updateTargets(pct, customLabel),
      complete: (doneLabel) => complete(doneLabel),
      stop: () => stop(),
    };
  }

  function complete(doneLabel = "İşlem başarıyla tamamlandı!") {
    if (activeTimer) {
      clearInterval(activeTimer);
      activeTimer = null;
    }
    updateTargets(100, doneLabel);

    hideTimer = setTimeout(() => {
      stop();
    }, 180);
  }

  function stop() {
    if (activeTimer) {
      clearInterval(activeTimer);
      activeTimer = null;
    }
    const hud = document.getElementById("dvFloatingHud");
    if (hud) {
      hud.classList.remove("visible");
      hud.innerHTML = "";
    }
    currentConfig = null;
  }

  return {
    start,
    set: updateTargets,
    complete,
    stop,
    buildCardMarkup,
  };
})();

// Window nesnesine bağlama
window.globalColumns = globalColumns;
window.numericColumns = numericColumns;
window.categoricalColumns = categoricalColumns;
window.calculatedColumns = calculatedColumns;
window.joinedColumns = joinedColumns;
window.sheetNames = sheetNames;
window.currentChartData = currentChartData;
window.currentStats = currentStats;
window.currentKpis = currentKpis;
window.currentAiInsight = currentAiInsight;
window.activeFileName = activeFileName;
window.currentPlotType = currentPlotType;
window.axisConfig = axisConfig;
window.activeFilters = activeFilters;
window.dashboardCharts = dashboardCharts;
window.PALETTE = PALETTE;
window.DataVizProgress = DataVizProgress;
