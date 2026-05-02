# Multi-LLM Routing and Anti-Leakage Policy

## Relationship to Synthesis Memos

- `llm_as_judge.md` explains why LLM-based evaluation is needed
- `synthesis_data_memo.md` explains synthetic data strategy

This document defines the **operational policy** for safe multi-LLM synthesis.

---

## Model Roles

We separate responsibilities across model tiers:

| Role | Purpose |
|------|--------|
| Frontier seed author | High-quality, difficult task generation |
| Dev-tier generator | Scalable expansion of tasks |
| Judge filter | Evaluates and filters generated tasks |

---

## Anti-Leakage Rules

### 1. No self-evaluation

A model must never generate and judge the same task.

```text
generator_model != judge_model
