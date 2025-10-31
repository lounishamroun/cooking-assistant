"""Smoke test for pipeline main module import and callable interface.
Does not run full Kaggle download to keep tests fast.
"""

def test_pipeline_main_importable():
    from app.main import main
    assert callable(main)
