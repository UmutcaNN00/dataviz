/* ════════════════════════════════════════════════════════════
   DATAVIZ PRO V6 — ENTERPRISE BI & FORECASTING MOTORU
   Multi-Sheet, Slicers, 50 Grafik, Formül Motoru, 
   Gelecek Tahminlemesi, KPI Tiles, Qwen2.5 AI, Executive PDF
════════════════════════════════════════════════════════════ */




document.addEventListener('DOMContentLoaded', () => {

  /* ── 1. UPLOAD & MULTI-SHEET LOGIC ── */
  const step1 = document.getElementById('step1-upload'), step2 = document.getElementById('step2-config'), step3 = document.getElementById('step3-dashboard');
  const mainDropZone = document.getElementById('mainDropZone'), mainFileInput = document.getElementById('mainFileInput');
  const mainUploadStatus = document.getElementById('mainUploadStatus');
  const sheetTabsBar = document.getElementById('sheetTabsBar');
  const sheetTabsList = document.getElementById('sheetTabsList');

  // Sürükle - Bırak (Drag & Drop) Olayları
  ['dragenter', 'dragover'].forEach(name => {
    mainDropZone.addEventListener(name, (e) => {
      e.preventDefault();
      e.stopPropagation();
      mainDropZone.classList.add('dragover');
    });
  });

  ['dragleave', 'dragend'].forEach(name => {
    mainDropZone.addEventListener(name, (e) => {
      e.preventDefault();
      e.stopPropagation();
      mainDropZone.classList.remove('dragover');
    });
  });

  mainDropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    mainDropZone.classList.remove('dragover');
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  // Dosya Seçildiğinde Tetiklenen Olay (label tag üzerinden native açılıyor)
  mainFileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  });

  async function handleFileUpload(file) {
    if (!file) return;
    activeFileName = file.name;
    mainUploadStatus.className = 'status-msg loading';
    mainUploadStatus.textContent = '⏳ Veri analiz ediliyor...';
    mainUploadStatus.style.display = 'block';

    const fd = new FormData(); fd.append('file', file);
    try {
      const res = await fetch('/upload', { method: 'POST', body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);

      numericColumns = data.numeric_columns || [];
      categoricalColumns = data.categorical_columns || [];
      globalColumns = [...categoricalColumns, ...numericColumns];
      calculatedColumns = [];
      activeFilters = [];
      dashboardCharts = [];
      sheetNames = data.sheet_names || [];

      updateDashboardBadge();
      renderActiveFilterChips();
      renderSheetTabs(sheetNames, data.active_sheet);
      
      document.getElementById('s2FileName').textContent = activeFileName;
      const pivotFileEl = document.getElementById('pivotFileName');
      if (pivotFileEl) pivotFileEl.textContent = activeFileName;
      
      // DATA PREP (Check Health)
      const healthRes = await fetch('/check_health');
      const healthData = await healthRes.json();
      
      if(healthData.has_issues) {
        document.getElementById('dpMissingRows').textContent = healthData.missing_rows;
        document.getElementById('dpTotalRows').textContent = healthData.total_rows;
        document.getElementById('dataPrepModal').classList.remove('hidden');
      } else {
        proceedToStep2();
      }
    } catch (err) {
      mainUploadStatus.className = 'status-msg error';
      mainUploadStatus.textContent = `❌ ${err.message}`;
    }
  }

  function renderSheetTabs(sheets, activeSheet) {
    const pivotSheetTabsBar = document.getElementById('pivotSheetTabsBar');
    const pivotSheetTabsList = document.getElementById('pivotSheetTabsList');

    if(!sheets || sheets.length <= 1) {
      if (sheetTabsBar) sheetTabsBar.classList.add('hidden');
      if (pivotSheetTabsBar) pivotSheetTabsBar.classList.add('hidden');
      return;
    }

    if (sheetTabsBar) sheetTabsBar.classList.remove('hidden');
    if (sheetTabsList) sheetTabsList.innerHTML = '';

    if (pivotSheetTabsBar) pivotSheetTabsBar.classList.remove('hidden');
    if (pivotSheetTabsList) pivotSheetTabsList.innerHTML = '';

    sheets.forEach(s => {
      const btn = document.createElement('button');
      btn.className = `sheet-tab-btn ${s === activeSheet ? 'active' : ''}`;
      btn.textContent = s;
      btn.addEventListener('click', () => switchSheet(s));
      if (sheetTabsList) sheetTabsList.appendChild(btn);

      const pBtn = document.createElement('button');
      pBtn.className = `sheet-tab-btn ${s === activeSheet ? 'active' : ''}`;
      pBtn.textContent = s;
      pBtn.addEventListener('click', () => switchSheet(s));
      if (pivotSheetTabsList) pivotSheetTabsList.appendChild(pBtn);
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
      if(!res.ok) throw new Error(data.error);

      numericColumns = data.numeric_columns || [];
      categoricalColumns = data.categorical_columns || [];
      globalColumns = [...categoricalColumns, ...numericColumns];
      calculatedColumns = [];
      activeFilters = [];
      renderActiveFilterChips();
      renderSheetTabs(sheetNames, sheetName);
      initDragDropPool();
      renderChartGrid('all');
    } catch(err) {
      alert("Sayfa değiştirme hatası: " + err.message);
    }
  }

  // DATA PREP MODAL ACTIONS
  document.getElementById('dpSkipBtn')?.addEventListener('click', () => {
    document.getElementById('dataPrepModal')?.classList.add('hidden');
    proceedToStep2();
  });
  
  document.getElementById('dpDropBtn')?.addEventListener('click', () => callCleanData('drop'));
  document.getElementById('dpFillBtn')?.addEventListener('click', () => callCleanData('fill_mean'));

  async function callCleanData(action) {
    const msgEl = document.getElementById('dpMessage');
    const origMsg = msgEl.textContent;
    msgEl.textContent = "⏳ Temizleniyor...";
    try {
      const res = await fetch('/clean_data', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:action}) });
      const data = await res.json();
      if(!res.ok) throw new Error(data.error);
      numericColumns = data.numeric_columns || [];
      categoricalColumns = data.categorical_columns || [];
      globalColumns = [...categoricalColumns, ...numericColumns];
      document.getElementById('dataPrepModal').classList.add('hidden');
      proceedToStep2();
    } catch(err) {
      alert("Hata: " + err.message);
      document.getElementById('dataPrepModal').classList.add('hidden');
      msgEl.textContent = origMsg;
    }
  }

  window.proceedToStep2 = proceedToStep2;
  function proceedToStep2() {
    initDragDropPool();
    renderChartGrid('all');
    showScreen(2);
  }


  /* ── 2. DRAG & DROP POOL (STEP 2) ── */
  let currentPoolFilter = 'all';
  let currentPoolSearch = '';

  function initDragDropPool() {
    const pool = document.getElementById('colPool');
    pool.innerHTML = '';
    axisConfig = { x: null, y: [] };
    document.getElementById('xZone').innerHTML = 'Sütunu Buraya Bırakın';
    document.getElementById('yZone').innerHTML = 'Sütunları Buraya Bırakın';
    
    updatePoolCounts();

    // Sütunları 3 net gruba ayır
    const file1Cols = globalColumns.filter(c => !joinedColumns.includes(c) && !calculatedColumns.includes(c));
    const joinedCols = globalColumns.filter(c => joinedColumns.includes(c));
    const calcCols = globalColumns.filter(c => calculatedColumns.includes(c));

    // Grup 1: Ana Dosya Sütunları
    renderPoolSection(pool, '📁 1. Dosya Sütunları', file1Cols, 'section_file1');

    // Grup 2: 2. Dosyadan Birleştirilen Sütunlar (Varsa)
    if (joinedCols.length > 0) {
      renderPoolSection(pool, '🔗 2. Dosya Sütunları (VLOOKUP)', joinedCols, 'section_joined');
    }

    // Grup 3: Özel Formül Sütunları (Varsa)
    if (calcCols.length > 0) {
      renderPoolSection(pool, '🧮 Hesaplanmış Formül Sütunları', calcCols, 'section_calc');
    }

    applyPoolFilterAndSearch();
  }

  function renderPoolSection(parentContainer, titleText, cols, sectionId) {
    if (!cols.length) return;

    const group = document.createElement('div');
    group.className = 'pool-section-group';
    group.id = sectionId;

    group.innerHTML = `
      <div class="pool-section-title">
        <span>${titleText}</span>
        <span style="font-size:0.7rem; font-weight:700; color:var(--muted);">${cols.length} Sütun</span>
      </div>
      <div class="pool-section-pills" id="pills_${sectionId}"></div>
    `;

    const pillsBox = group.querySelector('.pool-section-pills');

    // Kategorik önce, Sayısal sonra sırala
    const sorted = [...cols].sort((a, b) => {
      const aNum = numericColumns.includes(a) ? 1 : 0;
      const bNum = numericColumns.includes(b) ? 1 : 0;
      return aNum - bNum;
    });

    sorted.forEach(col => {
      const isNum = numericColumns.includes(col);
      const isCalc = calculatedColumns.includes(col);
      const isJoin = joinedColumns.includes(col);

      const pill = document.createElement('div');
      pill.className = `col-pill ${isCalc ? 'calc-pill' : ''} ${isJoin ? 'join-pill' : ''}`;
      pill.draggable = true;
      pill.dataset.col = col;
      pill.dataset.type = isNum ? 'num' : 'cat';
      pill.dataset.origin = isJoin ? 'joined' : (isCalc ? 'calc' : 'file1');
      pill.dataset.section = `pills_${sectionId}`;

      let typeTag = isNum ? '#' : 'T';
      let tagBadge = '';
      if (isJoin) {
        tagBadge = `<span class="join-tag-badge">🔗 Dosya 2</span>`;
      } else if (isCalc) {
        tagBadge = `<span style="color:var(--purple); font-weight:800; font-size:0.75rem; margin-right:2px;">fx</span>`;
      }

      pill.innerHTML = `${tagBadge}<span style="opacity:0.65; font-size:0.75rem; font-weight:800;">${typeTag}</span> <span>${col}</span>
                        <div class="pill-remove">×</div>`;

      pill.addEventListener('dragstart', (e) => {
        pill.classList.add('dragging');
        e.dataTransfer.setData('text/plain', col);
      });
      pill.addEventListener('dragend', () => pill.classList.remove('dragging'));
      
      // Part 3: Tıklama ile hızlı atama
      pill.addEventListener('click', (e) => {
        // Zaten eksendeyse tıklamayı yok say
        if (pill.classList.contains('in-zone')) return;
        
        const xZone = document.getElementById('xZone');
        if (!xZone.querySelector('.col-pill')) {
          assignPillToZone(col, 'xZone');
        } else {
          assignPillToZone(col, 'yZone');
        }
      });

      pill.querySelector('.pill-remove').addEventListener('click', (e) => {
        e.stopPropagation();
        const parentZone = pill.parentElement;
        const originSection = document.getElementById(pill.dataset.section) || pool;
        originSection.appendChild(pill);
        pill.classList.remove('in-zone');
        updateAxisConfig();
        if(parentZone) restoreZonePlaceholder(parentZone);
      });

      pillsBox.appendChild(pill);
    });

    parentContainer.appendChild(group);
  }

  function updatePoolCounts() {
    const total = globalColumns.length;
    const catCount = categoricalColumns.length;
    const numCount = numericColumns.length;
    const joinedCount = joinedColumns.length;

    const b = document.getElementById('poolCountBadge');
    if (b) b.textContent = `${total} Sütun`;
    const pAll = document.getElementById('pfcAllCount');
    if (pAll) pAll.textContent = total;
    const pCat = document.getElementById('pfcCatCount');
    if (pCat) pCat.textContent = catCount;
    const pNum = document.getElementById('pfcNumCount');
    if (pNum) pNum.textContent = numCount;

    const jBtn = document.getElementById('pfcJoinedBtn');
    if (jBtn) {
      if (joinedCount > 0) {
        jBtn.classList.remove('hidden');
        document.getElementById('pfcJoinedCount').textContent = joinedCount;
      } else {
        jBtn.classList.add('hidden');
      }
    }
  }

  // Havuz Arama & Kategori Filtreleme
  document.getElementById('poolSearchInput')?.addEventListener('input', (e) => {
    currentPoolSearch = e.target.value.toLowerCase().trim();
    applyPoolFilterAndSearch();
  });

  document.querySelectorAll('.pfc-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.pfc-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentPoolFilter = btn.dataset.pfilter;
      applyPoolFilterAndSearch();
    });
  });

  function applyPoolFilterAndSearch() {
    document.querySelectorAll('.col-pill').forEach(pill => {
      if (pill.classList.contains('in-zone')) return;

      const colName = pill.dataset.col.toLowerCase();
      const colType = pill.dataset.type;
      const origin = pill.dataset.origin;

      const matchesSearch = !currentPoolSearch || colName.includes(currentPoolSearch);

      let matchesFilter = true;
      if (currentPoolFilter === 'cat') matchesFilter = colType === 'cat';
      else if (currentPoolFilter === 'num') matchesFilter = colType === 'num';
      else if (currentPoolFilter === 'joined') matchesFilter = origin === 'joined';

      pill.style.display = (matchesSearch && matchesFilter) ? 'inline-flex' : 'none';
    });

    document.querySelectorAll('.pool-section-group').forEach(group => {
      const allPills = group.querySelectorAll('.col-pill:not(.in-zone)');
      let hasVisible = false;
      allPills.forEach(p => { if (p.style.display !== 'none') hasVisible = true; });
      group.style.display = hasVisible ? 'block' : 'none';
    });
  }

  document.querySelectorAll('.dd-zone').forEach(zone => {
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', e => {
      e.preventDefault(); zone.classList.remove('dragover');
      const colName = e.dataTransfer.getData('text/plain');
      assignPillToZone(colName, zone.id);
    });
  });

  function returnPillToPool(pill) {
    if(!pill) return;
    pill.classList.remove('in-zone');
    // Determine which section this pill belongs to
    const isCalc = pill.classList.contains('calc-pill');
    const isJoin = pill.classList.contains('join-pill');
    let section;
    if(isCalc) section = document.getElementById('pills_section_calc');
    else if(isJoin) section = document.getElementById('pills_section_joined');
    else section = document.getElementById('pills_section_file1');
    if(section) section.appendChild(pill);
    else document.getElementById('colPool').appendChild(pill);
  }

  function restoreZonePlaceholder(zone) {
    if(zone.id === 'xZone' && !zone.querySelector('.col-pill')) {
      zone.innerHTML = '<span class="zone-placeholder">Kategori sütununu buraya bırakın</span>';
    } else if(zone.id === 'yZone' && !zone.querySelector('.col-pill')) {
      zone.innerHTML = '<span class="zone-placeholder">Değer sütunlarını buraya bırakın</span>';
    }
  }

  function assignPillToZone(colName, zoneId) {
    const pill = document.querySelector(`.col-pill[data-col="${colName}"]`);
    if(!pill) return;
    const zone = document.getElementById(zoneId);

    if(zoneId === 'xZone') {
      const existing = zone.querySelector('.col-pill');
      if(existing) returnPillToPool(existing);
      zone.innerHTML = ''; 
    }
    
    if(zone.innerText.includes('Bırakın') || zone.innerText.includes('bırakın')) zone.innerHTML = '';
    zone.appendChild(pill);
    pill.classList.add('in-zone');
    updateAxisConfig();
  }

  function updateAxisConfig() {
    const xPill = document.getElementById('xZone').querySelector('.col-pill');
    axisConfig.x = xPill ? xPill.dataset.col : null;

    const yPills = document.getElementById('yZone').querySelectorAll('.col-pill');
    axisConfig.y = Array.from(yPills).map(p => p.dataset.col);

    evaluateCharts();
  }


  /* ── 3. FORMÜL & YENİ SÜTUN SİHİRBAZI ── */
  const calcColModal = document.getElementById('calcColModal');
  const calcCol1Select = document.getElementById('calcCol1Select');
  const calcCol2Select = document.getElementById('calcCol2Select');
  const calcScalarInput = document.getElementById('calcScalarInput');
  const calcUseScalar = document.getElementById('calcUseScalar');
  const calcNewColName = document.getElementById('calcNewColName');
  let selectedCalcOp = '+';

  document.getElementById('btnOpenCalcModal')?.addEventListener('click', () => {
    calcCol1Select.innerHTML = '';
    calcCol2Select.innerHTML = '';
    numericColumns.forEach(c => {
      calcCol1Select.innerHTML += `<option value="${c}">${c}</option>`;
      calcCol2Select.innerHTML += `<option value="${c}">${c}</option>`;
    });
    calcNewColName.value = '';
    calcScalarInput.value = '';
    calcUseScalar.checked = false;
    calcCol2Select.classList.remove('hidden');
    calcScalarInput.classList.add('hidden');
    calcColModal.classList.remove('hidden');
  });

  document.getElementById('btnCloseCalcModal')?.addEventListener('click', () => calcColModal.classList.add('hidden'));
  document.getElementById('btnCancelCalc')?.addEventListener('click', () => calcColModal.classList.add('hidden'));

  document.querySelectorAll('.op-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.op-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedCalcOp = btn.dataset.op;
    });
  });

  calcUseScalar.addEventListener('change', (e) => {
    if(e.target.checked) {
      calcCol2Select.classList.add('hidden');
      calcScalarInput.classList.remove('hidden');
    } else {
      calcCol2Select.classList.remove('hidden');
      calcScalarInput.classList.add('hidden');
    }
  });

  document.getElementById('btnExecuteCalc')?.addEventListener('click', async () => {
    const newName = calcNewColName.value.trim();
    if(!newName) { alert("Lütfen yeni sütun için bir isim girin."); return; }

    const payload = {
      new_column_name: newName,
      col1: calcCol1Select.value,
      operator: selectedCalcOp,
      col2: calcUseScalar.checked ? null : calcCol2Select.value,
      scalar: calcUseScalar.checked ? parseFloat(calcScalarInput.value) : null
    };

    try {
      const res = await fetch('/create_calculated_column', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if(!res.ok) throw new Error(data.error);

      numericColumns = data.numeric_columns || [];
      categoricalColumns = data.categorical_columns || [];
      globalColumns = [...categoricalColumns, ...numericColumns];
      calculatedColumns.push(data.new_column);

      calcColModal.classList.add('hidden');
      initDragDropPool();
    } catch(err) {
      alert("Hesaplama başarısız: " + err.message);
    }
  });


  /* ── 4. AKILLI VERİ BİRLEŞTİRİCİ (DATA JOINER / VLOOKUP) ── */
  const dataMergeModal = document.getElementById('dataMergeModal');
  const mergeFileInput = document.getElementById('mergeFileInput');
  const mergeDropZone = document.getElementById('mergeDropZone');
  const mergeFileStatus = document.getElementById('mergeFileStatus');
  const mergeConfigArea = document.getElementById('mergeConfigArea');
  const mergeKey1Select = document.getElementById('mergeKey1Select');
  const mergeKey2Select = document.getElementById('mergeKey2Select');
  const mergeJoinType = document.getElementById('mergeJoinType');
  const btnExecuteMerge = document.getElementById('btnExecuteMerge');
  let selectedFile2 = null;

  document.getElementById('btnOpenMergeModal')?.addEventListener('click', () => {
    selectedFile2 = null;
    mergeFileInput.value = '';
    mergeFileStatus.style.display = 'none';
    mergeConfigArea.classList.add('hidden');
    btnExecuteMerge.disabled = true;
    dataMergeModal.classList.remove('hidden');
  });

  document.getElementById('btnCloseMergeModal')?.addEventListener('click', () => dataMergeModal.classList.add('hidden'));
  document.getElementById('btnCancelMerge')?.addEventListener('click', () => dataMergeModal.classList.add('hidden'));

  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(name => {
    mergeDropZone?.addEventListener(name, (e) => { e.preventDefault(); e.stopPropagation(); });
  });
  mergeDropZone?.addEventListener('dragover', () => mergeDropZone.classList.add('dragover'));
  mergeDropZone?.addEventListener('dragleave', () => mergeDropZone.classList.remove('dragover'));
  mergeDropZone?.addEventListener('drop', (e) => {
    mergeDropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) handleSecondFileSelect(e.dataTransfer.files[0]);
  });
  mergeDropZone?.addEventListener('click', (e) => {
    if (e.target !== mergeFileInput) mergeFileInput.click();
  });
  mergeFileInput?.addEventListener('change', (e) => {
    if (e.target.files[0]) handleSecondFileSelect(e.target.files[0]);
  });

  async function handleSecondFileSelect(file) {
    if (!file) return;
    selectedFile2 = file;
    mergeFileStatus.style.display = 'block';
    mergeFileStatus.className = 'status-msg loading';
    mergeFileStatus.textContent = '⏳ 2. dosya taranıyor ve ortak sütunlar aranıyor...';

    const fd = new FormData();
    fd.append('file2', file);

    try {
      const res = await fetch('/preview_second_file', { method: 'POST', body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);

      mergeFileStatus.className = 'status-msg success';
      mergeFileStatus.textContent = `✓ ${data.file2_name} (${data.file2_rows} satır, ${data.cols2.length} sütun)`;

      mergeKey1Select.innerHTML = '';
      data.cols1.forEach(c => {
        mergeKey1Select.innerHTML += `<option value="${c}" ${c === data.auto_key1 ? 'selected' : ''}>${c}</option>`;
      });

      mergeKey2Select.innerHTML = '';
      data.cols2.forEach(c => {
        mergeKey2Select.innerHTML += `<option value="${c}" ${c === data.auto_key2 ? 'selected' : ''}>${c}</option>`;
      });

      mergeConfigArea.classList.remove('hidden');
      btnExecuteMerge.disabled = false;
    } catch(err) {
      mergeFileStatus.className = 'status-msg error';
      mergeFileStatus.textContent = `❌ ${err.message}`;
    }
  }

  btnExecuteMerge?.addEventListener('click', async () => {
    if (!selectedFile2) return;

    btnExecuteMerge.disabled = true;
    btnExecuteMerge.textContent = '⏳ Birleştiriliyor...';

    const fd = new FormData();
    fd.append('file2', selectedFile2);
    fd.append('key1', mergeKey1Select.value);
    fd.append('key2', mergeKey2Select.value);
    fd.append('join_type', mergeJoinType.value);

    try {
      const res = await fetch('/merge_datasets', { method: 'POST', body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);

      numericColumns = data.numeric_columns || [];
      categoricalColumns = data.categorical_columns || [];
      globalColumns = [...categoricalColumns, ...numericColumns];
      
      (data.new_joined_columns || []).forEach(c => {
        if (!joinedColumns.includes(c)) joinedColumns.push(c);
      });

      activeFilters = [];
      if (typeof renderActiveFilterChips === 'function') renderActiveFilterChips();

      dataMergeModal.classList.add('hidden');
      initDragDropPool();

      alert(`🎉 2. dosya başarıyla birleştirildi!\nToplam: ${data.total_rows} satır, ${data.total_cols} sütun.\nEklenen yeni sütunlar veri havuzunda '🔗' ikonu ile gösterilmektedir.`);
    } catch(err) {
      alert("Birleştirme başarısız: " + err.message);
    }

    btnExecuteMerge.disabled = false;
    btnExecuteMerge.textContent = '⚡ Dosyaları Birleştir';
  });


  /* ── 4. MAGIC TEMPLATES ── */
  document.querySelectorAll('.magic-btn[data-tpl]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const tpl = e.target.dataset.tpl;
      initDragDropPool();
      
      let xMatch = null;
      let yMatch = null;
      
      if(tpl === 'sales') {
        xMatch = globalColumns.find(c => /tarih|date|zaman|ay|yıl|gün/i.test(c)) || categoricalColumns[0];
        yMatch = globalColumns.find(c => /satış|tutar|fiyat|gelir|price|sales/i.test(c)) || numericColumns[0];
      } else if (tpl === 'hr') {
        xMatch = globalColumns.find(c => /departman|bölüm|pozisyon|unvan|dept/i.test(c)) || categoricalColumns[0];
        yMatch = globalColumns.find(c => /maaş|ücret|çalışan|salary|pay/i.test(c)) || numericColumns[0];
      } else if (tpl === 'finance') {
        xMatch = globalColumns.find(c => /tarih|date|zaman/i.test(c)) || categoricalColumns[0];
        yMatch = globalColumns.find(c => /kapanış|açılış|fiyat|close|open/i.test(c)) || numericColumns[0];
      }

      if(xMatch) assignPillToZone(xMatch, 'xZone');
      if(yMatch) assignPillToZone(yMatch, 'yZone');
      
      if(xMatch && yMatch) {
        setTimeout(() => {
           if(tpl === 'finance' && document.querySelector('.chart-card[data-id="candlestick"]')) goToStep3('line', 'Çizgi');
           else goToStep3('bar', 'Çubuk');
        }, 600);
      }
    });
  });


  /* ── 5. 50 CHART GRID ENGINE ── */
  const grid = document.getElementById('s2ChartGrid');
  const filters = document.getElementById('chartFilters');

  function renderChartGrid(filterCat) {
    if (!grid) return; // guard: element may not exist yet
    grid.innerHTML = '';
    CHARTS.forEach(ch => {
      if (filterCat !== 'all' && ch.cat !== filterCat) return;
      const card = document.createElement('div');
      card.className = 'chart-card disabled';
      card.tabIndex = 0;
      card.role = 'button'; 
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
      card.addEventListener('click', () => {
        if(card.classList.contains('disabled')) return;
        goToStep3(ch.id, ch.name);
      });
      card.addEventListener('keydown', e => {
        if (!card.classList.contains('disabled') && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          goToStep3(ch.id, ch.name);
        }
      });
      grid.appendChild(card);
    });
    evaluateCharts();
  }

  filters.addEventListener('click', (e) => {
    if(e.target.tagName !== 'BUTTON') return;
    filters.querySelectorAll('button').forEach(b => b.classList.remove('active'));
    e.target.classList.add('active');
    renderChartGrid(e.target.dataset.filter);
  });

  function evaluateCharts() {
    const hasX = !!axisConfig.x;
    const yCount = axisConfig.y.length;
    const yAllNum = axisConfig.y.every(col => numericColumns.includes(col));
    const warning = document.getElementById('axisWarning');
    if (warning) warning.classList.add('hidden');

    if (!hasX && yCount === 0) {
      document.querySelectorAll('.chart-card').forEach(c => c.className = 'chart-card disabled');
      return;
    }

    let rec = [], dis = [];

    const isXDate = hasX && /tarih|date|zaman|ay|yıl|gün/i.test(axisConfig.x);
    const isXNum = hasX && numericColumns.includes(axisConfig.x);

    if (hasX) {
      if (yCount === 0) {
        // Yalnızca X seçili: Dağılım ve parça grafikleri
        rec = ['histogram', 'bar', 'horizontalbar'];
        if (!isXNum) rec.push('pie', 'donut');
        dis = ['scatter', 'bubble', 'scatter3d', 'line3d', 'surface', 'heatmap', 'candlestick', 'ohlc', 'line', 'area'];
      } else if (yCount === 1) {
        if (isXDate) {
          rec = ['line', 'spline', 'step', 'area', 'bar', 'candlestick', 'ohlc'];
          dis = ['pie', 'donut', 'sunburst', 'radar'];
        } else if (isXNum) {
          rec = ['scatter', 'line', 'bar', 'histogram', 'bubble'];
          dis = ['pie', 'donut', 'sunburst', 'treemap', 'funnel'];
        } else {
          // X kategorik
          rec = ['bar', 'horizontalbar', 'pie', 'donut', 'treemap', 'funnel'];
          dis = ['line', 'spline', 'area', 'candlestick', 'ohlc'];
        }
      } else if (yCount >= 2) {
        if (isXDate) {
          rec = ['line', 'spline', 'stackedarea', 'groupedbar', 'stackedbar', 'candlestick', 'ohlc'];
          dis = ['pie', 'donut', 'funnelarea', 'scatter3d'];
        } else if (isXNum) {
          rec = ['scatter', 'bubble', 'scatter3d', 'line3d', 'surface', 'contour'];
          dis = ['pie', 'donut', 'funnelarea', 'treemap'];
        } else {
          rec = ['groupedbar', 'stackedbar', 'heatmap', 'parcats'];
          dis = ['pie', 'donut', 'funnelarea', 'line3d', 'surface'];
        }
      }
    } else {
      // X yok, Sadece Y ekseni seçili
      if (yCount === 1) {
        rec = ['histogram', 'box', 'violin', 'strip', 'rug'];
        dis = ['pie', 'donut', 'sunburst', 'treemap', 'bar', 'line', 'scatter'];
      } else if (yCount >= 2) {
        rec = ['scatter', 'bubble', 'density2d', 'histogram2d', 'heatmap', 'scattermatrix', 'parcoords'];
        dis = ['pie', 'donut', 'funnelarea', 'bar', 'line'];
      }
    }

    document.querySelectorAll('.chart-card').forEach(card => {
      const id = card.dataset.id;
      card.className = 'chart-card';
      card.tabIndex = 0;
      card.role = 'button';
      if (dis.includes(id)) card.classList.add('disabled');
      else if (rec.includes(id)) card.classList.add('recommended');
    });

    if (!yAllNum && yCount > 0 && warning) {
      warning.textContent = "Uyarı: Y Ekseninde Metinsel (Kategorik) sütun seçtiniz. Sayısal grafikler otomatik adet sayımı ile gösterilebilir.";
      warning.classList.remove('hidden');
    }
  }


  /* ── 6. STEP 3 & PLOTLY ENGINE (50 GRAFİK DESTEĞİ) ── */
  let currentPlotType = '';
  const chartArea = document.getElementById('chartArea');
  
  const resizeObserver = new ResizeObserver(() => {
    if (step3.classList.contains('active')) {
      try { Plotly.Plots.resize('chartArea'); } catch(e){}
    }
  });
  resizeObserver.observe(document.getElementById('chartAreaContainer'));

  async function goToStep3(chartId, chartName) {
    showScreen(3);
    currentPlotType = chartId;
    document.getElementById('currentChartTypeName').textContent = chartName;
    chartArea.innerHTML = ''; document.getElementById('chartAreaContainer').insertAdjacentHTML('beforeend', '<div id="megaChartLoader" class="chart-loading-spinner" style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%);"> <div class="spinner"></div><p>Mega Motor Ciziyor...</p></div>');
    
    // Reset AI Insight
    currentAiInsight = '';
    document.getElementById('aiResponseContainer').classList.add('hidden');
    document.getElementById('aiResponseContent').innerHTML = '';
    
    // Reset Pin Button
    const pinBtn = document.getElementById('btnPinToDashboard');
    pinBtn.classList.remove('pinned');
    pinBtn.innerHTML = '<span>📌</span> Panoya Ekle';

    await refreshActiveChart();
    fetchKpis();
  }

  async function refreshActiveChart() {
    if (!currentPlotType) return;
    
    // Part 3: Akıllı Metin Kurtarma (Smart Text Recovery)
    const aggFuncSelect = document.getElementById('s2AggFunc');
    if (axisConfig.y && axisConfig.y.length > 0) {
      const hasCategoricalY = axisConfig.y.some(col => categoricalColumns.includes(col));
      if (hasCategoricalY && aggFuncSelect.value !== 'count') {
        aggFuncSelect.value = 'count';
        console.warn('Metinsel sütun Y eksenine eklendiği için Toplulaştırma metodu Say (Count) olarak değiştirildi.');
        // Kısa süreliğine kullanıcıyı uyaracak bir class ekleyip çıkarabiliriz
        aggFuncSelect.style.outline = '2px solid var(--purple)';
        setTimeout(() => aggFuncSelect.style.outline = 'none', 1500);
      }
    }

    const isForecastEnabled = document.getElementById('enableForecast')?.checked || false;
    const forecastSteps = isForecastEnabled ? parseInt(document.getElementById('forecastStepsSelect').value) : 0;

    const reqBody = { 
      x_col: axisConfig.x, 
      y_cols: axisConfig.y, 
      agg_func: document.getElementById('s2AggFunc').value, 
      chart_type: currentPlotType,
      filters: activeFilters,
      forecast_steps: forecastSteps
    };

    try {
      const res = await fetch('/get_chart_data', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(reqBody) });
      const data = await res.json();
      if(!res.ok) throw new Error(data.error);
      
      currentChartData = data;
      drawMegaPlotly('chartArea', data, currentPlotType); const loader = document.getElementById('megaChartLoader'); if(loader) loader.remove();
      
      let statCols = axisConfig.y.filter(c => numericColumns.includes(c));
      if(!statCols.length) statCols = numericColumns.slice(0, 6);
      fetchStats(statCols);

      // Tahmin Bilgi Kutusu
      const fBox = document.getElementById('forecastInfoBox');
      if (data.forecast && fBox) {
        fBox.classList.remove('hidden');
        document.getElementById('forecastR2Val').textContent = `%${(data.forecast.r2 * 100).toFixed(1)}`;
      } else if(fBox) {
        fBox.classList.add('hidden');
      }

    } catch(err) {
      chartArea.innerHTML = `<div style="color:var(--red); padding:40px; text-align:center;">❌ Hata:<br>${err.message}</div>`;
    }
  }

  function drawMegaPlotly(targetElementId, data, type, isMini = false) {
    const mainColor = document.getElementById('chartColor').value;
    const bg = document.getElementById('chartBgColor').value;
    const sGrid = document.getElementById('showGrid').checked;
    const sLeg = isMini ? false : document.getElementById('showLegend').checked;
    const sz = parseInt(document.getElementById('traceSize').value);

    let traces = [];
    const layout = buildLayout(bg, sGrid, sLeg, isMini);
    if (!isMini) {
      layout.xaxis.title.text = document.getElementById('customXTitle').value || axisConfig.x || '';
      layout.yaxis.title.text = document.getElementById('customYTitle').value || (axisConfig.y.length ? axisConfig.y.join(', ') : '');
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
          traces.push({
            type: 'parcoords',
            dimensions: keys.map(k => ({ label: k, values: raw[k] }))
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
          const openVals = keys[1] ? raw[keys[1]] : y0.map(v => v * 0.98);
          const highVals = keys[2] ? raw[keys[2]] : y0.map(v => v * 1.03);
          const lowVals = keys[3] ? raw[keys[3]] : y0.map(v => v * 0.95);
          const closeVals = y0;

          traces.push({
            type: type,
            x: xVals.length ? xVals : Array.from({length: y0.length}, (_, i) => i + 1),
            open: openVals, high: highVals, low: lowVals, close: closeVals
          });
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
        // Scatter, Bubble, Geo
        else if (['scatter', 'bubble', 'scattergeo'].includes(type)) {
          keys.forEach((k, i) => {
            traces.push({
              type: type === 'scattergeo' ? 'scattergeo' : 'scatter', mode: 'markers', name: k,
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

        // Pie, Donut, Sunburst, Treemap, FunnelArea, Icicle
        if (['pie', 'donut', 'funnelarea', 'sunburst', 'treemap', 'icicle'].includes(type)) {
          const k = keys[0];
          if (k) {
            traces.push({
              type: ['sunburst', 'treemap', 'icicle'].includes(type) ? type : (type === 'funnelarea' ? 'funnelarea' : 'pie'),
              labels: ['sunburst', 'treemap', 'icicle'].includes(type) ? xVals : undefined,
              parents: ['sunburst', 'treemap', 'icicle'].includes(type) ? xVals.map(() => "") : undefined,
              [type === 'funnelarea' ? 'text' : 'labels']: xVals,
              values: agg[k],
              hole: type === 'donut' ? 0.5 : 0,
              marker: { colors: PALETTE }
            });
            layout.xaxis.visible = false; layout.yaxis.visible = false;
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

        // 🔮 GELECEK TAHMİNİ TRACE EKLEME
        if (data.forecast) {
          const fc = data.forecast;
          
          if (!isMini) {
            traces.push({
              type: 'scatter', mode: 'lines', name: 'Güven Bandı (%95 Alt)',
              x: fc.x, y: fc.lower, line: { color: 'transparent' }, showlegend: false, hoverinfo: 'none'
            });
            traces.push({
              type: 'scatter', mode: 'lines', name: 'Güven Bandı (%95)',
              x: fc.x, y: fc.upper, fill: 'tonexty', fillcolor: 'rgba(244,114,182,0.15)',
              line: { color: 'transparent' }, showlegend: false, hoverinfo: 'none'
            });
          }

          traces.push({
            type: 'scatter', mode: 'lines+markers', name: `🔮 Gelecek Tahmini (${fc.target_y})`,
            x: fc.x, y: fc.y,
            line: { dash: 'dot', color: '#f472b6', width: 3 },
            marker: { size: isMini ? 4 : 7, color: '#f472b6' }
          });
        }
      }

      Plotly.newPlot(targetElementId, traces, layout, { responsive: true, displayModeBar: !isMini, displaylogo: false });

    } catch(err) {
      document.getElementById(targetElementId).innerHTML = `<div style="color:var(--red); padding:20px; font-size:0.85rem;">❌ Çizim Hatası: ${err.message}</div>`;
    }
  }

  function buildLayout(bg, sGrid, sLeg, isMini = false) {
    const gc = sGrid ? 'rgba(255,255,255,0.08)' : 'transparent';
    const tc = '#94a3b8';
    return {
      autosize: true, paper_bgcolor: 'transparent', plot_bgcolor: bg, font: { family: 'Inter', color: tc }, showlegend: sLeg,
      legend: { bgcolor: 'transparent' }, margin: isMini ? { t:15, r:15, b:25, l:35 } : { t:30, r:30, b:50, l:50 },
      xaxis: { gridcolor: gc, zeroline: false, title: { text:'' } }, yaxis: { gridcolor: gc, zeroline: false, title: { text:'' } },
      polar: { angularaxis: { gridcolor: gc }, radialaxis: { gridcolor: gc } }
    };
  }

  // Tahmin Anahtarı Listener
  document.getElementById('enableForecast')?.addEventListener('change', refreshActiveChart);
  document.getElementById('forecastStepsSelect')?.addEventListener('change', () => {
    if(document.getElementById('enableForecast')?.checked) refreshActiveChart();
  });


  /* ── 7. AKILLI FİLTRELEME / SLICERS SİSTEMİ ── */
  const filterModal = document.getElementById('filterModal');
  const filterColumnSelect = document.getElementById('filterColumnSelect');
  const filterDynamicContainer = document.getElementById('filterDynamicContainer');
  const catFilterArea = document.getElementById('catFilterArea');
  const numFilterArea = document.getElementById('numFilterArea');
  const catCheckboxesList = document.getElementById('catCheckboxesList');
  const catSearchInput = document.getElementById('catSearchInput');
  const numFilterMin = document.getElementById('numFilterMin');
  const numFilterMax = document.getElementById('numFilterMax');

  let currentEditingFilter = null;

  function openFilterModal() {
    filterColumnSelect.innerHTML = '<option value="" disabled selected>Bir sütun seçin...</option>';
    globalColumns.forEach(c => {
      const isNum = numericColumns.includes(c);
      filterColumnSelect.innerHTML += `<option value="${c}">${isNum ? '# (Sayısal)' : 'T (Metin)'}: ${c}</option>`;
    });
    filterDynamicContainer.classList.add('hidden');
    catFilterArea.classList.add('hidden');
    numFilterArea.classList.add('hidden');
    filterModal.classList.remove('hidden');
  }

  document.getElementById('btnOpenFilterModalS2')?.addEventListener('click', openFilterModal);
  document.getElementById('btnOpenFilterModalS3')?.addEventListener('click', openFilterModal);
  document.getElementById('btnOpenFilterModalPivot')?.addEventListener('click', openFilterModal);
  document.getElementById('btnCloseFilterModal')?.addEventListener('click', () => filterModal.classList.add('hidden'));
  document.getElementById('btnCancelFilter')?.addEventListener('click', () => filterModal.classList.add('hidden'));

  filterColumnSelect.addEventListener('change', async () => {
    const colName = filterColumnSelect.value;
    if(!colName) return;

    try {
      const res = await fetch('/get_column_details', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ column: colName })
      });
      const data = await res.json();
      if(!res.ok) throw new Error(data.error);

      currentEditingFilter = data;
      filterDynamicContainer.classList.remove('hidden');

      if(data.type === 'cat') {
        numFilterArea.classList.add('hidden');
        catFilterArea.classList.remove('hidden');
        renderCatCheckboxes(data.categories);
      } else {
        catFilterArea.classList.add('hidden');
        numFilterArea.classList.remove('hidden');
        numFilterMin.value = data.min;
        numFilterMin.min = data.min;
        numFilterMin.max = data.max;
        numFilterMax.value = data.max;
        numFilterMax.min = data.min;
        numFilterMax.max = data.max;
      }
    } catch(err) {
      alert("Sütun detayları alınamadı: " + err.message);
    }
  });

  function renderCatCheckboxes(categories) {
    let htmlContent = '';
    categories.forEach((item) => {
      htmlContent += `
        <label class="cat-checkbox-item">
          <input type="checkbox" value="${item.value}" checked class="cat-chk">
          <span style="flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${item.value}</span>
          <span style="color:var(--muted); font-size:0.75rem;">(${item.count})</span>
        </label>
      `;
    });
    catCheckboxesList.innerHTML = htmlContent;
  }

  catSearchInput.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    document.querySelectorAll('.cat-checkbox-item').forEach(item => {
      const text = item.textContent.toLowerCase();
      item.style.display = text.includes(q) ? 'flex' : 'none';
    });
  });

  document.getElementById('btnSelectAllCat')?.addEventListener('click', () => {
    document.querySelectorAll('.cat-chk').forEach(c => c.checked = true);
  });
  document.getElementById('btnClearAllCat')?.addEventListener('click', () => {
    document.querySelectorAll('.cat-chk').forEach(c => c.checked = false);
  });

  document.getElementById('btnApplyFilter')?.addEventListener('click', () => {
    if(!currentEditingFilter) return;

    const col = currentEditingFilter.column;
    activeFilters = activeFilters.filter(f => f.column !== col);

    if(currentEditingFilter.type === 'cat') {
      const selectedVals = Array.from(document.querySelectorAll('.cat-chk:checked')).map(c => c.value);
      if(selectedVals.length < currentEditingFilter.categories.length) {
        activeFilters.push({ column: col, type: 'cat', values: selectedVals });
      }
    } else {
      const minVal = parseFloat(numFilterMin.value);
      const maxVal = parseFloat(numFilterMax.value);
      if(minVal > currentEditingFilter.min || maxVal < currentEditingFilter.max) {
        activeFilters.push({ column: col, type: 'num', min: minVal, max: maxVal });
      }
    }

    filterModal.classList.add('hidden');
    renderActiveFilterChips();
    
    if(step3.classList.contains('active')) {
      refreshActiveChart();
      fetchKpis();
    }
    if(screenPivotStudio && screenPivotStudio.classList.contains('active')) {
      refreshPivotStudio();
    }
  });

  function renderActiveFilterChips() {
    const s2List = document.getElementById('s2ActiveFiltersList');
    const s3List = document.getElementById('s3ActiveFiltersList');
    const pivotList = document.getElementById('pivotActiveFiltersList');
    
    if(activeFilters.length === 0) {
      if(s2List) s2List.innerHTML = '<span class="no-filter-hint">Filtre uygulanmadı (Tüm veri aktif)</span>';
      if(s3List) s3List.innerHTML = '<span class="no-filter-hint">Filtre uygulanmadı (Tüm veri aktif)</span>';
      if(pivotList) pivotList.innerHTML = '<span class="no-filter-hint">Filtre uygulanmadı (Tüm veri aktif)</span>';
      return;
    }

    let chipsHtml = '';
    activeFilters.forEach((f, idx) => {
      let desc = '';
      if(f.type === 'cat') desc = `${f.column}: ${f.values.length} değer`;
      else desc = `${f.column}: ${f.min} - ${f.max}`;

      chipsHtml += `
        <div class="filter-chip">
          <span>${desc}</span>
          <span class="filter-chip-remove" data-idx="${idx}" title="Filtreyi kaldır">×</span>
        </div>
      `;
    });

    if(s2List) s2List.innerHTML = chipsHtml;
    if(s3List) s3List.innerHTML = chipsHtml;
    if(pivotList) pivotList.innerHTML = chipsHtml;

    document.querySelectorAll('.filter-chip-remove').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const i = parseInt(e.target.dataset.idx);
        activeFilters.splice(i, 1);
        renderActiveFilterChips();
        if(step3.classList.contains('active')) {
          refreshActiveChart();
          fetchKpis();
        }
        if(screenPivotStudio && screenPivotStudio.classList.contains('active')) {
          refreshPivotStudio();
        }
      });
    });
  }


  /* ── 8. EXECUTIVE KPI ÖZETLERİ ── */
  async function fetchKpis() {
    try {
      const res = await fetch('/get_kpi_summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filters: activeFilters })
      });
      const data = await res.json();
      currentKpis = data.kpis || [];

      renderKpiTiles('dashboardKpiGrid', currentKpis);
      renderKpiTiles('chartKpiStrip', currentKpis);
    } catch(e) {
      console.error('KPI Hatası:', e);
      // alert('KPI verileri alınırken bir hata oluştu: ' + e.message);
    }
  }

  function renderKpiTiles(targetId, kpiList) {
    const container = document.getElementById(targetId);
    if (!container) return;
    container.innerHTML = '';

    kpiList.forEach(k => {
      container.innerHTML += `
        <div class="kpi-tile-card ${k.color}">
          <div class="kpi-tile-header">
            <span class="kpi-tile-title">${k.title}</span>
            <span class="kpi-tile-icon">${k.icon}</span>
          </div>
          <div class="kpi-tile-val">${k.value}</div>
          <div class="kpi-tile-sub">${k.sub}</div>
        </div>
      `;
    });
  }


  /* ── 9. ÇOKLU PANO (DASHBOARD CANVAS) SİSTEMİ ── */
  const btnPinToDashboard = document.getElementById('btnPinToDashboard');
  const dashboardGrid = document.getElementById('dashboardGrid');
  const dashboardEmptyState = document.getElementById('dashboardEmptyState');

  btnPinToDashboard.addEventListener('click', () => {
    if(!currentChartData) return;

    const customMainTitle = document.getElementById('customChartTitle')?.value.trim();
    const xCol = axisConfig.x || '';
    const yCols = axisConfig.y.length ? axisConfig.y.join(', ') : '';
    const typeName = document.getElementById('currentChartTypeName').textContent;
    
    let finalTitle = '';
    if (customMainTitle) {
      finalTitle = customMainTitle;
    } else if (xCol && yCols) {
      finalTitle = `${xCol} bazında ${yCols} (${typeName})`;
    } else if (yCols) {
      finalTitle = `${yCols} (${typeName})`;
    } else {
      finalTitle = `${typeName} Analizi`;
    }

    const dashItem = {
      id: 'dash_' + Date.now(),
      title: finalTitle,
      chartType: currentPlotType,
      data: JSON.parse(JSON.stringify(currentChartData)),
      filtersCount: activeFilters.length
    };

    dashboardCharts.push(dashItem);
    updateDashboardBadge();
    renderDashboardGrid();

    // Visual feedback
    btnPinToDashboard.classList.add('pinned');
    btnPinToDashboard.innerHTML = '<span>✓</span> Panoya Eklendi!';
    setTimeout(() => {
      btnPinToDashboard.innerHTML = '<span>📌</span> Panoya Ekle';
      btnPinToDashboard.classList.remove('pinned');
    }, 2000);
  });

  function updateDashboardBadge() {
    const badge = document.getElementById('dashBadgeCount');
    if(badge) badge.textContent = dashboardCharts.length;
  }

  function renderDashboardGrid() {
    if(!dashboardGrid) return;
    dashboardGrid.innerHTML = '';

    if(dashboardCharts.length === 0) {
      dashboardGrid.appendChild(dashboardEmptyState);
      return;
    }

    const renderSequential = async () => {
      for (let i = 0; i < dashboardCharts.length; i++) {
        const item = dashboardCharts[i];
        const card = document.createElement('div');
        card.className = 'dash-card';
        card.id = `card_${item.id}`;
        card.style.animationDelay = `${i * 0.1}s`;

        card.innerHTML = `
          <div class="dash-card-header">
            <div class="dash-card-title">
              <span>📊</span>
              <span class="dash-title-text" contenteditable="true" data-id="${item.id}" title="Başlığı değiştirmek için tıklayın">${item.title}</span>
              <span class="dash-edit-icon" title="Düzenle">✏️</span>
              ${item.filtersCount > 0 ? `<span class="dash-card-badge">${item.filtersCount} Filtre</span>` : ''}
            </div>
            <div class="dash-card-actions">
              <button class="dash-card-btn btn-delete-dash" data-id="${item.id}" title="Panodan Kaldır">🗑️</button>
            </div>
          </div>
          <div class="dash-card-body" id="plot_${item.id}">
            <div style="text-align:center; padding:20px; color:var(--muted)">Yükleniyor...</div>
          </div>
        `;

        dashboardGrid.appendChild(card);

        // Await a small delay to let DOM breathe
        await new Promise(resolve => requestAnimationFrame(resolve));
        await new Promise(resolve => setTimeout(resolve, 30));

        if (item.chartType === 'pivot') {
          const body = document.getElementById(`plot_${item.id}`);
          body.className = 'dash-card-body dash-pivot-widget';
          
          const p = item.pivotData;
          let tHtml = `<table><thead><tr>`;
          p.index_names.forEach(n => tHtml += `<th>${n}</th>`);
          p.column_headers.forEach(h => tHtml += `<th style="text-align:right;">${h}</th>`);
          tHtml += `</tr></thead><tbody>`;
          p.rows.slice(0, 15).forEach(r => {
            tHtml += `<tr style="${r.is_grand_total ? 'font-weight:bold; background:rgba(52,211,153,0.1); color:var(--green);' : ''}">`;
            r.row_labels.forEach(l => tHtml += `<td style="font-weight:600;">${l}</td>`);
            r.cells.forEach(v => tHtml += `<td style="text-align:right; font-family:monospace;">${v.toLocaleString('tr-TR', {maximumFractionDigits: 0})}</td>`);
            tHtml += `</tr>`;
          });
          tHtml += `</tbody></table>`;
          body.innerHTML = tHtml;
        } else {
          try {
            drawMegaPlotly(`plot_${item.id}`, item.data, item.chartType, true);
          } catch (e) {
            console.error("Dashboard chart render error", e);
            document.getElementById(`plot_${item.id}`).innerHTML = "<div style='padding:20px; color:red; text-align:center;'>Grafik Çizilemedi</div>";
          }
        }
      }
      
      // Setup live editing after rendering
      setupDashboardEvents();
    };

    renderSequential();
  }

  function setupDashboardEvents() {
    // Canlı Başlık Düzenleme
    document.querySelectorAll('.dash-title-text').forEach(titleEl => {
      // Remove old listeners to avoid duplicates
      const newEl = titleEl.cloneNode(true);
      titleEl.parentNode.replaceChild(newEl, titleEl);
      
      newEl.addEventListener('blur', (e) => {
        const id = e.target.dataset.id;
        const newTitle = e.target.innerText.trim();
        const targetItem = dashboardCharts.find(c => c.id === id);
        if (targetItem && newTitle) targetItem.title = newTitle;
      });
      newEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); e.target.blur(); }
      });
    });

    document.querySelectorAll('.btn-delete-dash').forEach(btn => {
      // Avoid duplicate listener issues
      const newBtn = btn.cloneNode(true);
      btn.parentNode.replaceChild(newBtn, btn);
      
      newBtn.addEventListener('click', (e) => {
        const id = e.currentTarget.dataset.id;
        dashboardCharts = dashboardCharts.filter(c => c.id !== id);
        updateDashboardBadge();
        renderDashboardGrid();
        fetchKpis();
      });
    });
  }

  document.getElementById('btnClearDashboard')?.addEventListener('click', () => {
    if(confirm("Panodaki tüm grafikler silinsin mi?")) {
      dashboardCharts = [];
      updateDashboardBadge();
      renderDashboardGrid();
    }
  });

  


