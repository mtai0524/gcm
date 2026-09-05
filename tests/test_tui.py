"""TUI chon file: helper thuan + chay tui_select bang chuoi phim gia lap."""
import subprocess

import pytest


def _write(repo, name, text):
    (repo / name).write_text(text, encoding="utf-8")


def _staged(repo):
    return subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=repo, capture_output=True, text=True,
    ).stdout.split()


@pytest.fixture
def keys(core, monkeypatch):
    """Thay read_key bang chuoi phim dinh san; man hinh co dinh 80x24."""
    script = []
    monkeypatch.setattr(core, "read_key", lambda: script.pop(0))
    monkeypatch.setattr(core, "term_size", lambda: (80, 24))
    monkeypatch.setattr(core._Screen, "render", staticmethod(lambda lines: None))
    return script


# ---- helper thuan ----

def test_shorten_path_keeps_filename(core):
    p = "src/Web/Components/Pages/Reports/Charts/Chart.razor"
    out = core.shorten_path(p, 30)
    assert out.endswith("/Chart.razor")
    assert "…" in out
    assert core.text_width(out) <= 30
    assert core.shorten_path("short.py", 30) == "short.py"  # khong dung toi


def test_clip_text_counts_wide_chars(core):
    assert core.text_width("日本") == 4
    assert core.clip_text("日本語テキスト", 5) == "日本…"
    assert core.clip_text("abc", 3) == "abc"


def test_clip_ansi_ignores_escape_codes(core):
    colored = "\033[32mhello\033[0m world"  # to mau tay: c() tat mau khi khong tty
    out = core.clip_ansi(colored, 7)
    assert "\033[32m" in out            # ma mau giu nguyen
    assert out.endswith("\033[0m")      # dong mau khi cat
    assert "wor" not in out             # cat dung 7 cot nhin thay
    assert "hello w" in out.replace("\033[32m", "").replace("\033[0m", "")


def test_scroll_window_keeps_cursor_visible(core):
    assert core._scroll_window(cursor=0, top=0, total=5, height=10) == 0
    assert core._scroll_window(cursor=15, top=0, total=50, height=10) == 6
    assert core._scroll_window(cursor=3, top=6, total=50, height=10) == 3
    assert core._scroll_window(cursor=49, top=0, total=50, height=10) == 40


def test_read_key_esc_sequences_are_mapped(core):
    assert core._KEY_ESC["[A"] == "up"
    assert core._KEY_ESC["[6~"] == "pgdn"
    assert core._KEY_CHARS["\x1b"] == "quit"


# ---- diff trong pager ----

def test_diff_lines_new_file_and_binary(core, git_repo):
    _write(git_repo, "new.txt", "line1\nline2\n")
    title, lines = core.diff_lines("??", "new.txt")
    assert "2 dong" in title
    assert any("line1" in ln for ln in lines)

    (git_repo / "bin.dat").write_bytes(b"\x00\x01\x02")
    _, lines = core.diff_lines("??", "bin.dat")
    assert "nhi phan" in lines[0]


def test_diff_lines_modified_file_colors_by_prefix(core, git_repo,
                                                   monkeypatch):
    _write(git_repo, "a.txt", "old\n")
    subprocess.run(["git", "add", "a.txt"], cwd=git_repo, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                    "commit", "-q", "-m", "a"], cwd=git_repo, check=True)
    _write(git_repo, "a.txt", "new\n")
    monkeypatch.setattr(core, "c",
                        lambda t, code: f"\033[{code}m{t}\033[0m")
    _, lines = core.diff_lines(" M", "a.txt")
    assert any(ln.startswith("\033[31m-old") for ln in lines)
    assert any(ln.startswith("\033[32m+new") for ln in lines)


# ---- tui_select bang phim gia lap ----

def test_tui_select_stages_only_ticked_files(core, git_repo, keys):
    _write(git_repo, "a.txt", "aaa")
    _write(git_repo, "b.txt", "bbb")
    _write(git_repo, "c.txt", "ccc")
    keys += ["space", "down", "down", "space", "enter"]  # tick a va c

    assert core.tui_select() is True
    assert _staged(git_repo) == ["a.txt", "c.txt"]


def test_tui_select_unticking_a_prestaged_file_unstages_it(core, git_repo,
                                                          keys):
    _write(git_repo, "a.txt", "aaa")
    _write(git_repo, "b.txt", "bbb")
    subprocess.run(["git", "add", "a.txt"], cwd=git_repo, check=True)
    assert _staged(git_repo) == ["a.txt"]
    keys += ["space", "down", "space", "enter"]  # bo tick a, tick b

    core.tui_select()
    assert _staged(git_repo) == ["b.txt"]


def test_tui_select_all_invert_and_wraparound(core, git_repo, keys):
    for name in ("a.txt", "b.txt", "c.txt"):
        _write(git_repo, name, name)
    keys += ["all", "invert", "up", "space", "enter"]  # all -> none -> tick c

    core.tui_select()
    assert _staged(git_repo) == ["c.txt"]


def test_tui_select_enter_with_nothing_ticked_stays_open(core, git_repo, keys):
    _write(git_repo, "a.txt", "aaa")
    keys += ["enter", "space", "enter"]  # enter dau tien chi nhac, khong thoat

    assert core.tui_select() is True
    assert _staged(git_repo) == ["a.txt"]
    assert keys == []  # da tieu thu het phim -> khong thoat som


def test_tui_select_quit_exits_zero_without_staging(core, git_repo, keys):
    _write(git_repo, "a.txt", "aaa")
    keys += ["space", "quit"]
    with pytest.raises(SystemExit) as e:
        core.tui_select()
    assert e.value.code == 0
    assert _staged(git_repo) == []


def test_tui_select_diff_key_opens_pager_and_returns(core, git_repo, keys):
    _write(git_repo, "a.txt", "aaa")
    keys += ["diff", "down", "pgdn", "quit",  # trong pager: cuon roi thoat
             "space", "enter"]
    assert core.tui_select() is True
    assert _staged(git_repo) == ["a.txt"]


def test_tui_select_default_all_preticks_everything(core, git_repo, keys):
    _write(git_repo, "a.txt", "aaa")
    _write(git_repo, "b.txt", "bbb")
    keys += ["enter"]
    core.tui_select(default_all=True)
    assert _staged(git_repo) == ["a.txt", "b.txt"]
