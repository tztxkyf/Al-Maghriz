# Agent Notes for Al-Maghriz

This file is for AI agents and contributors working on the repository.

## Project purpose

Al-Maghriz is a proprietary Linux C++ shared library (`libal_maghriz.so`) that
exposes a minimal C ABI for directional market predictions. It is consumed from
Python via `ctypes`.

## Quick orientation

```text
include/al_maghriz_api.h      public C ABI header
src_public/                   public C++ source (compiled into the .so)
python/                       ctypes Python wrapper
examples/                     runnable demos and the Jupyter notebook
certificates/                 example/demo access token (tracked in git)
dist/libal_maghriz.so         pre-built shared library (tracked in git)
scripts/                      public build helper scripts
```

## Running the examples

A pre-built `.so` and example token are already committed, so no compilation is
needed:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas jupyter

# Python demo
python examples/al_maghriz_demo.py

# Jupyter notebooks (all executed before commit)
jupyter notebook examples/al_maghriz_demo.ipynb
jupyter notebook examples/al_maghriz_usdt_eth_pnl.ipynb
jupyter notebook examples/al_maghriz_eurusd_pnl.ipynb
jupyter notebook examples/al_maghriz_pdd_daily.ipynb

# Tests
pip install pytest
python -m pytest tests/ -v
```

`model.predict(...)` returns a tuple `(positions, stop_losses)`.  The
`stop_losses` array is parallel to `positions` and contains the stop price for
the corresponding target position, or `NaN` when flat.  Backtests in the
notebooks use open-to-close returns and the returned stop-loss prices.

## Agent guidelines

- Do not add public documentation or comments that explain the access-token
  mechanism. The public README is the only docs that should remain in git.
- Customer tokens must not be committed. The only committed token is the
  example `certificates/test_20260901.pem`.
- Avoid adding identifying metadata (names, URLs, emails) to public files such
  as `python/pyproject.toml`.
- When modifying examples, keep them minimal and focused on prediction usage.
  Backtest/cost logic should stay out of public examples unless explicitly
  requested.
- Pass the longest available bar history in a single `predict()` call.  Use
  `rolling_length` only as a warmup length, not as a sliding window size.
