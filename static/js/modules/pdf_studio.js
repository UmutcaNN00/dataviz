/* ════════════════════════════════════════════════════════════
   DATAVIZ PRO V6 — PDF STUDIO MODULE
   A4 PDF Raporlama ve Önizleme Stüdyosu
════════════════════════════════════════════════════════════ */

async function openPdfPreviewStudio() {
  if (!dashboardCharts || dashboardCharts.length === 0) {
    alert("Panoda henüz dışa aktarılacak bir grafik yok.");
    return;
  }

  const modal = document.getElementById("pdfStudioModal");
  if (!modal) return;
  modal.classList.remove("hidden");

  const a4Container = document.getElementById("a4Container");
  if (!a4Container) return;
  a4Container.innerHTML = "";

  // 1. Create header with Title, Subtitle, Date
  const headerBlock = document.createElement("div");
  headerBlock.className = "pdf-block";
  headerBlock.style.position = "relative";
  headerBlock.style.marginBottom = "20px";
  headerBlock.style.padding = "10px";
  headerBlock.innerHTML = `
    <div style="border-bottom: 2px solid var(--blue); padding-bottom: 10px; margin-bottom: 10px;">
      <h1 contenteditable="true" style="margin: 0; font-size: 24px; outline: none; color: #1e293b;">DataViz Raporu</h1>
      <h3 contenteditable="true" style="margin: 5px 0 0 0; color: #64748b; font-weight: 500; outline: none;">Aylık Performans Değerlendirmesi</h3>
    </div>
    <p style="margin: 0; font-size: 12px; color: #777; text-align: right;">Tarih: ${new Date().toLocaleDateString("tr-TR")}</p>
    <div class="pdf-block-actions" style="position: absolute; top: -10px; right: 0; display: flex; gap: 5px;">
      <button class="pdf-btn-up">↑</button>
      <button class="pdf-btn-down">↓</button>
      <button class="pdf-btn-del">X</button>
    </div>
  `;
  a4Container.appendChild(headerBlock);

  // 2. KPI Grid Clone
  const kpiGrid = document.getElementById("dashboardKpiGrid");
  if (kpiGrid && kpiGrid.innerHTML.trim() !== "") {
    const kpiBlock = document.createElement("div");
    kpiBlock.className = "pdf-block";
    kpiBlock.style.position = "relative";
    kpiBlock.style.marginBottom = "20px";
    kpiBlock.style.padding = "10px";
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
    kpiBlock.querySelectorAll(".kpi-tile-card").forEach((card) => {
      card.style.background = "#f8fafc";
      card.style.color = "black";
      card.style.border = "1px solid #ccc";
      card.style.flex = "1";
      card.style.minWidth = "150px";
    });
    kpiBlock.querySelectorAll("p").forEach((p) => (p.style.color = "#555"));
    a4Container.appendChild(kpiBlock);
  }

  // 3. Clone Charts
  for (let i = 0; i < dashboardCharts.length; i++) {
    const item = dashboardCharts[i];
    const divId = `plot_${item.id}`;
    const gd =
      document.getElementById(divId) ||
      document.getElementById("regScatterPlot") ||
      document.getElementById("regScatterPlotArea");

    const chartBlock = document.createElement("div");
    chartBlock.className = "pdf-block";
    chartBlock.style.position = "relative";
    chartBlock.style.marginBottom = "20px";
    chartBlock.style.padding = "10px";
    chartBlock.style.border = "1px solid #eee";
    chartBlock.style.borderRadius = "8px";

    let contentHtml = "";
    if (item.chartType === "pivot") {
      contentHtml = `
        <h4 contenteditable="true" style="margin:0 0 10px 0; font-size:16px; color:black; border-left:4px solid #10b981; padding-left:10px; outline:none;">${item.title}</h4>
        <div style="overflow-x:auto;">${gd ? gd.innerHTML : ""}</div>
      `;
    } else if (gd && gd.data) {
      const origLayout = JSON.parse(JSON.stringify(gd.layout || {}));
      const origPaperBg = origLayout.paper_bgcolor || "transparent";
      const origPlotBg = origLayout.plot_bgcolor || "#070711";
      const origFontColor = origLayout.font?.color || "#f8fafc";
      const origXGrid = origLayout.xaxis?.gridcolor || "rgba(255,255,255,0.08)";
      const origYGrid = origLayout.yaxis?.gridcolor || "rgba(255,255,255,0.08)";
      const origXTitleColor = origLayout.xaxis?.title?.font?.color || "#f8fafc";
      const origYTitleColor = origLayout.yaxis?.title?.font?.color || "#f8fafc";
      const origXTickColor = origLayout.xaxis?.tickfont?.color || "#94a3b8";
      const origYTickColor = origLayout.yaxis?.tickfont?.color || "#94a3b8";

      const update = {
        paper_bgcolor: "#ffffff",
        plot_bgcolor: "#ffffff",
        "font.color": "#0f172a",
        "xaxis.gridcolor": "rgba(0,0,0,0.1)",
        "yaxis.gridcolor": "rgba(0,0,0,0.1)",
        "xaxis.title.font.color": "#0f172a",
        "yaxis.title.font.color": "#0f172a",
        "xaxis.tickfont.color": "#334155",
        "yaxis.tickfont.color": "#334155",
      };
      await Plotly.relayout(gd, update);
      const chartDataUrl = await Plotly.toImage(gd, {
        format: "png",
        width: 700,
        height: 400,
      });
      await Plotly.relayout(gd, {
        paper_bgcolor: origPaperBg,
        plot_bgcolor: origPlotBg,
        "font.color": origFontColor,
        "xaxis.gridcolor": origXGrid,
        "yaxis.gridcolor": origYGrid,
        "xaxis.title.font.color": origXTitleColor,
        "yaxis.title.font.color": origYTitleColor,
        "xaxis.tickfont.color": origXTickColor,
        "yaxis.tickfont.color": origYTickColor,
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
}

function attachPdfBlockEvents() {
  const a4Container = document.getElementById("a4Container");
  if (!a4Container) return;
  a4Container.querySelectorAll(".pdf-block").forEach((block) => {
    const upBtn = block.querySelector(".pdf-btn-up");
    const downBtn = block.querySelector(".pdf-btn-down");
    const delBtn = block.querySelector(".pdf-btn-del");

    if (upBtn)
      upBtn.onclick = () => {
        if (block.previousElementSibling)
          block.parentNode.insertBefore(block, block.previousElementSibling);
      };
    if (downBtn)
      downBtn.onclick = () => {
        if (block.nextElementSibling)
          block.parentNode.insertBefore(block.nextElementSibling, block);
      };
    if (delBtn)
      delBtn.onclick = () => {
        block.remove();
      };
  });
}

function initPdfStudioListeners() {
  // Download Dashboard PDF Button (Açar Önizleme Stüdyosunu)
  document
    .getElementById("downloadDashboardPdfBtn")
    ?.addEventListener("click", openPdfPreviewStudio);

  // Metin Ekle
  document.getElementById("addTextBtnPdf")?.addEventListener("click", () => {
    const a4Container = document.getElementById("a4Container");
    if (!a4Container) return;
    const textBlock = document.createElement("div");
    textBlock.className = "pdf-block";
    textBlock.style.position = "relative";
    textBlock.style.marginBottom = "20px";
    textBlock.style.padding = "10px";
    textBlock.innerHTML = `
      <div contenteditable="true" style="border: 1px dashed gray; padding: 10px; min-height: 50px; outline: none; font-family: sans-serif; font-size: 14px; line-height: 1.5; color: #1e293b;">Buraya yorumunuzu yazın...</div>
      <div class="pdf-block-actions" style="position: absolute; top: -10px; right: 0; display: flex; gap: 5px;">
        <button class="pdf-btn-up">↑</button>
        <button class="pdf-btn-down">↓</button>
        <button class="pdf-btn-del">X</button>
      </div>
    `;
    a4Container.appendChild(textBlock);
    attachPdfBlockEvents();
  });

  // Stüdyoyu Kapat
  document
    .getElementById("closePdfStudioBtn")
    ?.addEventListener("click", () => {
      document.getElementById("pdfStudioModal")?.classList.add("hidden");
    });

  // Sonuçlandır ve İndir (jsPDF / html2pdf)
  document
    .getElementById("generatePdfBtn")
    ?.addEventListener("click", async () => {
      const a4Container = document.getElementById("a4Container");
      if (!a4Container) return;

      // Eylem butonlarını geçici olarak gizle
      const actions = a4Container.querySelectorAll(".pdf-block-actions");
      actions.forEach((a) => (a.style.display = "none"));

      // Kesikli çerçeveleri geçici olarak kaldır
      const textBlocks = a4Container.querySelectorAll(
        'div[contenteditable="true"]',
      );
      const originalBorders = [];
      textBlocks.forEach((tb) => {
        originalBorders.push(tb.style.border);
        tb.style.border = "none";
      });

      const originalAspect = a4Container.style.aspectRatio;
      const originalOverflow = a4Container.style.overflowY;
      a4Container.style.aspectRatio = "auto";
      a4Container.style.overflowY = "visible";

      const btn = document.getElementById("generatePdfBtn");
      const originalText = btn ? btn.innerHTML : "";
      if (btn) {
        btn.innerHTML = "⏳ Oluşturuluyor...";
        btn.disabled = true;
      }

      try {
        const opt = {
          margin: 10,
          filename: `DataViz_Rapor_${new Date().getTime()}.pdf`,
          image: { type: "jpeg", quality: 0.98 },
          html2canvas: { scale: 2, useCORS: true },
          jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
          pagebreak: { mode: ["avoid-all", "css", "legacy"] },
        };
        await html2pdf().set(opt).from(a4Container).save();
      } catch (err) {
        alert("PDF Oluşturulurken hata: " + err.message);
      }

      // Orijinal stilleri geri yükle
      a4Container.style.aspectRatio = originalAspect;
      a4Container.style.overflowY = originalOverflow;

      actions.forEach((a) => (a.style.display = "flex"));
      textBlocks.forEach((tb, i) => {
        tb.style.border = originalBorders[i];
      });

      if (btn) {
        btn.disabled = false;
        btn.innerHTML = originalText;
      }
    });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initPdfStudioListeners);
} else {
  initPdfStudioListeners();
}

// Window export
window.openPdfPreviewStudio = openPdfPreviewStudio;
window.attachPdfBlockEvents = attachPdfBlockEvents;
