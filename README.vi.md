# gcm — Git Commit Message generator

[English](README.md) · [Tiếng Việt](README.vi.md)

Sinh commit message từ thay đổi đã `git add`, dùng Groq API (free). Python thuần, không cần cài gì.

**Cần:** Python 3.7+ · Groq API key (free): https://console.groq.com/keys

---

## 1. Cài đặt

**Bước 1 — Python** *(bỏ qua nếu `python --version` đã chạy được)*

| Hệ điều hành | Lệnh |
|----|---------|
| Windows | `winget install -e --id Python.Python.3.12` |
| macOS | `brew install python` |
| Linux | `sudo apt install python3` |

> **Windows:** cài xong, tắt alias giả của Microsoft Store
> (Settings → Apps → Advanced app settings → **App execution aliases** → tắt
> `python.exe`, `python3.exe`), rồi mở lại terminal. Không thì sẽ báo
> *"No installed Python found!"*.

**Bước 2 — gcm**

<details open>
<summary><b>Linux / macOS / Git Bash</b></summary>

```bash
git clone https://github.com/mtai0524/gcm.git ~/tools/gcm
bash ~/tools/gcm/install.sh
```
`install.sh` tạo lệnh `gcm`, thêm vào PATH và hỏi/lưu API key.
Mở terminal mới → `gcm -h`.
</details>

<details>
<summary><b>Windows — PowerShell</b></summary>

`gcm` là alias sẵn có của PowerShell, phải đè bằng function trong `$PROFILE`.

```powershell
# 1. tải tool
git clone https://github.com/mtai0524/gcm.git $HOME\tools\gcm

# 2. lưu API key
New-Item -ItemType Directory -Force -Path $HOME\.config\gcm | Out-Null
"gsk_..." | Out-File -Encoding ascii -NoNewline $HOME\.config\gcm\config

# 3. thêm lệnh gcm vào $PROFILE
if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Force -Path $PROFILE | Out-Null }
Add-Content $PROFILE @'

if (Test-Path Alias:gcm) { Remove-Item Alias:gcm -Force }
function gcm { py "$HOME\tools\gcm\gcm" @args }
'@

# 4. nạp lại & kiểm tra
. $PROFILE
gcm -h
```
> `py` lỗi thì đổi `py` → `python` trong dòng `function gcm`.
</details>

**API key** — đọc theo thứ tự: env `GROQ_API_KEY` → file `~/.config/gcm/config`
(Windows: `%USERPROFILE%\.config\gcm\config`, 1 dòng key `gsk_...`).

---

## 2. Update

Tiện nhất — để gcm tự cập nhật (mọi OS, khỏi nhớ đường dẫn):
```bash
gcm -u
```

Cách thủ công (`git pull` trong thư mục clone):
```bash
git -C ~/tools/gcm pull          # PowerShell: git -C $HOME\tools\gcm pull
```

Lệnh `gcm` trỏ vào thư mục clone nên pull là xong, không cài lại.

---

## Cách dùng

| Lệnh | |
|---------|--|
| `gcm`            | sinh message (English) + hỏi commit |
| `gcm -s`         | chọn file để stage rồi sinh |
| `gcm -m "gợi ý"` | truyền thêm ngữ cảnh cho model |
| `gcm -y`         | commit luôn, không hỏi |
| `gcm --amend`    | sửa (reword) commit gần nhất |
| `gcm --vi`       | message tiếng Việt |
| `gcm -a`         | `git add -A` rồi sinh |
| `gcm -p`         | chỉ in message, không hỏi |
| `gcm --model X`  | dùng model `X` (hoặc env `GCM_MODEL`) cho lần chạy này |
| `gcm -u`         | cập nhật gcm lên bản mới nhất |
| `gcm -h`         | trợ giúp |

Sau khi sinh: `[Enter]` commit · `[e]` sửa · `[r]` tạo lại · `[n]` hủy.

`gcm -s` (hoặc `gcm` khi chưa stage gì) liệt kê từng file để chọn:
```
Chọn file để stage (3 thay đổi):
  ●  1. added     src/app.py          ● đã stage · ○ chưa
  ○  2. modified  README.md
  ○  3. new       src/Web/Chart.razor
  số ('1 3', '1-3') · 'a' tất cả · Enter = tất cả · 'q' hủy
```

<details>
<summary>Ghi chú kỹ thuật</summary>

- Endpoint Groq `/openai/v1/chat/completions`, model `llama-3.3-70b-versatile`.
- Header `User-Agent` bắt buộc (thiếu là Cloudflare chặn 403).
- Ép UTF-8 khi đọc git output & in console (tránh lỗi cp1252 trên Windows).
- Diff > 12000 ký tự bị cắt trước khi gửi.
</details>
