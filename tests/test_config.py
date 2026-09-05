"""Config layer: mac dinh trong code, config.json chi chua phan nguoi dung doi."""
import json

import pytest


@pytest.fixture
def cfg_path(core, tmp_path, monkeypatch):
    """Tro CONFIG_PATH vao tmp + nap lai CONFIG (khong dung file that cua may)."""
    path = tmp_path / "gcm" / "config.json"
    monkeypatch.setattr(core, "CONFIG_PATH", str(path))
    monkeypatch.setattr(core, "LEGACY_CONFIG_PATH", str(path.parent / "config"))
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GCM_MODEL", raising=False)
    core.CONFIG = core.load_config()
    return path


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


# ---- doc / lop uu tien ----

def test_defaults_apply_without_file(core, cfg_path):
    assert not cfg_path.exists()
    assert core.cfg("model") == core.DEFAULT_MODEL
    assert core.cfg("push") == "ask"
    assert core.cfg("tui") is False
    assert core.config_source("model") == "mac dinh"


def test_file_overrides_default(core, cfg_path):
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text(json.dumps({"lang": "vi", "tui": True}), encoding="utf-8")
    core.CONFIG = core.load_config()
    assert core.cfg("lang") == "vi"
    assert core.cfg("tui") is True
    assert core.config_source("lang") == "file"
    assert core.config_source("push") == "mac dinh"  # key vang mat -> built-in


def test_env_overrides_file(core, cfg_path, monkeypatch):
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text(json.dumps({"model": "from-file"}), encoding="utf-8")
    monkeypatch.setenv("GCM_MODEL", "from-env")
    core.CONFIG = core.load_config()
    assert core.cfg("model") == "from-env"
    assert core.config_source("model") == "env GCM_MODEL"


def test_comment_keys_and_empty_values_ignored(core, cfg_path):
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text(json.dumps({
        "//": "ghi chu", "//lang": "vi | en", "_note": "cung la ghi chu",
        "lang": "",           # de trong = chua dat -> theo mac dinh
    }), encoding="utf-8")
    overrides, warnings = core.read_config_file()
    assert overrides == {}
    assert warnings == []


def test_bad_json_falls_back_to_defaults_with_warning(core, cfg_path):
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text('{"lang": "vi",}', encoding="utf-8")  # dau phay thua
    overrides, warnings = core.read_config_file()
    assert overrides == {}
    assert warnings and "JSON" in warnings[0]
    core.CONFIG = core.load_config()
    assert core.cfg("lang") == "en"  # van chay duoc bang mac dinh


def test_invalid_value_is_rejected_not_silently_used(core, cfg_path):
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text(json.dumps({"push": "yolo", "tui": "maybe"}),
                        encoding="utf-8")
    overrides, warnings = core.read_config_file()
    assert overrides == {}
    assert len(warnings) == 2
    core.CONFIG = core.load_config()
    assert core.cfg("push") == "ask"


def test_unknown_key_warns_but_keeps_the_rest(core, cfg_path):
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text(json.dumps({"lang": "vi", "colour": "red"}),
                        encoding="utf-8")
    overrides, warnings = core.read_config_file()
    assert overrides == {"lang": "vi"}
    assert any("colour" in w for w in warnings)


# ---- ghi ----

def test_save_config_creates_file_and_updates_in_place(core, cfg_path):
    core.save_config("api_key", "gsk_abc")
    assert read(cfg_path)["api_key"] == "gsk_abc"
    assert core.cfg("api_key") == "gsk_abc"  # CONFIG duoc nap lai ngay

    core.save_config("api_key", "gsk_xyz")
    assert read(cfg_path) == {"api_key": "gsk_xyz"}  # khong nhan doi key


def test_save_config_keeps_other_keys_and_comments(core, cfg_path):
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text(json.dumps({"//": "ghi chu", "lang": "vi"}),
                        encoding="utf-8")
    core.save_config("api_key", "gsk_1")
    data = read(cfg_path)
    assert data["//"] == "ghi chu"
    assert data["lang"] == "vi"
    assert data["api_key"] == "gsk_1"


