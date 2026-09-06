# Windows Automation Setup - SmolLM2 via Ollama

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   Windows Automation Setup - SmolLM2 via Ollama" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Ollama is installed
$ollamaPath = Get-Command ollama -ErrorAction SilentlyContinue

if (-not $ollamaPath) {
    Write-Host "[!] Ollama is not installed." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please install Ollama first:" -ForegroundColor White
    Write-Host "  1. Download from: https://ollama.ai/download" -ForegroundColor Gray
    Write-Host "  2. Run the installer" -ForegroundColor Gray
    Write-Host "  3. Restart this script" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Or install via winget:" -ForegroundColor White
    Write-Host "  winget install Ollama.Ollama" -ForegroundColor Gray
    Write-Host ""
    
    $install = Read-Host "Would you like to install Ollama now via winget? (y/n)"
    if ($install -eq 'y' -or $install -eq 'Y') {
        Write-Host "[*] Installing Ollama..." -ForegroundColor Cyan
        winget install Ollama.Ollama
        Write-Host "[!] Please restart your terminal and run this script again." -ForegroundColor Yellow
    }
    exit 1
}

Write-Host "[+] Ollama is installed" -ForegroundColor Green
Write-Host ""

# Check if Ollama server is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "[+] Ollama server is running" -ForegroundColor Green
}
catch {
    Write-Host "[*] Starting Ollama server..." -ForegroundColor Cyan
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
    Write-Host "[+] Ollama server started" -ForegroundColor Green
}

Write-Host ""

# Pull SmolLM2 model
Write-Host "[*] Pulling SmolLM2 model (this may take a few minutes)..." -ForegroundColor Cyan
& ollama pull smollm2

Write-Host ""
Write-Host "[+] SmolLM2 model is ready!" -ForegroundColor Green
Write-Host ""

# Install Python dependencies
Write-Host "[*] Installing Python dependencies..." -ForegroundColor Cyan
& pip install requests pyautogui

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   Setup Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the Windows Automation system:" -ForegroundColor White
Write-Host "  python windows_automation.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "Or use it in your code:" -ForegroundColor White
Write-Host "  from windows_automation import WindowsAutomation" -ForegroundColor Gray
Write-Host "  auto = WindowsAutomation()" -ForegroundColor Gray
Write-Host '  auto.run("open chrome")' -ForegroundColor Gray
Write-Host ""

Read-Host "Press Enter to continue"
