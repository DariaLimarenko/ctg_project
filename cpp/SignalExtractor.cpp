#include "SignalExtractor.h"
#include <algorithm>
#include <cmath>
#include <numeric>

std::vector<double> SignalExtractor::extractSignal(
    const cv::Mat& roi,
    double yMinValue,
    double yMaxValue,
    const std::string& debugMaskPath
) {
    if (roi.empty()) {
        return {};
    }

    cv::Mat gray;
    cv::cvtColor(roi, gray, cv::COLOR_BGR2GRAY);

    // Чёрная кривая значительно темнее розовой сетки и фона.
    cv::Mat darkMask;
    cv::threshold(gray, darkMask, 85, 255, cv::THRESH_BINARY_INV);

    // Удаляем мелкий шум, но не разрушаем тонкую линию графика.
    cv::Mat kernel = cv::getStructuringElement(cv::MORPH_RECT, cv::Size(2, 2));
    cv::morphologyEx(darkMask, darkMask, cv::MORPH_OPEN, kernel);

    if (!debugMaskPath.empty()) {
        cv::imwrite(debugMaskPath, darkMask);
    }

    const int h = darkMask.rows;
    const int w = darkMask.cols;
    std::vector<double> yPixels(w, std::numeric_limits<double>::quiet_NaN());

    for (int x = 0; x < w; ++x) {
        std::vector<int> ys;
        for (int y = 0; y < h; ++y) {
            if (darkMask.at<uchar>(y, x) > 0) {
                ys.push_back(y);
            }
        }

        if (!ys.empty()) {
            // Медиана устойчивее к отдельным буквам, цифрам и артефактам.
            std::sort(ys.begin(), ys.end());
            yPixels[x] = static_cast<double>(ys[ys.size() / 2]);
        }
    }

    interpolateMissing(yPixels, h / 2.0);

    std::vector<double> signal(w);
    for (int x = 0; x < w; ++x) {
        signal[x] = yMaxValue - (yPixels[x] / static_cast<double>(h)) * (yMaxValue - yMinValue);
    }

    return movingAverage(signal, 11);
}

void SignalExtractor::interpolateMissing(std::vector<double>& values, double fallbackValue) {
    const int n = static_cast<int>(values.size());
    if (n == 0) return;

    std::vector<int> known;
    for (int i = 0; i < n; ++i) {
        if (!std::isnan(values[i])) known.push_back(i);
    }

    if (known.empty()) {
        std::fill(values.begin(), values.end(), fallbackValue);
        return;
    }

    for (int i = 0; i < known.front(); ++i) {
        values[i] = values[known.front()];
    }

    for (size_t k = 0; k + 1 < known.size(); ++k) {
        int left = known[k];
        int right = known[k + 1];
        double yLeft = values[left];
        double yRight = values[right];

        for (int i = left + 1; i < right; ++i) {
            double alpha = static_cast<double>(i - left) / static_cast<double>(right - left);
            values[i] = yLeft * (1.0 - alpha) + yRight * alpha;
        }
    }

    for (int i = known.back() + 1; i < n; ++i) {
        values[i] = values[known.back()];
    }
}

std::vector<double> SignalExtractor::movingAverage(const std::vector<double>& data, int window) {
    if (data.empty() || window <= 1) return data;
    if (window % 2 == 0) ++window;

    const int n = static_cast<int>(data.size());
    const int half = window / 2;
    std::vector<double> result(n);

    for (int i = 0; i < n; ++i) {
        int a = std::max(0, i - half);
        int b = std::min(n - 1, i + half);
        double sum = 0.0;
        for (int j = a; j <= b; ++j) sum += data[j];
        result[i] = sum / static_cast<double>(b - a + 1);
    }

    return result;
}
