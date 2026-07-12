"""Public Python wrapper for the Al-Maghriz shared library."""

import ctypes
import os
from dataclasses import dataclass
from typing import List, Optional, Sequence, Union


class AlMaghrizError(Exception):
    """Base exception for Al-Maghriz errors."""


class AccessDeniedError(AlMaghrizError):
    """Raised when the token is missing, malformed or does not grant access."""


class AccessExpiredError(AlMaghrizError):
    """Raised when the token is no longer valid."""


class InvalidParameterError(AlMaghrizError):
    """Raised when public parameters are out of range or inputs are invalid."""


class InternalEngineError(AlMaghrizError):
    """Raised for unexpected internal engine errors."""


@dataclass
class AlMaghrizBar:
    timestamp_ms: int
    open: float
    high: float
    low: float
    close: float


class _AlMaghrizBarC(ctypes.Structure):
    _fields_ = [
        ("timestamp_ms", ctypes.c_int64),
        ("open", ctypes.c_double),
        ("high", ctypes.c_double),
        ("low", ctypes.c_double),
        ("close", ctypes.c_double),
    ]


class _AlMaghrizParamsC(ctypes.Structure):
    _fields_ = [
        ("A", ctypes.c_int),
        ("B", ctypes.c_int),
        ("C", ctypes.c_int),
        ("D", ctypes.c_int),
        ("E", ctypes.c_int),
        ("F", ctypes.c_int),
        ("G", ctypes.c_int),
        ("H", ctypes.c_int),
    ]


class _AlMaghrizResultC(ctypes.Structure):
    _fields_ = [
        ("status_code", ctypes.c_int),
        ("position_count", ctypes.c_size_t),
        ("positions", ctypes.POINTER(ctypes.c_double)),
        ("stop_losses", ctypes.POINTER(ctypes.c_double)),
        ("error_message", ctypes.c_char_p),
    ]


# Status codes mirrored from al_maghriz_api.h
_ALM_OK = 0
_ALM_NOT_ENOUGH_BARS = 1
_ALM_INVALID_ARGUMENT = 2
_ALM_ACCESS_DENIED = 3
_ALM_ACCESS_EXPIRED = 4
_ALM_INTERNAL_ERROR = 5


