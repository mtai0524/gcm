# gcm — Git Commit Message generator

[English](README.md) · [Tiếng Việt](README.vi.md)

AI commit messages from your staged diff, via Groq (free). Pure Python, no dependencies.

**Need:** Python 3.7+ · Groq API key (free): https://console.groq.com/keys

---

## 1. Install

**Step 1 — Python** *(skip if `python --version` already works)*

| OS | Command |
|----|---------|
| Windows | `winget install -e --id Python.Python.3.12` |
| macOS | `brew install python` |
| Linux | `sudo apt install python3` |

> **Windows:** after installing, turn off the fake Microsoft Store aliases
> (Settings → Apps → Advanced app settings → **App execution aliases** → off
> `python.exe`, `python3.exe`), then reopen the terminal. Otherwise you'll get
> *"No installed Python found!"*.

**Step 2 — gcm**

<details open>
<summary><b>Linux / macOS / Git Bash</b></summary>

```bash
git clone https://github.com/mtai0524/gcm.git ~/tools/gcm
bash ~/tools/gcm/install.sh
```
`install.sh` creates the `gcm` command, adds it to PATH, and asks for your API key.
Open a new terminal → `gcm -h`.
</details>

<details>
<summary><b>Windows — PowerShell</b></summary>

`gcm` is a built-in PowerShell alias, so override it with a function in `$PROFILE`.

```powershell
# 1. clone
git clone https://github.com/mtai0524/gcm.git $HOME\tools\gcm

# 2. save API key
New-Item -ItemType Directory -Force -Path $HOME\.config\gcm | Out-Null
"gsk_..." | Out-File -Encoding ascii -NoNewline $HOME\.config\gcm\config

# 3. add gcm to $PROFILE
if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Force -Path $PROFILE | Out-Null }
Add-Content $PROFILE @'

if (Test-Path Alias:gcm) { Remove-Item Alias:gcm -Force }
function gcm { py "$HOME\tools\gcm\gcm" @args }
'@

# 4. reload & check
. $PROFILE
gcm -h
```
> If `py` fails, change `py` → `python` in the `function gcm` line.
</details>

**API key** — resolved in order: env `GROQ_API_KEY` → file `~/.config/gcm/config`
(Windows: `%USERPROFILE%\.config\gcm\config`, one line: `gsk_...`).

---

## 2. Update

Easiest — let gcm update itself (works on any OS, no path to remember):
```bash
gcm -u
```

Manual fallback (`git pull` in the clone):
```bash
git -C ~/tools/gcm pull          # PowerShell: git -C $HOME\tools\gcm pull
```

`gcm` points at the cloned folder, so pulling is all you need — no reinstall.

---

## Usage

| Command | |
|---------|--|
| `gcm`            | generate message + ask to commit |
| `gcm -s`         | pick files to stage by number, then generate |
| `gcm -t`         | pick files in a TUI (↑↓ + space, `d` = view diff) |
| `gcm -m "hint"`  | give the model extra context |
| `gcm -y`         | commit immediately, no prompt |
| `gcm --push`     | auto-push after commit |
| `gcm --amend`    | reword the last commit |
| `gcm --vi` / `--en` | message language for this run |
| `gcm -a`         | `git add -A` first, then generate |
| `gcm -p`         | print message only (no prompt) |
| `gcm --model X`  | use model `X` (or env `GCM_MODEL`) for this run |
| `gcm config`     | show current config |
| `gcm -u`         | update gcm to the latest version |
| `gcm -h` / `-v`  | help / version |

After generating: `[Enter]` commit · `[p]` commit+push · `[e]` edit · `[r]` regenerate · `[n]` cancel.
The header shows your branch and unpushed commit count (`main ↑2`).

**Smart diff:** lockfiles (`package-lock.json`, `yarn.lock`...), `*.min.js` and binary
files are still committed but their content is not sent to the LLM; oversized files
are summarized with `--stat` instead of being cut off mid-diff.

### Config file (`~/.config/gcm/config`)

Set defaults once, skip the flags (`key = value`, all optional):

```ini
api_key = gsk_...      # free: https://console.groq.com/keys
lang = vi              # default message language
model = llama-3.3-70b-versatile
tui = true             # default to TUI file picker
push = ask             # ask | always | never
```

CLI flags override config. Old single-line key files still work.

`gcm -s` (or `gcm` when nothing is staged) lists each changed file to pick by number:
```
Chọn file để stage (3 thay đổi):
  ●  1. added     src/app.py          ● staged · ○ not staged
  ○  2. modified  README.md
  ○  3. new       src/Web/Chart.razor
  số ('1 3', '1-3') · 'a' tất cả · Enter = tất cả · 'q' hủy
```

`gcm -t` opens a TUI instead — move with `↑↓` (or `j`/`k`), toggle with `Space`,
`d` to preview the diff of the highlighted file, `a` for all, `Enter` to confirm.
Falls back to the numbered picker if the terminal doesn't support it (e.g. piped
input). Set `tui = true` in the config to make it the default.

<details>
<summary>Technical notes</summary>

- Groq endpoint `/openai/v1/chat/completions`, model `llama-3.3-70b-versatile`.
- `User-Agent` header is required (without it Cloudflare returns 403).
- Forces UTF-8 on git output & console (avoids cp1252 errors on Windows).
- Diffs over 12000 chars are truncated before sending.
</details>
