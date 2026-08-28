# Code-Skeleton Quality

## Why this exists

The agent writes a runnable code package under `$RUN/experiment/`: `model.py`, `data.py`, `train.py`, `evaluate.py`, `config.yaml`, `requirements.txt`, `README.md`. Stubs (`nn.Linear(1, 1)`, random-tensor data loaders) are not acceptable — this reference defines the bar the code must clear before delivery.

**Hard target:** an engineer with the user's data should be able to launch `python train.py --config config.yaml` and have the script train *something* that responds to the data, log per-epoch loss, save a checkpoint, and evaluate on a held-out split. It need not match SOTA — it must be *real code* not stub fragments.

## Required modules and their shape

### `model.py`

A real model class for the task type. Examples:

- For Transformer time-series forecasting: a small encoder-only Transformer with patched tokenisation, ≤ 200 lines.
- For image classification: a small ConvNet or a 4-block ViT, ≤ 200 lines.
- For NLP: a 2-layer encoder over BPE tokens, ≤ 150 lines.

```python
import torch
import torch.nn as nn

class PatchedTransformer(nn.Module):
    """Minimal channel-independent patched Transformer for long-horizon forecasting."""
    def __init__(self, context_len: int, horizon: int, patch_len: int = 16,
                 stride: int = 8, d_model: int = 128, n_heads: int = 4,
                 n_layers: int = 3, dropout: float = 0.1):
        super().__init__()
        self.patch_len = patch_len
        self.stride = stride
        n_patches = (context_len - patch_len) // stride + 1

        self.embed = nn.Linear(patch_len, d_model)
        self.pos = nn.Parameter(torch.zeros(1, n_patches, d_model))
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads, dropout=dropout,
            batch_first=True, norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.head = nn.Linear(n_patches * d_model, horizon)

    def forward(self, x):  # x: [B, L, C]
        B, L, C = x.shape
        x = x.permute(0, 2, 1)                    # [B, C, L]
        x = x.unfold(-1, self.patch_len, self.stride)  # [B, C, N, P]
        x = x.reshape(B * C, -1, self.patch_len)      # [B*C, N, P]
        z = self.embed(x) + self.pos                  # [B*C, N, d]
        h = self.encoder(z)                            # [B*C, N, d]
        out = self.head(h.reshape(B * C, -1))          # [B*C, H]
        return out.reshape(B, C, -1).permute(0, 2, 1)  # [B, H, C]
```

Things that count as **placeholders to remove**: `nn.Linear(1, 1)`, `def forward(self, x): return x`, `# TODO: implement` comments, `pass` bodies.

### `data.py`

A real data loader that:
- Reads from a configurable path (`config.yaml`)
- May be generated from an agent-discovered public dataset or a user-supplied dataset for this run
- Applies the pre-processing the design calls for (normalisation, windowing)
- Returns `torch.utils.data.Dataset` and `DataLoader` with proper train/val/test split
- Falls back to a small synthetic dataset (sinusoid + noise, MNIST-like, etc.) if no real data is provided, with a clear log line

```python
import os
import torch
from torch.utils.data import Dataset, DataLoader

class TimeSeriesWindowDataset(Dataset):
    def __init__(self, data_path: str, context_len: int, horizon: int,
                 split: str = "train", normalise: bool = True):
        ...
    def __len__(self): ...
    def __getitem__(self, idx): ...

def make_loaders(cfg) -> tuple[DataLoader, DataLoader, DataLoader]:
    """Return (train, val, test) loaders. Falls back to synthetic if cfg.data_path is None."""
    ...
```

Synthetic fallback should be flagged as such — the train.py log says "WARNING: synthetic data".

`data.py` is a runtime artifact, not a repository-global benchmark binding. For each run, it should
match the dataset declared in `$RUN/data_contract.md`.

### `train.py`

A real train loop, **not** a placeholder:

