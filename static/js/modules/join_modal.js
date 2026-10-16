/* ════════════════════════════════════════════════════════════
   DATAVIZ PRO V6 — JOIN & MERGE MODAL MODULE
   İkinci Veri Seti Birleştirme (Join & Merge) Modalı
════════════════════════════════════════════════════════════ */

var selectedFile2 = null;

function openDataMergeModal() {
  selectedFile2 = null;
  const mergeFileInput = document.getElementById("mergeFileInput");
  const mergeFileStatus = document.getElementById("mergeFileStatus");
  const mergeConfigArea = document.getElementById("mergeConfigArea");
  const btnExecuteMerge = document.getElementById("btnExecuteMerge");
  const dataMergeModal = document.getElementById("dataMergeModal");

  const mergeJoinType = document.getElementById("mergeJoinType");
  const fuzzyThresholdGroup = document.getElementById("fuzzyThresholdGroup");

  if (mergeFileInput) mergeFileInput.value = "";
  if (mergeFileStatus) mergeFileStatus.style.display = "none";
  if (mergeConfigArea) mergeConfigArea.classList.add("hidden");
  if (btnExecuteMerge) btnExecuteMerge.disabled = true;
  if (mergeJoinType) mergeJoinType.value = "left";
  if (fuzzyThresholdGroup) fuzzyThresholdGroup.classList.add("hidden");
  dataMergeModal?.classList.remove("hidden");
}

