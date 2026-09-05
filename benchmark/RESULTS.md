# BioNEET-Pro Content Classifier Evaluation Results

Generated: 2026-09-04 22:50:26

## Main Classifier Dataset (~600 samples)

| Metric | Value |
|--------|-------|
| Accuracy | 0.8341 |
| Macro Precision | 0.8953 |
| Macro Recall | 0.7425 |
| Macro F1 | 0.8025 |
| Avg Latency (ms) | 0.74 |
| P95 Latency (ms) | 0.89 |

### Per-Class Metrics

| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|-----|---------|
| Academic | 0.8122 | 0.9707 | 0.8844 | 205 |
| Educational-Sensitive | 0.9067 | 0.7473 | 0.8193 | 91 |
| Off-Topic | 0.6531 | 0.6275 | 0.6400 | 51 |
| Inappropriate | 1.0000 | 0.6087 | 0.7568 | 23 |
| Harmful | 1.0000 | 0.7600 | 0.8636 | 25 |
| Prompt-Injection | 1.0000 | 0.7407 | 0.8511 | 27 |

### Confusion Matrix

| True \ Predicted | Academic | Educationa | Off-Topic | Inappropri | Harmful | Prompt-Inj |
|---|---|---|---|---|---|---|
| Academic | 199 | 6 | 0 | 0 | 0 | 0 |
| Educational-Sensitive | 23 | 68 | 0 | 0 | 0 | 0 |
| Off-Topic | 19 | 0 | 32 | 0 | 0 | 0 |
| Inappropriate | 1 | 0 | 8 | 14 | 0 | 0 |
| Harmful | 3 | 1 | 2 | 0 | 19 | 0 |
| Prompt-Injection | 0 | 0 | 7 | 0 | 0 | 20 |

## Adversarial Dataset (60 edge cases)

| Metric | Value |
|--------|-------|
| Accuracy | 0.7018 |
| Macro Precision | 0.5114 |
| Macro Recall | 0.4799 |
| Macro F1 | 0.4295 |
| Avg Latency (ms) | 0.73 |
| P95 Latency (ms) | 1.28 |

### Per-Class Metrics (Adversarial)

| Class | Precision | Recall | F1 | Support |
|-------|-----------|--------|-----|---------|
| Academic | 0.2353 | 1.0000 | 0.3810 | 4 |
| Educational-Sensitive | 1.0000 | 0.4211 | 0.5926 | 19 |
| Off-Topic | 0.0000 | 0.0000 | 0.0000 | 0 |
| Inappropriate | 0.0000 | 0.0000 | 0.0000 | 0 |
| Harmful | 0.8333 | 0.5000 | 0.6250 | 10 |
| Prompt-Injection | 1.0000 | 0.9583 | 0.9787 | 24 |

### Confusion Matrix (Adversarial)

| True \ Predicted | Academic | Educationa | Off-Topic | Inappropri | Harmful | Prompt-Inj |
|---|---|---|---|---|---|---|
| Academic | 4 | 0 | 0 | 0 | 0 | 0 |
| Educational-Sensitive | 10 | 8 | 1 | 0 | 0 | 0 |
| Off-Topic | 0 | 0 | 0 | 0 | 0 | 0 |
| Inappropriate | 0 | 0 | 0 | 0 | 0 | 0 |
| Harmful | 3 | 0 | 2 | 0 | 5 | 0 |
| Prompt-Injection | 0 | 0 | 0 | 0 | 1 | 23 |

## Keyword Baseline Comparison

| Metric | Our Classifier | Keyword Baseline |
|--------|----------------|------------------|
| Accuracy | 0.8341 | 0.0000 |
| Macro Precision | 0.8953 | 0.0000 |
| Macro Recall | 0.7425 | 0.0000 |
| Macro F1 | 0.8025 | 0.0000 |

---

*Note: These are real measured numbers from the current implementation. They may differ from paper claims (99.33%/93.33%). Paper results should be corrected to match reality.*
