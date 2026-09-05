"""Bo chon nhap so (che do `gcm` thuong) + cac helper cua man review."""
import subprocess

import pytest


def _write(repo, name, text):
    (repo / name).write_text(text, encoding="utf-8")


def _staged(repo):
    return subprocess.run(["git", "diff", "--cached", "--name-only"],
                          cwd=repo, capture_output=True, text=True).stdout.split()


@pytest.fixture
def answers(core, monkeypatch):
    """Thay input() bang chuoi cau tra loi dinh san; khong tty -> khong pager."""
    script = []
    monkeypatch.setattr("builtins.input", lambda prompt="": script.pop(0))
    monkeypatch.setattr(core, "tui_supported", lambda: False)
    monkeypatch.setattr(core, "term_size", lambda: (80, 24))
    return script


# ---- parse_pick ----

@pytest.mark.parametrize("raw, expected", [
    ("1 3", [1, 3]),
    ("2-4", [2, 3, 4]),
    ("1,3", [1, 3]),
    ("a", [1, 2, 3, 4, 5]),
    ("-2", [1, 3, 4, 5]),            # chi loai -> tat ca tru 2
    ("a -2 -4", [1, 3, 5]),
    ("1-3 -2", [1, 3]),
    ("-1-3", [4, 5]),                # loai ca khoang
    ("9", []),                       # ngoai pham vi -> khong chon gi
    ("", []),
])
def test_parse_pick(core, raw, expected):
    assert core.parse_pick(raw, 5) == expected


def test_parse_pick_rejects_garbage(core):
    assert core.parse_pick("abc", 5) is None
    assert core.parse_pick("1 x", 5) is None


# ---- select_files ----

def test_select_files_stages_exactly_the_chosen_set(core, git_repo, answers):
    for name in ("a.txt", "b.txt", "c.txt"):
        _write(git_repo, name, name)
    subprocess.run(["git", "add", "c.txt"], cwd=git_repo, check=True)  # ● san
    # git status liet ke file da stage truoc: 1=c.txt, 2=a.txt, 3=b.txt
    answers += ["2 3"]

    assert core.select_files() is True
    assert _staged(git_repo) == ["a.txt", "b.txt"]  # c.txt da bi unstage


def test_select_files_enter_keeps_staging_when_something_is_staged(
        core, git_repo, answers):
    _write(git_repo, "a.txt", "a")
    _write(git_repo, "b.txt", "b")
    subprocess.run(["git", "add", "a.txt"], cwd=git_repo, check=True)
    answers += [""]
    assert core.select_files() is False   # giu nguyen
    assert _staged(git_repo) == ["a.txt"]


def test_select_files_enter_means_all_when_nothing_staged(core, git_repo,
                                                          answers):
    _write(git_repo, "a.txt", "a")
    _write(git_repo, "b.txt", "b")
    answers += [""]
    assert core.select_files() is True
    assert _staged(git_repo) == ["a.txt", "b.txt"]


def test_select_files_exclude_and_invert(core, git_repo, answers):
    for name in ("a.txt", "b.txt", "c.txt"):
        _write(git_repo, name, name)
    answers += ["-2"]
    core.select_files()
    assert _staged(git_repo) == ["a.txt", "c.txt"]

    answers += ["i"]                      # dao: b len, a/c xuong
    core.select_files()
    assert _staged(git_repo) == ["b.txt"]


def test_select_files_diff_then_pick(core, git_repo, answers, capsys):
    _write(git_repo, "a.txt", "hello\n")
    answers += ["d 1", "d", "?", "xyz", "1"]  # xem diff, help, sai, roi chon

    assert core.select_files() is True
    out = capsys.readouterr()
    assert "+hello" in out.out            # diff file 1 duoc in (khong tty)
    assert "'-2' bo file 2" in out.out    # help day du sau '?'
    assert "khong hieu" in out.err
    assert _staged(git_repo) == ["a.txt"]


def test_select_files_quit(core, git_repo, answers):
    _write(git_repo, "a.txt", "a")
    answers += ["q"]
    with pytest.raises(SystemExit) as e:
        core.select_files()
    assert e.value.code == 0
    assert _staged(git_repo) == []


def test_select_files_t_switches_to_tui(core, git_repo, answers, monkeypatch):
    _write(git_repo, "a.txt", "a")
    monkeypatch.setattr(core, "tui_supported", lambda: True)
    monkeypatch.setattr(core, "tui_select", lambda default_all=False: "TUI")
    answers += ["t"]
    assert core.select_files() == "TUI"


# ---- helper cho man review ----

def test_classify_diff_and_stats(core, git_repo):
    _write(git_repo, "a.txt", "old\n")
    subprocess.run(["git", "add", "a.txt"], cwd=git_repo, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                    "commit", "-q", "-m", "a"], cwd=git_repo, check=True)
    _write(git_repo, "a.txt", "new\nmore\n")
    subprocess.run(["git", "add", "a.txt"], cwd=git_repo, check=True)

    entries = core.classify_diff(core.run_git(["diff", "--staged", "--no-color"]))
    assert ("del", "-old") in entries and ("add", "+new") in entries
    assert core.diff_stats() == (1, 2, 1)
    assert core.diff_stats(from_head=True) == (1, 1, 0)  # commit 'a' them 1 dong


def test_show_diff_text_prints_when_no_tty(core, monkeypatch, capsys):
    monkeypatch.setattr(core, "tui_supported", lambda: False)
    core.show_diff_text("t", "@@ -1 +1 @@\n-a\n+b\n")
    out = capsys.readouterr().out
    assert "--- t ---" in out and "-a" in out and "+b" in out
