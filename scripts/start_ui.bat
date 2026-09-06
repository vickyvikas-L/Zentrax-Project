@echo off
title Zentrax Web UI Launcher
color 0B

REM Get project root (parent of scripts folder)
cd /d "%~dp0\.."
set "PROJECT_ROOT=%cd%"

echo ========================================
echo       ZENTRAX WEB UI LAUNCHER
echo ========================================
echo.

echo [1/3] Checking dependencies...
python -c "import websockets" 2>nul
if %errorlevel% neq 0 (
    echo X websockets not installed
    echo Installing websockets...
    pip install websockets
    if %errorlevel% equ 0 (
        echo + websockets installed successfully
    ) else (
        echo X Failed to install websockets
        echo Please run: pip install websockets
        pause
        exit /b 1
    )
) else (
    echo + websockets installed
)

echo.
echo [2/3] Starting WebSocket server...
if exist "%PROJECT_ROOT%\src\core\websocket_server.py" (
    start "Zentrax WebSocket Server" cmd /k "cd /d "%PROJECT_ROOT%" && python src\core\websocket_server.py"
    echo + WebSocket server started in new window
    timeout /t 2 /nobreak >nul
) else (
    echo X websocket_server.py not found!
    pause
    exit /b 1
)

echo.
echo [3/3] Opening web interface...
if exist "%PROJECT_ROOT%\frontend\index.html" (
    start "" "%PROJECT_ROOT%\frontend\index.html"
    echo + Web interface opened in browser
) else (
    echo X frontend\index.html not found!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ZENTRAX IS READY!
echo ========================================
echo.
echo The WebSocket server is running in a separate window.
echo The web interface should open in your browser.
echo.
echo To stop: Close the WebSocket server window
echo.
pause
