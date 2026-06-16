"""gcm GUI - cua so Tkinter (layout 2 cot) cho gcm.

Nhan `core` (module gcm) qua run_gui(core); KHONG import gcm truc tiep
(file `gcm` khong co duoi .py). Goi core.changed_files(), core.set_repo(), ...
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk


def run_gui(core):
    app = GcmApp(core)
    app.mainloop()


def _api_key(core):
    """Lay api_key tu env/config; '' neu chua co (khong sys.exit nhu get_api_key)."""
    return (os.environ.get("GROQ_API_KEY", "").strip()
            or core.CONFIG.get("api_key", ""))


class GcmApp(tk.Tk):
    def __init__(self, core):
        super().__init__()
        self.core = core
        self.title(f"gcm v{core.VERSION}")
        self.geometry("820x520")
        self.minsize(680, 420)
        self.file_vars = []      # list of (tk.BooleanVar, path)

        self._build_repo_bar()
        self._build_body()
        self._build_actions()

        # Mo san repo gan nhat neu con ton tai
        last = core.CONFIG.get("last_repo", "")
        if last and os.path.isdir(last):
            self._open_repo(last)

    # ---- layout ----
    def _build_repo_bar(self):
        bar = ttk.Frame(self, padding=8)
        bar.pack(fill="x")
        ttk.Label(bar, text="📁 Repo:").pack(side="left")
        self.repo_var = tk.StringVar(value="(chua chon)")
        ttk.Label(bar, textvariable=self.repo_var, foreground="#555").pack(
            side="left", padx=6)
        ttk.Button(bar, text="Chọn…", command=self._choose_repo).pack(
            side="right")

    def _build_body(self):
        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=8)

        left = ttk.Labelframe(body, text="File thay đổi", padding=6)
        self.files_frame = ttk.Frame(left)
        self.files_frame.pack(fill="both", expand=True)
        body.add(left, weight=1)

        right = ttk.Labelframe(body, text="Commit message (sửa được)", padding=6)
        self.msg_text = tk.Text(right, wrap="word", height=10)
        self.msg_text.pack(fill="both", expand=True)
        body.add(right, weight=2)

    def _build_actions(self):
        row = ttk.Frame(self, padding=8)
        row.pack(fill="x")
        ttk.Label(row, text="Gợi ý (-m):").pack(side="left")
        self.hint_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.hint_var, width=24).pack(
            side="left", padx=4)

        default_lang = "vi" if self.core.CONFIG.get("lang", "").lower() == "vi" \
            else "en"
        self.lang_var = tk.StringVar(value=default_lang)
        ttk.Radiobutton(row, text="vi", variable=self.lang_var,
                        value="vi").pack(side="left")
        ttk.Radiobutton(row, text="en", variable=self.lang_var,
                        value="en").pack(side="left")

        self.push_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, text="Push", variable=self.push_var).pack(
            side="right")
        self.commit_btn = ttk.Button(row, text="✓ Commit",
                                     command=self._commit)
        self.commit_btn.pack(side="right", padx=4)
        self.gen_btn = ttk.Button(row, text="⚡ Sinh message",
                                  command=self._generate)
        self.gen_btn.pack(side="right", padx=4)

        self.status_var = tk.StringVar(value="sẵn sàng")
        self.status = ttk.Label(self, textvariable=self.status_var,
                                anchor="w", padding=(8, 4))
        self.status.pack(fill="x")

    # ---- helpers ----
    def _set_status(self, text, color="#555"):
        self.status_var.set(text)
        self.status.configure(foreground=color)

    def _choose_repo(self):
        folder = filedialog.askdirectory(title="Chọn thư mục repo git")
        if folder:
            self._open_repo(folder)

    def _open_repo(self, folder):
        ok, msg = self.core.set_repo(folder)
        if not ok:
            self._set_status(f"Lỗi: {msg}", "#c00")
            return
        self.repo_var.set(self.core.REPO_ROOT)
        self.core.save_config("last_repo", self.core.REPO_ROOT)
        self._reload_files()
        self._set_status("đã mở repo", "#080")

    def _reload_files(self):
        for w in self.files_frame.winfo_children():
            w.destroy()
        self.file_vars = []
        for code, path in self.core.changed_files():
            var = tk.BooleanVar(value=True)
            label = f"{code.strip() or '?':<2} {path}"
            ttk.Checkbutton(self.files_frame, text=label,
                            variable=var).pack(anchor="w")
            self.file_vars.append((var, path))

    def _selected(self):
        return [p for var, p in self.file_vars if var.get()]

    def _all_paths(self):
        return [p for _var, p in self.file_vars]

    # ---- actions ----
    def _generate(self):
        api_key = _api_key(self.core)
        if not api_key:
            api_key = self._ask_api_key()
            if not api_key:
                return
        selected = self._selected()
        if not selected:
            self._set_status("Hãy chọn ít nhất 1 file.", "#c00")
            return

        self.gen_btn.configure(state="disabled")
        self._set_status("Đang sinh message…")
        vietnamese = self.lang_var.get() == "vi"
        hint = self.hint_var.get().strip() or None
        model = self.core.MODEL
        all_paths = self._all_paths()  # capture tren main thread (tranh race)

        def work():
            try:
                self.core.stage_files(selected, all_paths)
                msg = self.core.generate_message(
                    selected, vietnamese, hint, api_key, model)
                self.after(0, lambda: self._on_generated(msg))
            except Exception as e:  # noqa: BLE001 - hien thi moi loi cho user
                self.after(0, lambda: self._on_error(str(e)))

        threading.Thread(target=work, daemon=True).start()

    def _on_generated(self, msg):
        self.msg_text.delete("1.0", "end")
        self.msg_text.insert("1.0", msg)
        self.gen_btn.configure(state="normal")
        self._set_status("đã sinh message — kiểm tra rồi Commit", "#080")

    def _on_error(self, text):
        self.gen_btn.configure(state="normal")
        self._set_status(f"Lỗi: {text}", "#c00")

    def _commit(self):
        message = self.msg_text.get("1.0", "end").strip()
        if not message:
            self._set_status("Message trống.", "#c00")
            return
        message = self.core.add_coauthor(message) if self.push_var.get() \
            else message
        rc = self.core.commit_with_message(message)
        if rc != 0:
            self._set_status("commit thất bại (xem terminal/git).", "#c00")
            return
        if self.push_var.get():
            ok, out = self.core.push_simple()
            if not ok:
                self._set_status(f"đã commit, push lỗi: {out}", "#c00")
                self._reload_files()
                return
        self._set_status("✓ commit xong" + (" + push" if self.push_var.get()
                                             else ""), "#080")
        self.msg_text.delete("1.0", "end")
        self._reload_files()

    def _ask_api_key(self):
        from tkinter import simpledialog
        key = simpledialog.askstring(
            "Groq API key",
            "Dán Groq API key (lấy free tại console.groq.com/keys):",
            parent=self)
        if key:
            key = key.strip()
            self.core.save_config("api_key", key)
            self.core.CONFIG["api_key"] = key
        return key
