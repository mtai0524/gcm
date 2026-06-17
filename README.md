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
>
> If `. $PROFILE` errors with *"running scripts is disabled on this system"*,
> allow local scripts once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
> (answer `Y`), then re-run `. $PROFILE`.
</details>

**API key** — resolved in order: env `GROQ_API_KEY` → file `~/.config/gcm/config`
(Windows: `%USERPROFILE%\.config\gcm\config`, one line: `gsk_...`).

### Install on Windows (MSI)

Prefer a one-click install on Windows (no Git Bash, no manual Python)?

1. Go to the [Releases page](https://github.com/mtai0524/gcm/releases).
2. Download the latest `gcm-X.Y.Z.msi`.
3. Run it. The installer adds `gcm` to your system `PATH`.
4. Open a **new** terminal (PowerShell or CMD) and run `gcm -h`.

> If `gcm` still resolves to the built-in PowerShell alias (the profile step
> didn't run), set it up by hand — run in **PowerShell**:
>
> ```powershell
> # allow local scripts once, if . $PROFILE is blocked
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned   # answer Y
>
> if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Force -Path $PROFILE | Out-Null }
> Add-Content $PROFILE @'
>
> if (Test-Path Alias:gcm) { Remove-Item Alias:gcm -Force }
> function gcm { & "$env:LOCALAPPDATA\Programs\gcm\gcm.exe" @args }
> '@
> . $PROFILE
> ```

> The MSI is unsigned, so Windows SmartScreen may warn on first run — choose
> "More info" → "Run anyway". Update by downloading a newer MSI (`gcm -u`
> self-update only works for the git-cloned install).

#### Build the MSI yourself

Want to produce the `.msi` from source (e.g. after editing the code)? Open
**PowerShell in the repo root** and run:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1
```

This builds `gcm.exe` with PyInstaller and packages `gcm-X.Y.Z.msi` into the
repo root. Requirements (installed once):

```powershell
winget install -e --id Python.Python.3.12      # Python 3
winget install -e --id Microsoft.DotNet.SDK.8  # .NET SDK (for WiX)
```

The script auto-installs PyInstaller and the WiX toolset. Double-click the
resulting MSI to install, or upload it to GitHub Releases.

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
coauthor = devduide <devduide@users.noreply.github.com>  # off to disable
system_prompt = ...    # short override of how the AI writes ({lang} = language)
```

CLI flags override config. Old single-line key files still work.

**Example files** are provided to copy from: `config.example` and
`system_prompt.example.md` (install.sh copies them into `~/.config/gcm/`):

```bash
cp config.example ~/.config/gcm/config            # then edit api_key, coauthor...
cp system_prompt.example.md ~/.config/gcm/system_prompt.md   # then edit the prompt
```

#### Coauthor (collaborate with devduide)

When you **push from gcm**, it appends a `Co-authored-by:` trailer so the commit
credits a collaborator (GitHub shows the coauthor avatar). Defaults to `devduide`.
Change it to your own name/email, or set `coauthor = off` to disable entirely:

```ini
coauthor = Your Name <you@example.com>
# coauthor = off
```

#### System prompt (how the AI writes messages)

gcm picks the system prompt in priority order:

1. File `~/.config/gcm/system_prompt.md` — for long multi-line prompts (highest priority)
2. `system_prompt = ...` line in config — short one-line override
3. Built-in default prompt

A `{lang}` placeholder in the prompt is replaced with the language instruction per
`--vi`/`--en`; if the prompt has no `{lang}`, the language line is appended. Run
`gcm config` to see which source is active.

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
