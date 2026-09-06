# Zentrax Launcher for PowerShell
# Run with: .\Zentrax.ps1 [options]

param(
    [switch]$Headless,
    [switch]$NoBrowser,
    [int]$Port = 8080,
    [int]$WsPort = 8765
)

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Activate virtual environment
$venvPath = Join-Path $scriptPath ".venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
}

# Build arguments
$args = @()
if ($Headless) { $args += "--headless" }
if ($NoBrowser) { $args += "--no-browser" }
$args += "--port", $Port
$args += "--ws-port", $WsPort

# Run Zentrax
Write-Host "`n🚀 Starting Zentrax AI Assistant...`n" -ForegroundColor Cyan
python run.py @args