/// TÜM PANOYU PDF OLARAK DIŞA AKTARMA (INTERACTIVE A4 STUDIO)
document.getElementById('downloadDashboardPdfBtn')?.addEventListener('click', async () => {
    if(dashboardCharts.length === 0) {
        alert("Panoda henüz dışa aktarılacak bir grafik yok.");
        return;
    }
    
    document.getElementById('pdfStudioModal').classList.remove('hidden');
    const a4Container = document.getElementById('a4Container');
    a4Container.innerHTML = '';
    
    // Create header with Title, Subtitle, Date
    const headerBlock = document.createElement('div');
    headerBlock.className = 'pdf-block';
    headerBlock.style.position = 'relative';
    headerBlock.style.marginBottom = '20px';
    headerBlock.style.padding = '10px';
    headerBlock.innerHTML = `
        <div style="border-bottom: 2px solid var(--blue); padding-bottom: 10px; margin-bottom: 10px;">
            <h1 contenteditable="true" style="margin: 0; font-size: 24px; outline: none;">DataViz Raporu</h1>
            <h3 contenteditable="true" style="margin: 5px 0 0 0; color: #555; font-weight: 500; outline: none;">Aylık Performans Değerlendirmesi</h3>
        </div>
        <p style="margin: 0; font-size: 12px; color: #777; text-align: right;">Tarih: ${new Date().toLocaleDateString('tr-TR')}</p>
        <div class="pdf-block-actions" style="position: absolute; top: -10px; right: 0; display: flex; gap: 5px;">
            <button class="pdf-btn-up">↑</button>
            <button class="pdf-btn-down">↓</button>
            <button class="pdf-btn-del">X</button>
        </div>
    `;
    a4Container.appendChild(headerBlock);

    // KPI Grid Clone
    const kpiGrid = document.getElementById('dashboardKpiGrid');
    if (kpiGrid && kpiGrid.innerHTML.trim() !== '') {
        const kpiBlock = document.createElement('div');
        kpiBlock.className = 'pdf-block';
        kpiBlock.style.position = 'relative';
        kpiBlock.style.marginBottom = '20px';
        kpiBlock.style.padding = '10px';
        kpiBlock.innerHTML = `
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                ${kpiGrid.innerHTML}
            </div>
            <div class="pdf-block-actions" style="position: absolute; top: -10px; right: 0; display: flex; gap: 5px;">
                <button class="pdf-btn-up">↑</button>
                <button class="pdf-btn-down">↓</button>
                <button class="pdf-btn-del">X</button>
            </div>
        `;
        // Adjust KPI styles for white background
        kpiBlock.querySelectorAll('.kpi-tile-card').forEach(card => {
            card.style.background = '#f8fafc';
            card.style.color = 'black';
            card.style.border = '1px solid #ccc';
            card.style.flex = '1';
            card.style.minWidth = '150px';
        });
        kpiBlock.querySelectorAll('p').forEach(p => p.style.color = '#555');
        a4Container.appendChild(kpiBlock);
    }

    // Clone Charts
    for (let i = 0; i < dashboardCharts.length; i++) {
        const item = dashboardCharts[i];
        const divId = `plot_${item.id}`;
        const gd = document.getElementById(divId);
        
        const chartBlock = document.createElement('div');
        chartBlock.className = 'pdf-block';
        chartBlock.style.position = 'relative';
        chartBlock.style.marginBottom = '20px';
        chartBlock.style.padding = '10px';
        chartBlock.style.border = '1px solid #eee';
        chartBlock.style.borderRadius = '8px';
        
        let contentHtml = '';
        if (item.chartType === 'pivot') {
            contentHtml = `
                <h4 contenteditable="true" style="margin:0 0 10px 0; font-size:16px; color:black; border-left:4px solid #10b981; padding-left:10px; outline:none;">${item.title}</h4>
                <div style="overflow-x:auto;">${gd.innerHTML}</div>
            `;
        } else {
            const origLayout = JSON.parse(JSON.stringify(gd.layout || {}));
            const update = {
                paper_bgcolor: '#ffffff',
                plot_bgcolor: '#ffffff',
                'font.color': '#000000',
                'xaxis.gridcolor': 'rgba(0,0,0,0.1)',
                'yaxis.gridcolor': 'rgba(0,0,0,0.1)'
            };
            await Plotly.relayout(gd, update);
            const chartDataUrl = await Plotly.toImage(gd, {format: 'png', width: 700, height: 400});
            await Plotly.relayout(gd, {
                paper_bgcolor: origLayout.paper_bgcolor,
                plot_bgcolor: origLayout.plot_bgcolor,
                'font.color': origLayout.font?.color,
                'xaxis.gridcolor': origLayout.xaxis?.gridcolor,
                'yaxis.gridcolor': origLayout.yaxis?.gridcolor
            });
            contentHtml = `
                <h4 contenteditable="true" style="margin:0 0 10px 0; font-size:16px; color:black; border-left:4px solid #3b82f6; padding-left:10px; outline:none;">${item.title}</h4>
                <img src="${chartDataUrl}" style="width:100%; height:auto; display:block;">
            `;
        }

        chartBlock.innerHTML = `
            ${contentHtml}
            <div class="pdf-block-actions" style="position: absolute; top: -10px; right: 0; display: flex; gap: 5px;">
                <button class="pdf-btn-up">↑</button>
                <button class="pdf-btn-down">↓</button>
                <button class="pdf-btn-del">X</button>
            </div>
        `;
        a4Container.appendChild(chartBlock);
    }
    
    attachPdfBlockEvents();
});

