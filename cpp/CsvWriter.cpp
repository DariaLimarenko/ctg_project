#include "CsvWriter.h"
#include <fstream>
#include <iomanip>

bool CsvWriter::save(const std::string& path, const std::vector<CTGPoint>& data) {
    std::ofstream file(path);
    if (!file.is_open()) {
        return false;
    }

    file << "time_sec;time_min;FHR_bpm;Toco_value\n";
    file << std::fixed << std::setprecision(3);

    for (const auto& p : data) {
        file << p.timeSec << ';'
             << p.timeMin << ';'
             << std::setprecision(1) << p.fhrBpm << ';'
             << std::setprecision(1) << p.toco << '\n'
             << std::setprecision(3);
    }

    return true;
}
