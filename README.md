# gcm — Git Commit Message generator

Tool CLI sinh git commit message tự động từ thay đổi đã `git add`, dùng Groq API (free).
Python thuần (chỉ stdlib, không cần `pip install`).

## Yêu cầu

- **Python 3.7+** (kiểm tra: `python --version` hoặc `py --version`)
- **Groq API key** (free): lấy tại https://console.groq.com/keys

---

## Cài đặt trên Linux / macOS

```bash
git clone https://github.com/mtai0524/gcm.git ~/tools/gcm
bash ~/tools/gcm/install.sh
```

`install.sh` tự lo: tạo lệnh `gcm` trong `~/.local/bin`, thêm PATH nếu thiếu, và hỏi/lưu API key.

---

## Cài đặt trên Windows

> ⚠️ Trong **PowerShell**, `gcm` là lệnh có sẵn (alias của `Get-Command`). Cần đè nó
> bằng một function trong `$PROFILE` (xem bên dưới). Trong **Git Bash** thì không bị trùng.

### Cách A — PowerShell (terminal mặc định của VSCode)

**1. Tải tool về:**
```powershell
git clone https://github.com/mtai0524/gcm.git $HOME\tools\gcm
```

**2. Lưu API key:**
```powershell
New-Item -ItemType Directory -Force -Path $HOME\.config\gcm | Out-Null
"gsk_..." | Out-File -Encoding ascii -NoNewline $HOME\.config\gcm\config
```

**3. Thêm lệnh `gcm` vào PowerShell `$PROFILE` (đè alias Get-Command):**
```powershell
if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Force -Path $PROFILE | Out-Null }
Add-Content $PROFILE @'

# gcm - git commit message generator
if (Test-Path Alias:gcm) { Remove-Item Alias:gcm -Force }
function gcm { py "$HOME\tools\gcm\gcm" @args }
'@
```
> Nếu `py` không chạy được, đổi `py` thành `python` trong dòng `function gcm`.

**4. Nạp lại profile (hoặc mở terminal mới):**
```powershell
. $PROFILE
```

**5. Kiểm tra:**
```powershell
gcm -h
```

### Cách B — Git Bash

```bash
git clone https://github.com/mtai0524/gcm.git ~/tools/gcm
bash ~/tools/gcm/install.sh
```
`install.sh` tự dò Python (`py`/`python`), tạo wrapper `gcm`, thêm PATH và hỏi API key.
Đóng/mở lại Git Bash rồi chạy `gcm -h`.

### Nếu báo "không tìm thấy Python"

Windows có alias giả của Microsoft Store chen vào. Vào **Settings → Apps →
Advanced app settings → App execution aliases** → **TẮT** `python.exe` và `python3.exe`,
rồi mở lại terminal.

---

## Cách dùng

```bash
git add .     # stage thay đổi
gcm           # message tiếng Anh (Conventional Commits) + hỏi commit
gcm --vi      # message tiếng Việt
gcm -a        # tự git add -A rồi sinh
gcm -p        # chỉ in message, không hỏi (tiện copy / nối lệnh)
gcm -h        # trợ giúp
```

Sau khi sinh, tool hỏi: `[Enter]` commit luôn / `[e]` mở editor sửa / `[n]` hủy.

---

## Cập nhật phiên bản mới

Tool ở cả 2 OS đều trỏ vào thư mục đã clone, nên chỉ cần `git pull`:

```bash
# Linux / macOS / Git Bash
git -C ~/tools/gcm pull
```
```powershell
# PowerShell
git -C $HOME\tools\gcm pull
```

Không cần cài lại — lệnh `gcm` tự dùng bản mới.

---

## Cấu hình API key (chi tiết)

Tool đọc key theo thứ tự:
1. Biến môi trường `GROQ_API_KEY`
2. File `~/.config/gcm/config` (Windows: `%USERPROFILE%\.config\gcm\config`)

File config chỉ cần 1 dòng là key (`gsk_...`).

---

## Ghi chú kỹ thuật

- Endpoint: Groq `/openai/v1/chat/completions`, model `llama-3.3-70b-versatile`.
- Request bắt buộc có header `User-Agent`, nếu thiếu Cloudflare chặn 403 (error 1010).
- Đọc output `git` và in console đều ép UTF-8 (`errors=replace`) để không lỗi trên
  console Windows (cp1252) khi diff chứa ký tự tiếng Việt.
- Diff > 12000 ký tự sẽ bị cắt bớt trước khi gửi.
