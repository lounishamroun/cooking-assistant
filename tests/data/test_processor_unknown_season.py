"""Tests processor branch for Unknown season counting."""
import pandas as pd
from cooking_assistant.data.processor import prepare_merged_data


def test_prepare_merged_unknown_season_branch(recipes_df, capsys):
    interactions = pd.DataFrame([
        {"recipe_id": 1, "rating": 5, "date": "not-a-date"},  # invalid date
    ])
    merged = prepare_merged_data(recipes_df, interactions, verbose=True)
    out = capsys.readouterr().out
    assert 'Unknown' in merged['season'].values
    assert 'Unknown' in out  # printed distribution line
