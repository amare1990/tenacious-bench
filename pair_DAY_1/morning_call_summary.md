# Morning Call Summary — Day 1

Written by Yonas Eshete | Confirmed by Amare Kassa

The draft question was doing two jobs at once asking why low-rank decomposition is mathematically sufficient and asking what rank to actually pick for a 618-pair task. Amare caught this early: "Are you asking why LoRA works, or are you asking how to size rank for this specific dataset?" Those are different questions.

He also pushed on "inherently low-rank." Did I mean provable or just observed in practice? I hadn't thought about that distinction. I updated the question to say "mathematical property" and added "narrow domain adaptation" to pin the scope. That forced me to be honest about what I was actually missing.

His read at the end: he said he knew what a good answer would look like now something that names the mechanism and lets me reason about rank 16 versus rank 4 for this task, not just recite the formula. That was enough for me to commit the question as final.

---

Amare's question had four things bundled into it: the model mechanism, training data distribution, prompt structure, and evaluation design. I pushed back: "Which one is actually blocking you? You can't write one explainer that answers all four." He thought for a second and landed on the mechanism why the model produces the same output regardless of what the probe was testing. That's the one everything else hangs off.

I also asked whether the judge failure and the model failure were the same problem or different ones. His first answer was different. I wasn't convinced if the judge was fine-tuned on preference data with the same fluency bias as the model, they have the same root cause. He came around to that. The question got a lot narrower: one mechanism, two places it shows up.

When he could describe what a satisfying answer would look like in a single sentence, we stopped.