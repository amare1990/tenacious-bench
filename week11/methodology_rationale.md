# Methodology Rationale — Path B

## Declared Path

Path B: preference-tuned judge / critic.

## Week 10 Trace Evidence

The chosen path is grounded in Week 10 traces:

- `trace-003`: weak evidence was converted into overconfident hiring-pressure language.
- `trace-005`: internal bench terminology appeared in prospect-facing copy.
- `trace-006`: candidate output implied capacity certainty that the source evidence did not support.
- `trace-008`: the message bundled several asks instead of preserving one clear next step.
- `trace-010`: AI-maturity language created a condescending gap frame.

These are judge failures: a stronger critic should reject or down-rank the candidate before delivery.

## Paper Grounding

- Gebru et al., “Datasheets for Datasets,” Sections 3–4: motivates explicit documentation of dataset motivation, composition, collection, preprocessing, uses, distribution, and maintenance.
- Pushkarna et al., “Data Cards,” layered documentation model: motivates telescopic, periscopic, and microscopic documentation so reviewers can inspect high-level intent, section-level choices, and field-level schema details.
- Li et al. (2025), preference leakage / model-as-judge bias discussion: motivates separating generator and judge model families and forbidding the same model from generating and judging the same task.

## Alternative Paths Considered

Path A, generator fine-tuning, was dismissed because the Week 10 failures were not limited to generation quality; fluent outputs still violated Tenacious policy. Path C, trajectory or PRM training, was dismissed because the current system failure is mostly pre-send output acceptance, not multi-step tool trajectory search. Path B is the narrowest intervention aligned to the observed inconsistency failure mode.
