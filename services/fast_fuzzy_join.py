"""
DataViz - Hızlı Bulanık Birleştirme (Fast Fuzzy Join & Blocking) Servisi
N-Gram Ters Dizin (Inverted Index Blocking) ve Jaro-Winkler/Levenshtein benzerliği ile
O(N x M) kartezyen çarpımı O(N) seviyesine indirerek binlerce satırı milisaniyelerde eşleştirir.
"""

from typing import Tuple, Dict, Any, List
import time
from collections import defaultdict
import difflib
import unicodedata
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Türkçe karakter eşlemesi ve katlama (folding)
TR_CHAR_MAP = str.maketrans({
    "ç": "c", "Ç": "c",
    "ğ": "g", "Ğ": "g",
    "ı": "i", "I": "i", "İ": "i", "i": "i",
    "ö": "o", "Ö": "o",
    "ş": "s", "Ş": "s",
    "ü": "u", "Ü": "u",
})


def _normalize_fuzzy_text(text: Any) -> str:
    """Türkçe ve aksanlı karakterleri normalleştirerek karşılaştırmaya hazırlar."""
    if text is None or pd.isna(text):
        return ""
    s = str(text).strip()
    s = s.translate(TR_CHAR_MAP)
    normalized = unicodedata.normalize("NFKD", s)
    ascii_clean = "".join(c for c in normalized if not unicodedata.combining(c))
    return ascii_clean.lower().strip()


def _extract_ngrams(text: str, n: int = 3) -> set:
    """Metinden n-gram kümesi çıkarır."""
    norm = _normalize_fuzzy_text(text)
    if not norm:
        return set()
    s = f"  {norm}  "
    if len(s) < n:
        return {s}
    return {s[i : i + n] for i in range(len(s) - n + 1)}


