"""Tests for data loading helper functions."""
import pandas as pd
import pytest
from pathlib import Path

from cooking_assistant.config import get_latest_file_with_prefix, RAW_RECIPES_PREFIX, RAW_INTERACTIONS_PREFIX
from cooking_assistant.data.loader import load_recipes, load_interactions


def _write_csv(path: Path, rows):
    import csv
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


def test_get_latest_file_with_prefix(tmp_path):
    # Create two timestamped files
    f1 = tmp_path / f"{RAW_RECIPES_PREFIX}_20240101-120000.csv"
    f2 = tmp_path / f"{RAW_RECIPES_PREFIX}_20240201-120000.csv"
    _write_csv(f1, [{"id": 1, "name": "A"}])
    _write_csv(f2, [{"id": 2, "name": "B"}])

    latest = get_latest_file_with_prefix(RAW_RECIPES_PREFIX, tmp_path)
    assert latest == f2  # lexicographically later


def test_get_latest_file_with_prefix_fallback(tmp_path):
    # Only non-timestamp file
    f = tmp_path / f"{RAW_INTERACTIONS_PREFIX}.csv"
    _write_csv(f, [{"recipe_id": 1, "rating": 5, "date": "2024-03-10"}])
    latest = get_latest_file_with_prefix(RAW_INTERACTIONS_PREFIX, tmp_path)
    assert latest == f


def test_get_latest_file_with_prefix_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        get_latest_file_with_prefix("NON_EXISTENT", tmp_path)


def test_load_recipes_and_interactions(tmp_path, monkeypatch):
    # Create fake raw files
    recipes_file = tmp_path / f"{RAW_RECIPES_PREFIX}_20240101-120000.csv"
    interactions_file = tmp_path / f"{RAW_INTERACTIONS_PREFIX}_20240101-120000.csv"

    _write_csv(recipes_file, [
        {"id": 1, "name": "Salade", "minutes": 10},
        {"id": 2, "name": "Cake", "minutes": 30},
    ])
    _write_csv(interactions_file, [
        {"recipe_id": 1, "rating": 5, "date": "2024-03-10"},
        {"recipe_id": 2, "rating": 4, "date": "2024-03-11"},
    ])

    # Monkeypatch RAW_DATA_DIR usage by passing directory directly to loader functions
    df_r = load_recipes(tmp_path)
    df_i = load_interactions(tmp_path)

    assert len(df_r) == 2
    assert len(df_i) == 2
