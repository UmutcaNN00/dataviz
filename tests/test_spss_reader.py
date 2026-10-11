import unittest
import io
import os
import sys
import tempfile
import pandas as pd
import numpy as np

# Proje dizinini ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pyreadstat
from app import create_app
from services.file_service import read_spss_safely

class TestSPSSReader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

        # Örnek anket DataFrame'i
        cls.sample_df = pd.DataFrame({
            "yas": [22.0, 35.0, 48.0, 29.0, 61.0, 40.0],
            "cinsiyet": [1.0, 2.0, 1.0, 2.0, 1.0, 2.0],
            "gelir": [18000.0, 32000.0, 55000.0, 27000.0, 70000.0, 42000.0],
            "egitim": [2.0, 3.0, 4.0, 3.0, 1.0, 3.0],
            "memnuniyet": [4.0, 5.0, 2.0, 4.0, 5.0, 3.0]
        })

        cls.col_labels = {
            "yas": "Katılımcı Yaşı",
            "cinsiyet": "Cinsiyet",
            "gelir": "Aylık Hane Geliri (TL)",
            "egitim": "Mezun Olunan Okul",
            "memnuniyet": "Hizmet Memnuniyet Puanı (1-5)"
        }

        cls.val_labels = {
            "cinsiyet": {1: "Kadın", 2: "Erkek"},
            "egitim": {1: "İlkokul", 2: "Lise", 3: "Lisans", 4: "Lisansüstü"},
            "memnuniyet": {1: "Hiç Memnun Değil", 2: "Memnun Değil", 3: "Kararsız", 4: "Memnun", 5: "Çok Memnun"}
        }

        cls.temp_dir = tempfile.mkdtemp()
        cls.sav_path = os.path.join(cls.temp_dir, "anket_verisi.sav")
        pyreadstat.write_sav(
            cls.sample_df,
            cls.sav_path,
            column_labels=cls.col_labels,
            variable_value_labels=cls.val_labels
        )

    def test_direct_read_spss_safely(self):
        """read_spss_safely fonksiyonu doğru okuma ve dönüştürme yapıyor mu?"""
        df = read_spss_safely(self.sav_path)
        self.assertEqual(len(df), 6)
        
        # Soru etiketleri sütun adı oldu mu?
        self.assertIn("Cinsiyet", df.columns)
        self.assertIn("Aylık Hane Geliri (TL)", df.columns)
        
        # Değer etiketleri uygulandı mı?
        cinsiyetler = set(df["Cinsiyet"].dropna().unique())
        self.assertTrue("Kadın" in cinsiyetler and "Erkek" in cinsiyetler)
        
        # Likert ölçeği sayısal olarak korundu mu? (ANOVA/regresyon için kritik)
        memnuniyet_col = [c for c in df.columns if "Memnuniyet" in c][0]
        self.assertTrue(pd.api.types.is_numeric_dtype(df[memnuniyet_col]))

    def test_upload_route_with_spss(self):
        """Flask /upload rotası .sav dosyasını kabul edip başarıyla işliyor mu?"""
        with open(self.sav_path, "rb") as f:
            data = {
                "file": (io.BytesIO(f.read()), "anket_verisi.sav")
            }
            resp = self.client.post("/upload", data=data, content_type="multipart/form-data")
        
        self.assertEqual(resp.status_code, 200)
        res = resp.get_json()
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("total_rows"), 6)
        self.assertGreaterEqual(len(res.get("numeric_columns", [])), 2)

    def test_preview_second_file_with_spss(self):
        """Flask /preview_second_file rotası 2. dosya olarak .sav kabul ediyor mu?"""
        # Önce 1. dosyayı yükle
        with open(self.sav_path, "rb") as f:
            data = {"file": (io.BytesIO(f.read()), "anket_verisi.sav")}
            self.client.post("/upload", data=data, content_type="multipart/form-data")

        # 2. dosya olarak da .sav yükle
        with open(self.sav_path, "rb") as f:
            data2 = {"file2": (io.BytesIO(f.read()), "ikinci_anket.sav")}
            resp2 = self.client.post("/preview_second_file", data=data2, content_type="multipart/form-data")

        self.assertEqual(resp2.status_code, 200)
        res2 = resp2.get_json()
        self.assertTrue(res2.get("success"))
        self.assertEqual(res2.get("file2_rows"), 6)

    def test_empty_spss_error_handling(self):
        """Tamamen boş veya geçersiz dosya yüklendiğinde zarif hata dönüyor mu?"""
        empty_stream = io.BytesIO(b"")
        data = {"file": (empty_stream, "bos.sav")}
        resp = self.client.post("/upload", data=data, content_type="multipart/form-data")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.get_json())

if __name__ == "__main__":
    unittest.main()
