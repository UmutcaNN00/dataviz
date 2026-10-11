/* ════════════════════════════════════════════════════════════
   DATAVIZ PRO V6 — DATA PREP MODULE
   Veri Sağlığı, Tip Onarımı & NaN Temizleme Modalı
════════════════════════════════════════════════════════════ */

var lastHealthData = null;
var isDataPrepBusy = false;
window.isDataPrepBusy = false;

function updateAnomalyBadges(healthData) {
  const anomCount = healthData?.anomalies?.length || 0;
  const s2Badge = document.getElementById("s2AnomalyBadge");
  const poolBadge = document.getElementById("poolAnomalyBadge");
  const s3Badge = document.getElementById("s3AnomalyBadge");

  [s2Badge, poolBadge, s3Badge].forEach((badge) => {
    if (badge) {
      if (anomCount > 0) {
        badge.textContent = anomCount;
        badge.classList.remove("hidden");
      } else {
        badge.classList.add("hidden");
      }
    }
  });
}

async function openDataPrepModal(targetTab = null, preloadedData = null) {
  const modal = document.getElementById("dataPrepModal");
  if (!modal) return;
  modal.classList.remove("hidden");

  const cardsList = document.getElementById("dpAnomalyCardsList");
  const headerBanner = document.getElementById("dpAnomalyHeaderBanner");
  const batchBar = document.getElementById("dpBatchActionBar");
  const anomTabCount = document.getElementById("dpAnomalyTabCount");
  const nanTabCount = document.getElementById("dpNanTabCount");
  const msgEl = document.getElementById("dpMessage");
  const missEl = document.getElementById("dpMissingRows");
  const totEl = document.getElementById("dpTotalRows");
  const missCellsEl = document.getElementById("dpMissingCells");
  const dropBtn = document.getElementById("dpDropBtn");
  const fillBtn = document.getElementById("dpFillBtn");
  const fillZeroBtn = document.getElementById("dpFillZeroBtn");
  const fillMiceBtn = document.getElementById("dpFillMiceBtn");
  const fillKnnBtn = document.getElementById("dpFillKnnBtn");

  let healthProg = null;
  if (!preloadedData) {
    document.getElementById("dpTabBtnAnomalies")?.click();
    healthProg = window.DataVizProgress?.start({
      icon: "🩺",
      title: "Veri Sağlığı Taranıyor",
      containerId: "dpAnomalyCardsList",
      showHud: false,
      stages: [
        {
          at: 0,
          short: "Sütun Taraması",
          label: "Sütun veri tipleri kontrol ediliyor...",
        },
        {
          at: 50,
          short: "Anomali Tespiti",
          label: "Sayısal alanlardaki sözel değerler aranıyor...",
        },
        {
          at: 80,
          short: "Eksik Hücreler",
          label: "Boş (NaN) hücre dağılımı hesaplanıyor...",
        },
      ],
    });
  }
  if (totEl && (!totEl.textContent || totEl.textContent === "0"))
    totEl.textContent = "...";
  if (
    missCellsEl &&
    (!missCellsEl.textContent || missCellsEl.textContent === "0")
  )
    missCellsEl.textContent = "...";
  if (missEl && (!missEl.textContent || missEl.textContent === "0"))
    missEl.textContent = "...";

  try {
    let data = preloadedData;
    if (!data) {
      const res = await fetch("/check_health", { cache: "no-store" });
      data = await res.json();
      if (!res.ok) throw new Error(data.error || "Veri kontrol edilemedi");
      healthProg?.complete("Tarama tamamlandı!");
    }
    lastHealthData = data;
    updateAnomalyBadges(data);

    const anomalies = data.anomalies || [];
    const hasAnomalies = anomalies.length > 0;

    // Tab Sayaçları
    if (anomTabCount) {
      if (hasAnomalies) {
        anomTabCount.textContent = anomalies.length;
        anomTabCount.classList.remove("hidden");
      } else {
        anomTabCount.classList.add("hidden");
      }
    }

    if (nanTabCount) {
      if (data.missing_rows > 0) {
        nanTabCount.textContent = data.missing_rows;
        nanTabCount.classList.remove("hidden");
      } else {
        nanTabCount.classList.add("hidden");
      }
    }

    // Hangi sekme aktif açılsın?
    if (targetTab === "ensemble") {
      document.getElementById("dpTabBtnEnsemble")?.click();
    } else if (targetTab === "nans" || (!hasAnomalies && data.missing_rows > 0)) {
      document.getElementById("dpTabBtnNans")?.click();
    } else {
      document.getElementById("dpTabBtnAnomalies")?.click();
    }

    // Arka planda 3'lü Konsensüs Anomali verilerini yükle
    fetchAndRenderEnsembleAnomalies().catch(() => {});

    // ── SEKME 1: ANOMALİ KARTLARI ──
    if (hasAnomalies) {
      if (headerBanner) {
        headerBanner.innerHTML = `
          <div class="dp-alert-banner dp-alert-danger">
            ⚠️ <strong>${anomalies.length} adet sütunda</strong> sayısal alana sözel işlem/metin girildiği tespit edildi. Bu sütunları grafiklerde sayısal eksen (Y) olarak kullanabilmek için aşağıdaki onarma yöntemlerinden birini uygulayın:
          </div>
        `;
      }
      if (batchBar) batchBar.classList.remove("hidden");

      if (cardsList) {
        const escHtml = (s) =>
          String(s ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
        cardsList.innerHTML = anomalies
          .map(
            (anom) => `
          <div class="dp-anomaly-card premium-glass-card">
            <div class="dp-anomaly-card-header">
              <div class="dp-anomaly-title-group">
                <div class="dp-anomaly-icon">⚠️</div>
                <div class="dp-anomaly-info">
                  <strong class="dp-col-name">${escHtml(anom.column)}</strong>
                  <span class="dp-col-stats">${anom.numeric_count} geçerli sayı / ${anom.total_rows} satır</span>
                </div>
              </div>
              <div class="dp-anomaly-badge">
                ${anom.invalid_count} hücre (%${anom.invalid_pct}) sözel
              </div>
            </div>

            <div class="dp-anomaly-samples">
              <span class="dp-samples-label">Tespit Edilen Sözel Değerler:</span>
              <div class="dp-samples-list">
                ${(anom.sample_invalid_values || []).map((val) => `<span class="dp-sample-tag">${escHtml(val)}</span>`).join("")}
              </div>
            </div>

            <div class="dp-anomaly-actions-row">
              <button type="button" class="btn-heal-col btn-glass-primary" data-col="${escHtml(anom.column)}" data-mode="smart_heal" title="Sayıları ayıklar, para/yüzde temizler, kalan sözelleri ortalamaya eşitler">
                🪄 Akıllı Onar (Sayı Ayıkla)
              </button>
              <button type="button" class="btn-heal-col btn-glass-secondary" data-col="${escHtml(anom.column)}" data-mode="fill_zero" title="Sözel değerleri 0 ile ikame eder">
                0️⃣ 0 Yap
              </button>
              <button type="button" class="btn-heal-col btn-glass-secondary" data-col="${escHtml(anom.column)}" data-mode="fill_mean" title="Sözel değerleri sütun ortalaması ile ikame eder">
                📈 Ortalamayla Doldur
              </button>
              <button type="button" class="btn-heal-col btn-glass-secondary" data-col="${escHtml(anom.column)}" data-mode="coerce_nan" title="Sözelleri boş (NaN) yapar, sütunu sayısal tipe geçirir">
                🗑️ Boş (NaN) Yap
              </button>
              <button type="button" class="btn-heal-col btn-glass-danger" data-col="${escHtml(anom.column)}" data-mode="drop_rows" title="Bu sütunda sözel değer olan satırları tablodan çıkarır">
                ❌ Satırları Sil
              </button>
              <button type="button" class="btn-cluster-col btn-glass-secondary" data-col="${escHtml(anom.column)}" title="Bu sütundaki metin varyasyonlarını ve yazım hatalarını kümele" style="color: #c084fc; border-color: rgba(168, 85, 247, 0.35);">
                🔤 Varyasyonları Kümele
              </button>
            </div>
          </div>
        `,
          )
          .join("");

        // Kart butonlarını bağla
        cardsList.querySelectorAll(".btn-heal-col").forEach((b) => {
          b.addEventListener("click", (e) => {
            const col = e.currentTarget.dataset.col;
            const mode = e.currentTarget.dataset.mode;
            callRepairColumn(col, mode);
          });
        });

        cardsList.querySelectorAll(".btn-cluster-col").forEach((b) => {
          b.addEventListener("click", (e) => {
            const col = e.currentTarget.dataset.col;
            openTextClusteringModal(col);
          });
        });
      }
    } else {
      if (headerBanner) {
        headerBanner.innerHTML = `
          <div class="dp-alert-banner dp-alert-success">
            ✓ <strong>Mükemmel!</strong> Veri setinizdeki tüm sayısal sütunlar saf ve hatasız. Sayısal alanlara sözel metin girilmemiş.
          </div>
        `;
      }
      if (batchBar) batchBar.classList.add("hidden");
      if (cardsList) cardsList.innerHTML = "";
    }

    // ── SEKME 2: NAN İSTATİSTİKLERİ ──
    if (totEl) totEl.textContent = data.total_rows || 0;
    if (missCellsEl) missCellsEl.textContent = data.missing_cells || 0;
    if (missEl) missEl.textContent = data.missing_rows || 0;

    if (data.missing_rows > 0) {
      if (msgEl)
        msgEl.innerHTML = `<span class="dp-nan-warn-text">⚠️ ${data.missing_rows} satırda toplam ${data.missing_cells} adet boş (NaN) hücre tespit edildi.</span><br>Grafiklerin ve istatistik testlerinin kusursuz çalışması için aşağıdaki yöntemlerden birini seçebilirsiniz:`;
      [dropBtn, fillBtn, fillZeroBtn, fillMiceBtn, fillKnnBtn].forEach((b) => {
        if (b) b.style.display = "inline-flex";
      });
    } else {
      if (msgEl)
        msgEl.innerHTML = `<span class="dp-nan-success-text">✓ Tebrikler! Veri setinizde hiç eksik değer (NaN) bulunmuyor.</span><br>Tüm satır ve sütunlar eksiksiz ve analize %100 hazır.`;
      [dropBtn, fillBtn, fillZeroBtn, fillMiceBtn, fillKnnBtn].forEach((b) => {
        if (b) b.style.display = "none";
      });
    }
  } catch (err) {
    if (cardsList)
      cardsList.innerHTML = `<div style="color:var(--red); padding:10px;">Hata: ${err.message}</div>`;
    if (msgEl)
      msgEl.innerHTML = `<span style="color:var(--red); font-weight:700;">Hata: ${err.message}</span>`;
    if (totEl && totEl.textContent === "...") totEl.textContent = "-";
    if (missCellsEl && missCellsEl.textContent === "...")
      missCellsEl.textContent = "-";
    if (missEl && missEl.textContent === "...") missEl.textContent = "-";
  }
}

async function callRepairColumn(columnName, mode) {
  if (isDataPrepBusy) return;
  isDataPrepBusy = window.isDataPrepBusy = true;

  const btnHealAll = document.getElementById("btnHealAllColumns");
  const batchBar = document.getElementById("dpBatchActionBar");
  const DEFAULT_HEAL_TEXT = "🪄 Tümünü Akıllı Onar";

  if (btnHealAll) {
    btnHealAll.disabled = true;
    btnHealAll.textContent = "⏳ Onarılıyor...";
  }
  if (batchBar) {
    batchBar.classList.add("hidden");
  }

  const colTitle =
    columnName === "__all__"
      ? "Tüm Uyumsuz Sütunlar"
      : `"${columnName}" Sütunu`;
  const prog = window.DataVizProgress?.start({
    icon: "🪄",
    title: `${colTitle} Onarılıyor`,
    containerId: "dpAnomalyCardsList",
    showHud: false,
    stages: [
      {
        at: 0,
        short: "Hücre Taraması",
        label: "Sözel ve bozuk hücreler ayıklanıyor...",
      },
      {
        at: 40,
        short: "Tip Dönüşümü",
        label: "Sayısal tip dönüşümü ve onarım uygulanıyor...",
      },
      {
        at: 78,
        short: "Senkronizasyon",
        label: "Veri havuzu ve önbellek güncelleniyor...",
      },
    ],
  });

  try {
    const res = await fetch("/repair_column_anomalies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ column: columnName, repair_mode: mode }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Onarma işlemi başarısız oldu.");

    // Buton metnini ve kilidini anında sıfırla ("Onarılıyor..." takılı kalmasın)
    if (btnHealAll) {
      btnHealAll.disabled = false;
      btnHealAll.textContent = DEFAULT_HEAL_TEXT;
    }

    numericColumns = data.numeric_columns || [];
    categoricalColumns = data.categorical_columns || [];
    globalColumns = [...categoricalColumns, ...numericColumns];

    window.numericColumns = numericColumns;
    window.categoricalColumns = categoricalColumns;
    window.globalColumns = globalColumns;

    if (typeof initDragDropPool === "function") initDragDropPool(true);
    if (typeof renderPivotPoolStructured === "function")
      renderPivotPoolStructured();
    if (typeof renderChartGrid === "function") renderChartGrid("all");
    if (typeof evaluateCharts === "function") evaluateCharts();
    if (typeof window.populateRegColumnSelects === "function")
      window.populateRegColumnSelects();
    const trustScreen = document.getElementById("screen-trust-studio");
    if (
      trustScreen &&
      !trustScreen.classList.contains("hidden") &&
      typeof window.fetchAndRenderTrustReport === "function"
    ) {
      window.fetchAndRenderTrustReport().catch(() => {});
    }

    if (
      currentChartData &&
      currentPlotType &&
      typeof refreshActiveChart === "function"
    ) {
      refreshActiveChart();
    }
    const regPane = document.getElementById("tabRegression");
    if (
      regPane &&
      !regPane.classList.contains("hidden") &&
      typeof window.fetchAndRenderRegressionStudio === "function"
    ) {
      window.fetchAndRenderRegressionStudio().catch(() => {});
    }
    const pivotScreen = document.getElementById("screen-pivot-studio");
    if (
      pivotScreen &&
      !pivotScreen.classList.contains("hidden") &&
      typeof refreshPivotStudio === "function"
    ) {
      refreshPivotStudio();
    }

    prog?.complete(`${colTitle} başarıyla onarıldı!`);
    await new Promise((r) => setTimeout(r, 180));
    await openDataPrepModal("anomalies", data.health || null);

    const headerBanner = document.getElementById("dpAnomalyHeaderBanner");
    if (headerBanner) {
      const colNameText =
        columnName === "__all__"
          ? "Tüm uyumsuz sütunlar"
          : `"${columnName}" sütunu`;
      headerBanner.insertAdjacentHTML(
        "afterbegin",
        `<div style="background:rgba(16,185,129,0.14); border:1px solid rgba(52,211,153,0.35); border-radius:8px; padding:10px 14px; margin-bottom:10px; font-size:0.85rem; color:#6ee7b7; line-height:1.45;">
          ✓ <strong>${colNameText}</strong> başarıyla sayısal tipe onarıldı ve veri havuzuna eklendi!
        </div>`,
      );
    }
  } catch (err) {
    prog?.stop();
    await openDataPrepModal("anomalies", lastHealthData);
    alert("Onarma Hatası: " + err.message);
  } finally {
    isDataPrepBusy = window.isDataPrepBusy = false;
    if (btnHealAll) {
      btnHealAll.disabled = false;
      btnHealAll.textContent = DEFAULT_HEAL_TEXT;
    }
  }
}

async function callCleanData(action) {
  if (isDataPrepBusy) return;
  isDataPrepBusy = window.isDataPrepBusy = true;

  const msgEl = document.getElementById("dpMessage");
  const origMsg = msgEl ? msgEl.innerHTML : "";
  const dropBtn = document.getElementById("dpDropBtn");
  const fillBtn = document.getElementById("dpFillBtn");
  const fillZeroBtn = document.getElementById("dpFillZeroBtn");
  const fillMiceBtn = document.getElementById("dpFillMiceBtn");
  const fillKnnBtn = document.getElementById("dpFillKnnBtn");
  [dropBtn, fillBtn, fillZeroBtn, fillMiceBtn, fillKnnBtn].forEach((b) => {
    if (b) b.disabled = true;
  });

  let progIcon = "🧹";
  let progTitle = "Eksik Değerler (NaN) Temizleniyor";
  if (action === "mice") {
    progIcon = "⚡";
    progTitle = "MICE Çok Değişkenli İkame Hesaplanıyor";
  } else if (action === "knn") {
    progIcon = "👥";
    progTitle = "KNN En Yakın Komşu İkamesi Hesaplanıyor";
  } else if (action === "fill_mean") {
    progIcon = "📈";
    progTitle = "Ortalama ile Tamamlanıyor";
  } else if (action === "fill_zero") {
    progIcon = "0️⃣";
    progTitle = "Sıfır ile Dolduruluyor";
  }

  const prog = window.DataVizProgress?.start({
    icon: progIcon,
    title: progTitle,
    containerId: "dpMessage",
    showHud: false,
    stages: [
      {
        at: 0,
        short: "Eksik Tespiti",
        label: "Boş (NaN) hücreler ve örüntüler analiz ediliyor...",
      },
      {
        at: 45,
        short: "İkame / Silme",
        label: "Seçilen onarma algoritması yürütülüyor...",
      },
      {
        at: 80,
        short: "Doğrulama",
        label: "Veri tablosu ve dağılımlar yeniden doğrulanıyor...",
      },
    ],
  });
  try {
    const res = await fetch("/clean_data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: action }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    numericColumns = data.numeric_columns || [];
    categoricalColumns = data.categorical_columns || [];
    globalColumns = [...categoricalColumns, ...numericColumns];

    window.numericColumns = numericColumns;
    window.categoricalColumns = categoricalColumns;
    window.globalColumns = globalColumns;

    if (typeof initDragDropPool === "function") initDragDropPool(true);
    if (typeof renderPivotPoolStructured === "function")
      renderPivotPoolStructured();
    if (typeof renderChartGrid === "function") renderChartGrid("all");
    if (typeof evaluateCharts === "function") evaluateCharts();
    if (typeof window.populateRegColumnSelects === "function")
      window.populateRegColumnSelects();
    const trustScreen = document.getElementById("screen-trust-studio");
    if (
      trustScreen &&
      !trustScreen.classList.contains("hidden") &&
      typeof window.fetchAndRenderTrustReport === "function"
    ) {
      window.fetchAndRenderTrustReport().catch(() => {});
    }
    if (
      currentChartData &&
      currentPlotType &&
      typeof refreshActiveChart === "function"
    )
      refreshActiveChart();
    const regPane = document.getElementById("tabRegression");
    if (
      regPane &&
      !regPane.classList.contains("hidden") &&
      typeof window.fetchAndRenderRegressionStudio === "function"
    ) {
      window.fetchAndRenderRegressionStudio().catch(() => {});
    }
    const pivotScreen = document.getElementById("screen-pivot-studio");
    if (
      pivotScreen &&
      !pivotScreen.classList.contains("hidden") &&
      typeof refreshPivotStudio === "function"
    ) {
      refreshPivotStudio();
    }

    prog?.complete("Eksik veriler başarıyla temizlendi!");
    await new Promise((r) => setTimeout(r, 180));
    await openDataPrepModal("nans", data.health || null);
  } catch (err) {
    prog?.stop();
    alert("Hata: " + err.message);
    if (msgEl) msgEl.innerHTML = origMsg;
  } finally {
    isDataPrepBusy = window.isDataPrepBusy = false;
    [dropBtn, fillBtn, fillZeroBtn, fillMiceBtn, fillKnnBtn].forEach((b) => {
      if (b) b.disabled = false;
    });
  }
}

function initDataPrepListeners() {
  // Modal Sekme Değiştirici
  document.querySelectorAll(".dp-tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".dp-tab-btn").forEach((b) => {
        b.classList.remove("active");
        b.style.background = "";
        b.style.color = "";
        b.style.borderColor = "";
      });
      document
        .querySelectorAll(".dp-pane")
        .forEach((p) => p.classList.add("hidden"));

      btn.classList.add("active");
      btn.style.background = "";
      btn.style.color = "";
      btn.style.borderColor = "";

      const tab = btn.dataset.dptab;
      if (tab === "anomalies") {
        document.getElementById("dpPaneAnomalies")?.classList.remove("hidden");
      } else if (tab === "ensemble") {
        document.getElementById("dpPaneEnsemble")?.classList.remove("hidden");
        fetchAndRenderEnsembleAnomalies();
      } else {
        document.getElementById("dpPaneNans")?.classList.remove("hidden");
      }
    });
  });

  // Konsensüs Anomali Yenile Butonu
  document.getElementById("btnRefreshEnsembleDataPrep")?.addEventListener("click", () => {
    fetchAndRenderEnsembleAnomalies(true);
  });

  // Toplu Onarım Butonu
  document
    .getElementById("btnHealAllColumns")
    ?.addEventListener("click", () => {
      callRepairColumn("__all__", "smart_heal");
    });

  // Modal Açma Butonları
  [
    "btnOpenDataPrepModalS2",
    "btnOpenDataPrepModalPool",
    "btnOpenDataPrepModalS3",
  ].forEach((id) => {
    document
      .getElementById(id)
      ?.addEventListener("click", () => openDataPrepModal());
  });

  // Modal Kapatma Butonu
  document
    .getElementById("btnCloseDataPrepModal")
    ?.addEventListener("click", () => {
      document.getElementById("dataPrepModal")?.classList.add("hidden");
    });

  // Atla / İlerle Butonu
  document.getElementById("dpSkipBtn")?.addEventListener("click", () => {
    document.getElementById("dataPrepModal")?.classList.add("hidden");
    if (document.getElementById("step1-upload")?.classList.contains("active")) {
      if (typeof proceedToStep2 === "function") {
        proceedToStep2();
      } else if (typeof window.proceedToStep2 === "function") {
        window.proceedToStep2();
      }
    }
  });

  // Temizleme Butonları
  document
    .getElementById("dpDropBtn")
    ?.addEventListener("click", () => callCleanData("drop"));
  document
    .getElementById("dpFillBtn")
    ?.addEventListener("click", () => callCleanData("fill_mean"));
  document
    .getElementById("dpFillZeroBtn")
    ?.addEventListener("click", () => callCleanData("fill_zero"));
  document
    .getElementById("dpFillMiceBtn")
    ?.addEventListener("click", () => callCleanData("mice"));
  document
    .getElementById("dpFillKnnBtn")
    ?.addEventListener("click", () => callCleanData("knn"));

  // Bellek Sıkıştırma & Kirli Sayı Kurtarma Ribbon Butonları
  document
    .getElementById("btnOptimizeMemory")
    ?.addEventListener("click", optimizeMemoryAction);
  document
    .getElementById("btnRecoverDirtyTypes")
    ?.addEventListener("click", recoverDirtyTypesAction);

  // Metin Kümeleme Modalı Butonları
  document
    .getElementById("btnOpenTextClusteringModal")
    ?.addEventListener("click", () => openTextClusteringModal());
  document
    .getElementById("btnCloseTextClusteringModal")
    ?.addEventListener("click", closeTextClusteringModal);
  document
    .getElementById("btnTcCloseBtn")
    ?.addEventListener("click", closeTextClusteringModal);
  document
    .getElementById("btnTcFindClusters")
    ?.addEventListener("click", findTextClustersAction);
}

