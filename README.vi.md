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
'{ "api_key": "gsk_..." }' | Out-File -Encoding utf8 $HOME\.config\gcm\config.json

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
>
> `. $PROFILE` báo *"running scripts is disabled on this system"* thì cho phép
> chạy script local một lần: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
> (gõ `Y`), rồi chạy lại `. $PROFILE`.
</details>

**API key** — đọc theo thứ tự: env `GROQ_API_KEY` → `~/.config/gcm/config.json`
(Windows: `%USERPROFILE%\.config\gcm\config.json`). Cách nhanh nhất:
`gcm config set api_key gsk_...`

### Cài trên Windows (MSI)

Muốn cài một phát trên Windows (không cần Git Bash, không cần tự cài Python)?

1. Vào [trang Releases](https://github.com/mtai0524/gcm/releases).
2. Tải file `gcm-X.Y.Z.msi` mới nhất.
3. Chạy nó. Trình cài tự thêm `gcm` vào `PATH` hệ thống.
4. Mở terminal **mới** (PowerShell hoặc CMD) rồi gõ `gcm -h`.

> Nếu `gcm` vẫn ra alias built-in của PowerShell (bước cấu hình profile không
> chạy), tự thiết lập bằng tay — chạy trong **PowerShell**:
>
> ```powershell
> # cho phép chạy script local một lần, nếu . $PROFILE bị chặn
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned   # gõ Y
>
> if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Force -Path $PROFILE | Out-Null }
> Add-Content $PROFILE @'
>
> if (Test-Path Alias:gcm) { Remove-Item Alias:gcm -Force }
> function gcm { & "$env:LOCALAPPDATA\Programs\gcm\gcm.exe" @args }
> '@
> . $PROFILE
> ```

> MSI chưa ký số nên Windows SmartScreen có thể cảnh báo lần đầu — chọn
> "More info" → "Run anyway". Cập nhật bằng cách tải MSI mới hơn (lệnh tự cập
> nhật `gcm -u` chỉ dùng được cho bản cài bằng git clone).

#### Tự build file MSI

Muốn tạo file `.msi` từ mã nguồn (ví dụ sau khi sửa code)? Mở **PowerShell ở
thư mục gốc repo** rồi chạy:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1
```

Lệnh này build `gcm.exe` bằng PyInstaller và đóng gói `gcm-X.Y.Z.msi` vào thư
mục gốc repo. Cần cài sẵn (một lần):

```powershell
winget install -e --id Python.Python.3.12      # Python 3
winget install -e --id Microsoft.DotNet.SDK.8  # .NET SDK (cho WiX)
```

Script tự cài PyInstaller và WiX. Bấm đúp file MSI để cài, hoặc upload lên
GitHub Releases.

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
| `gcm`            | sinh message + hỏi commit |
| `gcm -s`         | chọn file để stage bằng số rồi sinh |
| `gcm -t`         | chọn file kiểu TUI (↑↓ + space, `d` = xem diff) |
| `gcm -m "gợi ý"` | truyền thêm ngữ cảnh cho model |
| `gcm -y`         | commit luôn, không hỏi |
| `gcm --push`     | tự push sau khi commit |
| `gcm --amend`    | sửa (reword) commit gần nhất |
| `gcm --vi` / `--en` | ngôn ngữ message cho lần chạy này |
| `gcm -a`         | `git add -A` rồi sinh |
| `gcm -p`         | chỉ in message, không hỏi |
| `gcm --model X`  | dùng model `X` (hoặc env `GCM_MODEL`) cho lần chạy này |
| `gcm config`     | xem config đang dùng + mỗi key đến từ đâu |
| `gcm config set KEY VALUE` | ghi 1 key vào `config.json` |
| `gcm config unset KEY` | bỏ override, quay về mặc định built-in |
| `gcm -u`         | cập nhật gcm lên bản mới nhất |
| `gcm -h` / `-v`  | trợ giúp / version |

Sau khi sinh: `[Enter]` commit · `[p]` commit+push · `[e]` sửa · `[r]` tạo lại · `[n]` hủy.
Khung review hiện branch + số commit chưa push (`main ↑2`).

**Smart diff:** lockfile (`package-lock.json`, `yarn.lock`...), `*.min.js`, file binary
vẫn được commit nhưng không gửi nội dung cho LLM; file quá to được tóm tắt bằng
`--stat` thay vì cắt cụt giữa chừng.

### Config file (`~/.config/gcm/config.json`)

**Mặc định nằm trong code, file của bạn chỉ chứa những gì bạn đổi.** Key nào không
ghi trong file thì cứ theo mặc định built-in — nâng cấp gcm đổi mặc định là máy bạn
ăn theo ngay, không bị file config cũ ghim lại giá trị cũ.

```jsonc
{
  "//": "key bắt đầu bằng // là ghi chú (JSON không có comment)",
  "api_key": "gsk_...",          // key free: https://console.groq.com/keys
  "lang": "vi",                  // vi | en - ngôn ngữ message mặc định
  "model": "openai/gpt-oss-120b",
  "tui": true,                   // mặc định chọn file kiểu TUI
  "push": "ask",                 // ask | always | never
  "coauthor": "devduide <devduide@users.noreply.github.com>",  // "off" để tắt
  "system_prompt": "..."         // override ngắn ({lang} = câu chỉ định ngôn ngữ)
}
```

Thứ tự ưu tiên: **cờ CLI > env (`GROQ_API_KEY`, `GCM_MODEL`) > `config.json` >
mặc định built-in**. `gcm config` in ra từng key kèm **nguồn** đang lấy:

```
config: ~/.config/gcm/config.json
  api_key        'gsk_abc...1234'          <- file
  lang           'vi'                      <- file
  model          'openai/gpt-oss-120b'     <- mac dinh
  push           'ask'                     <- mac dinh
```

Sửa tay cũng được, hoặc để gcm ghi hộ (giá trị trùng mặc định sẽ bị **xoá** khỏi
file thay vì ghim vào):

```bash
gcm config set lang vi
gcm config set api_key gsk_...
gcm config unset lang      # quay về mặc định built-in
gcm config path            # in đường dẫn file config
```

JSON hỏng hoặc giá trị sai (vd `"push": "sometimes"`) sẽ được báo rõ rồi bỏ qua —
gcm vẫn chạy bằng mặc định chứ không chết.

> **Tự tạo lần đầu:** lần đầu chạy `gcm` (mọi cách cài — kể cả bản MSI Windows),
> gcm tự tạo `~/.config/gcm/config.json`, file mẫu đầy đủ `config.example.json` và
> `system_prompt.example.md` nếu chưa có. gcm **không bao giờ** đè file bạn đã chỉnh.
>
> **Nâng cấp từ bản cũ?** File `key = value` cũ ở `~/.config/gcm/config` được tự
> động chuyển sang `config.json` ở lần chạy đầu và giữ lại thành `config.migrated`
> — bạn không phải làm gì thêm.

#### Coauthor (collab cùng devduide)

Khi **push từ gcm**, gcm thêm trailer `Co-authored-by:` để ghi credit (GitHub hiện
avatar coauthor). Mặc định là `devduide`. Đổi tên/email của bạn, hoặc đặt `"off"`
để tắt hẳn:

```bash
gcm config set coauthor "Tên Bạn <ban@example.com>"
gcm config set coauthor off
```

#### System prompt (cách AI viết message)

gcm chọn system prompt theo thứ tự ưu tiên:

1. File `~/.config/gcm/system_prompt.md` — cho prompt dài nhiều dòng (ưu tiên cao nhất)
2. Key `"system_prompt"` trong `config.json` — override ngắn
3. Prompt mặc định built-in

Placeholder `{lang}` trong prompt sẽ được thay bằng câu chỉ định ngôn ngữ theo
`--vi`/`--en`; nếu prompt không có `{lang}`, câu ngôn ngữ tự được nối vào cuối.
`gcm config` cho biết đang dùng nguồn nào.

```bash
cp system_prompt.example.md ~/.config/gcm/system_prompt.md   # rồi sửa prompt
```

`gcm -s` (hoặc `gcm` khi chưa stage gì) liệt kê từng file để chọn bằng số:
```
Chọn file để stage (3 thay đổi):
  ●  1. added     src/app.py          ● đã stage · ○ chưa
  ○  2. modified  README.md
  ○  3. new       src/Web/Chart.razor
  số ('1 3', '1-3') · 'a' tất cả · Enter = tất cả · 'q' hủy
```

`gcm -t` mở TUI thay vì nhập số — di chuyển `↑↓` (hoặc `j`/`k`), `Space` tick chọn,
`d` xem diff file đang trỏ, `a` tất cả, `Enter` xong. Tự về chế độ nhập số nếu
terminal không hỗ trợ (vd pipe). Chạy `gcm config set tui true` để thành mặc định.

<details>
<summary>Ghi chú kỹ thuật</summary>

- Endpoint Groq `/openai/v1/chat/completions`, model `openai/gpt-oss-120b`.
- Header `User-Agent` bắt buộc (thiếu là Cloudflare chặn 403).
- Ép UTF-8 khi đọc git output & in console (tránh lỗi cp1252 trên Windows).
- Diff > 12000 ký tự bị cắt trước khi gửi.
</details>
