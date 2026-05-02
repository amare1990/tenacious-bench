from huggingface_hub import HfApi
from pathlib import Path

MODEL_DIR = Path("week11/training/outputs/path_b_judge_lora")
REPO_ID = "amaremek/tenacious-judge-pathb"

if not MODEL_DIR.exists():
    raise FileNotFoundError(f"Missing model directory: {MODEL_DIR}")

required = [
    "adapter_config.json",
    "adapter_model.safetensors",
]

missing = [f for f in required if not (MODEL_DIR / f).exists()]
if missing:
    raise FileNotFoundError(f"Missing required adapter files: {missing}")

api = HfApi()

api.create_repo(
    repo_id=REPO_ID,
    repo_type="model",
    exist_ok=True,
)

api.upload_folder(
    folder_path=str(MODEL_DIR),
    repo_id=REPO_ID,
    repo_type="model",
    commit_message="Upload Tenacious Path B judge LoRA adapter",
)

print(f"Uploaded model to https://huggingface.co/{REPO_ID}")