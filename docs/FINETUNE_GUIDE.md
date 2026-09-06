# Zentrax LLM Fine-Tuning Guide

This guide explains how to fine-tune a language model for Zentrax Windows command generation.

## 📋 Prerequisites

1. **Python 3.8+** with pip
2. **CUDA-capable GPU** (recommended, 8GB+ VRAM) or CPU (slower)
3. **Ollama** (optional, for deployment)

## 🔧 Installation

```bash
# Install fine-tuning dependencies
pip install -r requirements_finetune.txt
```

## 🚀 Quick Start

### Option 1: One-Command Fine-Tuning

```bash
# Generate data + train + export (uses existing voice command data)
python scripts/finetune_llm.py --mode all
```

### Option 2: Step-by-Step

```bash
# Step 1: Generate training data
python scripts/finetune_llm.py --mode generate

# Step 2: Train the model
python scripts/finetune_llm.py --mode train --epochs 3

# Step 3: Test inference
python scripts/finetune_llm.py --mode inference --prompt "open chrome"
```

## 📊 Training Data

The fine-tuning script generates training data from:

1. **Built-in command variations** - 300+ samples covering:
   - Application commands (open/close apps)
   - Volume control
   - Window management
   - Screenshots
   - System commands
   - File operations
   - Web search

2. **Your existing data** (optional):
   ```bash
   python scripts/finetune_utils.py --action prepare
   ```
   This loads data from `training_data/voice_commands/` metadata files.

## ⚙️ Configuration

### Model Options

| Model | Size | VRAM Needed | Quality |
|-------|------|-------------|---------|
| `HuggingFaceTB/SmolLM2-360M-Instruct` | 360M | ~2GB | Good |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | 1.1B | ~4GB | Better |
| `microsoft/phi-2` | 2.7B | ~8GB | Best |

### Training Parameters

```python
# In finetune_llm.py - ZentraxFineTuneConfig
base_model = "HuggingFaceTB/SmolLM2-360M-Instruct"
num_epochs = 3           # More epochs = better fit (risk of overfitting)
batch_size = 4           # Reduce if OOM errors
learning_rate = 2e-4     # Standard for LoRA
lora_r = 16              # LoRA rank (higher = more params)
use_4bit = True          # Enable for memory efficiency
```

## 🐳 Deploying to Ollama

After fine-tuning:

```bash
# Navigate to output directory
cd zentrax_finetuned

# Create Ollama model
ollama create zentrax-finetuned -f Modelfile

# Test it
ollama run zentrax-finetuned "open chrome"
```

## 📁 File Structure

```
scripts/
├── finetune_llm.py          # Main fine-tuning script
├── finetune_utils.py        # Utilities & data preparation
training_data/
├── finetune_dataset.json    # Generated training data
├── voice_commands/          # Your recorded voice commands
zentrax_finetuned/           # Output directory (after training)
├── adapter_config.json      # LoRA config
├── adapter_model.safetensors # LoRA weights
├── merged/                  # Merged model for Ollama
└── Modelfile                # Ollama model file
```

## 🔍 Data Augmentation

To expand your training data:

```bash
python scripts/finetune_utils.py --action augment \
    --input training_data/finetune_dataset.json
```

This adds variations with:
- Prefixes: "please", "can you", "hey zentrax"
- Suffixes: "please", "now", "thanks"
- Common typos/speech errors

## 📈 Training Tips

1. **Start small**: Use SmolLM2-360M first to validate your setup
2. **Monitor loss**: Loss should decrease; if it plateaus, try more data
3. **Validate manually**: Test with commands after training
4. **Iterate**: Add more training data for commands that fail

## 🐛 Troubleshooting

### CUDA Out of Memory
```bash
# Reduce batch size
python scripts/finetune_llm.py --mode train --batch-size 2

# Or enable gradient checkpointing (edit config)
```

### bitsandbytes errors on Windows
```bash
# Use pre-built wheels
pip install bitsandbytes-windows
```

### Slow training on CPU
- Training on CPU is 10-50x slower
- Consider using Google Colab (free GPU)
- Or reduce epochs and dataset size

## 📜 License

MIT License - See main project LICENSE file.
