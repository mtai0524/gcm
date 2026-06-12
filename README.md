# gcm — Git Commit Message generator

Tool CLI sinh git commit message tự động từ thay đổi đã `git add`, dùng Groq API (free).
Python thuần (chỉ stdlib, không cần `pip install`).

**Yêu cầu:** Python 3.7+ · Groq API key (free) tại https://console.groq.com/keys

---

# 1. Cài đặt

### Bước 0 — Cài Python (nếu chưa có)

Kiểm tra trước, nếu đã ra `Python 3.x.x` thì bỏ qua bước này:

```bash
python --version    # hoặc: py --version  (Windows)
```

<details>
<summary><b>Windows</b></summary>

```powershell
winget install -e --id Python.Python.3.12
```
> Hoặc tải tại https://www.python.org/downloads/ — khi cài nhớ **tick "Add python.exe to PATH"**.

Sau khi cài, **TẮT alias giả của Microsoft Store** (nếu không sẽ báo *"No installed Python found!"*):
Settings → Apps → Advanced app settings → **App execution aliases** → tắt `python.exe` và `python3.exe`.
Rồi **đóng hẳn và mở lại terminal**.
</details>

<details>
<summary><b>macOS</b></summary>

```bash
brew install python      # hoặc tải tại https://www.python.org/downloads/
```
</details>

<details>
<summary><b>Linux</b></summary>

```bash
sudo apt install python3       # Debian/Ubuntu
sudo dnf install python3       # Fedora
```
</details>

---

Đã có Python → cài gcm theo hệ điều hành:

<details open>
<summary><b>Linux / macOS / Git Bash</b></summary>

```bash
git clone https://github.com/mtai0524/gcm.git ~/tools/gcm
bash ~/tools/gcm/install.sh
```

`install.sh` tự lo hết: tạo lệnh `gcm` trong `~/.local/bin`, thêm vào PATH nếu thiếu,
dò Python (`py`/`python`) trên Windows, và hỏi/lưu API key.

Mở terminal mới rồi kiểm tra:
```bash
gcm -h
```
</details>

<details>
<summary><b>Windows — PowerShell</b> (terminal mặc định của VSCode)</summary>

> ⚠️ Trong PowerShell, `gcm` là alias có sẵn của `Get-Command`. Phải đè bằng một
> function trong `$PROFILE`.

**1. Tải tool:**
```powershell
git clone https://github.com/mtai0524/gcm.git $HOME\tools\gcm
```

**2. Lưu API key:**
```powershell
New-Item -ItemType Directory -Force -Path $HOME\.config\gcm | Out-Null
"gsk_..." | Out-File -Encoding ascii -NoNewline $HOME\.config\gcm\config
```

**3. Thêm lệnh `gcm` vào `$PROFILE` (đè alias):**
```powershell
if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Force -Path $PROFILE | Out-Null }
Add-Content $PROFILE @'

# gcm - git commit message generator
if (Test-Path Alias:gcm) { Remove-Item Alias:gcm -Force }
function gcm { py "$HOME\tools\gcm\gcm" @args }
'@
```
> Nếu `py` không chạy, đổi `py` → `python` trong dòng `function gcm`.

**4. Nạp lại profile và kiểm tra:**
```powershell
. $PROFILE
gcm -h
```
</details>

### Cấu hình API key

Tool đọc key theo thứ tự:
1. Biến môi trường `GROQ_API_KEY`
2. File `~/.config/gcm/config` (Windows: `%USERPROFILE%\.config\gcm\config`) — chỉ cần 1 dòng là key `gsk_...`

`install.sh` sẽ hỏi key khi cài. Cấu hình thủ công sau:
```bash
echo "gsk_..." > ~/.config/gcm/config
```

### Lỗi "không tìm thấy Python" (Windows)

Windows có alias giả của Microsoft Store chen vào. Vào **Settings → Apps →
Advanced app settings → App execution aliases** → **TẮT** `python.exe` và `python3.exe`,
rồi mở lại terminal.

---

# 2. Update

Lệnh `gcm` ở cả 2 OS đều trỏ vào thư mục đã clone, nên chỉ cần `git pull` — không cần cài lại:

```bash
# Linux / macOS / Git Bash
git -C ~/tools/gcm pull
```
```powershell
# PowerShell
git -C $HOME\tools\gcm pull
```

---

## Cách dùng (tham khảo nhanh)

```bash
git add .     # stage thay đổi (hoặc dùng -s bên dưới)
gcm           # message tiếng Anh (Conventional Commits) + hỏi commit
gcm -s        # chọn file để stage (interactive) rồi sinh message
gcm --vi      # message tiếng Việt
gcm -a        # tự git add -A rồi sinh
gcm -p        # chỉ in message, không hỏi (tiện copy / nối lệnh)
gcm -h        # trợ giúp
```

Sau khi sinh: `[Enter]` commit luôn / `[e]` mở editor sửa / `[n]` hủy.

Chạy `gcm -s` (hoặc `gcm` khi chưa stage gì) để chọn file ngay trong tool:
```
Chọn file để stage:
  ●  1. added     src/app.py      ● = đã stage, ○ = chưa
  ○  2. modified  README.md
  ○  3. new       test/new.py
  Nhập số ('1 3', '1-3'), 'a' = tất cả, Enter = giữ nguyên, 'q' = hủy
```

## Ghi chú kỹ thuật

- Endpoint: Groq `/openai/v1/chat/completions`, model `llama-3.3-70b-versatile`.
- Request bắt buộc có header `User-Agent`, thiếu là Cloudflare chặn 403 (error 1010).
- Đọc output `git` và in console đều ép UTF-8 (`errors=replace`) để không lỗi trên
  console Windows (cp1252) khi diff chứa ký tự tiếng Việt.
- Diff > 12000 ký tự sẽ bị cắt bớt trước khi gửi.
</content>
</invoke>
