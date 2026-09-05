# PART 4 — Dataset forensic audit

Machine inventories: `dataset_inventory_data.json` (schemas + samples), `dataset_inventory_datasets.json` (row counts).
KB: 158 rows × 12 cols (`concept_id, chapter_id, chapter_name, topic, title, definition, mechanism_steps, neet_traps, sample_question, sample_options, correct_answer, explanation`). Thinnest chapters: Biotech-Applications 1, Neural 1, Digestion 1, Ecosystem 3, Human-Repro 2. Tracker: 270 rows baseline. Graph: 97 edges. MCQ cache: 157 validated items.

## Runtime wiring (proven by code grep + live runs)

| Dataset | Used in production? | Proof |
|---|---|---|
| `data/neet_knowledge_base.csv` | YES | `retrieval_engine.load_and_index` (77), `mcq_engine._build_mcq_pool` (83), `tutor_engine` sessions |
| `data/ncert_textbook_index.json` | YES | `retrieval_engine` Chunks index (111–139); live titles observed |
| `data/ncert_figures/tables/exercises_index.json` | YES (metadata) | `_attach_figures_tables`; captions in replies; PNGs not dumped |
| `data/concept_dependency_graph.csv` | YES (weakly) | `concept_graph.load_graph` (92); +0.05 score bonus |
| `data/syllabus_registry.json` | YES (mirror) | written by `syllabus._ensure_syllabus_file`; registry, not source of truth |
| `data/student_learning_tracker.csv` | YES (append-only log) | `tutor_engine.log_interaction` (154); 271 lines at baseline |
| `data/student_profiles/*.json` (43) | YES | `learner_model._get_profile_path`; live mastery verified |
| `data/dialogue_states/*.json` (3) | YES | `dialogue_state.record_turn` via `app.build_unified_answer` |
| `data/tutor_query_log.jsonl` | YES (observability) | `app.log_query`; 8 lines at baseline |
| `data/indexed_mcqs_cache.json` | YES (cache) | `mcq_engine._load_or_build_mcq_pool` (51); rebuilt live (97 KB present) |
| `datasets/test1.csv` (6150 rows) | YES | `mcq_engine.py:142` — Physiology/Anatomy/Biochemistry rows → hard MCQs (Gynaecology explicitly skipped in code) |
| `datasets/train.csv, train1.csv (182822 rows/122 MB), test.csv, validation.csv, validation1.csv, subjects-questions.csv (122519 rows), blooms_taxonomy_dataset.csv (8767 rows), blooms_taxonomy_questions1.csv` | **NO — dormant, zero code references** (grep-verified) | Dead weight; Bloom tags are assigned heuristically in `mcq_engine` (103–122), not from these files |
| `data/kaggle_imports/` (1 file) | On-demand | `scripts/import_kaggle_dataset.py:281` via `/api/tutor/import-kaggle` |
| `data/emergency_fallback_audit.log` (43 bytes, header only) | YES (sink) | Zero fallback events = fallback never fired in this deployment |

Answer-key reliability: KB `correct_answer` is an integer index into pipe-separated options; `mcq_engine.validate_mcq` enforces 4-distinct-options + index range + answer-text match on ingest. No independent key audit performed.
