/* ══════════════════════════════════════════════════════════════════
   DATAVIZ PRO — APPLE PRO EDITION CONTROLLER (analysis_apple.js)
   Full Integration: Reactive Store, Backend Wiring, Plotly 50 Engine,
   Hypothesis Lab, Data Healer, Joiner, Formula Wizard, Slicers,
   Pivot Studio, Executive Dashboard & A4 Report.
══════════════════════════════════════════════════════════════════ */

// ── GLOBAL REACTIVE STATE ──
const state = {
  activeDataset: {
    fileName: '',
    totalRows: 0,
    totalCols: 0,
    sheetNames: [],
    activeSheet: null,
    numericColumns: [],
    categoricalColumns: [],
    calculatedColumns: [],
    joinedColumns: []
  },
  axis: {
    x: null, // { name: string, type: 'num' | 'cat' }
    y: []    // Array of { name: string, type: 'num' | 'cat' }
  },
  aggFunc: 'sum',
  currentPlotType: 'scatter',
  currentPalette: '#38bdf8', // Default Cyan
  studioMode: 'charts',      // 'charts', 'stats', 'pivot', 'dash', 'table'
  activeFilters: [],         // Array of { column, type, values?, min?, max? }
  pinnedCharts: [],          // Pinned chart objects for Executive Dashboard
  pivotConfig: {
    rows: [],
    cols: [],
    values: [],
    agg_func: 'sum'
  },
  currentChartData: null,
  currentStats: null,
  currentRegression: null,
  currentHealth: null,
  tableLimit: 10,
  secondFileCols: null,
  formulaSelectedOp: '+'
};

// ── UTILITY HELPERS ──
function showToast(message, type = 'info', title = '') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'fixed bottom-5 right-5 z-[99999] flex flex-col gap-2.5 pointer-events-none';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  const borderColors = {
    info: 'border-blue-500/40 bg-[#0e1626]/95 text-blue-200',
    success: 'border-emerald-500/40 bg-[#0c1f18]/95 text-emerald-200',
    error: 'border-rose-500/40 bg-[#240f14]/95 text-rose-200',
    warning: 'border-amber-500/40 bg-[#241a0b]/95 text-amber-200'
  };
  const icons = { info: 'ℹ️', success: '✅', error: '❌', warning: '⚠️' };

  toast.className = `pointer-events-auto flex items-start gap-3 p-4 rounded-2xl border ${borderColors[type] || borderColors.info} shadow-2xl backdrop-blur-xl transition-all duration-300 transform translate-y-3 opacity-0 text-xs max-w-sm`;
  toast.innerHTML = `
    <span class="text-base select-none">${icons[type] || 'ℹ️'}</span>
    <div class="flex-1">
      ${title ? `<strong class="block font-bold text-white mb-0.5">${title}</strong>` : ''}
      <span class="leading-relaxed opacity-90">${message}</span>
    </div>
    <button class="text-slate-400 hover:text-white font-bold ml-2 select-none" onclick="this.parentElement.remove()">×</button>
  `;

  container.appendChild(toast);
  requestAnimationFrame(() => {
    toast.classList.remove('translate-y-3', 'opacity-0');
  });

  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-3');
    setTimeout(() => toast.remove(), 320);
  }, 4500);
}

function formatNum(n, decimals = 2) {
  if (n == null || isNaN(n)) return '-';
  const num = Number(n);
  if (Math.abs(num) >= 1000) {
    return num.toLocaleString('tr-TR', { maximumFractionDigits: decimals });
  }
  return num.toLocaleString('tr-TR', { minimumFractionDigits: 0, maximumFractionDigits: decimals });
}

function formatPValue(p) {
  if (p == null || isNaN(p)) return '-';
  if (p < 0.0001) return '< 0.0001';
  return p.toFixed(4);
}

// ── SCREEN NAVIGATION ──
function goToUploadScreen() {
  document.getElementById('screenStudio')?.classList.add('hidden');
  document.getElementById('screenUpload')?.classList.remove('hidden');
}

function goToStudioScreen() {
  document.getElementById('screenUpload')?.classList.add('hidden');
  document.getElementById('screenStudio')?.classList.remove('hidden');
  setTimeout(() => {
    if (window.Plotly && document.getElementById('livePlotlyArea')) {
      try { Plotly.Plots.resize('livePlotlyArea'); } catch (e) {}
    }
  }, 100);
}

// ── DATA INGESTION & DATASET SETUP ──
async function handleFileUpload(file) {
  if (!file) return;
  const statusEl = document.getElementById('uploadStatusMsg');
  if (statusEl) {
    statusEl.innerHTML = `<span class="animate-pulse text-cyan-400 font-mono">⏳ <strong>${file.name}</strong> Polars motoruna aktarılıyor...</span>`;
    statusEl.classList.remove('hidden');
  }

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/upload', { method: 'POST', body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Dosya yükleme başarısız.');

    applyDatasetData(data, file.name);
    showToast(`${file.name} başarıyla yüklendi (${data.total_rows.toLocaleString()} satır).`, 'success');
  } catch (err) {
    showToast(err.message, 'error', 'Dosya Yükleme Hatası');
    if (statusEl) statusEl.innerHTML = `<span class="text-rose-400">❌ ${err.message}</span>`;
  }
}

