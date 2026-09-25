"""
AI Service - Academic Statistical Interpreter
Integrates Qwen2.5 / transformers pipeline with instant local rule-based academic fallback.
"""

import importlib
import json
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

# Global lazy pipeline container
_hf_pipeline: Callable[..., Any] | None = None
_hf_pipeline_checked: bool = False


def get_hf_pipeline() -> Callable[..., Any] | None:
    """
    Lazy loader for HuggingFace transformers pipeline (Qwen2.5-1.5B-Instruct).
    Caches lookup state if transformers or model is not installed/loadable.
    """
    global _hf_pipeline, _hf_pipeline_checked
    if not _hf_pipeline_checked:
        _hf_pipeline_checked = True
        try:
            transformers_mod = importlib.import_module("transformers")
            pipeline_fn = transformers_mod.pipeline
            logger.info("Yapay Zeka (Qwen2.5) modeli yükleniyor...")
            _hf_pipeline = pipeline_fn(
                "text-generation", model="Qwen/Qwen2.5-1.5B-Instruct"
            )
        except Exception as e:  # noqa: BLE001
            logger.info(
                f"HuggingFace pipeline kullanılamıyor, kural motoruna geçilecek: {e}"
            )
            _hf_pipeline = None
    return _hf_pipeline


def generate_rule_based_insight(
    stats: dict[str, Any] | None,
    advanced: dict[str, Any] | None = None,
    chart_type: str = "Grafik",
    x_col: str = "Bilinmiyor",
    y_cols: list[str] | None = None,
) -> str:
    """
    Local Rule-based Executive & Academic Insight Generator.
    Produces rigorous Turkish statistical analysis without needing an external LLM.
    """
    y_list: list[str] = list(y_cols) if y_cols else []
    adv_dict: dict[str, Any] = advanced if isinstance(advanced, dict) else {}

    items: list[str] = []

    # --- YÖNETİCİ ÖZETİ (BUSINESS TEMPLATE) ---
    business_notes: list[str] = [f"### 💼 Yönetici Özeti ({chart_type.upper()})"]
    has_business_insight = False

    for col in y_list:
        adv = adv_dict.get(col)
        if not isinstance(adv, dict) and any(
            k in adv_dict for k in ("correlation", "type", "t_test", "anova")
        ):
            adv = adv_dict
        if not isinstance(adv, dict):
            continue

        adv_type = adv.get("type")
        best_g = adv.get("best_group")
        if adv_type in ("categorical_2", "categorical_n") and best_g:
            has_business_insight = True
            best_v = float(adv.get("best_val") or 0.0)
            worst_g = adv.get("worst_group")
            worst_v = float(adv.get("worst_val") or 0.0)
            business_notes.append(
                f"- **{col}** metriği baz alındığında; en yüksek değere sahip olan **{x_col}**, "
                f"**{best_g}** ({best_v:,.2f}) olarak ölçülmüştür. "
                f"En düşük performansı ise **{worst_g}** ({worst_v:,.2f}) sergilemektedir."
            )
            p_val = adv.get("p_value")
            if isinstance(p_val, (int, float)) and p_val < 0.05:
                business_notes.append(
                    f"  *Not: {x_col} grupları arasındaki bu fark istatistiksel olarak anlamlıdır (p < 0.05).*"
                )

        elif adv_type == "numeric" and adv.get("correlation") is not None:
            has_business_insight = True
            corr = float(adv.get("correlation") or 0.0)
            direction = (
                "pozitif (biri artarken diğeri de artan)"
                if corr >= 0
                else "negatif (biri artarken diğeri azalan)"
            )
            strength = adv.get("interpretation", "zayıf")
            business_notes.append(
                f"- **{x_col}** ile **{col}** arasında **{strength}** düzeyde ve **{direction}** yönlü bir ilişki tespit edilmiştir (Korelasyon: {corr:.2f})."
            )

    if has_business_insight:
        items.append("\n".join(business_notes))
        items.append("---")

    # --- AKADEMİK RAPOR ---
    items.append("### 🎓 Akademik Veri Analizi Raporu")
    items.append(
        f"**Değişkenler:** Bağımsız Değişken (X): `{x_col}`, "
        f"Bağımlı Değişkenler (Y): `{', '.join(y_list) if y_list else 'Genel Dağılım'}`"
    )

    if stats and isinstance(stats, dict):
        # Normalize if a flat stat dict was passed (e.g. {'mean': ..., 'std': ...})
        if any(k in stats for k in ("mean", "median", "min", "max", "std")) and not any(
            isinstance(v, dict) for v in stats.values()
        ):
            col_target = y_list[0] if y_list else "Metrik"
            stats_dict: dict[str, Any] = {col_target: stats}
        else:
            stats_dict = stats

        for col, s in stats_dict.items():
            if not isinstance(s, dict):
                continue
            mean_raw = s.get("mean")
            med_raw = s.get("median")
            min_raw = s.get("min")
            max_raw = s.get("max")
            std_raw = s.get("std")

            mean = float(mean_raw) if isinstance(mean_raw, (int, float)) else None
            med = float(med_raw) if isinstance(med_raw, (int, float)) else None
            min_v = float(min_raw) if isinstance(min_raw, (int, float)) else None
            max_v = float(max_raw) if isinstance(max_raw, (int, float)) else None
            std_v = float(std_raw) if isinstance(std_raw, (int, float)) else None

            col_notes = [f"#### 🔹 **{col} İstatistiksel Analizi:**"]
            if mean is not None and med is not None:
                skew = "simetrik ve normal dağılıma yakın"
                scale_ref = (
                    abs(med)
                    if abs(med) > 1e-9
                    else (std_v if std_v is not None and std_v > 1e-9 else 1.0)
                )
                rel_diff = (mean - med) / scale_ref
                if rel_diff > 0.15:
                    skew = "sağa çarpık (pozitif çarpıklık) dağılım yönünde"
                elif rel_diff < -0.15:
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

            if std_v is not None and mean is not None and mean != 0:
                cv = (std_v / abs(mean)) * 100
                col_notes.append(
                    f"- **Dağılım Ölçüleri:** Standart Sapma: **{std_v:,.2f}** "
                    f"(Varyasyon Katsayısı: %{cv:.1f})."
                )

            items.append("\n".join(col_notes))
    else:
        items.append(
            "- Belirtilen değişkenler üzerinde tanımlayıcı istatistikler incelenmiştir."
        )
        items.append("- Veri setindeki temel gözlemlerin dağılımı analiz edilmiştir.")

    items.append(
        "\n💡 **Akademik Sonuç:** Elde edilen bulgular doğrultusunda, "
        "temel metriklerdeki varyans farklılıklarının ve yapısal etkenlerin "
        "ileri istatistiksel yöntemlerle araştırılması önerilmektedir."
    )

    return "\n\n".join(items)


