# RoBERTa‑Base Abstract Binary‑Classification Model  
*Fine‑tuned **roberta‑base** with [Simple Transformers](https://simpletransformers.ai/)*

---

## 📦 Repository Contents

| File | Description |
|------|-------------|
| `config.json` | 🤗 Transformers model configuration |
| `model.safetensors` | **≈ 487 MB** fine‑tuned weights |
| `model_args.json` | Simple Transformers training arguments |
| `training_args.bin` | HuggingFace `TrainingArguments` snapshot |
| `tokenizer.json`, `vocab.json` | Tokenizer and vocabulary |
| `special_tokens_map.json` | Extra special‑tokens mapping |
| `tokenizer_config.json`, `merges.txt` | Tokenizer settings & BPE merges |
| `README.md` | This instruction |

---

## 🧩 Model Overview

The model is a **roberta‑base** checkpoint fine‑tuned on ~500 research abstracts for a **binary text‑classification** task:  
detecting whether an abstract relates to **welding‑fatigue** research.

| Label | Meaning |
|-------|---------|
| `1`   | *weld‑fatigue* abstract |
| `0`   | non‑weld‑fatigue abstract |

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install simpletransformers==0.64.3
# Simple Transformers will pull in transformers, torch, scikit‑learn, pandas …
```

### 2. Inference example

```python
from simpletransformers.classification import ClassificationModel

# local model directory
model_dir = r"PATH/TO/class_abstract"    # ← replace with your path
model = ClassificationModel("roberta", model_dir, use_cuda=False)

texts = [
    "(1) Numerical simulation method of Ultrasonic Pulse-Echo Inspection, which potentially Is a powerful means for Non Destructive Evaluation of cracks and flaws of steel structures, is built …… "
    "316l(n) stainless steel plates were joined using activated-tungsten inert gas (a-tig) welding and conventional tig welding process …… ",
]

preds, logits = model.predict(texts)
print("Predicted labels:", preds)   # e.g. [1, 0]
```
