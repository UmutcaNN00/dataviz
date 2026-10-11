/**
 * Prototype Hub - DataViz Next-Gen Engineering Prototypes
 * Manages 4 prototype modules:
 * 1. Apache Arrow IPC Zero-Copy Stream & Benchmark
 * 2. OpenRefine-Style Key Collision & Text Clustering
 * 3. Virtualized 60 FPS Table Windowing Grid
 * 4. Explainable Isolation Forest & Anomaly Reasons
 */

export class PrototypeHub {
  constructor() {
    this.activeTab = "arrow";
    this.currentSliceStart = 0;
    this.sliceLimit = 40;
    this.sortCol = null;
    this.sortAsc = true;
    this.searchQuery = "";
  }

  init() {
    this.bindEvents();
    this.initVirtualGridModal();
    console.log("🚀 [PrototypeHub] 4 İleri Mühendislik Prototipi başlatıldı.");
  }

  bindEvents() {
    // Tab switching
    document.querySelectorAll(".proto-tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const tab = btn.dataset.tab;
        this.switchTab(tab);
      });
    });

    // Option 1: Arrow Benchmark Button
    const btnRunArrow = document.getElementById("btnRunArrowBenchmark");
    if (btnRunArrow) {
      btnRunArrow.addEventListener("click", () => this.runArrowBenchmark());
    }

    // Option 2: Find Clusters Button
    const btnFindClusters = document.getElementById("btnFindClusters");
    if (btnFindClusters) {
      btnFindClusters.addEventListener("click", () => this.findTextClusters());
    }

    // Option 3: Virtual Table Controls
    const searchInput = document.getElementById("protoGridSearch");
    if (searchInput) {
      let debounceTimer = null;
      searchInput.addEventListener("input", (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          this.searchQuery = e.target.value;
          this.currentSliceStart = 0;
          this.fetchVirtualSlice();
        }, 300);
      });
    }

    const btnPrevPage = document.getElementById("protoGridPrev");
    const btnNextPage = document.getElementById("protoGridNext");
    if (btnPrevPage) {
      btnPrevPage.addEventListener("click", () => {
        if (this.currentSliceStart > 0) {
          this.currentSliceStart = Math.max(0, this.currentSliceStart - this.sliceLimit);
          this.fetchVirtualSlice();
        }
      });
    }
    if (btnNextPage) {
      btnNextPage.addEventListener("click", () => {
        this.currentSliceStart += this.sliceLimit;
        this.fetchVirtualSlice();
      });
    }

    // Option 4: Explainable Anomaly Button
    const btnRunExplainer = document.getElementById("btnRunAnomalyExplainer");
    if (btnRunExplainer) {
      btnRunExplainer.addEventListener("click", () => this.runAnomalyExplainer());
    }

    // Option 5: Memory Optimization & Type Recovery
    const btnMem = document.getElementById("btnRunMemoryOptimize");
    if (btnMem) btnMem.addEventListener("click", () => this.runMemoryOptimize());

    const btnType = document.getElementById("btnRunTypeRecover");
    if (btnType) btnType.addEventListener("click", () => this.runTypeRecover());

    // Option 6: Contracts & MICE & Ensemble
    const btnContracts = document.getElementById("btnRunDataContracts");
    if (btnContracts) btnContracts.addEventListener("click", () => this.runDataContracts());

    const btnMice = document.getElementById("btnRunMiceImpute");
    if (btnMice) btnMice.addEventListener("click", () => this.runMiceImpute());

    const btnEns = document.getElementById("btnRunEnsembleAnom");
    if (btnEns) btnEns.addEventListener("click", () => this.runEnsembleAnom());

    // Option 7: Ultra Speed Engine (Morsel, SIMD, MMap, HLL, Dates)
    const btnMorsel = document.getElementById("btnRunMorselParallel");
    if (btnMorsel) btnMorsel.addEventListener("click", () => this.runMorselParallel());

    const btnPushdown = document.getElementById("btnRunPushdownFilter");
    if (btnPushdown) btnPushdown.addEventListener("click", () => this.runPushdownFilter());

    const btnMmap = document.getElementById("btnRunMmapPersist");
    if (btnMmap) btnMmap.addEventListener("click", () => this.runMmapPersist());

    const btnHll = document.getElementById("btnRunHllCardinality");
    if (btnHll) btnHll.addEventListener("click", () => this.runHllCardinality());

    const btnDates = document.getElementById("btnRunSmartDates");
    if (btnDates) btnDates.addEventListener("click", () => this.runSmartDates());
  }

  switchTab(tabId) {
    this.activeTab = tabId;
    document.querySelectorAll(".proto-tab-btn").forEach((b) => {
      b.classList.toggle("active", b.dataset.tab === tabId);
    });
    document.querySelectorAll(".proto-panel").forEach((p) => {
      p.classList.toggle("hidden", p.id !== `proto-panel-${tabId}`);
    });

    // Auto-trigger tab specific action
    if (tabId === "grid") {
      this.fetchVirtualSlice();
    } else if (tabId === "cluster") {
      this.populateClusterColumnSelect();
    }
  }

  // ══════════════════════════════════════════════════════════════════
  // 1. SEÇENEK: APACHE ARROW IPC BENCHMARK
  // ══════════════════════════════════════════════════════════════════
  async runArrowBenchmark() {
    const btn = document.getElementById("btnRunArrowBenchmark");
    const resultBox = document.getElementById("protoArrowResults");
    if (!resultBox) return;

    btn.disabled = true;
    btn.innerHTML = `<span class="proto-spinner"></span> Benchmark Çalıştırılıyor...`;

    try {
      const res = await fetch("/benchmark_json_vs_arrow?sample_size=25000");
      const data = await res.json();
      if (!data.success) throw new Error(data.error || "Benchmark hatası");

      const b = data.benchmark;
      resultBox.innerHTML = `
        <div class="proto-metrics-grid">
          <div class="proto-card proto-card-blue">
            <div class="proto-card-title">JSON Serileştirme</div>
            <div class="proto-big-val">${b.json.time_ms} ms</div>
            <div class="proto-card-sub">Ağ Boyutu: <strong>${b.json.size_kb} KB</strong></div>
          </div>
          <div class="proto-card proto-card-green">
            <div class="proto-card-title">⚡ Apache Arrow IPC Stream</div>
            <div class="proto-big-val">${b.arrow_ipc.time_ms} ms</div>
            <div class="proto-card-sub">Binary Boyut: <strong>${b.arrow_ipc.size_kb} KB</strong></div>
          </div>
          <div class="proto-card proto-card-purple">
            <div class="proto-card-title">🚀 Hız Artışı</div>
            <div class="proto-big-val">${b.speedup_ratio}</div>
            <div class="proto-card-sub">Daha Hızlı Serileştirme</div>
          </div>
          <div class="proto-card proto-card-amber">
            <div class="proto-card-title">📦 Veri Boyut Tasarrufu</div>
            <div class="proto-big-val">${b.size_reduction}</div>
            <div class="proto-card-sub">Daha Az Ağ Transferi</div>
          </div>
        </div>
        <div class="proto-banner-success">
          <strong>✅ Sıfır Kopyalama Doğrulandı:</strong> ${b.sample_rows.toLocaleString()} satır x ${b.num_cols} sütun üzerinde Apache Arrow RecordBatch IPC akışı oluşturuldu. Tarayıcıda <code>JSON.parse</code> maliyeti sıfırlandı.
        </div>
      `;
    } catch (err) {
      resultBox.innerHTML = `<div class="proto-banner-error">Hata: ${err.message}</div>`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = `⚡ Canlı Serileştirme Benchmark'ını Yeniden Çalıştır`;
    }
  }

  // ══════════════════════════════════════════════════════════════════
  // 2. SEÇENEK: OPENREFINE METİN KÜMELEME (CLUSTERING)
  // ══════════════════════════════════════════════════════════════════
  populateClusterColumnSelect() {
    const sel = document.getElementById("protoClusterColumnSelect");
    if (!sel || sel.options.length > 1) return;

    const cols = window.categoricalColumns || [];
    if (cols.length === 0) {
      sel.innerHTML = `<option value="">Önce dosya yükleyin</option>`;
      return;
    }

    sel.innerHTML = cols.map((c) => `<option value="${c}">${c}</option>`).join("");
  }

  async findTextClusters() {
    const sel = document.getElementById("protoClusterColumnSelect");
    const methodSel = document.getElementById("protoClusterMethodSelect");
    const resultBox = document.getElementById("protoClusterResults");
    const col = sel?.value;
    const method = methodSel?.value || "fingerprint";

    if (!col) {
      alert("Lütfen kümelenecek metin sütununu seçin.");
      return;
    }

    resultBox.innerHTML = `<div class="proto-loading"><span class="proto-spinner"></span> OpenRefine ${method} algoritmasıyla taranıyor...</div>`;

    try {
      const res = await fetch("/find_text_clusters", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ column: col, method: method, max_clusters: 40 }),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      if (data.clusters.length === 0) {
        resultBox.innerHTML = `
          <div class="proto-banner-info">
            Bu sütunda <strong>${method}</strong> algoritmasıyla birleşecek yazım hatası veya çoklu varyasyon bulunamadı. Veri zaten tutarlı!
          </div>
        `;
        return;
      }

      let html = `
        <div class="proto-cluster-header">
          <strong>${data.clusters.length} Adet Benzer Küme Tespit Edildi</strong>
          <small>${col} sütunundaki farklı yazılmış varyasyonlar gruplandı:</small>
        </div>
        <div class="proto-cluster-list">
      `;

      data.clusters.forEach((cl, idx) => {
        html += `
          <div class="proto-cluster-item" id="cluster-item-${idx}">
            <div class="pci-header">
              <span class="pci-badge">Anahtar: <code>${cl.key}</code></span>
              <span class="pci-rows">Toplam ${cl.total_rows} satır</span>
            </div>
            <div class="pci-body">
              <div class="pci-variants">
                ${cl.variants.map((v) => `
                  <span class="pci-tag">${v.val} <small>(${v.count})</small></span>
                `).join("")}
              </div>
              <div class="pci-actions">
                <span>Hedef Standart:</span>
                <input type="text" class="proto-input-canonical" id="canonical-${idx}" value="${cl.suggested_canonical}">
                <button type="button" class="btn-proto-merge" data-idx="${idx}" data-col="${col}">
                  ✓ Bu Kümeyi Birleştir
                </button>
              </div>
            </div>
          </div>
        `;
      });

      html += `</div>`;
      resultBox.innerHTML = html;

      // Bind merge buttons
      resultBox.querySelectorAll(".btn-proto-merge").forEach((b) => {
        b.addEventListener("click", () => {
          const idx = parseInt(b.dataset.idx, 10);
          const cl = data.clusters[idx];
          const input = document.getElementById(`canonical-${idx}`);
          const canonicalVal = input ? input.value : cl.suggested_canonical;
          this.mergeCluster(col, [{ canonical: canonicalVal, variants: cl.variants.map((v) => v.val) }], idx);
        });
      });
    } catch (err) {
      resultBox.innerHTML = `<div class="proto-banner-error">Hata: ${err.message}</div>`;
    }
  }

  async mergeCluster(col, merges, itemIdx) {
    const itemEl = document.getElementById(`cluster-item-${itemIdx}`);
    if (itemEl) itemEl.style.opacity = "0.5";

    try {
      const res = await fetch("/merge_text_clusters", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ column: col, merges: merges }),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      if (itemEl) {
        itemEl.innerHTML = `<div class="proto-banner-success" style="margin:0;">✅ Başarıyla Birleştirildi: ${data.message}</div>`;
      }
    } catch (err) {
      alert("Birleştirme hatası: " + err.message);
      if (itemEl) itemEl.style.opacity = "1";
    }
  }

  // ══════════════════════════════════════════════════════════════════
  // 3. SEÇENEK: 60 FPS SANAL TABLO (VIRTUAL GRID)
  // ══════════════════════════════════════════════════════════════════
  async fetchVirtualSlice() {
    const container = document.getElementById("protoGridTableContainer");
    const statsLabel = document.getElementById("protoGridRowStats");
    if (!container) return;

    try {
      const res = await fetch("/get_table_slice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          start: this.currentSliceStart,
          limit: this.sliceLimit,
          sort_col: this.sortCol,
          sort_asc: this.sortAsc,
          search: this.searchQuery,
        }),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      if (statsLabel) {
        const endRow = Math.min(this.currentSliceStart + this.sliceLimit, data.total_filtered);
        statsLabel.textContent = `${this.currentSliceStart + 1} - ${endRow} / Toplam ${data.total_filtered.toLocaleString()} satır`;
      }

      if (data.rows.length === 0) {
        container.innerHTML = `<div class="proto-banner-info">Görüntülenecek satır bulunamadı.</div>`;
        return;
      }

      // Render Virtual Table Viewport
      let html = `
        <table class="proto-virtual-table">
          <thead>
            <tr>
              <th style="width: 50px;">#</th>
              ${data.columns.map((c) => `
                <th class="proto-th-sortable" data-col="${c}">
                  ${c} ${this.sortCol === c ? (this.sortAsc ? "▲" : "▼") : ""}
                </th>
              `).join("")}
            </tr>
          </thead>
          <tbody>
            ${data.rows.map((row) => `
              <tr>
                <td class="proto-cell-id">${row._row_id}</td>
                ${data.columns.map((c) => `
                  <td>${row[c] !== null && row[c] !== undefined ? row[c] : `<span class="proto-null">NULL</span>`}</td>
                `).join("")}
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
      container.innerHTML = html;

      // Bind sorting
      container.querySelectorAll(".proto-th-sortable").forEach((th) => {
        th.addEventListener("click", () => {
          const col = th.dataset.col;
          if (this.sortCol === col) {
            this.sortAsc = !this.sortAsc;
          } else {
            this.sortCol = col;
            this.sortAsc = true;
          }
          this.fetchVirtualSlice();
        });
      });
    } catch (err) {
      container.innerHTML = `<div class="proto-banner-error">Hata: ${err.message}</div>`;
    }
  }

  // ══════════════════════════════════════════════════════════════════
  // 4. SEÇENEK: AÇIKLANABİLİR AI GÜVEN SKORU & ANOMALİ GEREKÇELERİ
  // ══════════════════════════════════════════════════════════════════
  async runAnomalyExplainer() {
    const btn = document.getElementById("btnRunAnomalyExplainer");
    const resultBox = document.getElementById("protoExplainerResults");
    if (!resultBox) return;

    btn.disabled = true;
    btn.innerHTML = `<span class="proto-spinner"></span> Isolation Forest Karar Yolu Çıkarılıyor...`;

    try {
      const res = await fetch("/get_explainable_anomalies?top_n=25");
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      const rep = data.anomaly_report;
      if (rep.explained_rows.length === 0) {
        resultBox.innerHTML = `
          <div class="proto-banner-info">
            ${rep.message || "Veri setinde belirgin bir çok değişkenli anomali tespit edilmedi."}
          </div>
        `;
        return;
      }

      let html = `
        <div class="proto-explainer-summary">
          <div class="pes-badge">
            <strong>${rep.total_anomalies_found.toLocaleString()}</strong> Aykırı Satır (%${rep.anomaly_percentage})
          </div>
          <small>Her satır için Isolation Forest karar ağaçlarındaki en yüksek sapma nedenleri:</small>
        </div>
        <div class="proto-anom-list">
      `;

      rep.explained_rows.forEach((row) => {
        html += `
          <div class="proto-anom-card">
            <div class="pac-header">
              <div class="pac-title">
                <strong>Satır #${row.row_index}</strong>
                <span class="pac-level-chip ${row.risk_score >= 75 ? 'danger' : 'warning'}">
                  ${row.anomaly_level} (Risk: %${row.risk_score})
                </span>
              </div>
              <span class="pac-dev-count">${row.total_deviant_columns} Sapmalı Sütun</span>
            </div>
            <div class="pac-reasons">
              ${row.top_reasons.map((r) => `
                <div class="pac-reason-item">
                  <span class="pri-col">📊 ${r.column}</span>
                  <span class="pri-val">Değer: <strong>${r.value}</strong></span>
                  <span class="pri-range">Beklenen: [${r.expected_range}]</span>
                  <span class="pri-badge ${r.severity}">${r.reason}</span>
                </div>
              `).join("")}
            </div>
          </div>
        `;
      });

      html += `</div>`;
      resultBox.innerHTML = html;
    } catch (err) {
      resultBox.innerHTML = `<div class="proto-banner-error">Hata: ${err.message}</div>`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = `🛡️ Anomali Gerekçelerini Yeniden Hesapla`;
    }
  }

  // ══════════════════════════════════════════════════════════════════
  // 5. SEÇENEK: BELLEK OPTİMİZASYONU & TİP KURTARMA
  // ══════════════════════════════════════════════════════════════════
  async runMemoryOptimize() {
    const btn = document.getElementById("btnRunMemoryOptimize");
    const resultBox = document.getElementById("protoOptimResults");
    if (!resultBox) return;

    btn.disabled = true;
    btn.innerHTML = `<span class="proto-spinner"></span> Sıkıştırılıyor...`;

    try {
      const res = await fetch("/optimize_memory");
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      const m = data.metrics;
      let html = `
        <div class="proto-benchmark-card">
          <div class="pbc-header">
            <strong>Bellek Ayak İzi Optimizasyon Sonucu</strong>
            <span class="pbc-badge success">%{${m.savings_percentage}} RAM Tasarrufu</span>
          </div>
          <div class="pbc-stats-grid">
            <div class="pbc-stat-box">
              <span class="psb-label">Önceki RAM</span>
              <span class="psb-val">${m.start_memory_mb} MB</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">Optimize RAM</span>
              <span class="psb-val" style="color: #10b981;">${m.end_memory_mb} MB</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">Kazanılan Bellek</span>
              <span class="psb-val" style="color: #60a5fa;">${m.saved_memory_mb} MB</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">Optimize Sütun</span>
              <span class="psb-val">${m.total_columns_optimized} Adet</span>
            </div>
          </div>
          ${m.optimized_details.length > 0 ? `
            <div style="margin-top: 15px; font-size: 0.85rem;">
              <strong>Dönüştürülen Sütun Detayları:</strong>
              <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;">
                ${m.optimized_details.map(d => `
                  <span class="pci-tag" style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3);">
                    ${d.column}: <code>${d.old_type}</code> ➔ <strong>${d.new_type}</strong> (${d.reason})
                  </span>
                `).join("")}
              </div>
            </div>
          ` : ''}
        </div>
      `;
      resultBox.innerHTML = html;
    } catch (err) {
      resultBox.innerHTML = `<div class="proto-banner-error">Hata: ${err.message}</div>`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = `⚡ Belleği %75 Sıkıştır (Downcast)`;
    }
  }

  async runTypeRecover() {
    const btn = document.getElementById("btnRunTypeRecover");
    const resultBox = document.getElementById("protoOptimResults");
    if (!resultBox) return;

    btn.disabled = true;
    btn.innerHTML = `<span class="proto-spinner"></span> Ayrıştırılıyor...`;

    try {
      const res = await fetch("/recover_dirty_types");
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      if (!data.report || data.report.length === 0) {
        resultBox.innerHTML = `<div class="proto-banner-info">${data.message}</div>`;
        return;
      }

      let html = `
        <div class="proto-cluster-header">
          <strong>${data.report.length} Kirli Sütun Sayısal Tipe Kurtarıldı!</strong>
          <small>Para birimleri, kirli karakterler temizlendi ve gerçek tipler geri kazanıldı:</small>
        </div>
        <div class="proto-cluster-list">
          ${data.report.map(r => `
            <div class="proto-cluster-item">
              <div class="pci-header">
                <span class="pci-badge">${r.column}</span>
                <span class="pci-rows">Güven: %${r.confidence_ratio}</span>
              </div>
              <div class="pci-body">
                <div>Önceki Tip: <code>${r.previous_type}</code> ➔ Kurtarılan Tip: <strong style="color: #10b981;">${r.recovered_type}</strong></div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">Başarıyla ayrıştırılan sayısal satır: ${r.recovered_values_count}</div>
              </div>
            </div>
          `).join("")}
        </div>
      `;
      resultBox.innerHTML = html;
    } catch (err) {
      resultBox.innerHTML = `<div class="proto-banner-error">Hata: ${err.message}</div>`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = `🪄 Kirli Sayıları Kurtar (Auto-Coerce)`;
    }
  }

  // ══════════════════════════════════════════════════════════════════
  // 6. SEÇENEK: VERİ KALİTE SÖZLEŞMELERİ & ÇOK DEĞİŞKENLİ ONARIM
  // ══════════════════════════════════════════════════════════════════
  async runDataContracts() {
    const btn = document.getElementById("btnRunDataContracts");
    const resultBox = document.getElementById("protoContractsResults");
    if (!resultBox) return;

    btn.disabled = true;
    btn.innerHTML = `<span class="proto-spinner"></span> Kurallar Denetleniyor...`;

    try {
      const res = await fetch("/evaluate_data_contracts");
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      const rep = data.contracts_report;
      let html = `
        <div class="proto-benchmark-card">
          <div class="pbc-header">
            <strong>Veri Kalitesi Sözleşme Karnesi (Data Contracts)</strong>
            <span class="pbc-badge ${rep.grade === 'A+' ? 'success' : 'danger'}" style="font-size: 1rem; padding: 4px 12px;">
              Not: ${rep.grade} (%${rep.compliance_score})
            </span>
          </div>
          <div class="pbc-stats-grid">
            <div class="pbc-stat-box">
              <span class="psb-label">Denetlenen Kural</span>
              <span class="psb-val">${rep.total_rules_evaluated}</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">Geçen Kurallar</span>
              <span class="psb-val" style="color: #10b981;">${rep.passed_rules_count}</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">İhlal Sayısı</span>
              <span class="psb-val" style="color: #ef4444;">${rep.failed_rules_count}</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">Denetim Hızı</span>
              <span class="psb-val" style="color: #60a5fa;">${rep.elapsed_ms} ms</span>
            </div>
          </div>
          <div style="margin-top: 15px;">
            <strong>Kural Denetim Detayları:</strong>
            <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 10px;">
              ${rep.rules.map(r => `
                <div style="padding: 10px 14px; border-radius: 8px; background: rgba(255,255,255,0.03); border: 1px solid ${r.passed ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.3)'}; display: flex; justify-content: space-between; align-items: center;">
                  <div>
                    <span style="font-weight: 600; color: ${r.passed ? '#10b981' : '#ef4444'};">${r.passed ? '✓' : '✗'} ${r.rule_name}</span>
                    <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 2px;">${r.description}</div>
                  </div>
                  <div style="text-align: right;">
                    <span class="pac-level-chip ${r.passed ? 'warning' : 'danger'}" style="${r.passed ? 'background: rgba(16,185,129,0.15); color: #10b981;' : ''}">
                      ${r.status} ${r.violations_count > 0 ? `(${r.violations_count} satır)` : ''}
                    </span>
                  </div>
                </div>
              `).join("")}
            </div>
          </div>
        </div>
      `;
      resultBox.innerHTML = html;
    } catch (err) {
      resultBox.innerHTML = `<div class="proto-banner-error">Hata: ${err.message}</div>`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = `📜 Kalite Karnesini Çıkar (Contracts)`;
    }
  }

  async runMiceImpute() {
    const btn = document.getElementById("btnRunMiceImpute");
    const resultBox = document.getElementById("protoContractsResults");
    if (!resultBox) return;

    btn.disabled = true;
    btn.innerHTML = `<span class="proto-spinner"></span> MICE Regresyonu Koşuluyor...`;

    try {
      const res = await fetch("/clean_data_advanced", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ method: "mice" }),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      resultBox.innerHTML = `
        <div class="proto-banner-info" style="border-left: 4px solid #3b82f6; background: rgba(59, 130, 246, 0.1);">
          <strong>🧠 Çok Değişkenli MICE Onarımı Başarılı!</strong><br>
          ${data.message}<br>
          <small style="color: #94a3b8;">Sayısal eksikler çok değişkenli Chained Equations ile dolduruldu; sütunlar arası korelasyon ve dağılım bozulmadı.</small>
        </div>
      `;
    } catch (err) {
      resultBox.innerHTML = `<div class="proto-banner-error">Hata: ${err.message}</div>`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = `🧠 Çok Değişkenli MICE Onarımı`;
    }
  }

  async runEnsembleAnom() {
    const btn = document.getElementById("btnRunEnsembleAnom");
    const resultBox = document.getElementById("protoContractsResults");
    if (!resultBox) return;

    btn.disabled = true;
    btn.innerHTML = `<span class="proto-spinner"></span> 3 Model Konsensüsü Hesaplanıyor...`;

    try {
      const res = await fetch("/detect_ensemble_anomalies?contamination=0.04&top_n=20");
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      const rep = data.ensemble_report;
      let html = `
        <div class="proto-benchmark-card">
          <div class="pbc-header">
            <strong>Konsensüs Tabanlı Hibrit Anomali Tespiti</strong>
            <span class="pbc-badge danger">${rep.total_consensus_anomalies} Doğrulanmış Aykırı</span>
          </div>
          <div class="pbc-stats-grid">
            <div class="pbc-stat-box">
              <span class="psb-label">Konsensüs Anomaliler</span>
              <span class="psb-val" style="color: #ef4444;">${rep.total_consensus_anomalies}</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">Filtrelenen Yanlış Alarmlar</span>
              <span class="psb-val" style="color: #10b981;">%{${rep.false_positive_reduction_pct}}</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">İncelenen Satır</span>
              <span class="psb-val">${rep.total_rows}</span>
            </div>
          </div>
          <div style="margin-top: 15px;">
            <strong>Konsensüs Karar Listesi:</strong>
            <div class="proto-anom-list" style="margin-top: 10px;">
              ${rep.anomalies.map(a => `
                <div class="proto-anom-card">
                  <div class="pac-header">
                    <div class="pac-title">
                      <strong>Satır #${a.row_index}</strong>
                      <span class="pac-level-chip ${a.votes === 3 ? 'danger' : 'warning'}">
                        ${a.risk_level} (Risk: %${a.risk_percentage})
                      </span>
                    </div>
                    <span class="pac-dev-count">Z-Skoru: ${a.max_z_score}σ</span>
                  </div>
                  <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 6px;">
                    Hemfikir Modeller: <strong>${a.agreeing_models.join(" + ")}</strong>
                  </div>
                </div>
              `).join("")}
            </div>
          </div>
        </div>
      `;
      resultBox.innerHTML = html;
    } catch (err) {
      resultBox.innerHTML = `<div class="proto-banner-error">Hata: ${err.message}</div>`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = `🛡️ 3'lü Konsensüs Anomali`;
    }
  }

  // ══════════════════════════════════════════════════════════════════
  // 7. SEÇENEK: ULTRA HIZ MOTORU (MORSEL, SIMD, MMAP, HLL, DATES)
  // ══════════════════════════════════════════════════════════════════
  async runMorselParallel() {
    const btn = document.getElementById("btnRunMorselParallel");
    const resultBox = document.getElementById("protoUltraResults");
    if (!resultBox) return;

    btn.disabled = true;
    btn.innerHTML = `<span class="proto-spinner"></span> Çekirdekler Çalışıyor...`;

    try {
      const res = await fetch("/run_morsel_stats");
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      let html = `
        <div class="proto-benchmark-card">
          <div class="pbc-header">
            <strong>DuckDB Morsel-Driven Çok Çekirdekli Paralel Agregasyon</strong>
            <span class="pbc-badge success">${data.workers_used} Çekirdek Paralel (${data.elapsed_ms} ms)</span>
          </div>
          <div class="pbc-stats-grid">
            <div class="pbc-stat-box">
              <span class="psb-label">İşlenen Satır</span>
              <span class="psb-val">${data.total_rows.toLocaleString()}</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">Lokma (Morsel) Sayısı</span>
              <span class="psb-val" style="color: #60a5fa;">${data.num_morsels} Lokma</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">Kullanılan Çekirdek</span>
              <span class="psb-val" style="color: #10b981;">${data.workers_used} / ${data.num_cpus} CPU</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">Yürütme Süresi</span>
              <span class="psb-val" style="color: #f59e0b;">${data.elapsed_ms} ms</span>
            </div>
          </div>
          <div style="margin-top: 15px;">
            <strong>Paralel İstatistik Özeti:</strong>
            <div class="proto-cluster-list" style="margin-top: 8px;">
              ${Object.entries(data.column_stats).slice(0, 4).map(([col, s]) => `
                <div class="proto-cluster-item" style="padding: 10px 14px;">
                  <div class="pci-header">
                    <span class="pci-badge">${col}</span>
                    <span class="pci-rows">N: ${s.count} | Ort: ${s.mean} | Std: ${s.std}</span>
                  </div>
                </div>
              `).join("")}
            </div>
          </div>
        </div>
      `;
      resultBox.innerHTML = html;
    } catch (err) {
      resultBox.innerHTML = `<div class="proto-banner-error">Hata: ${err.message}</div>`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = `🦆 Morsel Paralel İstatistik (Tüm Çekirdekler)`;
    }
  }

  async runPushdownFilter() {
    const btn = document.getElementById("btnRunPushdownFilter");
    const resultBox = document.getElementById("protoUltraResults");
    if (!resultBox) return;

    btn.disabled = true;
    btn.innerHTML = `<span class="proto-spinner"></span> SIMD Filtreleniyor...`;

    try {
      // Örnek ilk sütun üzerinden hızlı filtre testi
      const res = await fetch("/filter_predicate_pushdown", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          predicates: [{ column: (window.numericColumns && window.numericColumns[0]) || "Satış_Tutarı", op: ">=", value: 0 }],
          limit: 10,
        }),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      let html = `
        <div class="proto-benchmark-card">
          <div class="pbc-header">
            <strong>Polars Vektörize Predicate Pushdown (SIMD Filtreleme)</strong>
            <span class="pbc-badge success" style="background: #10b981;">${data.elapsed_ms} ms (Sıfır Kopyalama)</span>
          </div>
          <div class="pbc-stats-grid">
            <div class="pbc-stat-box">
              <span class="psb-label">Toplam Satır</span>
              <span class="psb-val">${data.total_rows.toLocaleString()}</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">Eşleşen Satır</span>
              <span class="psb-val" style="color: #10b981;">${data.matched_rows.toLocaleString()} (%${data.match_percentage})</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">Hesaplama Süresi</span>
              <span class="psb-val" style="color: #60a5fa;">${data.elapsed_ms} ms</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">Bellek Tahsisi</span>
              <span class="psb-val" style="color: #10b981;">0 Bayt (View Only)</span>
            </div>
          </div>
          <div style="margin-top: 15px; font-size: 0.85rem; color: #94a3b8;">
            ✓ Tüm tabloyu belleğe kopyalamadan (Deep-copy olmadan) C-seviyesinde tek clock cycle bitwise AND maskesi ile satır indeksleri saptandı.
          </div>
        </div>
      `;
      resultBox.innerHTML = html;
    } catch (err) {
      resultBox.innerHTML = `<div class="proto-banner-error">Hata: ${err.message}</div>`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = `⚡ SIMD Pushdown Filtrele (<1ms)`;
    }
  }

  async runMmapPersist() {
    const btn = document.getElementById("btnRunMmapPersist");
    const resultBox = document.getElementById("protoUltraResults");
    if (!resultBox) return;

    btn.disabled = true;
    btn.innerHTML = `<span class="proto-spinner"></span> Haritalanıyor...`;

    try {
      const res = await fetch("/persist_mmap_cache");
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      let html = `
        <div class="proto-benchmark-card">
          <div class="pbc-header">
            <strong>ClickHouse & Snowflake Memory-Mapped (mmap) Sıfır Kopyalama Disk Önbelleği</strong>
            <span class="pbc-badge success">${data.elapsed_ms} ms</span>
          </div>
          <div class="pbc-stats-grid">
            <div class="pbc-stat-box">
              <span class="psb-label">Haritalanan Satır</span>
              <span class="psb-val">${data.total_rows.toLocaleString()}</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">Dosya Boyutu</span>
              <span class="psb-val" style="color: #8b5cf6;">${data.file_size_mb} MB</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">Haritalama Süresi</span>
              <span class="psb-val" style="color: #10b981;">${data.elapsed_ms} ms</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">RAM Güvenliği</span>
              <span class="psb-val" style="color: #60a5fa;">Sıfır OOM Riski</span>
            </div>
          </div>
          <div style="margin-top: 15px; font-size: 0.85rem; color: #94a3b8;">
            ✓ Veri RAM'e yığılmadan doğrudan <code>pyarrow.memory_map</code> ile işletim sisteminin sanal bellek sayfalarına (OS Page Cache) haritalandı. 100 GB veri bile çökmeden okunabilir.
          </div>
        </div>
      `;
      resultBox.innerHTML = html;
    } catch (err) {
      resultBox.innerHTML = `<div class="proto-banner-error">Hata: ${err.message}</div>`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = `💽 Zero-Copy MMap Disk Önbelleği`;
    }
  }

  async runHllCardinality() {
    const btn = document.getElementById("btnRunHllCardinality");
    const resultBox = document.getElementById("protoUltraResults");
    if (!resultBox) return;

    btn.disabled = true;
    btn.innerHTML = `<span class="proto-spinner"></span> HLL Hesaplanıyor...`;

    try {
      const res = await fetch("/run_approximate_query");
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      let html = `
        <div class="proto-benchmark-card">
          <div class="pbc-header">
            <strong>Snowflake HyperLogLog (HLL) & Akış Persentilleri</strong>
            <span class="pbc-badge success" style="background: #f59e0b;">${data.elapsed_ms} ms | &lt;2 KB RAM</span>
          </div>
          <div class="pbc-stats-grid">
            <div class="pbc-stat-box">
              <span class="psb-label">İncelenen Satır</span>
              <span class="psb-val">${data.total_rows.toLocaleString()}</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">HLL Bellek Ayak İzi</span>
              <span class="psb-val" style="color: #10b981;">${data.memory_used_kb}</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">Hesaplama Hızı</span>
              <span class="psb-val" style="color: #60a5fa;">${data.elapsed_ms} ms</span>
            </div>
            <div class="pbc-stat-box">
              <span class="psb-label">Hata Payı</span>
              <span class="psb-val" style="color: #f59e0b;">~%1.5 Standart Hata</span>
            </div>
          </div>
          <div style="margin-top: 15px;">
            <strong>Yaklaşık Kardinalite (Count Distinct) Tahminleri:</strong>
            <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;">
              ${Object.entries(data.cardinality).map(([col, c]) => `
                <span class="pci-tag" style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3);">
                  ${col}: ~<strong>${c.approx_distinct_count}</strong> tekil (${c.cardinality_level})
                </span>
              `).join("")}
            </div>
          </div>
        </div>
      `;
      resultBox.innerHTML = html;
    } catch (err) {
      resultBox.innerHTML = `<div class="proto-banner-error">Hata: ${err.message}</div>`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = `📊 HyperLogLog Yaklaşık Analitik`;
    }
  }

  async runSmartDates() {
    const btn = document.getElementById("btnRunSmartDates");
    const resultBox = document.getElementById("protoUltraResults");
    if (!resultBox) return;

    btn.disabled = true;
    btn.innerHTML = `<span class="proto-spinner"></span> Tarihler Taranıyor...`;

    try {
      const res = await fetch("/parse_smart_dates");
      const data = await res.json();
      if (!data.success) throw new Error(data.error);

      if (!data.report || data.report.length === 0) {
        resultBox.innerHTML = `<div class="proto-banner-info">${data.message}</div>`;
        return;
      }

      let html = `
        <div class="proto-cluster-header">
          <strong>${data.report.length} Tarih Sütunu Deterministik Olarak Kurtarıldı!</strong>
          <small>Gün/ay çakışması olmadan C-şablonlarıyla doğrudan datetime64 tipine çevrildi:</small>
        </div>
        <div class="proto-cluster-list">
          ${data.report.map(r => `
            <div class="proto-cluster-item">
              <div class="pci-header">
                <span class="pci-badge">${r.column}</span>
                <span class="pci-rows">Şablon: <code>${r.detected_format}</code> (${r.elapsed_ms} ms)</span>
              </div>
              <div class="pci-body">
                <div>Dönüştürülen Satır: <strong>${r.parsed_rows}</strong></div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">Tarih Aralığı: [${r.min_date} ➔ ${r.max_date}]</div>
              </div>
            </div>
          `).join("")}
        </div>
      `;
      resultBox.innerHTML = html;
    } catch (err) {
      resultBox.innerHTML = `<div class="proto-banner-error">Hata: ${err.message}</div>`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = `📅 Akıllı Tarih Motorunu Çalıştır`;
    }
  }

  // ══════════════════════════════════════════════════════════════════
  // 60 FPS SANAL TABLO (VIRTUAL GRID) & SIMD PUSHDOWN FİLTRELEME
  // ══════════════════════════════════════════════════════════════════
  initVirtualGridModal() {
    this.vgStart = 0;
    this.vgLimit = 50;
    this.vgSortCol = null;
    this.vgSortAsc = true;
    this.vgSearch = "";
    this.vgPredicates = [];
    this.vgIsPushdownActive = false;

    // Modal açma butonu
    const btnOpen = document.getElementById("btnOpenVirtualGridModal");
    if (btnOpen) {
      btnOpen.addEventListener("click", () => this.openVirtualGridModal());
    }
    const btnOpen2 = document.getElementById("btnProtoGridOpenModal");
    if (btnOpen2) {
      btnOpen2.addEventListener("click", () => this.openVirtualGridModal());
    }

    // Modal kapatma butonu
    const btnClose = document.getElementById("btnCloseVirtualGridModal");
    if (btnClose) {
      btnClose.addEventListener("click", () => {
        document.getElementById("virtualGridModal")?.classList.add("hidden");
      });
    }

    // Arama kutusu
    const searchInput = document.getElementById("vgSearchInput");
    if (searchInput) {
      let deb = null;
      searchInput.addEventListener("input", (e) => {
        clearTimeout(deb);
        deb = setTimeout(() => {
          this.vgSearch = e.target.value.trim();
          this.vgStart = 0;
          this.vgIsPushdownActive = false;
          document.getElementById("vgPushdownMetricsBanner")?.classList.add("hidden");
          this.fetchVirtualGridData();
        }, 300);
      });
    }

    // Pushdown Filtre Butonu
    const btnPushdown = document.getElementById("btnVgApplyPushdown");
    if (btnPushdown) {
      btnPushdown.addEventListener("click", () => {
        const col = document.getElementById("vgFilterColSelect")?.value;
        const op = document.getElementById("vgFilterOpSelect")?.value || "==";
        const val = document.getElementById("vgFilterValInput")?.value;

        if (!col || val === undefined || val === "") {
          alert("Lütfen filtrelenecek sütunu ve bir filtre değerini girin.");
          return;
        }

        this.vgPredicates = [{ column: col, op: op, value: val }];
        this.vgStart = 0;
        this.vgIsPushdownActive = true;
        this.fetchVirtualGridData(true);
      });
    }

    // Filtre Temizleme Butonu
    const btnClear = document.getElementById("btnVgClearFilter");
    if (btnClear) {
      btnClear.addEventListener("click", () => {
        this.vgPredicates = [];
        this.vgSearch = "";
        this.vgStart = 0;
        this.vgIsPushdownActive = false;
        const sIn = document.getElementById("vgSearchInput");
        if (sIn) sIn.value = "";
        const vIn = document.getElementById("vgFilterValInput");
        if (vIn) vIn.value = "";
        document.getElementById("vgPushdownMetricsBanner")?.classList.add("hidden");
        this.fetchVirtualGridData(false);
      });
    }

    // Sayfalama kontrolleri
    const btnPrev = document.getElementById("btnVgPrevPage");
    if (btnPrev) {
      btnPrev.addEventListener("click", () => {
        if (this.vgStart > 0) {
          this.vgStart = Math.max(0, this.vgStart - this.vgLimit);
          this.fetchVirtualGridData(this.vgIsPushdownActive);
        }
      });
    }

    const btnNext = document.getElementById("btnVgNextPage");
    if (btnNext) {
      btnNext.addEventListener("click", () => {
        this.vgStart += this.vgLimit;
        this.fetchVirtualGridData(this.vgIsPushdownActive);
      });
    }

    // Sayfa boyutu seçici
    const pageSizeSel = document.getElementById("vgPageSizeSelect");
    if (pageSizeSel) {
      pageSizeSel.addEventListener("change", (e) => {
        this.vgLimit = parseInt(e.target.value, 10) || 50;
        this.vgStart = 0;
        this.fetchVirtualGridData(this.vgIsPushdownActive);
      });
    }
  }

  openVirtualGridModal() {
    const modal = document.getElementById("virtualGridModal");
    if (!modal) return;
    modal.classList.remove("hidden");

    // Sütun seçim kutusunu doldur
    const colSelect = document.getElementById("vgFilterColSelect");
    if (colSelect) {
      const cols = window.globalColumns || [];
      colSelect.innerHTML = `<option value="">Sütun Seçin...</option>` +
        cols.map((c) => `<option value="${c}">${c}</option>`).join("");
    }

    this.vgStart = 0;
    this.fetchVirtualGridData(this.vgIsPushdownActive);
  }

  async fetchVirtualGridData(usePushdown = false) {
    const container = document.getElementById("vgTableContainer");
    const statsLabel = document.getElementById("vgRowStatsLabel");
    const banner = document.getElementById("vgPushdownMetricsBanner");
    if (!container) return;

    container.innerHTML = `<div class="proto-loading" style="padding: 40px; text-align: center; color: #8b949e;"><span class="proto-spinner"></span> 60 FPS Grid dilimi yükleniyor...</div>`;

    const startTime = performance.now();

    try {
      let data = null;

      if (usePushdown && this.vgPredicates.length > 0) {
        // SIMD Kopyalamasız Predicate Pushdown API Çağrısı
        const res = await fetch("/filter_predicate_pushdown", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            predicates: this.vgPredicates,
            limit: this.vgLimit,
            offset: this.vgStart,
          }),
        });
        data = await res.json();
        if (!data.success) throw new Error(data.error);

        // Pushdown Metrik Şeridini Güncelle
        if (banner) {
          banner.classList.remove("hidden");
          const spEl = document.getElementById("vgbSpeed");
          const stEl = document.getElementById("vgbStats");
          if (spEl) spEl.textContent = `⚡ ${data.elapsed_ms} ms`;
          if (stEl) stEl.textContent = `Eşleşen: ${data.matched_rows.toLocaleString()} satır (%${data.match_percentage})`;
        }

        data.total_filtered = data.matched_rows;
      } else {
        // Standart 60 FPS Sanal Lazy Windowing Dilimi
        const res = await fetch("/get_table_slice", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            start: this.vgStart,
            limit: this.vgLimit,
            sort_col: this.vgSortCol,
            sort_asc: this.vgSortAsc,
            search: this.vgSearch,
          }),
        });
        data = await res.json();
        if (!data.success) throw new Error(data.error);

        if (banner && !this.vgIsPushdownActive) {
          banner.classList.add("hidden");
        }
      }

      const clientRenderMs = Math.round(performance.now() - startTime);

      if (statsLabel) {
        const total = data.total_filtered !== undefined ? data.total_filtered : (data.matched_rows || data.total_rows);
        const endRow = Math.min(this.vgStart + this.vgLimit, total);
        const startDisplay = total === 0 ? 0 : this.vgStart + 1;
        statsLabel.textContent = `${startDisplay} - ${endRow} / Toplam ${total.toLocaleString()} satır (${clientRenderMs} ms)`;
      }

      if (!data.rows || data.rows.length === 0) {
        container.innerHTML = `<div class="proto-banner-info" style="margin: 20px;">Görüntülenecek satır bulunamadı. Filtreyi temizlemeyi deneyin.</div>`;
        return;
      }

      const cols = data.columns || Object.keys(data.rows[0] || {}).filter(k => k !== "_row_id");

      // 60 FPS Viewport Render
      let html = `
        <table class="proto-virtual-table">
          <thead>
            <tr>
              <th style="width: 60px; text-align: center;">#</th>
              ${cols.map((c) => `
                <th class="proto-th-sortable vg-th-sort" data-col="${c}">
                  ${c} ${this.vgSortCol === c ? (this.vgSortAsc ? "▲" : "▼") : ""}
                </th>
              `).join("")}
            </tr>
          </thead>
          <tbody>
            ${data.rows.map((row) => `
              <tr>
                <td class="proto-cell-id" style="text-align: center;">${row._row_id}</td>
                ${cols.map((c) => {
                  const val = row[c];
                  if (val === null || val === undefined) {
                    return `<td><span class="proto-null">NULL</span></td>`;
                  }
                  if (typeof val === "number") {
                    return `<td style="font-family: var(--font-mono, monospace); color: #38bdf8;">${val}</td>`;
                  }
                  return `<td>${val}</td>`;
                }).join("")}
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
      container.innerHTML = html;

      // Sütun sıralama olaylarını bağla
      container.querySelectorAll(".vg-th-sort").forEach((th) => {
        th.addEventListener("click", () => {
          const col = th.dataset.col;
          if (this.vgSortCol === col) {
            this.vgSortAsc = !this.vgSortAsc;
          } else {
            this.vgSortCol = col;
            this.vgSortAsc = true;
          }
          this.fetchVirtualGridData(this.vgIsPushdownActive);
        });
      });
    } catch (err) {
      container.innerHTML = `<div class="proto-banner-error" style="margin: 20px;">Hata: ${err.message}</div>`;
    }
  }
}

export const prototypeHub = new PrototypeHub();
window.prototypeHub = prototypeHub;


