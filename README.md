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

# 2. save API key (or run `gcm config set api_key gsk_...` after step 4)
New-Item -ItemType Directory -Force -Path $HOME\.config\gcm | Out-Null
'{ "api_key": "gsk_..." }' | Out-File -Encoding utf8 $HOME\.config\gcm\config.json

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

**API key** — resolved in order: env `GROQ_API_KEY` → `~/.config/gcm/config.json`
(Windows: `%USERPROFILE%\.config\gcm\config.json`). Easiest way to set it:
`gcm config set api_key gsk_...`

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
resulting MSI to install.

#### Publishing a release (automatic)

You never upload an MSI by hand. Bump `VERSION` in `gcm`, commit, push to
`master` — GitHub Actions (`.github/workflows/release.yml`) runs the tests,
builds the MSI on a Windows runner, and creates tag `vX.Y.Z` plus a Release with
`gcm-X.Y.Z.msi` attached. Pushes that don't change `VERSION` (or whose version is
already released) only run the tests. Pushing a tag `vX.Y.Z` by hand still works
too; the tag must match `VERSION`.

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
| `gcm config`     | show effective config + where each value comes from |
| `gcm config set KEY VALUE` | write one key to `config.json` |
| `gcm config unset KEY` | drop the override, back to the built-in default |
| `gcm -u`         | update gcm to the latest version |
| `gcm -h` / `-v`  | help / version |

After generating: `[Enter]` commit · `[p]` commit+push · `[e]` edit · `[r]` regenerate ·
`[m]` add a hint and regenerate · `[d]` view the staged diff · `[n]` cancel.
The header shows your branch, unpushed commit count and diff size (`main ↑2 · 3 file +120 −15`).

**Smart diff:** lockfiles (`package-lock.json`, `yarn.lock`...), `*.min.js` and binary
files are still committed but their content is not sent to the LLM; oversized files
are summarized with `--stat` instead of being cut off mid-diff.

### Config file (`~/.config/gcm/config.json`)

**Defaults live in the code; your file only holds what you changed.** Any key you
don't write keeps following the built-in default, so upgrades that change a default
take effect on your machine too — nothing is pinned by an old config file.

```jsonc
{
  "//": "keys starting with // are comments (JSON has none)",
  "api_key": "gsk_...",          // free: https://console.groq.com/keys
  "lang": "vi",                  // vi | en - default message language
  "model": "openai/gpt-oss-120b",
  "tui": true,                   // default to the TUI file picker
  "push": "ask",                 // ask | always | never
  "coauthor": "devduide <devduide@users.noreply.github.com>",  // "off" to disable
  "system_prompt": "..."         // short override ({lang} = language instruction)
}
```

The file gcm creates lists **every** key as a `"//key"` hint line (description +
current default) but only carries *values* for what you actually changed — so you
can see all the fields without any default being pinned. Those hint lines are
refreshed on each run; your values are never touched.

Resolution order: **CLI flag > env (`GROQ_API_KEY`, `GCM_MODEL`) > `config.json` >
built-in default**. `gcm config` prints every key with its value *and* its source:

```
config: ~/.config/gcm/config.json
  api_key        'gsk_abc...1234'          <- file
  lang           'vi'                      <- file
  model          'openai/gpt-oss-120b'     <- mac dinh
  push           'ask'                     <- mac dinh
```

Edit it by hand, or let gcm do it (values equal to the default are removed from the
file instead of being written):

```bash
gcm config set lang vi
gcm config set api_key gsk_...
gcm config unset lang      # back to the built-in default
gcm config path            # print the file path
```

Invalid JSON or a bad value (e.g. `"push": "sometimes"`) is reported and ignored —
gcm keeps running on the defaults instead of failing.