def generate_academic_insight(
    stats: dict[str, Any] | None,
    advanced: dict[str, Any] | None = None,
    chart_type: str = "Grafik",
    x_col: str = "Bilinmiyor",
    y_cols: list[str] | None = None,
) -> dict[str, Any]:
    """
    Generates academic insight using Qwen2.5 pipeline if available,
    falling back to high-fidelity rule-based statistical interpreter.

    Returns:
        dict: {"insight": str, "text": str, "fallback": bool}
    """
    y_list: list[str] = list(y_cols) if y_cols else []
    adv_dict: dict[str, Any] = advanced if isinstance(advanced, dict) else {}
    pipeline_obj = get_hf_pipeline()

    if pipeline_obj is not None:
        try:
            prompt = (
                f"Şu istatistikleri (Grafik: {chart_type}, X: {x_col}, Y: {', '.join(y_list)}) "
                f"akademik ve yönetici özeti düzeyinde Türkçe olarak kısaca yorumla: "
                f"İstatistikler: {json.dumps(stats, ensure_ascii=False)}, "
                f"İleri Testler: {json.dumps(adv_dict, ensure_ascii=False)}"
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
                    ),
                },
                {"role": "user", "content": prompt},
            ]
            response = pipeline_obj(messages, max_new_tokens=400, temperature=0.3)
            reply = str(response[0]["generated_text"][-1]["content"])
            return {"insight": reply, "text": reply, "fallback": False}
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Qwen2.5 üretim hatası, kural motoru devreye girdi: {e}")

    # Fallback to academic rule engine
    rule_insight = generate_rule_based_insight(
        stats, advanced=adv_dict, chart_type=chart_type, x_col=x_col, y_cols=y_list
    )
    return {"insight": rule_insight, "text": rule_insight, "fallback": True}
