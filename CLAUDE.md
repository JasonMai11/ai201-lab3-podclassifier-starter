# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add GROQ_API_KEY to .env
```

## Running

```bash
python app.py   # starts the Gradio UI at http://localhost:7860
```

There are no automated tests — correctness is validated by running the Evaluate tab in the UI, which calls the LLM 20 times against the held-out test set.

## Architecture

This is a **few-shot podcast episode classifier** with a Gradio UI. Episode descriptions are classified into `interview`, `solo`, `panel`, or `narrative` by passing labeled training examples directly in a prompt (not via fine-tuning) to `llama-3.3-70b-versatile` via the Groq API.

**Data flow:**

```
my_labels.json + train_episodes.json
        │
        ▼  load_labeled_examples()
build_few_shot_prompt(labeled_examples, description)
        │
        ▼  Groq API (single chat completion, no tool calls)
Parse response → {"label": ..., "reasoning": ...}
        │
        ▼  Gradio UI or evaluate.py
```

**Module responsibilities:**

- `config.py` — constants (`GROQ_API_KEY`, `LLM_MODEL`, `VALID_LABELS`, file paths). Import from here, never hardcode.
- `classifier.py` — `load_labeled_examples()` (complete), `build_few_shot_prompt()` (TODO), `classify_episode()` (TODO). The Groq client `_client` is module-level.
- `evaluate.py` — `run_evaluation()` and `format_evaluation_report()` are complete; `compute_accuracy()` and `compute_per_class_accuracy()` are TODO stubs.
- `app.py` — Gradio UI wiring only. No classification logic lives here.

**What's already implemented vs. what students must write:**

| Status | What |
|---|---|
| ✅ Complete | `load_labeled_examples()`, `run_evaluation()`, `format_evaluation_report()`, Gradio UI |
| ⬜ Milestone 1 | Label `data/my_labels.json` (20 training episodes) |
| ⬜ Milestone 2 | `build_few_shot_prompt()` + `classify_episode()` in `classifier.py` |
| ⬜ Milestone 3 | `compute_accuracy()` + `compute_per_class_accuracy()` in `evaluate.py` |

## Key details

- `classify_episode()` must return `{"label": str, "reasoning": str}` where `label` is one of `VALID_LABELS` or `"unknown"`.
- `load_labeled_examples()` silently skips episodes whose label is `null` or not in `VALID_LABELS` — the UI shows a warning if no valid labels exist.
- The Groq API pattern for a single completion (no tool calls, no streaming):
  ```python
  response = _client.chat.completions.create(
      model=LLM_MODEL,
      messages=[{"role": "user", "content": prompt}],
  )
  text = response.choices[0].message.content
  ```
- `specs/classifier-spec.md` and `specs/evaluation-spec.md` are meant to be filled in before coding each milestone. `specs/system-design.md` has the full architecture diagram.
- `data/taxonomy.md` defines edge cases between labels — consult it when labels are ambiguous.