// ══════════════════════════════════════════════════════════════════
// BİLDİRİM SİSTEMİ (TOAST NOTIFICATIONS)
// ══════════════════════════════════════════════════════════════════
function showDataPrepToast({
  title = "Bilgilendirme",
  message = "",
  type = "success",
  icon = "⚡",
  duration = 5000,
}) {
  let container = document.getElementById("datavizToastContainer");
  if (!container) {
    container = document.createElement("div");
    container.id = "datavizToastContainer";
    container.style.cssText =
      "position: fixed; top: 24px; right: 24px; z-index: 999999; display: flex; flex-direction: column; gap: 12px; pointer-events: none; max-width: 420px; width: calc(100% - 48px);";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `dataviz-toast-card dv-toast-${type}`;
  toast.innerHTML = `
    <div style="font-size: 1.4rem; line-height: 1; flex-shrink: 0; padding-top: 2px;">${icon}</div>
    <div style="flex: 1; min-width: 0;">
      <strong style="display: block; font-size: 0.92rem; color: #f5f5f7; margin-bottom: 3px;">${title}</strong>
      <div style="font-size: 0.8rem; color: #94a3b8; line-height: 1.45;">${message}</div>
    </div>
    <button type="button" style="background: none; border: none; color: #64748b; font-size: 1.1rem; cursor: pointer; padding: 0 4px; line-height: 1;" title="Kapat">×</button>
  `;

  const closeBtn = toast.querySelector("button");
  const removeToast = () => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(40px) scale(0.95)";
    setTimeout(() => toast.remove(), 300);
  };
  closeBtn?.addEventListener("click", removeToast);

  container.appendChild(toast);
  setTimeout(removeToast, duration);
}

