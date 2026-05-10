#!/usr/bin/env python3
"""Add a new entry to prompt_log.json — interactive or CLI mode."""
import json
import argparse
from datetime import datetime
from pathlib import Path

PHASES = [
    "Meilenstein 1 – Phase 1",
    "Meilenstein 1 – Phase 2",
    "Meilenstein 2 – Phase 1",
    "Meilenstein 2 – Phase 2",
]

TOOLS = ["Cursor", "Copilot", "Claude.ai", "ChatGPT", "Gemini", "Other"]


def load_log(path: str) -> dict:
    log_path = Path(path)
    if not log_path.exists():
        print(f"❌ Log not found at {path}. Run init_log.py first.")
        exit(1)
    with open(log_path, encoding="utf-8") as f:
        return json.load(f)


def save_log(path: str, log: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


def next_id(entries: list) -> str:
    if not entries:
        return "P001"
    last = entries[-1]["id"]
    num = int(last[1:]) + 1
    return f"P{num:03d}"


def prompt_interactive() -> dict:
    print("\n📝 Neuer Logbuch-Eintrag\n" + "─" * 40)

    # Phase
    print("Phase:")
    for i, p in enumerate(PHASES, 1):
        print(f"  {i}. {p}")
    phase_idx = int(input("Auswahl [1-4]: ").strip()) - 1
    phase = PHASES[phase_idx]

    # Tool
    print("\nTool:")
    for i, t in enumerate(TOOLS, 1):
        print(f"  {i}. {t}")
    tool_idx = int(input("Auswahl [1-6]: ").strip()) - 1
    tool = TOOLS[tool_idx]

    model = input("\nModell (z.B. claude-sonnet-4-20250514, gpt-4o): ").strip()
    purpose = input("Verwendungszweck (1-2 Sätze): ").strip()

    print("Prompt (Ende mit einer Leerzeile):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    prompt_text = "\n".join(lines)

    output_summary = input("\nOutput-Zusammenfassung: ").strip()
    files_raw = input("Geänderte Dateien (kommagetrennt, z.B. app.py,utils.py): ").strip()
    files_changed = [f.strip() for f in files_raw.split(",") if f.strip()]
    problems = input("Probleme/Notizen (leer lassen wenn keine): ").strip()
    rating = int(input("Bewertung [1-5]: ").strip())
    tags_raw = input("Tags (kommagetrennt, z.B. baseline,streamlit,chart): ").strip()
    tags = [t.strip().lower() for t in tags_raw.split(",") if t.strip()]

    return {
        "phase": phase,
        "tool": tool,
        "model": model,
        "purpose": purpose,
        "prompt": prompt_text,
        "output_summary": output_summary,
        "files_changed": files_changed,
        "problems": problems,
        "rating": rating,
        "tags": tags,
    }


def add_entry(log_path: str, data: dict):
    log = load_log(log_path)
    entry = {
        "id": next_id(log["entries"]),
        "timestamp": datetime.now().isoformat(),
        **data,
    }
    log["entries"].append(entry)
    save_log(log_path, log)
    print(f"\n✅ Eintrag {entry['id']} gespeichert ({log_path})")
    print(f"   Phase:   {entry['phase']}")
    print(f"   Tool:    {entry['tool']} / {entry['model']}")
    print(f"   Zweck:   {entry['purpose'][:60]}...")
    print(f"\n💡 Git-Tipp:")
    print(f'   git add prompt_log.json && git commit -m "{entry["id"]}: {entry["purpose"][:50]}"')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add entry to prompt logbook.")
    parser.add_argument("--log", default="./prompt_log.json")
    parser.add_argument("--interactive", action="store_true")
    # Non-interactive args
    parser.add_argument("--phase", default="Meilenstein 1 – Phase 1")
    parser.add_argument("--model", default="")
    parser.add_argument("--tool", default="Cursor")
    parser.add_argument("--purpose", default="")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--output-summary", default="")
    parser.add_argument("--files", default="")
    parser.add_argument("--problems", default="")
    parser.add_argument("--rating", type=int, default=3)
    parser.add_argument("--tags", default="")
    args = parser.parse_args()

    if args.interactive:
        data = prompt_interactive()
    else:
        data = {
            "phase": args.phase,
            "model": args.model,
            "tool": args.tool,
            "purpose": args.purpose,
            "prompt": args.prompt,
            "output_summary": args.output_summary,
            "files_changed": [f.strip() for f in args.files.split(",") if f.strip()],
            "problems": args.problems,
            "rating": args.rating,
            "tags": [t.strip().lower() for t in args.tags.split(",") if t.strip()],
        }

    add_entry(args.log, data)