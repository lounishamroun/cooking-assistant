"""Tests additional branches in prepare_merged_data (distribution output)."""
from cooking_assistant.data.processor import prepare_merged_data


def test_prepare_merged_verbose_output(recipes_df, interactions_df, capsys):
    merged = prepare_merged_data(recipes_df, interactions_df, verbose=True)
    out = capsys.readouterr().out
    assert 'Distribution by recipe type:' in out
    assert 'Distribution by season:' in out
    assert len(merged) > 0
