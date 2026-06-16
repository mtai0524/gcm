# Thiết kế: Giao diện GUI cho gcm (double-click)

- **Ngày:** 2026-06-16
- **Trạng thái:** Đã duyệt thiết kế, chờ viết plan
- **Mục tiêu:** Khi double-click `gcm.exe`, mở một cửa sổ đồ hoạ (GUI) để stage file,
  sinh commit message bằng AI, sửa và commit/push — thay vì cửa sổ console nhấp nháy
  rồi tắt. CLI hiện tại giữ nguyên 100%.

## 1. Bối cảnh

`gcm` là công cụ dòng lệnh (CLI) sinh git commit message qua Groq API. File `gcm`
là script Python thuần stdlib (929 dòng), được PyInstaller đóng gói `--onefile`
thành `gcm.exe` dạng console. Khi double-click trong Explorer, người dùng chỉ thấy
console nhấp nháy rồi đóng vì gcm cần chạy trong terminal với repo git ở thư mục
hiện tại.

Người dùng muốn double-click `gcm.exe` mở một **GUI thật sự** (nút bấm, danh sách
file, ô message), dùng **Tkinter** (có sẵn trong Python, không cần pip — giữ triết
lý stdlib của dự án).

## 2. Quyết định thiết kế đã chốt

| Vấn đề | Quyết định |
|--------|-----------|
| Entry point | **Một file `gcm.exe`** tự nhận biết: double-click → GUI, có tham số/chạy trong terminal → CLI |
| Phạm vi | **MVP gọn**: chọn repo → stage file → gợi ý + ngôn ngữ → sinh message → sửa → commit/push |
| Layout | **2 cột**: trái = danh sách file, phải = ô message |
| Nút "Mở CLI" | **Bỏ** (YAGNI) |
| Nhớ repo gần nhất | **Có** — lưu `last_repo` trong config |
| Framework GUI | **Tkinter** (stdlib, không cần pip) |

## 3. Kiến trúc

### 3.1 Phát hiện double-click vs terminal
Trong `main()` của `gcm`, trước khi xử lý CLI, thêm bước:

```
nếu len(sys.argv) == 1 và is_double_clicked():
    chạy GUI rồi thoát
ngược lại:
    chạy CLI như cũ
```

`is_double_clicked()` (chỉ Windows): dùng `ctypes` gọi
`kernel32.GetConsoleProcessList`. Khi Explorer mở exe console, một console mới được
tạo và **chỉ có 1 process** gắn vào → đặc trưng của double-click. Khi chạy trong
terminal sẵn có thì có >1 process. Trên môi trường không phải Windows, hàm trả
`False` (GUI chủ yếu nhắm Windows; vẫn có thể gọi GUI thủ công bằng flag `--gui`).

Sau khi xác định là double-click, gọi `kernel32.FreeConsole()` để **ẩn cửa sổ
console đen** rồi mở cửa sổ Tkinter.

### 3.2 Module
- GUI nằm trong **module mới `gcm_gui.py`** ở thư mục gốc repo, import các hàm lõi
  từ `gcm`. Giữ file `gcm` tập trung vào CLI + logic.
- Vì `gcm` không có đuôi `.py`, để import được trong cả lúc chạy script lẫn lúc
  PyInstaller đóng gói, dùng cách import bằng đường dẫn (`importlib`) hoặc tách lõi
  dùng chung. **Chi tiết để giai đoạn plan quyết** (xem Rủi ro mở).

### 3.3 Tái dùng hàm lõi (không viết lại logic)
GUI gọi thẳng:
- `changed_files()` → list `(code, path)` từ `git status --porcelain`
- `smart_diff(files)` → `(diff_text, skipped, truncated)` (dùng `git diff --staged`,
  nên phải `git add` file trước khi gọi)
- `build_prompt(diff, files, vietnamese, hint)` → `(system, user)`
- `call_groq(api_key, system, user, model)` → message (network call)
- `commit_with_message(message)`, `do_push()`, `add_coauthor()`
- `load_config()`

**Cần thêm vào `gcm`:**
1. `save_config(key, value)` — đọc–sửa–ghi `~/.config/gcm/config` dạng `key = value`
   (hiện chỉ có `load_config`, chưa có hàm ghi). Giữ nguyên các dòng/comment khác.
2. Hàm/đường dẫn cho GUI **đặt thư mục repo**: `os.chdir(folder)` rồi gọi lại
   `ensure_repo()` để xác thực. (gcm làm việc theo cwd / `REPO_ROOT`.)

## 4. Giao diện (layout 2 cột)

```
┌──────────────────────────────────────────────┐
│ 📁 Repo: [C:\my-repo        ] [Chọn…]          │
├────────────────┬─────────────────────────────┤
│ File thay đổi   │ Commit message (sửa được)   │
│ ☑ M src/app.py  │ feat(auth): add login flow  │
│ ☑ A README.md   │                             │
│ ☐ ? tmp.log     │ - ...                       │
├────────────────┴─────────────────────────────┤
│ Gợi ý (–m): [______]   Ngôn ngữ: ◉ vi ○ en     │
│ [⚡ Sinh message]      ☐ Push   [✓ Commit]      │
│ Trạng thái: sẵn sàng                            │
└──────────────────────────────────────────────┘
```

