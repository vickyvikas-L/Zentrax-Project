#!/usr/bin/env python3
"""
Export fine-tuned Zentrax model to Ollama format.

This script:
1. Merges LoRA adapter with base model
2. Converts to GGUF format using llama.cpp
3. Creates Ollama Modelfile
4. Imports into Ollama
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path


def check_dependencies():
    """Check if required tools are available."""
    print("🔍 Checking dependencies...")
    
    # Check for llama.cpp convert script
    llama_cpp_path = os.environ.get("LLAMA_CPP_PATH", "")
    
    # Check for Ollama
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        print(f"   ✅ Ollama: {result.stdout.strip()}")
        ollama_available = True
    except FileNotFoundError:
        print("   ⚠️  Ollama not found. Install from https://ollama.ai")
        ollama_available = False
    
    return ollama_available


def merge_lora_adapter(adapter_path: str, output_path: str, base_model: str = None):
    """Merge LoRA adapter with base model."""
    print(f"\n🔧 Merging LoRA adapter...")
    print(f"   Adapter: {adapter_path}")
    print(f"   Output: {output_path}")
    
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install torch transformers peft")
        return False
    
    # Read adapter config to get base model
    adapter_config_path = os.path.join(adapter_path, "adapter_config.json")
    if os.path.exists(adapter_config_path):
        with open(adapter_config_path, "r") as f:
            adapter_config = json.load(f)
        if base_model is None:
            base_model = adapter_config.get("base_model_name_or_path", "HuggingFaceTB/SmolLM2-135M-Instruct")
    
    if base_model is None:
        base_model = "HuggingFaceTB/SmolLM2-135M-Instruct"
    
    print(f"   Base model: {base_model}")
    
    # Load base model
    print("   Loading base model...")
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.float16,
        device_map="cpu",
        trust_remote_code=True,
    )
    
    # Load tokenizer
    print("   Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(adapter_path)
    
    # Load and merge LoRA
    print("   Loading LoRA adapter...")
    model = PeftModel.from_pretrained(model, adapter_path)
    
    print("   Merging weights...")
    model = model.merge_and_unload()
    
    # Save merged model
    print(f"   Saving merged model to: {output_path}")
    os.makedirs(output_path, exist_ok=True)
    model.save_pretrained(output_path, safe_serialization=True)
    tokenizer.save_pretrained(output_path)
    
    print("   ✅ Merge complete!")
    return True


def convert_to_gguf(model_path: str, output_path: str, quantization: str = "q4_k_m"):
    """Convert HuggingFace model to GGUF format."""
    print(f"\n📦 Converting to GGUF format...")
    print(f"   Model: {model_path}")
    print(f"   Output: {output_path}")
    print(f"   Quantization: {quantization}")
    
    # Try to find llama.cpp convert script
    llama_cpp_path = os.environ.get("LLAMA_CPP_PATH", "")
    convert_script = None
    
    # Common locations
    possible_paths = [
        os.path.join(llama_cpp_path, "convert_hf_to_gguf.py"),
        os.path.join(llama_cpp_path, "convert-hf-to-gguf.py"),
        "convert_hf_to_gguf.py",
        "convert-hf-to-gguf.py",
        os.path.expanduser("~/llama.cpp/convert_hf_to_gguf.py"),
        os.path.expanduser("~/llama.cpp/convert-hf-to-gguf.py"),
        "C:/llama.cpp/convert_hf_to_gguf.py",
        "C:/llama.cpp/convert-hf-to-gguf.py",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            convert_script = path
            break
    
    if convert_script:
        print(f"   Using: {convert_script}")
        
        # Run conversion
        cmd = [
            sys.executable, convert_script,
            model_path,
            "--outfile", output_path,
            "--outtype", quantization.replace("_", "-") if "q" in quantization else "f16",
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✅ GGUF conversion complete!")
                return True
            else:
                print(f"   ❌ Conversion failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    else:
        print("   ⚠️  llama.cpp not found. Manual conversion required.")
        print("\n   To convert manually:")
        print("   1. Clone llama.cpp: git clone https://github.com/ggerganov/llama.cpp")
        print("   2. Install: pip install -r llama.cpp/requirements.txt")
        print(f"   3. Run: python llama.cpp/convert_hf_to_gguf.py {model_path} --outfile {output_path}")
        print("\n   Alternative: Use Hugging Face's GGUF converter:")
        print("   pip install llama-cpp-python[server]")
        return False


def create_modelfile(gguf_path: str, output_path: str, model_name: str = "zentrax"):
    """Create Ollama Modelfile."""
    print(f"\n📝 Creating Ollama Modelfile...")
    
    # System prompt for Zentrax
    system_prompt = """You are Zentrax, an AI assistant specialized in Windows automation and system control.

When the user gives you a command, you should:
1. Think step-by-step about what action is needed
2. Respond with a JSON action that can be executed

Your response format should be:
<think>Brief reasoning about what to do</think>
<action>{"action": "action_name", "params": {...}}</action>

Available actions include:
- open_app: Open an application
- close_app: Close an application  
- create_file: Create a new file
- delete_file: Delete a file
- search_web: Search the web
- type_text: Type text
- press_key: Press a keyboard key
- take_screenshot: Capture the screen
- set_volume: Adjust system volume
- And many more...