async function loadSampleDataset() {
  const statusEl = document.getElementById('uploadStatusMsg');
  if (statusEl) {
    statusEl.innerHTML = `<span class="animate-pulse text-cyan-400 font-mono">🧠 Akademik örnek veri seti hazırlanıyor...</span>`;
    statusEl.classList.remove('hidden');
  }

  try {
    const res = await fetch('/load_sample', { method: 'POST' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Örnek veri yüklenemedi.');

    applyDatasetData(data, data.file_name || 'Akademik_Ornek_Veri_Seti.xlsx');
    showToast('Örnek akademik veri seti Polars belleğine yüklendi.', 'success');
  } catch (err) {
    showToast(err.message, 'error', 'Örnek Veri Hatası');
    if (statusEl) statusEl.innerHTML = `<span class="text-rose-400">❌ ${err.message}</span>`;
  }
}

function applyDatasetData(data, fileName) {
  state.activeDataset.fileName = fileName || 'Veri_Seti.xlsx';
  state.activeDataset.totalRows = data.total_rows || 0;
  state.activeDataset.totalCols = data.total_cols || 0;
  state.activeDataset.sheetNames = data.sheet_names || [];
  state.activeDataset.activeSheet = data.active_sheet || (data.sheet_names && data.sheet_names[0]) || null;
  state.activeDataset.numericColumns = data.numeric_columns || [];
  state.activeDataset.categoricalColumns = data.categorical_columns || [];
  state.activeDataset.calculatedColumns = [];
  state.activeDataset.joinedColumns = [];

  // Reset axes and filters
  state.axis.x = null;
  state.axis.y = [];
  state.activeFilters = [];

  syncGlobals();
  renderTopbar();
  renderSheetTabs();
  renderActiveFilterChips();
  renderColumnPool();
  initDefaultScenario();
  checkHealthAsync();
  goToStudioScreen();
}

function syncGlobals() {
  window.axisConfig = {
    x: state.axis.x ? state.axis.x.name : null,
    y: state.axis.y.map(i => i.name)
  };
  window.numericColumns = state.activeDataset.numericColumns || [];
  window.categoricalColumns = state.activeDataset.categoricalColumns || [];
  window.currentPalette = state.currentPalette;
  window.activeFilters = state.activeFilters || [];
}

async function checkHealthAsync() {
  try {
    const res = await fetch('/check_health', { cache: 'no-store' });
    const health = await res.json();
    if (res.ok && health.success) {
      state.currentHealth = health;
      updateHealthUI(health);
    }
  } catch (err) {
    console.warn('Veri sağlığı kontrolü uyarısı:', err);
  }
}

function updateHealthUI(health) {
  const statusEl = document.getElementById('topbarAnomalyStatus');
  const healerBadge = document.getElementById('badgeHealerCount');

  const anomalyCount = (health.anomalies && health.anomalies.length) || 0;
  const missingCount = health.missing_cells || 0;
  const totalIssues = anomalyCount + (missingCount > 0 ? 1 : 0);

  if (healerBadge) {
    healerBadge.textContent = totalIssues;
    if (totalIssues > 0) {
      healerBadge.className = 'text-xs px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-mono font-bold border border-rose-500/30';
    } else {
      healerBadge.className = 'text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-mono font-bold border border-emerald-500/30';
    }
  }

  if (statusEl) {
    if (totalIssues > 0) {
      statusEl.className = 'text-amber-400 text-xs flex items-center gap-1.5 font-semibold';
      statusEl.innerHTML = `<span class="w-2 h-2 rounded-full bg-amber-400 live-dot"></span> ${totalIssues} Anomali Tespit Edildi`;
    } else {
      statusEl.className = 'text-emerald-400 text-xs flex items-center gap-1.5 font-semibold';
      statusEl.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-400 live-dot"></span> 0 Anomali / Veri Temiz`;
    }
  }
}

// ── TOPBAR & MULTI-SHEET RENDERING ──
function renderTopbar() {
  const nameEl = document.getElementById('topbarFileName');
  const countEl = document.getElementById('topbarRowCount');
  if (nameEl) nameEl.textContent = state.activeDataset.fileName;
  if (countEl) {
    countEl.textContent = `${state.activeDataset.totalRows.toLocaleString()} Satır • ${getAllColumns().length} Sütun`;
  }
}

function renderSheetTabs() {
  const bar = document.getElementById('multiSheetBar');
  const container = document.getElementById('sheetButtonsContainer');
  if (!bar || !container) return;

  const sheets = state.activeDataset.sheetNames;
  if (!sheets || sheets.length <= 1) {
    bar.classList.add('hidden');
    return;
  }

  bar.classList.remove('hidden');
  container.innerHTML = sheets.map(sheet => {
    const isActive = sheet === state.activeDataset.activeSheet;
    return `
      <button onclick="handleSwitchSheet('${sheet}')" class="px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
        isActive
          ? 'bg-blue-600/30 text-blue-300 border border-blue-500/40'
          : 'bg-white/[0.04] text-slate-400 hover:text-white border border-transparent'
      }">
        ${sheet}
      </button>
    `;
  }).join('');
}

async function handleSwitchSheet(sheetName) {
  try {
    const res = await fetch('/switch_sheet', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sheet_name: sheetName })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    state.activeDataset.activeSheet = sheetName;
    state.activeDataset.totalRows = data.total_rows;
    state.activeDataset.totalCols = data.total_cols;
    state.activeDataset.numericColumns = data.numeric_columns || [];
    state.activeDataset.categoricalColumns = data.categorical_columns || [];
    state.axis.x = null;
    state.axis.y = [];

    renderTopbar();
    renderSheetTabs();
    renderColumnPool();
    initDefaultScenario();
    showToast(`"${sheetName}" sayfasına geçildi.`, 'info');
  } catch (err) {
    showToast(err.message, 'error', 'Sayfa Değiştirilemedi');
  }
}

// ── COLUMN POOL & AXIS ARCHITECT ──
function getAllColumns() {
  const seen = new Set();
  const list = [];
  const add = (col) => {
    if (col && !seen.has(col)) {
      seen.add(col);
      list.push(col);
    }
  };
  (state.activeDataset.categoricalColumns || []).forEach(add);
  (state.activeDataset.numericColumns || []).forEach(add);
  (state.activeDataset.calculatedColumns || []).forEach(add);
  (state.activeDataset.joinedColumns || []).forEach(add);
  return list;
}

function renderColumnPool() {
  const container = document.getElementById('leftColumnsContainer');
  const badge = document.getElementById('colCountBadge');
  if (!container) return;

  const allCols = getAllColumns();
  if (badge) badge.textContent = `${allCols.length} Sütun`;

  const numCount = state.activeDataset.numericColumns.length;
  const catCount = state.activeDataset.categoricalColumns.length;
  const joinedCount = state.activeDataset.joinedColumns.length;

  document.getElementById('btnPoolAll') && (document.getElementById('btnPoolAll').textContent = `Tümü (${allCols.length})`);
  document.getElementById('btnPoolCat') && (document.getElementById('btnPoolCat').textContent = `Metin (${catCount})`);
  document.getElementById('btnPoolNum') && (document.getElementById('btnPoolNum').textContent = `Sayısal (${numCount})`);
  
  const btnJoined = document.getElementById('btnPoolJoined');
  if (btnJoined) {
    if (joinedCount > 0) {
      btnJoined.classList.remove('hidden');
      btnJoined.textContent = `2. Dosya (${joinedCount})`;
    } else {
      btnJoined.classList.add('hidden');
    }
  }

  container.innerHTML = allCols.map(col => {
    const isNum = state.activeDataset.numericColumns.includes(col);
    const isJoined = state.activeDataset.joinedColumns.includes(col);
    const isCalc = state.activeDataset.calculatedColumns.includes(col);
    const colType = isNum ? 'num' : 'cat';

    let pillClass = isNum ? 'pill-num' : 'pill-cat';
    let dotColor = isNum ? 'bg-cyan-400 shadow-cyan-400/50' : 'bg-purple-400 shadow-purple-400/50';
    let typeBadge = isNum ? 'Sayısal' : 'Metin';
    let typeBadgeClass = isNum 
      ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30' 
      : 'bg-purple-500/20 text-purple-300 border-purple-500/30';

    if (isJoined) {
      pillClass = 'pill-joined';
      typeBadge = '🔗 2. Dosya';
      typeBadgeClass = 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
    } else if (isCalc) {
      typeBadge = '🧮 fx';
      typeBadgeClass = 'bg-amber-500/20 text-amber-300 border-amber-500/30';
    }

    return `
      <div class="col-card-item ${colType}-item ${isJoined ? 'joined-item' : ''} p-3 rounded-xl ${pillClass} transition-all group" data-col="${col}" draggable="true" ondragstart="handleDragStart(event, '${col}', '${colType}')">
        <div class="flex items-center justify-between mb-1.5">
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full ${dotColor} shadow-sm"></span>
            <span class="font-bold text-xs text-white">${col}</span>
            <span class="text-[10px] font-semibold px-2 py-0.2 rounded-full border ${typeBadgeClass}">${typeBadge}</span>
          </div>
          <div class="flex items-center gap-1">
            <button onclick="assignAxis('${col}', '${colType}', 'x')" title="X Eksenine Ata" class="px-2 py-1 rounded-md ${isNum ? 'bg-cyan-800 hover:bg-cyan-600 text-cyan-100' : 'bg-purple-600 hover:bg-purple-500 text-white'} text-[11px] font-bold transition-all shadow-sm">+ X</button>
            <button onclick="assignAxis('${col}', '${colType}', 'y')" title="Y Eksenine Ata" class="px-2 py-1 rounded-md ${isNum ? 'bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold' : 'bg-purple-900/60 hover:bg-purple-700 text-purple-200 font-semibold'} text-[11px] transition-all shadow-sm">+ Y</button>
          </div>
        </div>
        <div class="text-[11px] ${isNum ? 'text-cyan-200/70' : 'text-purple-200/70'} font-mono flex items-center justify-between">
          <span>${isNum ? 'Sayısal Metrik' : 'Kategorik Boyut'}</span>
          <span>${isNum ? 'SciPy / Polars' : 'Grup'}</span>
        </div>
      </div>
    `;
  }).join('');
}

function handleDragStart(e, col, type) {
  e.dataTransfer.setData('text/plain', JSON.stringify({ col, type }));
}

function handleDragOver(e) {
  e.preventDefault();
  e.currentTarget.classList.add('border-blue-400', 'bg-blue-900/20');
}

function handleDragLeave(e) {
  e.currentTarget.classList.remove('border-blue-400', 'bg-blue-900/20');
}

function handleDropSlot(e, axis) {
  e.preventDefault();
  e.currentTarget.classList.remove('border-blue-400', 'bg-blue-900/20');
  try {
    const raw = e.dataTransfer.getData('text/plain');
    if (!raw) return;
    const { col, type } = JSON.parse(raw);
    assignAxis(col, type, axis);
  } catch (err) {}
}

function filterLeftColumns() {
  const q = document.getElementById('leftColSearch')?.value.toLowerCase() || '';
  document.querySelectorAll('.col-card-item').forEach(card => {
    card.style.display = card.textContent.toLowerCase().includes(q) ? 'block' : 'none';
  });
}

function setColPoolFilter(type) {
  const btnAll = document.getElementById('btnPoolAll');
  const btnCat = document.getElementById('btnPoolCat');
  const btnNum = document.getElementById('btnPoolNum');
  const btnJoined = document.getElementById('btnPoolJoined');

  [btnAll, btnCat, btnNum, btnJoined].forEach(b => {
    if (b) b.className = "flex-1 py-1 rounded-lg text-slate-400 hover:text-white transition-all";
  });

  const cards = document.querySelectorAll('.col-card-item');

  if (type === 'all') {
    btnAll && (btnAll.className = "flex-1 py-1 rounded-lg font-semibold bg-white/[0.1] text-white transition-all");
    cards.forEach(c => c.style.display = 'block');
  } else if (type === 'cat') {
    btnCat && (btnCat.className = "flex-1 py-1 rounded-lg font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30 transition-all");
    cards.forEach(c => c.style.display = c.classList.contains('cat-item') ? 'block' : 'none');
  } else if (type === 'num') {
    btnNum && (btnNum.className = "flex-1 py-1 rounded-lg font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition-all");
    cards.forEach(c => c.style.display = c.classList.contains('num-item') ? 'block' : 'none');
  } else if (type === 'joined') {
    btnJoined && (btnJoined.className = "flex-1 py-1 rounded-lg font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 transition-all");
    cards.forEach(c => c.style.display = c.classList.contains('joined-item') ? 'block' : 'none');
  }
}

function assignAxis(name, type, axis) {
  if (axis === 'x') {
    state.axis.x = { name, type };
  } else {
    if (!state.axis.y.some(item => item.name === name)) {
      state.axis.y.push({ name, type });
    }
  }
  renderAxisSlotsView();
  evaluateStudioEngine();
}

function removeAxisItemY(name) {
  state.axis.y = state.axis.y.filter(item => item.name !== name);
  renderAxisSlotsView();
  evaluateStudioEngine();
}

function clearSpecificAxis(axis) {
  if (axis === 'x') state.axis.x = null;
  else state.axis.y = [];
  renderAxisSlotsView();
  evaluateStudioEngine();
}

function resetAxisSelection() {
  state.axis.x = null;
  state.axis.y = [];
  renderAxisSlotsView();
  evaluateStudioEngine();
}

function renderAxisSlotsView() {
  const slotX = document.getElementById('slotContainerX');
  const slotY = document.getElementById('slotContainerY');
  const btnDelX = document.getElementById('btnDelX');
  const btnDelY = document.getElementById('btnDelY');

  if (state.axis.x) {
    btnDelX?.classList.remove('hidden');
    const isNum = state.axis.x.type === 'num';
    slotX.innerHTML = `
      <div class="w-full flex items-center justify-between px-3 py-1.5 rounded-xl ${isNum ? 'pill-num' : 'pill-cat'} shadow-sm">
        <span class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full ${isNum ? 'bg-cyan-400' : 'bg-purple-400'}"></span>
          <strong class="text-xs text-white">${state.axis.x.name}</strong>
        </span>
        <button onclick="clearSpecificAxis('x')" class="text-xs text-slate-400 hover:text-rose-400 font-bold ml-2">×</button>
      </div>`;
  } else {
    btnDelX?.classList.add('hidden');
    slotX.innerHTML = `<span class="text-xs text-slate-400 italic">Sütun listesinden <strong class="text-indigo-400">[+ X]</strong> ile seçin</span>`;
  }

  if (state.axis.y.length > 0) {
    btnDelY?.classList.remove('hidden');
    slotY.innerHTML = state.axis.y.map(item => {
      const isNum = item.type === 'num';
      return `
        <div class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl ${isNum ? 'pill-num' : 'pill-cat'} shadow-sm">
          <span class="w-2 h-2 rounded-full ${isNum ? 'bg-cyan-400' : 'bg-purple-400'}"></span>
          <strong class="text-xs text-white">${item.name}</strong>
          <button onclick="removeAxisItemY('${item.name}')" class="text-xs text-slate-400 hover:text-rose-400 font-bold ml-1">×</button>
        </div>`;
    }).join('');
  } else {
    btnDelY?.classList.add('hidden');
    slotY.innerHTML = `<span class="text-xs text-slate-400 italic">Sütun listesinden <strong class="text-cyan-400">[+ Y]</strong> ile seçin</span>`;
  }
}

function initDefaultScenario() {
  const nums = state.activeDataset.numericColumns;
  const cats = state.activeDataset.categoricalColumns;

  if (nums.length >= 2) {
    // 2 Numeric variables -> Regression by default
    state.axis.x = { name: nums[0], type: 'num' };
    state.axis.y = [{ name: nums[1], type: 'num' }];
  } else if (cats.length >= 1 && nums.length >= 1) {
    // 1 Categorical + 1 Numeric -> ANOVA by default
    state.axis.x = { name: cats[0], type: 'cat' };
    state.axis.y = [{ name: nums[0], type: 'num' }];
  } else if (nums.length === 1) {
    state.axis.x = { name: nums[0], type: 'num' };
    state.axis.y = [];
  }
  renderAxisSlotsView();
  evaluateStudioEngine();
}

function applyPresetScenario(type) {
  const nums = state.activeDataset.numericColumns;
  const cats = state.activeDataset.categoricalColumns;

  if (type === 'regression') {
    if (nums.length >= 2) {
      state.axis.x = { name: nums[0], type: 'num' };
      state.axis.y = [{ name: nums[1], type: 'num' }];
    } else if (nums.length === 1) {
      state.axis.x = { name: nums[0], type: 'num' };
      state.axis.y = [{ name: nums[0], type: 'num' }];
    }
  } else if (type === 'anova') {
    if (cats.length >= 1 && nums.length >= 1) {
      state.axis.x = { name: cats[0], type: 'cat' };
      state.axis.y = [{ name: nums[0], type: 'num' }];
    }
  }
  renderAxisSlotsView();
  evaluateStudioEngine();
}

function updateAggFunc() {
  const sel = document.getElementById('aggSelector');
  if (sel) state.aggFunc = sel.value;
  evaluateStudioEngine();
}

// ── ENGINE EVALUATION & AUTO RECOMMENDATION ──
function evaluateStudioEngine() {
  syncGlobals();
  const banner = document.getElementById('statusAutoBanner');
  const badgeStats = document.getElementById('badgeStatsActive');
  const labelX = document.getElementById('heroLabelX');
  const labelY = document.getElementById('heroLabelY');

  if (!state.axis.x || state.axis.y.length === 0) {
    banner?.classList.add('hidden');
    badgeStats?.classList.add('hidden');
    renderPlaceholderStats();
    if (labelX) labelX.textContent = '-';
    if (labelY) labelY.textContent = '-';
    return;
  }

  badgeStats?.classList.remove('hidden');
  const isXNum = state.axis.x.type === 'num';
  const isYNum = state.axis.y.every(item => item.type === 'num');

  if (labelX) labelX.textContent = state.axis.x.name;
  if (labelY) labelY.textContent = state.axis.y.map(i => i.name).join(', ');

  if (isXNum && isYNum) {
    banner?.classList.remove('hidden');
    document.getElementById('statusAutoText') && (document.getElementById('statusAutoText').textContent = "2 Sayısal Değişken • OLS Regresyon Analizi & Scatter Önerildi");
    state.currentPlotType = 'scatter';
    renderRegressionStatsMode('linear');
  } else {
    banner?.classList.remove('hidden');
    document.getElementById('statusAutoText') && (document.getElementById('statusAutoText').textContent = "Metin + Sayısal Değişken • ANOVA Varyans Testi & Sütun Grafiği Önerildi");
    state.currentPlotType = 'bar';
    renderAnovaStatsMode();
  }

  renderActiveHeroChart();
  render50ChartGrid();
  if (state.studioMode === 'pivot') refreshPivotStudio();
  if (state.studioMode === 'dash') renderDashboardStage();
  if (state.studioMode === 'table') refreshTablePreview();
}

// ── 5 STUDIO MODES NAVIGATION ──
function changeStudioMode(mode) {
  state.studioMode = mode;
  const modes = [
    { id: 'btnNavCharts', pane: 'paneCharts', name: 'charts' },
    { id: 'btnNavStats', pane: 'paneStats', name: 'stats' },
    { id: 'btnNavPivot', pane: 'panePivot', name: 'pivot' },
    { id: 'btnNavDash', pane: 'paneDash', name: 'dash' },
    { id: 'btnNavTable', pane: 'paneTable', name: 'table' }
  ];

  modes.forEach(item => {
    const btn = document.getElementById(item.id);
    const pane = document.getElementById(item.pane);
    if (item.name === mode) {
      btn && (btn.className = "px-4 py-2 rounded-xl text-xs font-bold transition-all bg-blue-600 text-white shadow-md shadow-blue-600/30 flex items-center gap-2 shrink-0");
      pane?.classList.remove('hidden');
    } else {
      btn && (btn.className = "px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 hover:text-white hover:bg-white/[0.05] transition-all flex items-center gap-2 shrink-0");
      pane?.classList.add('hidden');
    }
  });

  if (mode === 'charts') {
    setTimeout(() => {
      if (window.Plotly && document.getElementById('livePlotlyArea')) {
        try { Plotly.Plots.resize('livePlotlyArea'); } catch (e) {}
      }
    }, 50);
  } else if (mode === 'pivot') {
    initPivotStudioDefaults();
    refreshPivotStudio();
  } else if (mode === 'dash') {
    renderDashboardStage();
  } else if (mode === 'table') {
    refreshTablePreview();
  }
}

// ── MODE 1: 50 PLOTLY CHARTS STUDIO ──
async function renderActiveHeroChart() {
  const plotlyContainer = document.getElementById('livePlotlyArea');
  const titleEl = document.getElementById('heroDisplayTitle');
  const tagEl = document.getElementById('heroDisplayTag');
  const subEl = document.getElementById('heroDisplaySubtitle');
  const eqBadge = document.getElementById('canvasEquationBadge');

  if (!plotlyContainer) return;

  if (!state.axis.x && state.axis.y.length === 0) {
    plotlyContainer.innerHTML = `
      <div class="h-full flex flex-col items-center justify-center text-slate-500 space-y-3">
        <span class="text-4xl">📊</span>
        <p class="text-xs">Sol panelden X ve Y değişkenlerini seçin.</p>
      </div>`;
    eqBadge?.classList.add('hidden');
    return;
  }

  const xCol = state.axis.x ? state.axis.x.name : null;
  const yCols = state.axis.y.map(i => i.name);
  const chartType = state.currentPlotType || 'bar';

  if (titleEl) titleEl.textContent = `${xCol || ''} ${yCols.length ? '& ' + yCols.join(', ') : ''} ${chartType.toUpperCase()} Analizi`;
  if (subEl) subEl.textContent = `X: ${xCol || 'Tümü'} • Y: ${yCols.join(', ') || 'Frekans'} • ${state.activeDataset.totalRows.toLocaleString()} Satır`;

  // Fetch chart data from backend
  try {
    const res = await fetch('/get_chart_data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chart_type: chartType,
        x_col: xCol,
        y_cols: yCols,
        agg_func: state.aggFunc,
        filters: state.activeFilters
      })
    });
    const chartData = await res.json();
    if (!res.ok) throw new Error(chartData.error || 'Grafik verisi alınamadı.');

    state.currentChartData = chartData;

    // Call drawMegaPlotly from charts_config.js or fallback to direct Plotly rendering
    if (typeof window.drawMegaPlotly === 'function') {
      await window.drawMegaPlotly('livePlotlyArea', chartData, chartType);
    } else {
      await fallbackPlotlyDraw('livePlotlyArea', chartData, chartType, xCol, yCols);
    }

    // Fetch regression curve if 2 numeric variables
    if (state.axis.x?.type === 'num' && state.axis.y[0]?.type === 'num') {
      fetchAndRenderRegressionBadge(xCol, state.axis.y[0].name);
    } else {
      eqBadge?.classList.add('hidden');
    }

    // Update ticker metrics
    updateChartTickerMetrics(chartData);

  } catch (err) {
    plotlyContainer.innerHTML = `<div class="h-full flex items-center justify-center text-rose-400 text-xs">⚠️ Grafik Çizim Hatası: ${err.message}</div>`;
  }
}

