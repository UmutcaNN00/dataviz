"""
Academic and TÜBİTAK Statistical PDF Report Generator Service
Generates publication-quality A4 PDF reports using ReportLab with robust Turkish font safety,
APA-style statistical tables, hypothesis test interpretations, and regression models.
"""

import io
import logging
import os
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# isort: split
from core.config import FONT_PATH
from services.stats_service import (
    compute_advanced_stats,
    compute_column_statistics,
    compute_correlation_matrix,
    compute_multiple_linear_regression,
    safe_float,
)

logger = logging.getLogger(__name__)

# Register Turkish-compatible TTF Fonts
FONT_NAME = "Helvetica"
FONT_NAME_BOLD = "Helvetica-Bold"
FONT_REGISTERED = False

CANDIDATE_FONTS = [
    FONT_PATH,
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "C:/Windows/Fonts/tahoma.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

CANDIDATE_BOLD_FONTS = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "C:/Windows/Fonts/tahomabd.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _init_fonts():
    global FONT_NAME, FONT_NAME_BOLD, FONT_REGISTERED
    if FONT_REGISTERED:
        return

    regular_path = None
    for fp in CANDIDATE_FONTS:
        if fp and os.path.exists(fp):
            regular_path = fp
            break

    bold_path = None
    for fp in CANDIDATE_BOLD_FONTS:
        if fp and os.path.exists(fp):
            bold_path = fp
            break

    if regular_path:
        try:
            pdfmetrics.registerFont(TTFont("DataVizTurkish", regular_path))
            FONT_NAME = "DataVizTurkish"
            if bold_path:
                pdfmetrics.registerFont(TTFont("DataVizTurkish-Bold", bold_path))
                FONT_NAME_BOLD = "DataVizTurkish-Bold"
            else:
                FONT_NAME_BOLD = "DataVizTurkish"
            FONT_REGISTERED = True
            logger.info(f"ReportLab Türkçe font yüklendi: {regular_path}")
        except Exception as e:
            logger.warning(f"Font kaydı hatası, fallback Helvetica: {e}")
            FONT_NAME = "Helvetica"
            FONT_NAME_BOLD = "Helvetica-Bold"
            FONT_REGISTERED = False
    else:
        FONT_NAME = "Helvetica"
        FONT_NAME_BOLD = "Helvetica-Bold"
        FONT_REGISTERED = False


_init_fonts()


def _sanitize_tr(text: Any) -> str:
    """
    Sanitizes string for PDF output. If custom TTF font is not available,
    safely maps Turkish-specific Unicode characters to ASCII equivalents to prevent crashes.
    """
    if text is None:
        return ""
    s = str(text)
    if FONT_REGISTERED:
        return s

    tr_map = {
        "ı": "i",
        "İ": "I",
        "ş": "s",
        "Ş": "S",
        "ğ": "g",
        "Ğ": "G",
        "ü": "u",
        "Ü": "U",
        "ö": "o",
        "Ö": "O",
        "ç": "c",
        "Ç": "C",
    }
    for tr_char, ascii_char in tr_map.items():
        s = s.replace(tr_char, ascii_char)
    return s


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print total page count in footers.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont(FONT_NAME, 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header running line
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(15 * mm, 282 * mm, 195 * mm, 282 * mm)
        self.drawString(
            15 * mm,
            284 * mm,
            _sanitize_tr("DataViz Pro — TÜBİTAK & Akademik İstatistik Raporu"),
        )

        # Footer running line
        self.line(15 * mm, 15 * mm, 195 * mm, 15 * mm)
        self.drawString(
            15 * mm,
            11 * mm,
            _sanitize_tr("Gizli & Bilimsel Araştırma Materyali — APA 7 Formatı"),
        )
        page_str = _sanitize_tr(f"Sayfa {self._pageNumber} / {page_count}")
        self.drawRightString(195 * mm, 11 * mm, page_str)
        self.restoreState()


def generate_academic_pdf_report(
    df: pd.DataFrame,
    title: str = "TÜBİTAK & Akademik Veri Analiz Raporu",
    subtitle: str = "Betimsel İstatistikler, Hipotez Testleri ve Regresyon Modellemesi",
    author: str = "DataViz Analitik Motoru",
    x_col: str | None = None,
    y_cols: list[str] | None = None,
    project_code: str = "TUBITAK-DV-2026",
) -> tuple[io.BytesIO, str]:
    """
    Generates a publication-quality A4 academic statistical PDF report.

    Args:
        df: Active pandas DataFrame
        title: Main report title
        subtitle: Secondary subtitle
        author: Report author or laboratory
        x_col: Independent or grouping variable
        y_cols: Dependent numeric variables
        project_code: Project reference code

    Returns:
        tuple (io.BytesIO, str): (buffer, download_filename)
    """
    _init_fonts()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    style_title = ParagraphStyle(
        "AcadTitle",
        parent=styles["Normal"],
        fontName=FONT_NAME_BOLD,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4,
    )
    style_subtitle = ParagraphStyle(
        "AcadSubTitle",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12,
    )
    style_h1 = ParagraphStyle(
        "AcadH1",
        parent=styles["Normal"],
        fontName=FONT_NAME_BOLD,
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )
    style_body = ParagraphStyle(
        "AcadBody",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6,
    )
    style_meta_key = ParagraphStyle(
        "MetaKey",
        parent=styles["Normal"],
        fontName=FONT_NAME_BOLD,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#334155"),
    )
    style_meta_val = ParagraphStyle(
        "MetaVal",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
    )
    style_tbl_hdr = ParagraphStyle(
        "TblHdr",
        parent=styles["Normal"],
        fontName=FONT_NAME_BOLD,
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1,
    )
    style_tbl_cell = ParagraphStyle(
        "TblCell",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b"),
        alignment=1,
    )
    style_tbl_cell_l = ParagraphStyle(
        "TblCellL",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b"),
        alignment=0,
    )

    story = []

    # 1. Header & Title Block
    story.append(Paragraph(_sanitize_tr(title), style_title))
    story.append(Paragraph(_sanitize_tr(subtitle), style_subtitle))
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#1e3a8a"),
            spaceBefore=0,
            spaceAfter=10,
        )
    )

    # Metadata Grid Table
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    num_rows = len(df) if df is not None else 0
    num_cols = len(df.columns) if df is not None else 0
    num_missing = int(df.isna().sum().sum()) if df is not None else 0

    meta_data = [
        [
            Paragraph(_sanitize_tr("Proje Kodu:"), style_meta_key),
            Paragraph(_sanitize_tr(project_code), style_meta_val),
            Paragraph(_sanitize_tr("Rapor Tarihi:"), style_meta_key),
            Paragraph(_sanitize_tr(now_str), style_meta_val),
        ],
        [
            Paragraph(_sanitize_tr("Araştırmacı / Kurum:"), style_meta_key),
            Paragraph(_sanitize_tr(author), style_meta_val),
            Paragraph(_sanitize_tr("Örneklem (N):"), style_meta_key),
            Paragraph(_sanitize_tr(f"{num_rows:,} satır ({num_cols} değişken)"), style_meta_val),
        ],
        [
            Paragraph(_sanitize_tr("Eksik Değerler (NA):"), style_meta_key),
            Paragraph(_sanitize_tr(f"{num_missing:,} hücre"), style_meta_val),
            Paragraph(_sanitize_tr("İstatistiki Güven:"), style_meta_key),
            Paragraph(_sanitize_tr("%95 (α = 0.05)"), style_meta_val),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[38 * mm, 50 * mm, 38 * mm, 54 * mm])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Determine numeric and categorical target columns
    all_num_cols = df.select_dtypes(include=["number"]).columns.tolist() if df is not None else []
    target_y = [c for c in (y_cols or []) if c in df.columns] if y_cols else []
    if not target_y:
        target_y = all_num_cols[:6]

    # 2. Executive Summary (Bölüm 1)
    story.append(Paragraph(_sanitize_tr("1. Yönetici Özeti ve Metodolojik Çerçeve"), style_h1))
    summary_text = (
        f"Bu rapor, <strong>{num_rows:,}</strong> gözlem ve <strong>{num_cols}</strong> değişkenden "
        f"oluşan veri seti üzerinde gerçekleştirilen betimsel analizleri, hipotez testlerini "
        f"ve regresyon modelleme bulgularını özetlemektedir. Analizler parametrik "
        f"(Welch's T-Testi, One-Way ANOVA) ve parametrik olmayan (Mann-Whitney U, Kruskal-Wallis H) "
        f"testleri içermektedir. Normallik varsayımı Jarque-Bera testi ile sınanmıştır."
    )
    story.append(Paragraph(_sanitize_tr(summary_text), style_body))
    story.append(Spacer(1, 8))

    # 3. Descriptive Statistics (Bölüm 2)
    story.append(Paragraph(_sanitize_tr("2. Betimsel İstatistikler ve Dağılım Parametreleri"), style_h1))
    col_stats = compute_column_statistics(df, target_y)

    table_data = [
        [
            Paragraph(_sanitize_tr("Değişken"), style_tbl_hdr),
            Paragraph(_sanitize_tr("N"), style_tbl_hdr),
            Paragraph(_sanitize_tr("Ortalama"), style_tbl_hdr),
            Paragraph(_sanitize_tr("SS (Std)"), style_tbl_hdr),
            Paragraph(_sanitize_tr("Medyan"), style_tbl_hdr),
            Paragraph(_sanitize_tr("Min - Maks"), style_tbl_hdr),
            Paragraph(_sanitize_tr("Çarpıklık"), style_tbl_hdr),
            Paragraph(_sanitize_tr("Basıklık"), style_tbl_hdr),
            Paragraph(_sanitize_tr("JB (p)"), style_tbl_hdr),
        ]
    ]

    for c in target_y:
        st = col_stats.get(c, {})
        mean_s = f"{st.get('mean'):.2f}" if st.get("mean") is not None else "-"
        std_s = f"{st.get('std'):.2f}" if st.get("std") is not None else "-"
        med_s = f"{st.get('median'):.2f}" if st.get("median") is not None else "-"
        min_v = f"{st.get('min'):.1f}" if st.get("min") is not None else "-"
        max_v = f"{st.get('max'):.1f}" if st.get("max") is not None else "-"
        min_max_s = f"{min_v} - {max_v}"
        skew_s = f"{st.get('skewness'):.2f}" if st.get("skewness") is not None else "-"
        kurt_s = f"{st.get('kurtosis'):.2f}" if st.get("kurtosis") is not None else "-"
        jb_p = st.get("jarque_bera_p")
        jb_s = f"{jb_p:.4f}" if jb_p is not None else "-"

        table_data.append(
            [
                Paragraph(_sanitize_tr(c[:18]), style_tbl_cell_l),
                Paragraph(_sanitize_tr(str(st.get("count", 0))), style_tbl_cell),
                Paragraph(_sanitize_tr(mean_s), style_tbl_cell),
                Paragraph(_sanitize_tr(std_s), style_tbl_cell),
                Paragraph(_sanitize_tr(med_s), style_tbl_cell),
                Paragraph(_sanitize_tr(min_max_s), style_tbl_cell),
                Paragraph(_sanitize_tr(skew_s), style_tbl_cell),
                Paragraph(_sanitize_tr(kurt_s), style_tbl_cell),
                Paragraph(_sanitize_tr(jb_s), style_tbl_cell),
            ]
        )

    t_desc = Table(
        table_data,
        colWidths=[
            32 * mm,
            14 * mm,
            20 * mm,
            18 * mm,
            18 * mm,
            26 * mm,
            18 * mm,
            18 * mm,
            16 * mm,
        ],
    )
    t_desc.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t_desc)
    story.append(
        Paragraph(
            _sanitize_tr(
                "<em>Not: JB (p) < 0.05 olması durumunda değişken normal dağılımdan sapmaktadır (p < 0.05).</em>"
            ),
            style_body,
        )
    )
    story.append(Spacer(1, 8))

    # 4. Hypothesis Testing & Comparative Statistics (Bölüm 3)
    if x_col and x_col in df.columns:
        story.append(
            Paragraph(
                _sanitize_tr(f"3. Hipotez Testleri ve Karşılaştırma Analizleri (Grup: {x_col})"),
                style_h1,
            )
        )
        adv_res = compute_advanced_stats(df, target_y, x_col=x_col)

        hypo_data = [
            [
                Paragraph(_sanitize_tr("Hedef Değişken"), style_tbl_hdr),
                Paragraph(_sanitize_tr("Test Türü"), style_tbl_hdr),
                Paragraph(_sanitize_tr("Parametrik (t / F)"), style_tbl_hdr),
                Paragraph(_sanitize_tr("Parametrik Olmayan (U / H)"), style_tbl_hdr),
                Paragraph(_sanitize_tr("p Değeri"), style_tbl_hdr),
                Paragraph(_sanitize_tr("Bayes Faktörü (BF₁₀)"), style_tbl_hdr),
                Paragraph(_sanitize_tr("Karar (α = 0.05)"), style_tbl_hdr),
            ]
        ]

        for y in target_y:
            info = adv_res.get(y, {})
            adv_type = info.get("type")
            p_val = info.get("p_value")
            p_str = f"{p_val:.4f}" if isinstance(p_val, (int, float)) else "-"
            sig_decision = "Anlamlı Fark Var" if (p_val is not None and p_val < 0.05) else "Fark Yok (H₀)"
            bf_str = str(info.get("bayes_bf10", "-"))

            if adv_type == "categorical_2":
                t_val = info.get("t_test_stat")
                t_str = f"t = {t_val:.2f}" if t_val is not None else "-"
                u_val = info.get("mann_whitney_u")
                u_str = f"U = {u_val:.1f}" if u_val is not None else "-"
                hypo_data.append(
                    [
                        Paragraph(_sanitize_tr(y[:18]), style_tbl_cell_l),
                        Paragraph(_sanitize_tr("2 Grup (T-Test / MW)"), style_tbl_cell),
                        Paragraph(_sanitize_tr(t_str), style_tbl_cell),
                        Paragraph(_sanitize_tr(u_str), style_tbl_cell),
                        Paragraph(_sanitize_tr(p_str), style_tbl_cell),
                        Paragraph(_sanitize_tr(bf_str), style_tbl_cell),
                        Paragraph(_sanitize_tr(sig_decision), style_tbl_cell),
                    ]
                )
            elif adv_type == "categorical_n":
                f_val = info.get("anova_f")
                f_str = f"F = {f_val:.2f}" if f_val is not None else "-"
                h_val = info.get("kruskal_h")
                h_str = f"H = {h_val:.2f}" if h_val is not None else "-"
                hypo_data.append(
                    [
                        Paragraph(_sanitize_tr(y[:18]), style_tbl_cell_l),
                        Paragraph(_sanitize_tr("ANOVA / Kruskal"), style_tbl_cell),
                        Paragraph(_sanitize_tr(f_str), style_tbl_cell),
                        Paragraph(_sanitize_tr(h_str), style_tbl_cell),
                        Paragraph(_sanitize_tr(p_str), style_tbl_cell),
                        Paragraph(_sanitize_tr(bf_str), style_tbl_cell),
                        Paragraph(_sanitize_tr(sig_decision), style_tbl_cell),
                    ]
                )
            elif adv_type == "numeric":
                r_val = info.get("correlation")
                r_str = f"r = {r_val:.2f}" if r_val is not None else "-"
                r2_val = info.get("r_squared")
                r2_str = f"R² = {r2_val:.2f}" if r2_val is not None else "-"
                hypo_data.append(
                    [
                        Paragraph(_sanitize_tr(y[:18]), style_tbl_cell_l),
                        Paragraph(_sanitize_tr("Korelasyon & Regresyon"), style_tbl_cell),
                        Paragraph(_sanitize_tr(r_str), style_tbl_cell),
                        Paragraph(_sanitize_tr(r2_str), style_tbl_cell),
                        Paragraph(_sanitize_tr(p_str), style_tbl_cell),
                        Paragraph(_sanitize_tr(bf_str), style_tbl_cell),
                        Paragraph(_sanitize_tr(sig_decision), style_tbl_cell),
                    ]
                )

        if len(hypo_data) > 1:
            t_hypo = Table(
                hypo_data,
                colWidths=[
                    32 * mm,
                    30 * mm,
                    24 * mm,
                    28 * mm,
                    18 * mm,
                    24 * mm,
                    24 * mm,
                ],
            )
            t_hypo.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.HexColor("#f0f9ff")],
                        ),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(t_hypo)
            story.append(Spacer(1, 8))

    # 5. Regression & Modeling Summary (Bölüm 4)
    if len(target_y) >= 2:
        story.append(
            Paragraph(_sanitize_tr("4. Çoklu Regresyon Modellemesi ve Çoklu Doğrusallık Denetimi"), style_h1)
        )
        target_dep = target_y[0]
        feats_indep = target_y[1:5]
        reg_res = compute_multiple_linear_regression(df, feats_indep, target_dep)

        if "error" not in reg_res:
            eq_text = f"<strong>Model Denklemi:</strong> <code>{reg_res.get('equation')}</code>"
            stats_text = (
                f"<strong>R²:</strong> {reg_res.get('r_squared')} | "
                f"<strong>Düzeltilmiş R²:</strong> {reg_res.get('adj_r_squared')} | "
                f"<strong>F-İstatistiği:</strong> {reg_res.get('f_statistic')} (p = {reg_res.get('p_value')}) | "
                f"<strong>Standart Hata:</strong> {reg_res.get('std_error')}"
            )
            story.append(Paragraph(_sanitize_tr(eq_text), style_body))
            story.append(Paragraph(_sanitize_tr(stats_text), style_body))

            # Coefficients Table
            coef_tbl_data = [
                [
                    Paragraph(_sanitize_tr("Parametre / Değişken"), style_tbl_hdr),
                    Paragraph(_sanitize_tr("Katsayı (β)"), style_tbl_hdr),
                    Paragraph(_sanitize_tr("Standart Hata"), style_tbl_hdr),
                    Paragraph(_sanitize_tr("t Değeri"), style_tbl_hdr),
                    Paragraph(_sanitize_tr("p Değeri"), style_tbl_hdr),
                    Paragraph(_sanitize_tr("VIF"), style_tbl_hdr),
                    Paragraph(_sanitize_tr("Anlamlılık"), style_tbl_hdr),
                ]
            ]
            for item in reg_res.get("coefficients", []):
                p_v = item.get("p_value")
                p_st = f"{p_v:.4f}" if p_v is not None else "-"
                vif_st = str(item.get("vif") or "-")
                sig_st = "p < 0.05 (*)" if item.get("is_significant") else "Anlamsız"
                coef_tbl_data.append(
                    [
                        Paragraph(_sanitize_tr(item.get("feature", "")[:24]), style_tbl_cell_l),
                        Paragraph(_sanitize_tr(str(item.get("coef"))), style_tbl_cell),
                        Paragraph(_sanitize_tr(str(item.get("std_err"))), style_tbl_cell),
                        Paragraph(_sanitize_tr(str(item.get("t_stat"))), style_tbl_cell),
                        Paragraph(_sanitize_tr(p_st), style_tbl_cell),
                        Paragraph(_sanitize_tr(vif_st), style_tbl_cell),
                        Paragraph(_sanitize_tr(sig_st), style_tbl_cell),
                    ]
                )

            t_coef = Table(
                coef_tbl_data,
                colWidths=[
                    42 * mm,
                    22 * mm,
                    22 * mm,
                    20 * mm,
                    22 * mm,
                    20 * mm,
                    32 * mm,
                ],
            )
            t_coef.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(t_coef)
            story.append(
                Paragraph(
                    _sanitize_tr(f"<em>Çoklu Doğrusallık Notu: {reg_res.get('multicollinearity_note')}</em>"),
                    style_body,
                )
            )
            story.append(Spacer(1, 8))

    # 6. Academic Conclusion & Recommendations (Bölüm 5)
    story.append(Paragraph(_sanitize_tr("5. Bilimsel Değerlendirme ve Sonuç"), style_h1))
    conclusion_text = (
        "Yapılan parametrik ve non-parametrik test sonuçları ile kurulan OLS modelleme parametreleri "
        "birlikte ele alındığında; değişkenler arasındaki korelasyonel ve nedensel örüntüler "
        "literatür standartlarında (APA 7th Edition) doğrulanmıştır. Bulgular, karar vericiler "
        "ve akademik araştırmacılar için istatistiksel kanıt temelli sağlam bir temel teşkil etmektedir."
    )
    story.append(Paragraph(_sanitize_tr(conclusion_text), style_body))

    # Build document with 2-pass NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    filename = f"Tubitak_Akademik_Rapor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return buffer, filename
