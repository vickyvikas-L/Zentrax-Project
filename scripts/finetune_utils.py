"""
Zentrax Advanced Fine-Tuning Utilities
Additional tools for preparing data and fine-tuning with different approaches.
"""

import json
import os
import glob
import random
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


# ============================================================================
# LOAD EXISTING TRAINING DATA
# ============================================================================

def load_voice_command_metadata(training_data_dir: str = "training_data/voice_commands") -> List[Dict]:
    """Load all voice command metadata files."""
    samples = []
    metadata_files = glob.glob(os.path.join(training_data_dir, "*_metadata.json"))
    
    for meta_file in metadata_files:
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                samples.extend(data)
        except Exception as e:
            print(f"⚠️  Error loading {meta_file}: {e}")
    
    return samples


def load_gesture_data(training_data_dir: str = "training_data/gestures") -> List[Dict]:
    """Load gesture training data."""
    samples = []
    gesture_files = glob.glob(os.path.join(training_data_dir, "*.json"))
    
    for gesture_file in gesture_files:
        try:
            with open(gesture_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                gesture_name = os.path.basename(gesture_file).replace(".json", "")
                samples.append({
                    "gesture": gesture_name,
                    "data": data
                })
        except Exception as e:
            print(f"⚠️  Error loading {gesture_file}: {e}")
    
    return samples


# ============================================================================
# COMMAND MAPPINGS FOR TRAINING
# ============================================================================

COMMAND_MAPPINGS = {
    # Voice commands -> Actions
    "open browser": {"action": "open_app", "target": "chrome"},
    "close window": {"action": "close_window", "target": "current"},
    "minimize": {"action": "minimize_window", "target": "current"},
    "maximize": {"action": "maximize_window", "target": "current"},
    "volume up": {"action": "volume_up", "extra": {"amount": 10}},
    "volume down": {"action": "volume_down", "extra": {"amount": 10}},
    "scroll up": {"action": "scroll", "target": "up", "extra": {"amount": 3}},
    "scroll down": {"action": "scroll", "target": "down", "extra": {"amount": 3}},
    "take screenshot": {"action": "screenshot"},
    "exit program": {"action": "close_app", "target": "current"},
    
    # Gestures -> Actions
    "open_palm": {"action": "stop", "target": "listening"},
    "closed_fist": {"action": "pause", "target": "media"},
    "pointing": {"action": "click", "target": "mouse"},
    "thumbs_up": {"action": "confirm", "target": "action"},
    "thumbs_down": {"action": "cancel", "target": "action"},
    "pinch": {"action": "zoom", "target": "in"},
    "swipe_left": {"action": "navigate", "target": "back"},
    "swipe_right": {"action": "navigate", "target": "forward"},
}


def create_training_from_existing_data(
    voice_data_dir: str = "training_data/voice_commands",
    output_path: str = "training_data/finetune_from_existing.json"
) -> str:
    """Create fine-tuning dataset from existing voice command data."""
    
    samples = []
    voice_samples = load_voice_command_metadata(voice_data_dir)
    
    for sample in voice_samples:
        recognized_text = sample.get("recognized_text", "").strip().lower()
        expected_command = sample.get("expected_command", "").strip().lower()
        
        if not recognized_text or not expected_command:
            continue
        
        # Get the action mapping
        action = COMMAND_MAPPINGS.get(expected_command, {
            "action": "unknown",
            "target": expected_command
        })
        
        # Create training sample with variations
        # Handle cases where recognized text has repetitions
        clean_text = recognized_text.replace(expected_command + " ", "").strip()
        if clean_text == expected_command:
            clean_text = recognized_text
        
        samples.append({
            "instruction": recognized_text,
            "output": json.dumps(action)
        })
        
        # Also add the clean expected command
        if expected_command != recognized_text:
            samples.append({
                "instruction": expected_command,
                "output": json.dumps(action)
            })
    
    # Format for training
    system_prompt = """You are Zentrax, an AI assistant that converts natural language commands into structured Windows automation actions. Output JSON with action, target, and extra fields."""
    
    formatted = []
    for sample in samples:
        text = f"""<|system|>
{system_prompt}
<|user|>
{sample['instruction']}
<|assistant|>
{sample['output']}"""
        formatted.append({"text": text})
    
    # Remove duplicates
    seen = set()
    unique_samples = []
    for s in formatted:
        if s["text"] not in seen:
            seen.add(s["text"])
            unique_samples.append(s)
    
    # Save
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(unique_samples, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created {len(unique_samples)} training samples from existing data")
    print(f"📁 Saved to: {output_path}")
    
    return output_path


# ============================================================================
# DATA AUGMENTATION
# ============================================================================

class DataAugmenter:
    """Augment training data with variations."""
    
    def __init__(self):
        self.prefixes = [
            "", "please ", "can you ", "could you ", "i want to ",
            "i need to ", "hey ", "okay ", "zentrax ", "hey zentrax ",
        ]
        self.suffixes = [
            "", " please", " now", " for me", " thanks",
        ]
        
    def augment_instruction(self, instruction: str) -> List[str]:
        """Generate variations of an instruction."""
        variations = []
        
        # Add prefix/suffix combinations
        for prefix in self.prefixes:
            for suffix in self.suffixes:
                variation = f"{prefix}{instruction}{suffix}".strip()
                if variation and variation not in variations:
                    variations.append(variation)
        
        # Add typo variations (common speech-to-text errors)
        typo_map = {
            "volume": ["volum", "volumne"],
            "browser": ["broser", "brower"],
            "screenshot": ["screen shot", "screensnot"],
            "minimize": ["minimise", "minimze"],
            "maximize": ["maximise", "maximze"],
            "window": ["windoe", "windwo"],
        }
        
        for word, typos in typo_map.items():
            if word in instruction:
                for typo in typos:
                    variation = instruction.replace(word, typo)
                    if variation not in variations:
                        variations.append(variation)
        
        return variations
    
    def augment_dataset(self, samples: List[Dict], max_per_sample: int = 5) -> List[Dict]:
        """Augment an entire dataset."""
        augmented = []
        
        for sample in samples:
            instruction = sample.get("instruction", "")
            output = sample.get("output", "")
            
            # Add original
            augmented.append(sample)
            
            # Add variations
            variations = self.augment_instruction(instruction)
            random.shuffle(variations)
            
            for var in variations[:max_per_sample]:
                augmented.append({
                    "instruction": var,
                    "output": output
                })
        
        return augmented


# ============================================================================
# DATASET SPLITTER
# ============================================================================

def split_dataset(
    data: List[Dict],
    train_ratio: float = 0.9,
    val_ratio: float = 0.1,
    seed: int = 42
) -> Tuple[List[Dict], List[Dict]]:
    """Split dataset into train and validation sets."""
    random.seed(seed)
    shuffled = data.copy()
    random.shuffle(shuffled)
    
    split_idx = int(len(shuffled) * train_ratio)
    train_data = shuffled[:split_idx]
    val_data = shuffled[split_idx:]
    
    print(f"📊 Dataset split: {len(train_data)} train, {len(val_data)} validation")
    
    return train_data, val_data


# ============================================================================
# GGUF EXPORT FOR OLLAMA
# ============================================================================

def create_ollama_modelfile(
    model_path: str,
    output_path: str = "Modelfile",
    model_name: str = "zentrax"
) -> str:
    """Create an Ollama Modelfile for the fine-tuned model."""
    
    modelfile = f'''# Zentrax Fine-tuned Model for Windows Command Generation
# Generated by Zentrax Fine-Tuning Script

FROM {model_path}

# Model parameters optimized for command generation
PARAMETER temperature 0.3
PARAMETER top_k 40
PARAMETER top_p 0.9
PARAMETER num_predict 256
PARAMETER repeat_penalty 1.1

# System prompt
SYSTEM """You are Zentrax, an intelligent AI assistant for Windows automation.

Your task is to convert natural language voice commands into structured JSON actions.

Output format:
{{"action": "<action_type>", "target": "<target>", "extra": {{"<key>": "<value>"}}}}

Available actions:
- open_app: Open an application (target = app name)
- close_window: Close current or specified window
- minimize_window: Minimize window
- maximize_window: Maximize window
- volume_up/volume_down: Adjust volume (extra.amount = 1-100)
- mute: Toggle mute
- screenshot: Take a screenshot
- scroll: Scroll up/down (target = direction, extra.amount)
- lock_screen: Lock the computer
- shutdown/restart/sleep: System power actions
- web_search: Search the web (target = query)
- open_file/open_folder: Open file or folder (path)
- type_text: Type text (target = text to type)
- key_press/key_combo: Press key or key combination

Be precise and always output valid JSON."""

# Template for chat format
TEMPLATE """{{{{ if .System }}}}<|system|>
{{{{ .System }}}}
{{{{ end }}}}<|user|>
{{{{ .Prompt }}}}
<|assistant|>
"""
'''
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(modelfile)
    
    print(f"✅ Ollama Modelfile created: {output_path}")
    print(f"\n🐳 To import into Ollama:")
    print(f"   ollama create {model_name} -f {output_path}")
    
    return output_path


# ============================================================================
# QUICK TRAINING SCRIPT
# ============================================================================

def quick_finetune(
    base_model: str = "HuggingFaceTB/SmolLM2-360M-Instruct",
    output_dir: str = "./zentrax_finetuned",
    epochs: int = 3,
    use_existing_data: bool = True
):
    """Quick one-liner to fine-tune Zentrax model."""
    
    print("="*60)
    print("🚀 ZENTRAX QUICK FINE-TUNING")
    print("="*60)
    
    # Import main training script
    from finetune_llm import ZentraxFineTuneConfig, ZentraxDatasetGenerator, ZentraxFineTuner
    
    # Generate or load data
    if use_existing_data and os.path.exists("training_data/voice_commands"):
        data_path = create_training_from_existing_data()
    else:
        generator = ZentraxDatasetGenerator()
        data_path = generator.save_dataset("training_data/finetune_dataset.json")
    
    # Configure and train
    config = ZentraxFineTuneConfig(
        base_model=base_model,
        output_dir=output_dir,
        training_data_path=data_path,
        num_epochs=epochs,
    )
    
    trainer = ZentraxFineTuner(config)
    trainer.train()
    trainer.merge_and_export()
    
    # Create Ollama Modelfile
    create_ollama_modelfile(
        os.path.join(output_dir, "merged"),
        os.path.join(output_dir, "Modelfile")
    )
    
    print("\n✨ Fine-tuning complete!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Zentrax Fine-Tuning Utilities")
    parser.add_argument("--action", choices=["prepare", "augment", "quick", "modelfile"],
                       default="prepare", help="Action to perform")
    parser.add_argument("--input", type=str, help="Input path")
    parser.add_argument("--output", type=str, help="Output path")
    parser.add_argument("--model", type=str, default="HuggingFaceTB/SmolLM2-360M-Instruct")
    parser.add_argument("--epochs", type=int, default=3)
    
    args = parser.parse_args()
    
    if args.action == "prepare":
        create_training_from_existing_data(
            output_path=args.output or "training_data/finetune_from_existing.json"
        )
    
    elif args.action == "augment":
        if not args.input:
            print("❌ Please provide --input for augmentation")
            exit(1)
        
        with open(args.input, "r") as f:
            data = json.load(f)
        
        augmenter = DataAugmenter()
        augmented = augmenter.augment_dataset(data)
        
        output_path = args.output or args.input.replace(".json", "_augmented.json")
        with open(output_path, "w") as f:
            json.dump(augmented, f, indent=2)
        
        print(f"✅ Augmented {len(data)} -> {len(augmented)} samples")
        print(f"📁 Saved to: {output_path}")
    
    elif args.action == "quick":
        quick_finetune(
            base_model=args.model,
            output_dir=args.output or "./zentrax_finetuned",
            epochs=args.epochs
        )
    
    elif args.action == "modelfile":
        if not args.input:
            print("❌ Please provide --input (model path) for Modelfile creation")
            exit(1)
        create_ollama_modelfile(
            args.input,
            args.output or "Modelfile"
        )
