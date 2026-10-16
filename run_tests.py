"""
DataViz Test Runner & Quality Suite
Runs all unit, integration, edge-case, and statistical tests across the platform.
Supports Windows, Linux, and macOS environments.
"""

import os
import sys
import subprocess
import time

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
os.environ["PYTHONPATH"] = BASE_DIR

def check_syntax() -> bool:
    import py_compile
    import glob
    files = [
        f for f in glob.glob(os.path.join(BASE_DIR, "**", "*.py"), recursive=True)
        if ".venv" not in f and "venv" not in f
    ]
    try:
        for f in files:
            py_compile.compile(f, doraise=True)
        print(f"  {len(files)} Python dosyası sözdizimi açısından kusursuz.")
        return True
    except Exception as e:
        print(f"  Sözdizimi hatası: {e}")
        return False

def run_step(step_name: str, cmd_or_func) -> bool:
    print(f"\n{'=' * 65}")
    print(f"🚀 [TEST ADIMI] {step_name}")
    print(f"{'=' * 65}")
    start = time.time()
    if callable(cmd_or_func):
        success = cmd_or_func()
    else:
        result = subprocess.run(cmd_or_func, cwd=BASE_DIR, env=os.environ)
        success = (result.returncode == 0)
    duration = time.time() - start
    if success:
        print(f"✅ {step_name} BAŞARIYLA TAMAMLANDI ({duration:.2f}s)")
        return True
    else:
        print(f"❌ {step_name} HATA İLE SONUÇLANDI")
        return False

def main():
    print("═════════════════════════════════════════════════════════════════")
    print("📊 DATAVIZ TÜM TEST VE DOĞRULAMA ÇALIŞTIRICISI")
    print(f"📍 Çalışma Dizini: {BASE_DIR}")
    print(f"🐍 Python Sürümü: {sys.version.split()[0]}")
    print("═════════════════════════════════════════════════════════════════")

    python_bin = sys.executable

    steps = [
        ("Python Dosyaları Sözdizimi Derleme Denetimi", check_syntax),
        ("Birim Testleri (Unittest Suite: Audit Fixes & SPSS Reader)", [
            python_bin, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"
        ]),
        ("Uç Durum ve Sıfır Bölme / NaN Denetimleri (Edge Cases)", [
            python_bin, "tests/test_edge_cases.py"
        ]),
        ("İleri Seviye Veri Temizleme & Bellek Testleri (Data Prep & Imputation)", [
            python_bin, "tests/test_new_prep_features.py"
        ]),
        ("Yeni Nesil Entegrasyon Testleri (SIMD Pushdown, Contracts, Ensemble)", [
            python_bin, "tests/test_nextgen_integration.py"
        ]),
        ("Flask REST API Uç Nokta Entegrasyon Testleri (Routes & Guards)", [
            python_bin, "tests/test_routes_api.py"
        ]),
        ("İstatistik, ANOVA, Bayes ve ReportLab PDF Testleri (Stats & PDF)", [
            python_bin, "tests/test_stats_and_reporting.py"
        ]),
        ("28/28 Uçtan Uca Master Sistem Bağlantı Testi (E2E Connectivity)", [
            python_bin, "tests/test_system_connectivity.py"
        ]),
    ]

    failed_steps = []
    total_start = time.time()

    for name, cmd in steps:
        success = run_step(name, cmd)
        if not success:
            failed_steps.append(name)

    total_duration = time.time() - total_start
    print("\n" + "═" * 65)
    print("📋 GENEL DOĞRULAMA VE TEST SONUÇ RAPORU")
    print("═" * 65)
    print(f"⏱️ Toplam Süre: {total_duration:.2f} saniye")
    print(f"🧪 Koşulan Test Adımı: {len(steps)}")
    print(f"✅ Başarılı: {len(steps) - len(failed_steps)}")
    print(f"❌ Başarısız: {len(failed_steps)}")

    if failed_steps:
        print("\n⚠️ Başarısız Olan Adımlar:")
        for f in failed_steps:
            print(f"  • {f}")
        sys.exit(1)
    else:
        print("\n🎉 TEBRİKLER! TÜM BİRİM, ENTEGRASYON VE DOĞRULAMA TESTLERİ %100 GEÇTİ!")
        sys.exit(0)

if __name__ == "__main__":
    main()