async function previewSecondFile(file) {
  if (!file) return;
  selectedFile2 = file;
  const mergeFileStatus = document.getElementById("mergeFileStatus");
  const mergeKey1Select = document.getElementById("mergeKey1Select");
  const mergeKey2Select = document.getElementById("mergeKey2Select");
  const mergeConfigArea = document.getElementById("mergeConfigArea");
  const btnExecuteMerge = document.getElementById("btnExecuteMerge");

  if (mergeFileStatus) {
    mergeFileStatus.style.display = "block";
    mergeFileStatus.className = "status-msg loading";
    mergeFileStatus.textContent =
      "⏳ 2. dosya taranıyor ve ortak sütunlar aranıyor...";
  }

  const fd = new FormData();
  fd.append("file2", file);

  try {
    const res = await fetch("/preview_second_file", {
      method: "POST",
      body: fd,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Dosya okunamadı");

    if (mergeFileStatus) {
      mergeFileStatus.className = "status-msg success";
      mergeFileStatus.textContent = `✓ ${data.file2_name} (${data.file2_rows} satır, ${data.cols2.length} sütun)`;
    }

    if (mergeKey1Select) {
      mergeKey1Select.innerHTML = "";
      (data.cols1 || []).forEach((c) => {
        mergeKey1Select.innerHTML += `<option value="${c}" ${c === data.auto_key1 ? "selected" : ""}>${c}</option>`;
      });
    }

    if (mergeKey2Select) {
      mergeKey2Select.innerHTML = "";
      (data.cols2 || []).forEach((c) => {
        mergeKey2Select.innerHTML += `<option value="${c}" ${c === data.auto_key2 ? "selected" : ""}>${c}</option>`;
      });
    }

    if (mergeConfigArea) mergeConfigArea.classList.remove("hidden");
    if (btnExecuteMerge) btnExecuteMerge.disabled = false;
  } catch (err) {
    if (mergeFileStatus) {
      mergeFileStatus.className = "status-msg error";
      mergeFileStatus.textContent = `❌ ${err.message}`;
    }
  }
}

async function executeMerge() {
  const btnExecuteMerge = document.getElementById("btnExecuteMerge");
  const mergeKey1Select = document.getElementById("mergeKey1Select");
  const mergeKey2Select = document.getElementById("mergeKey2Select");
  const mergeJoinType = document.getElementById("mergeJoinType");
  const dataMergeModal = document.getElementById("dataMergeModal");

  const key1Val = mergeKey1Select ? mergeKey1Select.value : "";
  const key2Val = mergeKey2Select ? mergeKey2Select.value : "";
  if (!key1Val || !key2Val) return;

  const joinType = mergeJoinType ? mergeJoinType.value : "left";

  if (btnExecuteMerge) {
    btnExecuteMerge.disabled = true;
    btnExecuteMerge.textContent = "⏳ Birleştiriliyor...";
  }

  try {
    if (joinType === "fast_fuzzy") {
      // ⚡ Hızlı Bulanık Eşleştirme (Fast Fuzzy - LSH / Inverted Index Blocking)
      const thresholdInput = document.getElementById("fuzzyThresholdInput");
      const threshold = thresholdInput
        ? parseFloat(thresholdInput.value) / 100.0
        : 0.7;

      const res = await fetch("/fast_fuzzy_join", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          key1: key1Val,
          key2: key2Val,
          threshold: threshold,
        }),
      });
      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.error || "Hızlı bulanık birleştirme başarısız");
      }

      const metrics = data.metrics || {};
      const newCols = data.columns || [];

      if (data.numeric_columns) {
        numericColumns = window.numericColumns = data.numeric_columns;
        categoricalColumns = window.categoricalColumns = data.categorical_columns || [];
        globalColumns = window.globalColumns = [...categoricalColumns, ...numericColumns];
      }
      if (data.total_rows) {
        totalRows = window.totalRows = data.total_rows;
      }
      if (data.new_joined_columns) {
        joinedColumns = window.joinedColumns = Array.from(new Set([...(window.joinedColumns || []), ...data.new_joined_columns]));
      }
      activeFilters = window.activeFilters = [];

      // Sağlık ve sütun tiplerini senkronize et
      try {
        const hRes = await fetch("/check_health", { cache: "no-store" });
        const hData = await hRes.json();
        if (hRes.ok) {
          numericColumns = hData.numeric_columns || numericColumns;
          categoricalColumns = hData.categorical_columns || categoricalColumns;
          globalColumns = [...categoricalColumns, ...numericColumns];
          window.numericColumns = numericColumns;
          window.categoricalColumns = categoricalColumns;
          window.globalColumns = globalColumns;
        }
      } catch (_) {
        if (!data.numeric_columns) {
          globalColumns = newCols;
          window.globalColumns = globalColumns;
        }
      }

      dataMergeModal?.classList.add("hidden");
      if (typeof initDragDropPool === "function") initDragDropPool(true);
      if (typeof renderPivotPoolStructured === "function")
        renderPivotPoolStructured();
      if (typeof renderChartGrid === "function") renderChartGrid("all");
      if (typeof evaluateCharts === "function") evaluateCharts();
      if (typeof window.populateRegColumnSelects === "function")
        window.populateRegColumnSelects();
      if (typeof checkDataHealthAsync === "function") checkDataHealthAsync();
      if (
        currentChartData &&
        currentPlotType &&
        typeof refreshActiveChart === "function"
      ) {
        refreshActiveChart();
      }

      const summaryMsg =
        `⚡ Hızlı Bulanık Eşleştirme (Fast Fuzzy) Başarıyla Tamamlandı!\n\n` +
        `⏱️ İşlem Süresi: ${metrics.elapsed_ms || 0} ms\n` +
        `🎯 Eşleşen Benzersiz Anahtar: ${metrics.matched_unique_keys || 0}\n` +
        `📊 Birleştirilen Toplam Satır: ${data.new_row_count || 0}\n` +
        `🚀 Hesaplama Tasarrufu: %${metrics.computation_reduction_pct || 0}\n\n` +
        `Yeni sütunlar veri havuzuna ve tablonuza eklendi.`;

      if (typeof window.showDataPrepToast === "function") {
        window.showDataPrepToast({
          title: "⚡ Hızlı Bulanık Birleştirme Tamamlandı!",
          message: `${metrics.matched_unique_keys || 0} anahtar eşleştirildi (%${metrics.computation_reduction_pct || 0} hesaplama tasarrufu, ${metrics.elapsed_ms || 0} ms).`,
          type: "success",
          icon: "⚡",
          duration: 7000,
        });
      }

      alert(summaryMsg);
    } else {
      // Standart Tablo Birleştirme (Left / Inner / Outer)
      const fd = new FormData();
      if (selectedFile2) fd.append("file2", selectedFile2);
      fd.append("key1", key1Val);
      fd.append("key2", key2Val);
      fd.append("join_type", joinType);

      const res = await fetch("/merge_datasets", { method: "POST", body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Birleştirme işlemi başarısız");

      numericColumns = data.numeric_columns || [];
      categoricalColumns = data.categorical_columns || [];
      globalColumns = [...categoricalColumns, ...numericColumns];

      window.numericColumns = numericColumns;
      window.categoricalColumns = categoricalColumns;
      window.globalColumns = globalColumns;

      (data.new_joined_columns || []).forEach((c) => {
        if (!joinedColumns.includes(c)) joinedColumns.push(c);
      });
      window.joinedColumns = joinedColumns;

      activeFilters = [];
      window.activeFilters = activeFilters;
      if (typeof renderActiveFilterChips === "function")
        renderActiveFilterChips();

      dataMergeModal?.classList.add("hidden");
      if (typeof initDragDropPool === "function") initDragDropPool(true);
      if (typeof renderPivotPoolStructured === "function")
        renderPivotPoolStructured();
      if (typeof window.populateRegColumnSelects === "function")
        window.populateRegColumnSelects();
      if (typeof checkDataHealthAsync === "function") checkDataHealthAsync();
      if (
        currentChartData &&
        currentPlotType &&
        typeof refreshActiveChart === "function"
      )
        refreshActiveChart();

      alert(
        `🎉 2. dosya başarıyla birleştirildi!\nToplam: ${data.total_rows} satır, ${data.total_cols} sütun.\nEklenen yeni sütunlar veri havuzunda '🔗' ikonu ile gösterilmektedir.`,
      );
    }
  } catch (err) {
    alert("Birleştirme başarısız: " + err.message);
  } finally {
    if (btnExecuteMerge) {
      btnExecuteMerge.disabled = false;
      btnExecuteMerge.textContent = "⚡ Dosyaları Birleştir";
    }
  }
}

