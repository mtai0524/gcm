# gcm — Windows MSI & GitHub Releases Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mỗi khi push tag `vX.Y.Z`, GitHub Actions tự build `gcm.exe` (PyInstaller) → `gcm-X.Y.Z.msi` (WiX v5) và đính kèm vào một GitHub Release.

**Architecture:** Một CLI Python một file (`gcm`, stdlib-only) được PyInstaller đóng thành `gcm.exe` độc lập trên runner `windows-latest`, rồi WiX gói thành MSI tự thêm vào PATH hệ thống. Version lấy từ hằng `VERSION` trong `gcm`; tag git phải khớp, CI kiểm tra.

**Tech Stack:** Python 3.12, PyInstaller (`--onefile`), WiX Toolset v5 (`dotnet tool`), GitHub Actions (`windows-latest`), `softprops/action-gh-release`.

**Lưu ý về môi trường:** Máy phát triển là Linux nên **không** build được MSI tại chỗ. Các bước "test" cục bộ chỉ xác minh: (a) PyInstaller freeze được `gcm`, (b) file `.wxs` đúng cú pháp XML, (c) file workflow đúng cú pháp YAML, (d) logic trích xuất version đúng. Build MSI thật chạy trên GitHub Actions khi push tag.

**Thư mục làm việc cho mọi lệnh:** `/home/devduide/devduide_project/tools/gcm` (đây là git repo, remote `origin` = github.com/mtai0524/gcm).

---

## File Structure

- Create: `packaging/windows/gcm.wxs` — mã nguồn WiX v5: cài `gcm.exe` vào Program Files, thêm PATH hệ thống, MajorUpgrade, mục Add/Remove Programs.
- Create: `.github/workflows/release.yml` — workflow build exe → msi → release khi push tag `v*`.
- Create: `.gitignore` bổ sung — bỏ qua `build/`, `dist/`, `*.spec`, `*.msi` sinh ra khi build cục bộ.
- Modify: `README.md` — thêm mục "Install on Windows (MSI)".
- Modify: `README.vi.md` — thêm mục "Cài trên Windows (MSI)".

---

### Task 1: De-risk — xác minh PyInstaller freeze được `gcm` cục bộ

Mục tiêu: chứng minh lệnh build và entry-point hoạt động trước khi viết CI.

**Files:** (không tạo file nguồn; chỉ build tạm rồi xoá)

- [ ] **Step 1: Cài PyInstaller (môi trường local)**

Run:
```bash
cd /home/devduide/devduide_project/tools/gcm
pip install --user pyinstaller
```
Expected: cài thành công (hoặc "already satisfied").

- [ ] **Step 2: Tạo bản sao entry-point có đuôi `.py`**

PyInstaller ổn định hơn khi script có đuôi `.py`. File gốc tên `gcm` (không đuôi) vẫn giữ nguyên; ta build từ bản sao.

Run:
```bash
cd /home/devduide/devduide_project/tools/gcm
cp gcm gcm_entry.py
```
Expected: tạo `gcm_entry.py`.

- [ ] **Step 3: Build onefile và đặt tên output là `gcm`**

Run:
```bash
cd /home/devduide/devduide_project/tools/gcm
pyinstaller --onefile --name gcm gcm_entry.py
```
Expected: tạo `dist/gcm` (binary Linux ELF), không lỗi import.

- [ ] **Step 4: Smoke test binary**

Run:
```bash
cd /home/devduide/devduide_project/tools/gcm
./dist/gcm -v
```
Expected output: `gcm v2.0.0`

- [ ] **Step 5: Dọn dẹp các sản phẩm build tạm**

Run:
```bash
cd /home/devduide/devduide_project/tools/gcm
rm -rf build dist gcm.spec gcm_entry.py
```
Expected: thư mục sạch, chỉ còn các file nguồn ban đầu.

> Không commit ở task này — chỉ là kiểm chứng. Nếu Step 4 fail, dừng lại và báo: nghĩa là `gcm` có vấn đề khi freeze và cần xử lý trước khi làm CI.

---

### Task 2: Tạo mã nguồn WiX `packaging/windows/gcm.wxs`

**Files:**
- Create: `packaging/windows/gcm.wxs`

- [ ] **Step 1: Tạo thư mục và file WiX**

Tạo file `packaging/windows/gcm.wxs` với nội dung chính xác sau (GUID đã sinh sẵn, cố định — KHÔNG đổi giữa các bản phát hành, nếu không nâng cấp sẽ hỏng):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">
  <Package
      Name="gcm"
      Manufacturer="devduide"
      Version="$(Version)"
      UpgradeCode="86B66A85-F6A0-4061-AE53-8F52B10FC1BD"
      Scope="perMachine"
      Compressed="yes">

    <MajorUpgrade DowngradeErrorMessage="A newer version of gcm is already installed." />
    <MediaTemplate EmbedCab="yes" />

    <!-- Thong tin hien trong Add/Remove Programs -->
    <Property Id="ARPURLINFOABOUT" Value="https://github.com/mtai0524/gcm" />
    <Property Id="ARPHELPLINK" Value="https://github.com/mtai0524/gcm" />

    <StandardDirectory Id="ProgramFiles64Folder">
      <Directory Id="INSTALLFOLDER" Name="gcm">
        <Component Id="GcmExe" Bitness="always64">
          <File Id="GcmExeFile" Source="dist/gcm.exe" KeyPath="yes" />
        </Component>
        <Component Id="GcmPath" Guid="ABB8F2A6-399B-4846-A72C-259FDCAB3A06" Bitness="always64">
          <Environment Id="PathEnv" Name="PATH" Value="[INSTALLFOLDER]"
                       Part="last" Action="set" System="yes" Permanent="no" />
        </Component>
      </Directory>
    </StandardDirectory>

    <Feature Id="Main" Title="gcm" Level="1">
      <ComponentRef Id="GcmExe" />
      <ComponentRef Id="GcmPath" />
    </Feature>
  </Package>
