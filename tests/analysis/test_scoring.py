"""Tests for Bayesian scoring functions."""
import pandas as pd

from cooking_assistant.analysis.scoring import calculate_bayesian_scores, calculate_top_n_by_type
from cooking_assistant.config import BAYESIAN_PARAMS, SEASON_ORDER


def test_calculate_bayesian_scores_basic(spring_plat_df, params_plat):
    season_mean = spring_plat_df[spring_plat_df['rating'] > 0]['rating'].mean()
    scored = calculate_bayesian_scores(spring_plat_df, season_mean, params_plat)

    # Required columns
    for col in ['recipe_id', 'Q_Score_Bayesien', 'Poids_Popularite', 'Score_Final', 'reviews_in_season', 'avg_rating', 'valid_reviews']:
        assert col in scored.columns

    # Q_Score_Bayesien should be between 0 and 5
    assert (scored['Q_Score_Bayesien'] >= 0).all() and (scored['Q_Score_Bayesien'] <= 5).all()

    # Popularity weight bounded in [0,1]
    assert (scored['Poids_Popularite'] >= 0).all() and (scored['Poids_Popularite'] <= 1).all()

    # Final score monotonic wrt Q_Score_Bayesien when Poids_Popularite > 0
    positive_weight = scored[scored['Poids_Popularite'] > 0]
    assert (positive_weight['Score_Final'] <= positive_weight['Q_Score_Bayesien']).all()


def test_calculate_top_n_by_type_structure(merged_df, recipes_df):
    params = BAYESIAN_PARAMS['plat']
    tops = calculate_top_n_by_type(merged_df, recipes_df, 'plat', params, season_order=SEASON_ORDER, top_n=5, verbose=False)

    # Should have keys for seasons with data
    assert 'Spring' in tops

    spring_df = tops['Spring']
    assert len(spring_df) <= 5
    required = ['recipe_id', 'Q_Score_Bayesien', 'Poids_Popularite', 'Score_Final', 'reviews_in_season']
    for col in required:
        assert col in spring_df.columns


def test_top_n_handles_empty_season(recipes_df):
    # Construct merged with a season that has no data for desserts
    interactions = pd.DataFrame([
        {"recipe_id": 1, "rating": 5, "date": "2024-03-10"},  # Only plat
    ])
    from cooking_assistant.data.processor import prepare_merged_data
    merged = prepare_merged_data(recipes_df, interactions, verbose=False)

    params = BAYESIAN_PARAMS['dessert']
    tops = calculate_top_n_by_type(merged, recipes_df, 'dessert', params, season_order=SEASON_ORDER, top_n=5, verbose=False)

    # Dessert should have no Spring key because no data
    assert 'Spring' not in tops or len(tops['Spring']) == 0


def test_calculate_top_n_by_type_verbose_fallback(recipes_df):
    # Interactions only with rating=0 so season_mean fallback triggers
    import pandas as pd
    interactions = pd.DataFrame([
        {"recipe_id": 2, "rating": 0, "date": "2024-04-10"},  # dessert only zero rating
    ])
    from cooking_assistant.data.processor import prepare_merged_data
    merged = prepare_merged_data(recipes_df, interactions, verbose=False)
    from cooking_assistant.config import BAYESIAN_PARAMS, SEASON_ORDER
    params = BAYESIAN_PARAMS['dessert']
    tops = calculate_top_n_by_type(merged, recipes_df, 'dessert', params, season_order=SEASON_ORDER, top_n=5, verbose=True)
    # If data present, spring should exist even though rating=0 (will yield avg_rating 0)
    assert 'Spring' in tops

def test_calculate_bayesian_scores_missing_final_score_branch(spring_plat_df, params_plat):
    # Remove Poids_Popularite after calculation to force recompute path? Instead emulate missing Score_Final
    season_mean = spring_plat_df[spring_plat_df['rating'] > 0]['rating'].mean()
    scored = calculate_bayesian_scores(spring_plat_df, season_mean, params_plat)
    # Create DataFrame without Score_Final to simulate branch usage elsewhere
    reduced = scored.drop(columns=['Score_Final'])
    # Final score logic tested in save_combined_results_by_type when Score_Final missing
    from cooking_assistant.utils.results import save_combined_results_by_type
    all_results = {'plat': {'Spring': reduced}}
    paths = save_combined_results_by_type(all_results, results_path=None)
    assert 'plat' in paths