async function fetchAndRenderRegressionBadge(xCol, yCol) {
  const eqBadge = document.getElementById('canvasEquationBadge');
  try {
    const res = await fetch('/get_regression_curve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        x_col: xCol,
        y_col: yCol,
        model_type: 'linear',
        corr_method: 'pearson',
        filters: state.activeFilters
      })
    });
    const regData = await res.json();
    if (res.ok && regData.success) {
      state.currentRegression = regData;
      eqBadge?.classList.remove('hidden');
      const bForm = document.getElementById('badgeFormula');
      const bR2 = document.getElementById('badgeR2');
      const bCorr = document.getElementById('badgeCorr');

      if (bForm) bForm.textContent = regData.regression?.equation || 'y = mx + c';
      if (bR2) bR2.textContent = `R² = ${regData.regression?.r_squared?.toFixed(4) || '-'}`;
      if (bCorr) bCorr.textContent = `r = ${regData.correlation?.r?.toFixed(4) || '-'}`;

      // Also update ticker metrics
      document.getElementById('tickerR') && (document.getElementById('tickerR').textContent = `r = ${regData.correlation?.r?.toFixed(3) || '-'}`);
      document.getElementById('tickerR2') && (document.getElementById('tickerR2').textContent = `R² = %${((regData.regression?.r_squared || 0) * 100).toFixed(1)}`);
      document.getElementById('tickerP') && (document.getElementById('tickerP').textContent = regData.regression?.p_value < 0.001 ? 'p < 0.001' : `p = ${regData.regression?.p_value?.toFixed(3)}`);
    } else {
      eqBadge?.classList.add('hidden');
    }
  } catch (e) {
    eqBadge?.classList.add('hidden');
  }
}

function updateChartTickerMetrics(chartData) {
  const rowCount = chartData.total_active_rows || state.activeDataset.totalRows;
  document.getElementById('tickerCount') && (document.getElementById('tickerCount').textContent = `${rowCount.toLocaleString()} Nokta`);
}

async function fallbackPlotlyDraw(targetId, data, type, xCol, yCols) {
  const el = document.getElementById(targetId);
  if (!el || !window.Plotly) return;

  const traces = [];
  const palette = [state.currentPalette, '#818cf8', '#34d399', '#fbbf24', '#f43f5e', '#a78bfa'];

  if (data.raw) {
    const raw = data.raw;
    const xVals = raw['__x__'] || [];
    yCols.forEach((y, i) => {
      traces.push({
        x: xVals,
        y: raw[y] || [],
        type: (type === 'scatter' || type === 'bubble') ? 'scatter' : (type === 'box' ? 'box' : 'bar'),
        mode: type === 'line' ? 'lines' : 'markers',
        marker: { color: palette[i % palette.length], size: 7 },
        name: y
      });
    });
  } else if (data.agg) {
    const agg = data.agg;
    const xVals = agg['__x__'] || [];
    yCols.forEach((y, i) => {
      traces.push({
        x: xVals,
        y: agg[y] || [],
        type: type === 'line' ? 'scatter' : (type === 'pie' || type === 'donut' ? 'pie' : 'bar'),
        mode: type === 'line' ? 'lines+markers' : undefined,
        hole: type === 'donut' ? 0.5 : undefined,
        marker: { color: palette[i % palette.length] },
        name: y
      });
    });
  }

  const layout = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: { family: 'Inter, sans-serif', color: '#94a3b8' },
    margin: { t: 25, r: 25, b: 45, l: 45 },
    xaxis: { gridcolor: 'rgba(255,255,255,0.06)', zeroline: false },
    yaxis: { gridcolor: 'rgba(255,255,255,0.06)', zeroline: false }
  };

  await Plotly.newPlot(targetId, traces, layout, { responsive: true, displayModeBar: false });
}

function render50ChartGrid(familyFilter = 'all') {
  const container = document.getElementById('chartGalleryGrid');
  if (!container) return;

  const chartList = window.CHARTS || [
    { id: 'scatter', name: 'Scatter & Regresyon', cat: 'rel', icon: '🔵', desc: 'Doğrusal trend ve saçılım' },
    { id: 'bar', name: 'Sütun Grafiği', cat: 'comp', icon: '📊', desc: 'Kategorik toplam ve ortalama' },
    { id: 'line', name: 'Çizgi Grafiği', cat: 'trend', icon: '📈', desc: 'Zaman ve periyot trendi' },
    { id: 'box', name: 'Kutu (Box Plot)', cat: 'dist', icon: '📦', desc: 'Varyans & çeyreklikler' },
    { id: 'donut', name: 'Halka (Donut)', cat: 'part', icon: '⭕', desc: 'Yüzdesel oran dağılımı' },
    { id: 'heatmap', name: 'Isı Haritası', cat: 'rel', icon: '🌡️', desc: 'Korelasyon matrisi' },
    { id: 'area', name: 'Alan Grafiği', cat: 'trend', icon: '🌊', desc: 'Kümülatif hacim trendi' },
    { id: 'violin', name: 'Keman (Violin)', cat: 'dist', icon: '🎻', desc: 'Yoğunluk ve kutu dağılımı' }
  ];

  const isXNum = state.axis.x?.type === 'num';
  const isYNum = state.axis.y[0]?.type === 'num';

  container.innerHTML = chartList.map(ch => {
    if (familyFilter !== 'all' && ch.cat !== familyFilter) return '';

    let matchTag = '%85 UYUM';
    let matchClass = 'bg-white/[0.06] text-slate-300 border-white/[0.1]';

    if (isXNum && isYNum && (ch.id === 'scatter' || ch.id === 'line')) {
      matchTag = '%98 UYUM';
      matchClass = 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
    } else if (!isXNum && isYNum && (ch.id === 'bar' || ch.id === 'box')) {
      matchTag = '%95 UYUM';
      matchClass = 'bg-purple-500/20 text-purple-300 border-purple-500/30';
    }

    const isActive = state.currentPlotType === ch.id;

    return `
      <div onclick="selectChartKind('${ch.id}')" class="pro-card rounded-2xl p-4 cursor-pointer transition-all ${
        isActive ? 'border-blue-500/70 bg-[#16202e] shadow-lg shadow-blue-500/10' : ''
      }">
        <div class="flex justify-between items-start mb-2">
          <div class="flex items-center gap-2">
            <span class="text-base">${ch.icon}</span>
            <strong class="text-xs font-bold text-white">${ch.name}</strong>
          </div>
          <span class="text-[10px] font-mono px-2 py-0.5 rounded-full border ${matchClass} font-bold">${matchTag}</span>
        </div>
        <p class="text-[11px] text-slate-400 mt-1 leading-relaxed">${ch.desc}</p>
      </div>
    `;
  }).join('');
}

function selectChartKind(kind) {
  state.currentPlotType = kind;
  renderActiveHeroChart();
  render50ChartGrid();
}

function filterChartFamily(fam) {
  const filterContainer = document.getElementById('chartFamilyFilters');
  if (filterContainer) {
    filterContainer.querySelectorAll('button').forEach(btn => {
      const isMatch = btn.getAttribute('data-family') === fam || (fam === 'all' && btn.getAttribute('data-family') === 'all');
      if (isMatch) {
        btn.className = "px-3 py-1 rounded-lg bg-blue-600 text-white shadow-sm font-semibold";
      } else {
        btn.className = "px-3 py-1 rounded-lg text-slate-400 hover:text-white font-semibold transition-all";
      }
    });
  }
  render50ChartGrid(fam);
}

