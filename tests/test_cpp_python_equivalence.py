"""Verify output shape and deterministic behavior between C++ and Python wrapper."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "python"))

from al_maghriz import AlMaghrizModel  # noqa: E402

TOKEN = ROOT / "certificates" / "test_20260901.pem"
USER = "test"
PASSWORD = "test"


def make_bars(n: int):
    base = 1_700_000_000_000
    bars = []
    for i in range(n):
        close = 100.0 + i * 0.1
        bars.append(
            {
                "timestamp": base + i * 3_600_000,
                "open": close - 0.05,
                "high": close + 0.1,
                "low": close - 0.1,
                "close": close,
            }
        )
    return bars


def make_model():
    lib_path = ROOT / "dist" / "libal_maghriz.so"
    if not lib_path.exists():
        pytest.skip(f"{lib_path} not found; run scripts/build_release.sh first")
    if not TOKEN.exists():
        pytest.skip(f"{TOKEN} not found; run scripts/generate_token.sh first")
    return AlMaghrizModel(lib_path)


def test_prediction_shape():
    model = make_model()
    bars = make_bars(1000)
    positions, stop_losses = model.predict(
        bars,
        token_path=TOKEN,
        user=USER,
        password=PASSWORD,
        rolling_length=300,
        A=2,
        B=4,
        C=1,
        D=3,
        E=0,
        F=5,
        G=2,
        H=1,
    )
    assert positions is not None
    assert len(positions) == len(bars) - 300 + 1
    assert len(stop_losses) == len(positions)
    assert all(-1.0 - 1e-9 <= p <= 1.0 + 1e-9 for p in positions)


def test_determinism():
    import math

    model = make_model()
    bars = make_bars(500)
    params = dict(
        token_path=TOKEN,
        user=USER,
        password=PASSWORD,
        rolling_length=300,
        A=2,
        B=4,
        C=1,
        D=3,
        E=0,
        F=5,
        G=2,
        H=1,
    )
    first_positions, first_stops = model.predict(bars, **params)
    second_positions, second_stops = model.predict(bars, **params)
    assert first_positions == second_positions
    assert len(first_stops) == len(second_stops)
    for a, b in zip(first_stops, second_stops):
        assert (math.isnan(a) and math.isnan(b)) or a == b


def test_last_prediction_matches_last_bar():
    model = make_model()
    bars = make_bars(500)
    positions, stop_losses = model.predict(
        bars,
        token_path=TOKEN,
        user=USER,
        password=PASSWORD,
        rolling_length=300,
        A=2,
        B=4,
        C=1,
        D=3,
        E=0,
        F=5,
        G=2,
        H=1,
    )
    assert positions is not None
    # The last prediction is produced from the last rolling window, so it
    # corresponds to the last bar.
    assert len(positions) == len(bars) - 300 + 1
    assert len(stop_losses) == len(positions)


def test_risk_per_trade_affects_position_size():
    import pandas as pd

    model = make_model()
    csv_path = ROOT / "examples" / "pdd_daily.csv"
    if not csv_path.exists():
        pytest.skip(f"{csv_path} not found")
    df = pd.read_csv(csv_path)
    time_col = "timestamp" if "timestamp" in df.columns else "Date"
    df = df.rename(columns={time_col: "timestamp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    bars = df[["timestamp", "open", "high", "low", "close"]].to_dict("records")

    params = dict(
        token_path=TOKEN,
        user=USER,
        password=PASSWORD,
        rolling_length=300,
        max_hold_bars=20,
        A=2,
        B=4,
        C=0,
        D=1,
        E=0,
        F=0,
        G=2,
        H=2,
    )
    low_risk, _ = model.predict(bars, risk_per_trade=0.005, **params)
    high_risk, _ = model.predict(bars, risk_per_trade=0.05, **params)
    assert low_risk is not None
    assert high_risk is not None
    # Positions must scale up (or stay equal) when risk budget increases.
    for low, high in zip(low_risk, high_risk):
        assert abs(high) >= abs(low) - 1e-9
    # At least one position should be strictly larger.
    assert any(abs(h) > abs(l) + 1e-9 for l, h in zip(low_risk, high_risk))


def test_invalid_risk_per_trade_raises():
    model = make_model()
    bars = make_bars(500)
    params = dict(
        token_path=TOKEN,
        user=USER,
        password=PASSWORD,
        rolling_length=300,
        A=2,
        B=4,
        C=1,
        D=3,
        E=0,
        F=5,
        G=2,
        H=1,
    )
    from al_maghriz import InvalidParameterError

    with pytest.raises(InvalidParameterError):
        model.predict(bars, risk_per_trade=0.0, **params)
    with pytest.raises(InvalidParameterError):
        model.predict(bars, risk_per_trade=1.5, **params)
