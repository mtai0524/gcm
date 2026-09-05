"""GUI Tkinter: chay that (an cua so), thao tac qua API cua GcmApp.

Can man hinh + tkinter; khong co thi skip. Moi test dung repo tam + config tam,
khong dung toi ~/.config/gcm cua may.
"""
import subprocess
import sys
import time
from pathlib import Path

import pytest

tk = pytest.importorskip("tkinter")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import gcm_gui  # noqa: E402


def _write(repo, name, text):
    (repo / name).write_text(text, encoding="utf-8")


def _staged(repo):
    return subprocess.run(["git", "diff", "--cached", "--name-only"],
                          cwd=repo, capture_output=True, text=True).stdout.split()


def _pump(app, done, timeout=15):
    """Chay vong lap su kien Tk den khi done() True (thread nen + after())."""
    t0 = time.time()
    while not done():
        app.update()
        if time.time() - t0 > timeout:
            raise AssertionError("GUI khong xong trong thoi gian cho")
        time.sleep(0.02)


@pytest.fixture
def app(core, git_repo, tmp_path, monkeypatch):
    monkeypatch.setattr(core, "CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.setattr(core, "GUI_MODE", True)  # loi -> GcmError nhu khi chay that
    core.CONFIG = core.load_config()
    monkeypatch.setattr(gcm_gui.messagebox, "showerror",
                        lambda *a, **k: None)  # khong chan test bang hop thoai
    a, last = None, None
    for _ in range(3):  # Tk tren Windows thi thoang khong tim thay init.tcl
        try:
            a = gcm_gui.GcmApp(core)
            break
        except tk.TclError as e:
            last = e
            time.sleep(0.2)
    if a is None:
        pytest.skip(f"khong co man hinh: {last}")
    a.withdraw()
    yield a
    a.destroy()


def test_open_repo_lists_files_prestaged_ticked(app, git_repo):
    _write(git_repo, "a.txt", "aaa")
    _write(git_repo, "b.txt", "bbb")
    subprocess.run(["git", "add", "a.txt"], cwd=git_repo, check=True)

    app._open_repo(str(git_repo))
    assert app._all_paths() == ["a.txt", "b.txt"]
    assert app._selected() == ["a.txt"]          # da stage san -> tick san
    assert "1/2" in app.count_var.get()
    assert app.branch_var.get().startswith("⎇ ")
    assert "b.txt" in app.tree.item("1", "values")[2]


def test_no_staged_files_means_everything_ticked(app, git_repo):
    _write(git_repo, "a.txt", "aaa")
    _write(git_repo, "b.txt", "bbb")
    app._open_repo(str(git_repo))
    assert app._selected() == ["a.txt", "b.txt"]

    app._tick_none()
    assert app._selected() == []
    app._invert()
    assert app._selected() == ["a.txt", "b.txt"]
    app._toggle("0")
    assert app._selected() == ["b.txt"]
    assert app.tree.set("0", "tick") == "☐"


def test_diff_preview_follows_selection(app, git_repo):
    _write(git_repo, "new.txt", "hello\n")
    app._open_repo(str(git_repo))
    app.tree.selection_set("0")
    app._preview_selected()
    body = app.diff_text.get("1.0", "end")
    assert "+hello" in body
    assert "new.txt" in app.diff_title_var.get()
    assert "add" in app.diff_text.tag_names("1.0")  # dong them duoc to mau


def test_generate_stages_ticked_files_and_fills_message(app, git_repo, core,
                                                        monkeypatch):
    _write(git_repo, "a.txt", "aaa")
    _write(git_repo, "b.txt", "bbb")
    seen = {}

    def fake_call_groq(api_key, system, user, model=None, temperature=0.3):
        seen["temperature"] = temperature
        return "feat: add a"

    monkeypatch.setattr(core, "call_groq", fake_call_groq)
    monkeypatch.setattr(core, "resolve_api_key", lambda: "gsk_test")
    app._open_repo(str(git_repo))
    app._toggle("1")  # bo tick b.txt

    app._generate()
    _pump(app, lambda: not app.busy)
    assert app.msg_text.get("1.0", "end").strip() == "feat: add a"
    assert _staged(git_repo) == ["a.txt"]   # chi stage file dang tick
    assert seen["temperature"] == 0.3

    app._generate(regen=True)               # sinh lai -> sang tao hon
    _pump(app, lambda: not app.busy)
    assert seen["temperature"] == pytest.approx(0.6)


def test_commit_creates_commit_and_reloads(app, git_repo):
    _write(git_repo, "a.txt", "aaa")
    app._open_repo(str(git_repo))
    app._set_message("feat: add a")

    app._commit()
    _pump(app, lambda: not app.busy)
    log = subprocess.run(["git", "log", "--oneline"], cwd=git_repo,
                         capture_output=True, text=True).stdout.splitlines()
    assert len(log) == 2 and "feat: add a" in log[0]
    assert app._all_paths() == []                     # da tai lai, tree sach
    assert app.msg_text.get("1.0", "end").strip() == ""
    assert "Đã commit" in app.status_var.get()


def test_core_error_shows_in_status_not_crash(app, git_repo, core, monkeypatch):
    _write(git_repo, "a.txt", "aaa")
    monkeypatch.setattr(core, "resolve_api_key", lambda: "gsk_test")

    def boom(*a, **k):
        core.fail("Groq API HTTP 401: bad key", "key sai hoac het han.")

    monkeypatch.setattr(core, "generate_message", boom)
    app._open_repo(str(git_repo))

    app._generate()
    _pump(app, lambda: not app.busy)
    assert app.status_var.get().startswith("Lỗi: Groq API HTTP 401")
    assert str(app.gen_btn.cget("state")) == "normal"  # nut mo lai sau loi


def test_summary_length_warning(app):
    app._set_message("x" * 80 + "\n\nbody")
    assert "hơi dài" in app.summary_var.get()
    app._set_message("feat: short")
    assert "hơi dài" not in app.summary_var.get()
