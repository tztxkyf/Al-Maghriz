#pragma once

#include <cstddef>

namespace al_maghriz {

enum class AccessStatus {
    OK = 0,
    TOKEN_MISSING,
    TOKEN_READ_ERROR,
    TOKEN_INVALID,
    ACCESS_DENIED,
    INTERNAL_ERROR
};

struct AccessContext {
    std::size_t rolling_length;
    std::size_t bar_count;
};

// Read the token file and check it against the supplied credentials.
AccessStatus check_access_token(
    const char* token_path,
    const char* user,
    const char* password
);

} // namespace al_maghriz
