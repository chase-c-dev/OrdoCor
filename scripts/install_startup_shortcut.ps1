param(
    [string]$ExePath = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ExePath)) {
    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    $ExePath = Join-Path $scriptRoot "..\release\OrdoCor.exe"
}

$resolvedExe = Resolve-Path -LiteralPath $ExePath -ErrorAction SilentlyContinue
if ($null -eq $resolvedExe) {
    Write-Error "OrdoCor.exe was not found at: $ExePath"
}

$startupFolder = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupFolder "OrdoCor.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $resolvedExe.Path
$shortcut.WorkingDirectory = Split-Path -Parent $resolvedExe.Path
$shortcut.WindowStyle = 1
$shortcut.Description = "Start OrdoCor automatically when Windows starts."
$shortcut.Save()

Write-Host "Created startup shortcut:"
Write-Host $shortcutPath
Write-Host ""
Write-Host "OrdoCor will start automatically the next time this Windows user signs in."