</Wix>
```

- [ ] **Step 2: Kiểm tra file đúng cú pháp XML (well-formed)**

Run:
```bash
cd /home/devduide/devduide_project/tools/gcm
python3 -c "import xml.dom.minidom; xml.dom.minidom.parse('packaging/windows/gcm.wxs'); print('XML OK')"
```
Expected output: `XML OK`

- [ ] **Step 3: Commit**

```bash
cd /home/devduide/devduide_project/tools/gcm
git add packaging/windows/gcm.wxs
git commit -m "build: add WiX source for Windows MSI packaging

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Tạo workflow phát hành `.github/workflows/release.yml`

**Files:**
- Create: `.github/workflows/release.yml`

- [ ] **Step 1: Tạo file workflow**

Tạo `.github/workflows/release.yml` với nội dung chính xác sau:

```yaml
name: release

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Determine and check version
        id: ver
        shell: bash
        run: |
          VERSION=$(python -c "import re;print(re.search(r'^VERSION = \"([^\"]+)\"', open('gcm').read(), re.M).group(1))")
          echo "version=$VERSION" >> "$GITHUB_OUTPUT"
          echo "gcm VERSION = $VERSION"
          if [ "${GITHUB_REF_TYPE}" = "tag" ]; then
            TAG="${GITHUB_REF_NAME#v}"
            if [ "$TAG" != "$VERSION" ]; then
              echo "::error::Tag $GITHUB_REF_NAME does not match VERSION $VERSION in gcm"
              exit 1
            fi
          fi

      - name: Install PyInstaller
        run: pip install pyinstaller

      - name: Build gcm.exe
        shell: bash
        run: |
          cp gcm gcm_entry.py
          pyinstaller --onefile --name gcm gcm_entry.py

      - name: Smoke test gcm.exe
        shell: bash
        run: |
          OUT=$(./dist/gcm.exe -v)
          echo "$OUT"
          echo "$OUT" | grep -q "gcm v${{ steps.ver.outputs.version }}"

      - name: Install WiX
        run: dotnet tool install --global wix

      - name: Build MSI
        shell: bash
        run: |
          wix build packaging/windows/gcm.wxs -d Version=${{ steps.ver.outputs.version }} -o gcm-${{ steps.ver.outputs.version }}.msi

      - name: Create GitHub Release
        if: github.ref_type == 'tag'
        uses: softprops/action-gh-release@v2
        with:
          files: gcm-${{ steps.ver.outputs.version }}.msi
          generate_release_notes: true
```

- [ ] **Step 2: Kiểm tra file đúng cú pháp YAML**

Run:
```bash
cd /home/devduide/devduide_project/tools/gcm
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml')); print('YAML OK')" 2>/dev/null \
  || (pip install --user pyyaml >/dev/null 2>&1 && python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml')); print('YAML OK')")
```
Expected output: `YAML OK`

- [ ] **Step 3: Commit**

```bash
cd /home/devduide/devduide_project/tools/gcm
git add .github/workflows/release.yml
git commit -m "ci: add release workflow to build Windows MSI on version tags

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Bỏ qua sản phẩm build cục bộ trong `.gitignore`

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Đọc `.gitignore` hiện tại**

Run:
```bash
cd /home/devduide/devduide_project/tools/gcm
cat .gitignore
```
Expected: thấy `__pycache__/` và `*.pyc`.

- [ ] **Step 2: Thêm các pattern build**

Thêm các dòng sau vào cuối `.gitignore`:
```
build/
dist/
*.spec
*.msi
gcm_entry.py
```

- [ ] **Step 3: Xác minh không có file build nào đang được theo dõi**

Run:
```bash
cd /home/devduide/devduide_project/tools/gcm
git status --porcelain
```
Expected: chỉ thấy `.gitignore` bị sửa (M), không có `dist/`, `build/`, `*.msi` xuất hiện.

- [ ] **Step 4: Commit**

```bash
cd /home/devduide/devduide_project/tools/gcm
git add .gitignore
git commit -m "chore: ignore PyInstaller and MSI build artifacts

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Bổ sung hướng dẫn cài MSI vào README (EN + VI)

**Files:**
- Modify: `README.md`
- Modify: `README.vi.md`

- [ ] **Step 1: Đọc README.md để tìm chỗ chèn (gần mục Install/Installation)**

