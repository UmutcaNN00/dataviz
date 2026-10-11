"""
DataViz - Kapsamlı Doğrulama ve Sınır Durum (Edge Cases) Test Paketi
Tüm UI metinleri, hata mesajları ve açıklamalar TÜRKÇE formatındadır.
"""

import io
import sys
import unittest
import numpy as np
import pandas as pd

# UTF-8 Konsol Desteği
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# DataViz servisleri ve store
from core.store import set_df, get_df, set_excel_data, get_excel_data, set_baseline_trust, set_is_cleaned
from services.file_service import (
    _deduplicate_columns,
    clean_dataframe,
    read_csv_safely,
    read_excel_safely,
    read_parquet_safely,
)
from services.memory_service import (
    optimize_dataframe_memory,
    auto_optimize_ingested_df,
)
from services.data_healer import clean_missing_data, detect_column_anomalies
from services.advanced_imputer import impute_missing_advanced
from services.clustering_service import find_clusters, apply_cluster_merges
from services.fast_fuzzy_join import fast_fuzzy_merge


class TestFileServiceAndMemory(unittest.TestCase):
    """1. Veri Yükleme ve Bellek Optimizasyonu Sınır Durum Testleri"""

    def test_deduplicate_columns_edge_cases(self):
        """None, boşluk, nan, Unnamed: ve satır sonu içeren sütun başlıkları"""
        raw_cols = ["", None, "Unnamed: 0", "nan", "Müşteri ID", "Müşteri ID", "Tutar\r\n", "Tutar\n"]
        cleaned = _deduplicate_columns(raw_cols)
        self.assertEqual(cleaned[0], "Sütun_1")
        self.assertEqual(cleaned[1], "Sütun_2")
        self.assertEqual(cleaned[2], "Sütun_3")
        self.assertEqual(cleaned[3], "Sütun_4")
        self.assertEqual(cleaned[4], "Müşteri ID")
        self.assertEqual(cleaned[5], "Müşteri ID_1")
        self.assertEqual(cleaned[6], "Tutar")
        self.assertEqual(cleaned[7], "Tutar_1")

    def test_clean_dataframe_edge_cases(self):
        """Boş DataFrame, tümü NaN olanlar ve Excel formül hataları"""
        empty_df = clean_dataframe(pd.DataFrame())
        self.assertTrue(empty_df.empty)

        all_nan_df = clean_dataframe(pd.DataFrame([[np.nan, np.nan], [np.nan, np.nan]]))
        self.assertTrue(all_nan_df.empty)

        excel_err_df = pd.DataFrame({
            "deger": ["#DIV/0!", "#VALUE!", "100", "#REF!"],
            "ad": ["Ali", "Veli", "Ayşe", "Fatma"]
        })
        cleaned = clean_dataframe(excel_err_df)
        self.assertTrue(pd.isna(cleaned.loc[0, "deger"]))
        self.assertTrue(pd.isna(cleaned.loc[1, "deger"]))
        self.assertEqual(cleaned.loc[2, "deger"], "100")

    def test_read_csv_safely_encodings_and_delimiters(self):
        """Farklı ayırıcılar (noktalı virgül, virgül, tab) ve Türkçe karakterler"""
        csv_content = "Adı;Soyadı;Maaş\nAhmet;Yılmaz;25000\nAyşe;Öztürk;30000"
        csv_bytes = csv_content.encode("windows-1254")
        df = read_csv_safely(io.BytesIO(csv_bytes))
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df.columns), ["Adı", "Soyadı", "Maaş"])
        self.assertEqual(df.loc[0, "Adı"], "Ahmet")

    def test_memory_optimization_nullable_int_with_na(self):
        """Nullable Int64 ve NA içeren sütunların çökmeden dönüştürülmesi"""
        df_na = pd.DataFrame({"id": pd.Series([10, 20, None, 50], dtype="Int64")})
        opt_df, metrics = optimize_dataframe_memory(df_na)
        self.assertNotIn("error", metrics)
        self.assertIn("UInt8", str(opt_df["id"].dtype))

    def test_memory_optimization_all_na_and_single_row(self):
        """Tümü NA olan int sütunu ve tek satırlık veri optimizasyonu"""
        df_all_na = pd.DataFrame({"all_na": pd.Series([None, None], dtype="Int64")})
        opt_df, metrics = optimize_dataframe_memory(df_all_na)
        self.assertNotIn("error", metrics)

        # Tek satırlık veri kategoriye zorlanmamalıdır (kardinalite koruması)
        df_single = pd.DataFrame({"kategori": ["Elektronik"], "tutar": [150.0]})
        opt_single, _ = optimize_dataframe_memory(df_single)
        self.assertNotEqual(str(opt_single["kategori"].dtype), "category")

    def test_auto_optimize_ingested_df(self):
        """Boru hattı: Kirli para birimi kurtarma + tarih kurtarma + downcasting"""
        df_dirty = pd.DataFrame({
            "fiyat": ["1.250,50 TL", "2.000,00 TL", "500,00 TL"],
            "tarih": ["2024-01-15", "2024-02-20", "2024-03-25"],
            "adet": [5, 10, 15]
        })
        optimized = auto_optimize_ingested_df(df_dirty)
        self.assertTrue(pd.api.types.is_numeric_dtype(optimized["fiyat"]))
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(optimized["tarih"]))


