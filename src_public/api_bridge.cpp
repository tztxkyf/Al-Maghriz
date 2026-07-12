#include "al_maghriz_api.h"

#include "access_runtime.hpp"
#include "parameter_mapper.hpp"
#include "type3_engine.hpp"
#include "validation.hpp"

#include <chrono>
#include <cstdlib>
#include <cstring>
#include <new>
#include <vector>

namespace al_maghriz {

namespace {

const char* version_string() {
    return "Al-Maghriz Core 1.0.0";
}

const char* access_status_message(AccessStatus s) {
    switch (s) {
        case AccessStatus::OK:
            return "ok";
        case AccessStatus::TOKEN_MISSING:
            return "token file not found";
        case AccessStatus::TOKEN_READ_ERROR:
            return "token read error";
        case AccessStatus::TOKEN_INVALID:
            return "token invalid";
        case AccessStatus::ACCESS_DENIED:
            return "access denied";
        case AccessStatus::INTERNAL_ERROR:
            return "internal error";
        default:
            return "access check failed";
    }
}

int access_status_to_alm(AccessStatus s) {
    switch (s) {
        case AccessStatus::OK:
            return ALM_OK;
        case AccessStatus::ACCESS_DENIED:
            return ALM_ACCESS_DENIED;
        case AccessStatus::TOKEN_MISSING:
        case AccessStatus::TOKEN_READ_ERROR:
        case AccessStatus::TOKEN_INVALID:
        case AccessStatus::INTERNAL_ERROR:
            return ALM_ACCESS_DENIED;
        default:
            return ALM_ACCESS_DENIED;
    }
}

AlMaghrizResult* make_error_result(int status, const char* message) {
    auto* result = new (std::nothrow) AlMaghrizResult();
    if (result == nullptr) {
        return nullptr;
    }
    result->status_code = status;
    result->position_count = 0;
    result->positions = nullptr;
    result->error_message = message;
    return result;
}

} // anonymous namespace

} // namespace al_maghriz

extern "C" {

ALM_API const char* alm_version() {
    return al_maghriz::version_string();
}

namespace {

AlMaghrizResult* alm_predict_impl(
    const AlMaghrizBar* bars,
    size_t bar_count,
    size_t rolling_length,
    int max_hold_bars,
    double risk_per_trade,
    const AlMaghrizParams* params,
    const char* token_path,
    const char* user,
    const char* password
) {
    using namespace al_maghriz;

    // Input validation.
    const int input_status = validate_inputs(
        bars,
        bar_count,
        rolling_length,
        max_hold_bars,
        params,
        token_path,
        user,
        password
    );
    if (input_status != ALM_OK) {
        const char* msg = (input_status == ALM_NOT_ENOUGH_BARS)
            ? "not enough bars"
            : "invalid argument";
        return make_error_result(input_status, msg);
    }

    const int risk_status = validate_risk_per_trade(risk_per_trade);
    if (risk_status != ALM_OK) {
        return make_error_result(
            ALM_INVALID_ARGUMENT,
            "risk_per_trade must be in (0, 1.0]"
        );
    }

    // Token check.
    const AccessStatus access_status = check_access_token(
        token_path,
        user,
        password
    );
    if (access_status != AccessStatus::OK) {
        const int alm_status = access_status_to_alm(access_status);
        return make_error_result(
            alm_status,
            access_status_message(access_status)
        );
    }

    // Parameter mapping.
    InternalParameters internal_params;
    const int map_status = map_public_parameters(params, internal_params);
    if (map_status != ALM_OK) {
        return make_error_result(
            ALM_INVALID_ARGUMENT,
            "invalid parameter set"
        );
    }

    // Run model and produce normalized target positions and stop-loss prices.
    std::vector<double> positions;
    std::vector<double> stop_losses;
    try {
        auto prediction = Type3Engine::predict(
            bars,
            bar_count,
            rolling_length,
            max_hold_bars,
            risk_per_trade,
            internal_params
        );
        positions = std::move(prediction.first);
        stop_losses = std::move(prediction.second);
    } catch (...) {
        return make_error_result(ALM_INTERNAL_ERROR, "engine error");
    }

    // Allocate result and copy arrays.
    auto* result = new (std::nothrow) AlMaghrizResult();
    if (result == nullptr) {
        return make_error_result(ALM_INTERNAL_ERROR, "out of memory");
    }

    result->status_code = ALM_OK;
    result->position_count = positions.size();

    if (!positions.empty()) {
        result->positions = static_cast<double*>(
            std::malloc(sizeof(double) * positions.size())
        );
        if (result->positions == nullptr) {
            delete result;
            return make_error_result(ALM_INTERNAL_ERROR, "out of memory");
        }
        std::memcpy(
            result->positions,
            positions.data(),
            sizeof(double) * positions.size()
        );

        result->stop_losses = static_cast<double*>(
            std::malloc(sizeof(double) * stop_losses.size())
        );
        if (result->stop_losses == nullptr) {
            std::free(result->positions);
            delete result;
            return make_error_result(ALM_INTERNAL_ERROR, "out of memory");
        }
        std::memcpy(
            result->stop_losses,
            stop_losses.data(),
            sizeof(double) * stop_losses.size()
        );
    } else {
        result->positions = nullptr;
        result->stop_losses = nullptr;
    }

    result->error_message = nullptr;
    return result;
}

} // anonymous namespace

ALM_API AlMaghrizResult* alm_predict(
    const AlMaghrizBar* bars,
    size_t bar_count,
    size_t rolling_length,
    int max_hold_bars,
    const AlMaghrizParams* params,
    const char* token_path,
    const char* user,
    const char* password
) {
    return alm_predict_impl(
        bars,
        bar_count,
        rolling_length,
        max_hold_bars,
        0.005, // default 0.5% risk per trade
        params,
        token_path,
        user,
        password
    );
}

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
) {
    return alm_predict_impl(
        bars,
        bar_count,
        rolling_length,
        max_hold_bars,
        risk_per_trade,
        params,
        token_path,
        user,
        password
    );
}

ALM_API void alm_free_result(AlMaghrizResult* result) {
    if (result == nullptr) {
        return;
    }
    if (result->positions != nullptr) {
        std::free(result->positions);
    }
    if (result->stop_losses != nullptr) {
        std::free(result->stop_losses);
    }
    delete result;
}

} // extern "C"
