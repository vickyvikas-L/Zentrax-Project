@echo off
REM Zentrax Training Environment Setup
REM Run this script to set up the training environment

echo ============================================================
echo    Zentrax Training Environment Setup
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

REM Check NVIDIA GPU
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo WARNING: nvidia-smi not found. GPU training may not work.
    echo Make sure you have NVIDIA drivers installed.
    echo.
)

REM Check CUDA version
echo Checking CUDA version...
nvidia-smi --query-gpu=driver_version,cuda_version --format=csv 2>nul

echo.
echo ============================================================
echo Step 1: Upgrading pip
echo ============================================================
python -m pip install --upgrade pip

echo.
echo ============================================================
echo Step 2: Uninstalling existing packages (clean install)
echo ============================================================
pip uninstall -y torch torchvision torchaudio transformers peft trl bitsandbytes accelerate datasets 2>nul

echo.
echo ============================================================
echo Step 3: Installing PyTorch with CUDA 11.8
echo ============================================================
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

echo.
echo ============================================================
echo Step 4: Installing training packages
echo ============================================================
pip install transformers datasets accelerate peft trl bitsandbytes tensorboard sentencepiece protobuf scipy

echo.
echo ============================================================
echo Step 5: Verifying installation
echo ============================================================
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0)}' if torch.cuda.is_available() else 'No GPU')"
python -c "import transformers, peft, trl, datasets, accelerate, bitsandbytes; print('All packages installed successfully!')"

echo.
echo ============================================================
echo    Setup Complete!
echo ============================================================
echo.
echo To start training:
echo   python scripts/train_smollm2.py --dataset data/zentrax_train.jsonl
echo.
echo For a quick test (1000 samples, 1 epoch):
echo   python scripts/train_smollm2.py --dataset data/zentrax_train.jsonl --max-samples 1000 --epochs 1
echo.
pause
