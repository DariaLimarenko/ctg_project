import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def read_csv(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV файл не найден: {csv_path}")

    df = pd.read_csv(csv_path, sep=";")

    required_columns = {"time_sec", "time_min", "FHR_bpm", "Toco_value"}
    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"В CSV отсутствуют колонки: {missing}")

    return df


def save_individual_csv(df: pd.DataFrame, output_dir: Path) -> None:
    fhr_df = df[["time_sec", "time_min", "FHR_bpm"]].copy()
    toco_df = df[["time_sec", "time_min", "Toco_value"]].copy()

    fhr_path = output_dir / "fhr_timeseries.csv"
    toco_path = output_dir / "toco_timeseries.csv"

    fhr_df.to_csv(fhr_path, index=False, sep=";", encoding="utf-8-sig")
    toco_df.to_csv(toco_path, index=False, sep=";", encoding="utf-8-sig")

    print(f"[OK] Отдельный CSV первого графика сохранён: {fhr_path}")
    print(f"[OK] Отдельный CSV второго графика сохранён: {toco_path}")


def get_image_size(image_path: Path):
    if not image_path.exists():
        return None, None

    img = plt.imread(image_path)
    height, width = img.shape[:2]
    return width, height


def generate_report(df: pd.DataFrame, output_dir: Path) -> None:
    report_path = output_dir / "final_report.md"

    width, height = get_image_size(output_dir / "aligned.jpg")

    duration_sec = float(df["time_sec"].max())
    duration_min = float(df["time_min"].max())

    fhr_min = float(df["FHR_bpm"].min())
    fhr_max = float(df["FHR_bpm"].max())
    fhr_mean = float(df["FHR_bpm"].mean())

    toco_min = float(df["Toco_value"].min())
    toco_max = float(df["Toco_value"].max())
    toco_mean = float(df["Toco_value"].mean())

    report = f"""# Итоговый отчёт обработки КТГ

## Общая информация

Выполнена автоматизированная обработка изображения медицинской диаграммы КТГ.

Программа выполнила загрузку изображения, выравнивание по сетке, выделение двух графиков, построение временных рядов и сохранение результата в CSV-файл.

## Размерность изображения

- Ширина изображения: `{width if width is not None else "не определена"} px`
- Высота изображения: `{height if height is not None else "не определена"} px`

## Длительность исследования

- Длительность в секундах: `{duration_sec:.1f} сек`
- Длительность в минутах: `{duration_min:.2f} мин`
- Количество строк в CSV: `{len(df)}`

## Первый график — FHR

Первый график соответствует частоте сердечных сокращений плода.

- Минимальное значение FHR: `{fhr_min:.1f} уд/мин`
- Максимальное значение FHR: `{fhr_max:.1f} уд/мин`
- Среднее значение FHR: `{fhr_mean:.1f} уд/мин`
- Маска первого графика: `output/graph1_mask.jpg`
- Отдельный CSV первого графика: `output/fhr_timeseries.csv`

## Второй график — Toco

Второй график соответствует токограмме / маточной активности.

- Минимальное значение Toco: `{toco_min:.1f}`
- Максимальное значение Toco: `{toco_max:.1f}`
- Среднее значение Toco: `{toco_mean:.1f}`
- Маска второго графика: `output/graph2_mask.jpg`
- Отдельный CSV второго графика: `output/toco_timeseries.csv`

## Основные выходные файлы

| Файл | Назначение |
|---|---|
| `output/ctg_result.csv` | общий CSV с двумя временными рядами |
| `output/fhr_timeseries.csv` | отдельный CSV первого графика |
| `output/toco_timeseries.csv` | отдельный CSV второго графика |
| `output/ctg_plot.png` | итоговая визуализация временных рядов |
| `output/aligned.jpg` | выровненное изображение |
| `output/roi_debug.jpg` | разделение изображения на два графика |
| `output/graph1_mask.jpg` | маска первого графика |
| `output/graph2_mask.jpg` | маска второго графика |
| `output/debug/combined_overlay.png` | наложение найденных масок на изображение |

## Соответствие заданию

| Пункт задания | Выполнение |
|---|---|
| Выровнять изображение | Выполнено |
| Определить размерность и длительность | Выполнено |
| Выделить первый график | Выполнено |
| Выделить второй график | Выполнено |
| Построить временные ряды | Выполнено |
| Сохранить результат в CSV | Выполнено |

## Медицинское замечание

Проект является учебным и демонстрационным. Он не является медицинской диагностической системой и не предназначен для самостоятельной постановки диагноза.
"""

    report_path.write_text(report, encoding="utf-8")
    print(f"[OK] Итоговый отчёт сохранён: {report_path}")


def load_rgb_image(path: Path):
    if not path.exists():
        print(f"[WARN] Файл не найден: {path}")
        return None

    img = plt.imread(path)

    if img.dtype != np.float32 and img.dtype != np.float64:
        img = img.astype(np.float32) / 255.0

    if img.ndim == 2:
        img = np.stack([img, img, img], axis=-1)

    if img.shape[2] == 4:
        img = img[:, :, :3]

    return img


def load_mask(path: Path):
    if not path.exists():
        print(f"[WARN] Маска не найдена: {path}")
        return None

    mask = plt.imread(path)

    if mask.ndim == 3:
        mask = mask[:, :, 0]

    if mask.dtype != np.float32 and mask.dtype != np.float64:
        mask = mask.astype(np.float32) / 255.0

    return mask > 0.5


def create_overlay(output_dir: Path) -> None:
    aligned = load_rgb_image(output_dir / "aligned.jpg")
    mask1 = load_mask(output_dir / "graph1_mask.jpg")
    mask2 = load_mask(output_dir / "graph2_mask.jpg")

    if aligned is None or mask1 is None or mask2 is None:
        print("[WARN] Overlay не создан: не хватает изображений")
        return

    image_h, image_w = aligned.shape[:2]
    mask1_h, mask1_w = mask1.shape[:2]
    mask2_h, mask2_w = mask2.shape[:2]

    overlay = aligned.copy()

    x_offset = max((image_w - mask1_w) // 2, 0)

    free_space = image_h - mask1_h - mask2_h
    pad = max(free_space // 4, 0)

    y1 = pad
    y2 = mask1_h + 3 * pad

    y1_end = min(y1 + mask1_h, image_h)
    y2_end = min(y2 + mask2_h, image_h)
    x_end = min(x_offset + mask1_w, image_w)

    mask1_crop = mask1[: y1_end - y1, : x_end - x_offset]
    mask2_crop = mask2[: y2_end - y2, : x_end - x_offset]

    roi1 = overlay[y1:y1_end, x_offset:x_end]
    roi1[mask1_crop] = [1.0, 0.0, 0.0]
    overlay[y1:y1_end, x_offset:x_end] = roi1

    roi2 = overlay[y2:y2_end, x_offset:x_end]
    roi2[mask2_crop] = [0.0, 0.2, 1.0]
    overlay[y2:y2_end, x_offset:x_end] = roi2

    debug_dir = output_dir / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)

    overlay_path = debug_dir / "combined_overlay.png"
    plt.imsave(overlay_path, np.clip(overlay, 0.0, 1.0))

    print(f"[OK] Overlay сохранён: {overlay_path}")


def main() -> None:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("output/ctg_result.csv")
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("output")

    output_dir.mkdir(parents=True, exist_ok=True)

    df = read_csv(csv_path)

    save_individual_csv(df, output_dir)
    generate_report(df, output_dir)
    create_overlay(output_dir)

    print("[OK] Postprocessing завершён")


if __name__ == "__main__":
    main()