function setGlobalPalette(hex) {
  state.currentPalette = hex;
  syncGlobals();
  renderActiveHeroChart();
}

// ── PINNING TO EXECUTIVE DASHBOARD ──
function pinCurrentChartToDashboard() {
  const title = document.getElementById('heroDisplayTitle')?.textContent || 'Grafik';
  const subtitle = document.getElementById('heroDisplaySubtitle')?.textContent || '';
  const xCol = state.axis.x?.name || '';
  const yCol = state.axis.y.map(i => i.name).join(', ') || '';
  const chartType = state.currentPlotType;
  const dataClone = JSON.parse(JSON.stringify(state.currentChartData || {}));

  const pinId = 'pin_' + Date.now();
  state.pinnedCharts.unshift({
    id: pinId,
    title,
    subtitle,
    xCol,
    yCol,
    chartType,
    data: dataClone,
    pinnedAt: new Date().toLocaleTimeString('tr-TR')
  });

  const badge = document.getElementById('dashBadgeNumber');
  if (badge) badge.textContent = state.pinnedCharts.length;

  showToast('Grafik Özel Gösterge Panosuna başarıyla sabitlendi!', 'success', 'Pano Güncellendi');
}

// ── MODE 2: STATS & HYPOTHESIS LAB ──
async function renderRegressionStatsMode(model = 'linear', corrMethod = 'pearson') {
  const container = document.getElementById('statsMainContainer');
  if (!container) return;

  const xName = state.axis.x?.name || 'X Değişkeni';
  const yName = state.axis.y[0]?.name || 'Y Değişkeni';

  state.currentRegModel = model;
  state.currentCorrMethod = corrMethod;

  container.innerHTML = `
    <div class="rounded-3xl bg-[#131b26] border border-cyan-500/30 p-8 space-y-6 shadow-2xl">
      <div class="flex flex-wrap items-center justify-between border-b border-white/[0.08] pb-4 gap-4">
        <div>
          <div class="flex items-center gap-2.5">
            <span class="w-8 h-8 rounded-xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold text-base">🔬</span>
            <h3 class="text-base font-bold text-white tracking-tight">Korelasyon &amp; Çoklu Regresyon Modeli</h3>
          </div>
          <p class="text-xs text-slate-400 mt-1">Bağımsız (X): <strong class="text-white">${xName}</strong> • Bağımlı (Y): <strong class="text-white">${yName}</strong></p>
        </div>
        <span class="text-xs font-mono font-bold px-3 py-1 rounded-full pill-num">2 Sayısal Değişken</span>
      </div>

      <!-- Model & Correlation Switchers -->
      <div class="flex flex-wrap items-center justify-between gap-4 bg-[#0b0f17] p-3 rounded-2xl border border-white/[0.08]">
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-xs font-bold text-slate-300">Regresyon Modeli:</span>
          <div class="flex flex-wrap bg-[#141b26] p-1 rounded-xl border border-white/[0.08] gap-1">
            <button onclick="renderRegressionStatsMode('linear', '${corrMethod}')" class="px-3 py-1 rounded-lg text-xs font-bold transition-all ${model === 'linear' ? 'bg-cyan-500 text-slate-950 shadow' : 'text-slate-400 hover:text-white'}">Doğrusal (Linear)</button>
            <button onclick="renderRegressionStatsMode('poly2', '${corrMethod}')" class="px-3 py-1 rounded-lg text-xs font-bold transition-all ${model === 'poly2' ? 'bg-cyan-500 text-slate-950 shadow' : 'text-slate-400 hover:text-white'}">Polinom (Derece 2)</button>
            <button onclick="renderRegressionStatsMode('poly3', '${corrMethod}')" class="px-3 py-1 rounded-lg text-xs font-bold transition-all ${model === 'poly3' ? 'bg-cyan-500 text-slate-950 shadow' : 'text-slate-400 hover:text-white'}">Polinom (Derece 3)</button>
            <button onclick="renderRegressionStatsMode('exp', '${corrMethod}')" class="px-3 py-1 rounded-lg text-xs font-bold transition-all ${model === 'exp' ? 'bg-cyan-500 text-slate-950 shadow' : 'text-slate-400 hover:text-white'}">Üstel (Exp)</button>
            <button onclick="renderRegressionStatsMode('log', '${corrMethod}')" class="px-3 py-1 rounded-lg text-xs font-bold transition-all ${model === 'log' ? 'bg-cyan-500 text-slate-950 shadow' : 'text-slate-400 hover:text-white'}">Logaritmik</button>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <span class="text-xs font-bold text-slate-300">Korelasyon Türü:</span>
          <div class="flex bg-[#141b26] p-1 rounded-xl border border-white/[0.08] gap-1">
            <button onclick="renderRegressionStatsMode('${model}', 'pearson')" class="px-3 py-1 rounded-lg text-xs font-bold transition-all ${corrMethod === 'pearson' ? 'bg-indigo-500 text-white shadow' : 'text-slate-400 hover:text-white'}">Pearson</button>
            <button onclick="renderRegressionStatsMode('${model}', 'spearman')" class="px-3 py-1 rounded-lg text-xs font-bold transition-all ${corrMethod === 'spearman' ? 'bg-indigo-500 text-white shadow' : 'text-slate-400 hover:text-white'}">Spearman</button>
            <button onclick="renderRegressionStatsMode('${model}', 'kendall')" class="px-3 py-1 rounded-lg text-xs font-bold transition-all ${corrMethod === 'kendall' ? 'bg-indigo-500 text-white shadow' : 'text-slate-400 hover:text-white'}">Kendall Tau</button>
          </div>
        </div>
      </div>

      <!-- 4 Scientific Metrics Cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4" id="statsSciCards">
        <div class="p-4 rounded-2xl bg-[#0b0f17] border border-white/[0.08]">
          <span class="text-xs text-slate-400 block mb-1" id="statCardRLabel">${corrMethod === 'spearman' ? 'Spearman (ρ)' : (corrMethod === 'kendall' ? 'Kendall (τ)' : 'Pearson Korelasyon (r)')}</span>
          <strong class="text-2xl font-bold text-cyan-400 font-mono tracking-tight" id="statCardR">-</strong>
          <span class="text-xs text-cyan-300/80 block mt-1" id="statCardRInterp">Hesaplanıyor...</span>
        </div>
        <div class="p-4 rounded-2xl bg-[#0b0f17] border border-white/[0.08]">
          <span class="text-xs text-slate-400 block mb-1">Belirlilik Katsayısı (R²)</span>
          <strong class="text-2xl font-bold text-emerald-400 font-mono tracking-tight" id="statCardR2">-</strong>
          <span class="text-xs text-emerald-300/80 block mt-1" id="statCardR2Interp">Varyans Açıklaması</span>
        </div>
        <div class="p-4 rounded-2xl bg-[#0b0f17] border border-white/[0.08]">
          <span class="text-xs text-slate-400 block mb-1">P Değeri (Anlamlılık)</span>
          <strong class="text-2xl font-bold text-amber-400 font-mono tracking-tight" id="statCardP">-</strong>
          <span class="text-xs block mt-1 font-semibold" id="statCardPSig">-</span>
        </div>
        <div class="p-4 rounded-2xl bg-[#0b0f17] border border-white/[0.08]">
          <span class="text-xs text-slate-400 block mb-1">Model Denklemi</span>
          <strong class="text-sm font-bold text-amber-300 font-mono block mt-2 truncate" id="statCardEq">-</strong>
        </div>
      </div>

      <!-- Academic AI Insight Generator Section -->
      <div class="p-5 rounded-2xl bg-[#0b0f17] border border-white/[0.08] space-y-3">
        <div class="flex items-center justify-between">
          <span class="font-bold text-white text-xs flex items-center gap-2">
            <span>🧠</span>
            <span>Akademik İstatistiksel Yorumlayıcı</span>
          </span>
          <button onclick="triggerAiInsight()" id="btnGenerateAi" class="px-3.5 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs transition-all shadow">
            Veriyi Yorumla
          </button>
        </div>
        <div id="aiInsightBox" class="p-4 rounded-xl bg-purple-950/20 border border-purple-500/20 text-xs text-slate-200 leading-relaxed space-y-1">
          <strong class="text-purple-300 block font-bold">💼 Yönetici &amp; Akademik Karar Özeti:</strong>
          <p id="aiInsightSummaryText"><strong>${xName}</strong> ve <strong>${yName}</strong> değişkenleri arasında korelasyon ve ${model} regresyon analizi SciPy motoru ile çözümleniyor...</p>
        </div>
      </div>

      <button onclick="changeStudioMode('charts'); selectChartKind('scatter');" class="w-full py-3.5 rounded-2xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-extrabold text-xs tracking-wide shadow-xl flex items-center justify-center gap-2">
        <span>📈</span>
        <span>Bu Regresyon Dağılım Grafiğini Canlı İncele →</span>
      </button>
    </div>`;

  // Fetch both regression and descriptive stats
  try {
    const [regRes, statsRes] = await Promise.all([
      fetch('/get_regression_curve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          x_col: xName,
          y_col: yName,
          model_type: model,
          corr_method: corrMethod,
          filters: state.activeFilters
        })
      }),
      fetch('/get_stats', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          columns: [yName, xName],
          x_col: xName,
          filters: state.activeFilters
        })
      })
    ]);

    const regData = await regRes.json();
    const statsData = await statsRes.json();

    if (statsRes.ok) {
      state.currentStats = statsData.stats || {};
      state.currentAdvanced = statsData.advanced || {};
    }

    if (regRes.ok && regData.success) {
      state.currentRegression = regData;

      const coef = regData.correlation?.r;
      const r2 = regData.regression?.r_squared;
      const pVal = regData.regression?.p_value != null ? regData.regression.p_value : regData.correlation?.p_value;
      const eq = regData.regression?.equation || '-';
      const interp = regData.correlation?.interpretation || (coef > 0.6 ? 'Güçlü İlişki' : (coef > 0.3 ? 'Orta Düzey İlişki' : 'Düşük İlişki'));

      document.getElementById('statCardR') && (document.getElementById('statCardR').textContent = coef != null ? coef.toFixed(4) : '-');
      document.getElementById('statCardRInterp') && (document.getElementById('statCardRInterp').textContent = interp);
      document.getElementById('statCardR2') && (document.getElementById('statCardR2').textContent = r2 != null ? r2.toFixed(4) : '-');
      document.getElementById('statCardR2Interp') && (document.getElementById('statCardR2Interp').textContent = r2 != null ? `%${(r2 * 100).toFixed(1)} Açıklanan Varyans` : '-');
      document.getElementById('statCardP') && (document.getElementById('statCardP').textContent = formatPValue(pVal));
      
      const sigEl = document.getElementById('statCardPSig');
      if (sigEl) {
        if (pVal != null && pVal < 0.05) {
          sigEl.className = 'text-xs text-emerald-400 block mt-1 font-semibold';
          sigEl.textContent = 'İstatistiksel Anlamlı (p < 0.05)';
        } else if (pVal != null) {
          sigEl.className = 'text-xs text-amber-400 block mt-1 font-semibold';
          sigEl.textContent = 'Anlamlı Değil (p ≥ 0.05)';
        } else {
          sigEl.className = 'text-xs text-slate-400 block mt-1 font-semibold';
          sigEl.textContent = '-';
        }
      }

      document.getElementById('statCardEq') && (document.getElementById('statCardEq').textContent = eq);

      const summaryText = document.getElementById('aiInsightSummaryText');
      if (summaryText) {
        summaryText.innerHTML = `<strong>${xName}</strong> ve <strong>${yName}</strong> değişkenleri arasında <strong>${corrMethod.toUpperCase()}</strong> korelasyonu <strong>${coef != null ? coef.toFixed(4) : '-'}</strong> (${interp}) olarak hesaplanmıştır. <strong>${eq}</strong> modeli varyansın <strong>%${r2 != null ? (r2 * 100).toFixed(1) : 0}</strong>'sini açıklamaktadır (${pVal != null && pVal < 0.05 ? 'Anlamlı' : 'Örneklem yetersiz veya anlamsız'}).`;
      }
    }
  } catch (e) {
    console.warn('Regresyon istatistik hesaplama hatası:', e);
  }
}