function attachPdfBlockEvents() {
    const a4Container = document.getElementById('a4Container');
    a4Container.querySelectorAll('.pdf-block').forEach(block => {
        const upBtn = block.querySelector('.pdf-btn-up');
        const downBtn = block.querySelector('.pdf-btn-down');
        const delBtn = block.querySelector('.pdf-btn-del');
        
        if (upBtn) upBtn.onclick = () => {
            if (block.previousElementSibling) block.parentNode.insertBefore(block, block.previousElementSibling);
        };
        if (downBtn) downBtn.onclick = () => {
            if (block.nextElementSibling) block.parentNode.insertBefore(block.nextElementSibling, block);
        };
        if (delBtn) delBtn.onclick = () => {
            block.remove();
        };
    });
}

document.getElementById('addTextBtnPdf')?.addEventListener('click', () => {
    const a4Container = document.getElementById('a4Container');
    const textBlock = document.createElement('div');
    textBlock.className = 'pdf-block';
    textBlock.style.position = 'relative';
    textBlock.style.marginBottom = '20px';
    textBlock.style.padding = '10px';
    textBlock.innerHTML = `
        <div contenteditable="true" style="border: 1px dashed gray; padding: 10px; min-height: 50px; outline: none; font-family: sans-serif; font-size: 14px; line-height: 1.5;">Buraya yorumunuzu yazın...</div>
        <div class="pdf-block-actions" style="position: absolute; top: -10px; right: 0; display: flex; gap: 5px;">
            <button class="pdf-btn-up">↑</button>
            <button class="pdf-btn-down">↓</button>
            <button class="pdf-btn-del">X</button>
        </div>
    `;
    a4Container.appendChild(textBlock);
    attachPdfBlockEvents();
});

