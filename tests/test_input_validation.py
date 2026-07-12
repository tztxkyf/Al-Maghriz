"""Tests for input validation and basic rolling behavior."""

import sys
from pathlib import Path

import pytest

# Make the python wrapper importable during tests.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "python"))

from al_maghriz import (  # noqa: E402
    AccessDeniedError,
    AlMaghrizModel,
    InvalidParameterError,
)

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
    return AlMaghrizModel(lib_path)


def test_version():
    model = make_model()
    assert model.version().startswith("Al-Maghriz")


def test_too_few_bars_returns_none():
    model = make_model()
    bars = make_bars(299)
    result = model.predict(
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
    assert result is None


def test_exactly_rolling_length_returns_one():
    model = make_model()
    bars = make_bars(300)
    if not TOKEN.exists():
        pytest.skip(f"{TOKEN} not found")
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
    assert isinstance(positions, list)
    assert len(positions) == 1
    assert len(stop_losses) == 1
    assert -1.0 - 1e-9 <= positions[0] <= 1.0 + 1e-9


def test_rolling_length_1000_bars():
    model = make_model()
    bars = make_bars(1000)
    if not TOKEN.exists():
        pytest.skip(f"{TOKEN} not found")
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
    assert isinstance(positions, list)
    assert len(positions) == 1000 - 300 + 1
    assert len(stop_losses) == len(positions)


def test_invalid_parameter_out_of_range():
    model = make_model()
    bars = make_bars(300)
    if not TOKEN.exists():
        pytest.skip(f"{TOKEN} not found")
    with pytest.raises(InvalidParameterError):
        model.predict(
            bars,
            token_path=TOKEN,
            user=USER,
            password=PASSWORD,
            rolling_length=300,
            A=6,  # out of range
            B=4,
            C=1,
            D=3,
            E=0,
            F=5,
            G=2,
            H=1,
        )


def test_missing_token_raises_access_denied():
    model = make_model()
    bars = make_bars(300)
    missing = ROOT / "certificates" / "definitely_missing.pem"
    with pytest.raises(AccessDeniedError):
        model.predict(
            bars,
            token_path=missing,
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


def test_unordered_bars():
    model = make_model()
    bars = make_bars(300)
    bars[100]["timestamp"] = bars[99]["timestamp"]
    if not TOKEN.exists():
        pytest.skip(f"{TOKEN} not found")
    with pytest.raises(InvalidParameterError):
        model.predict(
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


def test_high_lower_than_low():
    model = make_model()
    bars = make_bars(300)
    bars[50]["high"] = bars[50]["low"] - 1.0
    if not TOKEN.exists():
        pytest.skip(f"{TOKEN} not found")
    with pytest.raises(InvalidParameterError):
        model.predict(
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