async function renderAnovaStatsMode() {
  const container = document.getElementById('statsMainContainer');
  if (!container) return;

  const xName = state.axis.x?.name || 'Grup';
  const yName = state.axis.y[0]?.name || 'Metrik';

  container.innerHTML = `
    <div class="rounded-3xl bg-[#131b26] border border-purple-500/30 p-8 space-y-6 shadow-2xl">
      <div class="flex flex-wrap items-center justify-between border-b border-white/[0.08] pb-4 gap-4">
        <div>
          <div class="flex items-center gap-2.5">
            <span class="w-8 h-8 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold text-base">🧪</span>
            <h3 class="text-base font-bold text-white tracking-tight" id="statAnovaHeaderTitle">Hipotez ve Varyans Karşılaştırma Testi</h3>
          </div>
          <p class="text-xs text-slate-400 mt-1">Grup (X): <strong class="text-white">${xName}</strong> • Ölçülen Metrik (Y): <strong class="text-white">${yName}</strong></p>
        </div>
        <span class="text-xs font-mono font-bold px-3 py-1 rounded-full pill-cat" id="statAnovaBadge">Gruplar Arası Hipotez Testi</span>
      </div>

      <!-- 4 Scientific Metrics Cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="p-4 rounded-2xl bg-[#0b0f17] border border-white/[0.08]">
          <span class="text-xs text-slate-400 block mb-1" id="statTestStatLabel">Test İstatistiği</span>
          <strong class="text-2xl font-bold text-cyan-400 font-mono tracking-tight" id="statAnovaF">-</strong>
          <span class="text-xs text-cyan-300/80 block mt-1" id="statTestStatSub">Gruplar Arası Fark</span>
        </div>
        <div class="p-4 rounded-2xl bg-[#0b0f17] border border-white/[0.08]">
          <span class="text-xs text-slate-400 block mb-1">P Değeri</span>
          <strong class="text-2xl font-bold text-emerald-400 font-mono tracking-tight" id="statAnovaP">-</strong>
          <span class="text-xs block mt-1 font-semibold" id="statAnovaSig">-</span>
        </div>
        <div class="p-4 rounded-2xl bg-[#0b0f17] border border-white/[0.08]">
          <span class="text-xs text-slate-400 block mb-1" id="statBestLabel">🏆 En Başarılı Grup</span>
          <strong class="text-base font-bold text-emerald-400 block mt-1 truncate" id="statAnovaBest">-</strong>
          <span class="text-xs text-slate-400 block" id="statAnovaBestVal">Ortalama</span>
        </div>
        <div class="p-4 rounded-2xl bg-[#0b0f17] border border-white/[0.08]">
          <span class="text-xs text-slate-400 block mb-1" id="statLowLabel">⚠️ En Düşük Grup</span>
          <strong class="text-base font-bold text-rose-400 block mt-1 truncate" id="statAnovaLow">-</strong>
          <span class="text-xs text-slate-400 block" id="statAnovaLowVal">Ortalama</span>
        </div>
      </div>

      <div class="p-5 rounded-2xl bg-[#0b0f17] border border-white/[0.08] space-y-3">
        <div class="flex items-center justify-between">
          <span class="font-bold text-white text-xs flex items-center gap-2">
            <span>🧠</span>
            <span>Akademik İstatistiksel Yorumlayıcı</span>
          </span>
          <button onclick="triggerAiInsight()" id="btnGenerateAi" class="px-3.5 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs transition-all shadow">
            Veriyi Yorumla
          </button>
        </div>
        <div id="aiInsightBox" class="p-4 rounded-xl bg-purple-950/20 border border-purple-500/20 text-xs text-slate-200 leading-relaxed space-y-1">
          <strong class="text-purple-300 block font-bold text-sm">💼 Yönetici &amp; Akademik Karar Özeti:</strong>
          <p id="statAnovaVerdict"><strong>${xName}</strong> kategorileri arasında <strong>${yName}</strong> ortalamaları bakımından istatistiksel hipotez testi SciPy motoruyla hesaplanıyor...</p>
        </div>
      </div>

      <button onclick="changeStudioMode('charts'); selectChartKind('bar');" class="w-full py-3.5 rounded-2xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-extrabold text-xs tracking-wide shadow-xl flex items-center justify-center gap-2">
        <span>📊</span>
        <span>Bu Karşılaştırma Grafiğini Canlı İncele →</span>
      </button>
    </div>`;

  try {
    const res = await fetch('/get_stats', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        columns: [yName],
        x_col: xName,
        filters: state.activeFilters
      })
    });
    const sData = await res.json();
    if (res.ok) {
      state.currentStats = sData.stats || {};
      const adv = sData.advanced || {};
      state.currentAdvanced = adv;

      const isTwoGroup = adv.type === 'categorical_2' || adv.t_test != null;
      const tTest = adv.t_test;
      const anova = adv.anova;

      const pVal = isTwoGroup ? (tTest?.p_value != null ? tTest.p_value : adv.p_value) : (anova?.p_value != null ? anova.p_value : adv.p_value);
      const isSignificant = pVal != null && pVal < 0.05;

      const titleEl = document.getElementById('statAnovaHeaderTitle');
      const badgeEl = document.getElementById('statAnovaBadge');
      const testStatLabel = document.getElementById('statTestStatLabel');
      const testStatSub = document.getElementById('statTestStatSub');
      const fEl = document.getElementById('statAnovaF');
      const pEl = document.getElementById('statAnovaP');
      const sigEl = document.getElementById('statAnovaSig');
      const bestEl = document.getElementById('statAnovaBest');
      const bestValEl = document.getElementById('statAnovaBestVal');
      const lowEl = document.getElementById('statAnovaLow');
      const lowValEl = document.getElementById('statAnovaLowVal');
      const bestLabel = document.getElementById('statBestLabel');
      const lowLabel = document.getElementById('statLowLabel');
      const verdict = document.getElementById('statAnovaVerdict');

      if (isTwoGroup) {
        if (titleEl) titleEl.textContent = "Bağımsız İki Örneklem T-Testi (Student's t-test)";
        if (badgeEl) badgeEl.textContent = "2 Grup Kıyaslaması (t-test)";
        if (testStatLabel) testStatLabel.textContent = "t İstatistiği";
        if (testStatSub) testStatSub.textContent = "Student t Değeri";

        const tStat = tTest?.t_stat != null ? tTest.t_stat : adv.t_test_stat;
        if (fEl) fEl.textContent = tStat != null ? tStat.toFixed(4) : '-';
        if (pEl) pEl.textContent = formatPValue(pVal);

        const groupMeans = (tTest && tTest.group_means) ? tTest.group_means : (adv.group_means || {});
        const groups = Object.keys(groupMeans);

        if (groups.length >= 2) {
          if (bestLabel) bestLabel.textContent = `Grup 1: ${groups[0]}`;
          if (bestEl) bestEl.textContent = formatNum(groupMeans[groups[0]]);
          if (bestValEl) bestValEl.textContent = "Grup Ortalaması";

          if (lowLabel) lowLabel.textContent = `Grup 2: ${groups[1]}`;
          if (lowEl) lowEl.textContent = formatNum(groupMeans[groups[1]]);
          if (lowValEl) lowValEl.textContent = "Grup Ortalaması";
        }

        if (sigEl) {
          sigEl.className = isSignificant ? 'text-xs text-emerald-400 block mt-1 font-semibold' : 'text-xs text-amber-400 block mt-1 font-semibold';
          sigEl.textContent = isSignificant ? 'Fark Anlamlı (p < 0.05)' : 'Fark Anlamsız (p ≥ 0.05)';
        }

        if (verdict) {
          if (isSignificant) {
            verdict.innerHTML = `<strong>${xName}</strong>'in 2 grubu arasında <strong>${yName}</strong> ortalamaları bakımından p &lt; 0.05 düzeyinde istatistiksel açıdan anlamlı bir fark bulunmuştur (t = ${tStat != null ? tStat.toFixed(3) : '-'}, p = ${formatPValue(pVal)}). H₀ hipotezi reddedilmiştir; gruplar arasındaki fark şansa bağlı değildir.`;
          } else {
            verdict.innerHTML = `<strong>${xName}</strong>'in 2 grubu arasında <strong>${yName}</strong> ortalamaları bakımından istatistiksel olarak anlamlı bir fark saptanmamıştır (p = ${formatPValue(pVal)} ≥ 0.05). H₀ hipotezi kabul edilmiştir.`;
          }
        }

      } else {
        if (titleEl) titleEl.textContent = "Tek Yönlü Varyans Analizi (One-Way ANOVA)";
        if (badgeEl) badgeEl.textContent = "Çoklu Grup Varyans Testi";
        if (testStatLabel) testStatLabel.textContent = "F İstatistiği";
        if (testStatSub) testStatSub.textContent = "Gruplar Arası / İçi Varyans";

        const fStat = anova?.f_stat != null ? anova.f_stat : adv.anova_f;
        if (fEl) fEl.textContent = fStat != null ? fStat.toFixed(4) : '-';
        if (pEl) pEl.textContent = formatPValue(pVal);

        if (sigEl) {
          sigEl.className = isSignificant ? 'text-xs text-emerald-400 block mt-1 font-semibold' : 'text-xs text-amber-400 block mt-1 font-semibold';
          sigEl.textContent = isSignificant ? 'Varyans Farkı Anlamlı' : 'Varyans Farkı Anlamsız';
        }

        const bestG = adv.anova_best_group || adv.best_group || '-';
        const lowG = adv.anova_low_group || adv.worst_group || '-';
        if (bestEl) bestEl.textContent = bestG;
        if (bestValEl) bestValEl.textContent = adv.best_val != null ? `Toplam: ${formatNum(adv.best_val)}` : 'En Yüksek';
        if (lowEl) lowEl.textContent = lowG;
        if (lowValEl) lowValEl.textContent = adv.worst_val != null ? `Toplam: ${formatNum(adv.worst_val)}` : 'En Düşük';

        if (verdict) {
          if (isSignificant) {
            verdict.innerHTML = `<strong>${xName}</strong> kategorileri arasında <strong>${yName}</strong> ortalamaları bakımından p &lt; 0.05 düzeyinde istatistiksel açıdan anlamlı bir varyans farkı saptanmıştır (F = ${fStat != null ? fStat.toFixed(2) : '-'}, p = ${formatPValue(pVal)}). Gruplar arası fark şansa bağlı değildir.`;
          } else {
            verdict.innerHTML = `<strong>${xName}</strong> kategorileri arasında <strong>${yName}</strong> ortalamaları bakımından varyans farkı istatistiksel olarak anlamlı değildir (p = ${formatPValue(pVal)} ≥ 0.05). H₀ hipotezi korunmaktadır.`;
          }
        }
      }
    }
  } catch (e) {
    console.warn('ANOVA istatistik çekme hatası:', e);
  }
}

function renderPlaceholderStats() {
  const container = document.getElementById('statsMainContainer');
  if (!container) return;
  container.innerHTML = `
    <div class="rounded-3xl bg-[#131b26] border border-white/[0.08] p-12 text-center text-slate-400 max-w-lg mx-auto space-y-3">
      <span class="text-4xl block text-blue-400">🔬</span>
      <h4 class="text-base font-bold text-white">Değişken Seçimi Bekleniyor</h4>
      <p class="text-xs leading-relaxed">Sol sütun listesinden değişkenleri <strong class="text-indigo-300">[+ X]</strong> ve <strong class="text-cyan-300">[+ Y]</strong> butonlarıyla seçtiğinizde, Regresyon veya ANOVA analizleri burada anında görüntülenecektir.</p>
    </div>`;
}

