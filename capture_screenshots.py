import os
import time
from playwright.sync_api import sync_playwright

BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
OUTPUT_DIR = r"e:\antigravity\proje1\dataviz\docs\images"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=BRAVE_PATH,
            headless=True,
            args=["--disable-gpu", "--no-sandbox"],
        )
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # 1. LANDING PAGE
        print("1. Capturing landing.png...")
        page.goto("http://127.0.0.1:5000/")
        page.wait_for_timeout(1200)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "landing.png"))
        print(" -> landing.png captured")

        # 2. UPLOAD SCREEN (STEP 1)
        print("2. Capturing upload_progress.png (Step 1)...")
        page.goto("http://127.0.0.1:5000/analysis")
        page.wait_for_timeout(1200)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "upload_progress.png"))
        print(" -> upload_progress.png captured")

        # Load Sample Dataset
        print("Loading sample dataset...")
        page.click("#btnLoadSampleData")
        page.wait_for_selector("#colPool .col-pill", timeout=12000)
        page.wait_for_timeout(1500)

        # 3. ANALYSIS STEP 2 (CONFIG & CHARTS)
        print("3. Capturing analysis.png (Step 2)...")
        page.screenshot(path=os.path.join(OUTPUT_DIR, "analysis.png"))
        print(" -> analysis.png captured")

        # 4. DATA HEALER MODAL
        print("4. Capturing data_healer.png...")
        page.evaluate("openDataPrepModal()")
        page.wait_for_selector("#dataPrepModal:not(.hidden)", timeout=6000)
        page.wait_for_timeout(1200)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "data_healer.png"))
        print(" -> data_healer.png captured")
        # Close modal
        page.evaluate("document.getElementById('btnCloseDataPrepModal')?.click()")
        page.wait_for_timeout(600)

        # 5. TRUST STUDIO
        print("5. Capturing trust_studio.png...")
        page.evaluate("showScreen('trust')")
        page.wait_for_selector("#screen-trust-studio:not(.hidden)", timeout=6000)
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "trust_studio.png"))
        print(" -> trust_studio.png captured")
        # Return to Step 2
        page.evaluate("showScreen(2)")
        page.wait_for_timeout(1000)

        # 6. PIVOT STUDIO
        print("6. Capturing pivot_studio.png...")
        page.evaluate("showScreen('pivot')")
        page.wait_for_selector("#screen-pivot-studio:not(.hidden)", timeout=6000)
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "pivot_studio.png"))
        print(" -> pivot_studio.png captured")
        # Return to Step 2
        page.evaluate("showScreen(2)")
        page.wait_for_timeout(1000)

        # 7. STEP 3 - ACTIVE CHART
        print("7. Capturing studio_step3.png...")
        page.evaluate("""() => {
            const cat = Array.from(document.querySelectorAll('#colPool .col-pill[data-type="cat"]')).map(el => el.getAttribute('data-col'))[0] || 'Bolge';
            const num = Array.from(document.querySelectorAll('#colPool .col-pill[data-type="num"]')).map(el => el.getAttribute('data-col'))[0] || 'Toplam_Ciro_TL';
            axisConfig.x = cat;
            axisConfig.y = [num];
            goToStep3('bar', 'Dikey Çubuk Grafik');
        }""")
        page.wait_for_selector("#step3-dashboard:not(.hidden)", timeout=6000)
        page.wait_for_timeout(3000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "studio_step3.png"))
        print(" -> studio_step3.png captured")

        # 8. STEP 3 - STATS TAB
        print("8. Capturing stats_horizontal.png...")
        page.evaluate("""() => {
            const btn = document.querySelector('#mainTabsBar .tab-btn[data-tab="stats"]');
            if (btn) btn.click();
        }""")
        page.wait_for_timeout(2500)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "stats_horizontal.png"))
        print(" -> stats_horizontal.png captured")

        # 9. STEP 3 - REGRESSION TAB
        print("9. Capturing regression.png...")
        page.evaluate("""() => {
            const btn = document.querySelector('#mainTabsBar .tab-btn[data-tab="regression"]');
            if (btn) btn.click();
        }""")
        page.wait_for_timeout(2500)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "regression.png"))
        print(" -> regression.png captured")

        browser.close()
        print("SUCCESS: All 9 screenshots captured successfully!")


if __name__ == "__main__":
    run()
