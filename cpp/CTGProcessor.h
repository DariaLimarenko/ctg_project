#pragma once

#include "CsvWriter.h"
#include <opencv2/opencv.hpp>
#include <string>
#include <vector>

struct DimensionsInfo {
    int widthPx{};
    int heightPx{};
    double cellPx{};
    double durationSec{};
    double durationMin{};
    double pxPerSec{};
};

class CTGProcessor {
public:
    explicit CTGProcessor(std::string outputDir = "../output");

    bool loadImage(const std::string& imagePath);
    void alignImage();
    DimensionsInfo detectDimensions();
    void extractGraphRegions();
    void extractSignals();
    std::vector<CTGPoint> buildTimeSeries(double sampleRateHz = 1.0) const;
    bool saveCsv(const std::string& csvPath, double sampleRateHz = 1.0) const;

    const DimensionsInfo& dimensions() const { return dims; }

private:
    std::string outputDir;
    cv::Mat image;
    cv::Mat aligned;
    cv::Mat roiFhr;
    cv::Mat roiToco;
    DimensionsInfo dims;
    std::vector<double> fhrSignal;
    std::vector<double> tocoSignal;

    static double median(std::vector<double> values);
    static double interpolateAt(const std::vector<double>& signal, double index);
};
