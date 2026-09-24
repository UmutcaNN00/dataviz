import subprocess

git_path = r"C:\Users\umutc\AppData\Local\GitHubDesktop\app-3.6.5\resources\app\git\cmd\git.exe"

def run_git(*args):
    # Enforce UTF-8 encoding environment for the subprocess
    env = dict(subprocess.os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run([git_path, *args], capture_output=True, text=True, encoding='utf-8', env=env)
    return result

mapping = {
    "99dd121": "ilk-sürüm: DataViz - İnteraktif Excel Veri Analizi Platformu",
    "ff616c0": "belge: rozetler ve teknoloji yığını ile detaylı README eklendi",
    "cb0ebee": "özellik(grafik): öneri motoru yenilendi ve Sankey/Hiyerarşik grafikler onarıldı",
    "61e98e3": "belge: klonlama URL'si dataviz olarak güncellendi",
    "a1c634e": "belge: mimari şema, kural matrisi ve API belgeleriyle kurumsal düzeyde README",
    "09e2dfa": "özellik(arayüz): karşılama sayfası için akademik ve istatistik stüdyosu baştan tasarlandı",
    "aa67df6": "özellik(a4-demo): etkileşimli A4 PDF stüdyosu simülatör sayfası eklendi",
    "07fd89a": "düzeltme(karşılama): bilimsel marquee sınırsız yapıldı ve doğru veri birleştirme terminolojisi eklendi",
    "e1d7501": "özellik(veri-araçları): veri onarımı (NaN) ve veri birleştirme araçları tüm adımlarda erişilebilir kılındı",
    "303f0f7": "düzeltme(yükleme): dosya seçici onarıldı ve adım 2'ye geçiş pürüzsüz hale getirildi",
    "7ebd27e": "düzeltme(yükleme): tarayıcı uyumlu ve dayanıklı CSV/Excel dosya seçici eklendi",
    "c5b86e6": "düzeltme(yükleme): Chromium tıklama sorunu çözüldü ve örnek veri seti butonu eklendi",
    "2fa1311": "düzeltme(js): sözdizimi hataları çözüldü ve dosya yükleme olay dinleyicisi onarıldı",
    "3f19466": "düzeltme(genel): sonsuz döngü, NaN/Inf serileştirme ve Plotly render hataları giderildi, veri dışa aktar eklendi",
    "32580c5": "özellik(çekirdek): tahmin (forecasting) özelliği tamamen sistemden kaldırıldı",
    "786ecc1": "belge: README dosyası görseller, net yapı ve doğrulanmış içeriklerle yenilendi",
    "7316693": "belge: gereksiz görseller, zero-gpu ibaresi ve Pro eki çıkarıldı; proje adı DataViz yapıldı",
    "2fc45c6": "belge: lisans metni ve rozeti README'den çıkarıldı",
    "810981b": "özellik: docker desteği, akıllı tip onarıcı, veri sağlığı ve performans geliştirmeleri",
    "752c0b5": "yeniden-düzenleme: backend ve frontend modüler mimari dönüşümü",
    "0d9bd2e": "düzeltme: grafik çizimi, parametre uyuşmazlığı ve KPI/istatistik uç noktaları onarıldı",
    "3e21229": "düzeltme: grafik çizimi sonrası ekranda kalan yüklenme animasyonu kaldırıldı",
    "5418b32": "belge: 50+ grafik, büyük veri ve modüler mimariyi kapsayan kapsamlı README güncellemesi",
    "d3cd715": "düzeltme(entegrasyon): modüller arası rotalar, bağlantılar ve senkronizasyon uyumlu hale getirildi",
    "a9e19fc": "özellik: app.js, main_routes.py güncellemeleri, landing page korundu",
    "1c146a0": "belge: CHANGELOG.md eklendi",
    "02a9a81": "yeniden-düzenleme: 'Pro' markalaması ve demo konsept dosyaları profesyonel görünüm için kaldırıldı",
    "6bd566d": "belge: README dosyasına tarayıcı otomasyonu ile ekran görüntüleri eklendi",
    "da3b174": "belge: projeyi tam olarak anlatan, yetenekleri vurgulayan profesyonel bir readme hazırlandı"
}

hashes = [
    "99dd121", "ff616c0", "cb0ebee", "61e98e3", "a1c634e", "09e2dfa", "aa67df6", "07fd89a",
    "e1d7501", "303f0f7", "7ebd27e", "c5b86e6", "2fa1311", "3f19466", "32580c5", "786ecc1",
    "7316693", "2fc45c6", "810981b", "752c0b5", "0d9bd2e", "3e21229", "5418b32", "d3cd715",
    "a9e19fc", "1c146a0", "02a9a81", "6bd566d", "da3b174"
]

print("Resetting HEAD...")
run_git("reset", "--hard", "HEAD")

print("Checking out first commit...")
run_git("checkout", hashes[0])
run_git("commit", "--amend", "-m", mapping[hashes[0]], "--allow-empty")

for h in hashes[1:]:
    print(f"Processing {h}...")
    res = run_git("cherry-pick", h)
    if res.returncode != 0:
        print(f"Warning: Cherry-pick failed for {h}. Skipping.")
        run_git("cherry-pick", "--abort")
        continue
    run_git("commit", "--amend", "-m", mapping[h], "--allow-empty")

print("Forcing main branch update...")
run_git("branch", "-f", "main", "HEAD")
run_git("checkout", "main")
run_git("push", "-f", "origin", "main")
print("All done!")
