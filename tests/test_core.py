import subprocess


def _write(repo, name, text):
    (repo / name).write_text(text, encoding="utf-8")


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


def test_set_repo_ok(core, git_repo):
    ok, msg = core.set_repo(str(git_repo))
    assert ok is True
    assert msg == ""
    assert core.REPO_ROOT == str(git_repo)


def test_set_repo_not_a_repo(core, tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    ok, msg = core.set_repo(str(plain))
    assert ok is False
    assert "git" in msg.lower()


def test_last_repo_is_a_config_key(core):
    assert "last_repo" in core.CONFIG_KEYS


def test_stage_files_adds_selected_and_resets_rest(core, git_repo):
    _write(git_repo, "a.txt", "aaa")
    _write(git_repo, "b.txt", "bbb")
    all_changed = [p for _, p in core.changed_files()]
    assert set(all_changed) == {"a.txt", "b.txt"}

    core.stage_files(["a.txt"], all_changed)

    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=git_repo, capture_output=True, text=True,
    ).stdout.split()
    assert staged == ["a.txt"]


def test_generate_message_uses_staged_diff(core, git_repo, monkeypatch):
    _write(git_repo, "a.txt", "hello world")
    core.stage_files(["a.txt"], ["a.txt"])

    captured = {}

    def fake_call_groq(api_key, system, user, model=None, temperature=0.3):
        captured["user"] = user
        captured["api_key"] = api_key
        return "feat: add a.txt"

    monkeypatch.setattr(core, "call_groq", fake_call_groq)

    msg = core.generate_message(["a.txt"], vietnamese=False, hint="add file",
                                api_key="gsk_test", model="m")
    assert msg == "feat: add a.txt"
    assert "hello world" in captured["user"]  # real staged diff fed to prompt
    assert "add file" in captured["user"]      # hint included
    assert captured["api_key"] == "gsk_test"


def test_generate_message_empty_selection_raises(core, git_repo):
    import pytest
    with pytest.raises(ValueError):
        core.generate_message([], vietnamese=False, hint=None,
                              api_key="k", model="m")
