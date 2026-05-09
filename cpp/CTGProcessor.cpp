#include "CTGProcessor.h"
#include "SignalExtractor.h"
#include <algorithm>
#include <cmath>
#include <filesystem>
#include <iostream>
#include <numeric>

namespace fs = std::filesystem;

CTGProcessor::CTGProcessor(std::string outputDir)
    : outputDir(std::move(outputDir)) {
    fs::create_directories(this->outputDir);
}

bool CTGProcessor::loadImage(const std::string& imagePath) {
    image = cv::imread(imagePath);
    if (image.empty()) {
        std::cerr << "[ERROR] Не удалось открыть изображение: " << imagePath << "\n";
        return false;
    }

    if (image.rows > image.cols) {
        cv::rotate(image, image, cv::ROTATE_90_CLOCKWISE);
        std::cout << "[INFO] Изображение повернуто в горизонтальное положение.\n";
    }

    aligned = image.clone();
    std::cout << "[INFO] Изображение загружено: " << aligned.cols << "x" << aligned.rows << " px\n";
    return true;
}

void CTGProcessor::alignImage() {
    if (aligned.empty()) return;

    cv::Mat gray, edges;
    cv::cvtColor(aligned, gray, cv::COLOR_BGR2GRAY);
    cv::Canny(gray, edges, 50, 150, 3);

    std::vector<cv::Vec2f> lines;
    cv::HoughLines(edges, lines, 1, CV_PI / 180.0, 300);

    std::vector<double> angles;
    for (const auto& line : lines) {
        float theta = line[1];
        double angle = theta * 180.0 / CV_PI - 90.0;
        if (std::abs(angle) < 10.0) {
            angles.push_back(angle);
        }
    }

    double angle = median(angles);
    std::cout << "[INFO] Найденный угол наклона: " << angle << " град.\n";

    if (std::abs(angle) > 0.3) {
        cv::Point2f center(aligned.cols / 2.0f, aligned.rows / 2.0f);
        cv::Mat rot = cv::getRotationMatrix2D(center, angle, 1.0);
        cv::warpAffine(aligned, aligned, rot, aligned.size(), cv::INTER_LINEAR, cv::BORDER_REPLICATE);
    }

    cv::imwrite(outputDir + "/aligned.jpg", aligned);
}

DimensionsInfo CTGProcessor::detectDimensions() {
    if (aligned.empty()) return dims;

    dims.widthPx = aligned.cols;
    dims.heightPx = aligned.rows;

    cv::Mat gray;
    cv::cvtColor(aligned, gray, cv::COLOR_BGR2GRAY);

    std::vector<double> profile(gray.cols, 0.0);
    for (int x = 0; x < gray.cols; ++x) {
        double sum = 0.0;
        for (int y = 0; y < gray.rows; ++y) {
            sum += 255.0 - gray.at<uchar>(y, x);
        }
        profile[x] = sum / gray.rows;
    }

    double mean = std::accumulate(profile.begin(), profile.end(), 0.0) / profile.size();
    double sq = 0.0;
    for (double v : profile) sq += (v - mean) * (v - mean);
    double stddev = std::sqrt(sq / profile.size());
    double threshold = mean + stddev * 0.5;

    std::vector<int> peaks;
    const int minDistance = 5;
    int lastPeak = -minDistance;
    for (int x = 1; x < static_cast<int>(profile.size()) - 1; ++x) {
        if (profile[x] > threshold && profile[x] >= profile[x - 1] && profile[x] >= profile[x + 1]) {
            if (x - lastPeak >= minDistance) {
                peaks.push_back(x);
                lastPeak = x;
            }
        }
    }

    std::vector<double> diffs;
    for (size_t i = 1; i < peaks.size(); ++i) {
        double d = peaks[i] - peaks[i - 1];
        if (d >= 5 && d <= 25) diffs.push_back(d);
    }

    dims.cellPx = diffs.empty() ? aligned.cols / 100.0 : median(diffs);

    const double secondsPerSmallCell = 6.0; // 1 мм при 1 см/мин = 6 секунд
    double smallCells = aligned.cols / dims.cellPx;
    dims.durationSec = smallCells * secondsPerSmallCell;
    dims.durationMin = dims.durationSec / 60.0;
    dims.pxPerSec = dims.cellPx / secondsPerSmallCell;

    std::cout << "[DIM] Размер изображения: " << dims.widthPx << "x" << dims.heightPx << " px\n";
    std::cout << "[DIM] Шаг малой клетки: " << dims.cellPx << " px\n";
    std::cout << "[DIM] Длительность: " << dims.durationMin << " мин\n";

    return dims;
}

