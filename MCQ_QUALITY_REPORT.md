# MCQ Quality Report — BioNEETPro

Validator: `scripts/verify_mcq_coverage.py::validate` (mirrors backend `LocalMCQEngine.validate_mcq`; option-distinctness is case-sensitive like the backend).

Checks per record:
- question exists and > 10 chars
- exactly 4 options, none empty, all 4 distinct (case-sensitive)
- correct index is int 0..3 and correct_answer matches options[index]
- explanation exists; chapter exists
- no placeholder/garbage (lorem/placeholder/todo/xxx)
- no exact-duplicate question text (normalized whitespace+case)

- Records checked (engine pool): 6600
- Valid: 6600
- Invalid: 0
- Exact duplicates: 0
- Near-duplicate sample hits (>=0.92 similarity): 13

Method note: 778 pre-existing exact duplicates were removed (first occurrence kept; backup `data/indexed_mcqs_cache.pre_dedupe.json`), then deficient chapters were topped up with the no-LLM template/KB/family generator (`mcq_bank_generator.py --min-per-chapter 200 --kb-stems`). Final bank: 6600/6600 valid, 0 duplicates.

**Status: PASS**
