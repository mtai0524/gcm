def test_module_loads(core):
    assert core.VERSION
    assert callable(core.changed_files)


def test_save_config_creates_and_updates(core, tmp_path, monkeypatch):
    cfg = tmp_path / "config"
    monkeypatch.setattr(core, "CONFIG_PATH", str(cfg))

    core.save_config("api_key", "gsk_abc")
    assert "api_key = gsk_abc" in cfg.read_text(encoding="utf-8")

    core.save_config("api_key", "gsk_xyz")  # update in place
    text = cfg.read_text(encoding="utf-8")
    assert "gsk_xyz" in text and "gsk_abc" not in text
    assert text.count("api_key") == 1  # not duplicated


def test_save_config_preserves_other_lines(core, tmp_path, monkeypatch):
    cfg = tmp_path / "config"
    cfg.write_text("# comment\nlang = vi\n", encoding="utf-8")
    monkeypatch.setattr(core, "CONFIG_PATH", str(cfg))

    core.save_config("api_key", "gsk_1")
    text = cfg.read_text(encoding="utf-8")
    assert "# comment" in text
    assert "lang = vi" in text
    assert "api_key = gsk_1" in text
