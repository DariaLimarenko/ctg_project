"""
Единый запуск проекта:
1. собирает C++ проект через CMake;
2. запускает C++ обработку изображения;
3. запускает Python-визуализацию CSV.

Запуск из корня проекта:
    python run_pipeline.py
"""

import os
import platform
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CPP_DIR = ROOT / "cpp"
BUILD_DIR = ROOT / "build"
DATA_IMAGE = ROOT / "data" / "my_ctg.jpg"
OUTPUT_DIR = ROOT / "output"
CSV_PATH = OUTPUT_DIR / "ctg_result.csv"
PLOT_PATH = OUTPUT_DIR / "ctg_plot.png"


def run(command, cwd=None):
    print("\n$", " ".join(map(str, command)))
    subprocess.run(command, cwd=cwd, check=True)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    BUILD_DIR.mkdir(exist_ok=True)

    run(["cmake", "-S", str(CPP_DIR), "-B", str(BUILD_DIR)])
    run(["cmake", "--build", str(BUILD_DIR), "--config", "Release"])

    exe_name = "ctg_processor.exe" if platform.system() == "Windows" else "ctg_processor"
    exe_path = BUILD_DIR / ("Release" if platform.system() == "Windows" else "") / exe_name
    if not exe_path.exists():
        exe_path = BUILD_DIR / exe_name

    run([str(exe_path), str(DATA_IMAGE), str(CSV_PATH)])
    run(["python", str(ROOT / "python" / "visualize.py"), str(CSV_PATH), str(PLOT_PATH)])

    print("\nГотово!")
    print("CSV:", CSV_PATH)
    print("PNG:", PLOT_PATH)


if __name__ == "__main__":
    main()