def fast_fuzzy_merge(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    key1: str,
    key2: str,
    threshold: float = 0.70,
    how: str = "inner",
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    İki DataFrame'i ters dizin bloklaması (Inverted Index Blocking) kullanarak
    yüksek hızda bulanık (fuzzy) eşleştirir.
    
    Args:
        df1: 1. DataFrame
        df2: 2. DataFrame
        key1: 1. DataFrame'deki eşleştirme sütunu
        key2: 2. DataFrame'deki eşleştirme sütunu
        threshold: Minimum benzerlik oranı (0.0 - 1.0, varsayılan: 0.70)
        how: 'inner', 'left'
        
    Returns:
        (merged_df, metrics_report)
    """
    start_time = time.time()

    if df1 is None or df2 is None or key1 not in df1.columns or key2 not in df2.columns:
        return pd.DataFrame(), {"error": "Geçersiz DataFrame veya sütun adı"}

    # Boş DataFrame kontrolü
    if df1.empty or df2.empty:
        empty_merged = pd.DataFrame(columns=list(df1.columns) + [c for c in df2.columns if c != key2])
        return empty_merged, {
            "success": True,
            "elapsed_ms": 0.0,
            "matched_unique_keys": 0,
            "total_merged_rows": 0,
            "theoretical_comparisons": 0,
            "actual_evaluated_comparisons": 0,
            "computation_reduction_pct": 100.0,
            "sample_matches": [],
            "message": "Birleştirilecek tablolardan biri veya her ikisi boş.",
        }

    valid_how = "left" if str(how).lower().strip() == "left" else "inner"

    # Benzersiz anahtarları normalize edilmiş halleriyle al
    s1_non_null = df1[key1].dropna()
    s2_non_null = df2[key2].dropna()

    vals1 = s1_non_null.astype(str).unique().tolist()
    vals2 = s2_non_null.astype(str).unique().tolist()

    if not vals1 or not vals2:
        empty_merged = pd.DataFrame(columns=list(df1.columns) + [c for c in df2.columns if c != key2])
        return empty_merged, {
            "success": True,
            "elapsed_ms": 0.0,
            "matched_unique_keys": 0,
            "total_merged_rows": 0,
            "theoretical_comparisons": 0,
            "actual_evaluated_comparisons": 0,
            "computation_reduction_pct": 100.0,
            "sample_matches": [],
            "message": "Eşleştirme sütunlarında geçerli değer bulunamadı.",
        }

    # 1. 2. Tablo için N-Gram Ters Dizin (Inverted Index) Oluştur
    index_df2 = defaultdict(list)
    val2_ngrams = {}
    val2_normalized = {}

    for idx2, v2 in enumerate(vals2):
        norm2 = _normalize_fuzzy_text(v2)
        val2_normalized[idx2] = norm2
        ngs = _extract_ngrams(norm2, n=3)
        val2_ngrams[idx2] = ngs
        for ng in ngs:
            index_df2[ng].append(idx2)

    # 2. Aday Çiftleri Hızlı Filtrele (Blocking)
    matches_map = {}  # v1 (str) -> (best_v2_str, score)
    total_candidates_evaluated = 0
    total_theoretical_pairs = len(vals1) * len(vals2)

    for v1 in vals1:
        norm1 = _normalize_fuzzy_text(v1)
        ng1 = _extract_ngrams(norm1, n=3)

        # Sadece ortak n-gram paylaşan v2 indekslerini topla
        candidate_indices = set()
        for ng in ng1:
            if ng in index_df2:
                candidate_indices.update(index_df2[ng])

        total_candidates_evaluated += len(candidate_indices)

        # Adaylar arasında en yüksek benzerliği bul
        best_v2 = None
        best_score = 0.0

        for idx2 in candidate_indices:
            v2 = vals2[idx2]
            norm2 = val2_normalized[idx2]

            # Birebir normalizasyon eşitliği
            if norm1 == norm2 and norm1 != "":
                best_score = 1.0
                best_v2 = v2
                break

            # Hızlı Jaccard n-gram ön eleme
            intersection = len(ng1 & val2_ngrams[idx2])
            union = len(ng1 | val2_ngrams[idx2])
            jaccard = intersection / max(1, union)

            if jaccard >= (threshold * 0.4):
                # Detaylı SequenceMatcher benzerliği (normalize metinler üzerinde)
                score = difflib.SequenceMatcher(None, norm1, norm2).ratio()
                if score > best_score:
                    best_score = score
                    best_v2 = v2

        if best_v2 is not None and best_score >= threshold:
            matches_map[v1] = (best_v2, round(best_score, 3))

    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    # 3. Güvenli DataFrame Birleştirme (Tür Uyuşmazlığı Koruması)
    df1_mapped = df1.copy(deep=False)
    df2_mapped = df2.copy(deep=False)

    # Her iki tarafta da eşleşecek string anahtar kolonları oluştur
    df1_s = df1_mapped[key1].astype(str).where(df1_mapped[key1].notna(), other=None)
    df1_mapped["_fuzzy_join_key_"] = df1_s.map(
        lambda x: matches_map[x][0] if x is not None and x in matches_map else None
    )
    df1_mapped["_fuzzy_score"] = df1_s.map(
        lambda x: matches_map[x][1] if x is not None and x in matches_map else 0.0
    )

    df2_mapped = df2_mapped[df2_mapped[key2].notna()].copy()
    df2_mapped["_fuzzy_join_key_"] = df2_mapped[key2].astype(str)

    # İsim çakışması önleme
    cols_to_keep_right = [c for c in df2_mapped.columns if c != key2]

    merged_df = pd.merge(
        df1_mapped,
        df2_mapped[cols_to_keep_right],
        on="_fuzzy_join_key_",
        how=valid_how,
        suffixes=("_dosya1", "_dosya2"),
    )

    # Geçici birleştirme anahtarını temizle
    if "_fuzzy_join_key_" in merged_df.columns:
        merged_df.drop(columns=["_fuzzy_join_key_"], inplace=True)

    reduction_ratio = (
        (1.0 - (total_candidates_evaluated / max(1, total_theoretical_pairs))) * 100
        if total_theoretical_pairs > 0
        else 100.0
    )

    metrics = {
        "success": True,
        "elapsed_ms": elapsed_ms,
        "matched_unique_keys": len(matches_map),
        "total_merged_rows": len(merged_df),
        "theoretical_comparisons": total_theoretical_pairs,
        "actual_evaluated_comparisons": total_candidates_evaluated,
        "computation_reduction_pct": round(reduction_ratio, 1),
        "sample_matches": [
            {"kaynak": k, "hedef": v[0], "benzerlik": v[1]}
            for k, v in list(matches_map.items())[:8]
        ],
    }

    logger.info(
        f"Fast Fuzzy Merge tamamlandı: {len(matches_map)} eşleşme, {elapsed_ms}ms "
        f"(Hesaplama %{metrics['computation_reduction_pct']} azaltıldı)"
    )
    return merged_df, metrics
