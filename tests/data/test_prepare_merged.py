"""Tests for data preparation merging and season assignment."""
import pandas as pd
import pytest

from cooking_assistant.data.processor import prepare_merged_data


def test_prepare_merged_basic(recipes_df, interactions_df):
    merged = prepare_merged_data(recipes_df, interactions_df, verbose=False)
    assert 'season' in merged.columns
    assert 'name' in merged.columns
    assert merged['season'].isin(['Spring', 'Summer', 'Fall', 'Winter', 'Unknown']).all()


def test_prepare_merged_missing_columns_errors():
    recipes_bad = pd.DataFrame([{"id": 1, "name": "X"}])  # missing 'type'
    interactions_bad = pd.DataFrame([{"recipe_id": 1, "rating": 5}])  # missing 'date'
    with pytest.raises(ValueError):
        prepare_merged_data(recipes_bad, interactions_bad, verbose=False)
