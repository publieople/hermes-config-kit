# diag-autostart.ps1
# 诊断 Windows 开机自启失败的四件事。管理员 PowerShell 跑一次即可。
# 用法: powershell -NoProfile -ExecutionPolicy Bypass -File diag-autostart.ps1

$lnkCandidates = @(
    "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
    "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\Startup"
)
$lnkCandidates | ForEach-Object {
    if (Test-Path $_) {
        Get-ChildItem -Path $_ -Filter *.lnk | ForEach-Object {
            Write-Host "=== .lnk: $($_.FullName) ===" -ForegroundColor Cyan
            $shell = New-Object -ComObject WScript.Shell
            $sc = $shell.CreateShortcut($_.FullName)
            $sc | Format-List TargetPath, WorkingDirectory, Arguments, IconLocation, Description
            $bytes = [IO.File]::ReadAllBytes($_.FullName)
            $flags = [BitConverter]::ToUInt32($bytes, 0x14)
            Write-Host ("LinkFlags: 0x{0:X8}" -f $flags)
            Write-Host ("  RunAsUser 0x8000:   " + ([bool]($flags -band 0x8000)))
            Write-Host ("  HasLinkInfo 0x02:  " + ([bool]($flags -band 0x0002)))
            Write-Host ("  IsUnicode 0x80:    " + ([bool]($flags -band 0x0080)))
        }
    }
}

Write-Host "`n=== 最近 24h 应用错误 (匹配 AHK / 脚本名 / SmartScreen) ===" -ForegroundColor Cyan
Get-WinEvent -LogName Application -MaxEvents 300 -ErrorAction SilentlyContinue |
    Where-Object { $_.TimeCreated -gt (Get-Date).AddHours(-24) -and (
        $_.Message -match 'AutoHotKey|replace\.ahk|AHK|SmartScreen' -or
        $_.ProviderName -match 'AutoHotKey|AHK|SmartScreen') } |
    Select-Object -First 8 TimeCreated, ProviderName, Id, LevelDisplayName,
        @{n='Msg';e={ $_.Message.Substring(0, [Math]::Min(220, $_.Message.Length)) }} |
    Format-Table -AutoSize -Wrap

Write-Host "=== 最近 24h Defender 阻断 ===" -ForegroundColor Cyan
try {
    Get-WinEvent -LogName 'Microsoft-Windows-Windows Defender/Operational' -MaxEvents 200 -ErrorAction SilentlyContinue |
        Where-Object { $_.TimeCreated -gt (Get-Date).AddHours(-24) -and $_.Id -in 1116,1117,1121,1129,1131,1132 } |
        Select-Object -First 8 TimeCreated, Id,
            @{n='Msg';e={ $_.Message.Substring(0, [Math]::Min(200, $_.Message.Length)) }} |
        Format-Table -AutoSize -Wrap
} catch { Write-Host "Defender 日志不可读: $_" -ForegroundColor Yellow }

Write-Host "=== 现有计划任务 (匹配 AHK / replace / AutoHotKey) ===" -ForegroundColor Cyan
Get-ScheduledTask | Where-Object { $_.TaskName -match 'AHK|replace|AutoHotKey' } |
    Format-Table TaskName, State, TaskPath -AutoSize

Write-Host "=== HKCU Run 注册表 ===" -ForegroundColor Cyan
Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -ErrorAction SilentlyContinue |
    Format-List

Write-Host "=== SmartScreen ===" -ForegroundColor Cyan
Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer' -ErrorAction SilentlyContinue |
    Select-Object SmartScreenEnabled, EnableSmartScreen | Format-List