async function triggerAiInsight() {
  const box = document.getElementById('aiInsightBox');
  if (!box) return;

  box.innerHTML = `<span class="text-cyan-400 animate-pulse font-mono">🧠 SciPy ve Akademik LLM Yorumlayıcı analizi derinleştiriyor...</span>`;

  const xCol = state.axis.x?.name;
  const yCol = state.axis.y[0]?.name;

  try {
    const res = await fetch('/get_ai_insight', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chart_type: state.currentPlotType,
        x: xCol,
        y: [yCol],
        stats: state.currentStats || {},
        advanced_stats: state.currentAdvanced || state.currentRegression || {}
      })
    });
    const data = await res.json();
    const insightText = data.insight || 'Akademik analiz tamamlandı.';

    box.innerHTML = `
      <strong class="text-emerald-400 block font-bold text-sm">🎓 Akademik Hakem &amp; Uzman Analist Yorumu:</strong>
      <p class="text-xs text-slate-200 mt-1 leading-relaxed whitespace-pre-line">${insightText}</p>
    `;
  } catch (e) {
    box.innerHTML = `
      <strong class="text-emerald-400 block font-bold text-sm">🎓 Akademik Hakem &amp; Uzman Analist Yorumu:</strong>
      <p class="text-xs text-slate-200 mt-1 leading-relaxed">${xCol} ve ${yCol} arasındaki istatistiksel ilişki incelenmiş olup, parametrik testler ve varyans analizi başarıyla tamamlanmıştır.</p>
    `;
  }
}

// ── MODE 3: DYNAMIC PIVOT STUDIO ──
function initPivotStudioDefaults() {
  const cats = state.activeDataset.categoricalColumns;
  const nums = state.activeDataset.numericColumns;

  if (state.pivotConfig.rows.length === 0 && cats.length > 0) {
    state.pivotConfig.rows = [cats[0]];
  }
  if (state.pivotConfig.cols.length === 0 && cats.length > 1) {
    state.pivotConfig.cols = [cats[1]];
  }
  if (state.pivotConfig.values.length === 0 && nums.length > 0) {
    state.pivotConfig.values = [nums[0]];
  }

  const sel = document.getElementById('pivotAggFuncSelect');
  if (sel) sel.value = state.pivotConfig.agg_func || 'sum';

  // Populate row/col/val select dropzones
  renderPivotControls();
}

function addPivotItem(type, name) {
  if (!name) return;
  if (!state.pivotConfig[type].includes(name)) {
    state.pivotConfig[type].push(name);
    renderPivotControls();
    refreshPivotStudio();
  }
}

function changePivotAggFunc(func) {
  state.pivotConfig.agg_func = func;
  const sel = document.getElementById('pivotAggFuncSelect');
  if (sel) sel.value = func;
  renderPivotControls();
  refreshPivotStudio();
}

function renderPivotControls() {
  const rowEl = document.getElementById('pivotRowContainer');
  const colEl = document.getElementById('pivotColContainer');
  const valEl = document.getElementById('pivotValContainer');

  const allCols = getAllColumns();
  const numCols = state.activeDataset.numericColumns || [];

  if (rowEl) {
    const pills = state.pivotConfig.rows.map(r => `
      <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl pill-cat text-xs font-semibold">
        <span>${r}</span>
        <button onclick="removePivotItem('rows', '${r}')" class="text-slate-400 hover:text-rose-400 font-bold ml-0.5">×</button>
      </span>
    `).join('');

    const available = allCols.filter(c => !state.pivotConfig.rows.includes(c));
    const selectHtml = `
      <select onchange="addPivotItem('rows', this.value); this.value='';" class="px-2 py-1 rounded-lg bg-[#0b0f17] border border-purple-500/30 text-purple-200 text-xs outline-none cursor-pointer hover:bg-purple-900/20">
        <option value="" selected>+ Satır Ekle</option>
        ${available.map(c => `<option value="${c}">${c}</option>`).join('')}
      </select>
    `;
    rowEl.innerHTML = (pills ? pills : '<span class="text-xs text-slate-500 italic mr-1">Satır yok:</span>') + selectHtml;
  }

  if (colEl) {
    const pills = state.pivotConfig.cols.map(c => `
      <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl pill-cat text-xs font-semibold">
        <span>${c}</span>
        <button onclick="removePivotItem('cols', '${c}')" class="text-slate-400 hover:text-rose-400 font-bold ml-0.5">×</button>
      </span>
    `).join('');

    const available = allCols.filter(c => !state.pivotConfig.cols.includes(c));
    const selectHtml = `
      <select onchange="addPivotItem('cols', this.value); this.value='';" class="px-2 py-1 rounded-lg bg-[#0b0f17] border border-indigo-500/30 text-indigo-200 text-xs outline-none cursor-pointer hover:bg-indigo-900/20">
        <option value="" selected>+ Sütun Ekle</option>
        ${available.map(c => `<option value="${c}">${c}</option>`).join('')}
      </select>
    `;
    colEl.innerHTML = (pills ? pills : '<span class="text-xs text-slate-500 italic mr-1">Sütun yok:</span>') + selectHtml;
  }

  if (valEl) {
    const aggUpper = (state.pivotConfig.agg_func || 'sum').toUpperCase();
    const pills = state.pivotConfig.values.map(v => `
      <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl pill-num text-xs font-semibold">
        <span>${v} (${aggUpper})</span>
        <button onclick="removePivotItem('values', '${v}')" class="text-slate-400 hover:text-rose-400 font-bold ml-0.5">×</button>
      </span>
    `).join('');

    const available = (numCols.length > 0 ? numCols : allCols).filter(c => !state.pivotConfig.values.includes(c));
    const selectHtml = `
      <select onchange="addPivotItem('values', this.value); this.value='';" class="px-2 py-1 rounded-lg bg-[#0b0f17] border border-cyan-500/30 text-cyan-200 text-xs outline-none cursor-pointer hover:bg-cyan-900/20">
        <option value="" selected>+ Değer Ekle</option>
        ${available.map(c => `<option value="${c}">${c}</option>`).join('')}
      </select>
    `;
    valEl.innerHTML = (pills ? pills : '<span class="text-xs text-slate-500 italic mr-1">Değer yok:</span>') + selectHtml;
  }
}

function removePivotItem(type, name) {
  state.pivotConfig[type] = state.pivotConfig[type].filter(item => item !== name);
  renderPivotControls();
  refreshPivotStudio();
}

