# Day 2 Question — Agent and Tool-Use Internals

In my Tenacious outreach agent, I built a bench availability check that I assumed the model would call when a prospect asked about staffing. It turns out the scaffolding always runs that check before the model is involved and hands the result to the model as context. So what is the real difference between a tool the model decides to call versus a function the scaffolding runs and injects — and does it matter which one you use when you are trying to enforce a hard constraint?

**Grounded in:** `agent/main.py` (lines 178–182) and `agent/enrichment.py` (`check_bench_availability`). I described this system as having a bench-gated constraint in `method.md`, but I built it as a scaffolding pre-call, not a model-invoked tool. I cannot currently defend which approach is more reliable or explain what I would lose by switching to one over the other. Closing this gap would let me rewrite the bench-constraint paragraph in `method.md` to accurately describe what is actually enforcing the constraint and why.

**Why it generalizes:** Most FDEs building agent pipelines mix scaffolding pre-calls with model-invoked tools without knowing the reliability difference between the two. Understanding this distinction changes how you design constraints in any agentic system.
