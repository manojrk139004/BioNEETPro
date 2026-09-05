# PROJECT_STRUCTURE.md — BioNEET Pro Directory & Codebase Tree

This document outlines the meaningful project structure for **BioNEET Pro**, excluding virtual environments (`.venv/`), bytecode caches (`__pycache__/`), temporary files, and duplicated binary archives.

```
BioNEETPro/
│
├── BioNeet-Pro.html               # Main frontend single-page application (4,922 lines, 20 distinct views)
├── app.py                         # Flask AI backend server (REST & SSE endpoints, 1,189 lines)
│
├── [AI Tutor Core Pipeline]
│   ├── adaptive_tutor.py          # Central AI tutor orchestrator & RAG prompt builder
│   ├── fallback_controller.py     # Deterministic offline NCERT-grounded doubt solver
│   ├── nlp_pipeline.py            # Biological entity extraction and multi-turn anaphora resolver
│   ├── response_validator.py      # Post-generation faithfulness and citation verifier
│   └── tutor_engine.py            # Supplementary tutor response formatter
│
├── [Knowledge Retrieval & Ingestion]
│   ├── retrieval_engine.py        # Dual-corpus hybrid TF-IDF retriever (Textbook chunks + KB)
│   ├── ncert_ingestion.py         # PyMuPDF textbook PDF ingestion and section chunking pipeline
│   ├── figure_extractor.py        # Diagrams, figures, and tables extractor from NCERT PDFs
│   └── knowledge_ingestion.py     # CSV knowledge base ingestion and normalization utility
│
├── [Curriculum & Concept Modeling]
│   ├── syllabus.py                # 32 NCERT Biology chapters registry and boundary validator
│   ├── concept_graph.py           # Biological concept dependency graph & prerequisite tracker
│   └── concept_normalizer.py      # Terminology normalizer (colloquial -> NCERT canonical terms)
│
├── [Guardrails & Security]
│   ├── content_classifier.py      # In-syllabus vs out-of-syllabus vs adversarial query classifier
│   └── policy_engine.py           # Guardrail enforcement and safety gate
│
├── [Assessment & Learner State]
│   ├── learner_model.py           # Bayesian Knowledge Tracing (BKT) & student mastery engine
│   ├── mcq_engine.py              # MCQ serving, answer grading, and chapter analytics
│   ├── mcq_bank_generator.py      # Bloom-taxonomy-tagged NCERT MCQ bank generator
│   ├── flashcard_backend.py       # Leitner / SM-2 spaced repetition flashcard scheduler
│   ├── score_predictor.py         # Predictive model for estimated NEET Biology score (0-360)
│   └── dialogue_state.py          # Multi-turn conversation state & turn tracker
│
├── [Persistence Layer]
│   └── firestore_store.py         # Authoritative persistence (Cloud Firestore + local JSON fallback)
│
├── [Data Seeding & KB Utilities]
│   ├── add_data_1.py              # Knowledge base seeding script (Chapters 3-6)
│   ├── add_data_2.py              # Knowledge base seeding script (Chapters 7-10)
│   ├── add_data_3.py              # Knowledge base seeding script (Chapters 11-14)
│   ├── add_data_4.py              # Knowledge base seeding script (Chapters 15-18)
│   ├── fix_data.py                # Knowledge base integrity normalization utility
│   ├── update.py                  # Knowledge base batch updater
│   └── update_kb.py               # Incremental concept updater
│
├── benchmark/                     # Evaluation datasets and benchmarking scripts
│   ├── adversarial_dataset.json   # Adversarial prompts for jailbreak testing
│   ├── classifier_dataset.json    # Ground-truth dataset for syllabus classification
│   ├── keyword_baseline.py        # Baseline keyword retrieval benchmark
│   ├── keyword_baseline_results.json # Benchmark baseline results
│   ├── results.json               # Benchmark performance results
│   ├── RESULTS.md                 # Benchmark summary report
│   └── run_classifier_eval.py     # Evaluation runner for query classification
│
├── data/                          # Core runtime data assets and persistent stores
│   ├── concept_dependency_graph.csv # Concept relationship DAG (prerequisites, causes)
│   ├── indexed_mcqs_cache.json    # Cached MCQ questions database (5.3 MB)
│   ├── mcq_firestore_seed.json    # Firestore seed questions for MCQ collection (4.1 MB)
│   ├── ncert_exercises_index.json # Indexed textbook end-of-chapter exercises
│   ├── ncert_figures_index.json   # Indexed diagrams and figure captions from NCERT
│   ├── ncert_tables_index.json    # Indexed data tables from NCERT textbooks
│   ├── ncert_textbook_checksums.json # MD5/SHA checksums for textbook PDFs
│   ├── ncert_textbook_index.json  # 774 indexed, section-aligned NCERT textbook chunks (1.46 MB)
│   ├── neet_knowledge_base.csv    # 335 curated concept definitions, traps, and steps
│   ├── student_learning_tracker.csv # Aggregate student progress matrix
│   ├── syllabus_registry.json     # Canonical syllabus schema and chapter hierarchy
│   ├── chat_threads/              # Local fallback chat turn history (JSON)
│   ├── dialogue_states/           # Local fallback multi-turn dialogue memory (JSON)
│   ├── flashcard_state/           # Local fallback student flashcard decks (JSON)
│   ├── kaggle_imports/            # Imported external question datasets
│   ├── score_predictions/         # Local fallback predicted score snapshots (JSON)
│   ├── student_profiles/          # Local fallback student mastery vectors (JSON)
│   └── tutor_states/              # Local fallback active session stepper states (JSON)
│
├── datasets/                      # Auxiliary dataset files
│   └── test1.csv                  # Validation dataset (1.18 MB)
│
├── scripts/                       # Maintenance, diagnostic, and acceptance test scripts
│   ├── import_kaggle_dataset.py   # Kaggle dataset parser and transformer
│   ├── test_all_15_acceptance.py  # 15-point acceptance test suite
│   ├── test_conversational_flow.py # Multi-turn conversational flow tests
│   ├── test_mcq_acceptance.py     # MCQ generation and scoring acceptance test
│   ├── test_retrieval_quick.py    # Fast smoke test for retrieval engine
│   └── debug/                     # Diagnostic scripts and inspection utilities
│       ├── check_chapter_count.py # Validates 32 chapter coverage
│       ├── check_refs.py          # Validates cross-references
│       ├── check_textbook_terms.py # Checks textbook keyword matching
│       ├── README.md              # Debug directory documentation
│       └── ...                    # Debug test routines and output captures
│
├── tests/                         # Formal test suite and verification gate
│   ├── evaluate_tutor_beast.py    # 98-case golden evaluation suite (bio + out-of-syllabus)
│   ├── evaluate_tutor_system.py   # End-to-end evaluation benchmark
│   ├── test_master_suite.py       # 8-pillar master architectural test suite (17 tests)
│   ├── test_app_endpoints.py      # Flask REST API endpoint tests (5 tests)
│   ├── test_tutor_engine.py       # Tutor engine unit tests (6 tests)
│   ├── test_guardrails.py         # Content safety and jailbreak guardrail tests
│   ├── test_firestore_sync.py     # Firestore-to-local synchronization tests
│   ├── golden_tutor.json          # Golden query-answer reference pairs
│   └── ...                        # Additional unit and regression test scripts
│
├── scripts/
│   └── verify_mcq_coverage.py     # Independent MCQ coverage+quality verifier (added 2026-09-05)
│
├── tests/  (added 2026-09-05)
│   ├── test_security_regression.py# Auth/admin/MCQ/deploy/Firestore regression (11 tests)
│   └── test_markdown_rendering.py # Live-frontend Markdown/XSS tests via node (5 tests)
│
├── Textbook/                      # NCERT Biology Reference directory
│   └── README.md                  # Documentation of 32 rationalized NCERT Biology PDFs
│
├── Configuration & Deployment:
│   ├── .env.example               # Template environment variable configuration
│   ├── serviceAccount.json.example# Template Firebase service account credentials
│   ├── firebase.json              # Firebase Firestore project configuration
│   ├── firestore.indexes.json     # Firestore composite index definitions
│   ├── firestore.rules            # Firestore security rules (role-based access control)
│   ├── .firebaserc                # Firebase project target binding
│   ├── Dockerfile                 # Backend container build specification
│   ├── requirements.txt           # Python package dependency manifest
│   └── .gitignore                 # Git ignore rules
│
└── Documentation:
    ├── README.md                  # Primary project readme and run instructions
    ├── IMPLEMENTATION_REPORT.md   # Comprehensive implementation audit report
    ├── CHAPTER_RECONCILIATION.md  # NCERT rationalization and chapter mapping audit
    ├── first_review_prep_guide.md # Review preparation guide
    ├── review_day_cheat_sheet.md  # Quick reference sheet
    ├── evaluation_report.md       # Benchmark evaluation summary
    ├── AUDIT_README.md            # Technical architecture and system audit map
    ├── PROJECT_STRUCTURE.md       # Structural codebase hierarchy and file descriptions
    ├── DEPLOYMENT_NOTES.md        # Comprehensive deployment guide and blockers analysis
    ├── AUDIT_MANIFEST.md          # Source inventory and suspicious code catalog
    └── AUDIT_FINDINGS.md          # Vulnerability, security, and deployment risk report
    ├── FINAL_VERIFICATION_REPORT.md # Hardening-sprint verification matrix (added 2026-09-05)
    ├── API_ACCESS_CONTROL.md      # Route auth classification (added 2026-09-05)
    ├── BASELINE_VERIFICATION.md   # Pre-change baseline (added 2026-09-05)
    ├── STALE_FILES_REPORT.md      # Duplicate/stale audit (added 2026-09-05)
    ├── MCQ_COVERAGE_REPORT.*      # Verified chapter coverage (added 2026-09-05)
    └── MCQ_QUALITY_REPORT.md      # MCQ validation report (added 2026-09-05)
```
