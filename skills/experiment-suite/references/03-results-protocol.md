# Results Protocol

## Why this exists

`results.json` is the structured artefact that figures and reports build on. Whether the agent writes a deterministic simulated JSON or loads a measured JSON from the user's run, the schema must be uniform and the `provenance` field must be explicit. This reference defines the schema and the discipline.

## Required schema

```json
{
  "task": "long-horizon time-series forecasting",
  "dataset": "ETTm1",
  "horizons": [96, 192, 336, 720],
  "metrics": ["MSE", "MAE"],
  "seeds": [42, 43, 44],
  "provenance": {
    "mode": "simulated|measured",
    "source": "simulator|loaded from <path>|measured run on <hardware>",
    "timestamp": "2026-05-09T14:30:00Z",
    "git_sha": "abc1234"
  },
  "summary": {
    "<method_name>": {
      "<metric>": {
        "<horizon>": {
          "mean": 0.354,
          "std": 0.008,
          "n_seeds": 3
        }
      }
    }
  },
  "ablation": {
    "<variant_name>": {
      "<metric>": {
        "<horizon>": {
          "mean": 0.391,
          "std": 0.011,
          "n_seeds": 3,
          "delta_vs_full": 0.037
        }
      }
    }
  },
  "training_curves": {
    "<method_name>": {
      "train_loss": [0.612, 0.488, ...],
      "val_loss":   [0.589, 0.471, ...]
    }
  },
  "notes": "Free-form caveats: dataset version, hyperparameter search budget, hardware."
}
```

Not every experiment needs all blocks — `training_curves` is optional, `ablation` is optional if the design didn't include one. But `task`, `dataset`, `metrics`, `seeds`, `provenance`, and `summary` are required.

## Provenance discipline

The `provenance` block is non-negotiable.

### Simulated mode

```json
"provenance": {
  "mode": "simulated",
  "source": "experiment-suite/scripts/simulator.py",
  "timestamp": "2026-05-09T14:30:00Z",
  "note": "Numbers are randomly generated to mimic plausible value ranges; not measured."
}
```

### Measured mode (user supplied)

```json
"provenance": {
  "mode": "measured",
  "source": "loaded from /home/user/runs/2026-05-08/results.json",
  "timestamp": "2026-05-09T14:30:00Z",
  "hardware": "1× A100 80GB",
  "n_configs": 24,
  "wall_clock_hours": 38.5
}
```

### Measured mode (agent-discovered or agent-bound data)

When the agent itself found and bound an open dataset for this run, the provenance should still
name the actual run source and reference the bound dataset contract:

```json
"provenance": {
  "mode": "measured",
  "source": "measured run from experiment/train.py using dataset bound in data_contract.md",
  "dataset_contract": "./data_contract.md",
  "timestamp": "2026-05-09T14:30:00Z",
  "hardware": "1× A100 80GB"
}
```

### Mixed mode (some real, some simulated)

When part of the table is measured and part is simulated (e.g., baselines were run, but the new method was not), the `provenance` block becomes a mapping:

```json
"provenance": {
  "mode": "mixed",
  "by_method": {
    "DLinear": {"mode": "measured", "source": "..."},
    "PatchTST": {"mode": "measured", "source": "..."},
    "Ours": {"mode": "simulated", "source": "simulator"}
  }
}
```

Mixed mode is a smell — surface it loudly in the report and the disclosure footnote, and consider whether the experiment is worth publishing in this state.

### Auto-measured mode (sandbox / Jupyter execution)

When the agent uses `sandbox_execute` or Jupyter MCP to run the experiment code
automatically, the results are "auto-measured" — they come from real code
execution, not from the agent's imagination, but the execution environment
may differ from a production research setup.

```json
"provenance": {
  "mode": "measured",
  "source": "sandbox_execute via SANDBOX_API_BASE",
  "execution_time": 15.3,
  "timestamp": "2026-07-08T14:30:00Z",
  "environment_note": "Remote sandbox — may differ from local hardware"
}
```

Auto-measured results carry the same weight as user-measured results for
*correctness* (the code really ran), but the report should note the execution
environment when reporting wall-clock times or hardware-dependent metrics.

The three provenance modes in order of reliability:

| Mode | Source | Disclosure |
| --- | --- | --- |
| `simulated` | Agent-generated deterministic values | Must say "simulated" in every artifact |
| `measured` (auto) | `sandbox_execute` or Jupyter MCP | Note execution environment |
| `measured` (user) | User ran `train.py` themselves | Gold standard |

## Multi-seed rule

Each metric/horizon cell should have:
- `mean`, `std` over all seeds
- `n_seeds` ≥ 3 (otherwise the std is meaningless)
- Per-seed individual values stored under a separate top-level `runs` block if the user / reviewer wants them

If the experiment was run on a single seed, mark `n_seeds: 1` and `std: null` and acknowledge the limitation in the report.

## Writing a clean simulated results.json

When the agent writes the simulated JSON itself (no upstream simulator anymore), keep it minimal and well-formed:

1. Keep `summary`, `seeds`, and create the `provenance` block.
2. Move per-seed details to `runs` if useful, drop if not.
3. Remove the long disclaimer string from the JSON (it's prose; put it in the report).
4. Add `task`, `dataset`, `horizons`, `metrics` if the simulator didn't.
5. Ensure all numeric values are JSON numbers, not strings.

## Validation

Before declaring results complete:

```python
import json
with open("results.json") as f:
    r = json.load(f)
required = {"task", "dataset", "metrics", "seeds", "provenance", "summary"}
missing = required - set(r.keys())
assert not missing, f"missing fields: {missing}"
assert r["provenance"].get("mode") in {"simulated", "measured", "mixed"}
for method, by_metric in r["summary"].items():
    for metric, value in by_metric.items():
        # value can be a flat dict (single horizon) or nested by horizon
        if isinstance(value, dict) and "mean" not in value:
            for horizon, cell in value.items():
                assert "mean" in cell and "std" in cell
print("OK")
```

If validation fails, fix the schema before drafting the report or generating figures.

## Anti-patterns

- **Missing provenance.** A results.json without `provenance` is unusable downstream.
- **Single-seed without disclosure.** Either run more seeds or set `n_seeds: 1` and `std: null` and mention it in the report.
- **Per-seed variance hidden.** If the std across seeds is large (≥ 10% of the mean), say so in the report; don't bury it.
- **Inconsistent units.** "MSE" in one cell and "Mean Squared Error" in another is the same metric — pick one.
- **String numbers.** `"mean": "0.354"` breaks downstream tools; always emit JSON numbers.
- **Measured with no data binding.** If the numbers came from real execution but there is no
  `data_contract.md` or equivalent source record, the run is not auditable.

## Quick checklist

- [ ] `task`, `dataset`, `metrics`, `seeds`, `provenance`, `summary` all present
- [ ] `provenance.mode` is `simulated`, `measured`, or `mixed`
- [ ] Each cell has `mean`, `std`, `n_seeds`
- [ ] `n_seeds` ≥ 3 (or single-seed disclosed)
- [ ] No leftover simulator placeholder fields (`disclaimer` string, `runs` if not used)
- [ ] JSON numbers, not strings
- [ ] Validation script above passes
