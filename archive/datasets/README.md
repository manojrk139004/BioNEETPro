# Archived Datasets

These datasets were moved from `datasets/` to `archive/datasets/` on 2026-09-04 as part of the BioNEET-Pro cleanup (Phase 1 Bug Fix 8).

## Reason for Archival

These CSV files had **zero code references** in the BioNEET-Pro codebase. They were not used by any module, endpoint, or pipeline.

- `train1.csv` (125 MB) - Large training dataset, unused
- `train.csv` (6.3 MB) - Training dataset, unused
- `validation1.csv` (2 MB) - Validation dataset, unused
- `validation.csv` (0.5 MB) - Validation dataset, unused
- `test.csv` (0.5 MB) - Test dataset, unused
- `subjects-questions.csv` (29 MB) - Mixed subjects Q&A, unused
- `blooms_taxonomy_dataset.csv` (0.8 MB) - Bloom's taxonomy labeled data, unused
- `blooms_taxonomy_questions1.csv` (5 KB) - Bloom's taxonomy questions, unused

## Retained Dataset

- `test1.csv` (1.1 MB) - **KEPT in `datasets/`** because it is actively used by `mcq_engine.py` for medical physiology/anatomy/biochemistry MCQs (lines 143-194 in mcq_engine.py).

## Restoration

If any of these datasets are needed in the future, they can be restored from this archive directory.