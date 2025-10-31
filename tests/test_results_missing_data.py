import pandas as pd

def test_save_combined_results_empty(tmp_path):
    from cooking_assistant.utils.results import save_combined_results_by_type
    # Provide empty dict (no data per type) should not crash
    saved = save_combined_results_by_type({}, results_path=tmp_path)
    assert saved == {}


def test_save_combined_results_partial(tmp_path):
    from cooking_assistant.utils.results import save_combined_results_by_type
    # Build minimal seasonal data for one type with one season
    df_season = pd.DataFrame({
        'recipe_id': [1, 2],
        'name': ['A', 'B'],
        'Q_Score_Bayesien': [0.8, 0.7],
        'Poids_Popularite': [0.9, 0.85],
        'reviews_in_season': [5, 3],
    })
    all_results = {
        'plat': {'Spring': df_season}
    }
    saved = save_combined_results_by_type(all_results, results_path=tmp_path)
    assert 'plat' in saved
    out = saved['plat']
    assert out.exists()
    loaded = pd.read_csv(out)
    # ranking column should exist after harmonization
    assert 'ranking' in loaded.columns
    assert 'Final_Score' in loaded.columns or 'Q_Score_Bayesien' in loaded.columns
