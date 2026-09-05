"""gcm GUI - cua so Tkinter cho gcm.

Nhan `core` (module gcm) qua run_gui(core); KHONG import gcm truc tiep (file
`gcm` khong co duoi .py). Bo cuc:

    [repo] [nhanh ↑n]                              [↻ Tai lai] [Chon repo…]
    +-- File thay doi (tick) --+-- Commit message (sua duoc) -------------+
    |  ☑ modified  src/app.py  |                                          |
    |  ☐ new       README.md   +-- Diff cua file dang chon ---------------+
    |                          |  + them / - bot (to mau)                 |
    +--------------------------+------------------------------------------+
    Goi y: [......]  (vi)(en)  ☐ Push   [⚡ Sinh] [🔁 Sinh lai] [✓ Commit]
    trang thai .........................................  [==== dang chay]

Moi thao tac git/API chay o thread nen (cua so khong dong bang), ket qua tra
ve main thread qua after(). Loi cua core (GcmError) hien o thanh trang thai
va hop thoai thay vi bien mat trong console da an.
"""

import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, font as tkfont, messagebox, simpledialog, ttk

OK, ERR, MUTED = "#1a7f37", "#cf222e", "#57606a"
STATUS_COLORS = {
    "new": "#1a7f37", "added": "#1a7f37", "modified": "#9a6700",
    "deleted": "#cf222e", "renamed": "#8250df", "copied": "#8250df",
    "conflict": "#cf222e",
}
DIFF_TAGS = {  # loai dong (core.diff_entries) -> (mau chu, mau nen)
    "add": ("#1a7f37", "#e6ffec"), "del": ("#cf222e", "#ffebe9"),
    "hunk": ("#0969da", "#ddf4ff"), "head": ("#24292f", "#f6f8fa"),
    "meta": ("#8c959f", None), "note": ("#8c959f", None), "ctx": (None, None),
}
MAX_DIFF_LINES = 3000
SUMMARY_LIMIT = 72  # do dai dong tieu de commit nen giu duoi muc nay
_MONO_FAMILY = None  # cache: tkfont.families() cham (~1s tren Windows)


def run_gui(core):
    _enable_dpi_awareness()
    app = GcmApp(core)
    app.mainloop()


def _enable_dpi_awareness():
    """Windows: bao he thong ta tu lo DPI -> chu/khung sac net tren man HiDPI.

    Khong co buoc nay Tk bi phong to mo (bitmap scaling). Goi truoc khi tao
    cua so Tk. Loi (da bat san boi manifest cua exe, Windows cu...) thi bo qua.
    """
    if os.name != "nt":
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def status_name(code):
    """Ma 2 ky tu cua `git status --porcelain` -> ten de doc."""
    if code == "??":
        return "new"
    flags = code.replace(" ", "")
    for ch, name in (("U", "conflict"), ("D", "deleted"), ("R", "renamed"),
                     ("C", "copied"), ("A", "added"), ("M", "modified")):
        if ch in flags:
            return name
    return code.strip() or "?"


