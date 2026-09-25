---
name: massive-dataset-optimization
description: >-
  1 milyon satırdan büyük veri setleriyle çalışırken, bellek optimizasyonu veya
  performans iyileştirmesi yapılırken bu skill kullanılır. PyArrow zero-copy okuma,
  kategorik sütun optimizasyonu ve büyük veri stratejilerini içerir.
---

# Büyük Veri Seti Optimizasyonu (1M+ Satır)

## PyArrow Zero-Copy Parquet Okuma

En verimli Parquet okuma yöntemi — 100M × 22 sütun = **62.5 saniye, 6.35 GB RAM**:

```python
import pyarrow.parquet as pq

table = pq.read_table(source, use_threads=True)
df = table.to_pandas(split_blocks=True, self_destruct=True)
del table  # Arrow tablosunu hemen serbest bırak
```

- `split_blocks=True`: Her sütun bağımsız NumPy array olur, tek büyük blok yerine
- `self_destruct=True`: Pandas dönüşümü sırasında Arrow belleğini anında serbest bırakır
- `use_threads=True`: Çoklu thread ile paralel sütun okuma

## Kategorik Sütun Optimizasyonu (~1000x Hız Artışı)

`.apply()` yerine unique category parse + NumPy array indexing:

```python
def _parse_series_fast(series):
    if hasattr(series.dtype, 'categories'):
        # Sadece unique kategorileri parse et (~200K), 100M satırı değil
        cats = series.cat.categories
        parsed_cats = pd.to_numeric(cats, errors='coerce')
        # Codes üzerinden NumPy array indexing ile map et
        codes = series.cat.codes.values
        result = parsed_cats.values[codes]
        return pd.Series(result, index=series.index, dtype='float32')
    return pd.to_numeric(series, errors='coerce')
```

## Massive Dataset Kuralları

### Bellek Yönetimi
- **Shallow copy:** 1M+ satırlık DataFrame'lerde `df.copy(deep=False)` kullan, deep copy yerine
- **float32 çıktı:** Massive veri setlerinde `float64` yerine `float32` kullan (%50 bellek tasarrufu)
- **Sütun-sütun fillna:** Tam DataFrame `.fillna()` yerine her sütunu tek tek doldur

### Sağlık Kontrolü
- 500K+ satırlık veri setlerinde `missing_rows` hesaplaması için **50K satırlık örnekleme** kullan
- Tam 2D boolean matris oluşturmak bellek patlamasına neden olabilir

### Kategorik fillna
```python
if hasattr(col.dtype, 'categories'):
    if 'Bilinmiyor' not in col.cat.categories:
        col = col.cat.add_categories(['Bilinmiyor'])
    col = col.fillna('Bilinmiyor')
```

## Parquet Yazma Optimizasyonu

```python
df.to_parquet(
    path,
    engine='pyarrow',
    compression='zstd',           # En iyi sıkıştırma oranı
    use_dictionary=True,          # Kategorik sütunlar için dictionary encoding
    row_group_size=500_000,       # 500K satırlık gruplar
    write_statistics=True
)
```

## Benchmark Referansı

| Metrik | Değer |
|--------|-------|
| Veri seti | 100M satır × 22 sütun |
| Parquet boyutu | 4.20 GB (ZSTD) |
| Okuma süresi | 62.5 saniye |
| RAM kullanımı | 6.35 GB |
| Kategorik parse hızlanması | ~1000x |
