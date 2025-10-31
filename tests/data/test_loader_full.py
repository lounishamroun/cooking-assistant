"""Tests load_data function with fallback non-timestamp file names."""
from pathlib import Path
from cooking_assistant.data.loader import load_data
from cooking_assistant.config import RAW_RECIPES_PREFIX, RAW_INTERACTIONS_PREFIX
import csv


def test_load_data_fallback_names(tmp_path, monkeypatch):
    # Create raw directory and non-timestamp files
    raw_dir = tmp_path
    recipes_file = raw_dir / f"{RAW_RECIPES_PREFIX}.csv"
    interactions_file = raw_dir / f"{RAW_INTERACTIONS_PREFIX}.csv"

    with open(recipes_file, 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['id','name','type']); w.writerow([1,'R','plat'])
    with open(interactions_file, 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['recipe_id','rating','date']); w.writerow([1,5,'2024-03-21'])

    # Monkeypatch RAW_DATA_DIR used indirectly via get_latest_file_with_prefix by passing raw_dir to load_data
    recipes, interactions = load_data(raw_dir)
    assert len(recipes) == 1
    assert len(interactions) == 1
