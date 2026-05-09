#include "CTGProcessor.h"
#include <filesystem>
#include <iostream>

int main(int argc, char* argv[]) {
    std::string imagePath = argc > 1 ? argv[1] : "../data/my_ctg.jpg";
    std::string csvPath = argc > 2 ? argv[2] : "../output/ctg_result.csv";
    std::string outputDir = std::filesystem::path(csvPath).parent_path().string();
    if (outputDir.empty()) outputDir = "../output";

    std::cout << "============================================\n";
    std::cout << " CTG Image Processing: C++ / OpenCV\n";
    std::cout << "============================================\n";

    CTGProcessor processor(outputDir);

    if (!processor.loadImage(imagePath)) {
        return 1;
    }

    processor.alignImage();
    processor.detectDimensions();
    processor.extractGraphRegions();
    processor.extractSignals();

    if (!processor.saveCsv(csvPath, 1.0)) {
        std::cerr << "[ERROR] Не удалось сохранить CSV: " << csvPath << "\n";
        return 2;
    }

    std::cout << "[OK] CSV сохранён: " << csvPath << "\n";
    std::cout << "[OK] Отладочные изображения сохранены в: " << outputDir << "\n";
    return 0;
}
