# Evaluation Spec — Pod Classifier

Complete this spec **before** writing any code for Milestone 3.

Use Plan or Ask mode to think through each blank field. When you're done,
your answers here become the blueprint for `compute_accuracy()` and
`compute_per_class_accuracy()` in `evaluate.py`.

---

## Background: What is evaluation?

After building a classifier, we need to know how well it works. Evaluation answers:
- **Overall:** What fraction of episodes did we classify correctly?
- **Per-class:** Are we better at some labels than others?

Both functions take the same inputs: a list of predicted labels and a list of
ground-truth labels, in the same order.

---

## compute_accuracy(predictions, ground_truth)

### What it does
Returns the fraction of predictions that exactly match the ground truth.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `predictions` | `list[str]` | Labels predicted by `classify_episode()`, one per episode. |
| `ground_truth` | `list[str]` | The correct labels, in the same order as `predictions`. |

### Output

| Return value | Type | Description |
|---|---|---|
| accuracy | `float` | A value between 0.0 and 1.0. |

---

### Spec fields — fill these in before writing code

**Formula:**

```
accuracy = number of correct predictions / total number of predictions

A prediction is "correct" when predictions[i] exactly matches ground_truth[i]
(same string, same position). Divide by the total number of episodes (len(ground_truth)).
```

---

**Step-by-step logic:**

```
1. If ground_truth is empty, return 0.0 (avoid division by zero).
2. Use zip(predictions, ground_truth) to pair each prediction with its ground truth.
3. Count the pairs where predicted == truth (sum of a boolean comparison).
4. Divide that count by len(ground_truth) and return the float.
```

---

**Edge case — what if both lists are empty?**

```
Return 0.0. There are no predictions to evaluate, so accuracy is undefined —
0.0 is the safest default and avoids a ZeroDivisionError.
```

---

**Worked example:**

```
predictions  = ["interview", "solo", "panel", "interview"]
ground_truth = ["interview", "solo", "solo",  "narrative"]

Index 0: interview == interview  ✓
Index 1: solo      == solo       ✓
Index 2: panel     != solo       ✗
Index 3: interview != narrative  ✗

correct = 2, total = 4
compute_accuracy() returns 2 / 4 = 0.5
```

---

## compute_per_class_accuracy(predictions, ground_truth)

### What it does
Returns accuracy broken down by each label. For each label in `VALID_LABELS`,
reports how many episodes with that ground-truth label were classified correctly.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `predictions` | `list[str]` | Labels predicted by `classify_episode()`. |
| `ground_truth` | `list[str]` | Correct labels, in the same order. |

### Output

A `dict` keyed by label. Each value is a dict with three keys:

```python
{
    "interview": {"correct": int, "total": int, "accuracy": float},
    "solo":      {"correct": int, "total": int, "accuracy": float},
    "panel":     {"correct": int, "total": int, "accuracy": float},
    "narrative": {"correct": int, "total": int, "accuracy": float},
}
```

---

### Spec fields — fill these in before writing code

**What does "correct" mean for a given class?**

```
An episode counts as correctly classified for a class when BOTH conditions hold:
  1. ground_truth[i] == that class  (the episode actually belongs to this class)
  2. predictions[i]  == that class  (the classifier also predicted this class)

For "interview": the ground truth IS interview AND the prediction IS interview.
Episodes where the ground truth is a different label are not counted for this class
at all — even if the prediction happens to be "interview".
```

---

**What does "total" mean for a given class?**

```
"total" is the number of episodes whose GROUND TRUTH label is this class —
regardless of what the classifier predicted. It is NOT the total number of
predictions overall.

For "interview": count of episodes where ground_truth[i] == "interview".
```

---

**Step-by-step logic:**

```
1. Initialize a stats dict: for each label in VALID_LABELS set correct=0, total=0.
2. Loop over zip(predictions, ground_truth) to get each (predicted, truth) pair.
3. For each pair:
     - Increment stats[truth]["total"] by 1  (this episode belongs to class truth)
     - If predicted == truth, also increment stats[truth]["correct"] by 1
4. After the loop, compute accuracy for each label:
     accuracy = correct / total  if total > 0  else 0.0
5. Return the completed stats dict.
```

---

**Edge case — what if a class has no examples in ground_truth (total == 0)?**

```
Set accuracy to 0.0. Dividing by zero is undefined, and 0.0 is the value
specified in the evaluate.py docstring stub. In this lab the test set has
5 episodes per class so total==0 shouldn't occur, but the code must handle
it safely regardless.
```

---

**Worked example:**

```
predictions  = ["interview", "interview", "solo", "panel", "panel"]
ground_truth = ["interview", "solo",      "solo", "panel", "narrative"]

Pair-by-pair:
  (interview, interview) → interview total=1, correct=1
  (interview, solo)      → solo      total=1, correct=0  (predicted wrong)
  (solo,      solo)      → solo      total=2, correct=1
  (panel,     panel)     → panel     total=1, correct=1
  (panel,     narrative) → narrative total=1, correct=0  (predicted wrong)

label       correct  total  accuracy
----------  -------  -----  --------
interview      1       1      1.0
solo           1       2      0.5
panel          1       1      1.0
narrative      0       1      0.0
```

---

## Reflection questions (discuss at the checkpoint)

1. Your overall accuracy might be decent even if one class has very low accuracy.
   Why is per-class accuracy a more informative metric than overall accuracy alone?

2. If `panel` episodes consistently get misclassified as `interview`, what does
   that tell you about your training labels or your prompt?

3. You labeled 20 training episodes and evaluated on 20 test episodes (5 per class).
   How might the evaluation results change if you had labeled 100 training episodes?
   What if you had 200 test episodes?
