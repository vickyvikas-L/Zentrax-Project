# Whisper v3 Integration Guide

## Overview
Your project now uses OpenAI's Whisper model for enhanced speech recognition. Whisper provides:
- **Better accuracy** than Google Speech API
- **Offline capabilities** (no internet required after model download)
- **Multi-language support**
- **Noise robustness**

## Installation

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Install FFmpeg (Required for Whisper)
Download and install FFmpeg from: https://ffmpeg.org/download.html

Or use Chocolatey:
```powershell
choco install ffmpeg
```

### 3. Verify Installation
```powershell
python -c "import whisper; print('Whisper installed successfully')"
```

## Model Sizes
Choose the right model for your needs:

| Model  | Size  | Speed | Accuracy | Recommended For |
|--------|-------|-------|----------|----------------|
| tiny   | 39M   | Fast  | Good     | Testing |
| base   | 74M   | Fast  | Better   | **Default** (recommended) |
| small  | 244M  | Medium| Great    | High accuracy needs |
| medium | 769M  | Slow  | Excellent| Maximum accuracy |
| large  | 1550M | Slowest| Best   | Professional use |

## Usage

### Basic Usage (Default - Uses Whisper)
```python
from main import VoiceGestureControl

# Uses Whisper base model by default
controller = VoiceGestureControl()
controller.run()
```

### Advanced Configuration
```python
# Use a different Whisper model
controller = VoiceGestureControl(use_whisper=True, whisper_model="small")
controller.run()

# Disable Whisper and use Google API only
controller = VoiceGestureControl(use_whisper=False)
controller.run()
```

### Standalone Whisper Usage
```python
from whisper_handler import WhisperHandler
import speech_recognition as sr

# Initialize Whisper
whisper = WhisperHandler(model_name="base")

# Transcribe from microphone
mic = sr.Microphone()
text = whisper.listen_and_transcribe(mic)
print(f"You said: {text}")

# Transcribe from file
text = whisper.transcribe_from_file("audio.wav")
print(f"Transcription: {text}")
```

### Hybrid Mode (Automatic Fallback)
The system uses `HybridRecognizer` which:
1. Tries Whisper first (primary)
2. Falls back to Google API if Whisper fails
3. Provides best of both worlds

```python
from whisper_handler import HybridRecognizer

recognizer = HybridRecognizer(use_whisper=True, whisper_model="base")
```

## Features

### WhisperHandler
- Direct Whisper model integration
- Audio file transcription
- Real-time microphone transcription
- GPU acceleration support (if CUDA available)

### HybridRecognizer
- Automatic fallback mechanism
- Google API backup
- Seamless integration with existing code

## Performance Tips

1. **GPU Acceleration**: If you have NVIDIA GPU with CUDA:
   ```powershell
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

2. **Model Selection**: 
   - Use `tiny` or `base` for real-time applications
   - Use `small` or `medium` for better accuracy with slight delay

3. **First Run**: The model will be downloaded on first use (~74MB for base model)

## Troubleshooting

### Issue: "FFmpeg not found"
**Solution**: Install FFmpeg and add to PATH

### Issue: Slow transcription
**Solution**: Use smaller model (`tiny` or `base`) or enable GPU

### Issue: Low accuracy
**Solution**: Use larger model (`small` or `medium`)

### Issue: Import error
**Solution**: 
```powershell
pip install openai-whisper torch numpy
```

## Migration from Google API

Your existing code automatically uses Whisper now. No changes needed!

**Before:**
```python
text = self.recognizer.recognize_google(audio)
```

**After (handled automatically):**
```python
text = self.hybrid_recognizer.recognize(audio)  # Uses Whisper + fallback
```

## Configuration Options

Edit `main.py` to customize:
```python
# Line 245-246
if __name__ == "__main__":
    # Change model here
    controller = VoiceGestureControl(use_whisper=True, whisper_model="base")
    controller.run()
```

## Benefits Over Google API

✅ Works offline  
✅ No API key required  
✅ Better accuracy in noisy environments  
✅ Multi-language support built-in  
✅ No rate limits  
✅ Privacy-friendly (local processing)  

## System Requirements

- Python 3.8+
- 4GB RAM minimum (8GB recommended)
- 200MB free disk space for model
- GPU optional (speeds up processing)
