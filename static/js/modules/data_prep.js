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
    if (targetTab === "nans" || (!hasAnomalies && data.missing_rows > 0)) {
      document.getElementById("dpTabBtnNans")?.click();
    } else {
      document.getElementById("dpTabBtnAnomalies")?.click();
    }

    // ── SEKME 1: ANOMALİ KARTLARI ──
    if (hasAnomalies) {
      if (headerBanner) {
        headerBanner.innerHTML = `
          <div style="background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.25); border-radius:8px; padding:10px 14px; font-size:0.85rem; color:#fca5a5; line-height:1.5;">
            ⚠️ <strong>${anomalies.length} adet sütunda</strong> sayısal alana sözel işlem/metin girildiği tespit edildi. Bu sütunları grafiklerde sayısal eksen (Y) olarak kullanabilmek için aşağıdaki onarma yöntemlerinden birini uygulayın:
          </div>
        `;
      }
      if (batchBar) batchBar.classList.remove("hidden");

      if (cardsList) {
        cardsList.innerHTML = anomalies
          .map(
            (anom) => `
          <div class="dp-anomaly-card premium-glass-card">
            <div class="dp-anomaly-card-header">
              <div class="dp-anomaly-title-group">
                <div class="dp-anomaly-icon">⚠️</div>
                <div class="dp-anomaly-info">
                  <strong class="dp-col-name">${anom.column}</strong>
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
                ${(anom.sample_invalid_values || []).map((val) => `<span class="dp-sample-tag">${val}</span>`).join("")}
              </div>
            </div>

            <div class="dp-anomaly-actions-row">
              <button type="button" class="btn-heal-col btn-glass-primary" data-col="${anom.column}" data-mode="smart_heal" title="Sayıları ayıklar, para/yüzde temizler, kalan sözelleri ortalamaya eşitler">
                🪄 Akıllı Onar (Sayı Ayıkla)
              </button>
              <button type="button" class="btn-heal-col btn-glass-secondary" data-col="${anom.column}" data-mode="fill_zero" title="Sözel değerleri 0 ile ikame eder">
                0️⃣ 0 Yap
              </button>
              <button type="button" class="btn-heal-col btn-glass-secondary" data-col="${anom.column}" data-mode="fill_mean" title="Sözel değerleri sütun ortalaması ile ikame eder">
                📈 Ortalamayla Doldur
              </button>
              <button type="button" class="btn-heal-col btn-glass-secondary" data-col="${anom.column}" data-mode="coerce_nan" title="Sözelleri boş (NaN) yapar, sütunu sayısal tipe geçirir">
                🗑️ Boş (NaN) Yap
              </button>
              <button type="button" class="btn-heal-col btn-glass-danger" data-col="${anom.column}" data-mode="drop_rows" title="Bu sütunda sözel değer olan satırları tablodan çıkarır">
                ❌ Satırları Sil
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
      }
    } else {
      if (headerBanner) {
        headerBanner.innerHTML = `
          <div style="background:rgba(52,211,153,0.1); border:1px solid rgba(52,211,153,0.25); border-radius:8px; padding:14px; font-size:0.9rem; color:#6ee7b7; line-height:1.5;">
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
        msgEl.innerHTML = `<span style="color:var(--orange); font-weight:700;">⚠️ ${data.missing_rows} satırda toplam ${data.missing_cells} adet boş (NaN) hücre tespit edildi.</span><br>Grafiklerin ve istatistik testlerinin kusursuz çalışması için aşağıdaki yöntemlerden birini seçebilirsiniz:`;
      if (dropBtn) dropBtn.style.display = "inline-block";
      if (fillBtn) fillBtn.style.display = "inline-block";
      if (fillZeroBtn) fillZeroBtn.style.display = "inline-block";
    } else {
      if (msgEl)
        msgEl.innerHTML = `<span style="color:var(--green); font-weight:700;">✓ Tebrikler! Veri setinizde hiç eksik değer (NaN) bulunmuyor.</span><br>Tüm satır ve sütunlar eksiksiz ve analize %100 hazır.`;
      if (dropBtn) dropBtn.style.display = "none";
      if (fillBtn) fillBtn.style.display = "none";
      if (fillZeroBtn) fillZeroBtn.style.display = "none";
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

    if (
      currentChartData &&
      currentPlotType &&
      typeof refreshActiveChart === "function"
    ) {
      refreshActiveChart();
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
  [dropBtn, fillBtn, fillZeroBtn].forEach((b) => {
    if (b) b.disabled = true;
  });

  const prog = window.DataVizProgress?.start({
    icon: "🧹",
    title: "Eksik Değerler (NaN) Temizleniyor",
    containerId: "dpMessage",
    showHud: false,
    stages: [
      {
        at: 0,
        short: "Eksik Tespiti",
        label: "Boş (NaN) hücreler belirleniyor...",
      },
      {
        at: 45,
        short: "İkame / Silme",
        label: "Seçilen temizleme yöntemi uygulanıyor...",
      },
      {
        at: 80,
        short: "Doğrulama",
        label: "Veri tablosu yeniden doğrulanıyor...",
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
    if (
      currentChartData &&
      currentPlotType &&
      typeof refreshActiveChart === "function"
    )
      refreshActiveChart();

    prog?.complete("Eksik veriler başarıyla temizlendi!");
    await new Promise((r) => setTimeout(r, 180));
    await openDataPrepModal("nans", data.health || null);
  } catch (err) {
    prog?.stop();
    alert("Hata: " + err.message);
    if (msgEl) msgEl.innerHTML = origMsg;
  } finally {
    isDataPrepBusy = window.isDataPrepBusy = false;
    [dropBtn, fillBtn, fillZeroBtn].forEach((b) => {
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
        b.style.background = "transparent";
        b.style.color = "var(--muted)";
        b.style.borderColor = "transparent";
      });
      document
        .querySelectorAll(".dp-pane")
        .forEach((p) => p.classList.add("hidden"));

      btn.classList.add("active");
      btn.style.background = "rgba(167,139,250,0.15)";
      btn.style.color = "var(--purple)";
      btn.style.borderColor = "rgba(167,139,250,0.3)";

      const tab = btn.dataset.dptab;
      if (tab === "anomalies") {
        document.getElementById("dpPaneAnomalies")?.classList.remove("hidden");
      } else {
        document.getElementById("dpPaneNans")?.classList.remove("hidden");
      }
    });
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
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initDataPrepListeners);
} else {
  initDataPrepListeners();
}

// Window export
window.openDataPrepModal = openDataPrepModal;
window.callRepairColumn = callRepairColumn;
window.callCleanData = callCleanData;
window.updateAnomalyBadges = updateAnomalyBadges;
