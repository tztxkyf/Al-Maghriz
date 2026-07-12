#pragma once

#include "al_maghriz_api.h"
#include "internal_parameters.hpp"

namespace al_maghriz {

// Convert the public anonymous parameter set (A-H, each 0-5) into internal
// engine parameters.  Returns ALM_OK on success or ALM_INVALID_ARGUMENT when
// any public parameter is out of range.
int map_public_parameters(
    const AlMaghrizParams* params,
    InternalParameters& out
);

} // namespace al_maghriz
