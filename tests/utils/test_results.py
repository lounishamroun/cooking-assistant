"""Tests for results saving utilities."""
import pandas as pd

from cooking_assistant.utils.results import save_top_results, save_combined_results_by_type


def _build_scored_df(season: str):
    return pd.DataFrame([
        {
            'recipe_id': 1,
            'name': 'Salade de Printemps',
            'reviews_in_season': 2,
            'avg_rating': 4.5,
            'Q_Score_Bayesien': 4.4,
            'Poids_Popularite': 0.8,
            'Score_Final': 3.52,
            'Saison': season
        },
        {
            'recipe_id': 2,
            'name': 'Mousse au Chocolat',
            'reviews_in_season': 2,
            'avg_rating': 5.0,
            'Q_Score_Bayesien': 4.9,
            'Poids_Popularite': 0.7,
            'Score_Final': 3.43,
            'Saison': season
        },
    ])


def test_save_top_results_creates_file(tmp_results_dir):
    spring_df = _build_scored_df('Spring')
    summer_df = _build_scored_df('Summer')
    top_n_dict = {'Spring': spring_df, 'Summer': summer_df}

    path = save_top_results(top_n_dict, 'plat', results_path=tmp_results_dir, top_n=20)
    assert path.exists()
    df = pd.read_csv(path)
    # Columns renamed
    assert 'Nb_Reviews_Season' in df.columns
    assert 'Note_Moyenne' in df.columns


def test_save_combined_results_by_type(tmp_results_dir):
    spring_df = _build_scored_df('Spring')
    summer_df = _build_scored_df('Summer')

    all_results = {
        'plat': {'Spring': spring_df, 'Summer': summer_df},
        'dessert': {'Spring': spring_df.copy(), 'Summer': summer_df.copy()},
    }

    saved = save_combined_results_by_type(all_results, results_path=tmp_results_dir)

    # Should produce one file per provided type
    assert 'plat' in saved
    assert saved['plat'].exists()

    combo_df = pd.read_csv(saved['plat'])
    # Expected columns present after renaming
    expected_cols = {'ranking', 'recipe_id', 'name', 'Q_Score_Bayesien', 'Pop_Weight', 'Final_Score', 'reviews_in_season', 'Saison'}
    assert expected_cols.issubset(set(combo_df.columns))

    # Ranking starts at 1
    assert combo_df['ranking'].min() == 1


def test_save_combined_results_with_combined_score_column(tmp_results_dir):
    df = _build_scored_df('Spring')
    # Rename combined score to match special column name path
    df = df.rename(columns={'Score_Final': 'Q_Score_Bayesien_Poids_popularité'})
    all_results = {'plat': {'Spring': df}}
    saved = save_combined_results_by_type(all_results, results_path=tmp_results_dir)
    combo_df = pd.read_csv(saved['plat'])
    assert 'Final_Score' in combo_df.columns
