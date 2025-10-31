"""Reusable UI components for the Streamlit dashboard (non-destructive).
Encapsulates analytical & explanatory widgets without altering existing logic.
All user-visible strings standardized to English.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import streamlit as st
from pathlib import Path
import plotly.express as px

# ------------------------------------------------------------------
# CSS Injector (minimal risk: reads external stylesheet)
# ------------------------------------------------------------------

def inject_css():
    css_path = Path(__file__).parent / "styles.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Section header & info box
# ------------------------------------------------------------------

def section_header(title: str, anchor: str | None = None):
    anchor = anchor or title.lower().replace(" ", "-")
    st.markdown(f"<h2 id='{anchor}' class='section-header'>{title}</h2>", unsafe_allow_html=True)


def info_box(title: str, body: str):
    st.markdown(
        f"""
        <div class='info-box'>
          <h4>{title}</h4>
          <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------------
# Insight generation (rule-based, no new columns required)
# ------------------------------------------------------------------

def generate_insights(df: pd.DataFrame) -> list[str]:
    """Derive lightweight analytical bullet points; never raises."""
    if df.empty:
        return ["No filtered data available to generate insights."]
    insights: list[str] = []
    try:
        if {"effort_score", "bayes_mean"}.issubset(df.columns):
            corr_s = df["effort_score"].corr(df["bayes_mean"], method="spearman")
            if pd.notna(corr_s) and abs(corr_s) < 0.07:
                insights.append(f"Effort and popularity appear nearly independent (Spearman ≈ {corr_s:.3f}).")
        if "bayes_mean" in df.columns:
            q1, q3 = df["bayes_mean"].quantile([0.25, 0.75])
            iqr = q3 - q1
            if iqr < 0.05:
                insights.append(f"Low dispersion of popularity scores (IQR {iqr:.3f}) → homogeneous appeal.")
        if {"effort_score", "bayes_mean"}.issubset(df.columns):
            med_eff = df["effort_score"].median(); med_pop = df["bayes_mean"].median()
            easy_gems = df[(df.effort_score < med_eff) & (df.bayes_mean > med_pop)]
            ratio = len(easy_gems)/len(df) if len(df) else 0
            if ratio > 0.12:
                insights.append(f"Meaningful 'Easy Gems' segment ({ratio:.1%} of filtered recipes).")
        if "n_ingredients" in df.columns and "bayes_mean" in df.columns:
            ci = abs(df["n_ingredients"].corr(df["bayes_mean"], method="spearman"))
            if pd.notna(ci) and ci < 0.08:
                insights.append("Ingredient count has weak monotonic relation with popularity.")
    except Exception as e:  # defensive, never break page
        insights.append(f"(Insight generation limited: {e})")
    if not insights:
        insights.append("No strong patterns detected in the current subset.")
    return insights