async function refreshPivotStudio() {
  const container = document.getElementById('pivotTableOutput');
  if (!container) return;

  container.innerHTML = `<div class="p-8 text-center text-slate-400 font-mono text-xs animate-pulse">⏳ Polars Pivot Matrisi Hesaplanıyor...</div>`;

  try {
    const res = await fetch('/get_pivot_data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        rows: state.pivotConfig.rows,
        cols: state.pivotConfig.cols,
        values: state.pivotConfig.values,
        agg_func: state.pivotConfig.agg_func,
        filters: state.activeFilters
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Pivot verisi hesaplanamadı.');

    renderPivotTableHTML(container, data);
  } catch (err) {
    container.innerHTML = `<div class="p-8 text-center text-rose-400 text-xs">❌ Pivot Hatası: ${err.message}</div>`;
  }
}

function renderPivotTableHTML(container, data) {
  const minVal = data.min_value || 0;
  const maxVal = data.max_value || 1;
  const valRange = (maxVal - minVal) || 1;

  let html = `
    <div class="rounded-2xl border border-white/[0.08] overflow-hidden bg-[#0b0f17]">
      <table class="w-full text-left border-collapse text-xs">
        <thead>
          <tr class="border-b border-white/[0.08] bg-[#141b26] text-slate-300 font-semibold font-mono">
  `;

  // Corner headers
  data.index_names.forEach(name => {
    html += `<th class="py-3 px-4">${name}</th>`;
  });

  // Column headers
  data.column_headers.forEach(h => {
    const isGrand = h.includes('Genel Toplam');
    html += `<th class="py-3 px-4 ${isGrand ? 'text-white font-bold bg-white/[0.04]' : 'text-cyan-300'}">${h}</th>`;
  });

  html += `</tr></thead><tbody class="divide-y divide-white/[0.04] text-slate-200 font-mono">`;

  // Data rows
  data.rows.forEach(r => {
    const isRowGrand = r.is_grand_total;
    html += `<tr class="${isRowGrand ? 'border-t border-white/[0.1] bg-[#141b26] font-bold text-white' : 'hover:bg-white/[0.02]'}">`;

    r.row_labels.forEach(lbl => {
      html += `<td class="py-2.5 px-4 font-sans font-bold text-white">${lbl}</td>`;
    });

    r.cells.forEach((val, cIdx) => {
      const isColGrand = (data.column_headers[cIdx] || '').includes('Genel Toplam');
      let bgStyle = '';

      if (!isRowGrand && !isColGrand && val > 0) {
        const ratio = Math.min(1, Math.max(0, (val - minVal) / valRange));
        const alpha = 0.08 + (ratio * 0.45);
        bgStyle = `background: rgba(52, 211, 153, ${alpha.toFixed(3)});`;
      }

      html += `<td class="py-2.5 px-4 ${isColGrand ? 'text-white font-bold bg-white/[0.04]' : 'text-slate-200'}" style="${bgStyle}">${formatNum(val, 0)}</td>`;
    });

    html += `</tr>`;
  });

  html += `</tbody></table></div>`;
  container.innerHTML = html;
}

async function exportPivotExcel() {
  showToast('Pivot tablosu Excel (.xlsx) formatında derleniyor...', 'info');
  try {
    const res = await fetch('/export_pivot_excel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        rows: state.pivotConfig.rows,
        cols: state.pivotConfig.cols,
        values: state.pivotConfig.values,
        agg_func: state.pivotConfig.agg_func,
        filters: state.activeFilters
      })
    });
    if (!res.ok) throw new Error('Dışa aktarma başarısız.');
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Pivot_Analizi_${Date.now()}.xlsx`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    showToast('Pivot tablosu indirildi.', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ── MODE 4: EXECUTIVE DASHBOARD CANVAS ──
async function renderDashboardStage() {
  const kpiContainer = document.getElementById('dashKpiGrid');
  const pinnedContainer = document.getElementById('pinnedGrid');

  // 1. Fetch KPIs
  if (kpiContainer) {
    try {
      const res = await fetch('/get_kpi_summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filters: state.activeFilters })
      });
      const kpis = await res.json();
      if (res.ok && kpis.kpis) {
        kpiContainer.innerHTML = kpis.kpis.slice(0, 4).map(k => `
          <div class="p-4 rounded-2xl bg-[#131b26] border border-white/[0.08]">
            <span class="text-xs text-slate-400 block mb-1">${k.title}</span>
            <strong class="text-2xl font-bold text-white font-mono">${k.value}</strong>
            <span class="text-xs text-emerald-400 font-semibold block mt-1">${k.subtext || 'Aktif Veri'}</span>
          </div>
        `).join('');
      }
    } catch (e) {}
  }

  // 2. Render Pinned Charts
  if (pinnedContainer) {
    if (state.pinnedCharts.length === 0) {
      pinnedContainer.innerHTML = `
        <div class="col-span-full p-12 text-center text-slate-500 rounded-3xl bg-[#131b26] border border-white/[0.08] space-y-2">
          <span class="text-3xl">📍</span>
          <h4 class="text-sm font-bold text-white">Henüz Panoya Grafik Sabitlenmedi</h4>
          <p class="text-xs">50 Grafik Stüdyosunda herhangi bir grafiği incelerken <strong>"Panoya Sabitle"</strong> butonuna basarak buraya ekleyebilirsiniz.</p>
        </div>
      `;
      return;
    }

    pinnedContainer.innerHTML = state.pinnedCharts.map(ch => `
      <div class="p-5 rounded-3xl bg-[#131b26] border border-white/[0.08] space-y-3 relative group" id="${ch.id}">
        <div class="flex items-center justify-between">
          <h4 class="text-xs font-bold text-white truncate max-w-[80%]">${ch.title}</h4>
          <button onclick="removePinnedChart('${ch.id}')" class="text-slate-500 hover:text-rose-400 text-sm font-bold">×</button>
        </div>
        <div class="h-48 rounded-2xl bg-[#0b0f17] border border-white/[0.06] p-2 flex items-center justify-center overflow-hidden" id="plotly_${ch.id}">
          <span class="text-xs text-slate-500">Grafik yükleniyor...</span>
        </div>
        <div class="text-[11px] text-slate-400 flex justify-between font-mono">
          <span>X: ${ch.xCol} • Y: ${ch.yCol}</span>
          <span class="text-emerald-400">${ch.pinnedAt}</span>
        </div>
      </div>
    `).join('');

    // Draw miniature Plotly charts for each pinned card
    state.pinnedCharts.forEach(ch => {
      setTimeout(() => {
        fallbackPlotlyDraw(`plotly_${ch.id}`, ch.data, ch.chartType, ch.xCol, [ch.yCol]);
      }, 50);
    });
  }
}

function removePinnedChart(id) {
  state.pinnedCharts = state.pinnedCharts.filter(c => c.id !== id);
  const badge = document.getElementById('dashBadgeNumber');
  if (badge) badge.textContent = state.pinnedCharts.length;
  renderDashboardStage();
}

function clearDashboard() {
  state.pinnedCharts = [];
  const badge = document.getElementById('dashBadgeNumber');
  if (badge) badge.textContent = 0;
  renderDashboardStage();
  showToast('Pano temizlendi.', 'info');
}

function downloadDashboardPdf() {
  const el = document.getElementById('paneDash');
  if (!el || typeof html2pdf === 'undefined') {
    alert('PDF kütüphanesi yüklenemedi.');
    return;
  }
  showToast('Yönetici panosu A4 PDF olarak derleniyor...', 'info');
  html2pdf().set({
    margin: [10, 10, 10, 10],
    filename: `DataViz_Executive_Dashboard_${Date.now()}.pdf`,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true, backgroundColor: '#0b0f17' },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'landscape' }
  }).from(el).save();
}

// ── MODE 5: CANLI VERİ TABLOSU ──
async function refreshTablePreview() {
  const container = document.getElementById('liveTableContainer');
  if (!container) return;

  container.innerHTML = `<div class="p-8 text-center text-slate-400 font-mono text-xs animate-pulse">⏳ Bellek içi veriler getiriliyor...</div>`;

  try {
    const res = await fetch(`/get_sheet_preview?limit=${state.tableLimit}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Veri tablosu alınamadı.');

    const cols = data.columns || [];
    const rows = data.preview || [];

    let html = `
      <div class="rounded-2xl border border-white/[0.08] overflow-x-auto custom-scroll bg-[#131b26]">
        <table class="w-full text-left border-collapse text-xs whitespace-nowrap">
          <thead>
            <tr class="border-b border-white/[0.08] bg-[#0e131d] text-slate-400 font-semibold font-mono">
              <th class="py-3 px-4">#</th>
    `;

    cols.forEach(col => {
      const isNum = state.activeDataset.numericColumns.includes(col);
      html += `<th class="py-3 px-4 ${isNum ? 'text-cyan-300' : 'text-purple-300'}">${col} (${isNum ? '#' : 'T'})</th>`;
    });

    html += `</tr></thead><tbody class="divide-y divide-white/[0.04] text-slate-200 font-mono">`;

    rows.forEach((r, idx) => {
      html += `<tr class="hover:bg-white/[0.02]"><td class="py-2.5 px-4 text-slate-500 font-sans">${idx + 1}</td>`;
      cols.forEach(col => {
        const val = r[col];
        const isNum = state.activeDataset.numericColumns.includes(col);
        const formatted = isNum && val != null ? formatNum(val) : (val != null ? String(val) : '-');
        html += `<td class="py-2.5 px-4 ${isNum ? 'text-cyan-400 font-bold' : 'font-sans'}">${formatted}</td>`;
      });
      html += `</tr>`;
    });

    html += `</tbody></table></div>`;
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div class="p-8 text-center text-rose-400 text-xs">❌ Hata: ${err.message}</div>`;
  }
}

function updateTableLimit(lim) {
  state.tableLimit = parseInt(lim);
  refreshTablePreview();
}

// ── GLOBAL SLICERS & FILTERS ──
function renderActiveFilterChips() {
  const container = document.getElementById('activeSlicersList');
  if (!container) return;

  if (state.activeFilters.length === 0) {
    container.innerHTML = `<span class="text-xs text-slate-500 italic">Filtre uygulanmadı (Tüm veri aktif)</span>`;
    return;
  }

  container.innerHTML = state.activeFilters.map((f, idx) => `
    <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-blue-500/10 text-blue-300 border border-blue-500/25 text-xs">
      <span>${f.column}: ${f.type === 'cat' ? f.values.slice(0, 3).join(', ') + (f.values.length > 3 ? '...' : '') : `[${f.min || 0} - ${f.max || 'Max'}]`}</span>
      <button onclick="removeFilter(${idx})" class="text-blue-300 hover:text-rose-400 font-bold ml-1">×</button>
    </span>
  `).join('');
}

function removeFilter(target) {
  if (typeof target === 'number') {
    state.activeFilters.splice(target, 1);
  } else if (typeof target === 'string') {
    state.activeFilters = state.activeFilters.filter(f => f.column !== target);
  }
  syncGlobals();
  renderActiveFilterChips();
  evaluateStudioEngine();
  showToast('Filtre kaldırıldı.', 'info');
}

// ── MODAL 1: SMART DATA HEALER ──
function openHealerModal() {
  const modal = document.getElementById('modalHealer');
  if (!modal) return;
  modal.classList.remove('hidden');

  // Populate Anomalies Tab
  const list = document.getElementById('healerAnomalyList');
  const h = state.currentHealth;

  if (list && h) {
    const anomalies = h.anomalies || [];
    if (anomalies.length === 0) {
      list.innerHTML = `
        <div class="p-6 text-center text-emerald-400 rounded-2xl bg-emerald-500/10 border border-emerald-500/20">
          <span class="text-2xl block mb-2">🎉</span>
          <strong class="block text-sm">Sayısal Veri Sağlığı Mükemmel</strong>
          <span class="text-xs opacity-80">Sayısal alanlarda hiçbir sözel ek, sembol veya tip bozulması tespit edilmedi.</span>
        </div>`;
    } else {
      list.innerHTML = anomalies.map(a => `
        <div class="p-4 rounded-2xl bg-[#0b0f17] border border-white/[0.08] space-y-2">
          <div class="flex items-center justify-between text-xs">
            <span class="font-bold text-white flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-amber-400"></span>
              <span>[${a.column}] Sütun Analizi</span>
            </span>
            <span class="font-mono text-amber-400 font-semibold">${a.anomaly_count || 1} Anomali</span>
          </div>
          <p class="text-xs text-slate-400">${a.reason || 'Sözel ekler ve para simgeleri tespit edildi.'} Kayıpsız float64 tipine çevrilecektir.</p>
        </div>
      `).join('');
    }
  }

  // Populate NaN stats
  document.getElementById('healerTotalRows') && (document.getElementById('healerTotalRows').textContent = (h?.total_rows || state.activeDataset.totalRows).toLocaleString());
  document.getElementById('healerMissingCells') && (document.getElementById('healerMissingCells').textContent = (h?.missing_cells || 0).toLocaleString());
  document.getElementById('healerMissingRows') && (document.getElementById('healerMissingRows').textContent = (h?.missing_rows || 0).toLocaleString());
}

async function executeSmartHeal() {
  try {
    const res = await fetch('/repair_column_anomalies', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ column: '__all__', repair_mode: 'smart_heal' })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    state.activeDataset.numericColumns = data.numeric_columns || state.activeDataset.numericColumns;
    state.activeDataset.categoricalColumns = data.categorical_columns || state.activeDataset.categoricalColumns;
    renderColumnPool();
    checkHealthAsync();
    closeModal('modalHealer');
    showToast('Tüm anomaliler Polars ile kayıpsız olarak onarıldı!', 'success', 'Veri Onarıldı');
    evaluateStudioEngine();
  } catch (err) {
    showToast(err.message, 'error', 'Onarma Hatası');
  }
}

async function executeCleanNaN(action) {
  try {
    const res = await fetch('/clean_data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    state.activeDataset.totalRows = data.total_rows;
    state.activeDataset.numericColumns = data.numeric_columns || state.activeDataset.numericColumns;
    renderTopbar();
    checkHealthAsync();
    closeModal('modalHealer');
    showToast(`Eksik değerler başarıyla temizlendi (${action}).`, 'success');
    evaluateStudioEngine();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ── MODAL 2: DATA MERGE & JOIN ──
function openMergeModal() {
  const modal = document.getElementById('modalMerge');
  if (!modal) return;
  modal.classList.remove('hidden');

  // Populate Key 1 select
  const sel1 = document.getElementById('mergeKey1Select');
  if (sel1) {
    sel1.innerHTML = getAllColumns().map(c => `<option value="${c}">${c}</option>`).join('');
  }
}

async function handleSecondFileUpload(file) {
  if (!file) return;
  const statusEl = document.getElementById('mergeFileStatus');
  if (statusEl) {
    statusEl.innerHTML = `<span class="animate-pulse text-purple-400">⏳ 2. dosya (${file.name}) taranıyor...</span>`;
    statusEl.classList.remove('hidden');
  }

  const fd = new FormData();
  fd.append('file2', file);

  try {
    const res = await fetch('/preview_second_file', { method: 'POST', body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || '2. dosya okunamadı.');

    state.secondFileCols = data.cols2 || [];

    // Populate Key 2 select
    const sel2 = document.getElementById('mergeKey2Select');
    if (sel2) {
      sel2.innerHTML = state.secondFileCols.map(c => `<option value="${c}">${c}</option>`).join('');
      if (data.auto_key2) sel2.value = data.auto_key2;
    }
    const sel1 = document.getElementById('mergeKey1Select');
    if (sel1 && data.auto_key1) sel1.value = data.auto_key1;

    document.getElementById('mergeConfigArea')?.classList.remove('hidden');
    if (statusEl) statusEl.innerHTML = `<span class="text-emerald-400">✓ ${file.name} eşleştirmeye hazır (${data.file2_rows} satır).</span>`;
  } catch (err) {
    if (statusEl) statusEl.innerHTML = `<span class="text-rose-400">❌ ${err.message}</span>`;
  }
}

async function executeMerge() {
  const key1 = document.getElementById('mergeKey1Select')?.value;
  const key2 = document.getElementById('mergeKey2Select')?.value;
  const joinType = document.getElementById('mergeJoinType')?.value || 'left';

  if (!key1 || !key2) {
    showToast('Ortak bağlantı sütunlarını seçiniz.', 'warning');
    return;
  }

  try {
    const res = await fetch('/join_datasets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key1, key2, join_type: joinType })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Birleştirme başarısız.');

    state.activeDataset.totalRows = data.total_rows;
    state.activeDataset.totalCols = data.total_cols;
    state.activeDataset.numericColumns = data.numeric_columns || [];
    state.activeDataset.categoricalColumns = data.categorical_columns || [];
    state.activeDataset.joinedColumns = data.new_joined_columns || [];

    renderTopbar();
    renderColumnPool();
    closeModal('modalMerge');
    showToast(`2. dosya başarıyla birleştirildi (${data.new_joined_columns.length} yeni sütun eklendi).`, 'success', 'Birleşim Tamamlandı');
    evaluateStudioEngine();
  } catch (err) {
    showToast(err.message, 'error', 'Birleştirme Hatası');
  }
}

// ── MODAL 3: FORMULA WIZARD ──
function openFormulaModal() {
  const modal = document.getElementById('modalFormula');
  if (!modal) return;
  modal.classList.remove('hidden');

  const nums = state.activeDataset.numericColumns;
  const sel1 = document.getElementById('formulaCol1Select');
  const sel2 = document.getElementById('formulaCol2Select');

  if (sel1) sel1.innerHTML = nums.map(c => `<option value="${c}">${c}</option>`).join('');
  if (sel2) sel2.innerHTML = nums.map(c => `<option value="${c}">${c}</option>`).join('');
}

function selectFormulaOp(op) {
  state.formulaSelectedOp = op;
  document.querySelectorAll('.formula-op-btn').forEach(btn => {
    if (btn.dataset.op === op) {
      btn.className = "formula-op-btn px-3 py-1.5 rounded-lg bg-cyan-500 text-slate-950 font-bold text-sm shadow";
    } else {
      btn.className = "formula-op-btn px-3 py-1.5 rounded-lg bg-white/[0.08] hover:bg-white/[0.15] text-white font-bold text-sm transition-all";
    }
  });
}

async function executeFormula() {
  const newCol = document.getElementById('formulaNewColName')?.value.trim();
  const col1 = document.getElementById('formulaCol1Select')?.value;
  const col2 = document.getElementById('formulaCol2Select')?.value;
  const op = state.formulaSelectedOp || '+';

  if (!newCol) {
    showToast('Yeni sütun adı giriniz.', 'warning');
    return;
  }

  try {
    const res = await fetch('/create_calculated_column', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        new_col_name: newCol,
        col1,
        op,
        col2
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Formül hesaplanamadı.');

    state.activeDataset.numericColumns = data.numeric_columns;
    state.activeDataset.calculatedColumns.push(newCol);

    renderTopbar();
    renderColumnPool();
    closeModal('modalFormula');
    showToast(`[${newCol}] sütunu üretildi ve havuza eklendi.`, 'success', 'Formül Başarılı');
    evaluateStudioEngine();
  } catch (err) {
    showToast(err.message, 'error', 'Formül Hatası');
  }
}

// ── MODAL 4: SLICER / FILTER MODAL ──
function openFilterModal() {
  const modal = document.getElementById('modalFilter');
  if (!modal) return;
  modal.classList.remove('hidden');

  const sel = document.getElementById('filterColSelect');
  if (sel) {
    sel.innerHTML = getAllColumns().map(c => `<option value="${c}">${c}</option>`).join('');
    handleFilterColumnChange();
  }
}

async function handleFilterColumnChange() {
  const col = document.getElementById('filterColSelect')?.value;
  const dynContainer = document.getElementById('filterDynamicBody');
  if (!col || !dynContainer) return;

  dynContainer.innerHTML = `<span class="text-xs text-slate-400 font-mono animate-pulse">Sütun değerleri taranıyor...</span>`;

  try {
    const res = await fetch(`/get_column_unique_values?column=${encodeURIComponent(col)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    if (data.type === 'cat') {
      const cats = data.categories || [];
      dynContainer.innerHTML = `
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs text-slate-400 font-semibold">Dahil Edilecek Değerler (${cats.length}):</span>
            <div class="flex gap-2 text-xs">
              <button type="button" onclick="toggleAllFilterCats(true)" class="text-blue-400 hover:underline">Tümü</button>
              <button type="button" onclick="toggleAllFilterCats(false)" class="text-slate-400 hover:underline">Temizle</button>
            </div>
          </div>
          <div class="space-y-1.5 max-h-40 overflow-y-auto custom-scroll pr-1" id="filterCheckboxesList">
            ${cats.map(c => `
              <label class="flex items-center gap-2 text-xs text-white cursor-pointer hover:bg-white/[0.04] p-1 rounded">
                <input type="checkbox" value="${c.value}" checked class="accent-blue-600 rounded">
                <span>${c.value}</span>
                <span class="text-[10px] text-slate-500 font-mono">(${c.count})</span>
              </label>
            `).join('')}
          </div>
        </div>
      `;
    } else {
      dynContainer.innerHTML = `
        <div class="space-y-2 text-xs">
          <span class="text-slate-400 font-semibold block">Sayısal Aralık Filtresi:</span>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-slate-400 block mb-1">Büyüktür (Min)</label>
              <input type="number" id="filterNumMin" value="${data.min || 0}" step="any" class="w-full px-3 py-1.5 rounded-xl bg-[#0b0f17] border border-white/[0.1] text-white">
            </div>
            <div>
              <label class="text-slate-400 block mb-1">Küçüktür (Max)</label>
              <input type="number" id="filterNumMax" value="${data.max || 100}" step="any" class="w-full px-3 py-1.5 rounded-xl bg-[#0b0f17] border border-white/[0.1] text-white">
            </div>
          </div>
        </div>
      `;
    }
  } catch (err) {
    dynContainer.innerHTML = `<span class="text-xs text-rose-400">Hata: ${err.message}</span>`;
  }
}

