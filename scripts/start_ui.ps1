# Zentrax Web UI Launcher
# This script starts the WebSocket server and opens the web interface

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "      ZENTRAX WEB UI LAUNCHER          " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if websockets is installed
Write-Host "[1/3] Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import websockets" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ websockets installed" -ForegroundColor Green
    }
    else {
        throw "websockets not found"
    }
}
catch {
    Write-Host "✗ websockets not installed" -ForegroundColor Red
    Write-Host "Installing websockets..." -ForegroundColor Yellow
    pip install websockets
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ websockets installed successfully" -ForegroundColor Green
    }
    else {
        Write-Host "✗ Failed to install websockets" -ForegroundColor Red
        Write-Host "Please run: pip install websockets" -ForegroundColor Yellow
        pause
        exit 1
    }
}

Write-Host ""

# Get project root (parent of scripts folder)
$projectRoot = Split-Path $PSScriptRoot -Parent

# Start the WebSocket server in a new window
Write-Host "[2/3] Starting WebSocket server..." -ForegroundColor Yellow
$serverPath = Join-Path $projectRoot "src\core\websocket_server.py"

if (Test-Path $serverPath) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; python '$serverPath'"
    Write-Host "✓ WebSocket server started in new window" -ForegroundColor Green
    Start-Sleep -Seconds 2
}
else {
    Write-Host "✗ websocket_server.py not found at $serverPath!" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""

# Open the web interface
Write-Host "[3/3] Opening web interface..." -ForegroundColor Yellow
$htmlPath = Join-Path $projectRoot "frontend\index.html"

if (Test-Path $htmlPath) {
    Start-Process $htmlPath
    Write-Host "✓ Web interface opened in browser" -ForegroundColor Green
}
else {
    Write-Host "✗ frontend\index.html not found at $htmlPath!" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ZENTRAX IS READY!                    " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "The WebSocket server is running in a separate window." -ForegroundColor White
Write-Host "The web interface should open in your browser." -ForegroundColor White
Write-Host ""
Write-Host "To stop: Close the WebSocket server window" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit this launcher..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
