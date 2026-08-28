# Data Contract For Experiment Runs

Use this file whenever the run is intended to support a measured experiment, or when the agent
searches for and binds a dataset on the fly.

`experiment-suite` is a skill system, not a fixed benchmark repository. That means `data.py`
and `config.yaml` should be generated for the current run, not frozen globally. The price of this
flexibility is that the run can become impossible to audit unless the dataset choice is written
down explicitly. `data_contract.md` is the lightweight fix.

## Required file

Write `$RUN/data_contract.md` with this structure:

```markdown
# Data Contract

## Task binding
- research question:
- task type:
- target variable:

## Dataset route
- mode: user-supplied | agent-discovered | reused-public | controlled | synthetic-fallback
- source:
- repository / landing page:
- accession / DOI / stable URL:
- version / snapshot / date accessed:
- licence / access condition:
- persistent identifier quality: DOI | accession | stable URL | none

## Files used in this run
- file or subset:
- role: train / val / test / metadata / labels / source data

## Split protocol
- split source:
- split rule:
- leakage risks:

## Pre-processing contract
- raw to model input:
- normalization / filtering:
- exclusions:

## Reuse and publication notes
- can this run be marked measured:
- source-data / FAIR follow-up needed:
- unresolved risks:
```

## Minimum rules

- `agent-discovered` is valid. If the agent searched Hugging Face, ModelScope, GEO, SRA, or a
  paper-linked repository and selected one dataset, record that explicitly.
- If the data are reused public data, record the source and version.
- Prefer a stable identifier (DOI, accession, or repository record) over an ad hoc file link.
- If the data are controlled or restricted, record the access route and do not imply open
  reproducibility.
- If no acceptable real dataset is available, say so and fall back to `synthetic-fallback`.

## When a run may be called measured

A run may be marked `measured` only if:

- the code actually ran on non-simulated data,
- the dataset contract names the source and split,
- `results.json` provenance points to the measured run,
- the report and paper can trace the numbers back to this run.

Measured does not mean perfect benchmark design. It only means the numbers came from real execution
on bound data rather than a simulator.

## FAIR minimum for this run

For experiment-suite purposes, the minimum FAIR-style bar is:

- the dataset source is findable from the contract,
- the access condition is explicit,
- the version or snapshot is recorded,
- the files used for train/val/test are named,
- the preprocessing boundary is stated clearly enough for another engineer to rerun.

## Red flags

- `data.py` reads local files but `data_contract.md` never says what they are
- dataset source is only "open-source data" with no stable route
- no split rule is written down
- controlled data are treated as openly shareable
- report says measured, but provenance still points to a simulator