document.getElementById('closePdfStudioBtn')?.addEventListener('click', () => {
    document.getElementById('pdfStudioModal').classList.add('hidden');
});

document.getElementById('generatePdfBtn')?.addEventListener('click', async () => {
    const a4Container = document.getElementById('a4Container');
    
    // Hide actions temporarily
    const actions = a4Container.querySelectorAll('.pdf-block-actions');
    actions.forEach(a => a.style.display = 'none');
    
    // Remove dashed borders from text blocks temporarily
    const textBlocks = a4Container.querySelectorAll('div[contenteditable="true"]');
    const originalBorders = [];
    textBlocks.forEach(tb => {
        originalBorders.push(tb.style.border);
        tb.style.border = 'none';
    });

    // Temporarily remove height constraints so container expands to fit all content for PDF pagination
    const originalAspect = a4Container.style.aspectRatio;
    const originalOverflow = a4Container.style.overflowY;
    a4Container.style.aspectRatio = 'auto';
    a4Container.style.overflowY = 'visible';

    const btn = document.getElementById('generatePdfBtn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '⏳ Oluşturuluyor...';
    btn.disabled = true;

    try {
        const opt = {
            margin:       10,
            filename:     `Rapor_${new Date().getTime()}.pdf`,
            image:        { type: 'jpeg', quality: 0.98 },
            html2canvas:  { scale: 2, useCORS: true },
            jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' },
            pagebreak:    { mode: ['avoid-all', 'css', 'legacy'] }
        };
        await html2pdf().set(opt).from(a4Container).save();
    } catch(err) {
        alert("PDF Oluşturulurken hata: " + err.message);
    }

    // Restore original styles
    a4Container.style.aspectRatio = originalAspect;
    a4Container.style.overflowY = originalOverflow;
    
    // Restore actions and borders
    actions.forEach(a => a.style.display = 'flex');
    textBlocks.forEach((tb, i) => {
        tb.style.border = originalBorders[i];
    });

    btn.disabled = false;
    btn.innerHTML = originalText;
});




  /* ── 10. STATS & AI (Qwen2.5) & SINGLE PDF EXPORT ── */
  async function fetchStats(cols) {
    if(!cols.length) return;
    try {
        const res = await fetch('/get_stats', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({ columns: cols, filters: activeFilters, x_col: axisConfig.x })
        });
        const data = await res.json();
        currentStats = data.stats;
        const grid = document.getElementById('statsGrid');
        if (grid) grid.innerHTML = renderStatsCards(data);
    } catch(e) {
        console.error('Istatistik Hatasi:', e);
    }
}


