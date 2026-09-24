import sys
sys.path.insert(0, '.')
import json
from app import create_app
from core.store import set_df
import polars as pl
import pandas as pd

app = create_app()
client = app.test_client()

# Load 10M parquet or small sample into store
df_pd = pd.DataFrame({
    'Adet': [10, 20, 30, 40, 50, 60, 70, 80],
    'Maliyet': [100, 190, 310, 420, 490, 610, 700, 820],
    'Satis': [150, 280, 440, 590, 720, 890, 1020, 1190]
})
with client.session_transaction() as sess:
    sess['user_id'] = 'test_user_123'

set_df(df_pd, 1, user_id='test_user_123')

res_corr = client.post('/get_correlation_matrix', json={'method': 'pearson'})
print("Status corr matrix:", res_corr.status_code)
print("Corr matrix data:", res_corr.get_json())
assert res_corr.status_code == 200
assert 'matrix' in res_corr.get_json()

res_reg = client.post('/get_regression_studio_data', json={
    'x_col': 'Adet',
    'y_col': 'Satis',
    'model_type': 'linear',
    'corr_method': 'pearson'
})
print("Status regression studio:", res_reg.status_code)
data_reg = res_reg.get_json()
print("Equation:", data_reg['regression']['equation'])
print("R²:", data_reg['regression']['r_squared'])
print("CI lower points count:", len(data_reg['regression']['ci_lower']))
print("Scatter sample points count:", len(data_reg['scatter_x']))
assert res_reg.status_code == 200
assert data_reg['regression']['r_squared'] > 0.99
print("All backend tests PASSED!")
