import sys
sys.path.insert(0, '.')
import time
import numpy as np
import polars as pl
from services.stats_service import compute_robust_correlation, compute_robust_regression

print("10M satırlık parquet okunuyor...")
t0 = time.perf_counter()
df_pl = pl.read_parquet("uploads/10M_Devasa_Satis_Verisi.parquet")
t_read = time.perf_counter() - t0
print(f"Parquet okundu: {t_read:.3f} sn, satır sayısı: {len(df_pl):,}")

# Test numeric columns
col_x = "Adet"
col_y = [c for c in df_pl.columns if "Tutar" in c][0]
x_vals = df_pl[col_x].to_numpy()
y_vals = df_pl[col_y].to_numpy()

print("Korelasyon hesaplanıyor...")
t1 = time.perf_counter()
corr = compute_robust_correlation(x_vals, y_vals, method='pearson')
t_corr = time.perf_counter() - t1
print(f"Pearson Korelasyon hesaplandı ({t_corr:.3f} sn): r = {corr['coef']:.4f}, p = {corr['p_value']}")

print("Regresyon hesaplanıyor...")
t2 = time.perf_counter()
reg = compute_robust_regression(x_vals, y_vals, model_type='linear')
t_reg = time.perf_counter() - t2
print(f"Doğrusal Regresyon hesaplandı ({t_reg:.3f} sn): {reg['equation']}, R² = {reg['r_squared']:.4f}")
