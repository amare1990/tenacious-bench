import os
import json
import requests
import re

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
PROMPT_DIR = ROOT / "generation_scripts" / "synthesis_prompt_pack"
OUT_DIR = ROOT / "tenacious_bench_v0.1" / "synthesis_generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)

API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise ValueError("Set OPENROUTER_API_KEY env variable")

# MODEL = "openrouter/qwen/qwen3-next-80b-a3b"  
MODEL = os.getenv("OPENROUTER_MODEL_WEEK11", "qwen/qwen3-next-80b-a3b-instruct")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def call_llm(prompt):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=HEADERS,
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
            "max_tokens": 1500,
        },
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(response.text)

    content = response.json()["choices"][0]["message"]["content"]
    return content


def extract_json(text):    

    match = re.search(r"\[\s*{.*}\s*\]", text, re.DOTALL)
    if not match:
        raise ValueError("No valid JSON array found")

    return json.loads(match.group(0))


def main():
    task_counter = 0

    for prompt_file in sorted(PROMPT_DIR.glob("*.txt")):
        prompt = prompt_file.read_text()

        print(f"Running prompt: {prompt_file.name}")
        raw = call_llm(prompt)

        try:
            tasks = extract_json(raw)
        except Exception as e:
            print("Failed to parse JSON, skipping:", e)
            continue

        for t in tasks:
            t["task_id"] = f"synthesis_{task_counter:03d}"
            t.setdefault("metadata", {})
            t["metadata"]["source_prompt"] = prompt_file.name

            out_file = OUT_DIR / f"{t['task_id']}.json"
            with out_file.open("w") as f:
                json.dump(t, f, indent=2)

            task_counter += 1

    print(f"Generated {task_counter} synthesis tasks")


if __name__ == "__main__":
    main()
