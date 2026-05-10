#!/usr/bin/env python3
"""Initialize a new prompt_log.json file."""
import json
import argparse
from datetime import datetime
from pathlib import Path

def init_log(path: str, project_name: str = "Usability Dashboard"):
    log_path = Path(path)
    if log_path.exists():
        confirm = input(f"⚠️  {path} already exists. Overwrite? [y/N]: ")
        if confirm.lower() != "y":
            print("Aborted.")
            return

    log = {
        "meta": {
            "project": project_name,
            "created": datetime.now().isoformat(),
            "version": "1.0"
        },
        "entries": []
    }

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    print(f"✅ Logbuch erstellt: {path}")
    print(f"   Projekt: {project_name}")
    print(f"   Erstellt: {log['meta']['created']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize a new prompt logbook.")
    parser.add_argument("--path", default="./prompt_log.json", help="Path to log file")
    parser.add_argument("--project", default="Usability Dashboard", help="Project name")
    args = parser.parse_args()
    init_log(args.path, args.project)