```python
import argparse
import yaml
import torch
import torch.nn as nn
from torch.optim import AdamW

from data import make_loaders
from model import PatchedTransformer

def train(cfg):
    train_loader, val_loader, _ = make_loaders(cfg)
    model = PatchedTransformer(**cfg["model"])
    opt = AdamW(model.parameters(), lr=cfg["optim"]["lr"],
                weight_decay=cfg["optim"]["weight_decay"])
    loss_fn = nn.MSELoss()

    best_val = float("inf")
    for epoch in range(cfg["training"]["epochs"]):
        model.train()
        for x, y in train_loader:
            opt.zero_grad()
            yhat = model(x)
            loss = loss_fn(yhat, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        val_loss = evaluate(model, val_loader, loss_fn)
        print(f"epoch {epoch:03d} train={loss.item():.4f} val={val_loss:.4f}")
        if val_loss < best_val:
            best_val = val_loss
            torch.save(model.state_dict(), cfg["output"]["checkpoint"])

@torch.no_grad()
def evaluate(model, loader, loss_fn):
    model.eval()
    total, n = 0.0, 0
    for x, y in loader:
        yhat = model(x)
        total += loss_fn(yhat, y).item() * len(x)
        n += len(x)
    return total / max(n, 1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()
    with open(args.config) as f:
        cfg = yaml.safe_load(f)
    train(cfg)
```

### `evaluate.py`

A separate script that loads the saved checkpoint and computes the design's metrics on the test split. Outputs `results.json` with the schema defined in `references/03-results-protocol.md`.

### `config.yaml`

Real values, not `null`:

```yaml
data:
  path: ./data/ETTm1.csv
  context_len: 720
  horizon: 96
  normalise: true
model:
  context_len: 720
  horizon: 96
  patch_len: 16
  stride: 8
  d_model: 128
  n_heads: 4
  n_layers: 3
  dropout: 0.1
optim:
  lr: 0.0003
  weight_decay: 0.0
training:
  epochs: 30
  batch_size: 32
  seed: 42
output:
  checkpoint: ./checkpoint.pt
  results: ./results.json
```

The exact keys may differ by task. The important part is that the generated config binds to the
current run's dataset contract instead of silently assuming one baked-in dataset.

### `requirements.txt`

Pinned versions of what `model.py`, `data.py`, `train.py` actually import:

```
torch>=2.0
numpy>=1.24
pyyaml>=6.0
pandas>=2.0
```

Don't dump every PyData package; only what the code uses.

### `README.md`

A real README that:
- States the experiment's task and dataset assumption in 2 sentences
- Names the model briefly (architecture summary)
- Documents how to install (`pip install -r requirements.txt`)
- Documents how to launch (`python train.py --config config.yaml`)
- States the expected wall-clock per configuration on the user's hardware
- Names the synthetic fallback and disclaims that the package is a starting point, not a SOTA reproduction

## Testability

Before declaring the code skeleton complete:

```bash
cd output/experiment-suite/<slug>/experiment
python -c "import importlib; m = importlib.import_module('model'); print(m.__name__)"
python -c "import importlib; m = importlib.import_module('data'); print(m.__name__)"
python -c "import importlib; m = importlib.import_module('train'); print(m.__name__)"
python -c "import importlib; m = importlib.import_module('evaluate'); print(m.__name__)"
```

All four must import without error. (You don't need to run training — that costs hours; importing is the cheap correctness check.)

## Anti-patterns

- **Stub bodies** (`pass`, `return x`, `# TODO`).
- **Hard-coded fake data** in `data.py` without a `path:` config option.
- **No training loop in train.py**, just a `print("Training...")`.
- **`requirements.txt` listing 50 packages**, most unused.
- **README that doesn't say how to run.**

## Quick checklist

- [ ] `model.py` has a real model class for the task; no `pass` / `TODO`
- [ ] `data.py` reads from a config path; falls back to clearly-labelled synthetic
- [ ] `train.py` has a real loop with optimizer, loss, validation, checkpointing
- [ ] `evaluate.py` loads checkpoint and emits `results.json` matching the schema
- [ ] `config.yaml` has real values
- [ ] `requirements.txt` matches actual imports
- [ ] `README.md` documents install + launch + hardware expectation
- [ ] All four Python modules import cleanly
