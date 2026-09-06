# Zentrax Docker Launcher
# One command to start Ollama in Docker

param(
    [switch]$CPU,      # Force CPU mode
    [switch]$Stop,     # Stop containers
    [switch]$Logs,     # Show logs
    [switch]$Shell     # Open shell in container
)

$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           ZENTRAX DOCKER - ONE COMMAND LAUNCHER               ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Docker is not installed!" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from: https://docker.com" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is running
$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Docker is running" -ForegroundColor Green

# Handle commands
if ($Stop) {
    Write-Host "`nStopping Zentrax Docker containers..." -ForegroundColor Yellow
    docker-compose -f docker\docker-compose.yml down
    Write-Host "[OK] Containers stopped" -ForegroundColor Green
    exit 0
}

if ($Logs) {
    docker logs -f zentrax-ollama
    exit 0
}

if ($Shell) {
    docker exec -it zentrax-ollama bash
    exit 0
}

# Determine compose file
$composeFile = "docker\docker-compose.yml"
if ($CPU) {
    $composeFile = "docker\docker-compose.cpu.yml"
    Write-Host "[INFO] Using CPU-only mode" -ForegroundColor Yellow
} else {
    # Check for GPU
    $gpuCheck = docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] NVIDIA GPU detected - using GPU acceleration" -ForegroundColor Green
    } else {
        Write-Host "[INFO] No GPU detected - using CPU mode" -ForegroundColor Yellow
        $composeFile = "docker\docker-compose.cpu.yml"
    }
}

Write-Host ""
Write-Host "Starting Zentrax Docker containers..." -ForegroundColor Cyan
Write-Host "This may take a few minutes on first run..." -ForegroundColor Gray
Write-Host ""

# Start containers
docker-compose -f $composeFile up -d

Write-Host ""
Write-Host "Waiting for Ollama to initialize (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check status
Write-Host ""
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
    Write-Host "[OK] Ollama is running!" -ForegroundColor Green
} catch {
    Write-Host "[WAIT] Ollama is still initializing..." -ForegroundColor Yellow
    Write-Host "       Check logs with: docker logs zentrax-ollama" -ForegroundColor Gray
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ZENTRAX DOCKER IS READY!" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Ollama API:    http://localhost:11434" -ForegroundColor White
Write-Host ""
Write-Host "  Commands:" -ForegroundColor Gray
Write-Host "    .\docker\start.ps1 -Stop     Stop containers" -ForegroundColor Gray
Write-Host "    .\docker\start.ps1 -Logs     View logs" -ForegroundColor Gray
Write-Host "    .\docker\start.ps1 -Shell    Open container shell" -ForegroundColor Gray
Write-Host ""
Write-Host "  Now run Zentrax:" -ForegroundColor Yellow
Write-Host "    python run.py" -ForegroundColor White
Write-Host ""
