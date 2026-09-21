"""
AI Service - Academic Statistical Interpreter
Integrates Qwen2.5 / transformers pipeline with instant local rule-based academic fallback.
"""

import json
import logging

logger = logging.getLogger(__name__)

# Global lazy pipeline container
_hf_pipeline = None


def get_hf_pipeline():
    """
    Lazy loader for HuggingFace transformers pipeline (Qwen2.5-1.5B-Instruct).
    Caches False if transformers or model is not installed/loadable.
    """
    global _hf_pipeline
    if _hf_pipeline is None:
        try:
            from transformers import pipeline
            logger.info("Yapay Zeka (Qwen2.5) modeli yükleniyor...")
            _hf_pipeline = pipeline("text-generation", model="Qwen/Qwen2.5-1.5B-Instruct")
        except Exception as e:
            logger.info(f"HuggingFace pipeline kullanılamıyor, kural motoruna geçilecek: {e}")
            _hf_pipeline = False
    return _hf_pipeline


def generate_rule_based_insight(stats, chart_type='Grafik', x_col='Bilinmiyor', y_cols=None):
    """
    Local Rule-based Executive & Academic Insight Generator.
    Produces rigorous Turkish statistical analysis without needing an external LLM.
    """
    y_cols = y_cols or []
    items = [f"### 📊 Akademik Veri Analizi Raporu ({chart_type.upper()})"]
    items.append(
        f"**Değişkenler:** Bağımsız Değişken (X): `{x_col}`, "
        f"Bağımlı Değişkenler (Y): `{', '.join(y_cols) if y_cols else 'Genel Dağılım'}`"
    )

    if stats and isinstance(stats, dict):
        for col, s in stats.items():
            mean = s.get('mean')
            med = s.get('median')
            min_v = s.get('min')
            max_v = s.get('max')
            std_v = s.get('std')

            col_notes = [f"#### 🔹 **{col} İstatistiksel Analizi:**"]
            if mean is not None and med is not None:
                skew = "simetrik ve normal dağılıma yakın"
                if mean > med * 1.15:
                    skew = "sağa çarpık (pozitif çarpıklık) dağılım yönünde"
                elif mean < med * 0.85:
                    skew = "sola çarpık (negatif çarpıklık) dağılım yönünde"
                col_notes.append(
                    f"- **Merkezi Eğilim Ölçüleri:** Ortalama: **{mean:,.2f}**, Medyan: **{med:,.2f}**. "
                    f"Dağılım *{skew}* bir yapı göstermektedir."
                )

            if min_v is not None and max_v is not None:
                col_notes.append(
                    f"- **Dağılım Aralığı:** Minimum **{min_v:,.2f}**, Maksimum **{max_v:,.2f}** "
                    f"(Aralık: **{max_v - min_v:,.2f}**)."
                )

            if std_v is not None and mean and mean != 0:
                cv = (std_v / abs(mean)) * 100
                col_notes.append(
                    f"- **Dağılım Ölçüleri:** Standart Sapma: **{std_v:,.2f}** "
                    f"(Varyasyon Katsayısı: %{cv:.1f})."
                )

            items.append("\n".join(col_notes))
    else:
        items.append("- Belirtilen değişkenler üzerinde tanımlayıcı istatistikler incelenmiştir.")
        items.append("- Veri setindeki temel gözlemlerin dağılımı analiz edilmiştir.")

    items.append(
        "\n💡 **Akademik Sonuç:** Elde edilen bulgular doğrultusunda, "
        "temel metriklerdeki varyans farklılıklarının ve yapısal etkenlerin "
        "ileri istatistiksel yöntemlerle araştırılması önerilmektedir."
    )

    return "\n\n".join(items)


def generate_academic_insight(stats, chart_type='Grafik', x_col='Bilinmiyor', y_cols=None):
    """
    Generates academic insight using Qwen2.5 pipeline if available,
    falling back to high-fidelity rule-based statistical interpreter.
    
    Returns:
        dict: {"insight": str, "fallback": bool}
    """
    y_cols = y_cols or []
    pipeline_obj = get_hf_pipeline()

    if pipeline_obj:
        try:
            prompt = (
                f"Şu istatistikleri (Grafik: {chart_type}, X: {x_col}, Y: {', '.join(y_cols)}) "
                f"teknik olmayan birinin anlayacağı basitlikte, Türkçe olarak kısaca yorumla: "
                f"{json.dumps(stats, ensure_ascii=False)}"
            )
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Sen bir akademi profesörü ve istatistik uzmanısın. Amacın, sana gönderilen "
                        "verileri bilimsel bir titizlikle, nesnel ve profesyonel bir akademik dil "
                        "kullanarak analiz etmektir. Yanıtlarını Türkçe ver. Sadece verideki "
                        "istatistiksel eğilimleri (trend), varyans farklılıklarını ve en önemli bulguları "
                        "3-4 madde halinde özetle. Akademik sunumlara uygun, resmi bir istatistiksel "
                        "özet dili (ör. 'harika veriler' yerine 'anlamlı istatistiksel dağılım') kullan. "
                        "Okunabilirliği artırmak için Markdown kullan."
                    )
                },
                {"role": "user", "content": prompt}
            ]
            response = pipeline_obj(messages, max_new_tokens=400, temperature=0.3)
            reply = response[0]['generated_text'][-1]['content']
            return {"insight": reply, "fallback": False}
        except Exception as e:
            logger.warning(f"Qwen2.5 üretim hatası, kural motoru devreye girdi: {e}")

    # Fallback to academic rule engine
    rule_insight = generate_rule_based_insight(stats, chart_type=chart_type, x_col=x_col, y_cols=y_cols)
    return {"insight": rule_insight, "fallback": True}
