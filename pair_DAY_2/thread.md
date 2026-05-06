
# Thread

1/ My pair-day partner asked a subtle but important agent-systems question:

What is the difference between:
- a tool the model decides to call
vs
- a function the runtime/scaffolding executes before generation?

At first glance they look similar. Internally they are very different systems.

2/ In the Week 10 `conversion-engine` implementation we reviewed, the runtime executes:

```python
check_bench_availability(...)
````

before the model generates anything.

That means the staffing constraint is enforced by software scaffolding, not autonomous model reasoning.

3/ This distinction matters because the two architectures provide completely different guarantees.

Runtime-enforced constraints are deterministic.

Model-invoked tools are probabilistic.

4/ A runtime-enforced constraint behaves like:

```python
if not bench_available:
    return "Cannot commit engineers next Monday."
```

The model never gets the opportunity to violate the rule.

5/ A model-controlled tool behaves differently.

Even if the tool returns:
“Bench unavailable”

the model may still continue into a persuasive sales continuation because tool outputs compete against pretrained conversational priors.

6/ The deeper issue is that tool outputs do not automatically become load-bearing parts of reasoning.

The model can:

* acknowledge the tool
* mention the constraint
* appear grounded

while still generating along the same high-probability trajectory.

7/ During implementation review, we found an even more important failure mode.

In one objection-response path, the model was not actually “ignoring” structured context.

The runtime never routed the context into generation at all.

8/ The objection path fell through to:

> “Understood. Thanks for the reply.”

because `reply_type="objection"` had no dedicated branch.

That changed the diagnosis completely.

9/ We fixed this by adding:

* explicit objection handling
* structured context threading
* policy-result threading
* forced `Constraint check:` reasoning before drafting

10/ The key insight:

Tool-grounding failure can happen before the model even starts reasoning.

Sometimes the issue is not attention failure or probabilistic drift.

Sometimes the runtime never makes the context reachable.

11/ Practical lesson for production agents:

Hard constraints should usually live in the runtime:

* staffing limits
* permissions
* compliance
* pricing
* security

Use model-controlled tools for:

* retrieval
* search
* decomposition
* flexible workflows

12/ Full explainer:

https://medium.com/@amaremek/your-agent-is-probably-less-autonomous-than-you-think-21f9e1f5a3e8

13/ X thread:

https://x.com/amaremek/status/2052106152108794261

14/ Reviewed implementation repository:

https://github.com/amare1990/tenacious-bench.git

---