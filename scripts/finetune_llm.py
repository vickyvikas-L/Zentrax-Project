"""
Zentrax LLM Fine-Tuning Script
Fine-tune a language model for Windows command generation from natural language.

This script supports:
1. Preparing training data from your existing command patterns
2. Fine-tuning using HuggingFace Transformers + PEFT (LoRA)
3. Exporting the fine-tuned model for use with Ollama

Requirements:
    pip install torch transformers datasets peft accelerate bitsandbytes trl
"""

import json
import os
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Check for required packages
try:
    import torch
    from torch.utils.data import Dataset
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TrainingArguments,
        BitsAndBytesConfig,
        DataCollatorForLanguageModeling,
    )
    from peft import (
        LoraConfig,
        get_peft_model,
        prepare_model_for_kbit_training,
        TaskType,
    )
    from trl import SFTTrainer
    from datasets import Dataset as HFDataset
except ImportError as e:
    print(f"❌ Missing required package: {e}")
    print("\n📦 Install required packages with:")
    print("pip install torch transformers datasets peft accelerate bitsandbytes trl")
    exit(1)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class ZentraxFineTuneConfig:
    """Configuration for Zentrax LLM fine-tuning."""
    
    # Model settings
    base_model: str = "HuggingFaceTB/SmolLM2-360M-Instruct"  # or "microsoft/phi-2", "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    output_dir: str = "./zentrax_finetuned"
    
    # LoRA settings (Parameter Efficient Fine-Tuning)
    lora_r: int = 16  # LoRA rank
    lora_alpha: int = 32  # LoRA alpha
    lora_dropout: float = 0.05
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj", "k_proj", "o_proj"])
    
    # Training settings
    num_epochs: int = 3
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    warmup_ratio: float = 0.03
    max_seq_length: int = 512
    
    # Quantization (for memory efficiency)
    use_4bit: bool = True
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"
    
    # Paths
    training_data_path: str = "./training_data/finetune_dataset.json"
    

# ============================================================================
# TRAINING DATA GENERATION
# ============================================================================

