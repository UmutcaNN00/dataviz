"""
DataViz - 100 Million Row x 22 Column Realistic & Dirty Big Data Generator
Generates a 100,000,000-row Apache Parquet dataset (2.2 billion cells) in streaming 2.5M-row chunks
using PyArrow ZSTD compression and dictionary encoding for low memory overhead.
"""

import gc
import os
import time

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


def generate_100m_dataset(output_dir=None):
    if output_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        parent_sample_dir = os.path.join(
            os.path.dirname(base_dir), "ornek_veri_setleri"
        )
        output_dir = (
            parent_sample_dir if os.path.exists(os.path.dirname(base_dir)) else base_dir
        )

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "100M_Gercekci_Kirli_Veri_Seti_22Sutun.parquet")

    total_rows = 100_000_000
    chunk_size = 2_500_000  # 40 chunks of 2.5M rows -> low RAM footprint (~600 MB peak)
    num_chunks = total_rows // chunk_size

    print(f"Starting generation of {total_rows:,} rows x 22 columns -> {out_path}")
    t0 = time.time()

    rng = np.random.default_rng(20260925)

    # 1. Categorical pools (realistic Turkish e-commerce distribution)
    sehir_bolge_pairs = [
        ("İstanbul", "Marmara"),
        ("Ankara", "İç Anadolu"),
        ("İzmir", "Ege"),
        ("Bursa", "Marmara"),
        ("Antalya", "Akdeniz"),
        ("Adana", "Akdeniz"),
        ("Konya", "İç Anadolu"),
        ("Gaziantep", "Güneydoğu Anadolu"),
        ("Kocaeli", "Marmara"),
        ("Mersin", "Akdeniz"),
        ("Kayseri", "İç Anadolu"),
        ("Eskişehir", "İç Anadolu"),
        ("Diyarbakır", "Güneydoğu Anadolu"),
        ("Samsun", "Karadeniz"),
        ("Denizli", "Ege"),
        ("Şanlıurfa", "Güneydoğu Anadolu"),
        ("Sakarya", "Marmara"),
        ("Trabzon", "Karadeniz"),
        ("Malatya", "Doğu Anadolu"),
        ("Erzurum", "Doğu Anadolu"),
        ("Manisa", "Ege"),
        ("Balıkesir", "Marmara"),
        ("Kahramanmaraş", "Akdeniz"),
        ("Van", "Doğu Anadolu"),
        ("Aydın", "Ege"),
        ("Tekirdağ", "Marmara"),
        ("Muğla", "Ege"),
        ("Hatay", "Akdeniz"),
        ("Ordu", "Karadeniz"),
        ("Sivas", "İç Anadolu"),
    ]
    sehirler = np.array([p[0] for p in sehir_bolge_pairs], dtype=object)
    bolgeler = np.array([p[1] for p in sehir_bolge_pairs], dtype=object)
    sehir_weights = np.array(
        [
            0.18,
            0.09,
            0.07,
            0.05,
            0.045,
            0.035,
            0.035,
            0.035,
            0.035,
            0.03,
            0.025,
            0.025,
            0.025,
            0.025,
            0.025,
            0.02,
            0.02,
            0.02,
            0.02,
            0.018,
            0.018,
            0.018,
            0.016,
            0.015,
            0.015,
            0.015,
            0.015,
            0.015,
            0.012,
            0.013,
        ]
    )
    sehir_weights /= sehir_weights.sum()

    kat_alt_pairs = [
        ("Elektronik", "Akıllı Telefon"),
        ("Elektronik", "Dizüstü Bilgisayar"),
        ("Elektronik", "Tablet & Aksesuar"),
        ("Ev & Yaşam", "Mobilya"),
        ("Ev & Yaşam", "Küçük Ev Aletleri"),
        ("Ev & Yaşam", "Aydınlatma"),
        ("Moda & Giyim", "Dış Giyim"),
        ("Moda & Giyim", "Ayakkabı & Çanta"),
        ("Moda & Giyim", "Spor Giyim"),
        ("Süpermarket & Gıda", "Temel Gıda"),
        ("Süpermarket & Gıda", "Kahve & İçecek"),
        ("Süpermarket & Gıda", "Atıştırmalık"),
        ("Kozmetik & Bakım", "Cilt Bakımı"),
        ("Kozmetik & Bakım", "Parfüm & Deodorant"),
        ("Otomotiv & Yapı", "Oto Aksesuar"),
        ("Otomotiv & Yapı", "El Aletleri & Hırdavat"),
        ("Anne & Bebek", "Bebek Bezi & Bakım"),
        ("Kitap & Kırtasiye", "Akademik Yayınlar"),
    ]
    kategoriler = np.array([p[0] for p in kat_alt_pairs], dtype=object)
    alt_kategoriler = np.array([p[1] for p in kat_alt_pairs], dtype=object)
    kat_base_price = np.array(
        [
            28500.0,
            42000.0,
            9500.0,
            18500.0,
            4800.0,
            1650.0,
            2400.0,
            1950.0,
            1450.0,
            650.0,
            420.0,
            180.0,
            980.0,
            1650.0,
            2200.0,
            3100.0,
            890.0,
            540.0,
        ],
        dtype=np.float32,
    )

    odeme_yontemleri = np.array(
        [
            "Kredi Kartı (Tek Çekim)",
            "Taksitli Kredi Kartı",
            "Havale / EFT",
            "Dijital Cüzdan",
            "Kapıda Ödeme",
            "Kurumsal Açık Hesap",
        ],
        dtype=object,
    )

    musteri_segmentleri = np.array(
        [
            "Bireysel Standart",
            "Bireysel Plus / VIP",
            "KOBİ Ticari",
            "Kurumsal Enterprise",
            "Kamu / Akademik",
        ],
        dtype=object,
    )

    satis_kanallari = np.array(
        [
            "Mobil Uygulama (iOS/Android)",
            "Web Mağaza (Masaüstü)",
            "Pazaryeri Entegrasyonu",
            "Kurumsal B2B Portal",
            "Fiziksel Mağaza (POS)",
        ],
        dtype=object,
    )

    kargo_firmalari = np.array(
        [
            "Yurtiçi Lojistik",
            "Aras Ekspres",
            "MNG Kargo",
            "HepsiJet",
            "Trendyol Express",
            "PTT Kargo",
        ],
        dtype=object,
    )

    # Pre-build rich dirty string pools (200,000 distinct dirty strings each) for fast vectorized sampling
    pool_size = 200_000
    null_tokens = [
        "Yok",
        "Bilinmiyor",
        "Belirtilmemiş",
        "N/A",
        "Boş",
        "-",
        "NULL",
        "Hatalı",
    ]

    # Dirty Pool 1: Kirli_Etiket_Fiyati_TL ("₺14.250,75", "8.420 TL", "$1,250.50", "Yok", etc.)
    p_vals = rng.uniform(50.0, 95000.0, pool_size)
    dirty_fiyat_pool = []
    for i, v in enumerate(p_vals):
        r = i % 20
        if r == 0:
            dirty_fiyat_pool.append(null_tokens[i % len(null_tokens)])
        elif r in (1, 2, 3, 4, 5, 6):
            s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            dirty_fiyat_pool.append(f"₺{s}")
        elif r in (7, 8, 9, 10):
            s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            dirty_fiyat_pool.append(f"{s} TL")
        elif r in (11, 12):
            dirty_fiyat_pool.append(f"${v:,.2f}")
        elif r == 13:
            dirty_fiyat_pool.append(f"€{v:.2f}")
        else:
            dirty_fiyat_pool.append(f"{v:.2f}")
    dirty_fiyat_pool = np.array(dirty_fiyat_pool, dtype=object)

    # Dirty Pool 2: Kirli_Paket_Agirligi_Kg ("12.40kg", "8,50 kg", "4.2 lt", "Yok", etc.)
    w_vals = rng.uniform(0.15, 120.0, pool_size)
    dirty_agirlik_pool = []
    for i, w in enumerate(w_vals):
        r = i % 20
        if r == 0:
            dirty_agirlik_pool.append(null_tokens[i % len(null_tokens)])
        elif r in (1, 2, 3, 4, 5, 6, 7):
            dirty_agirlik_pool.append(f"{w:.2f}kg")
        elif r in (8, 9, 10, 11):
            dirty_agirlik_pool.append(f"{w:.2f}".replace(".", ",") + " kg")
        elif r in (12, 13):
            dirty_agirlik_pool.append(f"{w:.1f} lt")
        else:
            dirty_agirlik_pool.append(f"{w:.2f}")
    dirty_agirlik_pool = np.array(dirty_agirlik_pool, dtype=object)

    # Dirty Pool 3: Kirli_Indirim_Orani ("%18.5", "25,0%", "Yok", etc.)
    d_vals = rng.uniform(1.0, 65.0, pool_size)
    dirty_indirim_pool = []
    for i, d in enumerate(d_vals):
        r = i % 20
        if r == 0:
            dirty_indirim_pool.append(null_tokens[i % len(null_tokens)])
        elif r in (1, 2, 3, 4, 5, 6, 7, 8):
            dirty_indirim_pool.append(f"%{d:.1f}")
        elif r in (9, 10, 11, 12):
            dirty_indirim_pool.append(f"{d:.1f}%".replace(".", ","))
        else:
            dirty_indirim_pool.append(f"{d:.2f}")
    dirty_indirim_pool = np.array(dirty_indirim_pool, dtype=object)

    # Dirty Pool 4: Kirli_Musteri_Yillik_Ciro ("1.250.400", "₺3.450.000,50", "Bilinmiyor", etc.)
    c_vals = rng.integers(10_000, 25_000_000, pool_size)
    dirty_ciro_pool = []
    for i, c in enumerate(c_vals):
        r = i % 20
        if r == 0:
            dirty_ciro_pool.append(null_tokens[i % len(null_tokens)])
        elif r in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10):
            dirty_ciro_pool.append(f"{c:,}".replace(",", "."))
        elif r in (11, 12, 13):
            dirty_ciro_pool.append(f"₺{c:,},50".replace(",", "."))
        else:
            dirty_ciro_pool.append(str(c))
    dirty_ciro_pool = np.array(dirty_ciro_pool, dtype=object)

    # Dirty Pool 5: Kirli_Siparis_Adedi ("12 adet", "5adet", "Yok", etc.)
    q_vals = rng.integers(1, 250, pool_size)
    dirty_adet_pool = []
    for i, q in enumerate(q_vals):
        r = i % 20
        if r == 0:
            dirty_adet_pool.append(null_tokens[i % len(null_tokens)])
        elif r in (1, 2, 3, 4, 5, 6, 7):
            dirty_adet_pool.append(f"{q} adet")
        elif r in (8, 9, 10):
            dirty_adet_pool.append(f"{q}adet")
        else:
            dirty_adet_pool.append(str(q))
    dirty_adet_pool = np.array(dirty_adet_pool, dtype=object)

    writer = None
    base_ts = np.datetime64("2022-01-01T00:00:00", "ms").astype(np.int64)

    for chunk_idx in range(num_chunks):
        c_start = chunk_idx * chunk_size
        c_end = c_start + chunk_size

        # 1. Islem_ID (100% unique: 1 .. 100,000,000)
        islem_id = np.arange(c_start + 1, c_end + 1, dtype=np.int64)

        # 2. Islem_Zamani (Monotonically increasing + jitter -> unique timestamp per row)
        ts_ms = (
            base_ts
            + islem_id * 1250
            + rng.integers(0, 999, size=chunk_size, dtype=np.int64)
        )
        islem_zamani = ts_ms.astype("datetime64[ms]")

        # 3 & 4. Sehir & Bolge
        s_idx = rng.choice(len(sehirler), size=chunk_size, p=sehir_weights)
        col_sehir = sehirler[s_idx]
        col_bolge = bolgeler[s_idx]

        # 5 & 6. Urun_Kategorisi & Alt_Kategori
        k_idx = rng.integers(0, len(kategoriler), size=chunk_size)
        col_kategori = kategoriler[k_idx]
        col_alt_kategori = alt_kategoriler[k_idx]

        # 7, 8, 9, 10. Odeme_Yontemi, Musteri_Segmenti, Satis_Kanali, Kargo_Firmasi
        col_odeme = odeme_yontemleri[
            rng.integers(0, len(odeme_yontemleri), size=chunk_size)
        ]
        seg_idx = rng.integers(0, len(musteri_segmentleri), size=chunk_size)
        col_segment = musteri_segmentleri[seg_idx]
        col_kanal = satis_kanallari[
            rng.integers(0, len(satis_kanallari), size=chunk_size)
        ]
        col_kargo = kargo_firmalari[
            rng.integers(0, len(kargo_firmalari), size=chunk_size)
        ]

        # 11. Satis_Tutari (Continuous float32 with realistic category + segment effect + NaNs + Outliers)
        base_p = kat_base_price[k_idx] * (1.0 + 0.15 * seg_idx)
        satis_tutari = (
            base_p * rng.lognormal(mean=0.0, sigma=0.35, size=chunk_size)
        ).astype(np.float32)
        nan_mask_1 = rng.random(chunk_size) < 0.02
        outlier_mask_1 = rng.random(chunk_size) < 0.003
        satis_tutari[outlier_mask_1] *= 12.5
        satis_tutari[nan_mask_1] = np.nan

        # 12. Birim_Maliyet (Strongly correlated with Satis_Tutari: r ~ 0.88)
        birim_maliyet = (
            satis_tutari * rng.uniform(0.52, 0.78, size=chunk_size)
            + rng.normal(0, 120, size=chunk_size)
        ).astype(np.float32)
        birim_maliyet[rng.random(chunk_size) < 0.015] = np.nan

        # 13. Kargo_Ucreti (float32 with NaNs)
        kargo_ucreti = rng.uniform(29.90, 450.0, size=chunk_size).astype(np.float32)
        kargo_ucreti[rng.random(chunk_size) < 0.01] = np.nan

        # 14. Net_Kar (Satis_Tutari - Birim_Maliyet - Kargo_Ucreti)
        net_kar = (satis_tutari - birim_maliyet - kargo_ucreti).astype(np.float32)

        # 15. Musteri_Yasi (float32 with 1.5% NaNs + impossible age outliers like -5, 135, 199)
        musteri_yasi = rng.integers(18, 75, size=chunk_size).astype(np.float32)
        musteri_yasi[rng.random(chunk_size) < 0.002] = rng.choice(
            np.array([-5.0, 135.0, 199.0], dtype=np.float32), size=1
        )[0]
        musteri_yasi[rng.random(chunk_size) < 0.015] = np.nan

        # 16. Memnuniyet_Puani (1.00 - 5.00 correlated with segment)
        memnuniyet = np.clip(
            rng.normal(3.85 + 0.12 * seg_idx, 0.65, size=chunk_size), 1.0, 5.0
        ).astype(np.float32)
        memnuniyet[rng.random(chunk_size) < 0.02] = np.nan

        # 17. Oturum_Suresi_Sn (Continuous float32)
        oturum_suresi = rng.exponential(scale=240.0, size=chunk_size).astype(
            np.float32
        ) + np.float32(15.0)

        # 18–22. 5 Dirty String-Encoded Numeric Columns (for Data Healer testing)
        col_kirli_fiyat = dirty_fiyat_pool[rng.integers(0, pool_size, size=chunk_size)]
        col_kirli_agirlik = dirty_agirlik_pool[
            rng.integers(0, pool_size, size=chunk_size)
        ]
        col_kirli_indirim = dirty_indirim_pool[
            rng.integers(0, pool_size, size=chunk_size)
        ]
        col_kirli_ciro = dirty_ciro_pool[rng.integers(0, pool_size, size=chunk_size)]
        col_kirli_adet = dirty_adet_pool[rng.integers(0, pool_size, size=chunk_size)]

        table = pa.table(
            {
                "Islem_ID": pa.array(islem_id),
                "Islem_Zamani": pa.array(islem_zamani),
                "Sehir": pa.array(col_sehir).dictionary_encode(),
                "Bolge": pa.array(col_bolge).dictionary_encode(),
                "Urun_Kategorisi": pa.array(col_kategori).dictionary_encode(),
                "Alt_Kategori": pa.array(col_alt_kategori).dictionary_encode(),
                "Odeme_Yontemi": pa.array(col_odeme).dictionary_encode(),
                "Musteri_Segmenti": pa.array(col_segment).dictionary_encode(),
                "Satis_Kanali": pa.array(col_kanal).dictionary_encode(),
                "Kargo_Firmasi": pa.array(col_kargo).dictionary_encode(),
                "Satis_Tutari": pa.array(satis_tutari),
                "Birim_Maliyet": pa.array(birim_maliyet),
                "Kargo_Ucreti": pa.array(kargo_ucreti),
                "Net_Kar": pa.array(net_kar),
                "Musteri_Yasi": pa.array(musteri_yasi),
                "Memnuniyet_Puani": pa.array(memnuniyet),
                "Oturum_Suresi_Sn": pa.array(oturum_suresi),
                "Kirli_Etiket_Fiyati_TL": pa.array(col_kirli_fiyat).dictionary_encode(),
                "Kirli_Paket_Agirligi_Kg": pa.array(
                    col_kirli_agirlik
                ).dictionary_encode(),
                "Kirli_Indirim_Orani": pa.array(col_kirli_indirim).dictionary_encode(),
                "Kirli_Musteri_Yillik_Ciro": pa.array(
                    col_kirli_ciro
                ).dictionary_encode(),
                "Kirli_Siparis_Adedi": pa.array(col_kirli_adet).dictionary_encode(),
            }
        )

        if writer is None:
            writer = pq.ParquetWriter(
                out_path, table.schema, compression="zstd", compression_level=3
            )
        writer.write_table(table)

        del (
            table,
            islem_id,
            islem_zamani,
            satis_tutari,
            birim_maliyet,
            kargo_ucreti,
            net_kar,
        )
        if (chunk_idx + 1) % 5 == 0 or chunk_idx == 0:
            elapsed = time.time() - t0
            rows_done = (chunk_idx + 1) * chunk_size
            print(
                f"[{chunk_idx + 1:02d}/{num_chunks}] Wrote {rows_done:,} rows ({elapsed:.1f}s elapsed)"
            )
            gc.collect()

    if writer is not None:
        writer.close()

    total_time = time.time() - t0
    size_gb = os.path.getsize(out_path) / (1024**3)
    print(
        f"DONE! Generated {total_rows:,} rows x 22 columns in {total_time:.1f}s -> {out_path} ({size_gb:.2f} GB)"
    )


if __name__ == "__main__":
    generate_100m_dataset()