> **Auto-created on first run:** the first time you run `gcm` (any install method,
> including the Windows MSI), it creates `~/.config/gcm/config.json`, a fully
> documented `config.example.json`, and `system_prompt.example.md` if missing.
> gcm **never** overwrites a config file you've edited.
>
> **Upgrading from an older gcm?** An existing `key = value` file at
> `~/.config/gcm/config` is converted to `config.json` automatically on the first
> run and kept as `config.migrated` — nothing to do by hand.

#### Coauthor (collaborate with devduide)

When you **push from gcm**, it appends a `Co-authored-by:` trailer so the commit
credits a collaborator (GitHub shows the coauthor avatar). Defaults to `devduide`.
Change it to your own name/email, or set it to `"off"` to disable entirely:

```bash
gcm config set coauthor "Your Name <you@example.com>"
gcm config set coauthor off
```

#### System prompt (how the AI writes messages)

gcm picks the system prompt in priority order:

1. File `~/.config/gcm/system_prompt.md` — for long multi-line prompts (highest priority)
2. `"system_prompt"` in `config.json` — short override
3. Built-in default prompt

A `{lang}` placeholder in the prompt is replaced with the language instruction per
`--vi`/`--en`; if the prompt has no `{lang}`, the language line is appended. Run
`gcm config` to see which source is active.

```bash
cp system_prompt.example.md ~/.config/gcm/system_prompt.md   # then edit the prompt
```

`gcm -s` (or `gcm` when nothing is staged) lists each changed file to pick by number:
```
[main ↑2] Chọn file để stage (3 thay đổi, 1 đã stage):
  ●  1. added     src/app.py          ● staged · ○ not staged
  ○  2. modified  README.md
  ○  3. new       src/Web/Chart.razor
  số ('1 3', '2-5') · 'a' tất cả · '-2' bỏ file 2 · 'i' đảo · 'd 3' diff · '?' thêm · Enter · 'q' hủy
```
What you type is the exact set that gets staged (a pre-staged ● file you leave
out is unstaged). `-2` excludes, `a -2 -4` is "all but 2 and 4", `i` inverts the
current staging, `d 3` shows file 3's diff (`d` alone: everything staged),
`t` jumps to the TUI, `Enter` keeps what's staged — or takes everything when
nothing is.

`gcm -t` opens a full-screen TUI instead — move with `↑↓` (or `j`/`k`,
`PgUp`/`PgDn`, `Home`/`End`), toggle with `Space`, `a` all / `i` invert, `d` to
open the highlighted file's diff in a scrollable pager, `Enter` to confirm, `q`
or `Esc` to cancel. Long lists scroll, long paths are shortened to fit the
terminal, and nothing is left behind in your scrollback. Files that were already
staged start ticked; un-ticking one unstages it, so what you see ticked is
exactly what gets committed. Falls back to the numbered picker if the terminal
doesn't support it (e.g. piped input). Run `gcm config set tui true` to make it
the default.

### GUI (`gcm --gui`, or double-click `gcm.exe`)

A small window for people who'd rather not type: pick a repo (the last one
reopens automatically), tick files in a scrollable list (✓ column / Space /
double-click, plus All · None · Invert), see the **diff of the selected file**
with +/− highlighting, generate the message (⚡, or 🔁 to try a different
wording), edit it in place — the title length is checked against 72 chars — and
Commit, optionally with Push. Git and API calls run in the background so the
window never freezes, and errors show up in the status bar and a dialog instead
of vanishing in a hidden console. Shortcuts: `Ctrl+G` generate, `Ctrl+Enter`
commit, `F5` reload, `Ctrl+O` choose repo. Running `gcm` outside a git repo also
opens the GUI so you can pick one.

<details>
<summary>Technical notes</summary>

- Groq endpoint `/openai/v1/chat/completions`, model `openai/gpt-oss-120b`.
- `User-Agent` header is required (without it Cloudflare returns 403).
- Forces UTF-8 on git output & console (avoids cp1252 errors on Windows).
- Diffs over 12000 chars are truncated before sending.
</details>
