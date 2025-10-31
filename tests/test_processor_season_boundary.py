import pandas as pd


def test_prepare_merged_season_boundary():
    from cooking_assistant.data.processor import prepare_merged_data
    recipes = pd.DataFrame([
        {'id': 10, 'name': 'Boundary', 'type': 'plat'}
    ])
    interactions = pd.DataFrame([
        {'recipe_id': 10, 'rating': 5, 'date': '2024-03-21'},  # First day of Spring per logic
        {'recipe_id': 10, 'rating': 4, 'date': '2024-06-21'},  # First day of Summer per logic
    ])
    merged = prepare_merged_data(recipes, interactions, verbose=False)
    assert set(merged['season']) == {'Spring', 'Summer'}
    assert len(merged) == 2
    assert merged['season'].iloc[0] == 'Spring'
    assert merged['season'].iloc[1] == 'Summer'
