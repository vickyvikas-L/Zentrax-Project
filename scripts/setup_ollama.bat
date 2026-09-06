@echo off
echo ============================================================
echo   Windows Automation Setup - SmolLM2 via Ollama
echo ============================================================
echo.

REM Check if Ollama is installed
where ollama >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] Ollama is not installed.
    echo.
    echo Please install Ollama first:
    echo   1. Download from: https://ollama.ai/download
    echo   2. Run the installer
    echo   3. Restart this script
    echo.
    echo Or install via winget:
    echo   winget install Ollama.Ollama
    echo.
    pause
    exit /b 1
)

echo [+] Ollama is installed
echo.

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [*] Starting Ollama server...
    start /B ollama serve
    timeout /t 3 /nobreak >nul
)

echo [+] Ollama server is running
echo.

REM Pull SmolLM2 model
echo [*] Pulling SmolLM2 model (this may take a few minutes)...
ollama pull smollm2

echo.
echo [+] SmolLM2 model is ready!
echo.

REM Install Python dependencies
echo [*] Installing Python dependencies...
pip install requests pyautogui

echo.
echo ============================================================
echo   Setup Complete!
echo ============================================================
echo.
echo To start the Windows Automation system:
echo   python windows_automation.py
echo.
echo Or use it in your code:
echo   from windows_automation import WindowsAutomation
echo   auto = WindowsAutomation()
echo   auto.run("open chrome")
echo.
pause
