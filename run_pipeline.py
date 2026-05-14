"""
Единый запуск проекта:
1. собирает C++ проект через CMake;
2. запускает C++ обработку изображения;
3. запускает Python-визуализацию CSV;
4. запускает postprocessing:
   - отдельный CSV первого графика;
   - отдельный CSV второго графика;
   - итоговый Markdown-отчёт;
   - overlay-изображение.

Запуск из корня проекта:
    python run_pipeline.py
"""

import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CPP_DIR = ROOT / "cpp"
BUILD_DIR = ROOT / "build"
DATA_IMAGE = ROOT / "data" / "my_ctg.jpg"
OUTPUT_DIR = ROOT / "output"

CSV_PATH = OUTPUT_DIR / "ctg_result.csv"
PLOT_PATH = OUTPUT_DIR / "ctg_plot.png"
FHR_CSV_PATH = OUTPUT_DIR / "fhr_timeseries.csv"
TOCO_CSV_PATH = OUTPUT_DIR / "toco_timeseries.csv"
REPORT_PATH = OUTPUT_DIR / "final_report.md"
OVERLAY_PATH = OUTPUT_DIR / "debug" / "combined_overlay.png"


def run(command, cwd=None):
    print("\n$", " ".join(map(str, command)))
    subprocess.run(command, cwd=cwd, check=True)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    BUILD_DIR.mkdir(exist_ok=True)

    if not DATA_IMAGE.exists():
        raise FileNotFoundError(f"Исходное изображение не найдено: {DATA_IMAGE}")

    python_exe = sys.executable

    run(["cmake", "-S", str(CPP_DIR), "-B", str(BUILD_DIR)])
    run(["cmake", "--build", str(BUILD_DIR), "--config", "Release"])

    exe_name = "ctg_processor.exe" if platform.system() == "Windows" else "ctg_processor"
    exe_path = BUILD_DIR / ("Release" if platform.system() == "Windows" else "") / exe_name

    if not exe_path.exists():
        exe_path = BUILD_DIR / exe_name

    run([str(exe_path), str(DATA_IMAGE), str(CSV_PATH)])

    run([
        python_exe,
        str(ROOT / "python" / "visualize.py"),
        str(CSV_PATH),
        str(PLOT_PATH)
    ])

    run([
        python_exe,
        str(ROOT / "python" / "postprocess_results.py"),
        str(CSV_PATH),
        str(OUTPUT_DIR)
    ])

    print("\nГотово!")
    print("CSV:", CSV_PATH)
    print("PNG:", PLOT_PATH)
    print("FHR CSV:", FHR_CSV_PATH)
    print("Toco CSV:", TOCO_CSV_PATH)
    print("Report:", REPORT_PATH)
    print("Overlay:", OVERLAY_PATH)


if __name__ == "__main__":
    main()
