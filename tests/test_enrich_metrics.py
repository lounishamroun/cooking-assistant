import pandas as pd
import os
from pathlib import Path
import pytest

from scripts import enrich_metrics
from cooking_assistant.config import BAYESIAN_PARAMS


def _make_recipes_df():
    """Minimal classified recipes subset (no rating aggregates)."""
    return pd.DataFrame([
        {"id": 1, "name": "simple cake", "type": "dessert", "steps": "['mix','bake','cool']", "ingredients": "['flour','sugar','eggs','butter']"},
        {"id": 2, "name": "hearty stew", "type": "plat", "steps": "['chop','simmer','serve','store']", "ingredients": "['beef','carrot','onion','potato','stock']"},
    ])


def _make_interactions_df():
    """Synthetic interactions resembling RAW_interactions for real bayes_mean calc.
    rating=0 rows included to test exclusion from avg_valid_rating.
    """
    rows = [
        {"recipe_id": 1, "rating": 5, "date": "2020-01-01"},
        {"recipe_id": 1, "rating": 4, "date": "2020-01-02"},
        {"recipe_id": 1, "rating": 0, "date": "2020-01-03"},  # ignored in avg
        {"recipe_id": 2, "rating": 4, "date": "2020-01-01"},
        {"recipe_id": 2, "rating": 0, "date": "2020-01-02"},
    ]
    return pd.DataFrame(rows)


def test_effort_score_range():
    recipes = _make_recipes_df()
    effort = enrich_metrics._derive_effort(recipes)
    assert effort.notna().all(), "Effort scores should be computed"
    assert (effort >= 0).all() and (effort <= 10).all(), "Effort scores must be within 0-10"


def test_bayesian_mean_real_calculation(monkeypatch):
    recipes = _make_recipes_df()
    interactions = _make_interactions_df()

    # Monkeypatch loader helpers to avoid accessing real large files
    monkeypatch.setattr(enrich_metrics, "_load_interactions", lambda: interactions)

    stats = enrich_metrics._compute_rating_stats(interactions)
    bayes = enrich_metrics._derive_bayes_mean(recipes, stats)

    # Compute expected manually per type
    # dessert type (id=1): valid ratings = [5,4] avg=4.5
    # plat type (id=2): valid ratings = [4] avg=4.0
    kb_dessert = BAYESIAN_PARAMS['dessert']['kb']
    kb_plat = BAYESIAN_PARAMS['plat']['kb']
    global_mean_dessert = 4.5  # only dessert recipe
    global_mean_plat = 4.0     # only plat recipe
    expected_id1 = (2 * 4.5 + kb_dessert * global_mean_dessert) / (2 + kb_dessert)
    expected_id2 = (1 * 4.0 + kb_plat * global_mean_plat) / (1 + kb_plat)
    assert abs(bayes.iloc[0] - expected_id1) < 1e-6
    assert abs(bayes.iloc[1] - expected_id2) < 1e-6


def test_full_enrichment_generates_real_bayes(tmp_path, monkeypatch):
    recipes = _make_recipes_df()
    interactions = _make_interactions_df()
    source = tmp_path / "recipes_classified.csv"
    recipes.to_csv(source, index=False)
    target = tmp_path / "recipes_classified_enriched.csv"

    monkeypatch.setattr(enrich_metrics, "SOURCE", source)
    monkeypatch.setattr(enrich_metrics, "TARGET", target)
    monkeypatch.setattr(enrich_metrics, "_load_interactions", lambda: interactions)

    enrich_metrics.enrich(force=True)
    enriched = pd.read_csv(target)
    assert 'bayes_mean' in enriched.columns
    assert enriched['bayes_mean'].notna().all(), "bayes_mean should be real (not synthetic)"
    assert not enriched['Bayes_Is_Synthetic'].any(), "Synthetic flag should be False when interactions available"


def test_idempotent_behavior(tmp_path, monkeypatch):
    recipes = _make_recipes_df()
    interactions = _make_interactions_df()
    source = tmp_path / "recipes_classified.csv"
    target = tmp_path / "recipes_classified_enriched.csv"
    recipes.to_csv(source, index=False)
    monkeypatch.setattr(enrich_metrics, "SOURCE", source)
    monkeypatch.setattr(enrich_metrics, "TARGET", target)
    monkeypatch.setattr(enrich_metrics, "_load_interactions", lambda: interactions)

    enrich_metrics.enrich(force=True)
    first_mtime = os.path.getmtime(target)
    enrich_metrics.enrich()  # No force, should skip overwrite
    second_mtime = os.path.getmtime(target)
    assert first_mtime == second_mtime, "Second run without force should not modify file"


def test_bayes_mean_missing_interactions_marks_synthetic(tmp_path, monkeypatch):
    recipes = _make_recipes_df()
    source = tmp_path / "recipes_classified.csv"
    target = tmp_path / "recipes_classified_enriched.csv"
    recipes.to_csv(source, index=False)
    monkeypatch.setattr(enrich_metrics, "SOURCE", source)
    monkeypatch.setattr(enrich_metrics, "TARGET", target)
    # Force interactions loader to fail
    monkeypatch.setattr(enrich_metrics, "_load_interactions", lambda: (_ for _ in ()).throw(Exception("mock failure")))
    enrich_metrics.enrich(force=True)
    enriched = pd.read_csv(target)
    assert enriched['Bayes_Is_Synthetic'].any(), "Should mark synthetic when interactions unavailable"
