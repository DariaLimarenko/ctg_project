#pragma once

#include <opencv2/opencv.hpp>
#include <vector>
#include <string>

class SignalExtractor {
public:
    static std::vector<double> extractSignal(
        const cv::Mat& roi,
        double yMinValue,
        double yMaxValue,
        const std::string& debugMaskPath = ""
    );

    static std::vector<double> movingAverage(const std::vector<double>& data, int window);

private:
    static void interpolateMissing(std::vector<double>& values, double fallbackValue);
};
