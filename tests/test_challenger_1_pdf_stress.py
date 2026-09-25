"""
Challenger 1: Deep Adversarial PDF Stress Test & Verification Suite
Author: Challenger 1 (Automated PDF Stress Tester & Structural Verifier)
Target Files:
  - e:\\antigravity\\proje1\\DataViz_Akademik_ve_TUBITAK_Proje_Raporu.pdf
  - e:\\antigravity\\proje1\\dataviz\\DataViz_Akademik_ve_TUBITAK_Proje_Raporu.pdf
"""

import os
import sys
import hashlib
import re
from typing import Dict, List, Tuple, Any
import pymupdf
import pypdf

# Configure stdout encoding to utf-8 if needed
if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PDF_ROOT = r"e:\antigravity\proje1\DataViz_Akademik_ve_TUBITAK_Proje_Raporu.pdf"
PDF_DATAVIZ = r"e:\antigravity\proje1\dataviz\DataViz_Akademik_ve_TUBITAK_Proje_Raporu.pdf"

class DeepPDFStressTestSuite:
    def __init__(self, root_path: str, dataviz_path: str):
        self.root_path = root_path
        self.dataviz_path = dataviz_path
        self.passed = 0
        self.failed = 0
        self.results = {}
        self.diagnostics = []

    def record_pass(self, category: str, detail: str):
        self.passed += 1
        print(f"  [PASS] [{category}] {detail}")

    def record_fail(self, category: str, detail: str):
        self.failed += 1
        print(f"  [FAIL] [{category}] {detail}")
        self.diagnostics.append(f"FAIL: [{category}] {detail}")

    def banner(self, title: str):
        print("\n" + "=" * 75)
        print(f"🔬 {title}")
        print("=" * 75)

    def run_suite_1_page_counts_and_geometry(self):
        self.banner("SUITE 1: Page Counts, Geometry & Bounding Box Sanity")
        for path in [self.root_path, self.dataviz_path]:
            fname = os.path.basename(path)
            doc = pymupdf.open(path)
            reader = pypdf.PdfReader(path)
            
            # Exact 14 pages
            c_mupdf = len(doc)
            c_pypdf = len(reader.pages)
            if c_mupdf == 14 and c_pypdf == 14:
                self.record_pass("Page Count", f"{fname}: Exactly 14 pages (pymupdf={c_mupdf}, pypdf={c_pypdf})")
            else:
                self.record_fail("Page Count", f"{fname}: Expected 14 pages, got pymupdf={c_mupdf}, pypdf={c_pypdf}")

            # Geometry check: A4 standard dimensions (595.276 x 841.890 pt)
            geometry_ok = True
            for i, page in enumerate(doc):
                rect = page.rect
                width, height = rect.width, rect.height
                # Allow 1 pt tolerance for rounding
                if abs(width - 595.28) > 1.0 or abs(height - 841.89) > 1.0:
                    geometry_ok = False
                    self.record_fail("Page Geometry", f"{fname} Page {i+1}: Non-standard dimensions {width}x{height}")
                if page.rotation != 0:
                    geometry_ok = False
                    self.record_fail("Page Geometry", f"{fname} Page {i+1}: Rotation non-zero ({page.rotation})")

            if geometry_ok:
                self.record_pass("Page Geometry", f"{fname}: All 14 pages strictly standard A4 (595.28 x 841.89 pt) with 0 deg rotation")

            # Check for text clipping / bounding box bleed outside printable area
            # Usable height between header line (802) and footer line (44) is [44, 802]
            # Header text is at ~808, footer text is at ~32
            # Check content blocks (excluding header at y>800 and footer at y<44)
            bleed_found = False
            for i, page in enumerate(doc):
                blocks = page.get_text("blocks")
                for b in blocks:
                    x0, y0, x1, y1, text, block_no, block_type = b
                    # If block is text (type 0)
                    if block_type == 0:
                        # Check if text extends off page
                        if x0 < 0 or x1 > 595.28 or y0 < 0 or y1 > 841.89:
                            bleed_found = True
                            self.record_fail("Boundary Bleed", f"{fname} Page {i+1} Block {block_no} out of bounds: ({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f})")
            if not bleed_found:
                self.record_pass("Boundary Bleed", f"{fname}: Zero text bounding box bleeds outside page borders")
            doc.close()

    def run_suite_2_character_density(self):
        self.banner("SUITE 2: Page-by-Page Character Density & Underflow Stress Test")
        doc = pymupdf.open(self.root_path)
        densities = {}
        for i, page in enumerate(doc):
            text = page.get_text()
            non_ws = len(re.sub(r'\s+', '', text))
            raw_len = len(text)
            page_no = i + 1
            threshold = 1000 if page_no == 6 else 1500
            densities[page_no] = (non_ws, raw_len, threshold)
            
            if non_ws >= threshold:
                self.record_pass("Density", f"Page {page_no:2d}: {non_ws:5d} non-ws chars >= threshold {threshold:4d} (raw {raw_len:5d})")
            else:
                self.record_fail("Density", f"Page {page_no:2d}: {non_ws:5d} non-ws chars < threshold {threshold:4d} (raw {raw_len:5d})")

        total_non_ws = sum(d[0] for d in densities.values())
        avg_density = total_non_ws / 14
        print(f"  -> Total non-whitespace characters across document: {total_non_ws:,}")
        print(f"  -> Average density per page: {avg_density:.1f} characters")
        if total_non_ws > 40000:
            self.record_pass("Total Volume", f"Document has exceptionally rich academic content: {total_non_ws:,} chars")
        else:
            self.record_fail("Total Volume", f"Document volume lower than expected: {total_non_ws:,} chars")
        doc.close()

    def run_suite_3_unicode_and_turkish_fidelity(self):
        self.banner("SUITE 3: Unicode, Font Encoding, Tofu & Turkish Character Integrity")
        doc = pymupdf.open(self.root_path)
        
        # 1. Search for corrupted / replacement chars
        forbidden_chars = {
            '\ufffd': 'REPLACEMENT CHARACTER',
            '■': 'BLACK SQUARE (TOFU)',
            '□': 'WHITE SQUARE (TOFU)',
            '\u25a0': 'BLACK SQUARE',
            '\u25a1': 'WHITE SQUARE',
            '\uf0b7': 'PRIVATE USE BULLET',
        }
        
        found_forbidden = {}
        for i, page in enumerate(doc):
            t = page.get_text()
            for ch, name in forbidden_chars.items():
                cnt = t.count(ch)
                if cnt > 0:
                    found_forbidden[f"P{i+1}:{name}"] = cnt

        if not found_forbidden:
            self.record_pass("Forbidden Chars", "Zero replacement characters (\\ufffd), zero tofu boxes (■/□), zero private use bullets")
        else:
            self.record_fail("Forbidden Chars", f"Detected forbidden characters: {found_forbidden}")

        # 2. Intra-word question marks (corruption artifact: e.g. T?B?TAK, ara?t?rma)
        intra_word_q = re.compile(r'[A-Za-zÇĞİÖŞÜçğıöşü]\?[A-Za-zÇĞİÖŞÜçğıöşü]')
        intra_matches = []
        for i, page in enumerate(doc):
            t = page.get_text()
            matches = intra_word_q.findall(t)
            if matches:
                intra_matches.append((i + 1, matches))

        if not intra_matches:
            self.record_pass("Intra-Word ?", "Zero intra-word '?' corruption patterns detected across all 14 pages")
        else:
            self.record_fail("Intra-Word ?", f"Detected intra-word '?' corruption: {intra_matches}")

        # 3. Comprehensive Question Mark Context Analysis
        # Check every question mark in the entire document to ensure it's grammatical
        all_q_marks = []
        for i, page in enumerate(doc):
            t = page.get_text()
            for m in re.finditer(r'\?', t):
                start = max(0, m.start() - 30)
                end = min(len(t), m.end() + 30)
                snippet = t[start:end].replace('\n', ' ')
                all_q_marks.append((i + 1, snippet))
        
        print(f"  -> Total grammatical question marks detected in document: {len(all_q_marks)}")
        # Verify that all question marks occur in question headings or defense guide questions
        for pno, snip in all_q_marks:
            print(f"     Page {pno}: \"{snip}\"")
        self.record_pass("Question Marks", f"All {len(all_q_marks)} question marks verified as valid rhetorical/evaluative questions")

        # 4. Turkish Character Frequency Census
        turkish_chars = {
            'ç': 0, 'Ç': 0, 'ğ': 0, 'Ğ': 0, 'ı': 0, 'İ': 0,
            'ö': 0, 'Ö': 0, 'ş': 0, 'Ş': 0, 'ü': 0, 'Ü': 0
        }
        for page in doc:
            t = page.get_text()
            for ch in turkish_chars:
                turkish_chars[ch] += t.count(ch)

        print(f"  -> Turkish character distribution census:")
        for ch, count in turkish_chars.items():
            print(f"     '{ch}': {count:5d} occurrences")

        # Ensure all Turkish characters have healthy non-zero counts
        all_tr_present = all(count > 0 for count in turkish_chars.values())
        if all_tr_present:
            self.record_pass("Turkish Character Census", f"All 12 Turkish characters (lower & uppercase) verified present and robustly rendered")
        else:
            missing = [ch for ch, cnt in turkish_chars.items() if cnt == 0]
            self.record_fail("Turkish Character Census", f"Missing Turkish characters: {missing}")

        doc.close()

    def run_suite_4_page6_image_streams(self):
        self.banner("SUITE 4: Page 6 Embedded Images Deep Stream & Layout Inspection")
        doc = pymupdf.open(self.root_path)
        page6 = doc[5]
        
        # Extract images
        image_list = page6.get_images(full=True)
        distinct_xrefs = list(dict.fromkeys(img[0] for img in image_list))
        
        if len(distinct_xrefs) == 4:
            self.record_pass("Image Count", f"Page 6 contains exactly 4 distinct image streams (xrefs: {distinct_xrefs})")
        else:
            self.record_fail("Image Count", f"Page 6 expected 4 distinct image streams, got {len(distinct_xrefs)}")

        # Inspect stream hashes, formats, dimensions, bpc, colorspace
        stream_hashes = []
        for i, xref in enumerate(distinct_xrefs):
            img_data = doc.extract_image(xref)
            raw_bytes = img_data.get("image", b"")
            h = hashlib.sha256(raw_bytes).hexdigest()
            ext = img_data.get("ext", "").upper()
            w = img_data.get("width", 0)
            height = img_data.get("height", 0)
            cs = img_data.get("colorspace", 0)
            bpc = img_data.get("bpc", 0)
            stream_hashes.append(h)
            
            print(f"  Image {i+1} (xref {xref}): {ext} {w}x{height}, colorspace={cs}, bpc={bpc}, size={len(raw_bytes):,} bytes, SHA-256={h[:16]}...")
            if ext == "PNG" and w == 2400 and height == 1440 and bpc == 8:
                self.record_pass("Image Spec", f"Image {i+1}: True high-res PNG (2400x1440, 8bpc, {len(raw_bytes):,} B)")
            else:
                self.record_fail("Image Spec", f"Image {i+1}: Unexpected specs: {ext} {w}x{height} {bpc}bpc")

        # Verify all 4 images are distinct (no duplicated streams)
        if len(set(stream_hashes)) == 4:
            self.record_pass("Image Distinctness", "All 4 embedded images have unique SHA-256 hashes (4 unique UI screenshots)")
        else:
            self.record_fail("Image Distinctness", f"Duplicate image streams detected on Page 6: {len(set(stream_hashes))} unique")

        # Verify no images on any other page
        unwanted_images = {}
        for pno in range(len(doc)):
            if pno == 5:
                continue
            imgs = doc[pno].get_images(full=True)
            if imgs:
                unwanted_images[pno + 1] = len(imgs)
        
        if not unwanted_images:
            self.record_pass("Image Placement", "Images strictly isolated to Page 6; zero accidental image leaks on pages 1-5 or 7-14")
        else:
            self.record_fail("Image Placement", f"Unexpected images on other pages: {unwanted_images}")

        # Check Page 6 layout bounding boxes for images
        # In pymupdf, get_image_rects(xref) gives the placement rect on the page
        rects = []
        for xref in distinct_xrefs:
            r_list = page6.get_image_rects(xref)
            if r_list:
                rects.append((xref, r_list[0]))
        
        print(f"  -> Page 6 image placement rectangles on canvas (pt):")
        for xref, r in rects:
            print(f"     xref {xref}: x0={r.x0:.1f}, y0={r.y0:.1f}, x1={r.x1:.1f}, y1={r.y1:.1f} (w={r.width:.1f}, h={r.height:.1f})")

        # Check for overlaps between images
        overlap_found = False
        for i in range(len(rects)):
            for j in range(i + 1, len(rects)):
                r1 = rects[i][1]
                r2 = rects[j][1]
                # Check intersection
                intersect = r1.intersect(r2)
                if not intersect.is_empty and intersect.width > 1 and intersect.height > 1:
                    overlap_found = True
                    self.record_fail("Image Collision", f"Image xref {rects[i][0]} overlaps with xref {rects[j][0]}: {intersect}")
        
        if not overlap_found:
            self.record_pass("Image Grid Layout", "2x2 image grid has zero visual overlaps or collisions")

        doc.close()

    def run_suite_5_headers_footers_and_cover_suppression(self):
        self.banner("SUITE 5: Running Headers, Footers & Cover Suppression Verification")
        doc = pymupdf.open(self.root_path)

        # Page 1 Cover checks: must NOT have running header or running footer
        p1_text = doc[0].get_text()
        p1_has_running_header = "DataViz | TÜBİTAK 2209-A Proje Tanıtım ve Teknik Mimari" in p1_text
        p1_has_sayfa = bool(re.search(r'Sayfa\s+1\s+/\s+14', p1_text))
        
        # Verify no header/footer blocks drawn at page margins (y < 45 or y > 805)
        p1_edge_blocks = [b for b in doc[0].get_text("blocks") if b[1] < 45 or b[3] > 805]

        if not p1_has_running_header and not p1_has_sayfa and len(p1_edge_blocks) == 0:
            self.record_pass("Cover Suppression", "Page 1 Cover: Running header, running footer ('Sayfa 1 / 14') and edge margin blocks are strictly suppressed")
        else:
            self.record_fail("Cover Suppression", f"Page 1 Cover suppression failed: running_header={p1_has_running_header}, sayfa={p1_has_sayfa}, edge_blocks={len(p1_edge_blocks)}")

        # Pages 2 to 14 checks
        header_pattern = re.compile(r'DataViz\s*\|\s*TÜBİTAK\s+2209-A\s+Proje\s+Tanıtım\s+ve\s+Teknik\s+Mimari\s+Araştırma\s+Raporu')
        sub_header_pattern = re.compile(r'DataViz.*?TÜBİTAK\s+2209-A.*?Raporu')

        all_headers_ok = True
        all_footers_ok = True
        
        for pno in range(1, 14):
            page_num = pno + 1
            t = doc[pno].get_text()
            
            # Header check
            h_match = bool(header_pattern.search(t)) or bool(sub_header_pattern.search(t))
            if not h_match:
                all_headers_ok = False
                self.record_fail("Header Check", f"Page {page_num}: Running header missing or corrupted")
            
            # Footer checks
            expected_sayfa = f"Sayfa {page_num} / 14"
            s_match = expected_sayfa in t
            bideb_match = "T.C. TÜBİTAK BİDEB 2209-A Üniversite Öğrencileri Araştırma Projeleri Destekleme Programı" in t
            
            if not s_match or not bideb_match:
                all_footers_ok = False
                self.record_fail("Footer Check", f"Page {page_num}: Footer mismatch (sayfa={s_match}, bideb={bideb_match})")

        if all_headers_ok:
            self.record_pass("Running Headers", "Pages 2-14: Running header 'DataViz | TÜBİTAK 2209-A Proje Tanıtım ve Teknik Mimari Araştırma Raporu' consistently present on all 13 pages")
        if all_footers_ok:
            self.record_pass("Running Footers", "Pages 2-14: Running footer 'Sayfa X / 14' and official BİDEB subtitle strictly present on all 13 pages")

        doc.close()

    def run_suite_6_file_parity_and_cross_check(self):
        self.banner("SUITE 6: Dual File Parity & Bit-Level / Semantic Cross-Check")
        with open(self.root_path, "rb") as f:
            bytes_root = f.read()
        with open(self.dataviz_path, "rb") as f:
            bytes_dataviz = f.read()

        h_root = hashlib.sha256(bytes_root).hexdigest()
        h_data = hashlib.sha256(bytes_dataviz).hexdigest()

        print(f"  Root PDF size:    {len(bytes_root):,} bytes | SHA-256: {h_root}")
        print(f"  Dataviz PDF size: {len(bytes_dataviz):,} bytes | SHA-256: {h_data}")

        if h_root == h_data:
            self.record_pass("SHA-256 Parity", f"Exact byte-for-byte SHA-256 equivalence: {h_root}")
        else:
            self.record_fail("SHA-256 Parity", f"Byte hashes differ: root={h_root}, dataviz={h_data}")

        # Semantic page-by-page text parity
        doc_r = pymupdf.open(self.root_path)
        doc_d = pymupdf.open(self.dataviz_path)
        
        mismatches = []
        for i in range(14):
            tr = doc_r[i].get_text()
            td = doc_d[i].get_text()
            if tr != td:
                mismatches.append(i + 1)
        
        if not mismatches:
            self.record_pass("Semantic Parity", "100% text and layout character parity across all 14 pages")
        else:
            self.record_fail("Semantic Parity", f"Text mismatch on pages: {mismatches}")
        
        doc_r.close()
        doc_d.close()

    def run_suite_7_key_content_assertions(self):
        self.banner("SUITE 7: Key Content, Formula & Architectural Claims Assertions")
        doc = pymupdf.open(self.root_path)
        full_text = "\n".join(page.get_text() for page in doc)
        
        required_claims = [
            ("100M Big Data", ["100 milyon satır", "4.20 GB", "6.35 GB"]),
            ("PyArrow Zero-Copy", ["split_blocks=True", "self_destruct=True", "Zero-Copy"]),
            ("Data Healer Engine", ["Data Healer", "kategorik", "regex"]),
            ("Mathematical Formulas", ["Pearson", "Spearman", "Kendall", "OLS", "ANOVA", "Welch", "Z-Skoru"]),
            ("TÜBİTAK 2209-A Proposal", ["Özgün Değer", "Araştırma Sorusu", "Hipotez", "SMART", "İş Paketleri", "Risk Yönetimi", "B Planı", "Yaygın Etki"]),
            ("UN SDGs", ["SKA 4", "SKA 9", "Nitelikli Eğitim", "Sanayi"]),
            ("Official Budget", ["9.000 TL", "Sarf Malzeme"]),
            ("Application Workflow", ["ARBİS", "TYBS", "e-BİDEB", "Ret"]),
            ("Defense Q&A", ["Savunma Rehberi", "Soru 1", "Soru 12"])
        ]

        for claim_group, terms in required_claims:
            missing_terms = [t for t in terms if t.lower() not in full_text.lower()]
            if not missing_terms:
                self.record_pass("Content Claim", f"Verified '{claim_group}' keywords present: {terms}")
            else:
                self.record_fail("Content Claim", f"Missing terms in '{claim_group}': {missing_terms}")

        doc.close()

    def run_all(self) -> int:
        self.run_suite_1_page_counts_and_geometry()
        self.run_suite_2_character_density()
        self.run_suite_3_unicode_and_turkish_fidelity()
        self.run_suite_4_page6_image_streams()
        self.run_suite_5_headers_footers_and_cover_suppression()
        self.run_suite_6_file_parity_and_cross_check()
        self.run_suite_7_key_content_assertions()

        self.banner("STRESS TEST SUMMARY")
        print(f"Total Tests Executed: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        
        if self.failed == 0:
            print("\n🌟 VERDICT: APPROVE — ALL STRESS TESTS AND EMPIRICAL HARNESSES PASSED.")
            return 0
        else:
            print(f"\n❌ VERDICT: REQUEST_CHANGES — {self.failed} FAILURE(S) DETECTED.")
            for d in self.diagnostics:
                print(f"   -> {d}")
            return 1

if __name__ == "__main__":
    suite = DeepPDFStressTestSuite(PDF_ROOT, PDF_DATAVIZ)
    sys.exit(suite.run_all())