def test_save_config_drops_value_equal_to_default(core, cfg_path):
    core.save_config("lang", "vi")
    assert read(cfg_path)["lang"] == "vi"
    core.save_config("lang", "en")  # = mac dinh -> khong ghim vao file nua
    assert "lang" not in read(cfg_path)
    assert core.cfg("lang") == "en"


def test_save_config_coerces_and_validates(core, cfg_path):
    core.save_config("tui", "true")
    assert read(cfg_path)["tui"] is True  # bool that, khong phai chuoi
    with pytest.raises(ValueError):
        core.save_config("push", "sometimes")
    with pytest.raises(KeyError):
        core.save_config("nope", "x")


def test_unset_config_returns_to_default(core, cfg_path):
    core.save_config("model", "custom-model")
    assert core.unset_config("model") is True
    assert core.cfg("model") == core.DEFAULT_MODEL
    assert core.unset_config("model") is False  # khong con gi de bo


def test_prune_default_config_removes_redundant_keys(core, cfg_path):
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text(json.dumps({
        "//": "ghi chu",
        "api_key": "gsk_mine",
        "coauthor": core.DEFAULT_COAUTHOR,   # trung mac dinh -> bo
        "model": core.DEFAULT_MODEL,         # trung mac dinh -> bo
        "lang": "vi",                        # khac mac dinh -> giu
        "last_repo": "C:/x",                 # khong co mac dinh -> giu
    }), encoding="utf-8")

    assert sorted(core.prune_default_config()) == ["coauthor", "model"]
    data = read(cfg_path)
    assert data == {"//": "ghi chu", "api_key": "gsk_mine", "lang": "vi",
                    "last_repo": "C:/x"}
    assert core.prune_default_config() == []  # idempotent


# ---- file mau + migrate ----

def test_ensure_user_config_creates_usable_files(core, cfg_path):
    assert core.ensure_user_config() is True
    assert json.loads(cfg_path.read_text(encoding="utf-8"))["api_key"] == ""
    assert (cfg_path.parent / "config.example.json").exists()
    assert (cfg_path.parent / "system_prompt.example.md").exists()
    # File vua tao khong bat san key nao -> moi mac dinh van lay tu code
    assert core.read_config_file()[0] == {}


def test_ensure_user_config_does_not_overwrite(core, cfg_path):
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text('{"api_key": "gsk_mine"}', encoding="utf-8")
    assert core.ensure_user_config() is False
    assert read(cfg_path) == {"api_key": "gsk_mine"}


def test_config_example_covers_every_key(core):
    data = core.config_example_data()
    for key in core.CONFIG_KEYS:
        assert key in data
        assert f"//{key}" in data  # moi key deu co dong mo ta di kem


def test_migrate_legacy_key_value_file(core, cfg_path):
    legacy = cfg_path.parent / "config"
    legacy.parent.mkdir(parents=True)
    legacy.write_text(
        "# comment\n"
        "api_key = gsk_old\n"
        "lang = vi\n"
        "tui = true\n"
        f"model = {core.DEFAULT_MODEL}\n",  # trung mac dinh -> khong chuyen
        encoding="utf-8",
    )
    assert core.migrate_legacy_config() == ["api_key", "lang", "tui"]
    data = read(cfg_path)
    assert data["api_key"] == "gsk_old"
    assert data["tui"] is True
    assert "model" not in data
    assert not legacy.exists()
    assert (legacy.parent / "config.migrated").exists()


def test_migrate_legacy_single_line_key_file(core, cfg_path):
    legacy = cfg_path.parent / "config"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("gsk_justthekey\n", encoding="utf-8")
    assert core.migrate_legacy_config() == ["api_key"]
    assert read(cfg_path)["api_key"] == "gsk_justthekey"


def test_migrate_skipped_when_json_exists(core, cfg_path):
    legacy = cfg_path.parent / "config"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("api_key = gsk_old\n", encoding="utf-8")
    cfg_path.write_text('{"api_key": "gsk_new"}', encoding="utf-8")
    assert core.migrate_legacy_config() == []
    assert read(cfg_path)["api_key"] == "gsk_new"
    assert legacy.exists()  # file cu giu nguyen, khong dong vao
