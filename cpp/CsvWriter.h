#pragma once

#include <string>
#include <vector>

struct CTGPoint {
    double timeSec{};
    double timeMin{};
    double fhrBpm{};
    double toco{};
};

class CsvWriter {
public:
    static bool save(const std::string& path, const std::vector<CTGPoint>& data);
};
