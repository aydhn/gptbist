from pathlib import Path


def test_tmp_data_dir_is_isolated(tmp_data_dir):
    assert tmp_data_dir.exists()
    assert Path("data").resolve() != tmp_data_dir.resolve()


def test_settings_factory_overrides(settings_factory, tmp_data_dir):
    s = settings_factory(RUNTIME_MAX_ITERATIONS="3")
    assert Path(s.DATA_DIR) == tmp_data_dir
    assert s.RUNTIME_MAX_ITERATIONS == 3
