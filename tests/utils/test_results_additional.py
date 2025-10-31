"""Additional tests for results utility covering more branches."""
import pandas as pd
from cooking_assistant.utils.results import display_top_summary, save_combined_results_by_type


def test_display_top_summary_shows_ellipsis(capsys):
    # Build DataFrame with > show_top rows
    rows = []
    for i in range(6):
        rows.append({'recipe_id': i+1, 'name': f'R{i+1}', 'Score_Final': 1.0/(i+1), 'avg_rating': 4.0})
    df = pd.DataFrame(rows)
    top_dict = {'Spring': df}
    display_top_summary(top_dict, 'plat', season_order=['Spring'], show_top=3)
    out = capsys.readouterr().out
    assert '... and' in out


def test_save_combined_results_no_data_branch(tmp_path):
    # Provide empty data for one type and real for another to hit no-data path
    df = pd.DataFrame([
        {'recipe_id': 1, 'name': 'A', 'reviews_in_season': 1, 'Q_Score_Bayesien': 4.0, 'Poids_Popularite': 0.5}
    ])
    all_results = {
        'plat': {},  # triggers no data branch
        'dessert': {'Spring': df}  # triggers compute branch (without Score_Final)
    }
    save_combined_results_by_type(all_results, results_path=tmp_path)
    # Dessert file should exist
    assert (tmp_path / 'top20_dessert_for_each_season.csv').exists()