#include "validation.hpp"

#include <cmath>
#include <cstring>

namespace al_maghriz {

namespace {

bool is_nan(double x) {
    return std::isnan(x) || std::isinf(x);
}

int validate_bar_consistency(const AlMaghrizBar* bars, std::size_t bar_count) {
    if (bar_count == 0) {
        return ALM_OK; // Length check handled elsewhere.
    }

    int64_t prev_ts = bars[0].timestamp_ms;

    for (std::size_t i = 0; i < bar_count; ++i) {
        const auto& b = bars[i];

        if (is_nan(b.open) || is_nan(b.high) || is_nan(b.low) || is_nan(b.close)) {
            return ALM_INVALID_ARGUMENT;
        }

        if (b.high < b.low) {
            return ALM_INVALID_ARGUMENT;
        }

        if (b.open < b.low || b.open > b.high) {
            return ALM_INVALID_ARGUMENT;
        }

        if (b.close < b.low || b.close > b.high) {
            return ALM_INVALID_ARGUMENT;
        }

        if (i > 0) {
            if (b.timestamp_ms <= prev_ts) {
                return ALM_INVALID_ARGUMENT;
            }
            prev_ts = b.timestamp_ms;
        }
    }

    return ALM_OK;
}

} // anonymous namespace

int validate_inputs(
    const AlMaghrizBar* bars,
    std::size_t bar_count,
    std::size_t rolling_length,
    int max_hold_bars,
    const AlMaghrizParams* params,
    const char* token_path,
    const char* user,
    const char* password
) {
    if (token_path == nullptr || user == nullptr || password == nullptr) {
        return ALM_INVALID_ARGUMENT;
    }

    if (bars == nullptr) {
        return ALM_INVALID_ARGUMENT;
    }

    if (params == nullptr) {
        return ALM_INVALID_ARGUMENT;
    }

    if (rolling_length == 0 || max_hold_bars < 0) {
        return ALM_INVALID_ARGUMENT;
    }

    if (bar_count < rolling_length) {
        return ALM_NOT_ENOUGH_BARS;
    }

    if (bar_count > 100000) {
        return ALM_INVALID_ARGUMENT;
    }

    const int status = validate_bar_consistency(bars, bar_count);
    if (status != ALM_OK) {
        return status;
    }

    return ALM_OK;
}

int validate_risk_per_trade(double risk_per_trade) {
    if (std::isnan(risk_per_trade) || std::isinf(risk_per_trade)) {
        return ALM_INVALID_ARGUMENT;
    }
    if (risk_per_trade <= 0.0 || risk_per_trade > 1.0) {
        return ALM_INVALID_ARGUMENT;
    }
    return ALM_OK;
}

} // namespace al_maghriz