Thành phần:
- **Thanh repo:** ô đường dẫn (chỉ đọc) + nút **Chọn…** (folder picker
  `tkinter.filedialog.askdirectory`).
- **Cột trái — danh sách file:** mỗi dòng một checkbox + nhãn trạng thái
  (new/modified/added/deleted/renamed, ánh xạ từ code git) + đường dẫn. Mặc định
  tick các file đã/đang thay đổi (trừ file `??`/noise tuỳ chọn).
- **Cột phải — ô message:** `Text` nhiều dòng, sửa tự do.
- **Hàng dưới:** ô gợi ý (`-m`), radio ngôn ngữ vi/en (mặc định theo
  `config.lang`), nút **Sinh message**, checkbox **Push**, nút **Commit**, và
  **thanh trạng thái** (text màu: xám = thông tin, đỏ = lỗi, xanh = thành công).

## 5. Luồng hoạt động

1. **Mở GUI:** đọc config; nếu có `last_repo` và còn tồn tại → điền sẵn + nạp danh
   sách file. Nếu chưa có repo → ô trống, chờ bấm **Chọn…**.
2. **Chọn repo:** `os.chdir` + `ensure_repo`; nếu không phải git repo → báo đỏ.
   Lưu `last_repo` vào config.
3. **Sinh message** (chạy trong **thread nền**, cửa sổ không treo, trạng thái
   "Đang sinh…", nút bị vô hiệu tạm thời):
   - `git add` các file đã tick (file bỏ tick thì `git reset` để không lọt vào diff).
   - `smart_diff` → `build_prompt` → `call_groq`.
   - Kết quả đổ vào ô message (qua `widget.after` để cập nhật UI từ thread chính).
4. **Sửa message** tự do trong ô bên phải.
5. **Commit:** `commit_with_message(message)`. Nếu tick **Push** → `do_push()` (kèm
   coauthor theo config). Thành công → trạng thái xanh, làm mới danh sách file.

## 6. Xử lý lỗi & lần đầu chạy

- **Chưa có API key:** mở hộp thoại nhập key Groq (có link tới
  console.groq.com/keys), lưu bằng `save_config("api_key", …)`. Không có key thì
  không cho Sinh message.
- **Folder không phải git repo:** thanh trạng thái đỏ, không crash, không đổi
  `last_repo`.
- **Groq lỗi / mất mạng:** hiện thông báo lỗi, giữ nguyên cửa sổ và message hiện có.
- **Không tick file nào:** nhắc chọn ít nhất 1 file trước khi Sinh.
- **Commit/push thất bại:** hiện stderr của git ở thanh trạng thái.

## 7. Đóng gói & build

- `packaging/windows/build.ps1`: vẫn `--onefile`. Thêm `gcm_gui.py` vào lúc copy
  entry (cùng `gcm_entry.py`). Cân nhắc `--collect-submodules tkinter` nếu
  PyInstaller không tự gom (thường tự gom được).
- **Không cần thêm shortcut/UI trong MSI** — vẫn là một `gcm.exe` duy nhất; hành vi
  GUI là do exe tự quyết khi double-click. (Tuỳ chọn sau: thêm Start Menu shortcut
  trỏ tới `gcm.exe` để double-click tiện hơn — ngoài phạm vi MVP.)

## 8. Kiểm thử

- **Logic lõi** (`save_config`, ánh xạ trạng thái file, ráp diff→prompt): pytest
  với git repo tạm trong thư mục tmp.
- **Phát hiện double-click:** test `is_double_clicked` ở mức có thể (mock
  `GetConsoleProcessList`); phần phụ thuộc Windows kiểm thủ công.
- **GUI Tkinter:** kiểm thủ công theo checklist (mở, chọn repo, stage, sinh, sửa,
  commit, push, các nhánh lỗi). Không cố tự động hoá GUI.

## 9. Phạm vi loại trừ (không làm trong MVP)

- Xem diff từng file ngay trong GUI, chọn model, amend, cấu hình coauthor, tự cập
  nhật (`-u`) — các tính năng "đầy đủ ngang CLI" để sau.
- Nút "Mở terminal CLI".
- Tích hợp chuột phải Explorer ("Open gcm here").
- Start Menu shortcut trong MSI.

## 10. Rủi ro mở (giải quyết ở giai đoạn plan)

- **Import từ file `gcm` không có đuôi `.py`:** chọn cách import bằng `importlib`
  theo đường dẫn, hay tách phần lõi ra module dùng chung, hay đổi cách build. Cần
  thử nghiệm để chắc chạy được cả lúc dev lẫn lúc đã đóng gói PyInstaller.
- **`FreeConsole` + Tkinter:** xác nhận ẩn console rồi mở Tkinter mượt, không để
  lại cửa sổ đen chớp. Có thể cần dựng GUI trước rồi mới `FreeConsole`.
- **stage/unstage chính xác:** đảm bảo bỏ tick file thì nội dung không lọt vào diff
  (diff dùng `--staged`).