// ══════════════════════════════════════════════════════════════════
// 1. BELLEK OPTİMİZASYONU (%75 DOWNCAST)
// ══════════════════════════════════════════════════════════════════
async function optimizeMemoryAction() {
  if (isDataPrepBusy) return;
  const btn = document.getElementById("btnOptimizeMemory");
  const origHtml = btn ? btn.innerHTML : "";

  try {
    isDataPrepBusy = window.isDataPrepBusy = true;
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span style="font-size: 0.85rem;">⏳</span> <span class="tool-label">Sıkıştırılıyor...</span>`;
    }

    const res = await fetch("/optimize_memory", { method: "POST" });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || "Bellek optimizasyonu yapılamadı.");
    }

    const m = data.metrics || {};
    showDataPrepToast({
      title: "⚡ Bellek Başarıyla Sıkıştırıldı!",
      message: `RAM tüketimi %${m.savings_percentage} oranında düşürüldü (${m.start_memory_mb} MB ➔ ${m.end_memory_mb} MB). Toplam ${m.total_columns_optimized} sütun daha kompakt veri tiplerine (uint/int/category) dönüştürüldü.`,
      type: "success",
      icon: "⚡",
      duration: 6000,
    });

    if (typeof checkDataHealthAsync === "function") checkDataHealthAsync();
    if (typeof renderChartGrid === "function") renderChartGrid("all");
    if (typeof evaluateCharts === "function") evaluateCharts();
  } catch (err) {
    showDataPrepToast({
      title: "Optimizasyon Hatası",
      message: err.message,
      type: "error",
      icon: "⚠️",
    });
  } finally {
    isDataPrepBusy = window.isDataPrepBusy = false;
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = origHtml;
    }
  }
}

// ══════════════════════════════════════════════════════════════════
// 2. KİRLİ SAYILARI KURTAR (TYPE RECOVERY & COERCION)
// ══════════════════════════════════════════════════════════════════
async function recoverDirtyTypesAction() {
  if (isDataPrepBusy) return;
  const btn = document.getElementById("btnRecoverDirtyTypes");
  const origHtml = btn ? btn.innerHTML : "";

  try {
    isDataPrepBusy = window.isDataPrepBusy = true;
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span style="font-size: 0.85rem;">⏳</span> <span class="tool-label">Kurtarılıyor...</span>`;
    }

    const res = await fetch("/recover_dirty_types", { method: "POST" });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || "Tip kurtarma işlemi başarısız.");
    }

    const count = data.recovered_columns_count || 0;
    if (count > 0) {
      const details = (data.report || [])
        .map(
          (r) =>
            `<strong>${r.column}</strong>: ${r.previous_type} ➔ ${r.recovered_type} (%${r.confidence_ratio} güven)`,
        )
        .join("<br>");

      showDataPrepToast({
        title: `🪄 ${count} Adet Kirli Sütun Sayısal Tipe Kurtarıldı!`,
        message: details,
        type: "success",
        icon: "🪄",
        duration: 7000,
      });

      // Sağlık ve sütun listelerini senkronize et
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
          updateAnomalyBadges(hData);
        }
      } catch (_) {}

      if (typeof initDragDropPool === "function") initDragDropPool(true);
      if (typeof renderPivotPoolStructured === "function")
        renderPivotPoolStructured();
      if (typeof renderChartGrid === "function") renderChartGrid("all");
      if (typeof evaluateCharts === "function") evaluateCharts();
      if (typeof window.populateRegColumnSelects === "function")
        window.populateRegColumnSelects();
    } else {
      showDataPrepToast({
        title: "Tipler Zaten Tutarlı",
        message:
          data.message ||
          "Kurtarılacak kirli sayısal sütun bulunamadı, tüm tipler tutarlı.",
        type: "info",
        icon: "✓",
        duration: 5000,
      });
    }
  } catch (err) {
    showDataPrepToast({
      title: "Tip Kurtarma Hatası",
      message: err.message,
      type: "error",
      icon: "⚠️",
    });
  } finally {
    isDataPrepBusy = window.isDataPrepBusy = false;
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = origHtml;
    }
  }
}

