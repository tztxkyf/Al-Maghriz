#pragma once

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#if defined(_WIN32)
    #define ALM_API __declspec(dllexport)
#else
    #define ALM_API __attribute__((visibility("default")))
#endif

typedef struct {
    int64_t timestamp_ms;
    double open;
    double high;
    double low;
    double close;
} AlMaghrizBar;

typedef struct {
    int A;
    int B;
    int C;
    int D;
    int E;
    int F;
    int G;
    int H;
} AlMaghrizParams;

typedef struct {
    int status_code;
    size_t position_count;
    double* positions;
    double* stop_losses;
    const char* error_message;
} AlMaghrizResult;

enum AlMaghrizStatus {
    ALM_OK = 0,
    ALM_NOT_ENOUGH_BARS = 1,
    ALM_INVALID_ARGUMENT = 2,
    ALM_ACCESS_DENIED = 3,
    ALM_ACCESS_EXPIRED = 4,
    ALM_INTERNAL_ERROR = 5
};

ALM_API const char* alm_version();

/*
 * Run the model over `bar_count` OHLC bars and return a normalized target
 * position and its accompanying stop-loss price for each bar from index
 * `rolling_length - 1` onwards.
 *
 * The returned positions are doubles in the range [-1.0, 1.0], representing
 * the fraction of capital to allocate (e.g. +1.0 = fully long, -0.5 = half
 * short). The `stop_losses` array has the same length and contains the stop
 * price for the corresponding target position, or NaN when the position is
 * flat.
 *
 * `max_hold_bars` controls the maximum number of bars a position can be held
 * before it is force-closed. Pass 0 to auto-detect from the bar spacing
 * (48 for hourly, 20 for daily).
 *
 * The `bars` array must be sorted in chronological order: the first bar must
 * have the earliest timestamp and the last bar the latest timestamp. Duplicate
 * or out-of-order timestamps will cause `ALM_INVALID_ARGUMENT`.
 *
 * `alm_predict_ex` is the extended version that also accepts `risk_per_trade`,
 * the fraction of capital risked per trade (e.g. 0.005 = 0.5%).  `alm_predict`
 * calls `alm_predict_ex` with the default 0.5% risk budget.
 */
ALM_API AlMaghrizResult* alm_predict(
    const AlMaghrizBar* bars,
    size_t bar_count,
    size_t rolling_length,
    int max_hold_bars,
    const AlMaghrizParams* params,
    const char* token_path,
    const char* user,
    const char* password
);

ALM_API AlMaghrizResult* alm_predict_ex(
    const AlMaghrizBar* bars,
    size_t bar_count,
    size_t rolling_length,
    int max_hold_bars,
    double risk_per_trade,
    const AlMaghrizParams* params,
    const char* token_path,
    const char* user,
    const char* password
);

ALM_API void alm_free_result(AlMaghrizResult* result);

#ifdef __cplusplus
}
#endif
