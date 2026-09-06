"""
Zentrax SmolLM2 QLoRA Fine-Tuning Script
Train SmolLM2 on the generated Zentrax dataset for Windows automation.

Usage:
    # Full training
    python scripts/train_smollm2.py --dataset data/zentrax_train.jsonl

    # Quick test run
    python scripts/train_smollm2.py --dataset data/zentrax_train.jsonl --max-samples 1000 --epochs 1

    # Resume from checkpoint
    python scripts/train_smollm2.py --dataset data/zentrax_train.jsonl --resume models/zentrax-smollm2/checkpoint-500

Requirements:
    pip install torch transformers datasets peft accelerate bitsandbytes trl tensorboard
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# ============================================================================
# DEPENDENCY CHECK
# ============================================================================

def check_dependencies():
    """Check and report missing dependencies."""
    missing = []
    
    try:
        import torch
    except ImportError:
        missing.append("torch")
    
    try:
        import transformers
    except ImportError:
        missing.append("transformers")
    
    try:
        import datasets
    except ImportError:
        missing.append("datasets")
    
    try:
        import peft
    except ImportError:
        missing.append("peft")
    
    try:
        import trl
    except ImportError:
        missing.append("trl")
    
    # bitsandbytes is optional (GPU only)
    global BITSANDBYTES_AVAILABLE
    try:
        import bitsandbytes
        BITSANDBYTES_AVAILABLE = True
    except ImportError:
        BITSANDBYTES_AVAILABLE = False
        print("⚠️  bitsandbytes not available. 4-bit quantization disabled (CPU mode).")
    
    try:
        import accelerate
    except ImportError:
        missing.append("accelerate")
    
    if missing:
        print("❌ Missing required packages:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n📦 Install all requirements with:")
        print("pip install torch transformers datasets peft accelerate trl tensorboard")
        sys.exit(1)

BITSANDBYTES_AVAILABLE = False
check_dependencies()

import torch
from datasets import load_dataset, Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
)

# Optional: bitsandbytes for quantization (GPU only)
if BITSANDBYTES_AVAILABLE:
    from transformers import BitsAndBytesConfig

from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType,
    PeftModel,
)
from trl import SFTTrainer

# Try to import DataCollatorForCompletionOnlyLM (API changed in newer versions)
try:
    from trl import DataCollatorForCompletionOnlyLM
except ImportError:
    from transformers import DataCollatorForLanguageModeling as DataCollatorForCompletionOnlyLM
    print("⚠️  Using fallback DataCollator")


# ============================================================================
# CONFIGURATION
# ============================================================================

# Available SmolLM2 models (smallest to largest)
SMOLLM2_MODELS = {
    "135m": "HuggingFaceTB/SmolLM2-135M-Instruct",
    "360m": "HuggingFaceTB/SmolLM2-360M-Instruct",
    "1.7b": "HuggingFaceTB/SmolLM2-1.7B-Instruct",
}

DEFAULT_CONFIG = {
    # Model
    "model_name": "1.7b",  # Use 1.7B for best quality
    
    # QLoRA settings
    "load_in_4bit": True,
    "bnb_4bit_compute_dtype": "bfloat16",
    "bnb_4bit_quant_type": "nf4",
    "bnb_4bit_use_double_quant": True,
    
    # LoRA settings
    "lora_r": 64,
    "lora_alpha": 128,
    "lora_dropout": 0.05,
    "target_modules": [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    
    # Training
    "num_train_epochs": 3,
    "per_device_train_batch_size": 4,
    "per_device_eval_batch_size": 4,
    "gradient_accumulation_steps": 8,
    "learning_rate": 2e-4,
    "lr_scheduler_type": "cosine",
    "warmup_ratio": 0.05,
    "weight_decay": 0.01,
    "max_grad_norm": 1.0,
    
    # Precision
    "bf16": True,
    "tf32": True,
    
    # Sequence
    "max_seq_length": 1024,
    
    # Checkpointing
    "save_strategy": "steps",
    "save_steps": 500,
    "save_total_limit": 3,
    "logging_steps": 50,
    "eval_strategy": "steps",
    "eval_steps": 500,
    
    # Output
    "output_dir": "./models/zentrax-smollm2",
}


# ============================================================================
# PROMPT TEMPLATE
# ============================================================================

SYSTEM_PROMPT = """You are Zentrax, an intelligent OS-level AI assistant for Windows automation.
Your task is to analyze user commands and generate structured JSON actions.