class TestDataCleaningAndImputation(unittest.TestCase):
    """2. Veri Temizleme, İkame (MICE/KNN/Mod) ve Metin Kümeleme Testleri"""

    def test_clean_missing_data_modes(self):
        """drop, mean, median, zero, mode ve drop_duplicates işlemleri"""
        df = pd.DataFrame({
            "sayi": [10.0, 20.0, 20.0, np.nan],
            "kategori": ["A", "B", "B", None]
        })

        # 1. Mod ile doldurma (mode)
        df_mode = clean_missing_data(df, action="mode")
        self.assertEqual(df_mode.loc[3, "sayi"], 20.0)
        self.assertEqual(df_mode.loc[3, "kategori"], "B")

        # 2. Ortalama ile doldurma (mean)
        df_mean = clean_missing_data(df, action="mean")
        self.assertAlmostEqual(df_mean.loc[3, "sayi"], 50.0 / 3.0)

        # 3. Sıfır ile doldurma (zero)
        df_zero = clean_missing_data(df, action="zero")
        self.assertEqual(df_zero.loc[3, "sayi"], 0.0)

        # 4. Satır silme (drop)
        df_drop = clean_missing_data(df, action="drop")
        self.assertEqual(len(df_drop), 3)

        # 5. Mükerrer satır silme (drop_duplicates)
        df_dup = pd.DataFrame({"x": [1, 1, 2], "y": ["a", "a", "b"]})
        df_dedup = clean_missing_data(df_dup, action="drop_duplicates")
        self.assertEqual(len(df_dedup), 2)

    def test_advanced_imputer_edge_cases(self):
        """1 satırlık veride KNN, tümü NaN olan sütunda MICE ve yalnızca kategorik sütun"""
        # A. 1 satırlık veride KNN (n_samples <= n_neighbors çökme testi)
        df_single = pd.DataFrame({"a": [np.nan], "b": [10.0]})
        res_knn, rep_knn = impute_missing_advanced(df_single, method="knn", n_neighbors=5)
        self.assertTrue(rep_knn.get("success", False))
        self.assertFalse(pd.isna(res_knn.loc[0, "a"]))

        # B. Tümü NaN olan sütunla MICE (IterativeImputer sütun atlama çökme testi)
        df_all_nan = pd.DataFrame({"a": [np.nan, np.nan, np.nan], "b": [1.0, 2.0, 3.0]})
        res_mice, rep_mice = impute_missing_advanced(df_all_nan, method="mice")
        self.assertTrue(rep_mice.get("success", False))
        self.assertFalse(res_mice["a"].isna().any())

        # C. Yalnızca kategorik sütun seçimi
        df_cat = pd.DataFrame({"sehir": ["Ankara", None, "Ankara"]})
        res_cat, rep_cat = impute_missing_advanced(df_cat, method="mice", target_columns=["sehir"])
        self.assertTrue(rep_cat.get("success", False))
        self.assertEqual(res_cat.loc[1, "sehir"], "Ankara")

    def test_text_clustering_and_merging(self):
        """OpenRefine parmak izi kümeleme ve kanonik birleştirme"""
        df = pd.DataFrame({
            "sehir": ["İstanbul", "istanbul", "İSTANBUL", None, "Ankara", "ankara", "İzmir"]
        })

        # Küme tespiti (Türkçe karakter duyarlı)
        clusters = find_clusters(df, "sehir", method="fingerprint")
        self.assertTrue(len(clusters) >= 2)
        istanbul_cluster = next((c for c in clusters if "istanbul" in c["key"]), None)
        self.assertIsNotNone(istanbul_cluster)
        self.assertEqual(istanbul_cluster["variant_count"], 3)

        # Kanonik birleştirme
        merges = [{"canonical": "İstanbul", "variants": ["istanbul", "İSTANBUL"]}]
        healed_df, modified_count = apply_cluster_merges(df, "sehir", merges)
        self.assertEqual(modified_count, 2)
        # NaN değerin string 'nan' olarak bozulmadığını doğrula
        self.assertTrue(pd.isna(healed_df.loc[3, "sehir"]))
        self.assertEqual(healed_df.loc[0, "sehir"], "İstanbul")
        self.assertEqual(healed_df.loc[1, "sehir"], "İstanbul")
        self.assertEqual(healed_df.loc[2, "sehir"], "İstanbul")


