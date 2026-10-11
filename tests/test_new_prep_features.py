import sys
sys.stdout.reconfigure(encoding='utf-8')
import io
import json
import pandas as pd
import numpy as np
from app import create_app
from core.store import set_df, get_df

app = create_app()
client = app.test_client()

print("══════════════════════════════════════════════════════════════")
print("🧪 DATA PREP YENİ NESİL MÜHENDİSLİK ENTEGRASYON TESTLERİ")
print("══════════════════════════════════════════════════════════════")

# TEST 1: MICE & KNN Eksik Veri Temizleme (/clean_data ile "mice" ve "knn")
print("\n[TEST 1] MICE & KNN Eksik Veri Temizleme Testi:")
csv_missing = (
    "x1,x2,kat\n"
    "1.0,10.0,A\n"
    "2.0,20.0,B\n"
    ",30.0,A\n"
    "4.0,,B\n"
    "5.0,50.0,A\n"
    "6.0,60.0,B\n"
    ",70.0,A\n"
    "8.0,,B\n"
    "9.0,90.0,A\n"
    "10.0,100.0,B\n"
)

# MICE Testi
res_up = client.post("/upload", data={"file": (io.BytesIO(csv_missing.encode("utf-8")), "missing_test.csv")}, content_type="multipart/form-data")
assert res_up.status_code == 200, f"Upload başarısız: {res_up.data}"

res_mice = client.post("/clean_data", json={"action": "mice"})
assert res_mice.status_code == 200, f"MICE başarısız: {res_mice.data}"
data_mice = res_mice.get_json()
assert data_mice["success"] is True
health_mice = data_mice.get("health", {})
print(f"  ✅ MICE Temizleme Başarılı! Eksik satır: {health_mice.get('missing_rows', 0)}")

# KNN Testi
res_up = client.post("/upload", data={"file": (io.BytesIO(csv_missing.encode("utf-8")), "missing_test2.csv")}, content_type="multipart/form-data")
assert res_up.status_code == 200, f"Upload 2 başarısız: {res_up.data}"

res_knn = client.post("/clean_data", json={"action": "knn"})
assert res_knn.status_code == 200, f"KNN başarısız: {res_knn.data}"
data_knn = res_knn.get_json()
assert data_knn["success"] is True
health_knn = data_knn.get("health", {})
print(f"  ✅ KNN Temizleme Başarılı! Eksik satır: {health_knn.get('missing_rows', 0)}")

# TEST 2: Bellek Downcast (/optimize_memory) ve Kirli Sayı Kurtarma (/recover_dirty_types)
print("\n[TEST 2] Bellek Downcast & Kirli Sayı Kurtarma Testi:")
csv_dirty = "id,oran,kategori,kirli_fiyat\n"
for i in range(100):
    fiyat_str = f"{1000 + i * 25},50 TL"
    csv_dirty += f"{i},{round(0.1 + i*0.008, 4)},Kategori_{i % 3},{fiyat_str}\n"

res_up3 = client.post("/upload", data={"file": (io.BytesIO(csv_dirty.encode("utf-8")), "dirty_test.csv")}, content_type="multipart/form-data")
assert res_up3.status_code == 200

# Bellek Sıkıştırma
res_mem = client.post("/optimize_memory")
assert res_mem.status_code == 200, f"Bellek optimizasyonu başarısız: {res_mem.data}"
data_mem = res_mem.get_json()
assert data_mem["success"] is True
print(f"  ✅ Bellek Sıkıştırma Başarılı: %{data_mem['metrics']['savings_percentage']} RAM tasarrufu ({data_mem['metrics']['start_memory_mb']} MB -> {data_mem['metrics']['end_memory_mb']} MB)")

# Kirli Sayı Kurtarma
# Eğer upload anında otomatik kurtarılmışsa, manuel uç noktayı test etmek için ham kirli DataFrame ata
raw_dirty_df = pd.DataFrame({"id": list(range(100)), "kirli_fiyat": [f"{1000 + i * 25},50 TL" for i in range(100)]})
from core.store import set_df
with client.session_transaction() as sess:
    curr_uid = sess.get("user_id")
set_df(raw_dirty_df, 1, user_id=curr_uid)

res_dirty = client.post("/recover_dirty_types")
assert res_dirty.status_code == 200, f"Tip kurtarma başarısız: {res_dirty.data}"
data_dirty = res_dirty.get_json()
assert data_dirty["success"] is True
assert data_dirty["recovered_columns_count"] >= 1, "kirli_fiyat sütunu kurtarılamadı"
print(f"  ✅ Kirli Sayı Kurtarma Başarılı: {data_dirty['recovered_columns_count']} sütun kurtarıldı. Rapor: {data_dirty['report'][0]['column']} -> {data_dirty['report'][0]['recovered_type']}")

