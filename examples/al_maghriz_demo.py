#!/usr/bin/env python3
"""Minimal demo of the Al-Maghriz Python wrapper."""

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "python"))

from al_maghriz import AlMaghrizModel  # noqa: E402


def _load_yaml(text: str):
    try:
        import yaml
    except ImportError:
        return None
    return yaml.safe_load(text)


def load_config():
    base = Path(__file__).parent
    for ext, loader in [(".yaml", _load_yaml), (".json", json.loads)]:
        config_path = base / f"example_config{ext}"
        if config_path.exists():
            data = loader(config_path.read_text())
            if data is not None:
                return data, config_path
    return {
        "library_path": str(ROOT / "dist" / "libal_maghriz.so"),
        "token_path": str(ROOT / "certificates" / "test_20260901.pem"),
        "user": "test",
        "password": "test",
        "rolling_length": 300,
        "parameters": {
            "A": 2,
            "B": 4,
            "C": 0,
            "D": 1,
            "E": 0,
            "F": 0,
            "G": 2,
            "H": 2,
        },
    }, Path(__file__).with_name("example_config.json")


def resolve_path(path_str, base_path):
    path = Path(path_str)
    if not path.is_absolute():
        path = base_path.parent / path
    return path


def main() -> int:
    config, config_path = load_config()

    csv_path = Path(__file__).with_name("eth_hourly.csv")
    if not csv_path.exists():
        print(f"{csv_path} not found")
        return 1

    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    library_path = resolve_path(config["library_path"], config_path)
    if not library_path.exists():
        library_path = ROOT / "dist" / "libal_maghriz.so"

    model = AlMaghrizModel(library_path)
    print(f"Loaded {model.version()}")

    token_path = resolve_path(config["token_path"], config_path)
    if not token_path.exists():
        token_path = ROOT / "certificates" / "test_20260901.pem"

    user = config["user"]
    password = config["password"]
    params = config["parameters"]
    rolling_length = config["rolling_length"]

    result = model.predict(
        bars=df[["timestamp", "open", "high", "low", "close"]],
        token_path=token_path,
        user=user,
        password=password,
        rolling_length=rolling_length,
        **params,
    )
    if result is None:
        print("Not enough bars for prediction")
        return 0

    positions, stop_losses = result
    assert len(positions) == len(df) - rolling_length + 1
    assert len(stop_losses) == len(positions)
    non_zero = [p for p in positions if abs(p) > 1e-12]
    print(f"Produced {len(positions)} target positions")
    print(f"Non-zero positions: {len(non_zero)}")
    print(f"Position range: [{min(positions):.4f}, {max(positions):.4f}]")

    # Show the last target and its stop loss.
    print(f"Latest target: {positions[-1]:.6f}")
    print(f"Latest stop loss: {stop_losses[-1]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