class TestMergingAndFormulaEngine(unittest.TestCase):
    """3. Tablo Birleştirme, Fast Fuzzy Join ve Formül Motoru Testleri"""

    def test_fast_fuzzy_join_type_mismatch_and_turkish(self):
        """Tür uyuşmazlığı (str vs int), Türkçe karakterler ve boş veri setleri"""
        # A. Boş DataFrame
        df1_empty = pd.DataFrame({"k1": []})
        df2_empty = pd.DataFrame({"k2": []})
        m_empty, r_empty = fast_fuzzy_merge(df1_empty, df2_empty, "k1", "k2")
        self.assertTrue(r_empty.get("success", False))

        # B. Tür uyuşmazlığı (str vs int)
        df1_str = pd.DataFrame({"kod": ["101", "202"]})
        df2_int = pd.DataFrame({"kod": [101, 202], "fiyat": [50.0, 75.0]})
        m_type, r_type = fast_fuzzy_merge(df1_str, df2_int, "kod", "kod")
        self.assertTrue(r_type.get("success", False))
        self.assertEqual(r_type.get("matched_unique_keys"), 2)
        self.assertEqual(len(m_type), 2)

        # C. Türkçe harf duyarlılığı ('İstanbul' vs 'istanbul')
        df1_tr = pd.DataFrame({"sehir": ["İstanbul"], "puan": [100]})
        df2_tr = pd.DataFrame({"hedef": ["istanbul"], "katsayi": [1.5]})
        m_tr, r_tr = fast_fuzzy_merge(df1_tr, df2_tr, "sehir", "hedef", threshold=0.7)
        self.assertTrue(r_tr.get("success", False))
        self.assertEqual(r_tr.get("matched_unique_keys"), 1)
        self.assertEqual(m_tr.loc[0, "katsayi"], 1.5)

    def test_calculated_column_math_operations(self):
        """Formül motoru: Dört işlem, sıfıra bölme güvenliği, modulo ve üs alma"""
        from app import app
        client = app.test_client()

        df = pd.DataFrame({
            "a": [10.0, 20.0, 0.0],
            "b": [2.0, 0.0, 5.0]
        })
        set_df(df, 1)

        # 1. Sıfıra bölme (a / b -> sıfıra bölünen satır 0.0 olmalı, çökmemeli)
        res_div = client.post("/create_calculated_column", json={
            "new_col_name": "bolum",
            "col1": "a",
            "op": "/",
            "col2": "b"
        })
        self.assertEqual(res_div.status_code, 200)
        updated_df = get_df(1)
        self.assertEqual(updated_df.loc[0, "bolum"], 5.0)
        self.assertEqual(updated_df.loc[1, "bolum"], 0.0) # 20 / 0 -> 0.0 güvenli koruma

        # 2. Modulo işlemi (a % 3 sabit sayı)
        res_mod = client.post("/add_calculated_column", json={
            "new_col_name": "kalan",
            "col1": "a",
            "op": "%",
            "scalar": 3
        })
        self.assertEqual(res_mod.status_code, 200)
        updated_df = get_df(1)
        self.assertEqual(updated_df.loc[0, "kalan"], 1.0) # 10 % 3 = 1.0
        self.assertEqual(updated_df.loc[1, "kalan"], 2.0) # 20 % 3 = 2.0

        # 3. Üs alma işlemi (b ^ 2)
        res_pow = client.post("/create_calculated_column", json={
            "new_col_name": "kare",
            "col1": "b",
            "op": "^",
            "scalar": 2
        })
        self.assertEqual(res_pow.status_code, 200)
        updated_df = get_df(1)
        self.assertEqual(updated_df.loc[0, "kare"], 4.0)

    def test_preview_second_file_empty_guard(self):
        """preview_second_file rotasında boş dosya koruması"""
        from app import app
        client = app.test_client()

        # 1. Tabloyu hazırla
        set_df(pd.DataFrame({"id": [1, 2]}), 1)

        # Boş dosya gönder
        empty_data = {"file2": (io.BytesIO(b""), "empty.csv")}
        res = client.post("/preview_second_file", data=empty_data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 400)
        self.assertIn("boş", res.get_json().get("error", "").lower())

    def test_switch_sheet_api(self):
        """switch_sheet rotasında sayfa değiştirme ve doğrulama"""
        from app import app
        client = app.test_client()

        sheets = {
            "Sayfa1": pd.DataFrame({"id": [1, 2], "val": [10, 20]}),
            "Sayfa2": pd.DataFrame({"id": [3, 4], "val": [30, 40]}),
        }
        set_excel_data(sheets, ["Sayfa1", "Sayfa2"])
        set_df(sheets["Sayfa1"], 1)

        # Geçerli sayfa geçişi
        res = client.post("/switch_sheet", json={"sheet_name": "Sayfa2"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json().get("active_sheet"), "Sayfa2")
        df_active = get_df(1)
        self.assertEqual(len(df_active), 2)
        self.assertEqual(df_active.loc[0, "id"], 3)

        # Geçersiz sayfa adı
        res_invalid = client.post("/switch_sheet", json={"sheet_name": "OlmayanSayfa"})
        self.assertEqual(res_invalid.status_code, 400)
        self.assertIn("geçersiz", res_invalid.get_json().get("error", "").lower())

    def test_merge_datasets_api(self):
        """merge_datasets rotasında çakışan sütunlar ve tür dönüşümü ile birleştirme"""
        from app import app
        client = app.test_client()

        df1 = pd.DataFrame({"musteri_id": ["101", "102"], "tutar": [500, 1000], "sehir": ["Ankara", "İzmir"]})
        df2 = pd.DataFrame({"id": [101, 102], "puan": [85, 90], "sehir": ["Ankara_Merkez", "İzmir_Konak"]})
        set_df(df1, 1)
        set_df(df2, 2)

        res = client.post("/merge_datasets", json={
            "key1": "musteri_id",
            "key2": "id",
            "join_type": "left"
        })
        self.assertEqual(res.status_code, 200)
        merged = get_df(1)
        self.assertIn("puan", merged.columns)
        self.assertIn("sehir_2", merged.columns) # İsim çakışması önlendi
        self.assertEqual(len(merged), 2)

    def test_clean_data_api_modes(self):
        """clean_data uç noktasında mod ve MICE/KNN algoritmaları"""
        from app import app
        client = app.test_client()

        df = pd.DataFrame({
            "sayi": [10.0, 20.0, 20.0, np.nan],
            "kategori": ["X", "Y", "Y", None]
        })
        set_df(df, 1)

        res_mode = client.post("/clean_data", json={"action": "mode"})
        self.assertEqual(res_mode.status_code, 200)
        res_df = get_df(1)
        self.assertEqual(res_df["sayi"].isna().sum(), 0)

    def test_fast_fuzzy_join_api(self):
        """fast_fuzzy_join uç noktası API testi"""
        from app import app
        client = app.test_client()

        df1 = pd.DataFrame({"il": ["İstanbul", "Ankara"], "satis": [1000, 800]})
        df2 = pd.DataFrame({"sehir": ["istanbul", "ankara"], "hedef": [1200, 900]})
        set_df(df1, 1)
        set_df(df2, 2)

        res = client.post("/fast_fuzzy_join", json={
            "key1": "il",
            "key2": "sehir",
            "threshold": 0.75,
            "how": "left"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("new_row_count"), 2)

    def test_text_clusters_api(self):
        """find_text_clusters ve merge_text_clusters uç noktaları API testi"""
        from app import app
        client = app.test_client()

        df = pd.DataFrame({"urun": ["Laptop", "laptop", "LAPTOP", "Mouse", "mouse"]})
        set_df(df, 1)

        # 1. Kümeleri bul
        res_find = client.post("/find_text_clusters", json={"column": "urun", "method": "fingerprint"})
        self.assertEqual(res_find.status_code, 200)
        clusters = res_find.get_json().get("clusters")
        self.assertTrue(len(clusters) >= 1)

        # 2. Birleştir
        res_merge = client.post("/merge_text_clusters", json={
            "column": "urun",
            "merges": [{"canonical": "Laptop", "variants": ["laptop", "LAPTOP"]}]
        })
        self.assertEqual(res_merge.status_code, 200)
        updated_df = get_df(1)
        laptop_count = (updated_df["urun"] == "Laptop").sum()
        self.assertEqual(laptop_count, 3)


if __name__ == "__main__":
    unittest.main()