Always be helpful, precise, and safety-conscious."""

    modelfile_content = f'''# Zentrax - Windows Automation AI Assistant
# Generated by Zentrax export script

FROM {gguf_path}

# Set the temperature for response generation
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1

# Set the system prompt
SYSTEM """{system_prompt}"""

# Chat template
TEMPLATE """{{{{ if .System }}}}<|im_start|>system
{{{{ .System }}}}<|im_end|>
{{{{ end }}}}{{{{ if .Prompt }}}}<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
{{{{ end }}}}<|im_start|>assistant
{{{{ .Response }}}}<|im_end|>
"""

# Stop tokens
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|im_start|>"
'''

    with open(output_path, "w") as f:
        f.write(modelfile_content)
    
    print(f"   ✅ Modelfile created: {output_path}")
    return True


def create_modelfile_from_safetensors(merged_path: str, output_path: str):
    """Create Ollama Modelfile that references HF model directly (for Ollama 0.2+)."""
    print(f"\n📝 Creating Ollama Modelfile (HuggingFace format)...")
    
    system_prompt = """You are Zentrax, an AI assistant specialized in Windows automation and system control.

When the user gives you a command, analyze it and respond with:
1. Your reasoning in <think> tags
2. A JSON action in <action> tags

Example response:
<think>User wants to open Chrome browser</think>
<action>{"action": "open_app", "params": {"app_name": "chrome"}}</action>

Be helpful, precise, and safety-conscious."""

    # Ollama can now import directly from HF format
    modelfile_content = f'''# Zentrax - Windows Automation AI Assistant
FROM {merged_path}

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1

SYSTEM """{system_prompt}"""

TEMPLATE """{{{{ if .System }}}}<|im_start|>system
{{{{ .System }}}}<|im_end|>
{{{{ end }}}}{{{{ if .Prompt }}}}<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
{{{{ end }}}}<|im_start|>assistant
{{{{ .Response }}}}<|im_end|>
"""

PARAMETER stop "<|im_end|>"
PARAMETER stop "<|im_start|>"
'''

    with open(output_path, "w") as f:
        f.write(modelfile_content)
    
    print(f"   ✅ Modelfile created: {output_path}")
    return True


def import_to_ollama(modelfile_path: str, model_name: str = "zentrax"):
    """Import model into Ollama."""
    print(f"\n🚀 Importing to Ollama as '{model_name}'...")
    
    try:
        cmd = ["ollama", "create", model_name, "-f", modelfile_path]
        print(f"   Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ Model imported successfully!")
            print(f"\n   To use: ollama run {model_name}")
            return True
        else:
            print(f"   ❌ Import failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("   ❌ Ollama not found. Please install Ollama first.")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Export Zentrax model to Ollama")
    parser.add_argument("--adapter", type=str, default="./models/zentrax-smollm2/final",
                       help="Path to LoRA adapter")
    parser.add_argument("--output", type=str, default="./models/zentrax-merged",
                       help="Output directory for merged model")
    parser.add_argument("--name", type=str, default="zentrax",
                       help="Name for Ollama model")
    parser.add_argument("--base-model", type=str, default=None,
                       help="Base model name (auto-detected from adapter config)")
    parser.add_argument("--quantization", type=str, default="q4_k_m",
                       choices=["f16", "f32", "q4_0", "q4_1", "q4_k_m", "q5_0", "q5_1", "q5_k_m", "q8_0"],
                       help="Quantization type for GGUF")
    parser.add_argument("--skip-merge", action="store_true",
                       help="Skip merging (use existing merged model)")
    parser.add_argument("--skip-gguf", action="store_true",
                       help="Skip GGUF conversion (use HF format directly)")
    parser.add_argument("--skip-import", action="store_true",
                       help="Skip Ollama import")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("   Zentrax Model Export to Ollama")
    print("=" * 60)
    
    # Check dependencies
    ollama_available = check_dependencies()
    
    # Paths
    adapter_path = os.path.abspath(args.adapter)
    merged_path = os.path.abspath(args.output)
    gguf_path = os.path.join(merged_path, f"{args.name}.gguf")
    modelfile_path = os.path.join(merged_path, "Modelfile")
    
    # Step 1: Merge LoRA
    if not args.skip_merge:
        if not os.path.exists(adapter_path):
            print(f"❌ Adapter not found: {adapter_path}")
            return 1
        
        if not merge_lora_adapter(adapter_path, merged_path, args.base_model):
            return 1
    else:
        print(f"\n⏭️  Skipping merge (using: {merged_path})")
    
    # Step 2: Convert to GGUF (optional)
    if not args.skip_gguf:
        gguf_success = convert_to_gguf(merged_path, gguf_path, args.quantization)
        
        if gguf_success:
            # Create Modelfile with GGUF
            create_modelfile(gguf_path, modelfile_path, args.name)
        else:
            # Create Modelfile with HF path
            print("\n   Falling back to HuggingFace format...")
            create_modelfile_from_safetensors(merged_path, modelfile_path)
    else:
        print(f"\n⏭️  Skipping GGUF conversion")
        create_modelfile_from_safetensors(merged_path, modelfile_path)
    
    # Step 3: Import to Ollama
    if not args.skip_import and ollama_available:
        if not import_to_ollama(modelfile_path, args.name):
            print("\n   Manual import instructions:")
            print(f"   ollama create {args.name} -f {modelfile_path}")
    else:
        print(f"\n📋 To import manually:")
        print(f"   ollama create {args.name} -f {modelfile_path}")
    
    print("\n" + "=" * 60)
    print("   Export Complete!")
    print("=" * 60)
    print(f"\n   Merged model: {merged_path}")
    print(f"   Modelfile: {modelfile_path}")
    if not args.skip_import and ollama_available:
        print(f"\n   Run with: ollama run {args.name}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