class ZentraxDatasetGenerator:
    """Generate fine-tuning dataset for Zentrax Windows command generation."""
    
    def __init__(self):
        self.system_prompt = """You are Zentrax, an AI assistant that converts natural language commands into structured Windows automation actions. 

Given a user's voice command, output a JSON object with:
- "action": The type of action (open_app, close_window, volume_up, etc.)
- "target": The target of the action (app name, file path, etc.)
- "extra": Additional parameters if needed

Be precise and handle variations in user speech."""

    def generate_training_samples(self) -> List[Dict[str, str]]:
        """Generate comprehensive training samples for Windows commands."""
        
        samples = []
        
        # ============ APPLICATION COMMANDS ============
        app_variations = {
            "chrome": ["open chrome", "launch chrome", "start chrome", "open google chrome", 
                      "launch the browser", "open browser", "start browser", "open the browser",
                      "can you open chrome", "please open chrome", "i want to open chrome",
                      "open up chrome for me", "fire up chrome", "get chrome running"],
            "notepad": ["open notepad", "launch notepad", "start notepad", "open note pad",
                       "open the text editor", "i need notepad", "start text editor",
                       "open notepad please", "can you open notepad"],
            "vscode": ["open vscode", "launch vscode", "start vs code", "open visual studio code",
                      "open code editor", "launch code", "open vs code", "start visual studio code"],
            "calculator": ["open calculator", "launch calc", "start calculator", "open the calculator",
                          "i need a calculator", "open calc", "calculator please"],
            "file explorer": ["open file explorer", "open explorer", "show my files", "open files",
                             "launch file explorer", "open my documents", "show file explorer"],
            "settings": ["open settings", "launch settings", "open windows settings", 
                        "show settings", "go to settings", "open system settings"],
            "task manager": ["open task manager", "launch task manager", "show task manager",
                           "open taskmgr", "i need task manager", "show processes"],
            "spotify": ["open spotify", "launch spotify", "start spotify", "play spotify",
                       "open music player", "launch the music app"],
            "discord": ["open discord", "launch discord", "start discord"],
            "terminal": ["open terminal", "launch terminal", "open command prompt", "open cmd",
                        "start powershell", "open powershell"],
        }
        
        for app, variations in app_variations.items():
            for cmd in variations:
                samples.append({
                    "instruction": cmd,
                    "output": json.dumps({"action": "open_app", "target": app})
                })
        
        # ============ VOLUME COMMANDS ============
        volume_up_cmds = [
            "volume up", "increase volume", "turn up the volume", "louder please",
            "raise the volume", "make it louder", "crank up the volume", "volume up please",
            "increase the sound", "turn it up", "louder", "higher volume",
            "can you turn up the volume", "i can't hear, turn it up"
        ]
        volume_down_cmds = [
            "volume down", "decrease volume", "turn down the volume", "quieter please",
            "lower the volume", "make it quieter", "reduce volume", "volume down please",
            "decrease the sound", "turn it down", "softer", "lower volume",
            "it's too loud, turn it down", "can you lower the volume"
        ]
        mute_cmds = [
            "mute", "mute the sound", "silence", "mute audio", "turn off sound",
            "mute it", "unmute", "unmute audio", "toggle mute"
        ]
        
        for cmd in volume_up_cmds:
            samples.append({
                "instruction": cmd,
                "output": json.dumps({"action": "volume_up", "extra": {"amount": 10}})
            })
        for cmd in volume_down_cmds:
            samples.append({
                "instruction": cmd,
                "output": json.dumps({"action": "volume_down", "extra": {"amount": 10}})
            })
        for cmd in mute_cmds:
            samples.append({
                "instruction": cmd,
                "output": json.dumps({"action": "mute"})
            })
        
        # ============ WINDOW COMMANDS ============
        close_cmds = [
            "close window", "close this window", "close the window", "close it",
            "close current window", "close this app", "exit this", "close",
            "shut this down", "close this program", "exit window"
        ]
        minimize_cmds = [
            "minimize", "minimize window", "minimize this", "minimize the window",
            "hide window", "minimize current window", "put it down"
        ]
        maximize_cmds = [
            "maximize", "maximize window", "maximize this", "full screen",
            "maximize current window", "make it full screen", "expand window",
            "fullscreen", "go fullscreen"
        ]
        switch_cmds = [
            "switch window", "next window", "alt tab", "switch to next",
            "go to next window", "switch app", "change window", "next app"
        ]
        
        for cmd in close_cmds:
            samples.append({
                "instruction": cmd,
                "output": json.dumps({"action": "close_window", "target": "current"})
            })
        for cmd in minimize_cmds:
            samples.append({
                "instruction": cmd,
                "output": json.dumps({"action": "minimize_window", "target": "current"})
            })
        for cmd in maximize_cmds:
            samples.append({
                "instruction": cmd,
                "output": json.dumps({"action": "maximize_window", "target": "current"})
            })
        for cmd in switch_cmds:
            samples.append({
                "instruction": cmd,
                "output": json.dumps({"action": "switch_window", "target": "next"})
            })
        
        # ============ SCREENSHOT COMMANDS ============
        screenshot_cmds = [
            "take a screenshot", "screenshot", "capture screen", "take screenshot",
            "grab the screen", "screen capture", "snap the screen", "take a screen grab",
            "screenshot please", "can you take a screenshot", "capture this"
        ]
        for cmd in screenshot_cmds:
            samples.append({
                "instruction": cmd,
                "output": json.dumps({"action": "screenshot"})
            })
        
        # ============ SCROLL COMMANDS ============
        scroll_up_cmds = [
            "scroll up", "scroll upward", "go up", "page up", "scroll up please",
            "move up", "scroll to top", "up", "scroll higher"
        ]
        scroll_down_cmds = [
            "scroll down", "scroll downward", "go down", "page down", "scroll down please",
            "move down", "scroll to bottom", "down", "scroll lower"
        ]
        for cmd in scroll_up_cmds:
            samples.append({
                "instruction": cmd,
                "output": json.dumps({"action": "scroll", "target": "up", "extra": {"amount": 3}})
            })
        for cmd in scroll_down_cmds:
            samples.append({
                "instruction": cmd,
                "output": json.dumps({"action": "scroll", "target": "down", "extra": {"amount": 3}})
            })
        
        # ============ SYSTEM COMMANDS ============
        lock_cmds = [
            "lock screen", "lock the computer", "lock pc", "lock my computer",
            "lock this", "secure the computer", "lock windows"
        ]
        shutdown_cmds = [
            "shutdown", "shut down", "power off", "turn off computer",
            "shutdown computer", "shut down the pc", "power off the computer"
        ]
        restart_cmds = [
            "restart", "reboot", "restart computer", "reboot pc",
            "restart the computer", "reboot the system"
        ]
        sleep_cmds = [
            "sleep", "put to sleep", "hibernate", "sleep mode",
            "put computer to sleep", "go to sleep"
        ]
        
        for cmd in lock_cmds:
            samples.append({
                "instruction": cmd,
                "output": json.dumps({"action": "lock_screen"})
            })
        for cmd in shutdown_cmds:
            samples.append({
                "instruction": cmd,
                "output": json.dumps({"action": "shutdown", "extra": {"delay": 0}})
            })
        for cmd in restart_cmds:
            samples.append({
                "instruction": cmd,
                "output": json.dumps({"action": "restart", "extra": {"delay": 0}})
            })
        for cmd in sleep_cmds:
            samples.append({
                "instruction": cmd,
                "output": json.dumps({"action": "sleep"})
            })
        
        # ============ FILE OPERATIONS ============
        file_samples = [
            ("open my documents", {"action": "open_folder", "path": "Documents"}),
            ("open downloads folder", {"action": "open_folder", "path": "Downloads"}),
            ("open desktop", {"action": "open_folder", "path": "Desktop"}),
            ("open pictures folder", {"action": "open_folder", "path": "Pictures"}),
            ("create a new file", {"action": "create_and_open_file", "path": "new_file.txt"}),
            ("create a text file", {"action": "create_and_open_file", "path": "new_file.txt"}),
            ("open readme file", {"action": "open_file", "path": "readme.txt"}),
            ("find my pdf files", {"action": "search_files", "target": "*.pdf"}),
            ("search for documents", {"action": "search_files", "target": "*.docx"}),
        ]
        for instruction, output in file_samples:
            samples.append({
                "instruction": instruction,
                "output": json.dumps(output)
            })
        
        # ============ WEB SEARCH ============
        web_samples = [
            ("search for python tutorials", {"action": "web_search", "target": "python tutorials"}),
            ("google machine learning", {"action": "web_search", "target": "machine learning"}),
            ("search how to cook pasta", {"action": "web_search", "target": "how to cook pasta"}),
            ("look up weather forecast", {"action": "web_search", "target": "weather forecast"}),
            ("search for zentrax documentation", {"action": "web_search", "target": "zentrax documentation"}),
        ]
        for instruction, output in web_samples:
            samples.append({
                "instruction": instruction,
                "output": json.dumps(output)
            })
        
        # ============ SYSTEM INFO ============
        info_samples = [
            ("what's the battery level", {"action": "system_info", "target": "battery"}),
            ("check battery percentage", {"action": "system_info", "target": "battery"}),
            ("what time is it", {"action": "system_info", "target": "datetime"}),
            ("what's the date today", {"action": "system_info", "target": "datetime"}),
            ("show system information", {"action": "system_info", "target": "all"}),
        ]
        for instruction, output in info_samples:
            samples.append({
                "instruction": instruction,
                "output": json.dumps(output)
            })
        
        # ============ TYPING/INPUT COMMANDS ============
        type_samples = [
            ("type hello world", {"action": "type_text", "target": "hello world"}),
            ("write my email address", {"action": "type_text", "target": "email address placeholder"}),
            ("press enter", {"action": "key_press", "target": "enter"}),
            ("press escape", {"action": "key_press", "target": "escape"}),
            ("copy this", {"action": "key_combo", "target": "ctrl+c"}),
            ("paste", {"action": "key_combo", "target": "ctrl+v"}),
            ("undo", {"action": "key_combo", "target": "ctrl+z"}),
            ("save this", {"action": "key_combo", "target": "ctrl+s"}),
            ("select all", {"action": "key_combo", "target": "ctrl+a"}),
        ]
        for instruction, output in type_samples:
            samples.append({
                "instruction": instruction,
                "output": json.dumps(output)
            })
        
        return samples
    
    def format_for_training(self, samples: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format samples into chat format for fine-tuning."""
        formatted = []
        
        for sample in samples:
            # Chat format for instruction-following
            text = f"""<|system|>
{self.system_prompt}
<|user|>
{sample['instruction']}
<|assistant|>
{sample['output']}"""
            
            formatted.append({"text": text})
        
        return formatted
    
    def save_dataset(self, output_path: str) -> str:
        """Generate and save the training dataset."""
        samples = self.generate_training_samples()
        formatted = self.format_for_training(samples)
        
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(formatted, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Generated {len(formatted)} training samples")
        print(f"📁 Saved to: {output_path}")
        
        return output_path


# ============================================================================
# FINE-TUNING TRAINER
# ============================================================================

class ZentraxFineTuner:
    """Fine-tune a language model for Zentrax command generation."""
    
    def __init__(self, config: ZentraxFineTuneConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        
    def setup_quantization(self) -> Optional[BitsAndBytesConfig]:
        """Setup 4-bit quantization for memory efficiency."""
        if not self.config.use_4bit:
            return None
            
        compute_dtype = getattr(torch, self.config.bnb_4bit_compute_dtype)
        
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type=self.config.bnb_4bit_quant_type,
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=True,
        )
    
    def load_model(self):
        """Load the base model and tokenizer."""
        print(f"🔄 Loading base model: {self.config.base_model}")
        
        bnb_config = self.setup_quantization()
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.base_model,
            trust_remote_code=True,
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        
        # Load model
        model_kwargs = {
            "trust_remote_code": True,
            "device_map": "auto",
        }
        
        if bnb_config:
            model_kwargs["quantization_config"] = bnb_config
        
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model,
            **model_kwargs
        )
        
        if self.config.use_4bit:
            self.model = prepare_model_for_kbit_training(self.model)
        
        print("✅ Model loaded successfully")
    
    def setup_lora(self):
        """Setup LoRA for parameter-efficient fine-tuning."""
        print("🔧 Setting up LoRA configuration...")
        
        lora_config = LoraConfig(
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            target_modules=self.config.target_modules,
            lora_dropout=self.config.lora_dropout,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )
        
        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()
    
    def load_dataset(self) -> HFDataset:
        """Load the training dataset."""
        print(f"📂 Loading dataset from: {self.config.training_data_path}")
        
        with open(self.config.training_data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        dataset = HFDataset.from_list(data)
        print(f"✅ Loaded {len(dataset)} training samples")
        
        return dataset
    
    def train(self):
        """Run the fine-tuning process."""
        print("\n" + "="*60)
        print("🚀 STARTING ZENTRAX LLM FINE-TUNING")
        print("="*60 + "\n")
        
        # Load model
        self.load_model()
        
        # Setup LoRA
        self.setup_lora()
        
        # Load dataset
        dataset = self.load_dataset()
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.num_epochs,
            per_device_train_batch_size=self.config.batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            warmup_ratio=self.config.warmup_ratio,
            logging_steps=10,
            save_steps=100,
            save_total_limit=3,
            fp16=torch.cuda.is_available(),
            optim="paged_adamw_32bit" if self.config.use_4bit else "adamw_torch",
            lr_scheduler_type="cosine",
            report_to="none",  # Disable wandb/tensorboard
            remove_unused_columns=False,
        )
        
        # Create trainer
        trainer = SFTTrainer(
            model=self.model,
            train_dataset=dataset,
            tokenizer=self.tokenizer,
            args=training_args,
            max_seq_length=self.config.max_seq_length,
            dataset_text_field="text",
            packing=False,
        )
        
        # Train
        print("\n🎯 Training started...")
        trainer.train()
        
        # Save the model
        print("\n💾 Saving fine-tuned model...")
        trainer.save_model(self.config.output_dir)
        self.tokenizer.save_pretrained(self.config.output_dir)
        
        print(f"\n✅ Fine-tuning complete!")
        print(f"📁 Model saved to: {self.config.output_dir}")
        
        return self.config.output_dir
    
    def merge_and_export(self, output_path: Optional[str] = None):
        """Merge LoRA weights and export for Ollama."""
        if output_path is None:
            output_path = os.path.join(self.config.output_dir, "merged")
        
        print(f"\n🔀 Merging LoRA weights...")
        
        # Merge LoRA weights with base model
        merged_model = self.model.merge_and_unload()
        
        # Save merged model
        merged_model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)
        
        print(f"✅ Merged model saved to: {output_path}")
        
        # Create Modelfile for Ollama
        modelfile_content = f"""# Zentrax Fine-tuned Model
FROM {output_path}

PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER num_predict 256

SYSTEM \"\"\"You are Zentrax, an AI assistant that converts natural language commands into structured Windows automation actions. Output JSON with action, target, and extra fields.\"\"\"
"""
        
        modelfile_path = os.path.join(output_path, "Modelfile")
        with open(modelfile_path, "w") as f:
            f.write(modelfile_content)
        
        print(f"\n📝 Ollama Modelfile created: {modelfile_path}")
        print("\n🐳 To use with Ollama, run:")
        print(f"   ollama create zentrax-finetuned -f {modelfile_path}")
        
        return output_path


# ============================================================================
# INFERENCE HELPER
# ============================================================================

class ZentraxInference:
    """Run inference with the fine-tuned model."""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        
    def load(self):
        """Load the fine-tuned model."""
        print(f"🔄 Loading fine-tuned model from: {self.model_path}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            device_map="auto",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        )
        
        print("✅ Model loaded")
    
    def generate(self, user_input: str) -> str:
        """Generate a command from user input."""
        system_prompt = """You are Zentrax, an AI assistant that converts natural language commands into structured Windows automation actions. Output JSON with action, target, and extra fields."""
        
        prompt = f"""<|system|>
{system_prompt}
<|user|>
{user_input}
<|assistant|>
"""
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=128,
            temperature=0.3,
            top_p=0.9,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the assistant response
        if "<|assistant|>" in response:
            response = response.split("<|assistant|>")[-1].strip()
        
        return response


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Zentrax LLM Fine-Tuning")
    parser.add_argument("--mode", type=str, choices=["generate", "train", "inference", "all"],
                       default="all", help="Mode: generate data, train, inference, or all")
    parser.add_argument("--model", type=str, default="HuggingFaceTB/SmolLM2-360M-Instruct",
                       help="Base model to fine-tune")
    parser.add_argument("--output", type=str, default="./zentrax_finetuned",
                       help="Output directory for fine-tuned model")
    parser.add_argument("--data", type=str, default="./training_data/finetune_dataset.json",
                       help="Path for training dataset")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--prompt", type=str, help="Prompt for inference mode")
    
    args = parser.parse_args()
    
    # Create config
    config = ZentraxFineTuneConfig(
        base_model=args.model,
        output_dir=args.output,
        training_data_path=args.data,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
    )
    
    if args.mode in ["generate", "all"]:
        print("\n📊 GENERATING TRAINING DATA")
        print("-" * 40)
        generator = ZentraxDatasetGenerator()
        generator.save_dataset(config.training_data_path)
    
    if args.mode in ["train", "all"]:
        print("\n🎓 FINE-TUNING MODEL")
        print("-" * 40)
        trainer = ZentraxFineTuner(config)
        trainer.train()
        trainer.merge_and_export()
    
    if args.mode == "inference":
        if not args.prompt:
            print("❌ Please provide --prompt for inference mode")
            return
        
        print("\n🔮 RUNNING INFERENCE")
        print("-" * 40)
        inference = ZentraxInference(args.output)
        inference.load()
        result = inference.generate(args.prompt)
        print(f"\n📝 Input: {args.prompt}")
        print(f"🤖 Output: {result}")
    
    print("\n" + "="*60)
    print("✨ ZENTRAX FINE-TUNING COMPLETE!")
    print("="*60)


if __name__ == "__main__":
    main()
