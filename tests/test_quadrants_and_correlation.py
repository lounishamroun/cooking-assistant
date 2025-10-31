"""Minimal tests for quadrant computation and correlation ordering.

These focus on logic embedded in Streamlit components without requiring UI rendering.
"""

import pandas as pd
import numpy as np

from app.streamlit import components  # type: ignore


def _build_df():
    # Create deterministic dataframe with effort_score & bayes_mean spanning ranges
    data = {
        "recipe_id": range(1, 11),
        "effort_score": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "bayes_mean": [2.0, 2.5, 3.0, 3.5, 4.0, 1.0, 4.5, 4.2, 3.8, 4.9],
        "feature_a": [10, 9, 8, 7, 6, 5, 4, 3, 2, 1],  # negative correlation
        "feature_b": [1, 2, 1, 2, 1, 2, 1, 2, 1, 2],    # weak pattern
        "feature_c": [2.0, 2.5, 3.0, 3.5, 4.0, 4.2, 4.5, 4.6, 4.7, 4.8],  # strong positive
    }
    return pd.DataFrame(data)


def test_compute_quadrants_median_split():
    df = _build_df()
    # Use expected column name 'bayes_mean'
    qdict, med_eff, med_pop = components.compute_quadrants(df)

    # Median of effort_score (1..10) is 5.5 -> low <5.5 high >=5.5 (component uses < / >=)
    assert med_eff == np.median(df.effort_score)
    assert med_pop == np.median(df.bayes_mean)

    # Component quadrant labels
    assert set(qdict.keys()) == {"Easy Gems", "Ambitious Masterpiece", "Unloved Basic", "Reconsider"}

    # Sum of quadrant assignments equals total rows
    total_assigned = sum(len(sub) for sub in qdict.values())
    assert total_assigned == len(df)


def test_correlation_ordering():
    df = _build_df()
    # Replicate ordering subset: numeric cols except id-like removal already handled in component.
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    target = "bayes_mean"
    corr_series = {}
    for col in numeric_cols:
        if col == target:
            continue
        val = df[col].corr(df[target])
        if pd.notnull(val):
            corr_series[col] = val
    ordered = sorted(corr_series.items(), key=lambda kv: abs(kv[1]), reverse=True)
    # Weak pattern column expected at tail
    assert ordered[-1][0] == "feature_b"
    # Ensure we evaluated at least 3 predictive features
    assert {c for c, _ in ordered}.issuperset({"effort_score", "feature_a", "feature_c"})
