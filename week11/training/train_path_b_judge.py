import os
from pathlib import Path

from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import DPOTrainer, DPOConfig
from peft import LoraConfig, get_peft_model

ROOT = Path(__file__).resolve().parents[1]

TRAIN_FILE = ROOT / "training_data" / "path_b_preference" / "train_preferences.jsonl"
DEV_FILE = ROOT / "training_data" / "path_b_preference" / "dev_preferences.jsonl"

OUT_DIR = ROOT / "training" / "outputs" / "path_b_judge_lora"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = os.getenv("WEEK11_BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")


def main():
    dataset = load_dataset(
        "json",
        data_files={
            "train": str(TRAIN_FILE),
            "validation": str(DEV_FILE),
        },
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
        device_map="auto",
    )

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
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

    args = DPOConfig(
        output_dir=str(OUT_DIR),
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=5e-5,
        num_train_epochs=1,
        logging_steps=5,
        eval_steps=20,
        save_steps=50,
        save_total_limit=2,
        max_length=1024,
        max_prompt_length=768,
        report_to="none",
        remove_unused_columns=False,
    )

    trainer = DPOTrainer(
        model=model,
        args=args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        processing_class=tokenizer,
    )

    trainer.train()
    trainer.save_model(str(OUT_DIR))
    tokenizer.save_pretrained(str(OUT_DIR))

    print(f"Saved Path B LoRA judge adapter to {OUT_DIR}")


if __name__ == "__main__":
    main()
