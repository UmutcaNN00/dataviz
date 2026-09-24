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

  if (mergeFileInput) mergeFileInput.value = "";
  if (mergeFileStatus) mergeFileStatus.style.display = "none";
  if (mergeConfigArea) mergeConfigArea.classList.add("hidden");
  if (btnExecuteMerge) btnExecuteMerge.disabled = true;
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
  if (!selectedFile2 && (!key1Val || !key2Val)) return;

  if (btnExecuteMerge) {
    btnExecuteMerge.disabled = true;
    btnExecuteMerge.textContent = "⏳ Birleştiriliyor...";
  }

  const fd = new FormData();
  if (selectedFile2) fd.append("file2", selectedFile2);
  fd.append("key1", key1Val);
  fd.append("key2", key2Val);
  fd.append("join_type", mergeJoinType ? mergeJoinType.value : "left");

  try {
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
    if (
      currentChartData &&
      currentPlotType &&
      typeof refreshActiveChart === "function"
    )
      refreshActiveChart();

    alert(
      `🎉 2. dosya başarıyla birleştirildi!\nToplam: ${data.total_rows} satır, ${data.total_cols} sütun.\nEklenen yeni sütunlar veri havuzunda '🔗' ikonu ile gösterilmektedir.`,
    );
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
