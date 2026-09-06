@echo off
title Zentrax Docker Launcher
cd /d "%~dp0\.."

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║           ZENTRAX DOCKER - ONE COMMAND LAUNCHER               ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

REM Check if Docker is installed
where docker >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker is not installed!
    echo.
    echo Please install Docker Desktop from:
    echo   https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)

echo [OK] Docker is running
echo.

REM Check for GPU support
echo Checking for GPU support...
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] NVIDIA GPU detected - using GPU acceleration
    set COMPOSE_FILE=docker\docker-compose.yml
) else (
    echo [INFO] No GPU detected - using CPU mode
    set COMPOSE_FILE=docker\docker-compose.cpu.yml
)
echo.

REM Start containers
echo Starting Zentrax Docker containers...
echo This may take a few minutes on first run (downloading models)...
echo.

docker-compose -f docker\docker-compose.yml up -d

echo.
echo Waiting for Ollama to initialize (30 seconds)...
timeout /t 30 /nobreak >nul

REM Check if Ollama is ready
echo.
echo Checking Ollama status...
curl -s http://localhost:11434/api/tags >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Ollama is running at http://localhost:11434
) else (
    echo [WAIT] Ollama is still initializing...
    echo       Check logs with: docker logs zentrax-ollama
)

echo.
echo ════════════════════════════════════════════════════════════════
echo   ZENTRAX DOCKER IS READY!
echo ════════════════════════════════════════════════════════════════
echo.
echo   Ollama API:    http://localhost:11434
echo   Test command:  curl http://localhost:11434/api/tags
echo.
echo   Useful commands:
echo     Stop:    docker-compose -f docker\docker-compose.yml down
echo     Logs:    docker logs zentrax-ollama
echo     Shell:   docker exec -it zentrax-ollama bash
echo.
echo   Now run Zentrax:
echo     python run.py
echo.
pause