class GcmApp(tk.Tk):
    def __init__(self, core):
        super().__init__()
        self.core = core
        self.busy = False
        self.temperature = 0.3   # "Sinh lai" tang dan nhu phim [r] ben CLI
        self.rows = {}           # iid -> {"code", "path", "ticked"}
        # Thread nen KHONG dung Tk truc tiep: bo ket qua vao queue, main
        # thread poll bang after() -> an toan ca khi khong o trong mainloop.
        self._queue = queue.Queue()
        self.title(f"gcm v{core.VERSION}")
        self._scale = self._dpi_scale()
        self.geometry(f"{self._px(1040)}x{self._px(680)}")
        self.minsize(self._px(780), self._px(500))
        self.mono = self._mono_font()

        self._build_repo_bar()
        self._build_body()
        self._build_actions()
        self._build_status()
        self._bind_keys()
        self._set_repo_state(False)
        self.after(50, self._poll_queue)

        last = core.cfg("last_repo")
        if last and os.path.isdir(last):
            self._open_repo(last)

    # ---- do rong / font theo DPI ----
    def _dpi_scale(self):
        try:
            return max(1.0, self.winfo_fpixels("1i") / 96.0)
        except tk.TclError:
            return 1.0

    def _px(self, n):
        return int(n * self._scale)

    def _mono_font(self):
        global _MONO_FAMILY
        base = tkfont.nametofont("TkFixedFont")
        if _MONO_FAMILY is None:
            families = set(tkfont.families(self))
            _MONO_FAMILY = next(
                (f for f in ("Cascadia Mono", "Consolas", "Menlo",
                             "DejaVu Sans Mono", "Courier New")
                 if f in families), "")
        if _MONO_FAMILY:
            return tkfont.Font(family=_MONO_FAMILY, size=base.cget("size"))
        return base

    # ---- layout ----
    def _build_repo_bar(self):
        bar = ttk.Frame(self, padding=(10, 8, 10, 4))
        bar.pack(fill="x")
        ttk.Label(bar, text="📁").grid(row=0, column=0)
        self.repo_var = tk.StringVar(value="(chưa chọn repo — bấm Chọn repo…)")
        ttk.Label(bar, textvariable=self.repo_var, foreground=MUTED,
                  anchor="w").grid(row=0, column=1, sticky="w", padx=(6, 10))
        self.branch_var = tk.StringVar(value="")
        ttk.Label(bar, textvariable=self.branch_var, foreground="#0969da",
                  anchor="w").grid(row=0, column=2, sticky="w")
        bar.columnconfigure(2, weight=1)
        self.reload_btn = ttk.Button(bar, text="↻ Tải lại", width=10,
                                     command=self._reload)
        self.reload_btn.grid(row=0, column=3, padx=(8, 4))
        self.choose_btn = ttk.Button(bar, text="Chọn repo…", width=12,
                                     command=self._choose_repo)
        self.choose_btn.grid(row=0, column=4)

    def _build_body(self):
        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=10, pady=(4, 0))

        # -- trai: danh sach file --
        left = ttk.Frame(body, padding=(0, 0, 4, 0))
        head = ttk.Frame(left)
        head.pack(fill="x", pady=(0, 4))
        self.count_var = tk.StringVar(value="File thay đổi")
        ttk.Label(head, textvariable=self.count_var,
                  font=self._bold()).pack(side="left")
        for text, cmd in (("Đảo", self._invert), ("Không", self._tick_none),
                          ("Tất cả", self._tick_all)):
            ttk.Button(head, text=text, width=7, command=cmd).pack(
                side="right", padx=(2, 0))

        wrap = ttk.Frame(left)
        wrap.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(wrap, columns=("tick", "status", "path"),
                                 show="headings", selectmode="browse")
        self.tree.heading("tick", text="✓", command=self._toggle_all)
        self.tree.heading("status", text="Trạng thái", anchor="w")
        self.tree.heading("path", text="File", anchor="w")
        self.tree.column("tick", width=self._px(34), minwidth=self._px(30),
                         anchor="center", stretch=False)
        self.tree.column("status", width=self._px(84), minwidth=self._px(70),
                         anchor="w", stretch=False)
        self.tree.column("path", width=self._px(240), anchor="w", stretch=True)
        for name, color in STATUS_COLORS.items():
            self.tree.tag_configure(name, foreground=color)
        vsb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)
        self.tree.bind("<Button-1>", self._on_tree_click)
        self.tree.bind("<Double-1>", self._on_tree_double)
        self.tree.bind("<space>", lambda e: self._toggle_focused())
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._preview_selected())
        ttk.Label(left, text="Click ô ✓ hoặc Space để tick · chọn dòng để "
                             "xem diff", foreground=MUTED).pack(
            anchor="w", pady=(4, 0))
        body.add(left, weight=2)

        # -- phai: message (tren) + diff (duoi) --
        right = ttk.Panedwindow(body, orient="vertical")
        msg_frame = ttk.Labelframe(right, text="Commit message (sửa được)",
                                   padding=6)
        self.msg_text = tk.Text(msg_frame, wrap="word", undo=True, height=8,
                                padx=6, pady=4, relief="flat",
                                highlightthickness=1,
                                highlightbackground="#d0d7de")
        msg_vsb = ttk.Scrollbar(msg_frame, orient="vertical",
                                command=self.msg_text.yview)
        self.msg_text.configure(yscrollcommand=msg_vsb.set)
        self.msg_text.grid(row=0, column=0, sticky="nsew")
        msg_vsb.grid(row=0, column=1, sticky="ns")
        self.summary_var = tk.StringVar(value=f"Tiêu đề: 0/{SUMMARY_LIMIT}")
        self.summary_lbl = ttk.Label(msg_frame, textvariable=self.summary_var,
                                     foreground=MUTED)
        self.summary_lbl.grid(row=1, column=0, sticky="w", pady=(4, 0))
        msg_frame.rowconfigure(0, weight=1)
        msg_frame.columnconfigure(0, weight=1)
        self.msg_text.bind("<KeyRelease>", lambda e: self._update_summary())
        right.add(msg_frame, weight=3)

        diff_frame = ttk.Labelframe(right, text="Diff", padding=6)
        self.diff_title_var = tk.StringVar(value="(chọn một file để xem diff)")
        ttk.Label(diff_frame, textvariable=self.diff_title_var,
                  foreground=MUTED, font=self.mono).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        self.diff_text = tk.Text(diff_frame, wrap="none", font=self.mono,
                                 state="disabled", relief="flat",
                                 highlightthickness=1,
                                 highlightbackground="#d0d7de",
                                 padx=4, pady=2)
        for kind, (fg, bg) in DIFF_TAGS.items():
            opts = {}
            if fg:
                opts["foreground"] = fg
            if bg:
                opts["background"] = bg
            if opts:
                self.diff_text.tag_configure(kind, **opts)
        self.diff_text.tag_configure("head", font=self._mono_bold())
        d_vsb = ttk.Scrollbar(diff_frame, orient="vertical",
                              command=self.diff_text.yview)
        d_hsb = ttk.Scrollbar(diff_frame, orient="horizontal",
                              command=self.diff_text.xview)
        self.diff_text.configure(yscrollcommand=d_vsb.set,
                                 xscrollcommand=d_hsb.set)
        self.diff_text.grid(row=1, column=0, sticky="nsew")
        d_vsb.grid(row=1, column=1, sticky="ns")
        d_hsb.grid(row=2, column=0, sticky="ew")
        diff_frame.rowconfigure(1, weight=1)
        diff_frame.columnconfigure(0, weight=1)
        right.add(diff_frame, weight=2)
        body.add(right, weight=3)

    def _build_actions(self):
        row = ttk.Frame(self, padding=(10, 8, 10, 4))
        row.pack(fill="x")
        ttk.Label(row, text="Gợi ý:").grid(row=0, column=0)
        self.hint_var = tk.StringVar()
        hint = ttk.Entry(row, textvariable=self.hint_var)
        hint.grid(row=0, column=1, sticky="ew", padx=(6, 12))
        hint.bind("<Return>", lambda e: self._generate())
        row.columnconfigure(1, weight=1)

        self.lang_var = tk.StringVar(
            value="vi" if self.core.cfg("lang") == "vi" else "en")
        ttk.Radiobutton(row, text="vi", variable=self.lang_var,
                        value="vi").grid(row=0, column=2)
        ttk.Radiobutton(row, text="en", variable=self.lang_var,
                        value="en").grid(row=0, column=3, padx=(4, 12))
        self.push_var = tk.BooleanVar(value=self.core.cfg("push") == "always")
        ttk.Checkbutton(row, text="Push sau commit", variable=self.push_var
                        ).grid(row=0, column=4, padx=(0, 12))
        self.gen_btn = ttk.Button(row, text="⚡ Sinh message",
                                  command=self._generate)
        self.gen_btn.grid(row=0, column=5, padx=(0, 4))
        self.regen_btn = ttk.Button(row, text="🔁 Sinh lại",
                                    command=lambda: self._generate(regen=True))
        self.regen_btn.grid(row=0, column=6, padx=(0, 4))
        self.commit_btn = ttk.Button(row, text="✓ Commit", command=self._commit)
        self.commit_btn.grid(row=0, column=7)

    def _build_status(self):
        bar = ttk.Frame(self, padding=(10, 2, 10, 6))
        bar.pack(fill="x")
        self.status_var = tk.StringVar(value="Sẵn sàng.")
        self.status = ttk.Label(bar, textvariable=self.status_var, anchor="w",
                                foreground=MUTED)
        self.status.pack(side="left", fill="x", expand=True)
        self.progress = ttk.Progressbar(bar, mode="indeterminate",
                                        length=self._px(140))
        self.shortcuts = ttk.Label(
            bar, text="Ctrl+G sinh · Ctrl+Enter commit · F5 tải lại",
            foreground="#8c959f")
        self.shortcuts.pack(side="right")

    def _bind_keys(self):
        self.bind("<Control-g>", lambda e: self._generate())
        self.bind("<Control-G>", lambda e: self._generate())
        self.bind("<F5>", lambda e: self._reload())
        self.bind("<Control-o>", lambda e: self._choose_repo())
        for w in (self, self.msg_text):
            w.bind("<Control-Return>", self._on_ctrl_enter)

    def _bold(self):
        f = tkfont.nametofont("TkDefaultFont").copy()
        f.configure(weight="bold")
        return f

    def _mono_bold(self):
        f = tkfont.Font(font=self.mono)
        f.configure(weight="bold")
        return f

    # ---- cau noi thread nen -> main thread ----
    def _post(self, func, *args):
        """Goi tu thread nen: xep func(*args) de main thread chay."""
        self._queue.put((func, args))

    def _poll_queue(self):
        try:
            while True:
                func, args = self._queue.get_nowait()
                func(*args)
        except queue.Empty:
            pass
        self.after(50, self._poll_queue)

    # ---- trang thai chung ----
    def _status(self, text, color=MUTED):
        self.status_var.set(text)
        self.status.configure(foreground=color)

    def _set_busy(self, on, text=None):
        self.busy = on
        state = "disabled" if on else "normal"
        for b in (self.gen_btn, self.regen_btn, self.commit_btn,
                  self.reload_btn, self.choose_btn):
            b.configure(state=state)
        if on:
            self.shortcuts.pack_forget()
            self.progress.pack(side="right")
            self.progress.start(12)
            self.configure(cursor="watch")
            if text:
                self._status(text)
        else:
            self.progress.stop()
            self.progress.pack_forget()
            self.shortcuts.pack(side="right")
            self.configure(cursor="")
        self.update_idletasks()

    def _set_repo_state(self, has_repo):
        state = "normal" if has_repo else "disabled"
        for b in (self.gen_btn, self.regen_btn, self.commit_btn,
                  self.reload_btn):
            b.configure(state=state)

    def _errtext(self, e):
        if isinstance(e, SystemExit):
            return "lệnh git/API thất bại (xem terminal)."
        return str(e) or e.__class__.__name__

    def _on_error(self, e):
        self._set_busy(False)
        text = self._errtext(e)
        first = text.strip().splitlines()[0] if text.strip() else text
        self._status(f"Lỗi: {first}", ERR)
        if "\n" in text.strip() or len(text) > 90:
            messagebox.showerror("gcm - lỗi", text, parent=self)

    # ---- repo ----
    def _choose_repo(self):
        if self.busy:
            return
        folder = filedialog.askdirectory(title="Chọn thư mục repo git",
                                         parent=self)
        if folder:
            self._open_repo(folder)

    def _open_repo(self, folder):
        ok, msg = self.core.set_repo(folder)
        if not ok:
            self._status(f"Lỗi: {msg}", ERR)
            return
        root = self.core.REPO_ROOT
        self.repo_var.set(self.core.shorten_path(root, 70))
        self.title(f"gcm v{self.core.VERSION} — {os.path.basename(root)}")
        try:
            self.core.save_config("last_repo", root)
        except (OSError, ValueError):
            pass
        self._set_repo_state(True)
        self._reload()

    def _reload(self):
        if self.busy or not self.core.REPO_ROOT:
            return
        try:
            branch, ahead = self.core.branch_status()
            files = self.core.changed_files()
        except BaseException as e:  # noqa: BLE001 - core co the sys.exit
            self._status(f"Lỗi đọc repo: {self._errtext(e)}", ERR)
            return
        self.branch_var.set(f"⎇ {branch}" + (
            f"   ↑{ahead} commit chưa push" if ahead else ""))
        self.tree.delete(*self.tree.get_children())
        self.rows = {}
        # Nhu TUI: file da stage san thi tick san; chua stage gi thi tick het.
        staged = {p for code, p in files if code[0] not in " ?"}
        for i, (code, path) in enumerate(files):
            iid = str(i)
            ticked = (path in staged) if staged else True
            self.rows[iid] = {"code": code, "path": path, "ticked": ticked}
            name = status_name(code)
            self.tree.insert("", "end", iid=iid, tags=(name,),
                             values=(self._box(ticked), name, path))
        self._update_count()
        if files:
            self.tree.selection_set("0")
            self.tree.focus("0")
            self._status(f"{len(files)} file thay đổi"
                         + (f", {len(staged)} đã stage sẵn." if staged
                            else "."))
        else:
            self._show_diff(None)
            self._status("Working tree sạch — không có gì để commit.", OK)

    # ---- danh sach file ----
    @staticmethod
    def _box(ticked):
        return "☑" if ticked else "☐"

    def _set_tick(self, iid, value):
        row = self.rows[iid]
        row["ticked"] = value
        self.tree.set(iid, "tick", self._box(value))

    def _toggle(self, iid):
        self._set_tick(iid, not self.rows[iid]["ticked"])
        self._update_count()

    def _toggle_focused(self):
        iid = self.tree.focus()
        if iid:
            self._toggle(iid)
        return "break"

    def _tick_all(self):
        for iid in self.rows:
            self._set_tick(iid, True)
        self._update_count()

    def _tick_none(self):
        for iid in self.rows:
            self._set_tick(iid, False)
        self._update_count()

    def _toggle_all(self):
        if self.rows and all(r["ticked"] for r in self.rows.values()):
            self._tick_none()
        else:
            self._tick_all()

    def _invert(self):
        for iid, row in self.rows.items():
            self._set_tick(iid, not row["ticked"])
        self._update_count()

    def _update_count(self):
        n = len(self.rows)
        k = sum(1 for r in self.rows.values() if r["ticked"])
        self.count_var.set(f"File thay đổi  {k}/{n}" if n else "File thay đổi")

    def _selected(self):
        return [r["path"] for r in self.rows.values() if r["ticked"]]

    def _all_paths(self):
        return [r["path"] for r in self.rows.values()]

    def _on_tree_click(self, event):
        if self.tree.identify("region", event.x, event.y) == "heading":
            return None
        iid = self.tree.identify_row(event.y)
        if iid and self.tree.identify_column(event.x) == "#1":
            self._toggle(iid)
            return "break"  # khong doi dong dang chon -> diff giu nguyen
        return None

    def _on_tree_double(self, event):
        iid = self.tree.identify_row(event.y)
        if iid:
            self._toggle(iid)
        return "break"

    def _preview_selected(self):
        sel = self.tree.selection()
        self._show_diff(sel[0] if sel else None)

    def _show_diff(self, iid):
        self.diff_text.configure(state="normal")
        self.diff_text.delete("1.0", "end")
        if iid is None or iid not in self.rows:
            self.diff_title_var.set("(chọn một file để xem diff)")
            self.diff_text.configure(state="disabled")
            return
        row = self.rows[iid]
        try:
            title, entries = self.core.diff_entries(row["code"], row["path"])
        except BaseException as e:  # noqa: BLE001
            title, entries = row["path"], [("note", self._errtext(e))]
        self.diff_title_var.set(title)
        for kind, line in entries[:MAX_DIFF_LINES]:
            self.diff_text.insert("end", line + "\n", (kind,))
        if len(entries) > MAX_DIFF_LINES:
            self.diff_text.insert(
                "end", f"... ({len(entries) - MAX_DIFF_LINES} dòng nữa)\n",
                ("note",))
        self.diff_text.configure(state="disabled")

    # ---- message ----
    def _update_summary(self):
        first = self.msg_text.get("1.0", "1.end")
        n = len(first)
        self.summary_var.set(f"Tiêu đề: {n}/{SUMMARY_LIMIT}"
                             + ("  — hơi dài, nên rút gọn" if n > SUMMARY_LIMIT
                                else ""))
        self.summary_lbl.configure(
            foreground=ERR if n > SUMMARY_LIMIT else MUTED)

    def _set_message(self, msg):
        self.msg_text.delete("1.0", "end")
        self.msg_text.insert("1.0", msg)
        self.msg_text.edit_reset()
        self._update_summary()

    def _on_ctrl_enter(self, event):
        self._commit()
        return "break"

    # ---- sinh message ----
    def _generate(self, regen=False):
        if self.busy:
            return
        if not self.rows:
            self._status("Không có file thay đổi nào để sinh message.", ERR)
            return
        selected = self._selected()
        if not selected:
            self._status("Hãy tick ít nhất 1 file.", ERR)
            return
        api_key = self.core.resolve_api_key() or self._ask_api_key()
        if not api_key:
            return
        self.temperature = min(self.temperature + 0.3, 1.0) if regen else 0.3
        vietnamese = self.lang_var.get() == "vi"
        hint = self.hint_var.get().strip() or None
        model = self.core.cfg("model")
        all_paths = self._all_paths()  # lay tren main thread, tranh race
        temperature = self.temperature
        self._set_busy(True, "Đang sinh commit message…"
                       + (" (thử cách viết khác)" if regen else ""))

        def work():
            try:
                self.core.stage_files(selected, all_paths)
                msg = self.core.generate_message(
                    selected, vietnamese, hint, api_key, model, temperature)
            except BaseException as e:  # noqa: BLE001 - ke ca SystemExit tu core
                self._post(self._on_error, e)
                return
            self._post(self._on_generated, msg)

        threading.Thread(target=work, daemon=True).start()

    def _on_generated(self, msg):
        self._set_busy(False)
        self._set_message(msg)
        self._status("Đã sinh message — kiểm tra, sửa nếu cần rồi Commit.", OK)

    # ---- commit / push ----
    def _commit(self):
        if self.busy:
            return
        message = self.msg_text.get("1.0", "end").strip()
        if not message:
            self._status("Message trống — bấm Sinh message hoặc gõ tay.", ERR)
            return
        selected = self._selected()
        if not selected:
            self._status("Hãy tick ít nhất 1 file.", ERR)
            return
        all_paths = self._all_paths()
        want_push = self.push_var.get()
        # nhu CLI: chi them coauthor khi push tu gcm
        final = self.core.add_coauthor(message) if want_push else message
        self._set_busy(True, "Đang commit…")

        def work():
            try:
                self.core.stage_files(selected, all_paths)
                ok, out = self.core.commit_simple(final)
                if not ok:
                    raise self.core.GcmError("commit thất bại:\n" + out)
                pushed = None
                if want_push:
                    self._post(self._status, "Đang push…")
                    pushed = self.core.push_simple()
            except BaseException as e:  # noqa: BLE001
                self._post(self._on_error, e)
                return
            self._post(self._on_committed, len(selected), pushed)

        threading.Thread(target=work, daemon=True).start()

    def _on_committed(self, n_files, pushed):
        self._set_busy(False)
        self._set_message("")
        self.temperature = 0.3
        self._reload()  # truoc, de dong trang thai ket qua khong bi ghi de
        if pushed is not None and not pushed[0]:
            self._status(f"Đã commit {n_files} file, nhưng push lỗi.", ERR)
            messagebox.showerror("Push lỗi", pushed[1], parent=self)
        else:
            self._status(f"✓ Đã commit {n_files} file"
                         + (" + push." if pushed else "."), OK)

    def _ask_api_key(self):
        key = simpledialog.askstring(
            "Groq API key",
            "Dán Groq API key (lấy free tại console.groq.com/keys):",
            parent=self)
        if key:
            key = key.strip()
            try:
                self.core.save_config("api_key", key)  # nap lai CONFIG luon
            except (OSError, ValueError) as e:
                self._status(f"Không lưu được key: {e}", ERR)
        return key
