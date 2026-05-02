import json
import os
import random
from pathlib import Path

from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
from trl import DPOTrainer, DPOConfig
from peft import LoraConfig, get_peft_model

ROOT = Path(__file__).resolve().parents[1]

TRAIN_FILE = ROOT / "training_data" / "path_b_preference" / "train_preferences.jsonl"
DEV_FILE = ROOT / "training_data" / "path_b_preference" / "dev_preferences.jsonl"

OUT_DIR = ROOT / "training" / "outputs" / "path_b_judge_lora"
LOG_FILE = OUT_DIR / "train_log.jsonl"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42

MODEL_NAME = os.getenv("WEEK11_BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
MODEL_REVISION = os.getenv("WEEK11_BASE_MODEL_REVISION", "main")

LEARNING_RATE = 5e-5
PER_DEVICE_BATCH_SIZE = 1
GRADIENT_ACCUMULATION_STEPS = 8
EFFECTIVE_BATCH_SIZE = PER_DEVICE_BATCH_SIZE * GRADIENT_ACCUMULATION_STEPS
EPOCHS = 1
WARMUP_RATIO = 0.03
SCHEDULER = "cosine"

LORA_RANK = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05


def log_event(event):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(event) + "\n")
    print(json.dumps(event, indent=2))


def validate_inputs():
    if not TRAIN_FILE.exists():
        raise FileNotFoundError(f"Missing train preference file: {TRAIN_FILE}")
    if not DEV_FILE.exists():
        raise FileNotFoundError(f"Missing dev preference file: {DEV_FILE}")


def main():
    validate_inputs()

    random.seed(SEED)
    set_seed(SEED)

    log_event({
        "event": "training_start",
        "path": "B",
        "trainer": "DPOTrainer",
        "algorithm": "DPO",
        "seed": SEED,
        "model_name": MODEL_NAME,
        "model_revision": MODEL_REVISION,
        "training_type": "lora_only",
        "train_file": str(TRAIN_FILE),
        "dev_file": str(DEV_FILE),
        "learning_rate": LEARNING_RATE,
        "per_device_train_batch_size": PER_DEVICE_BATCH_SIZE,
        "gradient_accumulation_steps": GRADIENT_ACCUMULATION_STEPS,
        "effective_batch_size": EFFECTIVE_BATCH_SIZE,
        "epochs": EPOCHS,
        "warmup_ratio": WARMUP_RATIO,
        "scheduler": SCHEDULER,
        "lora_rank": LORA_RANK,
        "lora_alpha": LORA_ALPHA,
        "lora_dropout": LORA_DROPOUT,
    })

    dataset = load_dataset(
        "json",
        data_files={
            "train": str(TRAIN_FILE),
            "validation": str(DEV_FILE),
        },
    )

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        revision=MODEL_REVISION,
        trust_remote_code=True,
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        revision=MODEL_REVISION,
        trust_remote_code=True,
        device_map="auto",
    )

    lora_config = LoraConfig(
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    args = DPOConfig(
        output_dir=str(OUT_DIR),
        per_device_train_batch_size=PER_DEVICE_BATCH_SIZE,
        per_device_eval_batch_size=PER_DEVICE_BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
        learning_rate=LEARNING_RATE,
        num_train_epochs=EPOCHS,
        warmup_ratio=WARMUP_RATIO,
        lr_scheduler_type=SCHEDULER,
        logging_steps=5,
        logging_dir=str(OUT_DIR / "logs"),
        eval_steps=20,
        save_steps=50,
        save_total_limit=2,
        max_length=1024,
        max_prompt_length=768,
        report_to="none",
        remove_unused_columns=False,
        seed=SEED,
    )

    trainer = DPOTrainer(
        model=model,
        args=args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        processing_class=tokenizer,
    )

    train_result = trainer.train()

    log_event({
        "event": "training_complete",
        "train_loss": getattr(train_result, "training_loss", None),
        "metrics": train_result.metrics if hasattr(train_result, "metrics") else {},
    })

    trainer.save_model(str(OUT_DIR))
    tokenizer.save_pretrained(str(OUT_DIR))

    log_event({
        "event": "model_saved",
        "output_dir": str(OUT_DIR),
    })

    print(f"Saved Path B LoRA judge adapter to {OUT_DIR}")


if __name__ == "__main__":
    main()