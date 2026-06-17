import json
import os
from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_LABELS, DATA_PATH, TRAIN_FILE, LABELS_FILE

_client = Groq(api_key=GROQ_API_KEY)


def load_labeled_examples() -> list[dict]:
    """
    Load the training episodes and merge them with the student's labels.

    Returns a list of dicts, each with:
      - "id"          : episode ID
      - "title"       : episode title
      - "podcast"     : podcast name
      - "description" : episode description
      - "label"       : the label from my_labels.json (may be None if not yet annotated)

    Only returns episodes where the label is a valid, non-null string.
    Episodes with null labels are silently skipped.
    """
    train_path = os.path.join(DATA_PATH, TRAIN_FILE)
    labels_path = os.path.join(DATA_PATH, LABELS_FILE)

    with open(train_path, encoding="utf-8") as f:
        episodes = {ep["id"]: ep for ep in json.load(f)}

    with open(labels_path, encoding="utf-8") as f:
        labels = {entry["id"]: entry["label"] for entry in json.load(f)}

    labeled = []
    for ep_id, ep in episodes.items():
        label = labels.get(ep_id)
        if label in VALID_LABELS:
            labeled.append({**ep, "label": label})

    return labeled


def build_few_shot_prompt(labeled_examples: list[dict], description: str) -> str:
    """
    Build a few-shot classification prompt using the student's labeled training examples.
    """
    task = (
        "You are classifying podcast episodes by their structural format.\n"
        "Assign exactly one of these four labels:\n"
        "  interview - host + guest(s); Q&A structure; guest drives content\n"
        "  solo      - one host, no guests; shares their own thoughts or experience\n"
        "  panel     - 3+ speakers as equals; no clear host-guest dynamic\n"
        "  narrative - story assembled from external sources; documentary arc\n\n"
    )

    if labeled_examples:
        examples_block = "Examples:\n\n"
        for ex in labeled_examples:
            examples_block += (
                f"Title: {ex['title']}\n"
                f"Description: {ex['description']}\n"
                f"Label: {ex['label']}\n\n"
            )
    else:
        examples_block = "No examples available — classify based on the task description alone.\n\n"

    classify_block = (
        "Now classify this episode:\n\n"
        f"Description: {description}\n\n"
        "Respond using EXACTLY this format:\n"
        "Label: <one of: interview, solo, panel, narrative>\n"
        "Reasoning: <one or two sentences explaining your choice>\n"
    )

    return task + examples_block + classify_block


def classify_episode(description: str, labeled_examples: list[dict]) -> dict:
    """
    Classify a single podcast episode description using the few-shot LLM classifier.
    """
    try:
        prompt = build_few_shot_prompt(labeled_examples, description)
        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        text = response.choices[0].message.content or ""

        label, reasoning = "unknown", ""
        for line in text.splitlines():
            if line.lower().startswith("label:"):
                label = line.split(":", 1)[1].strip().lower()
            elif line.lower().startswith("reasoning:"):
                reasoning = line.split(":", 1)[1].strip()

        # fallback: scan words for a valid label if structured format was ignored
        if label not in VALID_LABELS:
            for word in text.lower().split():
                if word.strip(".,") in VALID_LABELS:
                    label = word.strip(".,")
                    break
            else:
                label = "unknown"

        if label not in VALID_LABELS:
            label = "unknown"

        return {"label": label, "reasoning": reasoning or text.strip()}

    except Exception as e:
        return {"label": "unknown", "reasoning": f"Classification failed: {e}"}
