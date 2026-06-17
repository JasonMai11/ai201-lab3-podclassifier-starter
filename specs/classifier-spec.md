# Classifier Spec — Pod Classifier

Complete this spec **before** writing any code for Milestone 2.

Use Plan or Ask mode to think through each blank field. When you're done,
your answers here become the blueprint for `build_few_shot_prompt()` and
`classify_episode()` in `classifier.py`.

---

## build_few_shot_prompt(labeled_examples, description)

### What it does
Constructs a prompt string for the LLM that includes the task instructions,
all labeled training examples, and the new episode description to classify.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `labeled_examples` | `list[dict]` | Each dict has `"title"`, `"description"`, `"label"` (and others). These are the examples you labeled in Milestone 1. |
| `description` | `str` | The episode description to classify. |

### Output

| Return value | Type | Description |
|---|---|---|
| prompt | `str` | A complete prompt string ready to send to the LLM. |

---

### Spec fields — fill these in before writing code

**Task instruction (what should the LLM know about the task?):**

```
You are classifying podcast episodes by their format. Classify the episode
into exactly one of these four labels:

- interview: a conversation between a host and one or more guests
- solo: a single host speaking from memory, experience, or opinion — no guests,
  no assembled external sources
- panel: multiple guests with roughly equal speaking time, often debating or
  discussing a topic together
- narrative: a story assembled from external sources — interviews, archival
  audio, reporting — with a clear narrative arc

Return only the label and your reasoning. Do not explain the taxonomy.
```

---

**How should labeled examples be formatted in the prompt?**

```
Each example should include the episode title, a brief excerpt or the full
description, and the correct label. Separate examples with a blank line or
a delimiter like "---". Include all fields that help the model see why the
label was applied — title and description are both useful; other fields
(like episode ID) are not needed.
```

---

**Example block sketch (write one concrete example):**

```
Title: {title}
Description: {description}
Label: {label}
```

---

**How should the new episode (to be classified) be presented?**

```
Present it in the same format as the labeled examples, but omit the Label
line and replace it with an instruction to classify. For example:

Title: {title}
Description: {description}
Label: ?

Then add a line like: "Classify the episode above. Return your answer in
the format below:" followed by the output format you chose.
```

---

**What output format should you request from the LLM?**

```
Request this exact format:

Respond using EXACTLY this format:
Label: <one of: interview, solo, panel, narrative>
Reasoning: <one or two sentences explaining your choice>

Tradeoffs:
- JSON is more structured but models often wrap it in markdown fences, complicating parsing.
- A bare label on its own line is fragile if the model adds a preamble sentence.
- "Label: X" / "Reasoning: Y" gives deterministic split points while staying human-readable.
  Parsing: scan lines for one starting with "label:" and one with "reasoning:", split on
  the first ":" and strip. If "Label:" is missing, fall back to scanning all words for
  a valid label string.
```

---

**Edge cases to handle in the prompt:**

```
- Empty labeled_examples: Omit the examples block entirely and add a note:
  "No examples available — classify based on the task description alone."
  The UI already warns users when no labels exist, so this is just a graceful fallback.
- Very short description: No special handling needed — the model can classify
  even a one-sentence description using the task instruction alone.
```

---

## classify_episode(description, labeled_examples)

### What it does
Classifies a single podcast episode description using the few-shot LLM classifier.
Returns a dict with a label and reasoning.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `description` | `str` | The episode description to classify. |
| `labeled_examples` | `list[dict]` | Labeled training examples from `load_labeled_examples()`. |

### Output

| Return value | Type | Description |
|---|---|---|
| result | `dict` | Must have keys `"label"` and `"reasoning"`. `"label"` must be one of `VALID_LABELS` or `"unknown"`. |

---

### Spec fields — fill these in before writing code

**Step 1 — Build the prompt:**

```
Call build_few_shot_prompt(labeled_examples, description) and store the
returned string in a variable (e.g., prompt). Pass through both arguments
exactly as received — no modification needed before calling.
```

---

**Step 2 — Send to the LLM:**

```
Call _client.chat.completions.create() with:
  - model: the model name from config (LLM_MODEL)
  - messages: a list with one dict — {"role": "user", "content": prompt}
    (system-design.md shows an optional system message too — either shape works)
  - max_tokens: a reasonable limit (e.g., 200–300) to keep responses concise

Extract the response text from:
  response.choices[0].message.content
```

---

**Step 3 — Parse the response:**

```
Iterate over response_text.splitlines(). For each line:
  - If line.lower().startswith("label:"):
      label = line.split(":", 1)[1].strip().lower()
  - If line.lower().startswith("reasoning:"):
      reasoning = line.split(":", 1)[1].strip()

Fallback: if label is still "unknown" after the line scan, do a word-level scan
of the full response text — check each word (stripped of ".,") against VALID_LABELS
and take the first match. This handles cases where the model adds a preamble or
omits the "Label:" prefix entirely.
```

---

**Step 4 — Validate the label:**

```
After parsing, check: if label not in VALID_LABELS, set label = "unknown".
This covers cases where the model returns a capitalised variant ("Solo"), a
misspelling, or something entirely unexpected. The .lower() in the parse step
handles capitalisation, so "unknown" is only needed for genuinely invalid values.
```

---

**Step 5 — Handle errors gracefully:**

```
Wrap the entire function body in try/except Exception as e and return:
  {"label": "unknown", "reasoning": f"Classification failed: {e}"}

Possible failures:
- Network/API error (Groq outage, rate limit, bad API key)
- response.choices is empty or content is None
- Completely unparseable response (no "Label:" line and no valid label word found)

Returning {"label": "unknown", ...} on any failure keeps the evaluation loop
running through all 20 episodes even if one call goes wrong.
```

---

### Return value structure

```python
{
    "label": str,      # one of VALID_LABELS, or "unknown" if invalid/error
    "reasoning": str,  # brief explanation from the LLM
}
```

---

## Notes on label quality

The classifier is only as good as your labels. If your training examples have
inconsistent or ambiguous labels, the LLM will learn the wrong pattern.

Before implementing the classifier, re-read `data/taxonomy.md` and double-check
any labels you're unsure about. Annotation quality is part of the lab.

---

## Implementation Notes

*Fill this in after implementing and testing both functions.*

**Test: what does the raw LLM response look like for one episode?**

```
Episode tested: "The Case for Four-Day Workweeks" (solo example from app.py)
Expected raw response:
  Label: solo
  Reasoning: The host speaks in first person throughout and explicitly states
  they want to share their own view — there are no guests and no Q&A structure.
```

**How did you parse the label out of the response?**

```
Iterate over response.splitlines(). Find the line that starts with "label:"
(case-insensitive), then: line.split(":", 1)[1].strip().lower()
Similarly for "reasoning:". If the "Label:" line is missing entirely, fall back
to scanning each whitespace-separated word (stripped of ".,") against VALID_LABELS.
```

**Did any episodes return `"unknown"`? If so, why?**

```
Unlikely with llama-3.3-70b-versatile given an explicit format instruction.
Would occur if the model ignores the format and responds in prose — e.g.,
"This appears to be a solo episode." — and no valid label word appears in
the fallback word scan. The try/except also catches API-level failures the
same way.
```

**One thing about the output format that surprised you:**

```
The model may occasionally add a brief preamble sentence before the "Label:" line
(e.g., "Based on the description provided:"). The line-scan approach handles this
naturally because it searches all lines rather than assuming the label is first.
```
