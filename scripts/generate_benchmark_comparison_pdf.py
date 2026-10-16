import os
import sys
import shutil
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, inch
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Python 3.14 Windows Türkçe karakter güvenliği
sys.stdout.reconfigure(encoding='utf-8')

# 1. FONT KAYITLARI (Windows Türkçe Güvenliği)
FONT_NORMAL = "Arial"
FONT_BOLD = "Arial-Bold"
FONT_CODE = "Consolas"

try:
    pdfmetrics.registerFont(TTFont(FONT_NORMAL, 'C:/Windows/Fonts/arial.ttf'))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, 'C:/Windows/Fonts/arialbd.ttf'))
    pdfmetrics.registerFont(TTFont(FONT_CODE, 'C:/Windows/Fonts/consola.ttf'))
except Exception as e:
    print(f"Font yükleme uyarısı: {e}")

# 2. RENK PALETİ (Modern, Kurumsal & Canlı)
C_DARK = HexColor("#0F172A")        # Çok Koyu Lacivert/Gri (Slate 900)
C_PRIMARY = HexColor("#1E3A8A")     # Derin Mavi (Blue 900)
C_SECONDARY = HexColor("#2563EB")   # Parlak Mavi (Blue 600)
C_ACCENT = HexColor("#0284C7")      # Canlı Gökyüzü Mavisi (Sky 600)
C_TEXT = HexColor("#334155")        # Gövde Metni (Slate 700)
C_MUTED = HexColor("#64748B")       # Açıklama / Alt Metin (Slate 500)
C_LIGHT_BG = HexColor("#F8FAFC")    # Kart Zemin (Slate 50)
C_BORDER = HexColor("#E2E8F0")      # İnce Kenarlık (Slate 200)
C_SUCCESS = HexColor("#059669")     # Yeşil (Emerald 600)
C_SUCCESS_BG = HexColor("#ECFDF5")  # Açık Yeşil
C_WARNING = HexColor("#D97706")     # Turuncu (Amber 600)
C_WARNING_BG = HexColor("#FFFBEB")  # Açık Turuncu
C_PURPLE = HexColor("#7C3AED")      # Mor
C_PURPLE_BG = HexColor("#F5F3FF")   # Açık Mor
C_WHITE = HexColor("#FFFFFF")

# 3. İKİ GEÇİŞLİ NUMARALANDIRMA (NumberedCanvas)
class NumberedCanvas(canvas.Canvas):
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
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont(FONT_NORMAL, 8)
        self.setFillColor(C_MUTED)

        # Kapak sayfası hariç üstbilgi / altbilgi bas
        if self._pageNumber > 1:
            # Üstbilgi (Header)
            self.drawString(40, 808, "DataViz — Analitik, İstatistik & Görselleştirme Araçları Mimari Kıyaslama Raporu")
            self.drawRightString(555, 808, "Ekim 2026 | Teknik Rapor")
            self.setStrokeColor(C_BORDER)
            self.setLineWidth(0.75)
            self.line(40, 800, 555, 800)

            # Altbilgi (Footer)
            self.line(40, 45, 555, 45)
            self.drawString(40, 32, "DataViz Açık & Yerel Analitik Platformu | Gizli & Kapsamlı Benchmark Raporu")
            page_text = f"Sayfa {self._pageNumber} / {page_count}"
            self.drawRightString(555, 32, page_text)

        self.restoreState()

