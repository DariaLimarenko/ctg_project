"""Краткая статистика по CSV с временными рядами КТГ."""

import sys
from pathlib import Path
import pandas as pd


def main() -> None:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("../output/ctg_result.csv")
    df = pd.read_csv(csv_path, sep=";")

    print("Файл:", csv_path)
    print("Количество строк:", len(df))
    print("Длительность, мин:", round(df["time_min"].max(), 2))
    print()

    stats = df[["FHR_bpm", "Toco_value"]].describe().round(2)
    print(stats)


if __name__ == "__main__":
    main()