function toggleAllFilterCats(checked) {
  document.querySelectorAll('#filterCheckboxesList input[type="checkbox"]').forEach(cb => cb.checked = checked);
}

function applyCurrentFilter() {
  const col = document.getElementById('filterColSelect')?.value;
  if (!col) return;

  const isNum = state.activeDataset.numericColumns.includes(col);

  // Remove existing filter on the same column to avoid duplicate/conflicting filter rules
  state.activeFilters = state.activeFilters.filter(f => f.column !== col);

  if (isNum) {
    const min = parseFloat(document.getElementById('filterNumMin')?.value);
    const max = parseFloat(document.getElementById('filterNumMax')?.value);
    state.activeFilters.push({ column: col, type: 'num', min, max });
  } else {
    const selected = [];
    document.querySelectorAll('#filterCheckboxesList input[type="checkbox"]:checked').forEach(cb => {
      selected.push(cb.value);
    });
    if (selected.length === 0) {
      showToast('En az 1 kategori seçiniz.', 'warning');
      return;
    }
    state.activeFilters.push({ column: col, type: 'cat', values: selected });
  }

  syncGlobals();
  renderActiveFilterChips();
  closeModal('modalFilter');
  showToast(`[${col}] filtresi uygulandı.`, 'success');
  evaluateStudioEngine();
}

// ── MODAL 5: A4 EXECUTIVE REPORT STUDIO ──
function openA4Modal() {
  const modal = document.getElementById('modalA4');
  if (!modal) return;
  modal.classList.remove('hidden');

  // Fill in A4 report details
  const xCol = state.axis.x?.name || 'Metrik X';
  const yCol = state.axis.y[0]?.name || 'Metrik Y';
  const summaryEl = document.getElementById('a4SummaryParagraph');

  if (summaryEl) {
    if (state.currentRegression) {
      const reg = state.currentRegression.regression;
      const corr = state.currentRegression.correlation;
      const pVal = reg?.p_value != null ? reg.p_value : corr?.p_value;
      summaryEl.innerHTML = `<strong>${xCol}</strong> ve <strong>${yCol}</strong> değişkenleri arasında <strong>${corr?.method ? corr.method.toUpperCase() : 'PEARSON'}</strong> korelasyon analizi yapılmış olup <strong>r = ${corr?.r != null ? corr.r.toFixed(4) : '-'}</strong> düzeyinde ilişki saptanmıştır (${formatPValue(pVal)}). Kurulan model <strong>${reg?.equation || '-'}</strong> denklemiyle varyansın <strong>%${((reg?.r_squared || 0) * 100).toFixed(1)}</strong>'ini açıklamaktadır.`;
    } else if (state.currentAdvanced) {
      const adv = state.currentAdvanced;
      if (adv.t_test) {
        summaryEl.innerHTML = `<strong>${xCol}</strong> kategorik değişkeninin 2 grubu arasında <strong>${yCol}</strong> metriği bakımından Student's T-Testi uygulanmıştır (t = ${adv.t_test.t_stat?.toFixed(3)}, p = ${formatPValue(adv.t_test.p_value)}). Toplam ${state.activeDataset.totalRows.toLocaleString()} satırlık veri incelenmiştir.`;
      } else if (adv.anova) {
        summaryEl.innerHTML = `<strong>${xCol}</strong> kategorik değişkeninin grupları arasında <strong>${yCol}</strong> metriği bakımından Tek Yönlü ANOVA uygulanmıştır (F = ${adv.anova.f_stat?.toFixed(2)}, p = ${formatPValue(adv.anova.p_value)}). En yüksek ortalamayı <strong>${adv.anova_best_group || adv.best_group || '-'}</strong> grubu sergilemektedir.`;
      } else {
        summaryEl.innerHTML = `<strong>${xCol}</strong> ve <strong>${yCol}</strong> değişkenleri arasında kurumsal dağılım ve varyans analizleri gerçekleştirilmiştir. Toplam ${state.activeDataset.totalRows.toLocaleString()} satırlık veri seti doğrulanmıştır.`;
      }
    } else {
      summaryEl.innerHTML = `<strong>${xCol}</strong> ve <strong>${yCol}</strong> değişkenleri arasında kurumsal dağılım ve varyans analizleri gerçekleştirilmiştir. Toplam ${state.activeDataset.totalRows.toLocaleString()} satırlık veri seti doğrulanmıştır.`;
    }
  }

  const dateEl = document.getElementById('a4ReportDate');
  if (dateEl) dateEl.textContent = new Date().toLocaleDateString('tr-TR', { year: 'numeric', month: 'long', day: 'numeric' });
}

function downloadA4Pdf() {
  const container = document.getElementById('a4ReportContainer');
  if (!container || typeof html2pdf === 'undefined') {
    alert('PDF kütüphanesi yüklenemedi.');
    return;
  }
  showToast('A4 Yönetici Raporu PDF olarak indiriliyor...', 'info');
  html2pdf().set({
    margin: [10, 10, 10, 10],
    filename: `DataViz_A4_Yonetici_Raporu_${Date.now()}.pdf`,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true, backgroundColor: '#ffffff' },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
  }).from(container).save().then(() => {
    closeModal('modalA4');
  });
}

// ── EXPORT PARQUET STREAM ──
async function exportParquetStream() {
  showToast('Veri seti Apache Parquet formatında indiriliyor...', 'info');
  try {
    const res = await fetch('/export_data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ format: 'parquet', filters: state.activeFilters })
    });
    if (!res.ok) throw new Error('Parquet çıktısı alınamadı.');
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `DataViz_Export_${Date.now()}.parquet`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    showToast('Parquet dosyası başarıyla indirildi.', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ── MODAL HELPERS ──
function openModal(id) {
  if (id === 'modalHealer') return openHealerModal();
  if (id === 'modalMerge') return openMergeModal();
  if (id === 'modalFormula') return openFormulaModal();
  if (id === 'modalFilter') return openFilterModal();
  if (id === 'modalA4') return openA4Modal();
  const m = document.getElementById(id);
  if (m) m.classList.remove('hidden');
}

function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add('hidden');
}

// ── INITIAL BOOTSTRAP ──
document.addEventListener('DOMContentLoaded', async () => {
  // ESC and Backdrop modal close
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay:not(.hidden)').forEach(m => m.classList.add('hidden'));
    }
  });

  document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.addEventListener('click', e => {
      if (e.target === modal) modal.classList.add('hidden');
    });
  });

  // Check if session already has an active dataset
  try {
    const res = await fetch('/check_health', { cache: 'no-store' });
    const health = await res.json();
    if (res.ok && health.success && health.total_rows > 0) {
      // Fetch sheet preview to retrieve metadata
      const pRes = await fetch('/get_sheet_preview?limit=1');
      const pData = await pRes.json();
      if (pRes.ok && pData.columns) {
        const numCols = [];
        const catCols = [];
        pData.columns.forEach(c => {
          // simple detection
          if (pData.preview && pData.preview[0] && typeof pData.preview[0][c] === 'number') {
            numCols.push(c);
          } else {
            catCols.push(c);
          }
        });
        applyDatasetData({
          total_rows: health.total_rows,
          total_cols: pData.columns.length,
          numeric_columns: numCols,
          categorical_columns: catCols
        }, 'Aktif_Veri_Seti.xlsx');
        return;
      }
    }
  } catch (e) {}

  // If URL has ?sample=1 or ?sample=true, auto-load sample
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('sample') === '1' || urlParams.get('sample') === 'true' || urlParams.get('load_sample') === '1') {
    loadSampleDataset();
  }
});
