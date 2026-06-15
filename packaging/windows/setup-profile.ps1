# setup-profile.ps1 - cau hinh lenh 'gcm' cho PowerShell, chay boi MSI luc cai/go.
#
# Vi sao can: 'gcm' la alias BUILT-IN cua PowerShell (= Get-Command), va alias
# duoc uu tien hon ca file .exe tren PATH. Nen du gcm.exe da cai, go 'gcm' van
# ra Get-Command. Cach duy nhat de 'gcm' goi duoc tool la ghi de trong profile:
# xoa alias roi dinh nghia function tro toi gcm.exe.
param([string]$Action = "install")

# Ghi DUOI DANG literal $env:LOCALAPPDATA de profile tu resolve luc chay
# (khong hardcode username, khong vo khi doi may).
$exe = '$env:LOCALAPPDATA\Programs\gcm\gcm.exe'
$block = @(
    "# gcm - git commit message generator (managed by gcm installer)",
    'if (Test-Path Alias:gcm) { Remove-Item Alias:gcm -Force }',
    "function gcm { & `"$exe`" @args }"
)

# Ho tro ca Windows PowerShell 5 va PowerShell 7
$profiles = @(
    (Join-Path $HOME 'Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1'),
    (Join-Path $HOME 'Documents\PowerShell\Microsoft.PowerShell_profile.ps1')
)

foreach ($p in $profiles) {
    $dir = Split-Path $p
    $exists = Test-Path -LiteralPath $p
    if (-not $exists -and $Action -eq 'uninstall') { continue }

    # Giu lai moi dong KHONG dinh toi gcm (xoa cau hinh gcm cu/trung lap)
    $kept = @()
    if ($exists) {
        $kept = @(Get-Content -LiteralPath $p | Where-Object { $_ -notmatch 'gcm' })
    }

    if ($Action -eq 'install') {
        if (-not (Test-Path -LiteralPath $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
        $kept = $kept + $block
    }

    Set-Content -LiteralPath $p -Value $kept -Encoding UTF8
}
