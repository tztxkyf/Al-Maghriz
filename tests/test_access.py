"""Tests for token-based access checks."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "python"))

from al_maghriz import (  # noqa: E402
    AccessDeniedError,
    AlMaghrizModel,
)

VALID_TOKEN = ROOT / "certificates" / "test_20260901.pem"


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


def test_valid_token():
    model = make_model()
    bars = make_bars(300)
    positions, stop_losses = model.predict(
        bars,
        token_path=VALID_TOKEN,
        user="test",
        password="test",
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


def test_wrong_password():
    model = make_model()
    bars = make_bars(300)
    with pytest.raises(AccessDeniedError):
        model.predict(
            bars,
            token_path=VALID_TOKEN,
            user="test",
            password="wrong",
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


def test_missing_token():
    model = make_model()
    bars = make_bars(300)
    missing = ROOT / "certificates" / "definitely_missing.pem"
    with pytest.raises(AccessDeniedError):
        model.predict(
            bars,
            token_path=missing,
            user="test",
            password="test",
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


def test_modified_token():
    model = make_model()
    bars = make_bars(300)
    corrupted = ROOT / "certificates" / "corrupted.pem"
    corrupted.write_text(VALID_TOKEN.read_text().strip()[:-4] + "dead")
    with pytest.raises(AccessDeniedError):
        model.predict(
            bars,
            token_path=corrupted,
            user="test",
            password="test",
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
