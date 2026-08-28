# Figure Contract For Experiment Packages

Use this before writing plotting code. The figure is part of the experiment's argument, not decoration after the fact.

## Required working note

Write a short contract to `$RUN/figures/figure_contract.md` before generating figures:

```text
Core conclusion:
Figure archetype:
Target output:
Final size:
Panel map:
  a:
  b:
  c:
Evidence hierarchy:
  hero evidence:
  validation evidence:
  controls / robustness:
Statistics needed:
Source data needed:
Reviewer risk:
```

## Rules

- The core conclusion must be one sentence with a verb.
- Every panel must answer a distinct question.
- If removing a panel does not weaken the argument, remove or merge it.
- Give the main result the clearest panel; do not make every subplot equally important by default.
- Keep controls and robustness panels visually quieter than the hero panel.

## Figure archetypes

Pick one of these before plotting:

- `quantitative grid`
- `schematic-led composite`
- `image plate + quant`
- `asymmetric mixed-modality figure`

For most experiment-suite outputs, the default is `quantitative grid`. If the experiment involves microscopy, pathology, gels, or spatial overlays, use `image plate + quant` instead.

## Reviewer-risk prompts

Before plotting, ask these privately:

- Is the sample split actually comparable across methods?
- Are the error bars / intervals defined?
- Could a skeptical reader claim cherry-picking?
- Does the figure need a direct disclosure marker because the numbers are simulated?
- Would a simpler chart communicate the same claim more clearly?
