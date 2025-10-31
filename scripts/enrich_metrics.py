"""Post-processing enrichment for recipe classification output.

Reads the existing `data/interim/recipes_classified.csv` produced by the
classification pipeline (kept untouched) and writes an enriched version
`data/interim/recipes_classified_enriched.csv` adding:

    - effort_score        (heuristic complexity, 0-10)
    - bayes_mean          (REAL Bayesian shrunk rating mean per recipe, type-specific kb)
    - rating_count_valid  (# of ratings > 0)
    - rating_count_total  (all reviews including zeros)
    - avg_valid_rating    (average rating > 0)
    - Effort_Is_Synthetic / Bayes_Is_Synthetic flags

Logic principles:
    • Non-destructive: original classified file is never overwritten.
    • Deterministic: given the same raw interactions the result is stable.
    • Conservative: Bayesian shrink uses per-type kb from config.
    • No synthetic bayes_mean: if a recipe has zero valid ratings we still produce
        a shrunk value = global type mean (since valid count = 0). Flag synthetic
        only if required rating data entirely unavailable.
"""
from __future__ import annotations
import os
import pandas as pd
from pathlib import Path
from cooking_assistant.config import BAYESIAN_PARAMS, RAW_INTERACTIONS_PREFIX, RAW_DATA_DIR, get_latest_file_with_prefix

SOURCE = Path("data/interim/recipes_classified.csv")
TARGET = Path("data/interim/recipes_classified_enriched.csv")


def _load_source() -> pd.DataFrame:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Source file not found: {SOURCE}")
    return pd.read_csv(SOURCE)


def _derive_effort(df: pd.DataFrame) -> pd.Series:
    """Heuristic effort score (0-10).
    Uses available proxies; if nothing available returns NaN.
    Proxies checked in priority order:
      - number of steps (len of parsed steps list if present)
      - number of ingredients (len of parsed ingredients list if present)
      - name length as a very weak fallback
    Combines normalized components (weights sum to 1).
    """
    import ast
    n = len(df)
    steps_counts = pd.Series([None] * n, dtype="float")
    ingr_counts = pd.Series([None] * n, dtype="float")

    if "steps" in df.columns:
        def _count_steps(val):
            try:
                seq = ast.literal_eval(val) if isinstance(val, str) else val
                return len(seq) if hasattr(seq, "__len__") else None
            except Exception:
                return None
        steps_counts = df["steps"].map(_count_steps)
    if "ingredients" in df.columns:
        def _count_ingr(val):
            try:
                seq = ast.literal_eval(val) if isinstance(val, str) else val
                return len(seq) if hasattr(seq, "__len__") else None
            except Exception:
                return None
        ingr_counts = df["ingredients"].map(_count_ingr)

    name_len = df.get("name", pd.Series([None]*n)).map(lambda x: len(str(x)) if pd.notna(x) else None)

    # Normalize each component independently to 0-1 where possible.
    def _norm(s: pd.Series) -> pd.Series:
        s_num = pd.to_numeric(s, errors="coerce")
        maxv = s_num.max()
        if pd.isna(maxv) or maxv == 0:
            return pd.Series([None]*len(s), dtype="float")
        return s_num / maxv

    w_steps, w_ingr, w_name = 0.5, 0.3, 0.2
    norm_steps = _norm(steps_counts)
    norm_ingr = _norm(ingr_counts)
    norm_name = _norm(name_len)

    combined = (
        norm_steps.fillna(0)*w_steps +
        norm_ingr.fillna(0)*w_ingr +
        norm_name.fillna(0)*w_name
    )
    # Scale to 0-10
    return (combined * 10).round(2)


def _load_interactions() -> pd.DataFrame:
    """Load latest raw interactions file to compute real rating stats."""
    interactions_file = get_latest_file_with_prefix(RAW_INTERACTIONS_PREFIX, RAW_DATA_DIR)
    return pd.read_csv(interactions_file, encoding="utf-8")


