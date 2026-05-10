#!/usr/bin/env python3
"""Quick overview of all CSV files in a data folder."""
import argparse
from pathlib import Path

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def inspect_csv(path: Path):
    print(f"\n📄 {path.name}  ({path.stat().st_size // 1024} KB)")
    print("─" * 50)
    if HAS_PANDAS:
        try:
            df = pd.read_csv(path, nrows=5)
            print(f"   Zeilen (gesamt): ~{sum(1 for _ in open(path)) - 1}")
            print(f"   Spalten ({len(df.columns)}): {', '.join(df.columns.tolist())}")
            print(f"   Datentypen:\n{df.dtypes.to_string()}")
            print(f"\n   Vorschau (5 Zeilen):")
            print(df.to_string(index=False))
        except Exception as e:
            print(f"   ⚠️ Fehler beim Lesen: {e}")
    else:
        # Fallback: plain Python
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = [f.readline().strip() for _ in range(6)]
        print(f"   Header: {lines[0]}")
        print(f"   Erste Zeilen:")
        for line in lines[1:]:
            if line:
                print(f"     {line[:100]}")


def main():
    parser = argparse.ArgumentParser(description="Inspect CSV files in data folder.")
    parser.add_argument("--folder", default="./data", help="Path to data folder")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.exists():
        print(f"❌ Ordner nicht gefunden: {args.folder}")
        return

    csv_files = sorted(folder.glob("*.csv"))
    if not csv_files:
        print(f"📭 Keine CSV-Dateien in {args.folder}")
        return

    print(f"🗂  {len(csv_files)} CSV-Datei(en) in '{args.folder}'")
    for csv in csv_files:
        inspect_csv(csv)

    print(f"\n✅ Übersicht abgeschlossen.")
    if not HAS_PANDAS:
        print("💡 Tipp: Installiere pandas für detailliertere Statistiken: pip install pandas")


if __name__ == "__main__":
    main()