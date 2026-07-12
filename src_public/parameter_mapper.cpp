#include "parameter_mapper.hpp"

namespace al_maghriz {

int map_public_parameters(
    const AlMaghrizParams* params,
    InternalParameters& out
) {
    if (params == nullptr) {
        return ALM_INVALID_ARGUMENT;
    }

    try {
        out = InternalParameters::from_public(*params);
    } catch (const InvalidParameter&) {
        return ALM_INVALID_ARGUMENT;
    } catch (...) {
        return ALM_INTERNAL_ERROR;
    }

    return ALM_OK;
}

} // namespace al_maghriz
