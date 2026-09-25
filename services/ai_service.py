"""
Statistical Interpretation Service - Academic & Executive Insight Engine
Deterministic rule-based statistical interpreter producing clear, concise Turkish commentary
for ANOVA, Welch's T-Test, Correlation, Regression, and Descriptive Statistics.
"""

from typing import Any


def _describe_correlation(corr: float) -> tuple[str, str]:
    """Returns plain-Turkish strength and direction description for a correlation coefficient."""
    abs_c = abs(corr)
    direction = "pozitif" if corr >= 0 else "negatif"
    meaning = (
        "biri artarken diğeri de artmaktadır"
        if corr >= 0
        else "biri artarken diğeri azalmaktadır"
    )
    if abs_c >= 0.8:
        strength = f"çok güçlü {direction}"
    elif abs_c >= 0.6:
        strength = f"güçlü {direction}"
    elif abs_c >= 0.4:
        strength = f"orta düzeyde {direction}"
    elif abs_c >= 0.2:
        strength = f"zayıf {direction}"
    else:
        strength = "çok zayıf / ihmal edilebilir"
    return strength, meaning


def _describe_distribution(s: dict[str, Any]) -> str | None:
    """Builds a single concise sentence summarizing a numeric column's distribution."""
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

    if mean is None or med is None:
        return None

    scale_ref = (
        abs(med)
        if abs(med) > 1e-9
        else (std_v if std_v is not None and std_v > 1e-9 else 1.0)
    )
    rel_diff = (mean - med) / scale_ref
    if rel_diff > 0.15:
        skew_text = "yüksek uç değerler ortalamayı yukarı çekmektedir (sağa çarpık)"
    elif rel_diff < -0.15:
        skew_text = "düşük uç değerler ortalamayı aşağı çekmektedir (sola çarpık)"
    else:
        skew_text = "veriler ortalama etrafında dengeli dağılmıştır (simetrik)"

    spread_text = ""
    if min_v is not None and max_v is not None:
        spread_text = (
            f" Değerler **{min_v:,.2f}** ile **{max_v:,.2f}** aralığında değişmektedir."
        )
    elif std_v is not None and mean != 0:
        cv = (std_v / abs(mean)) * 100
        if cv < 25:
            spread_text = " Gözlemler birbirine yakın ve tutarlıdır."
        elif cv >= 60:
            spread_text = " Gözlemler geniş bir aralığa yayılmıştır."

    return (
        f"Ortalama **{mean:,.2f}**, medyan **{med:,.2f}** düzeyindedir; "
        f"{skew_text}.{spread_text}"
    )


def _extract_key_findings(
    stats: dict[str, Any] | None,
    advanced: dict[str, Any] | None = None,
    x_col: str = "Bilinmiyor",
    y_cols: list[str] | None = None,
) -> list[str]:
    """Extracts concise, readable bullet-point findings from descriptive and inferential statistics."""
    findings: list[str] = []
    y_list: list[str] = list(y_cols) if y_cols else []
    adv_dict: dict[str, Any] = advanced if isinstance(advanced, dict) else {}

    for col in y_list:
        adv = adv_dict.get(col)
        if not isinstance(adv, dict) and any(
            k in adv_dict for k in ("correlation", "type", "t_test", "anova")
        ):
            adv = adv_dict
        if not isinstance(adv, dict):
            continue

        adv_type = adv.get("type")
        if adv_type == "numeric" and adv.get("correlation") is not None:
            corr = float(adv.get("correlation") or 0.0)
            strength, meaning = _describe_correlation(corr)
            if abs(corr) >= 0.2:
                findings.append(
                    f"<strong>İlişki Yönü:</strong> <strong>{x_col}</strong> ile <strong>{col}</strong> arasında "
                    f"<strong>{strength}</strong> bir ilişki vardır (<em>r</em> = {corr:.2f}); {meaning}."
                )
            else:
                findings.append(
                    f"<strong>İlişki Yönü:</strong> <strong>{x_col}</strong> ile <strong>{col}</strong> arasında "
                    f"belirgin bir doğrusal ilişki görülmemektedir (<em>r</em> = {corr:.2f})."
                )

            r2 = adv.get("r_squared")
            eq = adv.get("regression")
            if isinstance(r2, (int, float)):
                findings.append(
                    f"<strong>Model Gücü:</strong> Kurulan model (<code>{eq or '-'}</code>), "
                    f"<strong>{col}</strong> değişiminin <strong>%{r2 * 100:.1f}</strong>'ini açıklamaktadır."
                )

            p_val = adv.get("p_value")
            if isinstance(p_val, (int, float)):
                if p_val < 0.05:
                    findings.append(
                        "<strong>Güvenilirlik:</strong> Sonuç istatistiksel olarak <strong>anlamlı ve güvenilirdir</strong> (<em>p</em> &lt; 0.05)."
                    )
                else:
                    findings.append(
                        "<strong>Güvenilirlik:</strong> İlişki istatistiksel anlamlılık eşiğini aşmamaktadır; tesadüfi olabilir (<em>p</em> ≥ 0.05)."
                    )

        elif adv_type in ("categorical_2", "categorical_n"):
            best_g = adv.get("best_group")
            worst_g = adv.get("worst_group")
            if best_g and worst_g:
                best_v = float(adv.get("best_val") or 0.0)
                worst_v = float(adv.get("worst_val") or 0.0)
                findings.append(
                    f"<strong>Grup Karşılaştırması:</strong> En yüksek <strong>{col}</strong> ortalaması "
                    f"<strong>{best_g}</strong> ({best_v:,.2f}), en düşük ise <strong>{worst_g}</strong> ({worst_v:,.2f}) grubundadır."
                )

    if stats and isinstance(stats, dict):
        stats_dict = (
            {y_list[0] if y_list else "Metrik": stats}
            if any(k in stats for k in ("mean", "median", "min", "max", "std"))
            and not any(isinstance(v, dict) for v in stats.values())
            else stats
        )
        for col, s in stats_dict.items():
            if not isinstance(s, dict):
                continue
            dist_summary = _describe_distribution(s)
            if dist_summary:
                clean_html = dist_summary.replace("**", "<strong>", 1)
                while "**" in clean_html:
                    clean_html = clean_html.replace("**", "</strong>", 1).replace(
                        "**", "<strong>", 1
                    )
                findings.append(f"<strong>{col} Dağılımı:</strong> {clean_html}")

    return findings