class AlMaghrizModel:
    """Loadable interface to the Al-Maghriz C++ shared library.

    Parameters
    ----------
    library_path:
        Path to ``libal_maghriz.so``.
    """

    def __init__(self, library_path: Union[str, os.PathLike]):
        self._lib = ctypes.CDLL(str(library_path))
        self._configure_abi()

    def _configure_abi(self) -> None:
        self._lib.alm_version.restype = ctypes.c_char_p
        self._lib.alm_version.argtypes = []

        self._lib.alm_predict.restype = ctypes.POINTER(_AlMaghrizResultC)
        self._lib.alm_predict.argtypes = [
            ctypes.POINTER(_AlMaghrizBarC),
            ctypes.c_size_t,
            ctypes.c_size_t,
            ctypes.c_int,
            ctypes.POINTER(_AlMaghrizParamsC),
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
        ]

        self._lib.alm_predict_ex.restype = ctypes.POINTER(_AlMaghrizResultC)
        self._lib.alm_predict_ex.argtypes = [
            ctypes.POINTER(_AlMaghrizBarC),
            ctypes.c_size_t,
            ctypes.c_size_t,
            ctypes.c_int,
            ctypes.c_double,
            ctypes.POINTER(_AlMaghrizParamsC),
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
        ]

        self._lib.alm_free_result.restype = None
        self._lib.alm_free_result.argtypes = [ctypes.POINTER(_AlMaghrizResultC)]

    def version(self) -> str:
        """Return the library version string."""
        value = self._lib.alm_version()
        if value is None:
            return ""
        return value.decode("utf-8")

    def predict(
        self,
        bars: Sequence,
        token_path: Union[str, os.PathLike],
        user: str,
        password: str,
        rolling_length: int = 300,
        max_hold_bars: int = 0,
        risk_per_trade: float = 0.005,
        **anonymous_params,
    ) -> Optional[tuple[List[float], List[float]]]:
        """Run the model and return normalized target positions and stop losses.

        Returns ``None`` when fewer than ``rolling_length`` bars are supplied.
        Otherwise returns a tuple ``(positions, stop_losses)`` where each list
        has length ``len(bars) - rolling_length + 1``.  ``positions`` contains
        values in ``[-1.0, 1.0]`` and ``stop_losses`` contains the accompanying
        stop price (or ``NaN`` when the position is flat).

        ``max_hold_bars`` controls the maximum bars a position is held before
        force-close. Pass 0 to auto-detect from bar spacing (48 for hourly,
        20 for daily).

        ``risk_per_trade`` is the fraction of capital risked per trade (default
        0.005 = 0.5%).  Larger values produce larger target positions when the
        stop distance is wide.
        """
        if len(bars) < rolling_length:
            return None

        if not isinstance(risk_per_trade, (int, float)):
            raise InvalidParameterError("risk_per_trade must be a number")
        if not 0.0 < risk_per_trade <= 1.0:
            raise InvalidParameterError(
                f"risk_per_trade={risk_per_trade} is out of range (0, 1.0]"
            )

        params = self._build_params(anonymous_params)
        c_bars = self._convert_bars(bars)

        result = self._lib.alm_predict_ex(
            c_bars,
            len(bars),
            rolling_length,
            max_hold_bars,
            float(risk_per_trade),
            ctypes.byref(params),
            os.fspath(token_path).encode("utf-8"),
            user.encode("utf-8"),
            password.encode("utf-8"),
        )

        try:
            self._raise_on_error(result)
            count = result.contents.position_count
            positions = [result.contents.positions[i] for i in range(count)]
            stop_losses = [result.contents.stop_losses[i] for i in range(count)]
            return positions, stop_losses
        finally:
            self._lib.alm_free_result(result)

    def _build_params(self, anonymous_params) -> _AlMaghrizParamsC:
        keys = ["A", "B", "C", "D", "E", "F", "G", "H"]
        missing = [k for k in keys if k not in anonymous_params]
        if missing:
            raise InvalidParameterError(f"Missing parameters: {missing}")

        try:
            values = {k: int(anonymous_params[k]) for k in keys}
        except (TypeError, ValueError) as exc:
            raise InvalidParameterError(f"Parameters must be integers: {exc}")

        for k, v in values.items():
            if not 0 <= v <= 5:
                raise InvalidParameterError(
                    f"Parameter {k}={v} is out of range [0, 5]"
                )

        return _AlMaghrizParamsC(
            A=values["A"],
            B=values["B"],
            C=values["C"],
            D=values["D"],
            E=values["E"],
            F=values["F"],
            G=values["G"],
            H=values["H"],
        )

    def _convert_bars(
        self, bars: Sequence
    ) -> ctypes.Array:
        # Accept pandas DataFrames directly.
        records = self._to_records(bars)
        c_bars = (_AlMaghrizBarC * len(records))()
        for i, bar in enumerate(records):
            c_bars[i] = self._to_c_bar(bar)
        return c_bars

    def _to_records(self, bars):
        # pandas DataFrame
        if hasattr(bars, "to_dict") and hasattr(bars, "iterrows"):
            return bars.to_dict("records")
        return bars

    def _to_c_bar(self, bar) -> _AlMaghrizBarC:
        if isinstance(bar, AlMaghrizBar):
            return _AlMaghrizBarC(
                timestamp_ms=bar.timestamp_ms,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
            )

        # Accept dict-like or pandas-Series-like objects.
        if hasattr(bar, "timestamp_ms"):
            ts = bar.timestamp_ms
        elif "timestamp_ms" in bar:
            ts = bar["timestamp_ms"]
        elif "timestamp" in bar:
            ts = bar["timestamp"]
        else:
            raise InvalidParameterError(f"Bar object missing timestamp: {bar}")

        # Convert pandas Timestamp / datetime to integer milliseconds.
        if hasattr(ts, "timestamp"):
            ts = int(ts.timestamp() * 1000)
        else:
            ts = int(ts)

        return _AlMaghrizBarC(
            timestamp_ms=ts,
            open=float(bar["open"]),
            high=float(bar["high"]),
            low=float(bar["low"]),
            close=float(bar["close"]),
        )

    def _raise_on_error(self, result) -> None:
        if not result:
            raise InternalEngineError("alm_predict returned null")

        code = result.contents.status_code
        message = ""
        if result.contents.error_message:
            try:
                message = result.contents.error_message.decode("utf-8")
            except Exception:
                message = str(result.contents.error_message)

        if code == _ALM_OK:
            return
        if code == _ALM_NOT_ENOUGH_BARS:
            return
        if code == _ALM_INVALID_ARGUMENT:
            raise InvalidParameterError(message or "invalid argument")
        if code == _ALM_ACCESS_DENIED:
            raise AccessDeniedError(message or "access denied")
        if code == _ALM_ACCESS_EXPIRED:
            raise AccessExpiredError(message or "access expired")
        raise InternalEngineError(message or f"internal error (code {code})")
