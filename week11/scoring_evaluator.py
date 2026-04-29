import json
import sys
import re

BANNED_PHRASES = [
    "world-class", "top talent", "rockstar", "ninja",
    "quick chat", "i hope this email finds you well",
    "skyrocket", "supercharge", "10x", "circling back",
    "just following up", "synergize", "ecosystem"
]

def word_count(text):
    return len(text.split())

def has_banned_phrase(text):
    text_lower = text.lower()
    return any(p in text_lower for p in BANNED_PHRASES)

def uses_bench_word(text):
    return "bench" in text.lower()

def extract_first_number(text):
    match = re.search(r"\d+", text)
    return int(match.group()) if match else None

def capacity_supported(task):
    requested = extract_first_number(task["input"].get("hiring_signal", ""))
    available = extract_first_number(task["input"].get("bench_summary", ""))

    if requested is None or available is None:
        return True

    return requested <= available

def has_signal_reference(text, signal):
    important_words = [
        w.lower().strip(".,!?")
        for w in signal.split()
        if len(w) > 2
    ]
    text_lower = text.lower()
    return any(w in text_lower for w in important_words)

def has_one_cta(text):
    cta_terms = ["would", "could", "can", "calendar", "call", "reply", "book"]
    text_lower = text.lower()
    return sum(term in text_lower for term in cta_terms) <= 2

def score_task(task):
    body = task["candidate_output"]["body"]
    subject = task["candidate_output"]["subject"]
    full_text = f"{subject}\n{body}"
    rubric = task["rubric"]
    signal = task["input"]["hiring_signal"]

    score = 0
    max_score = 7

    if word_count(body) <= rubric["max_body_words"]:
        score += 1

    if len(subject) <= rubric["max_subject_chars"]:
        score += 1

    if not has_banned_phrase(full_text):
        score += 1

    if not uses_bench_word(body):
        score += 1

    if has_signal_reference(body, signal):
        score += 1

    if has_one_cta(body):
        score += 1

    if capacity_supported(task):
        score += 1

    hard_failures = []

    if uses_bench_word(body):
        hard_failures.append("external_bench_language")

    if not capacity_supported(task):
        hard_failures.append("unsupported_capacity_commitment")

    if hard_failures:
        score = min(score, 2)

    return score, max_score


if __name__ == "__main__":
    path = sys.argv[1]

    with open(path, "r") as f:
        task = json.load(f)

    score, max_score = score_task(task)
    print(f"Score: {score}/{max_score}")