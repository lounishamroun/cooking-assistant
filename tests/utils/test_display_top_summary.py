"""Tests display_top_summary to ensure it iterates and prints without error."""
import pandas as pd
from cooking_assistant.utils.results import display_top_summary


def test_display_top_summary_runs(capsys):
    # Minimal data for two seasons
    spring = pd.DataFrame([
        {'recipe_id': 1, 'name': 'Salade', 'Score_Final': 3.0, 'avg_rating': 4.0}
    ])
    summer = pd.DataFrame([
        {'recipe_id': 2, 'name': 'Glace', 'Score_Final': 2.5, 'avg_rating': 3.5}
    ])
    top_dict = {'Spring': spring, 'Summer': summer}
    display_top_summary(top_dict, 'plat', season_order=['Spring', 'Summer'], show_top=3)
    out = capsys.readouterr().out
    assert 'TOP 3 RECIPES BY SEASON - PLAT' in out
    assert 'SPRING' in out
    assert 'SUMMER' in out
