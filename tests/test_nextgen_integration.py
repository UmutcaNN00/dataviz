import json
import pandas as pd
import numpy as np

import app
from core.store import set_df

# Test veri seti hazırla ve aktif dataframe olarak set et
df = pd.DataFrame({
    'Musteri_ID': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
    'Satis_Tutari': [150.0, 220.5, 95.0, 1800.0, 310.0, 420.0, 15.0, 290.0, 330.0, 9999.0], # 9999 aykiri
    'Yas': [25, 34, 45, 29, 31, 52, 23, 41, 38, 99], # 99 aykiri
    'Memnuniyet_Orani': [85, 90, 75, 95, 80, 88, 60, 92, 85, 150], # 150 kural ihlali (>100)
    'Sehir': ['Istanbul', 'Ankara', 'Izmir', 'Bursa', 'Antalya', 'Istanbul', 'Ankara', 'Izmir', 'Bursa', 'Istanbul']
})

client = app.app.test_client()

with client.session_transaction() as sess:
    sess['user_id'] = 'test_user_123'

set_df(df, 1, user_id='test_user_123')

print("--- 1. TEST: /get_table_slice ---")
res = client.post('/get_table_slice', json={'start': 0, 'limit': 10, 'sort_col': 'Satis_Tutari', 'sort_asc': False})
assert res.status_code == 200, f'get_table_slice failed: {res.data}'
d1 = res.get_json()
assert d1['success'] is True
assert len(d1['rows']) == 10
assert d1['rows'][0]['_row_id'] is not None
print("OK! Toplam satir:", d1['total_rows'], "Donen:", len(d1['rows']))

print("--- 2. TEST: /filter_predicate_pushdown (SIMD) ---")
res = client.post('/filter_predicate_pushdown', json={
    'predicates': [{'column': 'Satis_Tutari', 'op': '>=', 'value': 300}],
    'limit': 10,
    'offset': 0
})
assert res.status_code == 200, f'filter_predicate_pushdown failed: {res.data}'
d2 = res.get_json()
assert d2['success'] is True
assert d2['zero_copy_preserved'] is True
assert 'elapsed_ms' in d2
assert len(d2['rows']) == d2['matched_rows']
assert d2['rows'][0]['_row_id'] is not None
print(f"OK! Eslesen: {d2['matched_rows']}, Hiz: {d2['elapsed_ms']} ms")

print("--- 3. TEST: /evaluate_data_contracts ---")
res = client.get('/evaluate_data_contracts')
assert res.status_code == 200, f'evaluate_data_contracts failed: {res.data}'
d3 = res.get_json()
assert d3['success'] is True
rep = d3['contracts_report']
assert 'grade' in rep
assert 'compliance_score' in rep
assert len(rep['rules']) > 0
print(f"OK! Not: {rep['grade']}, Skor: %{rep['compliance_score']}, Kural Sayisi: {rep['total_rules_evaluated']}")

print("--- 4. TEST: /detect_ensemble_anomalies (3'lu Konsensus) ---")
res = client.get('/detect_ensemble_anomalies?contamination=0.1&top_n=5')
assert res.status_code == 200, f'detect_ensemble_anomalies failed: {res.data}'
d4 = res.get_json()
assert d4['success'] is True
ens = d4['ensemble_report']
assert 'total_consensus_anomalies' in ens
assert 'anomalies' in ens
print(f"OK! Konsensus Anomali: {ens['total_consensus_anomalies']}, Yanlis Alarm Azaltma: %{ens['false_positive_reduction_pct']}")

print("--- 5. TEST: /get_explainable_anomalies (Aciklanabilir Gerekceler) ---")
res = client.get('/get_explainable_anomalies?top_n=5')
assert res.status_code == 200, f'get_explainable_anomalies failed: {res.data}'
d5 = res.get_json()
assert d5['success'] is True
exp = d5['anomaly_report']
assert 'explained_rows' in exp
print(f"OK! Tespit Edilen Aykiri: {exp['total_anomalies_found']}")
if exp['explained_rows']:
    r0 = exp['explained_rows'][0]
    reason_txt = r0['top_reasons'][0]['reason'].encode('ascii', errors='replace').decode('ascii')
    print(f"   Ornek gerekce: Satir #{r0['row_index']} -> {reason_txt}")

print("\n*** TEBRIKLER! TUM 5 YENI NESIL ENTEGRASYON TESTI EKSIKSIZ GECTI! ***")
