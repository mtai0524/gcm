<#
build.ps1 - Build file cai gcm-X.Y.Z.msi ngay tren may Windows (khong can GitHub Actions).

Yeu cau:
  - Python 3   (winget install Python.Python.3.12)
  - .NET SDK   (winget install Microsoft.DotNet.SDK.8)  -> can cho WiX

Cach dung (mo PowerShell trong thu muc repo gcm):
  powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1

Ket qua: file gcm-X.Y.Z.msi nam o thu muc goc cua repo.
#>

$ErrorActionPreference = 'Stop'

# 0. Ve thu muc goc repo (script nam o packaging\windows\)
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $RepoRoot
Write-Host "==> Repo: $RepoRoot"

# 1. Tim Python
$py = $null
foreach ($c in 'py', 'python', 'python3') {
    if (Get-Command $c -ErrorAction SilentlyContinue) { $py = $c; break }
}
if (-not $py) {
    throw "Khong tim thay Python. Cai: winget install Python.Python.3.12 roi mo lai PowerShell."
}
Write-Host "==> Python: $py"

# 2. Doc VERSION tu file gcm (nguon chan ly duy nhat)
$m = Select-String -Path 'gcm' -Pattern '^VERSION = "([^"]+)"' | Select-Object -First 1
if (-not $m) { throw "Khong doc duoc VERSION trong file gcm." }
$Version = $m.Matches[0].Groups[1].Value
Write-Host "==> Version: $Version"

# 3. Cai PyInstaller
Write-Host "==> Cai PyInstaller..."
& $py -m pip install --upgrade pyinstaller

# 4. Build gcm.exe (copy sang .py cho PyInstaller on dinh)
Write-Host "==> Build gcm.exe..."
Copy-Item gcm gcm_entry.py -Force
# gcm_gui.py da nam o thu muc goc repo; --paths . de PyInstaller tim thay no.
& $py -m PyInstaller --onefile --name gcm `
    --hidden-import gcm_gui `
    --paths . `
    gcm_entry.py

# 5. Smoke test: gcm.exe -v phai in 'gcm v<Version>'
$out = (& .\dist\gcm.exe -v) -join "`n"
Write-Host "    gcm.exe -v -> $out"
if ($out -notmatch ("gcm v" + [regex]::Escape($Version))) {
    throw "Smoke test that bai: '$out' khong chua 'gcm v$Version'."
}

# 6. Dam bao co .NET SDK + WiX v5
if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    throw "Khong tim thay .NET SDK. Cai: winget install Microsoft.DotNet.SDK.8 roi mo lai PowerShell."
}
$wix = dotnet tool list --global | Select-String -Pattern '^\s*wix\s'
if (-not $wix) {
    Write-Host "==> Cai WiX v5..."
    dotnet tool install --global wix --version 5.*
}
# Dam bao thu muc tool global nam trong PATH cua phien nay
$toolsDir = Join-Path $env:USERPROFILE '.dotnet\tools'
if ($env:PATH -notlike "*$toolsDir*") { $env:PATH = "$env:PATH;$toolsDir" }

# 6b. Cai WiX UI extension - PHAI CUNG VERSION voi wix (vd 5.0.2), neu khong
#     'wix extension add' se lay ban moi nhat (7.x) -> WIX0144 not found.
$WixVer = ((& wix --version) -replace '\+.*$', '').Trim()
Write-Host "==> Cai WiX UI extension khop wix v$WixVer..."
wix extension add -g "WixToolset.UI.wixext/$WixVer"

# 7. Dong goi MSI (kem -ext UI)
$Msi = "gcm-$Version.msi"
Write-Host "==> Build $Msi..."
wix build -arch x64 -ext WixToolset.UI.wixext packaging\windows\gcm.wxs -d Version=$Version -o $Msi

# 8. Don dep san pham build trung gian (giu lai file .msi)
Remove-Item -Recurse -Force build, dist, gcm.spec, gcm_entry.py -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "==> XONG! File cai: $(Join-Path $RepoRoot $Msi)"
Write-Host "    Bam doi de cai, hoac upload len GitHub Releases (keo-tha tren web, mien phi)."
