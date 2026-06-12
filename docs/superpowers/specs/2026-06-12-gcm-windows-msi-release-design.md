# gcm — Đóng gói MSI cho Windows & phát hành qua GitHub Releases

Ngày: 2026-06-12
Trạng thái: Đã duyệt thiết kế

## Mục tiêu

Tạo trang **GitHub Releases** cho `gcm`, mỗi khi ra phiên bản mới sẽ **tự build** một
file cài đặt **`.msi` cho Windows** và đính kèm vào release để người dùng tải về cài
trực tiếp — **không cần Git Bash, không cần tự cài Python**.

`gcm` hiện là một CLI Python một file (865 dòng, chỉ dùng stdlib), đã có sẵn trên
GitHub (`https://github.com/mtai0524/gcm.git`) với `install.sh` cho Linux/macOS/Git Bash.
Việc này bổ sung đường cài chính quy cho Windows, không thay đổi cách cài hiện có.

## Hướng tiếp cận

Build chạy trên **runner `windows-latest` của GitHub Actions** (máy phát triển là Linux,
không build được artifact Windows tại chỗ).

Chuỗi build: **PyInstaller** (`gcm` → `gcm.exe`, nhúng sẵn trình thông dịch Python) →
**WiX v5** (`gcm.exe` → `gcm-X.Y.Z.msi`, tự thêm vào PATH).

Lý do chọn PyInstaller + WiX thay vì `cx_Freeze bdist_msi`: kiểm soát tốt việc thêm PATH,
mục Add/Remove Programs, và logic nâng cấp; người dùng cuối không cần cài Python.

## Nguồn version duy nhất

- Hằng `VERSION` trong file `gcm` (hiện `"2.0.0"`, dòng 47) là nguồn chân lý duy nhất.
- Release được kích hoạt bằng tag git dạng `vX.Y.Z`.
- CI **kiểm tra tag khớp `VERSION`**; nếu lệch thì fail sớm trước khi build.

## Thành phần thêm vào repo

### 1. `packaging/windows/gcm.wxs` (mã nguồn WiX v5)
- Cài `gcm.exe` vào `C:\Program Files\gcm\`.
- Thêm thư mục cài vào **PATH hệ thống** (machine-wide) để gõ được `gcm` ở mọi terminal.
- Có mục trong **Add/Remove Programs** (Programs and Features) với tên, version, publisher
  (`devduide`), và đường dẫn gỡ cài.
- `UpgradeCode` cố định + `MajorUpgrade` để cài bản mới tự gỡ bản cũ.
- Version của MSI nhận qua biến `-d Version=X.Y.Z` lúc `wix build`.

### 2. `.github/workflows/release.yml`
Kích hoạt: `on: push: tags: ['v*']` (kèm tùy chọn `workflow_dispatch` để build thử thủ công).

Job `build-windows` trên `windows-latest`:
1. `actions/checkout`
2. `actions/setup-python` (3.12)
3. Bước **kiểm tra version**: đọc `VERSION` từ file `gcm`, so với tag; lệch → fail.
4. `pip install pyinstaller`
5. `pyinstaller --onefile --name gcm gcm` → `dist/gcm.exe`
6. **Smoke test**: chạy `dist/gcm.exe -v`, kỳ vọng output chứa `gcm v<VERSION>`.
7. Cài WiX: `dotnet tool install --global wix`
8. `wix build packaging/windows/gcm.wxs -d Version=<VERSION> -o gcm-<VERSION>.msi`
9. Tạo **GitHub Release** cho tag, đính kèm `gcm-<VERSION>.msi`
   (dùng `softprops/action-gh-release` hoặc `gh release create`).

### 3. README
Thêm mục "Cài trên Windows (MSI)" trỏ tới trang Releases và mô tả ngắn cách cài/gỡ.

## Luồng phát hành (cho maintainer)

1. Sửa `VERSION` trong `gcm`.
2. `git commit` thay đổi.
3. `git tag vX.Y.Z && git push --tags`.
4. GitHub Actions tự build `gcm.exe` → `gcm-X.Y.Z.msi` → tạo release đính kèm MSI.

## Xử lý lỗi

- Tag không khớp `VERSION` → fail ở bước kiểm tra (trước khi tốn công build).
- PyInstaller / smoke test / WiX lỗi → job fail, không tạo release.

## Kiểm thử

- **Smoke test trong CI**: `gcm.exe -v` phải in đúng version trước khi đóng MSI.
- (Tùy chọn, không bắt buộc ở bản đầu) Cài thử MSI im lặng trên runner
  (`msiexec /i ... /quiet`) rồi gọi `gcm -v` để xác minh PATH — để sau nếu cần.

## Hạn chế đã biết (chấp nhận được ở bản đầu)

- **MSI chưa ký số**: Windows SmartScreen sẽ cảnh báo khi cài. Ký số cần chứng chỉ trả
  phí — để dành cho sau.
- **`gcm -u` không dùng được cho bản cài MSI**: lệnh tự cập nhật chạy `git pull` trong
  thư mục nguồn; bản MSI không có git repo. Người dùng MSI cập nhật bằng cách tải MSI mới.
  Không đổi hành vi `gcm -u` ở bản này (nó đã báo lỗi hợp lý khi không có repo).

## Ngoài phạm vi

- Không build binary Linux/macOS trong release lần này (đã có `install.sh`).
- Không ký số MSI.
- Không đổi logic nội tại của `gcm` ngoài việc đảm bảo `VERSION`/`-v` hoạt động cho exe.
