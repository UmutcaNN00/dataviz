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


def generate_rule_based_insight(stats, advanced=None, chart_type='Grafik', x_col='Bilinmiyor', y_cols=None):
    """
    Local Rule-based Executive & Academic Insight Generator.
    Produces rigorous Turkish statistical analysis without needing an external LLM.
    """
    y_cols = y_cols or []
    advanced = advanced or {}
    
    items = []

    # --- YÖNETİCİ ÖZETİ (BUSINESS TEMPLATE) ---
    business_notes = [f"### 💼 Yönetici Özeti ({chart_type.upper()})"]
    has_business_insight = False

    for col in y_cols:
        adv = advanced.get(col)
        if not adv:
            continue
        
        if adv.get('type') in ['categorical_2', 'categorical_n'] and adv.get('best_group'):
            has_business_insight = True
            best_g = adv.get('best_group')
            best_v = adv.get('best_val', 0)
            worst_g = adv.get('worst_group')
            worst_v = adv.get('worst_val', 0)
            business_notes.append(
                f"- **{col}** metriği baz alındığında; en yüksek değere sahip olan **{x_col}**, "
                f"**{best_g}** ({best_v:,.2f}) olarak ölçülmüştür. "
                f"En düşük performansı ise **{worst_g}** ({worst_v:,.2f}) sergilemektedir."
            )
            if adv.get('p_value') is not None and adv.get('p_value') < 0.05:
                business_notes.append(f"  *Not: {x_col} grupları arasındaki bu fark istatistiksel olarak anlamlıdır (p < 0.05).*")

        elif adv.get('type') == 'numeric' and adv.get('correlation'):
            has_business_insight = True
            corr = adv.get('correlation', 0)
            direction = "pozitif (biri artarken diğeri de artan)" if corr > 0 else "negatif (biri artarken diğeri azalan)"
            strength = adv.get('interpretation', 'zayıf')
            business_notes.append(
                f"- **{x_col}** ile **{col}** arasında **{strength}** düzeyde ve **{direction}** yönlü bir ilişki tespit edilmiştir (Korelasyon: {corr:.2f})."
            )

    if has_business_insight:
        items.append("\n".join(business_notes))
        items.append("---")

    # --- AKADEMİK RAPOR ---
    items.append(f"### 🎓 Akademik Veri Analizi Raporu")
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


def generate_academic_insight(stats, advanced=None, chart_type='Grafik', x_col='Bilinmiyor', y_cols=None):
    """
    Generates academic insight using Qwen2.5 pipeline if available,
    falling back to high-fidelity rule-based statistical interpreter.
    
    Returns:
        dict: {"insight": str, "fallback": bool}
    """
    y_cols = y_cols or []
    advanced = advanced or {}
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
                        "Okunabilirliliği artırmak için Markdown kullan."
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
    rule_insight = generate_rule_based_insight(stats, advanced=advanced, chart_type=chart_type, x_col=x_col, y_cols=y_cols)
    return {"insight": rule_insight, "fallback": True}