// AI Yorumlayıcı
  document.getElementById('btnGenerateInsight')?.addEventListener('click', async () => {
    const btn = document.getElementById('btnGenerateInsight');
    const container = document.getElementById('aiResponseContainer');
    const content = document.getElementById('aiResponseContent');
    
    btn.disabled = true;
    btn.innerHTML = '🔄 AI Yorumluyor...';
    container.classList.add('hidden');

    try {
      const res = await fetch('/generate_insight', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          stats: currentStats,
          chart_type: document.getElementById('currentChartTypeName').textContent,
          x_col: axisConfig.x,
          y_cols: axisConfig.y
        })
      });
      const data = await res.json();
      if(!res.ok) throw new Error(data.error);

      let text = data.insight;
      text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      text = text.replace(/\n\*/g, '<br/>•');
      text = text.replace(/\n/g, '<br/>');
      
      currentAiInsight = text;
      content.innerHTML = text;
      container.classList.remove('hidden');
    } catch(err) {
      content.innerHTML = `<div style="color:var(--red);">${err.message}</div>`;
      container.classList.remove('hidden');
    }
    
    btn.disabled = false;
    btn.innerHTML = 'Yeniden Yorumla';
  });

  // Tekil PDF Export
  document.getElementById('downloadPdfBtn')?.addEventListener('click', async () => {
    const btn = document.getElementById('downloadPdfBtn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '⏳ Rapor Oluşturuluyor...';
    btn.disabled = true;

    try {
      const chartDataUrl = await Plotly.toImage('chartArea', {format: 'png', width: 1200, height: 700});
      
      const wrapper = document.createElement('div');
      wrapper.style.padding = '40px';
      wrapper.style.background = '#ffffff';
      wrapper.style.color = '#111827';
      wrapper.style.fontFamily = 'Inter, sans-serif';
      
      let html = `
        <div style="border-bottom: 2px solid #a78bfa; padding-bottom: 20px; margin-bottom: 30px; display:flex; justify-content:space-between; align-items:flex-end;">
          <div>
            <h1 style="margin:0; font-size:28px; font-weight:800; color:#4c1d95;">⬡ DataViz Pro</h1>
            <p style="margin:5px 0 0; color:#6b7280; font-size:14px;">Profesyonel Yönetici Raporu</p>
          </div>
          <div style="color:#9ca3af; font-size:12px;">Tarih: ${new Date().toLocaleDateString('tr-TR')}</div>
        </div>

        <h3 style="color:#1f2937; margin-bottom:15px; font-size:18px;">Görsel Analiz: ${document.getElementById('currentChartTypeName').textContent}</h3>
        <div style="border:1px solid #e5e7eb; border-radius:12px; padding:10px; margin-bottom:30px;">
          <img src="${chartDataUrl}" style="width:100%; border-radius:8px;" />
        </div>
      `;

      if(currentAiInsight) {
        html += `
          <h3 style="color:#1f2937; margin-bottom:15px; font-size:18px;">🤖 AI Veri Yorumu</h3>
          <div style="background:#f3f4f6; padding:20px; border-radius:12px; border-left:4px solid #a78bfa; margin-bottom:30px; font-size:14px; line-height:1.6;">
            ${currentAiInsight}
          </div>
        `;
      }

      if(currentStats && Object.keys(currentStats).length > 0) {
        html += `<h3 style="color:#1f2937; margin-bottom:15px; font-size:18px;">İstatistiksel Özet</h3>
                 <table style="width:100%; border-collapse:collapse; font-size:13px; text-align:left;">
                   <tr style="background:#f9fafb; border-bottom:1px solid #e5e7eb;">
                     <th style="padding:10px;">Sütun</th>
                     <th style="padding:10px;">Ortalama</th>
                     <th style="padding:10px;">Medyan</th>
                     <th style="padding:10px;">Min</th>
                     <th style="padding:10px;">Max</th>
                   </tr>`;
        Object.entries(currentStats).forEach(([k, v]) => {
          html += `<tr style="border-bottom:1px solid #e5e7eb;">
            <td style="padding:10px; font-weight:600;">${k}</td>
            <td style="padding:10px;">${v.mean?.toFixed(2) || '-'}</td>
            <td style="padding:10px;">${v.median?.toFixed(2) || '-'}</td>
            <td style="padding:10px;">${v.min?.toFixed(2) || '-'}</td>
            <td style="padding:10px;">${v.max?.toFixed(2) || '-'}</td>
          </tr>`;
        });
        html += `</table>`;
      }

      wrapper.innerHTML = html;
      
      const opt = {
        margin:       10,
        filename:     `DataViz_Raporu_${Date.now()}.pdf`,
        image:        { type: 'jpeg', quality: 0.98 },
        html2canvas:  { scale: 2 },
        jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
      };

      await html2pdf().set(opt).from(wrapper).save();
    } catch(err) {
      alert("PDF Oluşturulurken hata: " + err.message);
    }
    
    btn.disabled = false;
    btn.innerHTML = originalText;
  });


  /* ── 11. INSPECTOR & TABS ── */
  document.querySelectorAll('.i-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.i-tab').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.i-pane').forEach(p => {
        p.classList.remove('active');
        p.classList.remove('hidden');
      });
      btn.classList.add('active');
      document.getElementById(`itab-${btn.dataset.itab}`).classList.add('active');
    });
  });

  const traceSizeInput = document.getElementById('traceSize');
  if(traceSizeInput) traceSizeInput.addEventListener('input', e => document.getElementById('traceSizeVal').textContent = e.target.value);

  document.getElementById('applyCustomsBtn')?.addEventListener('click', () => {
    if(currentChartData) refreshActiveChart();
  });
  
  document.getElementById('downloadPngBtn')?.addEventListener('click', () => {
    Plotly.downloadImage('chartArea', { format: 'png', width: 1600, height: 900, filename: `DataVizPro_${currentPlotType}` });
  });

  const screenPivotStudio = document.getElementById('screen-pivot-studio');

  window.showScreen = showScreen;
  function showScreen(num) {
    [step1, step2, step3, screenPivotStudio].forEach(s => { 
      if(s) { s.classList.add('hidden'); s.classList.remove('active'); }
    });
    if(num===1 && step1) { step1.classList.remove('hidden'); step1.classList.add('active'); }
    if(num===2 && step2) { step2.classList.remove('hidden'); step2.classList.add('active'); }
    if(num===3 && step3) { step3.classList.remove('hidden'); step3.classList.add('active'); }
    if((num===4 || num==='pivot') && screenPivotStudio) { 
      screenPivotStudio.classList.remove('hidden'); 
      screenPivotStudio.classList.add('active'); 
      initPivotStudio();
      refreshPivotStudio();
    }
  }

  document.getElementById('btnCancelStep2')?.addEventListener('click', () => showScreen(1));
  document.getElementById('btnBackToStep2')?.addEventListener('click', () => showScreen(2));
  document.getElementById('btnNewFile')?.addEventListener('click', () => {
    mainFileInput.value = '';
    document.getElementById('mainUploadStatus').style.display = 'none';
    showScreen(1);
  });
  document.getElementById('btnPivotNewFile')?.addEventListener('click', () => {
    mainFileInput.value = '';
    document.getElementById('mainUploadStatus').style.display = 'none';
    showScreen(1);
  });

  // Stüdyo Geçiş Butonları (Mode Switchers)
  // document.getElementById('btnModePivotS2')?.addEventListener('click', () => showScreen(4));
  // document.getElementById('btnModePivotS3')?.addEventListener('click', () => showScreen(4));
  document.getElementById('btnModeChartsS2')?.addEventListener('click', () => showScreen(2));
  document.getElementById('btnModeChartsS3')?.addEventListener('click', () => showScreen(3));
  document.getElementById('btnPivotBackToCharts')?.addEventListener('click', () => {
    if (axisConfig.x || axisConfig.y.length) showScreen(3);
    else showScreen(2);
  });

  // Topbar Help & Refresh handlers
  document.getElementById('topbarHelp')?.addEventListener('click', () => {
    alert('⌨️ Kısayollar:\n\nG → Grafik sekmesi\nS → İstatistik sekmesi\nD → Dashboard sekmesi\nP → Panoya ekle\n? → Bu yardım\nEsc → Modal kapat');
  });
  document.getElementById('refreshStatsBtn')?.addEventListener('click', () => {
    if(axisConfig.y && axisConfig.y.length > 0) {
      fetchStats(axisConfig.y);
    }
  });

  // Main area Tab Bar (Step 3)
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.add('hidden'));
      btn.classList.add('active');
      
      const tabName = btn.dataset.tab;

      if(tabName === 'chart') {
        document.getElementById('tabChart').classList.remove('hidden');
        try { Plotly.Plots.resize('chartArea'); } catch(e){}
      } else if(tabName === 'stats') {
        document.getElementById('tabStats').classList.remove('hidden');
      } else if(tabName === 'ai') {
        document.getElementById('tabAi').classList.remove('hidden');
      } else if(tabName === 'dashboard') {
        document.getElementById('tabDashboard').classList.remove('hidden');
        renderDashboardGrid();
        fetchKpis();
      }
    });
  });


  /* ══════════ 12. BAĞIMSIZ PIVOT MATRİS STÜDYOSU MOTORU ══════════ */
  let pivotConfig = {
    rows: [],
    cols: [],
    values: [],
    agg_func: 'sum'
  };
  let currentPivotData = null;
  let currentPivotPoolSearch = '';
  let currentPivotPoolFilter = 'all';

  function initPivotStudio() {
    const pivotPool = document.getElementById('pivotColPool');
    if (!pivotPool) return;

    // Otomatik akıllı ilk varsayılanlar (Asla boş ve uyarı ile açılmasın)
    if (pivotConfig.rows.length === 0) {
      const defRow = categoricalColumns.find(c => /bolge|sehir|kategori|segment/i.test(c)) || categoricalColumns[0] || globalColumns[0];
      if (defRow) pivotConfig.rows = [defRow];
    }
    if (pivotConfig.cols.length === 0 && categoricalColumns.length > 1) {
      const defCol = categoricalColumns.find(c => !pivotConfig.rows.includes(c) && /odeme|kategori|tip|tur|yil/i.test(c)) || categoricalColumns.find(c => !pivotConfig.rows.includes(c));
      if (defCol) pivotConfig.cols = [defCol];
    }
    if (pivotConfig.values.length === 0) {
      const defVal = numericColumns.find(c => /tutar|ciro|kar|satis|fiyat/i.test(c)) || numericColumns[0];
      if (defVal) pivotConfig.values = [defVal];
    }

    renderPivotPoolStructured();
    renderPivotDropZones();
    refreshPivotStudio();
  }

  function renderPivotPoolStructured() {
    const pool = document.getElementById('pivotColPool');
    if (!pool) return;
    pool.innerHTML = '';

    const countBadge = document.getElementById('pivotPoolCountBadge');
    if (countBadge) countBadge.textContent = `${globalColumns.length} Sütun`;

    // Filtre sayaçları
    const catCount = categoricalColumns.length;
    const numCount = numericColumns.length;
    const joinedCount = joinedColumns.length;

    const elAll = document.getElementById('pfcPivotAllCount');
    const elCat = document.getElementById('pfcPivotCatCount');
    const elNum = document.getElementById('pfcPivotNumCount');
    const elJoined = document.getElementById('pfcPivotJoinedCount');
    const elJoinedBtn = document.getElementById('pfcPivotJoinedBtn');

    if (elAll) elAll.textContent = globalColumns.length;
    if (elCat) elCat.textContent = catCount;
    if (elNum) elNum.textContent = numCount;
    if (elJoinedBtn) {
      if (joinedCount > 0) {
        elJoinedBtn.classList.remove('hidden');
        if (elJoined) elJoined.textContent = joinedCount;
      } else {
        elJoinedBtn.classList.add('hidden');
      }
    }

    const file1Cols = globalColumns.filter(c => !joinedColumns.includes(c) && !calculatedColumns.includes(c));
    const joinedCols = globalColumns.filter(c => joinedColumns.includes(c));
    const calcCols = globalColumns.filter(c => calculatedColumns.includes(c));

    renderPivotPoolSection(pool, '📁 1. Dosya Sütunları', file1Cols, 'section_pivot_file1');
    if (joinedCols.length > 0) {
      renderPivotPoolSection(pool, '🔗 2. Dosya Sütunları (VLOOKUP)', joinedCols, 'section_pivot_joined');
    }
    if (calcCols.length > 0) {
      renderPivotPoolSection(pool, '🧮 Hesaplanmış Formül Sütunları', calcCols, 'section_pivot_calc');
    }

    applyPivotPoolFilterAndSearch();
  }

  function renderPivotPoolSection(parentContainer, titleText, cols, sectionId) {
    if (!cols.length) return;

    const group = document.createElement('div');
    group.className = 'pool-section-group';
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

    cols.forEach(col => {
      const isNum = numericColumns.includes(col);
      const isJoined = joinedColumns.includes(col);
      const isCalc = calculatedColumns.includes(col);

      const isUsed = pivotConfig.rows.includes(col) || pivotConfig.cols.includes(col) || pivotConfig.values.includes(col);

      const pill = document.createElement('div');
      pill.className = `col-pill ${isJoined ? 'joined-pill' : ''} ${isCalc ? 'calc-pill' : ''} ${isUsed ? 'in-zone' : ''}`;
      pill.draggable = true;
      pill.dataset.col = col;
      pill.dataset.type = isNum ? 'num' : 'cat';
      pill.dataset.origin = isJoined ? 'joined' : (isCalc ? 'calc' : 'main');

      const tagHtml = isNum 
        ? `<span class="col-pill-tag num" title="Sayısal Sütun">#</span>` 
        : `<span class="col-pill-tag cat" title="Kategorik / Metin Sütun">T</span>`;

      const joinBadge = isJoined ? `<span class="join-tag-badge">🔗 Dosya 2</span>` : '';
      const calcBadge = isCalc ? `<span class="join-tag-badge" style="background:rgba(245,158,11,0.2); color:#fbbf24; border-color:rgba(245,158,11,0.4);">🧮 fx</span>` : '';

      pill.innerHTML = `${tagHtml} <span class="col-pill-name">${col}</span> ${joinBadge} ${calcBadge}`;

      // Drag start
      pill.addEventListener('dragstart', e => {
        e.dataTransfer.setData('text/plain', col);
        e.dataTransfer.effectAllowed = 'copyMove';
      });

      // Click to add / assign
      pill.addEventListener('click', () => {
        if (pivotConfig.rows.includes(col)) {
          pivotConfig.rows = pivotConfig.rows.filter(x => x !== col);
          pivotConfig.cols.push(col);
        } else if (pivotConfig.cols.includes(col)) {
          pivotConfig.cols = pivotConfig.cols.filter(x => x !== col);
        } else if (pivotConfig.values.includes(col)) {
          if (pivotConfig.values.length > 1) pivotConfig.values = pivotConfig.values.filter(x => x !== col);
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
    document.querySelectorAll('#pivotColPool .col-pill').forEach(pill => {
      const colName = pill.dataset.col.toLowerCase();
      const colType = pill.dataset.type;
      const origin = pill.dataset.origin;

      const matchesSearch = !currentPivotPoolSearch || colName.includes(currentPivotPoolSearch);

      let matchesFilter = true;
      if (currentPivotPoolFilter === 'cat') matchesFilter = colType === 'cat';
      else if (currentPivotPoolFilter === 'num') matchesFilter = colType === 'num';
      else if (currentPivotPoolFilter === 'joined') matchesFilter = origin === 'joined';

      pill.style.display = (matchesSearch && matchesFilter) ? 'inline-flex' : 'none';
    });

    document.querySelectorAll('#pivotColPool .pool-section-group').forEach(group => {
      const allPills = group.querySelectorAll('.col-pill');
      let hasVisible = false;
      allPills.forEach(p => { if (p.style.display !== 'none') hasVisible = true; });
      group.style.display = hasVisible ? 'block' : 'none';
    });
  }

  // Pivot Pool Search & Filter Buttons
  document.getElementById('pivotPoolSearchInput')?.addEventListener('input', (e) => {
    currentPivotPoolSearch = e.target.value.toLowerCase().trim();
    applyPivotPoolFilterAndSearch();
  });

  document.querySelectorAll('[data-pivotfilter]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-pivotfilter]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentPivotPoolFilter = btn.dataset.pivotfilter;
      applyPivotPoolFilterAndSearch();
    });
  });

  function renderPivotDropZones() {
    const rowZone = document.getElementById('pivotRowZone');
    const colZone = document.getElementById('pivotColZone');
    const valZone = document.getElementById('pivotValZone');
    if (!rowZone || !colZone || !valZone) return;

    rowZone.innerHTML = '';
    colZone.innerHTML = '';
    valZone.innerHTML = '';

    if (pivotConfig.rows.length === 0) rowZone.innerHTML = '<span style="opacity:0.6; font-size:0.85rem;">Sütunları Buraya Bırakın veya Havuzdan Tıklayın</span>';
    if (pivotConfig.cols.length === 0) colZone.innerHTML = '<span style="opacity:0.6; font-size:0.85rem;">Sütunları Buraya Bırakın (Opsiyonel)</span>';
    if (pivotConfig.values.length === 0) valZone.innerHTML = '<span style="opacity:0.6; font-size:0.85rem;">Sayısal Sütunları Buraya Bırakın</span>';

    // Rows
    pivotConfig.rows.forEach(col => {
      const pill = createPivotZonePill(col, 'cat', () => {
        pivotConfig.rows = pivotConfig.rows.filter(x => x !== col);
        renderPivotPoolStructured();
        renderPivotDropZones();
        refreshPivotStudio();
      });
      rowZone.appendChild(pill);
    });

    // Columns
    pivotConfig.cols.forEach(col => {
      const pill = createPivotZonePill(col, 'cat', () => {
        pivotConfig.cols = pivotConfig.cols.filter(x => x !== col);
        renderPivotPoolStructured();
        renderPivotDropZones();
        refreshPivotStudio();
      });
      colZone.appendChild(pill);
    });

    // Values
    pivotConfig.values.forEach(col => {
      const pill = createPivotZonePill(col, 'num', () => {
        if (pivotConfig.values.length > 1) {
          pivotConfig.values = pivotConfig.values.filter(x => x !== col);
          renderPivotPoolStructured();
          renderPivotDropZones();
          refreshPivotStudio();
        }
      });
      valZone.appendChild(pill);
    });
  }

  function createPivotZonePill(col, type, onRemove) {
    const isNum = type === 'num' || numericColumns.includes(col);
    const pill = document.createElement('div');
    pill.className = `col-pill ${isNum ? '' : ''}`;
    pill.dataset.col = col;
    pill.dataset.type = isNum ? 'num' : 'cat';

    const tagHtml = isNum ? `<span class="col-pill-tag num">#</span>` : `<span class="col-pill-tag cat">T</span>`;
    pill.innerHTML = `${tagHtml} <span>${col}</span> <span class="col-pill-remove" title="Kaldır">×</span>`;

    pill.querySelector('.col-pill-remove').addEventListener('click', (e) => {
      e.stopPropagation();
      onRemove();
    });
    pill.addEventListener('click', onRemove);
    return pill;
  }

  // Setup Drag & Drop for Pivot Zones
  ['pivotRowZone', 'pivotColZone', 'pivotValZone'].forEach(zoneId => {
    const zone = document.getElementById(zoneId);
    if (!zone) return;

    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', e => {
      e.preventDefault();
      zone.classList.remove('dragover');
      const colName = e.dataTransfer.getData('text/plain');
      if (!colName || !globalColumns.includes(colName)) return;

      const pZone = zone.dataset.pivotZone;
      // Remove from everywhere first to prevent desync
      pivotConfig.rows = pivotConfig.rows.filter(x => x !== colName);
      pivotConfig.cols = pivotConfig.cols.filter(x => x !== colName);
      pivotConfig.values = pivotConfig.values.filter(x => x !== colName);
      
      if (pZone === 'row') {
        pivotConfig.rows.push(colName);
      } else if (pZone === 'col') {
        pivotConfig.cols.push(colName);
      } else if (pZone === 'val') {
        pivotConfig.values.push(colName);
      }

      renderPivotPoolStructured();
      renderPivotDropZones();
      refreshPivotStudio();
    });
  });

  // Modals in Pivot Studio
  document.getElementById('btnOpenCalcModalPivot')?.addEventListener('click', () => {
    document.getElementById('btnOpenCalcModal')?.click();
  });
  document.getElementById('btnOpenMergeModalPivot')?.addEventListener('click', () => {
    document.getElementById('btnOpenMergeModal')?.click();
  });

  // Aggregation Function Select
  document.getElementById('pivotAggSelect')?.addEventListener('change', (e) => {
    pivotConfig.agg_func = e.target.value;
    refreshPivotStudio();
  });

  // Refresh Matrix Data
  async function refreshPivotStudio() {
    const container = document.getElementById('pmsTableContainer');
    const badge = document.getElementById('pmsStatsBadge');
    if (!container) return;

    if (pivotConfig.rows.length === 0 && pivotConfig.cols.length === 0) {
      container.innerHTML = '<div class="pivot-loading-msg">⚠️ Lütfen en az 1 Satır veya Sütun seçin.</div>';
      if (badge) badge.textContent = '0 Boyut';
      return;
    }
    if (pivotConfig.values.length === 0) {
      container.innerHTML = '<div class="pivot-loading-msg">⚠️ Lütfen en az 1 Sayısal Değer seçin.</div>';
      if (badge) badge.textContent = '0 Metrik';
      return;
    }

    container.innerHTML = '<div class="pivot-loading-msg">⏳ Pivot Tablosu Hesaplanıyor...</div>';
    pivotConfig.agg_func = document.getElementById('pivotAggSelect')?.value || 'sum';

    try {
      const res = await fetch('/get_pivot_data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rows: pivotConfig.rows,
          cols: pivotConfig.cols,
          values: pivotConfig.values,
          agg_func: pivotConfig.agg_func,
          filters: activeFilters
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error);

      currentPivotData = data;
      renderPivotMatrixStage(data);

      if (badge) {
        badge.textContent = `${data.rows.length} Satır x ${data.column_headers.length} Sütun (${data.total_data_rows.toLocaleString('tr-TR')} Kayıt)`;
      }
    } catch(err) {
      container.innerHTML = `<div class="pivot-loading-msg" style="color:var(--red);">❌ ${err.message}</div>`;
      if (badge) badge.textContent = 'Hata';
    }
  }

  function renderPivotMatrixStage(data) {
    const container = document.getElementById('pmsTableContainer');
    if (!container) return;

    const useHeatmap = document.getElementById('pmsHeatmapToggle')?.checked ?? true;
    const minVal = data.min_value;
    const maxVal = data.max_value;
    const valRange = (maxVal - minVal) || 1;

    let html = `<table class="pivot-matrix-table" id="pmsLiveTable">`;

    // 1. Header
    html += `<thead><tr>`;
    data.index_names.forEach(name => {
      html += `<th class="pmt-corner">${name}</th>`;
    });
    data.column_headers.forEach(h => {
      const isGrand = h.includes('Genel Toplam');
      html += `<th class="${isGrand ? 'pmt-grand-total-th' : 'pmt-col-header'}">${h}</th>`;
    });
    html += `</tr></thead>`;

    // 2. Body
    html += `<tbody>`;
    data.rows.forEach(r => {
      const isRowGrand = r.is_grand_total;
      html += `<tr class="${isRowGrand ? 'pmt-grand-total-row' : ''}">`;

      // Row labels
      r.row_labels.forEach(lbl => {
        html += `<td class="pmt-row-header">${lbl}</td>`;
      });

      // Cell values
      r.cells.forEach((val, cIdx) => {
        const isColGrand = (data.column_headers[cIdx] || '').includes('Genel Toplam');
        let bgStyle = '';

        if (useHeatmap && !isRowGrand && !isColGrand && val > 0) {
          const ratio = Math.min(1, Math.max(0, (val - minVal) / valRange));
          const alpha = 0.08 + (ratio * 0.45);
          bgStyle = `background: rgba(52, 211, 153, ${alpha.toFixed(3)});`;
        }

        let formattedVal = val.toLocaleString('tr-TR', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
        if (val >= 1000) formattedVal = val.toLocaleString('tr-TR', { maximumFractionDigits: 0 });

        const cellClass = `pmt-val-cell ${isColGrand ? 'pmt-grand-total-cell' : ''} ${useHeatmap ? 'has-heatmap' : ''}`;
        html += `<td class="${cellClass}" style="${bgStyle}">${formattedVal}</td>`;
      });

      html += `</tr>`;
    });
    html += `</tbody></table>`;

    container.innerHTML = html;
  }

  // Heatmap Değişimi
  document.getElementById('pmsHeatmapToggle')?.addEventListener('change', () => {
    if (currentPivotData) renderPivotMatrixStage(currentPivotData);
  });

  // Excel Olarak İndir (.xlsx)
  document.getElementById('btnPmsExportExcel')?.addEventListener('click', async () => {
    const btn = document.getElementById('btnPmsExportExcel');
    const orig = btn.innerHTML;
    btn.innerHTML = '⏳ İndiriliyor...';
    btn.disabled = true;

    try {
      const res = await fetch('/export_pivot_excel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rows: pivotConfig.rows,
          cols: pivotConfig.cols,
          values: pivotConfig.values,
          agg_func: pivotConfig.agg_func,
          filters: activeFilters
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || 'Excel indirilemedi');
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `DataViz_Ozet_Pivot_${Date.now()}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch(err) {
      alert("Excel indirme hatası: " + err.message);
    }

    btn.innerHTML = orig;
    btn.disabled = false;
  });

  // Tabloyu Kopyala (TSV Formatında Panoya)
  document.getElementById('btnPmsCopyTable')?.addEventListener('click', () => {
    const table = document.getElementById('pmsLiveTable');
    if (!table) return;

    let tsv = [];
    table.querySelectorAll('tr').forEach(row => {
      let rowData = [];
      row.querySelectorAll('th, td').forEach(cell => {
        rowData.push(cell.innerText.trim().replace(/\n/g, ' '));
      });
      tsv.push(rowData.join('\t'));
    });

    const tsvText = tsv.join('\n');
    navigator.clipboard.writeText(tsvText).then(() => {
      const btn = document.getElementById('btnPmsCopyTable');
      const orig = btn.innerHTML;
      btn.innerHTML = '✓ Kopyalandı!';
      setTimeout(() => btn.innerHTML = orig, 2000);
    }).catch(err => {
      alert("Kopyalama başarısiz: " + err.message);
    });
  });

  // Panoya Ekle (Dashboard Widget)
  document.getElementById('btnPmsPinDashboard')?.addEventListener('click', () => {
    if (!currentPivotData) return;

    const rowName = pivotConfig.rows.join(' & ') || 'Tümü';
    const colName = pivotConfig.cols.join(' & ');
    const valName = pivotConfig.values.join(', ');
    const title = `${rowName} ${colName ? 'x ' + colName : ''} Özet Pivot (${valName})`;

    const dashItem = {
      id: 'dash_pivot_' + Date.now(),
      title: title,
      chartType: 'pivot',
      pivotData: JSON.parse(JSON.stringify(currentPivotData)),
      filtersCount: activeFilters.length
    };

    dashboardCharts.push(dashItem);
    updateDashboardBadge();
    renderDashboardGrid();

    const btn = document.getElementById('btnPmsPinDashboard');
    btn.innerHTML = '<span>✓</span> Panoya Eklendi!';
    setTimeout(() => {
      btn.innerHTML = '<span>📌</span> Panoya Ekle';
    }, 2000);
  });

});


// SPRINT 3: Prevent global window drop to avoid navigating away
window.addEventListener('dragover', e => e.preventDefault());
window.addEventListener('drop', e => e.preventDefault());


function renderStatsCards(data) {
    if (!data || !data.stats || Object.keys(data.stats).length === 0) {
        return '<div class="bento-loading" style="grid-column: 1 / -1; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 24px; text-align: center; color: var(--muted);">İstatistik bulunamadı veya hesaplanamadı.</div>';
    }

    let html = '';
    
    Object.keys(data.stats).forEach(col => {
        const m = data.stats[col];
        const adv = data.advanced && data.advanced[col] ? data.advanced[col] : null;
        
        let advHtml = '';
        if (adv) {
            if (adv.type === 'numeric') {
                advHtml = `
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1);">
                        <h4 style="font-size: 0.9rem; color: #a78bfa; margin-bottom: 8px;">Korelasyon & Regresyon</h4>
                        <div class="b-stat-body" style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                            <div class="b-metric"><span>Korelasyon (r)</span><strong>${adv.correlation ? adv.correlation.toFixed(3) : '-'}</strong></div>
                            <div class="b-metric"><span>R² Değeri</span><strong>${adv.r_squared ? adv.r_squared.toFixed(3) : '-'}</strong></div>
                            <div class="b-metric" style="grid-column: 1 / -1;"><span>P Değeri</span><strong>${adv.p_value != null ? adv.p_value.toExponential(2) : '-'}</strong></div>
                            <div class="b-metric" style="grid-column: 1 / -1; background: rgba(167, 139, 250, 0.1); padding: 8px; border-radius: 6px;"><span>Regresyon Denklemi</span><strong style="color: #a78bfa;">${adv.regression || '-'}</strong></div>
                        </div>
                    </div>
                `;
            } else if (adv.type === 'categorical_2') {
                advHtml = `
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1);">
                        <h4 style="font-size: 0.9rem; color: #34d399; margin-bottom: 8px;">Bağımsız Örneklem T-Testi</h4>
                        <div class="b-stat-body" style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                            <div class="b-metric"><span>T İstatistiği</span><strong>${adv.t_test_stat ? adv.t_test_stat.toFixed(3) : '-'}</strong></div>
                            <div class="b-metric"><span>P Değeri</span><strong>${adv.p_value != null ? adv.p_value.toExponential(2) : '-'}</strong></div>
                        </div>
                    </div>
                `;
            } else if (adv.type === 'categorical_n') {
                advHtml = `
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1);">
                        <h4 style="font-size: 0.9rem; color: #fbbf24; margin-bottom: 8px;">Tek Yönlü ANOVA</h4>
                        <div class="b-stat-body" style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                            <div class="b-metric"><span>F İstatistiği</span><strong>${adv.anova_f ? adv.anova_f.toFixed(3) : '-'}</strong></div>
                            <div class="b-metric"><span>P Değeri</span><strong>${adv.p_value != null ? adv.p_value.toExponential(2) : '-'}</strong></div>
                        </div>
                    </div>
                `;
            }
        }

        html += `
        <div class="stat-card" style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 24px; display: flex; flex-direction: column;">
            <div class="b-stat-header" style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                <div class="b-stat-name" style="font-weight: 700; font-size: 1.1rem; color: var(--text);">${col}</div>
                <div class="b-stat-badge" style="font-size: 0.75rem; background: rgba(255,255,255,0.1); padding: 4px 8px; border-radius: 4px;">Sayısal</div>
            </div>
            
            <div class="b-stat-body" style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                <div class="b-metric primary" style="display: flex; flex-direction: column; gap: 4px;">
                    <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">Ortalama</span>
                    <strong style="color: #60a5fa; font-size: 1.1rem;">${m.mean ? m.mean.toFixed(2) : '-'}</strong>
                </div>
                <div class="b-metric" style="display: flex; flex-direction: column; gap: 4px;">
                    <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">Medyan</span>
                    <strong style="font-size: 1.1rem;">${m.median ? m.median.toFixed(2) : '-'}</strong>
                </div>
                <div class="b-metric danger" style="display: flex; flex-direction: column; gap: 4px;">
                    <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">Min</span>
                    <strong style="color: #f87171; font-size: 1.1rem;">${m.min ? m.min.toFixed(2) : '-'}</strong>
                </div>
                <div class="b-metric success" style="display: flex; flex-direction: column; gap: 4px;">
                    <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">Max</span>
                    <strong style="color: #34d399; font-size: 1.1rem;">${m.max ? m.max.toFixed(2) : '-'}</strong>
                </div>
                <div class="b-metric" style="display: flex; flex-direction: column; gap: 4px;">
                    <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">Std. Sapma</span>
                    <strong style="font-size: 1.1rem;">${m.std ? m.std.toFixed(2) : '-'}</strong>
                </div>
                <div class="b-metric" style="display: flex; flex-direction: column; gap: 4px;">
                    <span style="font-size: 0.75rem; color: var(--muted); text-transform: uppercase;">Eksik Veri</span>
                    <strong style="font-size: 1.1rem;">${m.missing !== undefined ? m.missing : '-'}</strong>
                </div>
            </div>
            
            ${advHtml}
        </div>`;
    });
    return html;
}


document.addEventListener('DOMContentLoaded', () => {
  /* ── DRAGGABLE RESIZER FOR STEP 2 ── */
  const s2Resizer = document.getElementById('s2-resizer');
  const s2LeftPane = document.querySelector('.s2-left-pane');
  const s2BodySplit = document.querySelector('.s2-body-split');
  
  if (s2Resizer && s2LeftPane && s2BodySplit) {
    let isDragging = false;
    
    s2Resizer.addEventListener('mousedown', (e) => {
      isDragging = true;
      document.body.style.cursor = 'col-resize';
      s2BodySplit.style.userSelect = 'none';
    });
    
    document.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const containerRect = s2BodySplit.getBoundingClientRect();
      let newWidth = e.clientX - containerRect.left;
      
      if (newWidth < 200) newWidth = 200;
      if (newWidth > containerRect.width - 200) newWidth = containerRect.width - 200;
      
      s2LeftPane.style.width = newWidth + 'px';
    });
    
    document.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        document.body.style.cursor = '';
        s2BodySplit.style.userSelect = '';
      }
    });
  }
});