def build_pdf(output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    # Tipografi ve Stil Tanımları
    s_cover_title = ParagraphStyle(
        'CoverTitle',
        fontName=FONT_BOLD,
        fontSize=24,
        leading=30,
        textColor=C_DARK,
        alignment=0,
        spaceAfter=10
    )

    s_cover_subtitle = ParagraphStyle(
        'CoverSubtitle',
        fontName=FONT_NORMAL,
        fontSize=12,
        leading=17,
        textColor=C_SECONDARY,
        alignment=0,
        spaceAfter=20
    )

    s_cover_desc = ParagraphStyle(
        'CoverDesc',
        fontName=FONT_NORMAL,
        fontSize=9.5,
        leading=14,
        textColor=C_TEXT,
        alignment=0,
        spaceAfter=15
    )

    s_h1 = ParagraphStyle(
        'Heading1_Custom',
        fontName=FONT_BOLD,
        fontSize=16,
        leading=21,
        textColor=C_PRIMARY,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    s_h2 = ParagraphStyle(
        'Heading2_Custom',
        fontName=FONT_BOLD,
        fontSize=12,
        leading=16,
        textColor=C_DARK,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    s_h3 = ParagraphStyle(
        'Heading3_Custom',
        fontName=FONT_BOLD,
        fontSize=10,
        leading=13,
        textColor=C_SECONDARY,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )

    s_body = ParagraphStyle(
        'Body_Custom',
        fontName=FONT_NORMAL,
        fontSize=9,
        leading=13.5,
        textColor=C_TEXT,
        spaceAfter=6
    )

    s_bullet = ParagraphStyle(
        'Bullet_Custom',
        fontName=FONT_NORMAL,
        fontSize=8.5,
        leading=12.5,
        textColor=C_TEXT,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    s_code = ParagraphStyle(
        'Code_Custom',
        fontName=FONT_CODE,
        fontSize=8,
        leading=10.5,
        textColor=C_PRIMARY
    )

    s_card_text = ParagraphStyle(
        'CardText',
        fontName=FONT_NORMAL,
        fontSize=8.5,
        leading=12,
        textColor=C_TEXT
    )

    s_card_bold = ParagraphStyle(
        'CardBold',
        fontName=FONT_BOLD,
        fontSize=9,
        leading=12,
        textColor=C_DARK
    )

    s_table_header = ParagraphStyle(
        'TableHeader',
        fontName=FONT_BOLD,
        fontSize=8,
        leading=10.5,
        textColor=C_WHITE,
        alignment=1
    )

    s_table_cell = ParagraphStyle(
        'TableCell',
        fontName=FONT_NORMAL,
        fontSize=7.5,
        leading=10,
        textColor=C_TEXT
    )

    s_table_cell_bold = ParagraphStyle(
        'TableCellBold',
        fontName=FONT_BOLD,
        fontSize=7.5,
        leading=10,
        textColor=C_DARK
    )

    s_table_cell_center = ParagraphStyle(
        'TableCellCenter',
        fontName=FONT_NORMAL,
        fontSize=7.5,
        leading=10,
        textColor=C_TEXT,
        alignment=1
    )

    story = []

    # =========================================================================
    # KAPAK SAYFASI (EXECUTIVE COVER)
    # =========================================================================
    story.append(Spacer(1, 20))
    
    # Üst Rozet
    badge_data = [[
        Paragraph("<font color='#2563EB'><b>DATA ANALYTICS & ARCHITECTURE BENCHMARK</b></font> | STRATEJİK İNCELEME RAPORU", s_code)
    ]]
    t_badge = Table(badge_data, colWidths=[515])
    t_badge.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_LIGHT_BG),
        ('BOX', (0,0), (-1,-1), 1, C_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_badge)
    story.append(Spacer(1, 25))

    story.append(Paragraph("DataViz Benzeri Uygulamaların Özellikleri, Mimarileri ve Kapsamlı Karşılaştırması", s_cover_title))
    story.append(Paragraph("Tableau, Power BI, SPSS, JASP, Jamovi, OpenRefine, Perspective, PyGWalker, Rill & Superset'in En Temel (Base) Seviyede Teknik Anatomisi", s_cover_subtitle))
    
    story.append(HRFlowable(width="100%", thickness=2.5, color=C_SECONDARY, spaceBefore=0, spaceAfter=18))

    story.append(Paragraph(
        "<b>Raporun Amacı:</b> Bu araştırma raporu; modern veri bilimi, istatistiksel modelleme, veri temizleme ve interaktif görselleştirme kulvarında öncü olan 10'dan fazla küresel yazılımı incelemektedir. "
        "Uygulamaların <b>hangi dilleri kullandıkları, görsel arayüzlerinin nasıl çalıştığı, veri hesaplama motorlarının çalışma prensipleri ve bellek (RAM) modelleri</b> "
        "teknik jargonlardan arındırılmış, herkesin kavrayabileceği en temel (base) seviyede ele alınmıştır.",
        s_cover_desc
    ))

    # Kapak Bilgi Kutusu
    meta_data = [
        [Paragraph("<b>Araştırma Konusu:</b>", s_card_bold), Paragraph("Yerel Veri Analitiği, İstatistik & BI Araçları Karşılaştırması", s_card_text)],
        [Paragraph("<b>Kapsanan Araçlar:</b>", s_card_bold), Paragraph("DataViz, Tableau, Power BI, SPSS, JASP, Jamovi, OpenRefine, Perspective, PyGWalker, Rill Data, Superset", s_card_text)],
        [Paragraph("<b>Mimari Odak:</b>", s_card_bold), Paragraph("Frontend (Arayüz), Backend (Mantık), Query Engine (Hesap Motoru), Memory Storage (RAM Modeli)", s_card_text)],
        [Paragraph("<b>Hedef Ekosistem:</b>", s_card_bold), Paragraph("Büyük Veri, Akademik Anketler, İş Zekası ve Yerel (Offline-First) Gizlilik", s_card_text)],
        [Paragraph("<b>Tarih & Durum:</b>", s_card_bold), Paragraph("Ekim 2026 | Üretim Sürümü 2.5 Değerlendirmesi", s_card_text)]
    ]
    t_meta = Table(meta_data, colWidths=[130, 385])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_LIGHT_BG),
        ('BOX', (0,0), (-1,-1), 1, C_BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('LINEBELOW', (0,0), (-1,-2), 0.5, C_BORDER),
    ]))
    story.append(t_meta)
    
    # Kapak Görseli (Eğer mevcutsa live_analysis_capture)
    img_path = "docs/images/live_analysis_capture.png"
    if os.path.exists(img_path):
        story.append(Spacer(1, 20))
        img = Image(img_path, width=515, height=220)
        story.append(img)
        story.append(Spacer(1, 5))
        story.append(Paragraph("<i>Şekil 1: DataViz — Yeni nesil yerel veri analitiği, doğrulanmış grafik ve istatistik stüdyosu genel görünümü.</i>", s_muted_caption := ParagraphStyle('MC', fontName=FONT_NORMAL, fontSize=7.5, textColor=C_MUTED, alignment=1)))

    story.append(PageBreak())

    # =========================================================================
    # BÖLÜM 1: TEMEL SEVİYE MİMARİ REHBERİ (BASE ARCHITECTURE)
    # =========================================================================
    story.append(Paragraph("1. Temel Seviye Mimari Rehberi: Bir Veri Programının İçi Nasıl Çalışır?", s_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=C_PRIMARY, spaceBefore=2, spaceAfter=10))

    story.append(Paragraph(
        "Modern veri analitiği ve görselleştirme yazılımlarını doğru kıyaslayabilmek için, bu sistemlerin iç mimarisini oluşturan "
        "<b>4 ana parçayı</b> ve bunların günlük hayattaki karşılıklarını temel düzeyde kavramak gerekir:",
        s_body
    ))

    # 4 Temel Katman Kartları
    layers_data = [
        [
            Paragraph("<b>1. Ön Yüz (Frontend / Arayüz)</b>", s_card_bold),
            Paragraph("Kullanıcının gözüyle gördüğü ve tıkladığı kısımdır. Butonlar, pencereler, sürükle-bırak eksen rafları ve grafik çizimleridir. <i>(Web: HTML/CSS/React/Svelte, Masaüstü: C++/Qt, WPF, Electron).</i>", s_card_text)
        ],
        [
            Paragraph("<b>2. Arka Plan (Backend / Çekirdek)</b>", s_card_bold),
            Paragraph("Tıklanan butonun ne yapacağını yöneten beyindir. Dosyaları diskten okur, güvenlik kontrolleri yapar, kullanıcı yetkilerini denetler ve hesap motorunu tetikler. <i>(Python, C++, C#, Java, Go, Rust).</i>", s_card_text)
        ],
        [
            Paragraph("<b>3. Hesap Motoru (Engine / Hesap Makinesi)</b>", s_card_bold),
            Paragraph("Milyonlarca satırlık verinin ortalamasını alan, toplayan, filtreleyen gizli motordur. <b>Eski motorlar</b> her satırı tek tek gezer (yavaştır); <b>modern motorlar</b> sütunları toplu olarak işlemci çekirdeklerine dağıtır (SIMD / Vektörize; yüz kat hızlıdır).", s_card_text)
        ],
        [
            Paragraph("<b>4. Bellek Mimarisi (RAM / Storage Modeli)</b>", s_card_bold),
            Paragraph("Verinin bilgisayarın geçici hafızasında (RAM) nasıl saklandığıdır. <br/>"
                      "• <i>Satır Tabanlı (Row-based):</i> Veriyi klasik defter gibi satır satır tutar (SPSS, eski veritabanları).<br/>"
                      "• <i>Sütun Tabanlı (Columnar / Apache Arrow / Parquet):</i> Her sütunu ayrı dikey bir şerit olarak saklar. Sadece ilgilenilen sütunu okur, hafızada %80 az yer kaplar ve anında yanıt verir.", s_card_text)
        ]
    ]
    t_layers = Table(layers_data, colWidths=[150, 365])
    t_layers.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_LIGHT_BG),
        ('BOX', (0,0), (-1,-1), 1, C_BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_layers)
    story.append(Spacer(1, 14))

    # =========================================================================
    # BÖLÜM 2: MODERN AÇIK KAYNAK VE YEREL VERİ ARAÇLARI
    # =========================================================================
    story.append(Paragraph("2. Modern Açık Kaynak & Yerel EDA / Görselleştirme Araçları", s_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=C_PRIMARY, spaceBefore=2, spaceAfter=10))

    # 2.1 PyGWalker
    story.append(Paragraph("2.1 PyGWalker (Graphic Walker) & Kanaries", s_h2))
    story.append(Paragraph(
        "<b>Temel Amacı:</b> Python veya Jupyter Notebook kullanan veri bilimcilerin, karmaşık kodlar yazmak yerine tek satırla "
        "(<code>pyg.walk(df)</code>) Tableau tarzı görsel sürükle-bırak grafik paneli açmasını sağlamaktır.",
        s_body
    ))
    story.append(Paragraph("• <b>Ön Yüz:</b> TypeScript, React ve Vega-Lite deklaratif grafik motoru.", s_bullet))
    story.append(Paragraph("• <b>Arka Plan & Veri Motoru:</b> Python çekirdeği + <b>DuckDB</b> ve <b>Apache Arrow</b>. Web tarafında doğrudan tarayıcı içinde çalışan DuckDB-Wasm sürümü de bulunur.", s_bullet))
    story.append(Paragraph("• <b>Güçlü Yönleri:</b> Sıfır konfigürasyon, 10 milyon satırda dahi DuckDB sayesinde takılmadan filtreleme, Tableau benzeri raf ergonomisi.", s_bullet))
    story.append(Paragraph("• <b>Zayıf Yönleri:</b> Bağımsız bir masaüstü yazılımı değildir (Notebook widget'ıdır); istatistiksel hipotez testleri (ANOVA, Regresyon vb.) içermez; veri temizleme yetenekleri zayıftır.", s_bullet))
    story.append(Paragraph("• <b>DataViz ile Farkı:</b> DataViz, PyGWalker'ın sürükle-bırak arayüz mantığını benimser; ancak onu izole bir widget olmaktan çıkarıp tam teşekküllü bağımsız bir masaüstü analitik stüdyosuna dönüştürür.", s_bullet))
    story.append(Spacer(1, 8))

    # 2.2 JASP ve Jamovi
    story.append(Paragraph("2.2 JASP ve Jamovi (Açık Kaynak SPSS Alternatifleri)", s_h2))
    story.append(Paragraph(
        "<b>Temel Amacı:</b> IBM SPSS'in çok yüksek lisans ücretlerine karşılık; üniversite öğrencileri, psikologlar ve akademisyenler için "
        "geliştirilmiş ücretsiz, açık kaynaklı ve modern arayüzlü masaüstü istatistik yazılımlarıdır.",
        s_body
    ))
    story.append(Paragraph("• <b>Ön Yüz:</b> JASP C++ ve Qt framework kullanır; Jamovi ise modern web teknolojilerine dayalı <b>Electron (HTML/CSS/JS)</b> kabuğu kullanır.", s_bullet))
    story.append(Paragraph("• <b>Arka Plan & Veri Motoru:</b> İkisinin de arkasında gömülü bir <b>R Çalışma Zamanı (R Runtime)</b> çalışır. Kullanıcı butonlara bastıkça arka planda R scriptleri çalıştırılır.", s_bullet))
    story.append(Paragraph("• <b>Güçlü Yönleri:</b> Parametreler değiştikçe anında güncellenen (reaktif) akademik APA 7 standardında tablolar. JASP özellikle Bayesyen istatistikte dünya lideridir.", s_bullet))
    story.append(Paragraph("• <b>Zayıf Yönleri:</b> R dili tek çekirdekli (single-threaded) çalıştığı için 500 bin satırın üzerindeki büyük dosyalarda kilitlenir; veri temizleme ve ETL kabiliyeti neredeyse yoktur; modern iş zekası panoları hazırlanamaz.", s_bullet))
    story.append(Paragraph("• <b>DataViz ile Farkı:</b> DataViz, JASP/Jamovi'nin sunduğu APA formatlı güvenilir istatistiği hedefler; ancak arka plandaki hantal R yerine çok çekirdekli modern C/Python motorlarını kullanarak milyonlarca satırda anlık sonuç üretir.", s_bullet))
    story.append(Spacer(1, 8))

    # 2.3 OpenRefine
    story.append(Paragraph("2.3 OpenRefine (Açık Kaynak Veri Temizleme ve Zenginleştirme)", s_h2))
    story.append(Paragraph(
        "<b>Temel Amacı:</b> Eksik, hatalı, dağınık ve kirli tabloları akıllı algoritmalarla temizlemek, standartlaştırmak ve dönüştürmektir.",
        s_body
    ))
    story.append(Paragraph("• <b>Ön Yüz & Arka Plan:</b> Tarayıcıda çalışan HTML5/jQuery + <b>Java (Jetty gömülü sunucusu)</b>.", s_bullet))
    story.append(Paragraph("• <b>Çalışma Mantığı:</b> <i>Metin Kümeleme (Clustering)</i> algoritmalarıyla benzer yazımları tek tıkla birleştirir (Örn: 'Ankara', 'ankara', 'Ankra' -> 'Ankara'). Yapılan her işlemi <b>JSON Tarif (Recipe)</b> olarak saklar.", s_bullet))
    story.append(Paragraph("• <b>Güçlü Yönleri:</b> Dünyadaki en güçlü açık kaynak veri temizleme ve fasetleme aracıdır; temizleme adımları kaydedilip başka dosyalarda otomatik tekrarlanabilir.", s_bullet))
    story.append(Paragraph("• <b>Zayıf Yönleri:</b> Grafik çizemez, istatistik yapamaz. Arayüzü 2010 yılından kalmadır. Büyük dosyalarda Java bellek sınırına takılır.", s_bullet))
    story.append(Paragraph("• <b>DataViz ile Farkı:</b> DataViz, OpenRefine'ın metin kümeleme ve adım adım temizleme tarifini doğrudan bünyesinde barındırır; ancak bunu modern bir görselleştirme ve istatistik stüdyosuyla birleştirir.", s_bullet))
    story.append(Spacer(1, 8))

    # 2.4 Perspective
    story.append(Paragraph("2.4 Perspective (FinOS / J.P. Morgan)", s_h2))
    story.append(Paragraph(
        "<b>Temel Amacı:</b> Finans analistlerinin ve borsacıların, canlı akan devasa veri akışlarını (streaming data) mikrosaniye gecikmeyle pivot edip 60 FPS hızla ekranda kaydırmasını sağlamaktır.",
        s_body
    ))
    story.append(Paragraph("• <b>Teknolojisi:</b> C++ çekirdek motoru, <b>WebAssembly (WASM)</b>, Web Components ve <b>Apache Arrow (Zero-Copy)</b> bellek modeli.", s_bullet))
    story.append(Paragraph("• <b>Güçlü Yönleri:</b> Tarayıcıda ulaşılabilecek en yüksek veri ızgarası (data grid) ve anlık pivot performansı.", s_bullet))
    story.append(Paragraph("• <b>Zayıf Yönleri:</b> Son kullanıcı yazılımı değildir; geliştiricilerin projelerine eklediği teknik bir bileşendir.", s_bullet))

    story.append(PageBreak())

    # =========================================================================
    # BÖLÜM 3: BÜYÜK KURUMSAL MASAÜSTÜ DEVLERİ
    # =========================================================================
    story.append(Paragraph("3. Büyük Kurumsal & Klasik Masaüstü Analitik Devleri", s_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=C_PRIMARY, spaceBefore=2, spaceAfter=10))

    # 3.1 Tableau Desktop
    story.append(Paragraph("3.1 Tableau Desktop (Salesforce)", s_h2))
    story.append(Paragraph(
        "<b>Temel Amacı:</b> Kurumsal iş analistleri ve yöneticiler için dünyanın en popüler ve estetik gösterge paneli (dashboard) yazılımıdır.",
        s_body
    ))
    story.append(Paragraph("• <b>Arayüz & Sorgu:</b> C++ ve Qt masaüstü arayüzü; <b>VizQL (Görsel Sorgu Dili)</b>. Kullanıcının sürükle-bırak yaptığı her hareketi anında matematiksel veri sorgularına çevirir.", s_bullet))
    story.append(Paragraph("• <b>Hesap Motoru:</b> <b>Hyper Engine</b> (LLVM anlık derleme yapan, dünyanın en hızlı sütun tabanlı bellek içi ilişkisel motorlarından biridir).", s_bullet))
    story.append(Paragraph("• <b>Güçlü Yönleri:</b> Sürükle-bırak görselleştirme ergonomisinde pazarın altın standardı; yüz milyonlarca satırda yerel hız.", s_bullet))
    story.append(Paragraph("• <b>Zayıf Yönleri:</b> Lisans ücretleri aşırı pahalıdır; SPSS gibi akademik istatistiksel hipotez testleri yapamaz; veri temizlemek için ayrı bir yazılım (Tableau Prep) satın alınmasını zorunlu kılar.", s_bullet))
    story.append(Paragraph("• <b>DataViz ile Farkı:</b> DataViz, Tableau'nun raf sistemini (X, Y, Renk, Boyut) örnek alır; ancak Tableau'nun sunmadığı SPSS kalitesinde istatistik ve veri temizlemeyi ücretsiz ve tek bir yerel pakette sunar.", s_bullet))
    story.append(Spacer(1, 8))

    # 3.2 Microsoft Power BI Desktop
    story.append(Paragraph("3.2 Microsoft Power BI Desktop", s_h2))
    story.append(Paragraph(
        "<b>Temel Amacı:</b> Excel'in yetersiz kaldığı büyük kurumsal verilerde self-service raporlama ve iş zekası ihtiyacını karşılamaktır.",
        s_body
    ))
    story.append(Paragraph("• <b>Teknolojisi:</b> Windows WPF + Chromium WebView2. Veri hazırlama tarafında <b>Power Query (M Dili)</b>; hesaplama tarafında <b>VertiPaq Motoru</b> ve <b>DAX</b> formül dili.", s_bullet))
    story.append(Paragraph("• <b>Güçlü Yönleri:</b> Power Query ile adım adım veri temizleme çok başarılıdır; VertiPaq motoru veriyi bellekte 10 kat sıkıştırır; masaüstü uygulaması ücretsizdir.", s_bullet))
    story.append(Paragraph("• <b>Zayıf Yönleri:</b> Yalnızca Windows'ta çalışır (macOS/Linux desteği yoktur); DAX formül dilinin öğrenilmesi çok zordur; derin istatistiksel analizler yapılamaz; kullanıcıyı bulut lisanslarına bağımlı kılmaya odaklanır.", s_bullet))
    story.append(Paragraph("• <b>DataViz ile Farkı:</b> DataViz, platform bağımsızdır (Windows/Mac/Linux); DAX karmaşıklığı yerine doğrudan görsel istatistik ve formüllerle çalışır.", s_bullet))
    story.append(Spacer(1, 8))

    # 3.3 IBM SPSS Statistics
    story.append(Paragraph("3.3 IBM SPSS Statistics", s_h2))
    story.append(Paragraph(
        "<b>Temel Amacı:</b> Sosyal bilimler, tıp, psikoloji ve anket araştırmalarında 50 yıldır kullanılan standart istatistiksel analiz yazılımıdır.",
        s_body
    ))
    story.append(Paragraph("• <b>Teknolojisi:</b> C/C++ çekirdek motoru + Java Swing arayüzü. Tescilli <code>.sav</code> ikili dosya formatı.", s_bullet))
    story.append(Paragraph("• <b>Güçlü Yönleri:</b> Değişken etiketleri (Variable Labels), değer etiketleri (Value Labels: 1='Kadın', 2='Erkek') gibi metadata yönetiminde ve akademik test zenginliğinde endüstri standardıdır.", s_bullet))
    story.append(Paragraph("• <b>Zayıf Yönleri:</b> Arayüzü 1995 yılından kalmadır; grafik motoru çok zayıftır; modern büyük verilerde donar; lisans fiyatları inanılmaz derecede yüksektir.", s_bullet))
    story.append(Paragraph("• <b>DataViz ile Farkı:</b> DataViz, SPSS'in en büyük gücü olan <code>.sav</code> dosyalarını doğrudan okur ve etiketlerini korur; fakat SPSS'in çağ dışı arayüzünü modern, donanım hızlandırmalı interaktif bir stüdyo ile değiştirir.", s_bullet))
    story.append(Spacer(1, 8))

    # 3.4 KNIME Analytics Platform
    story.append(Paragraph("3.4 KNIME Analytics Platform", s_h2))
    story.append(Paragraph(
        "<b>Temel Amacı:</b> Kod yazmadan kutuları (düğümleri) birbirine oklarla bağlayarak veri temizleme, birleştirme ve makine öğrenimi modelleri kurmaktır.",
        s_body
    ))
    story.append(Paragraph("• <b>Teknolojisi:</b> Java, Eclipse OSGi modüler mimarisi + Columnar Table Backend (Apache Arrow).", s_bullet))
    story.append(Paragraph("• <b>Güçlü / Zayıf Yönleri:</b> 4000+ hazır işlem kutusuyla açık kaynaklı devasa bir kütüphanedir; ancak açılışı ve çalışması çok ağırdır (Java yükü). Basit bir grafik çizmek veya veriyi anında incelemek için bile onlarca kutuyu bağlamak gerekir.", s_bullet))

    story.append(PageBreak())

    # =========================================================================
    # BÖLÜM 4: YENİ NESİL MODERN WEB VE HIZLI BI ARAÇLARI
    # =========================================================================
    story.append(Paragraph("4. Yeni Nesil Modern Web & Hızlı BI Araçları", s_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=C_PRIMARY, spaceBefore=2, spaceAfter=10))

    story.append(Paragraph("4.1 Rill Data & Evidence.dev (DuckDB Tabanlı Hızlı BI)", s_h2))
    story.append(Paragraph(
        "<b>Temel Amacı:</b> Eski hantal iş zekası araçlarına tepki olarak doğan; yerel veya bulut ortamındaki Parquet/CSV dosyalarını "
        "<b>DuckDB</b> motorunun gücüyle mikrosaniyeler içinde gösterge panellerine dönüştüren yeni nesil 'Fast BI' araçlarıdır.",
        s_body
    ))
    story.append(Paragraph("• <b>Teknolojisi:</b> Go / C++ / DuckDB + <b>Svelte / TypeScript</b>. Veriler DuckDB'nin sütun tabanlı bellek motorunda vektörize olarak işlenir.", s_bullet))
    story.append(Paragraph("• <b>Güçlü Yönleri:</b> Milyonlarca satırda milisaniyenin altında filtreleme hızı; minimalist ve ultra modern arayüz; sıfır veritabanı kurulum zorunluluğu.", s_bullet))
    story.append(Paragraph("• <b>Zayıf Yönleri:</b> İleri istatistiksel testler ve görsel veri temizleme araçları yoktur.", s_bullet))
    story.append(Spacer(1, 8))

    story.append(Paragraph("4.2 Apache Superset & Metabase (Merkezi Veri Ambarı BI)", s_h2))
    story.append(Paragraph(
        "<b>Temel Amacı:</b> Şirketlerin merkezi veri ambarlarına (PostgreSQL, Snowflake, BigQuery) bağlanıp tüm şirkete web üzerinden rapor sunmasını sağlayan kurumsal platformlardır.",
        s_body
    ))
    story.append(Paragraph("• <b>Teknolojisi:</b> Python/Flask (Superset) veya Clojure (Metabase) + React frontend + Apache ECharts.", s_bullet))
    story.append(Paragraph("• <b>Farkı:</b> Bu araçlar veriyi kendileri işlemez, bağlı oldukları veritabanına SQL sorgusu gönderirler (Push-down). Tek başına bir Excel/SPSS dosyasını yerel makinede hemen açıp analiz etmek için uygun değillerdir; karmaşık sunucu kurulumu gerektirirler.", s_bullet))
    story.append(Spacer(1, 14))

    # =========================================================================
    # BÖLÜM 5: BÜYÜK KARŞILAŞTIRMA MATRİSLERİ
    # =========================================================================
    story.append(Paragraph("5. Kapsamlı Karşılaştırma Matrisleri (Özellik & Mimari)", s_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=C_PRIMARY, spaceBefore=2, spaceAfter=10))

    story.append(Paragraph("<b>Tablo 1: Fonksiyonel Yetenekler ve Kullanıcı Deneyimi Kıyaslaması</b>", s_h2))
    
    # Tablo 1
    matrix1_data = [
        [
            Paragraph("<b>Uygulama</b>", s_table_header),
            Paragraph("<b>Görselleştirme (BI)</b>", s_table_header),
            Paragraph("<b>İstatistiksel Modelleme</b>", s_table_header),
            Paragraph("<b>Veri Temizleme & ETL</b>", s_table_header),
            Paragraph("<b>SPSS / Anket Desteği</b>", s_table_header),
            Paragraph("<b>Yerel Hız & Gizlilik</b>", s_table_header)
        ],
        [
            Paragraph("<b>DataViz (Proje)</b>", s_table_cell_bold),
            Paragraph("<font color='#059669'><b>27 Doğrulanmış Grafik</b></font>", s_table_cell),
            Paragraph("<font color='#059669'><b>OLS, ANOVA, Pearson</b></font>", s_table_cell),
            Paragraph("<font color='#059669'><b>MICE, Kümeleme, Downcast</b></font>", s_table_cell),
            Paragraph("<font color='#059669'><b>Tam (.sav, .parquet)</b></font>", s_table_cell),
            Paragraph("<font color='#059669'><b>%100 Yerel (SIMD)</b></font>", s_table_cell)
        ],
        [
            Paragraph("Tableau Desktop", s_table_cell_bold),
            Paragraph("Mükemmel (VizQL)", s_table_cell),
            Paragraph("Çok Kısıtlı", s_table_cell),
            Paragraph("Ayrı Araç İster (Prep)", s_table_cell),
            Paragraph("Kısıtlı", s_table_cell),
            Paragraph("Hızlı (Hyper)", s_table_cell)
        ],
        [
            Paragraph("Power BI Desktop", s_table_cell_bold),
            Paragraph("Mükemmel (DAX)", s_table_cell),
            Paragraph("Çok Kısıtlı", s_table_cell),
            Paragraph("Harika (Power Query)", s_table_cell),
            Paragraph("Kısıtlı", s_table_cell),
            Paragraph("Hızlı (Yalnızca Win)", s_table_cell)
        ],
        [
            Paragraph("IBM SPSS Statistics", s_table_cell_bold),
            Paragraph("Çok Zayıf & Hantal", s_table_cell),
            Paragraph("Mükemmel (Akademik)", s_table_cell),
            Paragraph("Zor ve Eski", s_table_cell),
            Paragraph("Doğal Formatı (.sav)", s_table_cell),
            Paragraph("Yavaş (Klasik Disk)", s_table_cell)
        ],
        [
            Paragraph("JASP / Jamovi", s_table_cell_bold),
            Paragraph("Sabit Çıktılar", s_table_cell),
            Paragraph("Mükemmel (APA Tablo)", s_table_cell),
            Paragraph("Yok Düzeyinde", s_table_cell),
            Paragraph("Mevcut", s_table_cell),
            Paragraph("Orta (R Tek Çekirdek)", s_table_cell)
        ],
        [
            Paragraph("OpenRefine", s_table_cell_bold),
            Paragraph("Grafik Çizemez", s_table_cell),
            Paragraph("Yok", s_table_cell),
            Paragraph("Dünyanın En İyisi", s_table_cell),
            Paragraph("Yok", s_table_cell),
            Paragraph("Orta (Java Heap)", s_table_cell)
        ],
        [
            Paragraph("PyGWalker", s_table_cell_bold),
            Paragraph("Harika (Vega-Lite)", s_table_cell),
            Paragraph("Yok", s_table_cell),
            Paragraph("Temel Filtreleme", s_table_cell),
            Paragraph("Yok", s_table_cell),
            Paragraph("Hızlı (DuckDB)", s_table_cell)
        ],
        [
            Paragraph("Rill Data", s_table_cell_bold),
            Paragraph("Hızlı Metrik Panosu", s_table_cell),
            Paragraph("Yok", s_table_cell),
            Paragraph("Yok", s_table_cell),
            Paragraph("Yok", s_table_cell),
            Paragraph("Ultra Hızlı (DuckDB)", s_table_cell)
        ]
    ]
    t1 = Table(matrix1_data, colWidths=[90, 85, 85, 95, 80, 80])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_PRIMARY),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('INNERGRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('BOX', (0,0), (-1,-1), 1, C_PRIMARY),
        ('BACKGROUND', (0,1), (-1,1), C_SUCCESS_BG), # DataViz satırı yeşil
        ('BACKGROUND', (0,2), (-1,-1), C_WHITE),
        ('ROWBACKGROUNDS', (0,2), (-1,-1), [C_WHITE, C_LIGHT_BG])
    ]))
    story.append(t1)
    story.append(Spacer(1, 14))

    # Tablo 2: Teknik Mimari & Motor Kıyaslaması
    story.append(Paragraph("<b>Tablo 2: Teknik Mimari, Kullanılan Diller ve Bellek Modelleri</b>", s_h2))
    matrix2_data = [
        [
            Paragraph("<b>Uygulama</b>", s_table_header),
            Paragraph("<b>Ön Yüz (Frontend)</b>", s_table_header),
            Paragraph("<b>Arka Plan Dili</b>", s_table_header),
            Paragraph("<b>Hesaplama Motoru</b>", s_table_header),
            Paragraph("<b>Bellek Formatı</b>", s_table_header),
            Paragraph("<b>Lisans / Model</b>", s_table_header)
        ],
        [
            Paragraph("<b>DataViz</b>", s_table_cell_bold),
            Paragraph("Modern Web / HTML5", s_table_cell),
            Paragraph("Python / C-SIMD", s_table_cell),
            Paragraph("Polars / PyArrow", s_table_cell),
            Paragraph("Apache Arrow (Sütun)", s_table_cell),
            Paragraph("Açık & Taşınabilir", s_table_cell)
        ],
        [
            Paragraph("Tableau Desktop", s_table_cell_bold),
            Paragraph("C++ / Qt", s_table_cell),
            Paragraph("C++", s_table_cell),
            Paragraph("Hyper Engine (LLVM)", s_table_cell),
            Paragraph("Hyper Columnar", s_table_cell),
            Paragraph("Ticari (Çok Pahalı)", s_table_cell)
        ],
        [
            Paragraph("Power BI Desktop", s_table_cell_bold),
            Paragraph("WPF / WebView2", s_table_cell),
            Paragraph("C# / .NET", s_table_cell),
            Paragraph("VertiPaq Motoru", s_table_cell),
            Paragraph("Sıkıştırılmış Sütun", s_table_cell),
            Paragraph("Ücretsiz (Win Yalnız)", s_table_cell)
        ],
        [
            Paragraph("IBM SPSS", s_table_cell_bold),
            Paragraph("Java Swing", s_table_cell),
            Paragraph("C/C++ & Java", s_table_cell),
            Paragraph("Klasik SPSS Motoru", s_table_cell),
            Paragraph(".sav Satır Tabanlı", s_table_cell),
            Paragraph("Ticari (Aşırı Pahalı)", s_table_cell)
        ],
        [
            Paragraph("JASP / Jamovi", s_table_cell_bold),
            Paragraph("C++ (Qt) / Electron", s_table_cell),
            Paragraph("C++ / Python", s_table_cell),
            Paragraph("R İstatistik Motoru", s_table_cell),
            Paragraph("R data.frame", s_table_cell),
            Paragraph("Açık Kaynak (GPL)", s_table_cell)
        ],
        [
            Paragraph("OpenRefine", s_table_cell_bold),
            Paragraph("HTML5 / jQuery", s_table_cell),
            Paragraph("Java (Jetty)", s_table_cell),
            Paragraph("Java Grid Engine", s_table_cell),
            Paragraph("Java Bellek Nesneleri", s_table_cell),
            Paragraph("Açık Kaynak (BSD)", s_table_cell)
        ],
        [
            Paragraph("Perspective", s_table_cell_bold),
            Paragraph("Web Components", s_table_cell),
            Paragraph("C++ (WASM)", s_table_cell),
            Paragraph("C++ SIMD Motoru", s_table_cell),
            Paragraph("Arrow (Zero-Copy)", s_table_cell),
            Paragraph("Açık Kaynak (Apache)", s_table_cell)
        ],
        [
            Paragraph("Rill Data", s_table_cell_bold),
            Paragraph("Svelte / TypeScript", s_table_cell),
            Paragraph("Go / C++", s_table_cell),
            Paragraph("DuckDB SQL", s_table_cell),
            Paragraph("DuckDB Columnar", s_table_cell),
            Paragraph("Açık Kaynak (Apache)", s_table_cell)
        ]
    ]
    t2 = Table(matrix2_data, colWidths=[85, 90, 80, 95, 85, 80])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_DARK),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('INNERGRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('BOX', (0,0), (-1,-1), 1, C_DARK),
        ('BACKGROUND', (0,1), (-1,1), C_SUCCESS_BG),
        ('ROWBACKGROUNDS', (0,2), (-1,-1), [C_WHITE, C_LIGHT_BG])
    ]))
    story.append(t2)

    story.append(PageBreak())

    # =========================================================================
    # BÖLÜM 6: DATAVIZ'İN STRATEJİK DEĞERİ VE SONUÇ
    # =========================================================================
    story.append(Paragraph("6. DataViz'in Ekosistemdeki Konumu & Stratejik Sentez", s_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=C_PRIMARY, spaceBefore=2, spaceAfter=10))

    story.append(Paragraph(
        "Yapılan küresel mimari araştırma; piyasadaki hiçbir aracın <b>Görselleştirme, İstatistiksel Modelleme, Akıllı Veri Temizleme ve Yerel Yüksek Hızı</b> "
        "tek bir hafif masaüstü yazılımda birleştirmediğini kanıtlamaktadır. "
        "DataViz, mevcut devlerin en güçlü yönlerini bir araya getirerek (Unbundling & Rebundling) pazarda benzersiz bir pozisyon almaktadır:",
        s_body
    ))

    # 4 Güç Kartı
    pillar_data = [
        [
            Paragraph("<font color='#2563EB'><b>1. Tableau'dan:</b></font><br/><b>Görsel Raf Ergonomisi</b>", s_card_bold),
            Paragraph("Tableau'nun ünlü X-Ekseni, Y-Ekseni sürükle-bırak raf mantığını 27 adet matematiksel olarak doğrulanmış grafik türüyle tarayıcıya taşır.", s_card_text)
        ],
        [
            Paragraph("<font color='#059669'><b>2. SPSS ve JASP'tan:</b></font><br/><b>Akademik İstatistik Güveni</b>", s_card_bold),
            Paragraph("Uydurma/rastgele katsayılar yerine; saf matematiksel OLS Regresyonu, ANOVA varyans ayrışımı, Pearson/Spearman korelasyonu ve .sav anket formatı desteği.", s_card_text)
        ],
        [
            Paragraph("<font color='#D97706'><b>3. OpenRefine'dan:</b></font><br/><b>Akıllı Veri İyileştirme</b>", s_card_bold),
            Paragraph("Yazım hatalarını tek tıkla çözen metin kümeleme (clustering), MICE/KNN eksik veri tamamlama ve bellek downcasting optimizasyonu.", s_card_text)
        ],
        [
            Paragraph("<font color='#7C3AED'><b>4. DuckDB & Polars'tan:</b></font><br/><b>10M+ Satırda SIMD Yerel Hızı</b>", s_card_bold),
            Paragraph("Sıfır bulut bağımlılığı (%100 yerel gizlilik), Apache Arrow sütun tabanlı bellek mimarisi ve çok çekirdekli paralelleştirme gücü.", s_card_text)
        ]
    ]
    t_pillars = Table(pillar_data, colWidths=[140, 375])
    t_pillars.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_LIGHT_BG),
        ('BOX', (0,0), (-1,-1), 1, C_BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_pillars)
    story.append(Spacer(1, 14))

    # İkinci Görsel (Pivot Studio veya Regresyon Stüdyosu)
    img_pivot = "docs/images/pivot_studio.png"
    if os.path.exists(img_pivot):
        img2 = Image(img_pivot, width=515, height=200)
        story.append(img2)
        story.append(Spacer(1, 4))
        story.append(Paragraph("<i>Şekil 2: DataViz — Çok boyutlu çapraz tablo, dinamik ısı haritası ve canlı pivot stüdyosu.</i>", s_muted_caption))
        story.append(Spacer(1, 10))

    # Yönetici Özeti & Sonuç Çağrısı
    story.append(Paragraph("<b>Yönetici Özeti & Stratejik Değerlendirme:</b>", s_h2))
    story.append(Paragraph(
        "Geleneksel kurumsal araçlar (Tableau, Power BI, SPSS) kullanıcıları ya <b>pahalı bulut aboneliklerine</b> mahkûm etmekte "
        "ya da <b>1990'lardan kalma hantal arayüzlerle</b> büyük veride dondurmaktadır. "
        "Açık kaynaklı araçlar ise (OpenRefine, JASP, PyGWalker) yalnızca tek bir alanda uzmanlaşıp diğer alanları boş bırakmaktadır. "
        "<br/><br/>"
        "<b>DataViz</b>; kurulum gerektirmeyen taşınabilir (portable) yapısı, %100 çevrimdışı veri güvenliği, modern sütun tabanlı bellek mimarisi "
        "ve veri temizlemeden akademik istatistiğe uzanan bütüncül stüdyosu ile bağımsız araştırmacılar, veri bilimciler ve kurumsal analistler için "
        "<b>en pratik, hızlı ve maliyetsiz yerel analitik standardını</b> temsil etmektedir.",
        s_body
    ))

    # Belgeyi Oluştur
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] PDF başarıyla üretildi: {output_path}")

if __name__ == "__main__":
    target_pdf = os.path.abspath("docs/DataViz_Benzeri_Uygulamalar_ve_Mimari_Karsilastirma_Raporu.pdf")
    build_pdf(target_pdf)
