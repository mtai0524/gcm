"""Cac moc trong core ma GUI dua vao: fail()/GcmError, diff_entries, commit_simple."""
import subprocess

import pytest


def _write(repo, name, text):
    (repo / name).write_text(text, encoding="utf-8")


def test_fail_exits_in_cli_mode_and_raises_in_gui_mode(core, monkeypatch, capsys):
    monkeypatch.setattr(core, "GUI_MODE", False)
    with pytest.raises(SystemExit) as e:
        core.fail("hong roi", "goi y sua")
    assert e.value.code == 1
    assert "hong roi" in capsys.readouterr().err

    monkeypatch.setattr(core, "GUI_MODE", True)
    with pytest.raises(core.GcmError) as e:
        core.fail("hong roi", "goi y sua")
    assert "hong roi" in str(e.value) and "goi y sua" in str(e.value)


def test_run_git_failure_becomes_gcm_error_in_gui_mode(core, git_repo,
                                                       monkeypatch):
    monkeypatch.setattr(core, "GUI_MODE", True)
    with pytest.raises(core.GcmError):
        core.run_git(["checkout", "nhanh-khong-ton-tai"])


def test_diff_entries_kinds(core, git_repo):
    _write(git_repo, "a.txt", "old\n")
    subprocess.run(["git", "add", "a.txt"], cwd=git_repo, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                    "commit", "-q", "-m", "a"], cwd=git_repo, check=True)
    _write(git_repo, "a.txt", "new\n")
    title, entries = core.diff_entries(" M", "a.txt")
    kinds = {k for k, _ in entries}
    assert title == "diff a.txt"
    assert {"meta", "head", "hunk", "add", "del"} <= kinds
    assert ("del", "-old") in entries and ("add", "+new") in entries

    _write(git_repo, "n.txt", "x\n")
    title, entries = core.diff_entries("??", "n.txt")
    assert entries == [("add", "+x")]
    assert "file moi" in title

    # diff_lines (TUI) chi la diff_entries + mau: cung so dong, cung noi dung
    _, colored = core.diff_lines("??", "n.txt")
    assert len(colored) == 1 and "+x" in colored[0]


def test_commit_simple_returns_output(core, git_repo):
    _write(git_repo, "a.txt", "aaa")
    subprocess.run(["git", "add", "a.txt"], cwd=git_repo, check=True)
    ok, out = core.commit_simple("feat: a")
    assert ok is True and "feat: a" in out

    ok, out = core.commit_simple("feat: nothing")  # khong co gi de commit
    assert ok is False and out


def test_generate_message_passes_temperature(core, git_repo, monkeypatch):
    _write(git_repo, "a.txt", "aaa")
    core.stage_files(["a.txt"], ["a.txt"])
    seen = {}

    def fake(api_key, system, user, model=None, temperature=0.3):
        seen["t"] = temperature
        return "ok"

    monkeypatch.setattr(core, "call_groq", fake)
    core.generate_message(["a.txt"], False, None, "k", "m", temperature=0.9)
    assert seen["t"] == 0.9