// ══════════════════════════════════════════════════════════════════
// 3. OPENREFINE METİN KÜMELEME & İYİLEŞTİRME (TEXT CLUSTERING)
// ══════════════════════════════════════════════════════════════════
function openTextClusteringModal(selectedCol = null) {
  const modal = document.getElementById("textClusteringModal");
  if (!modal) return;

  const sel = document.getElementById("tcColumnSelect");
  if (sel) {
    const catCols = window.categoricalColumns || categoricalColumns || [];
    const allCols = window.globalColumns || globalColumns || [];
    const targetCols = catCols.length > 0 ? catCols : allCols;

    if (targetCols.length === 0) {
      sel.innerHTML = `<option value="">Önce bir veri seti yükleyin</option>`;
    } else {
      sel.innerHTML = targetCols
        .map(
          (c) =>
            `<option value="${c}" ${c === selectedCol ? "selected" : ""}>${c}</option>`,
        )
        .join("");
    }
  }

  modal.classList.remove("hidden");
  if (selectedCol) {
    findTextClustersAction();
  }
}

function closeTextClusteringModal() {
  document.getElementById("textClusteringModal")?.classList.add("hidden");
}

async function findTextClustersAction() {
  const sel = document.getElementById("tcColumnSelect");
  const methodSel = document.getElementById("tcMethodSelect");
  const resultBox = document.getElementById("tcClustersResult");
  const statusMsg = document.getElementById("tcStatusMessage");
  const btn = document.getElementById("btnTcFindClusters");

  const col = sel?.value;
  const method = methodSel?.value || "fingerprint";

  if (!col) {
    showDataPrepToast({
      title: "Sütun Seçilmedi",
      message: "Lütfen kümelenecek metin sütununu seçin.",
      type: "error",
      icon: "⚠️",
    });
    return;
  }

  if (resultBox) {
    resultBox.innerHTML = `
      <div style="text-align: center; color: var(--muted); padding: 50px 10px;">
        <div style="font-size: 1.8rem; margin-bottom: 10px;">⏳</div>
        <div>OpenRefine <strong>${method}</strong> algoritması ile varyasyonlar taranıyor...</div>
      </div>
    `;
  }
  if (btn) btn.disabled = true;
  if (statusMsg) statusMsg.textContent = "Taranıyor...";

  try {
    const res = await fetch("/find_text_clusters", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ column: col, method: method, max_clusters: 50 }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || "Kümeleme hesaplanamadı.");
    }

    const clusters = data.clusters || [];
    if (statusMsg) {
      statusMsg.textContent = `${clusters.length} küme tespit edildi.`;
    }

    if (clusters.length === 0) {
      if (resultBox) {
        resultBox.innerHTML = `
          <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 12px; padding: 24px; text-align: center; color: #6ee7b7; margin: 10px 0;">
            <div style="font-size: 1.6rem; margin-bottom: 6px;">✓</div>
            <strong>Mükemmel! Bu Sütunda Yazım Varyasyonu Yok</strong>
            <p style="font-size: 0.82rem; color: #94a3b8; margin: 6px 0 0 0;">
              "<strong>${col}</strong>" sütununda <strong>${method}</strong> algoritmasıyla birleşecek farklı yazım hataları veya varyasyonlar bulunamadı. Veri zaten tutarlı!
            </p>
          </div>
        `;
      }
      return;
    }

    // Kümeleri kartlar olarak oluştur
    let html = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding: 4px 2px;">
        <div>
          <strong style="font-size: 0.95rem; color: #f5f5f7;">${clusters.length} Adet Benzer Küme Tespit Edildi</strong>
          <div style="font-size: 0.78rem; color: var(--muted); margin-top: 2px;">"${col}" sütunundaki farklı yazılmış varyasyonlar gruplandı.</div>
        </div>
        <button type="button" class="btn-primary" id="btnTcMergeAllClusters" style="background: linear-gradient(135deg, #10b981, #059669); font-size: 0.82rem; padding: 8px 14px; white-space: nowrap;">
          ⚡ Tümünü Standartlaştır (${clusters.length} Küme)
        </button>
      </div>
      <div style="display: flex; flex-direction: column; gap: 10px;">
    `;

    clusters.forEach((cl, idx) => {
      html += `
        <div id="tc-cluster-item-${idx}" style="background: #18181c; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 14px; transition: all 0.2s ease;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 0.76rem; background: rgba(168, 85, 247, 0.14); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700;">
                Anahtar: ${cl.key}
              </span>
              <span style="font-size: 0.76rem; color: var(--muted);">
                ${cl.variant_count} varyasyon / <strong>${cl.total_rows} satır</strong>
              </span>
            </div>
          </div>

          <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px;">
            ${cl.variants
              .map(
                (v) => `
              <span style="font-size: 0.76rem; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); padding: 3px 8px; border-radius: 6px; color: #f5f5f7;">
                ${v.val} <strong style="color: #60a5fa;">(${v.count})</strong>
              </span>
            `,
              )
              .join("")}
          </div>

          <div style="display: flex; align-items: center; gap: 10px; background: rgba(0, 0, 0, 0.25); padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.04);">
            <label style="font-size: 0.78rem; font-weight: 700; color: var(--muted); white-space: nowrap; margin: 0;">Hedef Standart:</label>
            <input type="text" id="tc-canonical-input-${idx}" value="${cl.suggested_canonical.replace(/"/g, "&quot;")}" style="flex: 1; height: 32px; background: #121215; border: 1px solid rgba(255, 255, 255, 0.14); border-radius: 6px; color: #fff; padding: 0 10px; font-size: 0.82rem;" />
            <button type="button" class="btn-tc-single-merge btn-glass-primary" data-idx="${idx}" style="white-space: nowrap; height: 32px; padding: 0 12px; font-size: 0.78rem;">
              ✓ Birleştir
            </button>
          </div>
        </div>
      `;
    });

    html += `</div>`;
    if (resultBox) resultBox.innerHTML = html;

    // Tekil Birleştirme Butonlarını Bağla
    resultBox?.querySelectorAll(".btn-tc-single-merge").forEach((b) => {
      b.addEventListener("click", () => {
        const idx = parseInt(b.dataset.idx, 10);
        const cl = clusters[idx];
        const input = document.getElementById(`tc-canonical-input-${idx}`);
        const canonicalVal = input ? input.value.trim() : cl.suggested_canonical;
        const variants = cl.variants.map((v) => v.val);
        const itemEl = document.getElementById(`tc-cluster-item-${idx}`);
        mergeSingleClusterAction(col, canonicalVal, variants, itemEl);
      });
    });

    // Tümünü Standartlaştır Butonunu Bağla
    document
      .getElementById("btnTcMergeAllClusters")
      ?.addEventListener("click", () => {
        mergeAllClustersAction(col, clusters);
      });
  } catch (err) {
    if (resultBox) {
      resultBox.innerHTML = `
        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 12px; padding: 18px; color: #fca5a5; font-size: 0.85rem;">
          ⚠️ <strong>Tarama Hatası:</strong> ${err.message}
        </div>
      `;
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function mergeSingleClusterAction(col, canonical, variants, itemElement) {
  if (!canonical || !variants || variants.length === 0) return;
  if (itemElement) itemElement.style.opacity = "0.5";

  try {
    const res = await fetch("/merge_text_clusters", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        column: col,
        merges: [{ canonical: canonical, variants: variants }],
      }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || "Birleştirme yapılamadı.");
    }

    if (itemElement) {
      itemElement.style.opacity = "1";
      itemElement.style.borderColor = "rgba(16, 185, 129, 0.4)";
      itemElement.innerHTML = `
        <div style="color: #6ee7b7; font-size: 0.84rem; display: flex; align-items: center; gap: 8px;">
          <span>✓</span> <strong>Standartlaştırıldı:</strong> ${data.message} (${variants.length} varyasyon ➔ "${canonical}")
        </div>
      `;
    }

    showDataPrepToast({
      title: "Metin Kümesi Birleştirildi",
      message: `"${col}" sütununda ${data.message}`,
      type: "success",
      icon: "✓",
    });

    if (typeof checkDataHealthAsync === "function") checkDataHealthAsync();
    if (typeof renderChartGrid === "function") renderChartGrid("all");
    if (typeof evaluateCharts === "function") evaluateCharts();
  } catch (err) {
    if (itemElement) itemElement.style.opacity = "1";
    showDataPrepToast({
      title: "Birleştirme Hatası",
      message: err.message,
      type: "error",
      icon: "⚠️",
    });
  }
}

async function mergeAllClustersAction(col, clusters) {
  const btnAll = document.getElementById("btnTcMergeAllClusters");
  if (btnAll) {
    btnAll.disabled = true;
    btnAll.textContent = "⏳ Birleştiriliyor...";
  }

  const merges = clusters.map((cl, idx) => {
    const input = document.getElementById(`tc-canonical-input-${idx}`);
    const canonicalVal = input ? input.value.trim() : cl.suggested_canonical;
    return {
      canonical: canonicalVal || cl.suggested_canonical,
      variants: cl.variants.map((v) => v.val),
    };
  });

  try {
    const res = await fetch("/merge_text_clusters", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ column: col, merges: merges }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.error || "Toplu birleştirme başarısız.");
    }

    const resultBox = document.getElementById("tcClustersResult");
    if (resultBox) {
      resultBox.innerHTML = `
        <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 14px; padding: 24px; text-align: center; color: #6ee7b7; margin: 10px 0;">
          <div style="font-size: 2rem; margin-bottom: 8px;">🎉</div>
          <strong style="font-size: 1.05rem;">Tüm Metin Kümeleri Başarıyla Standartlaştırıldı!</strong>
          <p style="font-size: 0.85rem; color: #94a3b8; margin: 8px 0 0 0;">
            ${data.message} Veri setindeki yazım varyasyonları tekilleştirildi.
          </p>
        </div>
      `;
    }

    showDataPrepToast({
      title: "Toplu Standartlaştırma Tamamlandı!",
      message: `"${col}" sütununda ${data.message}`,
      type: "success",
      icon: "🎉",
      duration: 6000,
    });

    if (typeof checkDataHealthAsync === "function") checkDataHealthAsync();
    if (typeof renderChartGrid === "function") renderChartGrid("all");
    if (typeof evaluateCharts === "function") evaluateCharts();
  } catch (err) {
    showDataPrepToast({
      title: "Toplu Birleştirme Hatası",
      message: err.message,
      type: "error",
      icon: "⚠️",
    });
    if (btnAll) {
      btnAll.disabled = false;
      btnAll.textContent = "⚡ Tümünü Standartlaştır";
    }
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initDataPrepListeners);
} else {
  initDataPrepListeners();
}

// ════════════════════════════════════════════════════════════
// KONSENSÜS TABANLI HİBRİT ANOMALİ & AÇIKLANABİLİR GEREKÇELER
// ════════════════════════════════════════════════════════════
async function fetchAndRenderEnsembleAnomalies(force = false) {
  const cardsList = document.getElementById("dpEnsembleCardsList");
  const tabBadge = document.getElementById("dpEnsembleTabCount");
  const consensusEl = document.getElementById("dpConsensusCount");
  const singleEl = document.getElementById("dpSingleModelCount");
  const redPctEl = document.getElementById("dpFalsePositiveRedPct");

  if (!cardsList) return;

  cardsList.innerHTML = `<div class="dp-loading-placeholder" style="padding: 24px; text-align: center; color: #8b949e;"><span class="proto-spinner"></span> 3'lü Model Konsensüsü ve Açıklanabilir Karar Yolları Hesaplanıyor...</div>`;

  try {
    const [ensRes, expRes] = await Promise.allSettled([
      fetch("/detect_ensemble_anomalies?contamination=0.04&top_n=30").then(r => r.json()),
      fetch("/get_explainable_anomalies?top_n=30").then(r => r.json()),
    ]);

    const ensData = ensRes.status === "fulfilled" && ensRes.value.success ? ensRes.value.ensemble_report : null;
    const expData = expRes.status === "fulfilled" && expRes.value.success ? expRes.value.anomaly_report : null;

    if (!ensData && !expData) {
      throw new Error(ensRes.value?.error || expRes.value?.error || "Anomali modelleri çalıştırılamadı.");
    }

    // Sayaçları ve metrikleri güncelle
    const consensusCount = ensData?.total_consensus_anomalies || expData?.total_anomalies_found || 0;
    const singleCount = ensData?.total_single_model_alerts || 0;
    const redPct = ensData?.false_positive_reduction_pct || 0;

    if (consensusEl) consensusEl.textContent = consensusCount;
    if (singleEl) singleEl.textContent = singleCount;
    if (redPctEl) redPctEl.textContent = `%${redPct}`;

    if (tabBadge) {
      if (consensusCount > 0) {
        tabBadge.textContent = consensusCount;
        tabBadge.classList.remove("hidden");
      } else {
        tabBadge.classList.add("hidden");
      }
    }

    // Açıklamaları row_index anahtarına göre indeksle
    const explanationsByRow = {};
    if (expData?.explained_rows) {
      expData.explained_rows.forEach((r) => {
        explanationsByRow[r.row_index] = r;
      });
    }

    // Gösterilecek liste
    const anomaliesList = ensData?.anomalies || [];
    if (anomaliesList.length === 0 && (!expData?.explained_rows || expData.explained_rows.length === 0)) {
      cardsList.innerHTML = `<div class="dp-alert-banner dp-alert-success" style="margin: 10px 0; background: rgba(16,185,129,0.12); color: #34d399; padding: 14px 18px; border-radius: 8px;">✓ Harika! Veri setinde hiçbir model konsensüsüyle doğrulanmış kritik anomali tespit edilmedi.</div>`;
      return;
    }

    let html = "";
    anomaliesList.forEach((a) => {
      const rowIdx = a.row_index;
      const exp = explanationsByRow[rowIdx] || null;
      const reasons = exp?.top_reasons || [];
      const riskClass = a.votes === 3 ? "critical" : a.votes === 2 ? "high" : "suspicious";

      html += `
        <div class="dp-hybrid-card ${riskClass}">
          <div class="dhc-header">
            <div class="dhc-row-badge">
              <span>Satır #${rowIdx}</span>
              <span class="dhc-risk-chip ${riskClass}">${a.risk_level} (%${a.risk_percentage})</span>
            </div>
            <span style="font-size: 0.82rem; font-weight: 700; color: #f59e0b;">Z-Sapması: ${a.max_z_score}&sigma;</span>
          </div>

          <div class="dhc-models-row">
            <span>Hemfikir Modeller (${a.votes}/3 Oy):</span>
            ${a.agreeing_models.map(m => `<span class="dhc-model-badge">✓ ${m}</span>`).join("")}
          </div>

          ${reasons.length > 0 ? `
            <div class="dhc-reasons-container">
              <span style="font-size: 0.78rem; font-weight: 700; color: #cbd5e1;">Açıklanabilir İstatistiksel Gerekçeler:</span>
              ${reasons.map(r => `
                <div class="dhc-reason-item">
                  <span class="dhc-reason-col">📊 ${r.column}: <strong>${r.value}</strong></span>
                  <span class="dhc-reason-stat">Normal Aralık: [${r.expected_range}] (Ort: ${r.mean})</span>
                  <span class="dhc-reason-deviation ${r.severity}">${r.reason}</span>
                </div>
              `).join("")}
            </div>
          ` : `
            <div style="font-size: 0.8rem; color: #94a3b8; font-style: italic;">
              Bu satır çok boyutlu uzayda komşuluk yoğunluğu (LOF) ve tecrit ağaçları (iForest) yoluyla aykırı saptandı.
            </div>
          `}

          ${a.preview ? `
            <div class="dhc-preview-row">
              <span style="font-weight: 600; color: #94a3b8;">Satır Değerleri:</span>
              ${Object.entries(a.preview).map(([k, v]) => `<span><strong>${k}:</strong> ${v}</span>`).join(" • ")}
            </div>
          ` : ""}
        </div>
      `;
    });

    cardsList.innerHTML = html;
  } catch (err) {
    cardsList.innerHTML = `<div class="dp-alert-banner dp-alert-danger" style="margin: 10px 0; color: #f87171; background: rgba(239,68,68,0.12); padding: 14px 18px; border-radius: 8px;">Hata: ${err.message}</div>`;
  }
}

// Window export
window.openDataPrepModal = openDataPrepModal;
window.callRepairColumn = callRepairColumn;
window.callCleanData = callCleanData;
window.updateAnomalyBadges = updateAnomalyBadges;
window.showDataPrepToast = showDataPrepToast;
window.optimizeMemoryAction = optimizeMemoryAction;
window.recoverDirtyTypesAction = recoverDirtyTypesAction;
window.openTextClusteringModal = openTextClusteringModal;
window.closeTextClusteringModal = closeTextClusteringModal;
window.fetchAndRenderEnsembleAnomalies = fetchAndRenderEnsembleAnomalies;