Run:
```bash
cd /home/devduide/devduide_project/tools/gcm
grep -niE "install|cài|## " README.md | head -30
```
Expected: thấy vị trí các heading để chèn mục mới ngay sau phần cài đặt hiện có.

- [ ] **Step 2: Chèn mục Windows MSI vào `README.md`**

Thêm khối sau vào `README.md`, đặt ngay sau phần hướng dẫn install hiện có (sau heading Install/Installation, trước phần Usage):

```markdown
### Install on Windows (MSI)

Prefer a one-click install on Windows (no Git Bash, no manual Python)?

1. Go to the [Releases page](https://github.com/mtai0524/gcm/releases).
2. Download the latest `gcm-X.Y.Z.msi`.
3. Run it. The installer adds `gcm` to your system `PATH`.
4. Open a **new** terminal (PowerShell or CMD) and run `gcm -h`.

> The MSI is unsigned, so Windows SmartScreen may warn on first run — choose
> "More info" → "Run anyway". Update by downloading a newer MSI (`gcm -u`
> self-update only works for the git-cloned install).
```

- [ ] **Step 3: Chèn mục tương ứng vào `README.vi.md`**

Thêm khối sau vào `README.vi.md`, cùng vị trí tương ứng (sau phần cài đặt hiện có):

```markdown
### Cài trên Windows (MSI)

Muốn cài một phát trên Windows (không cần Git Bash, không cần tự cài Python)?

1. Vào [trang Releases](https://github.com/mtai0524/gcm/releases).
2. Tải file `gcm-X.Y.Z.msi` mới nhất.
3. Chạy nó. Trình cài tự thêm `gcm` vào `PATH` hệ thống.
4. Mở terminal **mới** (PowerShell hoặc CMD) rồi gõ `gcm -h`.

> MSI chưa ký số nên Windows SmartScreen có thể cảnh báo lần đầu — chọn
> "More info" → "Run anyway". Cập nhật bằng cách tải MSI mới hơn (lệnh tự cập
> nhật `gcm -u` chỉ dùng được cho bản cài bằng git clone).
```

- [ ] **Step 4: Commit**

```bash
cd /home/devduide/devduide_project/tools/gcm
git add README.md README.vi.md
git commit -m "docs: document Windows MSI install from GitHub Releases

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Push lên GitHub và cắt bản release đầu tiên

**Files:** (không sửa file; thao tác git/CI)

- [ ] **Step 1: Push các commit lên origin**

Run:
```bash
cd /home/devduide/devduide_project/tools/gcm
git push origin master
```
Expected: push thành công.

- [ ] **Step 2: (Tùy chọn) Chạy thử workflow thủ công trước khi tag**

Trên GitHub: tab **Actions** → workflow **release** → **Run workflow** (nhánh master).
Hoặc bằng CLI nếu có `gh`:
```bash
cd /home/devduide/devduide_project/tools/gcm
gh workflow run release.yml --ref master
```
Expected: workflow chạy, build ra MSI (không tạo release vì không phải tag). Mục đích: bắt lỗi build sớm.

> Nếu bước này fail, đọc log job trên GitHub Actions, sửa `gcm.wxs` hoặc `release.yml`,
> commit, push lại, rồi chạy lại trước khi gắn tag.

- [ ] **Step 3: Gắn tag khớp `VERSION` và push tag**

`VERSION` hiện là `2.0.0`, nên tag phải là `v2.0.0`:
```bash
cd /home/devduide/devduide_project/tools/gcm
git tag v2.0.0
git push origin v2.0.0
```
Expected: workflow `release` tự chạy, build MSI, và tạo Release `v2.0.0` đính kèm `gcm-2.0.0.msi`.

- [ ] **Step 4: Xác minh release**

Mở `https://github.com/mtai0524/gcm/releases` và kiểm tra:
- Có release `v2.0.0`.
- Có file đính kèm `gcm-2.0.0.msi` tải về được.

> Quy trình phát hành về sau: sửa `VERSION` trong `gcm` → commit → push → `git tag vX.Y.Z && git push origin vX.Y.Z`.

---

## Self-Review (đã thực hiện)

- **Spec coverage:** WiX source (Task 2) ✓, workflow build+check+release (Task 3) ✓, version là nguồn duy nhất + kiểm tra tag khớp (Task 3 Step 1) ✓, smoke test `gcm.exe -v` (Task 3) ✓, README EN+VI (Task 5) ✓, hai hạn chế đã biết được nêu trong README (Task 5) ✓. PyInstaller+WiX (không phải cx_Freeze) ✓.
- **Placeholder scan:** không có TBD/TODO; mọi bước có lệnh và nội dung file đầy đủ.
- **Type/string consistency:** tên `INSTALLFOLDER`, `GcmExe`, `GcmPath`, output `gcm v2.0.0`, biến `$(Version)` ↔ `-d Version=`, output `steps.ver.outputs.version`, tên file `gcm-X.Y.Z.msi` đồng nhất giữa các task. GUID `UpgradeCode`/`GcmPath` cố định và khớp giá trị đã sinh.
