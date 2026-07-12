#include "access_runtime.hpp"

#include <openssl/evp.h>

#include <algorithm>
#include <chrono>
#include <cctype>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <string>
#include <vector>

namespace al_maghriz {

namespace {

struct YearMonthDay {
    int year;
    int month;
    int day;
};

YearMonthDay today_ymd() {
    const auto now = std::chrono::system_clock::now();
    const std::time_t t = std::chrono::system_clock::to_time_t(now);
    std::tm tm = {};
    gmtime_r(&t, &tm);
    return {tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday};
}

YearMonthDay add_months(const YearMonthDay& ymd, int months) {
    const int total = ymd.year * 12 + (ymd.month - 1) + months;
    return {total / 12, (total % 12) + 1, ymd.day};
}

std::string ymd_to_string(const YearMonthDay& ymd) {
    std::ostringstream oss;
    oss << ymd.year
        << std::setw(2) << std::setfill('0') << ymd.month
        << std::setw(2) << std::setfill('0') << ymd.day;
    return oss.str();
}

std::vector<std::string> candidate_dates(const YearMonthDay& today) {
    std::vector<std::string> dates;
    dates.reserve(24);
    for (int i = 0; i < 24; ++i) {
        dates.push_back(ymd_to_string(add_months({today.year, today.month, 1}, i)));
    }
    return dates;
}

std::string sha256_hex(const std::string& input) {
    EVP_MD_CTX* ctx = EVP_MD_CTX_new();
    if (ctx == nullptr) {
        return "";
    }

    unsigned char hash[EVP_MAX_MD_SIZE];
    unsigned int length = 0;

    if (EVP_DigestInit_ex(ctx, EVP_sha256(), nullptr) != 1 ||
        EVP_DigestUpdate(ctx, input.data(), input.size()) != 1 ||
        EVP_DigestFinal_ex(ctx, hash, &length) != 1) {
        EVP_MD_CTX_free(ctx);
        return "";
    }

    EVP_MD_CTX_free(ctx);

    std::ostringstream oss;
    for (unsigned int i = 0; i < length; ++i) {
        oss << std::hex << std::setw(2) << std::setfill('0')
            << static_cast<int>(hash[i]);
    }
    return oss.str();
}

std::string read_token_file(const char* path) {
    std::ifstream file(path);
    if (!file) {
        return "";
    }

    std::string content(
        (std::istreambuf_iterator<char>(file)),
        std::istreambuf_iterator<char>()
    );

    content.erase(
        std::remove_if(
            content.begin(),
            content.end(),
            [](unsigned char c) { return std::isspace(c); }
        ),
        content.end()
    );

    return content;
}

} // anonymous namespace

AccessStatus check_access_token(
    const char* token_path,
    const char* user,
    const char* password
) {
    if (token_path == nullptr || user == nullptr || password == nullptr) {
        return AccessStatus::ACCESS_DENIED;
    }

    const std::string token = read_token_file(token_path);
    if (token.empty()) {
        return AccessStatus::TOKEN_MISSING;
    }

    if (token.size() != 64) {
        return AccessStatus::TOKEN_INVALID;
    }

    const YearMonthDay today = today_ymd();
    const auto dates = candidate_dates(today);

    for (const auto& date : dates) {
        const std::string input =
            "CaiFuMiMa_" + std::string(user) + "_" + std::string(password) + "_" + date;
        if (sha256_hex(input) == token) {
            return AccessStatus::OK;
        }
    }

    return AccessStatus::ACCESS_DENIED;
}

} // namespace al_maghriz