def _compute_rating_stats(interactions: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-recipe rating statistics required for Bayesian shrink.
    We treat rating > 0 as VALID (Food.com sometimes stores 0 for unrated saves).
    Returns DataFrame with columns: recipe_id, rating_count_valid, rating_count_total, avg_valid_rating.
    """
    # Ensure columns exist
    required_cols = {"recipe_id", "rating"}
    missing = required_cols - set(interactions.columns)
    if missing:
        raise ValueError(f"Missing columns in interactions for rating stats: {missing}")

    valid_mask = interactions["rating"] > 0
    grp_valid = interactions[valid_mask].groupby("recipe_id")
    avg_valid = grp_valid["rating"].mean().rename("avg_valid_rating")
    cnt_valid = grp_valid.size().rename("rating_count_valid")
    cnt_total = interactions.groupby("recipe_id").size().rename("rating_count_total")

    stats = pd.concat([avg_valid, cnt_valid, cnt_total], axis=1).reset_index()
    stats["rating_count_valid"] = stats["rating_count_valid"].fillna(0).astype(int)
    stats["rating_count_total"] = stats["rating_count_total"].fillna(0).astype(int)
    stats["avg_valid_rating"] = stats["avg_valid_rating"].fillna(0).round(3)
    return stats


def _derive_bayes_mean(recipes: pd.DataFrame, stats: pd.DataFrame) -> pd.Series:
    """Compute REAL Bayesian shrunk mean per recipe using type-specific kb.
    Formula per recipe i of type t:
        bayes_mean_i = (cnt_valid_i * avg_valid_i + kb_t * global_mean_t) / (cnt_valid_i + kb_t)
    Where global_mean_t is the mean of valid ratings (>0) for that type.
    """
    merged = recipes.merge(stats, left_on="id", right_on="recipe_id", how="left")
    # Fill missing counts (no interactions) with 0; avg_valid stays 0.
    merged["rating_count_valid"] = merged["rating_count_valid"].fillna(0)
    merged["avg_valid_rating"] = merged["avg_valid_rating"].fillna(0)
    # Compute global means per type for shrink target.
    # Need interactions-derived stats joined with type.
    type_means = merged.groupby("type")["avg_valid_rating"].apply(lambda s: s[s>0].mean()).to_dict()
    # Fallback if a type has no >0 ratings: use overall mean of all >0 ratings.
    overall_mean = merged[merged["avg_valid_rating"] > 0]["avg_valid_rating"].mean()
    for t in type_means:
        if pd.isna(type_means[t]):
            type_means[t] = overall_mean if not pd.isna(overall_mean) else 0.0
    bayes_values = []
    for _, row in merged.iterrows():
        kb = BAYESIAN_PARAMS[row["type"]]["kb"] if row["type"] in BAYESIAN_PARAMS else 25
        cnt = row["rating_count_valid"]
        avg = row["avg_valid_rating"]
        global_mean_t = type_means.get(row["type"], overall_mean if not pd.isna(overall_mean) else 0.0)
        bayes = (cnt * avg + kb * global_mean_t) / (cnt + kb) if (cnt + kb) > 0 else 0.0
        bayes_values.append(round(bayes, 3))
    return pd.Series(bayes_values, index=recipes.index, name="bayes_mean")


def enrich(force: bool = False):
    df = _load_source()
    if TARGET.exists() and not force:
        print(f"Enriched file already exists: {TARGET} (use force=True to overwrite).")
        return

    # Load interactions for real rating stats.
    try:
        interactions = _load_interactions()
        stats = _compute_rating_stats(interactions)
    except Exception as e:
        print(f"Warning: failed to load interactions for real bayes_mean ({e}). bayes_mean will be synthetic (all NaN).")
        stats = pd.DataFrame(columns=["recipe_id","rating_count_valid","rating_count_total","avg_valid_rating"])

    effort = _derive_effort(df)
    bayes = _derive_bayes_mean(df, stats)
    # Merge stats into df (left join on id)
    df = df.merge(stats, left_on="id", right_on="recipe_id", how="left")
    df.drop(columns=["recipe_id"], inplace=True)
    df["effort_score"] = effort
    df["bayes_mean"] = bayes

    # Flags: Effort synthetic if heuristic missing inputs; Bayes synthetic only if stats absent.
    df["Effort_Is_Synthetic"] = df["effort_score"].isna()
    df["Bayes_Is_Synthetic"] = (df["rating_count_total"].isna())

    df.to_csv(TARGET, index=False)
    print(f"Enriched dataset written to {TARGET} ({len(df)} rows). Real bayes_mean computed for {df['bayes_mean'].notna().sum()} recipes.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Enrich classified recipes with effort & Bayesian mean.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing enriched file if present.")
    args = parser.parse_args()
    try:
        enrich(force=args.force)
    except Exception as e:
        print(f"Enrichment failed: {e}")
        raise