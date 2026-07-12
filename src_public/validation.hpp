#pragma once

#include "al_maghriz_api.h"
#include <cstddef>

namespace al_maghriz {

// Validate the inputs to alm_predict / alm_predict_ex.
// Returns ALM_OK if everything is acceptable, otherwise a non-zero status code.
int validate_inputs(
    const AlMaghrizBar* bars,
    std::size_t bar_count,
    std::size_t rolling_length,
    int max_hold_bars,
    const AlMaghrizParams* params,
    const char* token_path,
    const char* user,
    const char* password
);

// Validate an optional risk-per-trade value.  Must be in (0, 1].
int validate_risk_per_trade(double risk_per_trade);

} // namespace al_maghriz