# TEST 3: OpenRefine Metin Kümeleme (/find_text_clusters) ve Birleştirme (/merge_text_clusters)
print("\n[TEST 3] OpenRefine Metin Kümeleme & İyileştirme Testi:")
csv_cluster = (
    "sehir,puan\n"
    "İstanbul,85\n"
    "istanbul,90\n"
    "İSTANBUL ,78\n"
    "ankara,95\n"
    "Ankara,88\n"
    "ANKARA,92\n"
    "İzmir,80\n"
    "izmir,82\n"
    "Bursa,70\n"
)
res_up4 = client.post("/upload", data={"file": (io.BytesIO(csv_cluster.encode("utf-8")), "cluster_test.csv")}, content_type="multipart/form-data")
assert res_up4.status_code == 200

# Kümeleri Bul
res_find = client.post("/find_text_clusters", json={"column": "sehir", "method": "fingerprint"})
assert res_find.status_code == 200, f"find_text_clusters başarısız: {res_find.data}"
data_find = res_find.get_json()
assert data_find["success"] is True
assert data_find["cluster_count"] >= 2, "İstanbul ve Ankara kümeleri bulunamadı"
print(f"  ✅ Metin Kümeleri Bulundu: {data_find['cluster_count']} küme tespit edildi.")

# Kümeleri Birleştir
merges_payload = [
    {"canonical": "İstanbul", "variants": ["İstanbul", "istanbul", "İSTANBUL "]},
    {"canonical": "Ankara", "variants": ["ankara", "Ankara", "ANKARA"]}
]
res_merge_cl = client.post("/merge_text_clusters", json={"column": "sehir", "merges": merges_payload})
assert res_merge_cl.status_code == 200, f"merge_text_clusters başarısız: {res_merge_cl.data}"
data_merge_cl = res_merge_cl.get_json()
assert data_merge_cl["success"] is True
print(f"  ✅ Kümeler Birleştirildi: {data_merge_cl['message']}")

# TEST 4: Hızlı Bulanık Eşleştirme (Fast Fuzzy Join) (/fast_fuzzy_join)
print("\n[TEST 4] Hızlı Bulanık Eşleştirme (Fast Fuzzy Join) Testi:")
csv_f1 = (
    "musteri,satis\n"
    "Ali Yilmaz,100\n"
    "Mehmet Demir,200\n"
    "Ayse Kaya,150\n"
    "Fatma Celik,300\n"
)
csv_f2 = (
    "ad_soyad,sehir\n"
    "Ali Yılmaz,İstanbul\n"
    "Mehmet  Demir ,Ankara\n"
    "Ayşe Kaya,İzmir\n"
    "Kemal Sunal,Bursa\n"
)
# 1. Dosyayı yükle
res_up_f1 = client.post("/upload", data={"file": (io.BytesIO(csv_f1.encode("utf-8")), "f1.csv")}, content_type="multipart/form-data")
assert res_up_f1.status_code == 200

# 2. Dosyayı preview_second_file ile yükle
res_up_f2 = client.post("/preview_second_file", data={"file2": (io.BytesIO(csv_f2.encode("utf-8")), "f2.csv")}, content_type="multipart/form-data")
assert res_up_f2.status_code == 200

res_fuzzy = client.post("/fast_fuzzy_join", json={
    "key1": "musteri",
    "key2": "ad_soyad",
    "threshold": 0.70
})
assert res_fuzzy.status_code == 200, f"fast_fuzzy_join başarısız: {res_fuzzy.data}"
data_fuzzy = res_fuzzy.get_json()
assert data_fuzzy["success"] is True
metrics = data_fuzzy["metrics"]
assert metrics["matched_unique_keys"] >= 3, f"Eşleşen anahtar sayısı beklenenden az: {metrics['matched_unique_keys']}"
print(f"  ✅ Fast Fuzzy Join Başarılı! Eşleşen Anahtar: {metrics['matched_unique_keys']}, Süre: {metrics['elapsed_ms']} ms, Tasarruf: %{metrics['computation_reduction_pct']}")

print("\n══════════════════════════════════════════════════════════════")
print("🎉 TÜM 4 YENİ NESİL MÜHENDİSLİK ÖZELLİĞİ BAŞARIYLA DOĞRULANDI!")
print("══════════════════════════════════════════════════════════════")
