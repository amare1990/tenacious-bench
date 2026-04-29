import json
import sys
import re

BANNED_PHRASES = [
    "world-class", "top talent", "rockstar", "ninja",
    "quick chat", "i hope this email finds you well"
]

def word_count(text):
    return len(text.split())

def has_banned_phrase(text):
    text_lower = text.lower()
    return any(p in text_lower for p in BANNED_PHRASES)

def uses_bench_word(text):
    return "bench" in text.lower()

def has_signal_reference(text, signal):
    # simple check: at least one keyword overlap
    for word in signal.lower().split():
        if word in text.lower():
            return True
    return False

def has_one_cta(text):
    # naive: look for one question mark
    return text.count("?") <= 1

def score_task(task):
    body = task["candidate_output"]["body"]
    subject = task["candidate_output"]["subject"]
    rubric = task["rubric"]
    signal = task["input"]["hiring_signal"]

    score = 0
    max_score = 6

    # 1. word count
    if word_count(body) <= rubric["max_body_words"]:
        score += 1

    # 2. subject length
    if len(subject) <= rubric["max_subject_chars"]:
        score += 1

    # 3. banned phrases
    if not has_banned_phrase(body):
        score += 1

    # 4. bench usage
    if not uses_bench_word(body):
        score += 1

    # 5. grounding
    if has_signal_reference(body, signal):
        score += 1

    # 6. CTA
    if has_one_cta(body):
        score += 1

    return score, max_score


if __name__ == "__main__":
    path = sys.argv[1]
    with open(path, "r") as f:
        task = json.load(f)

    score, max_score = score_task(task)
    print(f"Score: {score}/{max_score}")