Guidelines:
- Understand natural language variations of commands
- Output valid JSON actions with: action, target, path, extra
- For unclear commands, ask for clarification
- Refuse harmful or dangerous requests
- Require confirmation for destructive actions"""

def format_sample(sample: Dict[str, Any]) -> str:
    """Format a training sample into the chat template."""
    
    instruction = sample.get("instruction", "")
    reasoning = sample.get("reasoning", "")
    action = sample.get("action", {})
    context = sample.get("context")
    
    # Build context string if present
    context_str = ""
    if context:
        context_str = f"\n\nContext: {json.dumps(context)}"
    
    # Format the action as JSON
    action_json = json.dumps(action, indent=2)
    
    # SmolLM2 uses ChatML format
    formatted = f"""<|im_start|>system
{SYSTEM_PROMPT}
<|im_end|>
<|im_start|>user
{instruction}{context_str}
<|im_end|>
<|im_start|>assistant
### Reasoning:
{reasoning}

### Action:
```json
{action_json}
```
<|im_end|>"""
    
    return formatted


def format_sample_simple(sample: Dict[str, Any]) -> str:
    """Simpler format without reasoning (for faster training)."""
    
    instruction = sample.get("instruction", "")
    action = sample.get("action", {})
    
    action_json = json.dumps(action)
    
    formatted = f"""<|im_start|>system
{SYSTEM_PROMPT}
<|im_end|>
<|im_start|>user
{instruction}
<|im_end|>
<|im_start|>assistant
{action_json}
<|im_end|>"""
    
    return formatted


# ============================================================================
# DATASET LOADING
# ============================================================================

def load_zentrax_dataset(
    path: str,
    max_samples: Optional[int] = None,
    eval_split: float = 0.05,
    simple_format: bool = False,
) -> tuple:
    """Load and prepare the Zentrax dataset."""
    
    print(f"📂 Loading dataset from: {path}")
    
    # Load JSONL file
    dataset = load_dataset("json", data_files=path, split="train")
    
    if max_samples:
        dataset = dataset.select(range(min(max_samples, len(dataset))))
        print(f"   Using {len(dataset)} samples (limited)")
    else:
        print(f"   Loaded {len(dataset)} samples")
    
    # Format samples
    format_fn = format_sample_simple if simple_format else format_sample
    
    def add_formatted_text(example):
        example["text"] = format_fn(example)
        return example
    
    dataset = dataset.map(add_formatted_text, num_proc=4)
    
    # Split into train/eval
    split = dataset.train_test_split(test_size=eval_split, seed=42)
    train_dataset = split["train"]
    eval_dataset = split["test"]
    
    print(f"   Train: {len(train_dataset)}, Eval: {len(eval_dataset)}")
    
    return train_dataset, eval_dataset


# ============================================================================
# MODEL LOADING
# ============================================================================

def load_model_and_tokenizer(
    model_size: str = "1.7b",
    load_in_4bit: bool = True,
    device_map: str = "auto",
):
    """Load SmolLM2 model with QLoRA configuration."""
    
    model_name = SMOLLM2_MODELS.get(model_size, model_size)
    print(f"🤖 Loading model: {model_name}")
    
    # Check if CUDA is available
    has_cuda = torch.cuda.is_available()
    
    # Quantization config (only if bitsandbytes available and CUDA)
    if load_in_4bit and BITSANDBYTES_AVAILABLE and has_cuda:
        print("   Using 4-bit quantization (QLoRA)")
        from transformers import BitsAndBytesConfig
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )
        dtype = torch.bfloat16
    else:
        bnb_config = None
        dtype = torch.float32
        if not has_cuda:
            print("   Using CPU mode (float32)")
            device_map = "cpu"
        else:
            print("   Using full precision (no quantization)")
    
    # Load model
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map=device_map,
        trust_remote_code=True,
        torch_dtype=dtype,
    )
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    
    # Set padding token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id
    
    # Ensure left padding for generation
    tokenizer.padding_side = "right"
    
    # Print model info
    total_params = sum(p.numel() for p in model.parameters())
    print(f"   Total parameters: {total_params:,}")
    
    return model, tokenizer


def setup_lora(model, config: Dict[str, Any]):
    """Configure LoRA adapters on the model."""
    
    print("🔧 Setting up LoRA adapters...")
    
    # Prepare model for k-bit training (only if quantized)
    if BITSANDBYTES_AVAILABLE and torch.cuda.is_available():
        model = prepare_model_for_kbit_training(model)
    
    # LoRA configuration
    lora_config = LoraConfig(
        r=config.get("lora_r", 64),
        lora_alpha=config.get("lora_alpha", 128),
        lora_dropout=config.get("lora_dropout", 0.05),
        target_modules=config.get("target_modules", [
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ]),
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    
    # Apply LoRA
    model = get_peft_model(model, lora_config)
    
    # Print trainable parameters
    model.print_trainable_parameters()
    
    return model


# ============================================================================
# TRAINING
# ============================================================================

def train(
    model,
    tokenizer,
    train_dataset,
    eval_dataset,
    config: Dict[str, Any],
    resume_from: Optional[str] = None,
):
    """Run the training loop."""
    
    output_dir = config.get("output_dir", "./models/zentrax-smollm2")
    
    print(f"🚀 Starting training...")
    print(f"   Output directory: {output_dir}")
    
    # Check if CUDA is available
    has_cuda = torch.cuda.is_available()
    
    # Import SFTConfig for TRL 0.26+
    try:
        from trl import SFTConfig
        use_sft_config = True
    except ImportError:
        use_sft_config = False
    
    # Formatting function for new TRL API
    def formatting_func(example):
        return example["text"]
    
    if use_sft_config:
        # TRL 0.26+ API with SFTConfig
        from trl import SFTConfig
        
        training_args = SFTConfig(
            output_dir=output_dir,
            
            # Training
            num_train_epochs=config.get("num_train_epochs", 3),
            per_device_train_batch_size=config.get("per_device_train_batch_size", 4),
            per_device_eval_batch_size=config.get("per_device_eval_batch_size", 4),
            gradient_accumulation_steps=config.get("gradient_accumulation_steps", 8),
            
            # Optimizer
            learning_rate=config.get("learning_rate", 2e-4),
            lr_scheduler_type=config.get("lr_scheduler_type", "cosine"),
            warmup_ratio=config.get("warmup_ratio", 0.05),
            weight_decay=config.get("weight_decay", 0.01),
            max_grad_norm=config.get("max_grad_norm", 1.0),
            optim="adamw_torch",
            
            # Precision (disable bf16/tf32 for CPU)
            bf16=config.get("bf16", True) and has_cuda,
            fp16=False,
            
            # Logging
            logging_dir=f"{output_dir}/logs",
            logging_steps=config.get("logging_steps", 50),
            report_to=[],  # Disable tensorboard
            
            # Checkpointing
            save_strategy=config.get("save_strategy", "steps"),
            save_steps=config.get("save_steps", 500),
            save_total_limit=config.get("save_total_limit", 3),
            
            # Evaluation
            eval_strategy=config.get("eval_strategy", "steps"),
            eval_steps=config.get("eval_steps", 500),
            metric_for_best_model="eval_loss",
            load_best_model_at_end=True,
            
            # SFT specific
            max_length=config.get("max_seq_length", 1024),
            packing=False,
            
            # Other
            gradient_checkpointing=has_cuda,
            group_by_length=True,
            dataloader_pin_memory=has_cuda,
        )
        
        # Initialize trainer (TRL 0.26+ API)
        trainer = SFTTrainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            processing_class=tokenizer,
            formatting_func=formatting_func,
        )
    else:
        # Old TRL API (pre-0.26)
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=config.get("num_train_epochs", 3),
            per_device_train_batch_size=config.get("per_device_train_batch_size", 4),
            per_device_eval_batch_size=config.get("per_device_eval_batch_size", 4),
            gradient_accumulation_steps=config.get("gradient_accumulation_steps", 8),
            learning_rate=config.get("learning_rate", 2e-4),
            lr_scheduler_type=config.get("lr_scheduler_type", "cosine"),
            warmup_ratio=config.get("warmup_ratio", 0.05),
            weight_decay=config.get("weight_decay", 0.01),
            max_grad_norm=config.get("max_grad_norm", 1.0),
            optim="adamw_torch",
            bf16=config.get("bf16", True) and has_cuda,
            fp16=False,
            logging_dir=f"{output_dir}/logs",
            logging_steps=config.get("logging_steps", 50),
            report_to=["tensorboard"],
            save_strategy=config.get("save_strategy", "steps"),
            save_steps=config.get("save_steps", 500),
            save_total_limit=config.get("save_total_limit", 3),
            eval_strategy=config.get("eval_strategy", "steps"),
            eval_steps=config.get("eval_steps", 500),
            metric_for_best_model="eval_loss",
            load_best_model_at_end=True,
            gradient_checkpointing=has_cuda,
            group_by_length=True,
            dataloader_pin_memory=has_cuda,
            use_cpu=not has_cuda,
        )
        
        # Data collator for old API
        response_template = "<|im_start|>assistant\n"
        collator = DataCollatorForCompletionOnlyLM(
            response_template=response_template,
            tokenizer=tokenizer,
        )
        
        trainer = SFTTrainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            tokenizer=tokenizer,
            data_collator=collator,
            dataset_text_field="text",
            max_seq_length=config.get("max_seq_length", 1024),
            packing=False,
        )
    
    # Train
    if resume_from:
        print(f"   Resuming from: {resume_from}")
        trainer.train(resume_from_checkpoint=resume_from)
    else:
        trainer.train()
    
    # Save final model
    final_path = f"{output_dir}/final"
    print(f"💾 Saving final model to: {final_path}")
    trainer.save_model(final_path)
    tokenizer.save_pretrained(final_path)
    
    return trainer


# ============================================================================
# EXPORT TO OLLAMA
# ============================================================================

def merge_and_export(
    base_model_name: str,
    adapter_path: str,
    output_path: str,
    quantize: bool = True,
):
    """Merge LoRA adapter with base model and export for Ollama."""
    
    print(f"🔗 Merging adapter with base model...")
    print(f"   Base model: {base_model_name}")
    print(f"   Adapter: {adapter_path}")
    
    # Load base model (full precision for merging)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    
    # Load and merge adapter
    model = PeftModel.from_pretrained(base_model, adapter_path)
    merged_model = model.merge_and_unload()
    
    # Save merged model
    print(f"💾 Saving merged model to: {output_path}")
    merged_model.save_pretrained(output_path)
    
    # Save tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
    tokenizer.save_pretrained(output_path)
    
    # Create Modelfile for Ollama
    modelfile_content = f'''# Zentrax Fine-tuned SmolLM2
# Generated: {datetime.now().isoformat()}

FROM {output_path}/zentrax-merged.Q4_K_M.gguf

PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|im_start|>"

SYSTEM """{SYSTEM_PROMPT}"""

TEMPLATE """<|im_start|>system
{{{{ .System }}}}<|im_end|>
<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
<|im_start|>assistant
"""
'''
    
    modelfile_path = f"{output_path}/Modelfile"
    with open(modelfile_path, "w") as f:
        f.write(modelfile_content)
    
    print(f"📄 Created Modelfile at: {modelfile_path}")
    print()
    print("=" * 60)
    print("NEXT STEPS FOR OLLAMA DEPLOYMENT:")
    print("=" * 60)
    print()
    print("1. Convert to GGUF format (requires llama.cpp):")
    print(f"   python llama.cpp/convert_hf_to_gguf.py {output_path} --outtype q4_k_m")
    print()
    print("2. Create Ollama model:")
    print(f"   cd {output_path}")
    print("   ollama create zentrax -f Modelfile")
    print()
    print("3. Test the model:")
    print("   ollama run zentrax 'open chrome'")
    print("=" * 60)
    
    return output_path


# ============================================================================
# INFERENCE TEST
# ============================================================================

def test_inference(model, tokenizer, prompts: list = None):
    """Test the fine-tuned model with sample prompts."""
    
    if prompts is None:
        prompts = [
            "open chrome",
            "create a folder called Projects on desktop",
            "take a screenshot",
            "search for pdf files in documents",
            "delete system32",  # Should be denied
            "volume up",
        ]
    
    print("\n" + "=" * 60)
    print("INFERENCE TEST")
    print("=" * 60)
    
    model.eval()
    
    for prompt in prompts:
        print(f"\n📝 Input: {prompt}")
        
        # Format input
        input_text = f"""<|im_start|>system
{SYSTEM_PROMPT}
<|im_end|>
<|im_start|>user
{prompt}
<|im_end|>
<|im_start|>assistant
"""
        
        # Tokenize
        inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.3,
                top_p=0.9,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.convert_tokens_to_ids("<|im_end|>"),
            )
        
        # Decode
        response = tokenizer.decode(outputs[0], skip_special_tokens=False)
        
        # Extract assistant response
        if "<|im_start|>assistant" in response:
            response = response.split("<|im_start|>assistant")[-1]
            response = response.split("<|im_end|>")[0].strip()
        
        print(f"🤖 Output: {response[:500]}")
        print("-" * 40)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Fine-tune SmolLM2 for Zentrax Windows automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full training
  python scripts/train_smollm2.py --dataset data/zentrax_train.jsonl

  # Quick test with 1000 samples
  python scripts/train_smollm2.py --dataset data/zentrax_train.jsonl --max-samples 1000 --epochs 1

  # Use smaller model for limited VRAM
  python scripts/train_smollm2.py --dataset data/zentrax_train.jsonl --model 360m

  # Resume from checkpoint
  python scripts/train_smollm2.py --dataset data/zentrax_train.jsonl --resume models/zentrax-smollm2/checkpoint-500

  # Export to Ollama after training
  python scripts/train_smollm2.py --export --adapter models/zentrax-smollm2/final
        """
    )
    
    # Dataset
    parser.add_argument("--dataset", "-d", type=str, default="data/zentrax_train.jsonl",
                       help="Path to training dataset (JSONL)")
    parser.add_argument("--max-samples", type=int, default=None,
                       help="Limit number of training samples (for testing)")
    parser.add_argument("--simple-format", action="store_true",
                       help="Use simpler format without reasoning")
    
    # Model
    parser.add_argument("--model", "-m", type=str, default="1.7b",
                       choices=["135m", "360m", "1.7b"],
                       help="SmolLM2 model size")
    parser.add_argument("--output", "-o", type=str, default="./models/zentrax-smollm2",
                       help="Output directory for model")
    
    # Training
    parser.add_argument("--epochs", type=int, default=3,
                       help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=4,
                       help="Per-device batch size")
    parser.add_argument("--lr", type=float, default=2e-4,
                       help="Learning rate")
    parser.add_argument("--lora-r", type=int, default=64,
                       help="LoRA rank")
    
    # Checkpointing
    parser.add_argument("--resume", type=str, default=None,
                       help="Resume from checkpoint path")
    parser.add_argument("--save-steps", type=int, default=500,
                       help="Save checkpoint every N steps")
    
    # Export
    parser.add_argument("--export", action="store_true",
                       help="Export to Ollama format (requires --adapter)")
    parser.add_argument("--adapter", type=str, default=None,
                       help="Path to trained adapter for export")
    
    # Other
    parser.add_argument("--test", action="store_true",
                       help="Run inference test after training")
    parser.add_argument("--no-train", action="store_true",
                       help="Skip training (useful with --test)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("   Zentrax SmolLM2 Fine-Tuning")
    print("=" * 60)
    print(f"  Model: SmolLM2-{args.model.upper()}")
    print(f"  Dataset: {args.dataset}")
    print(f"  Output: {args.output}")
    print(f"  Epochs: {args.epochs}")
    print("=" * 60)
    print()
    
    # Export mode
    if args.export:
        if not args.adapter:
            print("❌ --adapter required for export mode")
            sys.exit(1)
        
        base_model = SMOLLM2_MODELS.get(args.model, args.model)
        merge_and_export(
            base_model_name=base_model,
            adapter_path=args.adapter,
            output_path=f"{args.output}/merged",
        )
        return
    
    # Build config
    config = DEFAULT_CONFIG.copy()
    config.update({
        "model_name": args.model,
        "output_dir": args.output,
        "num_train_epochs": args.epochs,
        "per_device_train_batch_size": args.batch_size,
        "learning_rate": args.lr,
        "lora_r": args.lora_r,
        "lora_alpha": args.lora_r * 2,
        "save_steps": args.save_steps,
        "eval_steps": args.save_steps,
    })
    
    # Check CUDA
    if torch.cuda.is_available():
        print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
        print(f"   VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        print("⚠️  No GPU detected. Training will be slow.")
    print()
    
    # Load dataset
    train_dataset, eval_dataset = load_zentrax_dataset(
        args.dataset,
        max_samples=args.max_samples,
        simple_format=args.simple_format,
    )
    
    # Load model
    model, tokenizer = load_model_and_tokenizer(
        model_size=args.model,
        load_in_4bit=config["load_in_4bit"],
    )
    
    # Setup LoRA
    model = setup_lora(model, config)
    
    # Training
    if not args.no_train:
        trainer = train(
            model=model,
            tokenizer=tokenizer,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            config=config,
            resume_from=args.resume,
        )
    
    # Test inference
    if args.test:
        test_inference(model, tokenizer)
    
    print("\n✅ Training complete!")
    print(f"   Model saved to: {args.output}/final")
    print()
    print("Next steps:")
    print(f"  1. Test: python scripts/train_smollm2.py --no-train --test --adapter {args.output}/final")
    print(f"  2. Export: python scripts/train_smollm2.py --export --adapter {args.output}/final")


if __name__ == "__main__":
    main()
