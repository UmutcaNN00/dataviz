/* ════════════════════════════════════════════════════════════
   DATAVIZ PRO V6 — APPLICATION COORDINATOR (app.js)
   Screen Transitions, Upload Handlers, Navigation & Shortcuts
════════════════════════════════════════════════════════════ */

var isUploading = false;

// ── SCREEN TRANSITIONS COORDINATOR ──
function showScreen(num) {
  const ids = ['step1-upload', 'step2-config', 'step3-dashboard', 'screen-pivot-studio'];
  const screens = ids.map(id => document.getElementById(id));
  screens.forEach(s => s && (s.classList.add('hidden'), s.classList.remove('active')));

  const activeIdx = (num === 'pivot' || num === 4) ? 3 : (num - 1);
  const target = screens[activeIdx];
  if (target) { target.classList.remove('hidden'); target.classList.add('active'); }

  if ((num === 4 || num === 'pivot') && typeof initPivotStudio === 'function') {
    initPivotStudio();
    if (typeof refreshPivotStudio === 'function') refreshPivotStudio();
  }
}

function proceedToStep2() {
  if (typeof initDragDropPool === 'function') initDragDropPool();
  if (typeof renderChartGrid === 'function') renderChartGrid('all');
  showScreen(2);
}

async function goToStep3(chartId, chartName) {
  currentPlotType = window.currentPlotType = chartId;
  const titleEl = document.getElementById('activeChartTitle');
  if (titleEl && chartName) titleEl.textContent = chartName;
  showScreen(3);
  if (typeof refreshActiveChart === 'function') await refreshActiveChart();
}

// ── DATASET INGESTION & HEALTH HELPERS ──
function setUploadStatus(html, isError = false) {
  const el = document.getElementById('mainUploadStatus');
  if (!el) return;
  if (!html) { el.style.display = 'none'; return; }
  el.className = `status-msg ${isError ? 'error' : 'loading'}`;
  el.innerHTML = html;
  el.style.display = 'block';
}

function applyUploadedDataset(data) {
  numericColumns = window.numericColumns = data.numeric_columns || [];
  categoricalColumns = window.categoricalColumns = data.categorical_columns || [];
  globalColumns = window.globalColumns = [...categoricalColumns, ...numericColumns];
  calculatedColumns = window.calculatedColumns = [];
  activeFilters = window.activeFilters = [];
  dashboardCharts = window.dashboardCharts = [];
  sheetNames = window.sheetNames = data.sheet_names || [];

  if (typeof updateDashboardBadge === 'function') updateDashboardBadge();
  if (typeof renderActiveFilterChips === 'function') renderActiveFilterChips();
  renderSheetTabs(sheetNames, data.active_sheet);

  const s2 = document.getElementById('s2FileName');
  if (s2) s2.textContent = activeFileName;
  const pv = document.getElementById('pivotFileName');
  if (pv) pv.textContent = activeFileName;

  setUploadStatus(null);
  proceedToStep2();
  checkDataHealthAsync();
}

async function checkDataHealthAsync() {
  try {
    const res = await fetch('/check_health', { cache: 'no-store' });
    const health = await res.json();
    if (typeof updateAnomalyBadges === 'function') updateAnomalyBadges(health);
    if (health?.has_issues && typeof openDataPrepModal === 'function') openDataPrepModal(null, health);
  } catch (err) {
    console.warn('Veri kontrol uyarısı:', err);
  }
}

