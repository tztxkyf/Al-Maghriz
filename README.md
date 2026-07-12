# Al-Maghriz

> *Al-Maghriz* (المغرز) is the Arabic name for the star **Megrez** (δ Ursae
> Majoris). In Chinese it is known as **Tiān Quán** (天權, "Star of Celestial
> Balance") or **Běi Dǒu Sì** (北斗四, "Fourth Star of the Northern Dipper"),
> as it is the fourth star in the Big Dipper asterism.

Al-Maghriz is a Linux C++ shared library (`libal_maghriz.so`) that exposes a
minimal C ABI for directional market predictions. It is designed to be called
from Python (or any language that can load a C ABI).

## Features

- Minimal C ABI: `alm_version`, `alm_predict`, `alm_free_result`
- Eight anonymous integer parameters (`A`–`H`, range `0–5`)
- Returns normalized target positions in `[-1.0, 1.0]` plus accompanying stop-loss prices
- Built-in position sizing, stops, and max-hold logic
- Python wrapper with `ctypes`
- Release build with hidden symbols and stripped binary

## Project Layout

```text
Al-Maghriz/
├── CMakeLists.txt
├── README.md
├── .gitignore
├── include/
│   └── al_maghriz_api.h          # public C ABI header
├── src_public/                   # public implementation layer
├── python/                       # Python wrapper
├── examples/                     # demo scripts, notebooks and sample data
├── tests/                        # pytest suite
├── scripts/                      # build tools
├── certificates/                 # example token (committed)
└── dist/                         # pre-built shared library
```

## Use the Pre-built Library

A release `dist/libal_maghriz.so` is already committed in the repository, so
end users can use it without compiling. You only need the OpenSSL runtime:

```bash
sudo apt-get update
sudo apt-get install -y libssl3
```

## Run the Demo

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas matplotlib jupyter

# Python demo
python examples/al_maghriz_demo.py

# Jupyter notebooks
jupyter notebook examples/al_maghriz_demo.ipynb
jupyter notebook examples/al_maghriz_usdt_eth_pnl.ipynb
jupyter notebook examples/al_maghriz_eurusd_pnl.ipynb
jupyter notebook examples/al_maghriz_pdd_daily.ipynb
```

The demos load the bundled CSVs (`examples/eth_hourly.csv` and
`examples/eurusd_hourly.csv`) and run signals with the default parameter set.

## Python Quick Start

```python
from al_maghriz import AlMaghrizModel

model = AlMaghrizModel("./dist/libal_maghriz.so")
positions, stop_losses = model.predict(
    bars=df[["timestamp", "open", "high", "low", "close"]],
    token_path="./certificates/test_20260901.pem",
    user="test",
    password="test",
    rolling_length=300,
    max_hold_bars=0,  # 0 = auto-detect (48 hourly / 20 daily)
    A=2, B=4, C=0, D=1, E=0, F=0, G=2, H=2,
)
```

`positions` is a list of normalized target positions in `[-1.0, 1.0]`, one for
each bar from index `rolling_length - 1` onwards.  `stop_losses` is a parallel
list containing the stop price for each target position, or `NaN` when the
position is flat.  The model executes at the open of the signal bar and holds
through the close, so a consumer backtest should use **open-to-close** returns
and add its own cost assumptions.

`risk_per_trade` (default `0.005` = 0.5%) controls position sizing.  The target
position is sized so that losing the distance from entry to the returned stop
price risks exactly this fraction of capital, capped at `1.0` (full leverage).
Wider stops therefore produce smaller positions.  Pass a larger value, e.g.
`risk_per_trade=0.02`, to increase exposure on volatile instruments.

Input bars must be supplied in chronological order, earliest timestamp first and
latest timestamp last. Out-of-order, duplicate, or non-monotonic timestamps will
be rejected with `ALM_INVALID_ARGUMENT`.

All eight parameters (`A`–`H`) accept integer values in the range `0–5`.
Values outside this range are rejected with `ALM_INVALID_ARGUMENT`.

You can store `user`, `password`, and parameters in a config file
(`examples/example_config.json` or `examples/example_config.yaml`) and load
them in your script.

## Run Tests

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pytest pandas

python -m pytest tests/ -v
```

## Renewing or Extending Your Token

Each token has an expiry date embedded in its filename (e.g.
`certificates/test_20260901.pem`). When your token expires, contact the author
to subscribe to a longer license. Provide your current `user`, the desired new
`end_date`, and any volume or deployment details needed for pricing.

## License

Proprietary — see [`LICENSE`](LICENSE).
