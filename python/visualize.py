"""
Визуализация результата обработки КТГ.

C++ программа формирует CSV:
    time_sec;time_min;FHR_bpm;Toco_value

Этот Python-скрипт читает CSV, дополнительно сглаживает данные
и сохраняет итоговый график в PNG.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    from scipy.signal import savgol_filter
except Exception:
    savgol_filter = None


def smooth_signal(values: np.ndarray, window: int = 31) -> np.ndarray:
    """Сглаживание временного ряда."""
    if len(values) < 7:
        return values

    if window >= len(values):
        window = len(values) - 1
    if window % 2 == 0:
        window -= 1
    if window < 5:
        return values

    if savgol_filter is not None:
        return savgol_filter(values, window_length=window, polyorder=3)

    kernel = np.ones(window) / window
    return np.convolve(values, kernel, mode="same")


def read_csv(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV файл не найден: {csv_path}")

    df = pd.read_csv(csv_path, sep=";")
    required = {"time_sec", "time_min", "FHR_bpm", "Toco_value"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"В CSV не хватает колонок: {missing}")

    return df


def plot_timeseries(df: pd.DataFrame, output_path: Path) -> None:
    df = df.copy()
    df["FHR_smooth"] = smooth_signal(df["FHR_bpm"].to_numpy(dtype=float), 31)
    df["Toco_smooth"] = smooth_signal(df["Toco_value"].to_numpy(dtype=float), 31)

    duration = df["time_min"].max()

    fig = plt.figure(figsize=(16, 8), facecolor="#fafafa")

    ax1 = fig.add_subplot(2, 1, 1)
    ax1.plot(df["time_min"], df["FHR_smooth"], linewidth=1.2, label="ЧСС плода (FHR)")
    ax1.axhline(120, linestyle="--", linewidth=0.8, alpha=0.7, label="норма нижняя")
    ax1.axhline(160, linestyle="--", linewidth=0.8, alpha=0.7, label="норма верхняя")
    ax1.set_ylim(60, 220)
    ax1.set_ylabel("ЧСС, уд/мин")
    ax1.set_xlabel("Время, мин")
    ax1.set_title("График 1 — Частота сердечных сокращений плода (FHR)", fontweight="bold")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    ax2 = fig.add_subplot(2, 1, 2)
    ax2.plot(df["time_min"], df["Toco_smooth"], linewidth=1.2, label="Токограмма (Toco)")
    ax2.set_ylim(0, 120)
    ax2.set_ylabel("Значение Toco")
    ax2.set_xlabel("Время, мин")
    ax2.set_title("График 2 — Токограмма / маточная активность", fontweight="bold")
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    fig.suptitle(
        f"КТГ — восстановленные временные ряды | Длительность: {duration:.1f} мин | Скорость: 1 см/мин",
        fontsize=13,
        fontweight="bold",
    )

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"[OK] График сохранён: {output_path}")


def main() -> None:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("output/ctg_result.csv")
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("output/ctg_plot.png")

    df = read_csv(csv_path)
    print(f"[INFO] Загружено строк: {len(df)}")
    print(df.head(10).to_string(index=False))

    plot_timeseries(df, output_path)


if __name__ == "__main__":
    main()
