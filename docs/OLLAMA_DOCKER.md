# 🐳 Ollama Docker Setup for Zentrax

This guide explains how to run Ollama (SmolLM2 model) in a Docker container for Zentrax.

## Prerequisites

1. **Docker Desktop** - Download from [docker.com](https://www.docker.com/products/docker-desktop/)
2. **WSL 2** (Windows) - Docker Desktop will prompt you to install if needed
3. **NVIDIA GPU** (Optional) - For GPU acceleration

---

## 🚀 Quick Start - One Command!

### Windows Batch (Simplest)
```batch
docker\start.bat
```

### PowerShell (with Options)
```powershell
.\docker\start.ps1
```

That's it! The launcher will:
1. ✅ Check if Docker is running
2. ✅ Auto-detect NVIDIA GPU
3. ✅ Start Ollama container
4. ✅ Download SmolLM2 model
5. ✅ Show status when ready

---

## 📋 Docker Commands

### PowerShell Launcher Options

```powershell
.\docker\start.ps1              # Start with auto GPU detection
.\docker\start.ps1 -CPU         # Force CPU mode (no GPU)
.\docker\start.ps1 -Stop        # Stop all containers
.\docker\start.ps1 -Logs        # View container logs
.\docker\start.ps1 -Shell       # Open shell inside container
```

### Manual Docker Commands

| Command | Description |
|---------|-------------|
| `docker-compose -f docker/docker-compose.yml up -d` | Start with GPU |
| `docker-compose -f docker/docker-compose.cpu.yml up -d` | Start CPU-only |
| `docker-compose -f docker/docker-compose.yml down` | Stop containers |
| `docker logs zentrax-ollama` | View logs |
| `docker exec -it zentrax-ollama bash` | Open container shell |

---

## 🔍 Verify Ollama is Running

### Check API
```powershell
# Test if Ollama is responding
Invoke-RestMethod http://localhost:11434/api/tags

# Or using curl
curl http://localhost:11434/api/tags
```

### Test Generation
```powershell
$body = @{
    model = "smollm2"
    prompt = "Hello, how are you?"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -Body $body -ContentType "application/json"
```

---

## 🎮 GPU vs CPU

### GPU Mode (Faster)
The default `docker-compose.yml` includes NVIDIA GPU support:

**Requirements:**
- NVIDIA GPU with CUDA support
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

### CPU Mode (No GPU Required)
Use `docker-compose.cpu.yml` for systems without NVIDIA GPU:

```powershell
# Automatic detection
.\docker\start.ps1    # Auto-detects and uses CPU if no GPU

# Force CPU mode
.\docker\start.ps1 -CPU
```

---

## 🔧 Configuration Files

### docker/docker-compose.yml (GPU)
```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: zentrax-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

### docker/docker-compose.cpu.yml (CPU)
```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: zentrax-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    # No GPU section - runs on CPU
```

---

## 📦 Using Different Models

```powershell
# Pull additional models
docker exec zentrax-ollama ollama pull llama3.2
docker exec zentrax-ollama ollama pull mistral
docker exec zentrax-ollama ollama pull codellama

# List installed models
docker exec zentrax-ollama ollama list

# Remove a model
docker exec zentrax-ollama ollama rm llama3.2
```

### Configure Zentrax to Use Different Model
Edit `config/zentrax_config.json`:
```json
{
  "llm": {
    "model": "llama3.2"
  }
}
```

---

## 🔗 Connecting to Zentrax

Zentrax automatically connects to Ollama at `http://localhost:11434`. No configuration needed!

### Remote Ollama Server
If Ollama is on a different host, edit `config/zentrax_config.json`:
```json
{
  "llm": {
    "ollama_url": "http://your-host:11434"
  }
}
```

---

## 🛠️ Troubleshooting

### Container Won't Start
```powershell
# Check Docker status
docker ps -a

# View detailed logs
docker logs zentrax-ollama --tail 50

# Restart container
docker restart zentrax-ollama
```

### GPU Not Detected
```powershell
# Check NVIDIA driver
nvidia-smi

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### Model Not Responding
```powershell
# Restart and re-pull model
docker restart zentrax-ollama
Start-Sleep -Seconds 10
docker exec zentrax-ollama ollama pull smollm2
```

### Port Already in Use
```powershell
# Find what's using port 11434
netstat -ano | findstr :11434

# Kill the process or change port in docker-compose.yml
```

### Clean Reset
```powershell
# Remove everything and start fresh
docker-compose -f docker/docker-compose.yml down -v
docker-compose -f docker/docker-compose.yml up -d
```

---

## 📊 Resource Usage

| Model | RAM Usage | GPU VRAM | Speed |
|-------|-----------|----------|-------|
| smollm2 | ~2GB | ~2GB | Fast |
| llama3.2 | ~4GB | ~4GB | Medium |
| mistral | ~8GB | ~6GB | Slower |

---

## 🚀 Next Steps

After Docker is running:
```powershell
# Run Zentrax
python run.py
```

Zentrax will automatically connect to the containerized Ollama!
