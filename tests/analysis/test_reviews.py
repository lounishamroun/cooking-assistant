"""Tests for top reviews analysis."""
from cooking_assistant.analysis.reviews import analyze_top_reviews_by_type_season
from cooking_assistant.config import RECIPE_TYPES, SEASONS


def test_analyze_top_reviews_basic(merged_df, recipes_df):
    results = analyze_top_reviews_by_type_season(
        merged_df=merged_df,
        recipes_df=recipes_df,
        top_n=10,
        verbose=False
    )

    assert 'combined_results' in results
    assert 'by_type_season' in results

    combined = results['combined_results']
    # Ensure essential columns present
    for col in ['season', 'type', 'recipe_id', 'total_reviews']:
        assert col in combined.columns

    # Check median stats integration when available
    if 'median_reviews_type_season' in combined.columns:
        assert combined['median_reviews_type_season'].notna().any()


def test_analyze_top_reviews_limits_top_n(merged_df, recipes_df):
    results = analyze_top_reviews_by_type_season(
        merged_df=merged_df,
        recipes_df=recipes_df,
        top_n=3,
        verbose=False
    )
    by_type_season = results['by_type_season']

    # For each type-season with data, max rows should be <=3
    for t in RECIPE_TYPES:
        seasons_map = by_type_season.get(t, {})
        for s in SEASONS:
            if s in seasons_map:
                assert len(seasons_map[s]) <= 3


def test_analyze_top_reviews_verbose_paths(merged_df, recipes_df, capsys):
    analyze_top_reviews_by_type_season(
        merged_df=merged_df,
        recipes_df=recipes_df,
        top_n=5,
        verbose=True
    )
    out = capsys.readouterr().out
    assert 'ANALYZING TOP 5 RECIPES' in out
    assert 'MEDIAN ANALYSIS' in out
