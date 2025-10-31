"""Tests loader error paths for classified recipes missing file."""
import pytest
from pathlib import Path

from cooking_assistant.data.loader import load_classified_recipes


def test_load_classified_recipes_missing(tmp_path):
    missing = tmp_path / 'recipes_classified.csv'
    with pytest.raises(FileNotFoundError):
        load_classified_recipes(missing)
