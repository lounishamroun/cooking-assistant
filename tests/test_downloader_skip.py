from pathlib import Path
import pandas as pd


def test_downloader_skip_existing(monkeypatch, tmp_path):
    """If timestamped files for both stems exist, downloader.main should skip without calling kagglehub."""
    stems = ['RAW_recipes', 'RAW_interactions']
    for stem in stems:
        existing = tmp_path / f"{stem}_20250101-000000.csv"
        existing.write_text("id,name\n1,Test")

    from cooking_assistant.data import downloader
    monkeypatch.setattr(downloader, 'RAW_DIR', tmp_path)
    monkeypatch.setattr(downloader, 'RAW_DATA_DIR', tmp_path)

    # Ensure detection sees existing copies
    for stem in stems:
        assert downloader.has_any_timestamped_copy(stem) is True

    # Monkeypatch kagglehub.load_dataset to raise if called (it should NOT be)
    def fake_load_dataset(*args, **kwargs):
        raise AssertionError("kagglehub.load_dataset should not be called when files already exist")
    monkeypatch.setattr(downloader.kagglehub, 'load_dataset', fake_load_dataset)

    # Run main; should skip both files without triggering fake_load_dataset
    downloader.main()