def render_insight_panel(df: pd.DataFrame):
    insights = generate_insights(df)
    if not insights:
        return
    bullets = "".join(f"<li>{txt}</li>" for txt in insights)
    st.markdown(f"<div class='insight-panel'><ul class='point-list'>{bullets}</ul></div>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Quadrant computation & plot
# ------------------------------------------------------------------

def compute_quadrants(df: pd.DataFrame):
    """Return quadrant DataFrames & medians; empty dict if required columns absent."""
    if df.empty or not {"effort_score", "bayes_mean"}.issubset(df.columns):
        return {}, None, None
    med_eff = df["effort_score"].median(); med_pop = df["bayes_mean"].median()
    quadrants = {
        "Easy Gems": df[(df.effort_score < med_eff) & (df.bayes_mean > med_pop)],
        "Ambitious Masterpiece": df[(df.effort_score >= med_eff) & (df.bayes_mean > med_pop)],
        "Unloved Basic": df[(df.effort_score < med_eff) & (df.bayes_mean <= med_pop)],
        "Reconsider": df[(df.effort_score >= med_eff) & (df.bayes_mean <= med_pop)],
    }
    return quadrants, med_eff, med_pop


def quadrant_summary(qdict: dict[str, pd.DataFrame], total: int):
    rows = []
    for label, sub in qdict.items():
        pct = (len(sub)/total)*100 if total else 0
        name_col = "name" if "name" in sub.columns else ("Name" if "Name" in sub.columns else None)
        example = sub.head(1)[name_col].iloc[0] if (name_col and not sub.empty) else "—"
        rows.append((label, len(sub), pct, example))
    return rows


def render_quadrant_plot(df: pd.DataFrame):
    qdict, med_eff, med_pop = compute_quadrants(df)
    if not qdict:
        st.info("Required columns ('effort_score', 'bayes_mean') not available.")
        return
    sample = df.sample(min(len(df), 15000), random_state=42)  # performance guard
    hover_cols = [c for c in ["name", "Name", "effort_score", "bayes_mean"] if c in sample.columns]
    fig = px.scatter(
        sample, x="effort_score", y="bayes_mean", opacity=0.55,
        color_discrete_sequence=["#c44a42"],
        hover_data={c: True for c in hover_cols},
    )
    fig.add_vline(x=med_eff, line_width=1, line_dash="dash", line_color="#888")
    fig.add_hline(y=med_pop, line_width=1, line_dash="dash", line_color="#888")
    fig.update_layout(title="Effort vs Popularity Quadrants (medians)")
    st.plotly_chart(fig, use_container_width=True)

    rows = quadrant_summary(qdict, len(df))
    st.markdown("<div class='quadrant-legend'>", unsafe_allow_html=True)
    for label, count, pct, example in rows:
        st.markdown(
            f"<div class='quadrant-tag'><strong>{label}</strong><br>{count} recipes · {pct:.1f}%<br><em>{example}</em></div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Correlation heatmap (ordered)
# ------------------------------------------------------------------

def render_correlation(df: pd.DataFrame, method: str = "spearman"):
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    # Exclude identifier and synthetic flag columns from analytical correlation
    exclude = {"ID", "id", "Effort_Is_Synthetic", "Bayes_Is_Synthetic", "Confidence_Is_Synthetic"}
    numeric_cols = [c for c in numeric_cols if c not in exclude]
    if len(numeric_cols) < 3:
        st.info("Not enough numeric columns for correlation analysis.")
        return
    # Drop columns that are all NaN or constant (no variance → correlation undefined / trivial)
    filtered = []
    for c in numeric_cols:
        col = pd.to_numeric(df[c], errors="coerce")
        if col.nunique(dropna=True) > 1:  # retain columns with variance
            filtered.append(c)
    if len(filtered) < 2:
        st.info("Numeric columns are constant; cannot compute meaningful correlations.")
        return
    corr = df[filtered].corr(method=method)
    target = "bayes_mean" if "bayes_mean" in corr.columns else filtered[0]
    order = corr[target].abs().sort_values(ascending=False).index.tolist()
    corr_ordered = corr.loc[order, order]
    fig = px.imshow(
        corr_ordered,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
    )
    fig.update_layout(title=f"Ordered Correlation Matrix ({method.capitalize()}) by |corr({target})|")
    st.plotly_chart(fig, use_container_width=True)
    # Explanatory panel tailored to actual displayed columns
    shown_cols = ", ".join(corr_ordered.columns.tolist())
    st.markdown(
        f"""
        <div class='info-box large-text'>
            <h4>Reading the Matrix</h4>
            <ul class='info-points'>
                <li><strong>Scope:</strong> Columns analyzed → {shown_cols}</li>
                <li><strong>Order:</strong> Sorted by |corr(bayes_mean)| (or target) to surface strongest links.</li>
                <li><strong>Scale:</strong> -1 inverse · +1 direct · ~0 weak/no monotonic relation.</li>
                <li><strong>Filtering:</strong> IDs, synthetic flags, constants removed to avoid noise.</li>
                <li><strong>Caution:</strong> Correlation ≠ causation; rating compression may mute effects.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------------
# Public render bundle for easy integration
# ------------------------------------------------------------------

def render_insights_and_quadrants(df: pd.DataFrame):
        section_header("Analytical Synopsis")
        render_insight_panel(df)
        st.markdown(
                """
                <div class='info-box large-text'>
                    <h4>Interpretation Guide</h4>
                    <ul class='info-points'>
                        <li><strong>Medians:</strong> Used for splits (robust vs outliers).</li>
                        <li><strong>Easy Gems:</strong> Low effort · High popularity → promote.</li>
                        <li><strong>Ambitious Masterpiece:</strong> High effort · High popularity → showcase.</li>
                        <li><strong>Unloved Basic:</strong> Low effort · Low popularity → consider refresh.</li>
                        <li><strong>Reconsider:</strong> High effort · Low popularity → simplify or reposition.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
        )
        section_header("Popularity vs Effort Quadrants")
        render_quadrant_plot(df)

__all__ = [
    "inject_css",
    "section_header",
    "info_box",
    "render_insight_panel",
    "render_quadrant_plot",
    "render_insights_and_quadrants",
    "render_correlation",
]
