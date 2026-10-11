"""
Clustering Service - OpenRefine-Style Key Collision and Text Clustering
Features:
1. Fingerprint (Token sort + ASCII folding + Punctuation removal)
2. N-Gram Fingerprint (Character n-gram deduplication)
3. Phonetic / Soundex Keying
4. Fast vectorized cluster detection and batch canonical merging
"""

import logging
import re
import unicodedata
from collections import defaultdict
from typing import Any, Optional, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Turkish character mapping for ASCII folding
TR_CHAR_MAP = str.maketrans({
    "ç": "c", "Ç": "c",
    "ğ": "g", "Ğ": "g",
    "ı": "i", "I": "i", "İ": "i", "i": "i",
    "ö": "o", "Ö": "o",
    "ş": "s", "Ş": "s",
    "ü": "u", "Ü": "u",
})


def normalize_ascii(text: str) -> str:
    """Folds Unicode and Turkish accented characters into ASCII counterparts."""
    if not text:
        return ""
    folded = text.translate(TR_CHAR_MAP)
    normalized = unicodedata.normalize("NFKD", folded)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def fingerprint(text: str) -> str:
    """
    OpenRefine-style Fingerprint:
    1. Strip leading/trailing whitespace
    2. Lowercase
    3. Fold accents/Turkish characters to ASCII
    4. Remove punctuation and special characters
    5. Tokenize into words by whitespace
    6. Sort tokens alphabetically and deduplicate
    7. Join tokens with a single space
    """
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    s = text.strip().lower()
    if not s:
        return ""
    s = normalize_ascii(s)
    # Remove punctuation
    s = re.sub(r"[^\w\s]", "", s)
    tokens = sorted(list(set(s.split())))
    return " ".join(tokens)


def ngram_fingerprint(text: str, n: int = 2) -> str:
    """
    OpenRefine-style N-Gram Fingerprint:
    Splits normalized string into character n-grams, deduplicates, sorts, and joins.
    """
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    s = text.strip().lower()
    if not s:
        return ""
    s = normalize_ascii(s)
    s = re.sub(r"[\s\W_]+", "", s)
    if len(s) < n:
        return s
    ngrams = sorted(list(set(s[i:i + n] for i in range(len(s) - n + 1))))
    return "".join(ngrams)


def phonetic_soundex(text: str) -> str:
    """
    Soundex Phonetic key generator for clustering auditory similarities.
    """
    if not text:
        return ""
    s = normalize_ascii(text.strip().upper())
    s = re.sub(r"[^A-Z]", "", s)
    if not s:
        return ""

    first_char = s[0]
    mapping = {
        "B": "1", "F": "1", "P": "1", "V": "1",
        "C": "2", "G": "2", "J": "2", "K": "2", "Q": "2", "S": "2", "X": "2", "Z": "2",
        "D": "3", "T": "3",
        "L": "4",
        "M": "5", "N": "5",
        "R": "6",
    }
    encoded = [first_char]
    prev_code = mapping.get(first_char, "")

    for char in s[1:]:
        code = mapping.get(char, "0")
        if code != "0" and code != prev_code:
            encoded.append(code)
            prev_code = code
        elif code == "0":
            prev_code = ""
        if len(encoded) == 4:
            break

    while len(encoded) < 4:
        encoded.append("0")
    return "".join(encoded)


def find_clusters(
    df: pd.DataFrame,
    col_name: str,
    method: str = "fingerprint",
    max_clusters: int = 50,
) -> list[dict[str, Any]]:
    """
    Identifies text clusters with multiple distinct variants that share the same key.
    """
    if col_name not in df.columns:
        raise ValueError(f"Sütun bulunamadı: {col_name}")

    series = df[col_name].dropna().astype(str)
    if len(series) == 0:
        return []

    # Choose key generator
    if method == "ngram":
        key_fn = lambda s: ngram_fingerprint(s, 2)
    elif method == "soundex":
        key_fn = phonetic_soundex
    else:
        key_fn = fingerprint

    # Value counts: { original_value: count }
    val_counts = series.value_counts()

    # Bucket into key -> { original_val: count }
    buckets = defaultdict(lambda: defaultdict(int))
    for val, count in val_counts.items():
        key = key_fn(val)
        if key:
            buckets[key][val] += int(count)

    clusters = []
    for key, variants_dict in buckets.items():
        # Only interested if there are 2 or more distinct string variants
        if len(variants_dict) > 1:
            # Sort variants by frequency descending
            sorted_variants = sorted(variants_dict.items(), key=lambda x: x[1], reverse=True)
            total_rows = sum(variants_dict.values())
            canonical_choice = sorted_variants[0][0]  # Most frequent variant

            clusters.append({
                "key": key,
                "total_rows": total_rows,
                "variant_count": len(variants_dict),
                "suggested_canonical": canonical_choice,
                "variants": [{"val": v, "count": c} for v, c in sorted_variants],
            })

    # Sort clusters by total impacted rows descending
    clusters.sort(key=lambda x: x["total_rows"], reverse=True)
    return clusters[:max_clusters]


def apply_cluster_merges(
    df: pd.DataFrame,
    col_name: str,
    merges: list[dict[str, Any]],
) -> Tuple[pd.DataFrame, int]:
    """
    Vectorized replacement of string variants with canonical values.
    merges: [ { "canonical": "Ankara", "variants": ["ankara", "ANKARA ", "Ank ra"] }, ... ]
    """
    if col_name not in df.columns:
        raise ValueError(f"Sütun bulunamadı: {col_name}")

    replacement_map = {}
    for item in merges:
        canonical = item.get("canonical", "").strip()
        variants = item.get("variants", [])
        if canonical and variants:
            for v in variants:
                if v != canonical:
                    replacement_map[v] = canonical

    if not replacement_map:
        return df, 0

    healed_df = df.copy()
    orig_s = healed_df[col_name]
    null_mask = orig_s.isna()

    if isinstance(orig_s.dtype, pd.CategoricalDtype):
        needed_cats = [c for c in set(replacement_map.values()) if c not in orig_s.cat.categories]
        if needed_cats:
            orig_s = orig_s.cat.add_categories(needed_cats)
        healed_s = orig_s.replace(replacement_map)
    else:
        str_s = orig_s.astype(str)
        healed_s = str_s.replace(replacement_map)
        if null_mask.any():
            healed_s = healed_s.where(~null_mask, np.nan)

    healed_df[col_name] = healed_s
    modified_rows = int(df[col_name].astype(str).isin(list(replacement_map.keys())).sum())

    logger.info(f"Clustering merge applied on '{col_name}': {len(replacement_map)} varyasyon -> {modified_rows} satır güncellendi.")
    return healed_df, modified_rows
