#!/usr/bin/env python3
"""Export prompt_log.json to a clean Markdown document for submission."""
import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

STARS = {1: "⭐", 2: "⭐⭐", 3: "⭐⭐⭐", 4: "⭐⭐⭐⭐", 5: "⭐⭐⭐⭐⭐"}


def load_log(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def export_md(log_path: str, out_path: str, data_folder: str = "./data"):
    log = load_log(log_path)
    meta = log.get("meta", {})
    entries = log.get("entries", [])

    # Group by phase
    by_phase = defaultdict(list)
    for e in entries:
        by_phase[e["phase"]].append(e)

    lines = []

    # Header
    lines += [
        f"# Prompt-Logbuch – {meta.get('project', 'Projekt')}",
        "",
        f"> Erstellt: {meta.get('created', '')[:10]}  ",
        f"> Exportiert: {datetime.now().strftime('%Y-%m-%d %H:%M')}  ",
        f"> Einträge gesamt: {len(entries)}",
        "",
        "---",
        "",
    ]

    # Summary table
    lines += [
        "## Übersicht",
        "",
        "| ID | Datum | Phase | Tool / Modell | Bewertung | Zweck |",
        "|----|-------|-------|---------------|-----------|-------|",
    ]
    for e in entries:
        date = e["timestamp"][:10]
        rating_str = STARS.get(e.get("rating", 0), "")
        purpose_short = e["purpose"][:50] + ("..." if len(e["purpose"]) > 50 else "")
        lines.append(
            f"| {e['id']} | {date} | {e['phase']} | {e['tool']} / {e['model']} | {rating_str} | {purpose_short} |"
        )

    lines += ["", "---", ""]

    # Entries by phase
    for phase, phase_entries in by_phase.items():
        lines += [f"## {phase}", ""]

        for e in phase_entries:
            rating_str = STARS.get(e.get("rating", 0), str(e.get("rating", "")))
            files_str = ", ".join(e.get("files_changed", [])) or "–"
            tags_str = " ".join(f"`{t}`" for t in e.get("tags", []))
            problems = e.get("problems", "").strip() or "–"

            lines += [
                f"### {e['id']} — {e['purpose']}",
                "",
                f"| Feld | Wert |",
                f"|------|------|",
                f"| **Datum** | {e['timestamp'][:16].replace('T', ' ')} |",
                f"| **Modell** | `{e['model']}` |",
                f"| **Tool** | {e['tool']} |",
                f"| **Bewertung** | {rating_str} |",
                f"| **Dateien** | {files_str} |",
                f"| **Tags** | {tags_str} |",
                "",
                "**Prompt:**",
                "",
                "```",
                e.get("prompt", ""),
                "```",
                "",
                "**Output-Zusammenfassung:**",
                "",
                e.get("output_summary", ""),
                "",
                "**Probleme / Notizen:**",
                "",
                problems,
                "",
                "---",
                "",
            ]

    # Data sources section
    data_path = Path(data_folder)
    if data_path.exists():
        csv_files = list(data_path.glob("*.csv"))
        if csv_files:
            lines += [
                "## Verwendete Datensätze",
                "",
                "| Datei | Größe |",
                "|-------|-------|",
            ]
            for csv in sorted(csv_files):
                size_kb = csv.stat().st_size // 1024
                lines.append(f"| `{csv.name}` | {size_kb} KB |")
            lines += ["", "---", ""]

    # Write output
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ Markdown exportiert: {out_path}")
    print(f"   {len(entries)} Einträge, {len(by_phase)} Phasen")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export prompt log to Markdown.")
    parser.add_argument("--log", default="./prompt_log.json")
    parser.add_argument("--out", default="./PROMPT_LOGBUCH.md")
    parser.add_argument("--data", default="./data", help="Path to data folder")
    args = parser.parse_args()
    export_md(args.log, args.out, args.data)