function initJoinModalListeners() {
  const dataMergeModal = document.getElementById("dataMergeModal");
  const mergeFileInput = document.getElementById("mergeFileInput");
  const mergeDropZone = document.getElementById("mergeDropZone");
  const btnExecuteMerge = document.getElementById("btnExecuteMerge");

  ["btnOpenMergeModal", "btnOpenMergeModalS2", "btnOpenMergeModalS3"].forEach(
    (id) => {
      document
        .getElementById(id)
        ?.addEventListener("click", openDataMergeModal);
    },
  );

  document
    .getElementById("btnCloseMergeModal")
    ?.addEventListener("click", () => {
      dataMergeModal?.classList.add("hidden");
    });
  document.getElementById("btnCancelMerge")?.addEventListener("click", () => {
    dataMergeModal?.classList.add("hidden");
  });

  if (mergeDropZone) {
    ["dragenter", "dragover", "dragleave", "drop"].forEach((name) => {
      mergeDropZone.addEventListener(name, (e) => {
        e.preventDefault();
        e.stopPropagation();
      });
    });
    mergeDropZone.addEventListener("dragover", () =>
      mergeDropZone.classList.add("dragover"),
    );
    mergeDropZone.addEventListener("dragleave", () =>
      mergeDropZone.classList.remove("dragover"),
    );
    mergeDropZone.addEventListener("drop", (e) => {
      mergeDropZone.classList.remove("dragover");
      if (
        e.dataTransfer &&
        e.dataTransfer.files &&
        e.dataTransfer.files.length
      ) {
        previewSecondFile(e.dataTransfer.files[0]);
      }
    });
    mergeDropZone.addEventListener("click", (e) => {
      if (e.target !== mergeFileInput) mergeFileInput?.click();
    });
  }

  mergeFileInput?.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      previewSecondFile(e.target.files[0]);
    }
  });

  btnExecuteMerge?.addEventListener("click", executeMerge);

  // Hızlı Bulanık Eşleştirme (Fast Fuzzy) Seçim ve Eşik Dinleyicileri
  const mergeJoinType = document.getElementById("mergeJoinType");
  const fuzzyThresholdGroup = document.getElementById("fuzzyThresholdGroup");
  const fuzzyThresholdInput = document.getElementById("fuzzyThresholdInput");
  const fuzzyThresholdBadge = document.getElementById("fuzzyThresholdBadge");

  mergeJoinType?.addEventListener("change", (e) => {
    if (e.target.value === "fast_fuzzy") {
      fuzzyThresholdGroup?.classList.remove("hidden");
    } else {
      fuzzyThresholdGroup?.classList.add("hidden");
    }
  });

  fuzzyThresholdInput?.addEventListener("input", (e) => {
    const val = e.target.value;
    if (fuzzyThresholdBadge) {
      fuzzyThresholdBadge.textContent = `%${val} (${(val / 100).toFixed(2)})`;
    }
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initJoinModalListeners);
} else {
  initJoinModalListeners();
}

// Window export
window.openDataMergeModal = openDataMergeModal;
window.previewSecondFile = previewSecondFile;
window.handleSecondFileSelect = previewSecondFile;
window.btnExecuteMerge = executeMerge;
window.executeMerge = executeMerge;