// ── UPLOAD & SAMPLE DATASET LOADERS ──
async function handleLoadSampleData() {
  if (isUploading) return;
  isUploading = true;
  activeFileName = window.activeFileName = 'Akademik_Ornek_Veri_Seti.xlsx';
  setUploadStatus('⏳ Hazır örnek veri seti yükleniyor...');

  try {
    const res = await fetch('/load_sample', { method: 'POST' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Örnek veri yüklenemedi');
    applyUploadedDataset(data);
  } catch (err) {
    alert('Örnek veri yüklenemedi: ' + err.message);
    setUploadStatus(null);
  } finally {
    isUploading = false;
  }
}

async function handleFileUpload(file) {
  if (!file || isUploading) return;
  isUploading = true;
  activeFileName = window.activeFileName = file.name;
  setUploadStatus(`⏳ <strong>${file.name}</strong> yükleniyor ve analiz ediliyor...`);

  const fd = new FormData();
  fd.append('file', file);

  try {
    const res = await fetch('/upload', { method: 'POST', body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Dosya yüklenemedi');
    applyUploadedDataset(data);
  } catch (err) {
    const errMsg = err.message || 'Dosya okunamadı veya biçim desteklenmiyor.';
    setUploadStatus(`⚠️ <strong>Dosya Yükleme Hatası:</strong> ${errMsg}`, true);
    alert(`⚠️ Dosya Yüklenemedi:\n\n${errMsg}`);
  } finally {
    isUploading = false;
    const fin = document.getElementById('mainFileInput');
    if (fin) fin.value = '';
  }
}

function renderSheetTabs(sheets, activeSheet) {
  const bar = document.getElementById('sheetTabsBar'), list = document.getElementById('sheetTabsList');
  const pBar = document.getElementById('pivotSheetTabsBar'), pList = document.getElementById('pivotSheetTabsList');
  if (!sheets || sheets.length <= 1) {
    bar?.classList.add('hidden'); pBar?.classList.add('hidden');
    return;
  }
  [bar, pBar].forEach(b => b?.classList.remove('hidden'));
  [list, pList].forEach(l => { if (l) l.innerHTML = ''; });

  sheets.forEach(s => {
    [list, pList].forEach(c => {
      if (!c) return;
      const btn = document.createElement('button');
      btn.className = `sheet-tab-btn ${s === activeSheet ? 'active' : ''}`;
      btn.textContent = s;
      btn.onclick = () => switchSheet(s);
      c.appendChild(btn);
    });
  });
}

async function switchSheet(sheetName) {
  try {
    const res = await fetch('/switch_sheet', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sheet_name: sheetName })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    numericColumns = window.numericColumns = data.numeric_columns || [];
    categoricalColumns = window.categoricalColumns = data.categorical_columns || [];
    globalColumns = window.globalColumns = [...categoricalColumns, ...numericColumns];
    calculatedColumns = window.calculatedColumns = [];
    activeFilters = window.activeFilters = [];

    if (typeof renderActiveFilterChips === 'function') renderActiveFilterChips();
    renderSheetTabs(sheetNames, sheetName);
    if (typeof initDragDropPool === 'function') initDragDropPool();
    if (typeof renderChartGrid === 'function') renderChartGrid('all');
  } catch(err) {
    alert("Sayfa değiştirme hatası: " + err.message);
  }
}

// ── DOM BOOTSTRAP & NAVIGATION LISTENERS ──
document.addEventListener('DOMContentLoaded', () => {
  // Modal kapatıcılar (Escape & Backdrop)
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') document.querySelectorAll('.modal-overlay:not(.hidden)').forEach(m => m.classList.add('hidden'));
  });
  document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.addEventListener('click', e => { if (e.target === modal) modal.classList.add('hidden'); });
  });

  window.addEventListener('dragover', e => e.preventDefault(), false);
  window.addEventListener('drop', e => e.preventDefault(), false);

  const dropZone = document.getElementById('mainDropZone'), fileInput = document.getElementById('mainFileInput');
  ['dragenter', 'dragover'].forEach(n => dropZone?.addEventListener(n, e => { e.preventDefault(); dropZone.classList.add('dragover'); }));
  ['dragleave', 'dragend'].forEach(n => dropZone?.addEventListener(n, e => { e.preventDefault(); dropZone.classList.remove('dragover'); }));
  dropZone?.addEventListener('drop', e => {
    e.preventDefault(); dropZone.classList.remove('dragover');
    if (e.dataTransfer?.files?.length) handleFileUpload(e.dataTransfer.files[0]);
  });
  dropZone?.addEventListener('click', e => { if (!e.target.closest('#btnLoadSampleData')) fileInput?.click(); });
  document.getElementById('btnBrowseFile')?.addEventListener('click', e => { e.preventDefault(); fileInput?.click(); });
  document.getElementById('btnLoadSampleData')?.addEventListener('click', e => { e.preventDefault(); handleLoadSampleData(); });
  fileInput?.addEventListener('change', e => { if (e.target.files?.length) handleFileUpload(e.target.files[0]); });

  // Navigasyon butonları
  document.getElementById('btnCancelStep2')?.addEventListener('click', () => showScreen(1));
  document.getElementById('btnBackToStep2')?.addEventListener('click', () => showScreen(2));
  const resetToUpload = () => { if (fileInput) fileInput.value = ''; setUploadStatus(null); showScreen(1); };
  document.getElementById('btnNewFile')?.addEventListener('click', resetToUpload);
  document.getElementById('btnPivotNewFile')?.addEventListener('click', resetToUpload);

  document.getElementById('btnModeChartsS2')?.addEventListener('click', () => showScreen(2));
  document.getElementById('btnModeChartsS3')?.addEventListener('click', () => showScreen(3));
  document.getElementById('btnPivotBackToCharts')?.addEventListener('click', () => {
    if (axisConfig.x || axisConfig.y.length) showScreen(3); else showScreen(2);
  });

  ['btnOpenPivotStudioS2', 'btnOpenPivotStudioS3', 'btnPivotStudioTop'].forEach(id => {
    document.getElementById(id)?.addEventListener('click', () => showScreen(4));
  });

  document.getElementById('topbarHelp')?.addEventListener('click', () => {
    alert('⌨️ Kısayollar:\n\nG → Grafik sekmesi\nS → İstatistik sekmesi\nD → Dashboard sekmesi\nP → Panoya ekle\n? → Bu yardım\nEsc → Açık pencereleri kapat');
  });

  document.getElementById('refreshStatsBtn')?.addEventListener('click', () => {
    if (axisConfig.y && axisConfig.y.length > 0 && typeof fetchStats === 'function') fetchStats();
  });

  // Step 3 Tab Bar
  document.querySelectorAll('#mainTabsBar .tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#mainTabsBar .tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.add('hidden'));
      btn.classList.add('active');
      const tabName = btn.dataset.tab;
      if (tabName === 'chart') {
        document.getElementById('tabChart')?.classList.remove('hidden');
        try { Plotly.Plots.resize('chartArea'); } catch(e){}
      } else if (tabName === 'stats') {
        document.getElementById('tabStats')?.classList.remove('hidden');
      } else if (tabName === 'ai') {
        document.getElementById('tabAi')?.classList.remove('hidden');
      } else if (tabName === 'dashboard') {
        document.getElementById('tabDashboard')?.classList.remove('hidden');
        if (typeof renderDashboardGrid === 'function') renderDashboardGrid();
        if (typeof fetchKpis === 'function') fetchKpis();
      }
    });
  });

  // Klavye kısayolları
  document.addEventListener('keydown', e => {
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;
    const key = e.key.toLowerCase();
    if (key === 'g') document.querySelector('#mainTabsBar .tab-btn[data-tab="chart"]')?.click();
    else if (key === 's') document.querySelector('#mainTabsBar .tab-btn[data-tab="stats"]')?.click();
    else if (key === 'd') document.querySelector('#mainTabsBar .tab-btn[data-tab="dashboard"]')?.click();
    else if (key === 'p') document.getElementById('btnPinToDashboard')?.click();
    else if (key === '?') document.getElementById('topbarHelp')?.click();
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
  switchSheet
});
