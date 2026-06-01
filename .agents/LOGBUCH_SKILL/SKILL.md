---
name: prompt-logbook
description: >
  Manage a structured prompt logbook (prompt_log.json) for AI-assisted development projects.
  Use this skill whenever the user wants to: log a new AI prompt entry, add a prompt to the logbook,
  export the logbook as Markdown, initialize a new logbook, filter or view entries by phase or tag,
  or update an existing entry. Trigger on phrases like "log this prompt", "add to logbook",
  "export log", "neuen Eintrag hinzufügen", "Logbuch exportieren", or any mention of
  "prompt log", "Prompt-Logbuch", or "log entry". Also trigger when the user finishes a
  Cursor/Copilot session and wants to document what was done.
---

# Prompt Logbook Manager

Manages `prompt_log.json` — the structured prompt diary for AI-assisted development (e.g., Streamlit dashboard projects). Supports adding entries, exporting to Markdown, and filtering.

---

## File Locations

| File | Purpose |
|------|---------|
| `prompt_log.json` | Source of truth – all entries |
| `PROMPT_LOGBUCH.md` | Auto-generated Markdown export (for submission) |
| `data/` | CSV datasets used in the project |

Default location: project root directory (same level as `app.py`).

---

## Entry Schema

Each entry in `prompt_log.json` follows this structure:

```json
{
  "id": "P001",
  "timestamp": "2025-05-10T14:32:00",
  "phase": "Meilenstein 1 – Phase 1",
  "model": "claude-sonnet-4-20250514",
  "tool": "Cursor",
  "purpose": "Kurze Beschreibung des Ziels",
  "prompt": "Der vollständige Prompt-Text",
  "output_summary": "Was wurde erzeugt / was hat funktioniert",
  "files_changed": ["app.py", "requirements.txt"],
  "problems": "Beschreibung von Problemen oder leer string",
  "rating": 4,
  "tags": ["baseline", "streamlit", "chart"]
}
```

### Field Reference

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | string | ✅ | Auto-increment: P001, P002, ... |
| `timestamp` | ISO8601 | ✅ | Auto-filled if not given |
| `phase` | string | ✅ | See phases below |
| `model` | string | ✅ | e.g. `claude-sonnet-4-20250514`, `gpt-4o` |
| `tool` | string | ✅ | `Cursor`, `Copilot`, `Claude.ai`, `ChatGPT` |
| `purpose` | string | ✅ | 1–2 sentences: Verwendungszweck |
| `prompt` | string | ✅ | Full prompt text |
| `output_summary` | string | ✅ | What was generated, briefly |
| `files_changed` | array | ✅ | List of modified files |
| `problems` | string | ✅ | Empty string `""` if none |
| `rating` | int 1–5 | ✅ | 1=poor, 5=excellent |
| `tags` | array | ✅ | Lowercase, relevant keywords |

### Valid Phases
- `"Meilenstein 1 – Phase 1"` — KI-Baseline-Entwurf (Streamlit MVP)
- `"Meilenstein 1 – Phase 2"` — HCI-Analyse & Usability-Probleme
- `"Meilenstein 2 – Phase 1"` — Iteratives Redesign
- `"Meilenstein 2 – Phase 2"` — Nutzertests & Evaluation

---

## Operations

### 1. Initialize a new logbook

When the user starts a new project, run:

```bash
python prompt-logbook/scripts/init_log.py --path ./prompt_log.json
```

Creates an empty `prompt_log.json`:
```json
{ "entries": [], "meta": { "project": "Usability Dashboard", "created": "<timestamp>" } }
```

### 2. Add a new entry

```bash
python prompt-logbook/scripts/add_entry.py \
  --log ./prompt_log.json \
  --interactive
```

In interactive mode, the script prompts for each field. For quick non-interactive use:

```bash
python prompt-logbook/scripts/add_entry.py \
  --log ./prompt_log.json \
  --phase "Meilenstein 1 – Phase 1" \
  --model "claude-sonnet-4-20250514" \
  --tool "Cursor" \
  --purpose "Erste Streamlit App erstellen" \
  --prompt "Erstelle eine Streamlit App mit..." \
  --output-summary "App mit 2 Charts generiert" \
  --files "app.py,requirements.txt" \
  --problems "" \
  --rating 4 \
  --tags "baseline,streamlit"
```

The `id` and `timestamp` are auto-generated.

### 3. Export to Markdown

```bash
python prompt-logbook/scripts/export_md.py \
  --log ./prompt_log.json \
  --out ./PROMPT_LOGBUCH.md
```

Generates a clean Markdown document grouped by phase — ready for submission.

### 4. Filter & view entries

```bash
# By phase
python prompt-logbook/scripts/query_log.py --log ./prompt_log.json --phase "Meilenstein 1"

# By tag
python prompt-logbook/scripts/query_log.py --log ./prompt_log.json --tag "baseline"

# Summary table (all entries)
python prompt-logbook/scripts/query_log.py --log ./prompt_log.json --summary
```

---

## Cursor Integration Reminder

Add this to **Cursor → Settings → User Rules**:

> After every code generation response, remind me: "🪵 Log this prompt! Run: python prompt-logbook/scripts/add_entry.py --log ./prompt_log.json --interactive"

---

## Git Workflow

After each log entry:

```bash
git add prompt_log.json
git commit -m "$(python -c "import json; e=json.load(open('prompt_log.json'))['entries'][-1]; print(e['id']+': '+e['purpose'])")"
```

This links every logbook entry to a git commit for full traceability.

---

## CSV Data Handling

The project expects CSV files in a `data/` folder. When a new CSV is added:

1. Run the data inspector to get a quick overview:
```bash
python prompt-logbook/scripts/inspect_data.py --folder ./data
```

2. Log the data exploration as a prompt entry (tool: `Claude.ai` or `Cursor`, tags: `["data", "exploration"]`).

3. The export script includes a **Data Sources** section in the Markdown output automatically.

---

## For more detail, see:
- `scripts/` — all executable scripts
- `assets/template_entry.json` — blank entry template to copy-paste into Cursor