void CTGProcessor::extractGraphRegions() {
    if (aligned.empty()) return;

    cv::Mat hsv;
    cv::cvtColor(aligned, hsv, cv::COLOR_BGR2HSV);

    cv::Mat mask1, mask2, redMask;
    cv::inRange(hsv, cv::Scalar(0, 40, 40), cv::Scalar(12, 255, 255), mask1);
    cv::inRange(hsv, cv::Scalar(155, 40, 40), cv::Scalar(180, 255, 255), mask2);
    cv::bitwise_or(mask1, mask2, redMask);

    std::vector<double> rowProfile(redMask.rows, 0.0);
    for (int y = 0; y < redMask.rows; ++y) {
        rowProfile[y] = cv::mean(redMask.row(y))[0];
    }

    int h = aligned.rows;
    int w = aligned.cols;
    int mid = h / 2;
    int range = h / 6;
    int from = std::max(0, mid - range);
    int to = std::min(h - 1, mid + range);

    int splitRow = mid;
    double bestValue = 1e18;
    for (int y = from; y <= to; ++y) {
        if (rowProfile[y] < bestValue) {
            bestValue = rowProfile[y];
            splitRow = y;
        }
    }

    int pad = h / 30;
    int xPad = 10;

    cv::Rect r1(xPad, pad, w - 2 * xPad, std::max(1, splitRow - 2 * pad));
    cv::Rect r2(xPad, splitRow + pad, w - 2 * xPad, std::max(1, h - splitRow - 2 * pad));

    roiFhr = aligned(r1).clone();
    roiToco = aligned(r2).clone();

    cv::Mat debug = aligned.clone();
    cv::line(debug, cv::Point(0, splitRow), cv::Point(w, splitRow), cv::Scalar(0, 255, 0), 3);
    cv::putText(debug, "Graph 1: FHR", cv::Point(20, splitRow / 2), cv::FONT_HERSHEY_SIMPLEX, 1.1, cv::Scalar(0, 200, 0), 3);
    cv::putText(debug, "Graph 2: Toco", cv::Point(20, splitRow + (h - splitRow) / 2), cv::FONT_HERSHEY_SIMPLEX, 1.1, cv::Scalar(0, 200, 0), 3);
    cv::imwrite(outputDir + "/roi_debug.jpg", debug);

    std::cout << "[ROI] Строка разделения: " << splitRow << " px\n";
    std::cout << "[ROI] FHR: " << roiFhr.cols << "x" << roiFhr.rows << " px\n";
    std::cout << "[ROI] Toco: " << roiToco.cols << "x" << roiToco.rows << " px\n";
}

void CTGProcessor::extractSignals() {
    fhrSignal = SignalExtractor::extractSignal(roiFhr, 60.0, 220.0, outputDir + "/graph1_mask.jpg");
    tocoSignal = SignalExtractor::extractSignal(roiToco, 0.0, 100.0, outputDir + "/graph2_mask.jpg");

    std::cout << "[SIGNAL] FHR точек: " << fhrSignal.size() << "\n";
    std::cout << "[SIGNAL] Toco точек: " << tocoSignal.size() << "\n";
}

std::vector<CTGPoint> CTGProcessor::buildTimeSeries(double sampleRateHz) const {
    std::vector<CTGPoint> result;
    if (fhrSignal.empty() || tocoSignal.empty() || dims.durationSec <= 0.0 || sampleRateHz <= 0.0) {
        return result;
    }

    int n = static_cast<int>(dims.durationSec * sampleRateHz);
    result.reserve(n);

    for (int i = 0; i < n; ++i) {
        double timeSec = i / sampleRateHz;
        double alpha = timeSec / dims.durationSec;

        double idxFhr = alpha * static_cast<double>(fhrSignal.size() - 1);
        double idxToco = alpha * static_cast<double>(tocoSignal.size() - 1);

        CTGPoint p;
        p.timeSec = timeSec;
        p.timeMin = timeSec / 60.0;
        p.fhrBpm = interpolateAt(fhrSignal, idxFhr);
        p.toco = interpolateAt(tocoSignal, idxToco);
        result.push_back(p);
    }

    return result;
}

bool CTGProcessor::saveCsv(const std::string& csvPath, double sampleRateHz) const {
    return CsvWriter::save(csvPath, buildTimeSeries(sampleRateHz));
}

double CTGProcessor::median(std::vector<double> values) {
    if (values.empty()) return 0.0;
    std::sort(values.begin(), values.end());
    size_t mid = values.size() / 2;
    if (values.size() % 2 == 1) return values[mid];
    return (values[mid - 1] + values[mid]) / 2.0;
}

double CTGProcessor::interpolateAt(const std::vector<double>& signal, double index) {
    if (signal.empty()) return 0.0;
    if (index <= 0.0) return signal.front();
    if (index >= signal.size() - 1) return signal.back();

    int left = static_cast<int>(std::floor(index));
    int right = left + 1;
    double alpha = index - left;
    return signal[left] * (1.0 - alpha) + signal[right] * alpha;
}