def generate_rule_based_insight(
    stats: dict[str, Any] | None,
    advanced: dict[str, Any] | None = None,
    chart_type: str = "Grafik",
    x_col: str = "Bilinmiyor",
    y_cols: list[str] | None = None,
) -> str:
    """
    Deterministic Statistical Insight Generator.
    Produces clear, plain-Turkish bullet points without repetitive filler text.
    """
    y_list: list[str] = list(y_cols) if y_cols else []
    adv_dict: dict[str, Any] = advanced if isinstance(advanced, dict) else {}

    bullets: list[str] = []

    # 1. KARŞILAŞTIRMA VEYA İLİŞKİ ÖZETİ
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
            best_v = float(adv.get("best_val") or 0.0)
            worst_g = adv.get("worst_group")
            worst_v = float(adv.get("worst_val") or 0.0)
            bullets.append(
                f"- **En Yüksek & En Düşük Grup:** **{col}** ortalaması en yüksek **{x_col}** grubu "
                f"**{best_g}** ({best_v:,.2f}), en düşük grup ise **{worst_g}** ({worst_v:,.2f}) olarak ölçülmüştür."
            )

            p_val = adv.get("p_value")
            if isinstance(p_val, (int, float)):
                test_label = (
                    "ANOVA" if adv_type == "categorical_n" else "Bağımsız T-Testi"
                )
                if p_val < 0.05:
                    bullets.append(
                        f"- **Farkın Anlamlılığı ({test_label}):** Gruplar arasındaki bu fark istatistiksel olarak "
                        f"**anlamlıdır** (*p* < 0.05); yani **{x_col}** değişimi sonuçları gerçekten etkilemektedir."
                    )
                else:
                    bullets.append(
                        f"- **Farkın Anlamlılığı ({test_label}):** Gruplar arasındaki fark istatistiksel olarak "
                        f"**anlamlı değildir** (*p* ≥ 0.05); gruplar birbirine yakın performans göstermektedir."
                    )

        elif adv_type == "numeric" and adv.get("correlation") is not None:
            corr = float(adv.get("correlation") or 0.0)
            strength, meaning = _describe_correlation(corr)
            if abs(corr) >= 0.2:
                bullets.append(
                    f"- **İlişki Yönü & Gücü:** **{x_col}** ile **{col}** arasında **{strength}** bir ilişki vardır "
                    f"(*r* = {corr:.2f}); {meaning}."
                )
            else:
                bullets.append(
                    f"- **İlişki Yönü & Gücü:** **{x_col}** ile **{col}** arasında belirgin bir doğrusal ilişki "
                    f"görülmemektedir (*r* = {corr:.2f})."
                )

            r2 = adv.get("r_squared")
            eq = adv.get("regression")
            if isinstance(r2, (int, float)) and eq:
                bullets.append(
                    f"- **Model Açıklayıcılığı:** Kurulan regresyon modeli (`{eq}`), **{col}** değişiminin "
                    f"**%{r2 * 100:.1f}**'ini açıklamaktadır."
                )

            p_val = adv.get("p_value")
            if isinstance(p_val, (int, float)):
                if p_val < 0.05:
                    bullets.append(
                        "- **Güvenilirlik:** Gözlenen ilişki istatistiksel olarak **anlamlı ve güvenilirdir** (*p* < 0.05)."
                    )
                else:
                    bullets.append(
                        "- **Güvenilirlik:** Gözlenen ilişki istatistiksel olarak **anlamlı değildir** (*p* ≥ 0.05)."
                    )

    # 2. DAĞILIM ÖZETİ (Her sayısal sütun için tek ve net bir cümle)
    if stats and isinstance(stats, dict):
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
            dist_summary = _describe_distribution(s)
            if dist_summary:
                bullets.append(f"- **{col} Dağılım Özeti:** {dist_summary}")

    if not bullets:
        bullets.append(
            "- Seçilen değişkenler için temel dağılım istatistikleri hesaplanmıştır."
        )

    return "\n".join(bullets)


def generate_academic_insight(
    stats: dict[str, Any] | None,
    advanced: dict[str, Any] | None = None,
    chart_type: str = "Grafik",
    x_col: str = "Bilinmiyor",
    y_cols: list[str] | None = None,
) -> dict[str, Any]:
    """
    Generates deterministic academic and executive statistical insights.

    Returns:
        dict: {"insight": str, "text": str, "key_findings": list[str]}
    """
    y_list: list[str] = list(y_cols) if y_cols else []
    adv_dict: dict[str, Any] = advanced if isinstance(advanced, dict) else {}

    rule_insight = generate_rule_based_insight(
        stats, advanced=adv_dict, chart_type=chart_type, x_col=x_col, y_cols=y_list
    )
    key_findings = _extract_key_findings(
        stats, advanced=adv_dict, x_col=x_col, y_cols=y_list
    )
    return {
        "insight": rule_insight,
        "text": rule_insight,
        "key_findings": key_findings,
    }
