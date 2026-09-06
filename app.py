

import datetime
import json
import os
import re
import sys
import time
from collections import defaultdict, deque
from pathlib import Path

import requests
from flask import Flask, Response, jsonify, request, send_file
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent

try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
    load_dotenv(BASE_DIR / ".env.local", override=True)
except ImportError:
    def load_plain_env(path):
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8-sig") as env_file:
            for raw_line in env_file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

    load_plain_env(BASE_DIR / ".env")
    load_plain_env(BASE_DIR / ".env.local")


app = Flask(__name__)
# Reject absurdly large bodies before JSON parsing (input validation).
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_CONTENT_LENGTH_BYTES", "262144"))

# NOTE on rate limiting: the limiter below is IN-MEMORY and therefore
# process-local (each gunicorn worker / container replica tracks its own
# buckets). This is appropriate for low-volume deployment. For multi-replica
# production, upgrade to a shared Redis token bucket (see DEPLOYMENT_NOTES.md).
# Authentication mode (fail CLOSED by default):
#   Production (default): REQUIRE_FIREBASE_AUTH is True — only verified Firebase
#     ID tokens are honored; caller-supplied student_id is never trusted (401/403).
#   Development (explicit opt-in ONLY): set DEV_AUTH_MODE=true (local runs and
#     the dev test-suite). An explicit REQUIRE_FIREBASE_AUTH=false is also
#     honored for legacy setups, but DEV_AUTH_MODE is the documented switch.
# A single dynamic helper (is_strict_auth(), evaluated per request) is the only
# source of truth — no duplicate config systems.
def _env_flag(name, default=False):
    return os.environ.get(name, "true" if default else "false").lower() == "true"


def is_strict_auth():
    """True unless development auth mode is explicitly enabled."""
    if _env_flag("DEV_AUTH_MODE", False):
        return False
    req = os.environ.get("REQUIRE_FIREBASE_AUTH")
    if req is not None:
        return req.lower() == "true"
    return True


REQUIRE_FIREBASE_AUTH = is_strict_auth()

DEFAULT_ALLOWED = [
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://bio-neet-pro.vercel.app",
    "https://bioneetpro.onrender.com",
    "null",
]

env_origins = os.environ.get("ALLOWED_ORIGINS", "").strip()
if env_origins:
    ALLOWED_ORIGINS = [
        origin.strip()
        for origin in env_origins.split(",")
        if origin.strip() and origin.strip() != "file://"
    ]
else:
    ALLOWED_ORIGINS = list(DEFAULT_ALLOWED)

for essential in ("https://bio-neet-pro.vercel.app", "null"):
    if essential not in ALLOWED_ORIGINS and "*" not in ALLOWED_ORIGINS:
        ALLOWED_ORIGINS.append(essential)

VERCEL_ORIGIN_REGEX = re.compile(r"^https:\/\/.*\.vercel\.app$")

CORS(
    app,
    resources={
        r"/*": {
            "origins": (
                ALLOWED_ORIGINS + [VERCEL_ORIGIN_REGEX]
                if "*" not in ALLOWED_ORIGINS
                else "*"
            ),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
            "expose_headers": ["Content-Type", "Authorization"],
        }
    },
)


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    if origin:
        if (
            origin in ALLOWED_ORIGINS
            or "*" in ALLOWED_ORIGINS
            or origin.endswith(".vercel.app")
            or origin.endswith(".onrender.com")
        ):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Accept"
    return response

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL") or os.environ.get("AI_API_BASE_URL")
if not OPENROUTER_BASE_URL:
    OPENROUTER_BASE_URL = "https://router.bynara.id/v1" if OPENROUTER_KEY and OPENROUTER_KEY.startswith("sk-nry-") else "https://openrouter.ai/api/v1"
OPENROUTER_BASE_URL = OPENROUTER_BASE_URL.rstrip("/")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "gpt-4o-mini")
AI_MAX_TOKENS = int(os.environ.get("AI_MAX_TOKENS", "550"))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX_REQUESTS", "20"))
_rate_buckets = defaultdict(deque)

SYSTEM_PROMPT = """You are BioNEET Pro AI Tutor - an expert NEET Biology teacher.
Your answers must be clear, concise, student-friendly, and aligned with NCERT.
Use bullets where useful, include NEET tips, and keep answers under 300 words unless more detail is needed.
You are context-sensitive: adapt your answer using the student's selected chapter, topic, exam goal, and recent chat history when provided."""


from adaptive_tutor import adaptive_tutor
from fallback_controller import fallback_controller
from learner_model import learner_manager
from mcq_engine import mcq_engine
from nlp_pipeline import nlp_pipeline
from syllabus import syllabus_validator
from content_classifier import content_classifier
from policy_engine import policy_engine
from response_validator import response_validator
from score_predictor import api_predict_score, get_student_prediction
import firestore_store
from retrieval_engine import retrieval_engine
from flashcard_backend import (
    create_flashcard,
    get_due_flashcards,
    review_flashcard,
    get_flashcard_stats,
    get_all_flashcards,
    delete_flashcard,
    update_flashcard,
)


def _append_chat_turn(student_id: str, user_msg: str, assistant_msg: str):
    """Persist chat thread (Firestore-first, file fallback; cap 30 turns)."""
    try:
        sid = "".join(c for c in str(student_id or "")
                      if c.isalnum() or c in ("-", "_", "@", "."))[:64] or "student_local"
        thread = firestore_store.load_doc("chat_threads", sid, default=None) or {"turns": []}
        turns = thread.get("turns") or []
        turns.append({"user": (user_msg or "")[:1500],
                      "assistant": (assistant_msg or "")[:4000]})
        thread["turns"] = turns[-30:]
        firestore_store.save_doc("chat_threads", sid, thread)
    except Exception:
        pass


def _policy_redirect_admits(query, history=None):
    """Evidence-grounded admission for Off-Topic redirects (general mechanism).

    The content classifier has imperfect recall on valid NCERT topics. When it
    says redirect but retrieval returns evidence COVERING the query's distinctive
    terms, the evidence wins and the query proceeds. Applies ONLY to "redirect"
    (scope) decisions — "block" decisions (harm, injection, abuse) are never
    overridden. True out-of-scope queries have no such evidence and still refuse.
    """
    try:
        probe = retrieval_engine.search(query=query, expanded_query=query,
                                        top_k=4)
    except Exception:
        return False
    top0 = probe[0] if probe else None
    if not top0:
        return False
    # Admit if confidence is HIGH or MEDIUM (normal path)
    if top0.get("confidence") in ("HIGH", "MEDIUM"):
        return True
    # Low-confidence but strong evidence coverage: admit for topics that
    # have genuine KB support (the syllabus validator may be imperfect).
    cov_terms = [t for t in dict.fromkeys(
        retrieval_engine._content_terms(str(query or "").lower()))
        if len(t) >= 4]
    need = min(2, len(cov_terms))
    if need >= 1 and retrieval_engine.evidence_covers(
            str(query or "").lower(), top0) >= need:
        # Check that at least half the distinctive query terms appear in the
        # full evidence (title + topic + definition + mechanism_steps +
        # sample_question), matching the evidence_covers logic exactly.
        hay = (str(top0.get("title", "")) + " "
               + str(top0.get("topic", "")) + " "
               + str(top0.get("definition", "")) + " "
               + str(top0.get("mechanism_steps", "")) + " "
               + str(top0.get("sample_question", ""))).lower()
        matched = sum(1 for t in cov_terms if t in hay)
        if matched >= (len(cov_terms) + 1) // 2:
            return True
    return False


def _apply_policy_decision(classif, query, history=None):
    """Returns (allowed: bool, decision: dict). Centralizes the policy gate so
    both chat entry points share the evidence-admission behavior."""
    from adaptive_tutor import AdaptiveBiologyTutor
    if AdaptiveBiologyTutor._is_greeting(query):
        return True, {"action": "allow", "mode": "greeting", "is_greeting": True}

    decision = policy_engine.evaluate(classif, query)
    if decision["action"] != "redirect":
        # "block" verdicts (harm, injection, abuse) are NEVER overridden.
        return decision["action"] == "allow", decision
    # Topic-less follow-up deferral (contract Rule 2): a redirect for a query
    # carrying NO explicit topic, asked WITH conversation history, is deferred
    # to the adaptive layer's focal-inheritance machinery (which resolves it
    # against server-side focal state or refuses honestly without context).
    # Cold topic-less queries still redirect; true OOS still refuses downstream.
    try:
        if (history
                and not nlp_pipeline._has_explicit_topic(str(query or ""))):
            return True, dict(decision, action="allow",
                              deferred_followup=True,
                              tone_flag=decision.get("tone_flag"))
    except Exception:
        pass
    if _policy_redirect_admits(query, history):
        decision = dict(decision, action="allow",
                        admitted_by_evidence=True,
                        tone_flag=decision.get("tone_flag"))
        return True, decision
    return False, decision


def demo_ai_answer(message, student_id="student_local", history=None, context=None):
    clean = (message or "").strip()
    if not clean:
        return (
            "👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n"
            "*\"Please ask any NCERT Biology doubt or request practice MCQs!\"*"
        )

    from adaptive_tutor import AdaptiveBiologyTutor
    if AdaptiveBiologyTutor._is_greeting(clean):
        res = adaptive_tutor.generate_tutoring_response("Hi", student_id=student_id)
        return res.get("reply", "")

    # 0. Content Classification & Policy Guardrail Gate
    # (evidence-grounded admission for imperfect Off-Topic redirects)
    classif = content_classifier.classify(clean, history=history)
    allowed, decision = _apply_policy_decision(classif, clean, history)
    if not allowed:
        return decision.get("reply") or "I cannot fulfill this request."

    # 1. NLP Intent Detection: Check if student is requesting on-demand MCQs
    nlp_res = nlp_pipeline.process_query(clean, history or [], student_id=student_id)
    if nlp_res["intent"] == "mcq_request":
        mcq_data = mcq_engine.generate_mcqs(clean, student_id=student_id)
        raw_reply = mcq_engine.format_mcqs_for_chat(mcq_data)
        val = response_validator.validate_response(raw_reply, student_id=student_id)
        return val["sanitized_response"]

    # 2. ONE BRAIN: single unified pipeline (RAG generator + template fallback inside).
    # /chat, /ask and /api/tutor/answer all end up here — no divergent logic.
    out = build_unified_answer(clean, student_id, history, context, include_steps=False)

    # 3. Controlled Emergency Fallback (only if unified pipeline is LOW and flag enabled)
    if out.get("confidence") == "LOW" and fallback_controller.should_trigger_fallback("LOW"):
        fb = fallback_controller.execute_fallback(clean, "local_low_confidence", history)
        if fb:
            val = response_validator.validate_response(fb["reply"], student_id=student_id)
            return val["sanitized_response"]

    val = response_validator.validate_response(out.get("reply", ""), concept_id=out.get("concept_id"), student_id=student_id)
    return val["sanitized_response"]


def client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    return forwarded.split(",")[0].strip() or request.remote_addr or "unknown"


def rate_limited():
    now = time.time()
    bucket = _rate_buckets[client_ip()]
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_MAX:
        return True
    bucket.append(now)
    return False


def payload():
    return request.get_json(silent=True) if request.is_json else {}


def candidate_models():
    models = [OPENROUTER_MODEL] if OPENROUTER_MODEL and OPENROUTER_MODEL != "agnes-2.0-flash" else []
    if OPENROUTER_KEY and OPENROUTER_KEY.startswith("sk-nry-"):
        models.extend(["agnes-2.5-flash"])
    else:
        models.extend(["google/gemini-2.0-flash-lite:free", "meta-llama/llama-3.3-70b-instruct:free"])
    return list(dict.fromkeys([m for m in models if m and m != "minimax-m3-free" and m != "agnes-2.0-flash"]))


try:
    from tutor_engine import tutor_engine
except Exception as e:
    print(f"Warning: tutor_engine could not be loaded: {e}")
    tutor_engine = None


@app.get("/")
def serve_index():
    """Serve the BioNEET Pro web frontend directly on root URL."""
    for name in ("index.html", "BioNeet-Pro.html"):
        index_file = BASE_DIR / name
        if index_file.exists():
            return send_file(index_file)
    return health()


@app.get("/health")
def health():
    ds_count = len(tutor_engine.df) if tutor_engine else 0
    return jsonify(
        {
            "status": "ok",
            "service": "BioNEET Pro AI & Algorithmic Backend",
            "ai_configured": bool(OPENROUTER_KEY),
            "demo_mode": not bool(OPENROUTER_KEY),
            "local_algorithm_active": tutor_engine is not None,
            "algorithm": "TF-IDF Vectorizer + Cosine Similarity & Bayesian Knowledge Tracing",
            "dataset_file": "neet_knowledge_base.csv",
            "dataset_records": ds_count,
            "model": OPENROUTER_MODEL if OPENROUTER_KEY else "local-algorithmic-vsm",
            "provider": OPENROUTER_BASE_URL.split("/")[2] if (OPENROUTER_KEY and "://" in OPENROUTER_BASE_URL) else "local-laptop-engine",
        }
    )


@app.get("/api/health")
def api_health():
    """Lightweight liveness probe (no AI calls)."""
    return health()


@app.get("/api/ready")
def api_ready():
    """Readiness probe: engine + MCQ pool loaded?"""
    engine_ok = tutor_engine is not None
    try:
        pool_n = len(mcq_engine.mcq_pool)
    except Exception:
        pool_n = 0
    ready = bool(engine_ok and pool_n >= 100)
    return jsonify({"ready": ready, "engine": engine_ok,
                    "mcq_pool": pool_n}), (200 if ready else 503)


def ai_reply():
    try:
        if rate_limited():
            return jsonify({"error": "Too many requests. Wait a minute and try again."}), 429

        data = payload() or {}
        message = str(data.get("message") or data.get("question") or "").strip()
        if not message:
            return jsonify({"error": "No message provided."}), 400
        if len(message) > 3000:
            return jsonify({"error": "Message is too long. Keep it under 3000 characters."}), 400

        # BioNEETPro Core Rule: LOCAL-FIRST execution by default
        force_external = data.get("mode") == "external" or data.get("force_api") is True
        if not force_external:
            student_id = auth_student_id(data) or "student_local"
            history = data.get("history", [])
            context = data.get("context", {})
            out = build_unified_answer(message, student_id=student_id, history=history, context=context, include_steps=False)
            reply_text = out.get("reply", "")
            _append_chat_turn(student_id, message, reply_text)
            resp = {
                "reply": reply_text,
                "answer": reply_text,
                "mode": out.get("mode", "local_adaptive"),
                "source_mode": out.get("source_mode", "local_ncert"),
                "fallback_tier": out.get("fallback_tier", "tier_1"),
                "status": out.get("status", "success"),
                "confidence": out.get("confidence", "HIGH"),
            }
            if out.get("model_used"):
                resp["model_used"] = out.get("model_used")
            if out.get("follow_up_chips"):
                resp["follow_up_chips"] = out.get("follow_up_chips")
            # Interactive chat MCQs: attach the just-generated structured batch
            # ONLY when the current message actually requested MCQs (never a
            # stale batch from an earlier turn).
            try:
                is_mcq_req = (nlp_pipeline.process_query(
                    message, [], student_id=student_id).get("intent")
                    == "mcq_request")
            except Exception:
                is_mcq_req = False
            try:
                batch = (mcq_engine.get_recent_mcqs(student_id=student_id)
                         if is_mcq_req else [])
                if batch:
                    resp["mcqs"] = [
                        {"question": q.get("question", ""),
                         "options": q.get("options", []),
                         "correct_index": q.get("correct_index", 0),
                         "chapter": q.get("chapter", ""),
                         "topic": q.get("topic", ""),
                         "concept_id": q.get("concept_id", "BIO-GEN"),
                         "difficulty": q.get("difficulty", "medium"),
                         "cognitive_level": q.get("cognitive_level", "BT2"),
                         "explanation": q.get("explanation", "")}
                        for q in batch[:10]]
                    resp["mcq_count"] = len(resp["mcqs"])
            except Exception:
                pass
            return jsonify(resp)

        history = data.get("history", [])
        context = data.get("context", {})
        safe_history = []
        if isinstance(history, list):
            for item in history[-8:]:
                if not isinstance(item, dict) or not item.get("content"):
                    continue
                role = item.get("role") if item.get("role") in {"user", "assistant"} else "user"
                safe_history.append({"role": role, "content": str(item.get("content"))[:1500]})

        context_lines = []
        if isinstance(context, dict):
            for label, key in [("Selected chapter", "chapter"), ("Selected topic", "topic"), ("Student goal", "goal"), ("Mode", "mode")]:
                value = str(context.get(key) or "").strip()
                if value:
                    context_lines.append(f"{label}: {value[:160]}")
        context_prompt = "\n".join(context_lines)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context_prompt:
            messages.append({"role": "system", "content": "Student context for this answer:\n" + context_prompt})
        messages.extend([*safe_history, {"role": "user", "content": message}])
        
        last_error = ""
        for model in candidate_models():
            try:
                response = requests.post(
                    f"{OPENROUTER_BASE_URL}/chat/completions",
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENROUTER_KEY}"},
                    json={"model": model, "messages": messages, "max_tokens": AI_MAX_TOKENS, "temperature": 0.5},
                    timeout=8,
                )
                response.raise_for_status()
                body = response.json()
                return jsonify({"reply": body["choices"][0]["message"]["content"], "model": model})
            except requests.Timeout:
                last_error = f"{model}: request timed out"
                print(f"AI provider timeout on {model}")
            except requests.HTTPError as exc:
                details = exc.response.text[:500] if exc.response is not None else str(exc)
                last_error = f"{model}: {details}"
                print(f"AI provider error on {model}: {details}")

        return jsonify({"error": f"AI provider error: {last_error}"}), 502
    except requests.Timeout:
        return jsonify({"error": "Request timed out. Try again."}), 504
    except requests.ConnectionError:
        return jsonify({"error": "AI provider unreachable. The local tutor remains available via the default path."}), 502
    except requests.RequestException as exc:
        return jsonify({"error": f"AI provider request failed: {str(exc)[:200]}"}), 502
    except Exception as exc:
        print(f"Chat error: {exc}")
        return jsonify({"error": "Unexpected server error."}), 500


@app.post("/chat")
def chat():
    return ai_reply()


@app.post("/ask")
def ask():
    response = ai_reply()
    if isinstance(response, tuple):
        return response
    data = response.get_json(silent=True) or {}
    if "reply" in data:
        return jsonify({"answer": data["reply"]})
    return response


# ==========================================
# Local Algorithmic Tutor Endpoints
# ==========================================

@app.post("/api/tutor/query")
def tutor_query():
    """
    Step 1 of Local Algorithmic Tutor:
    Takes natural language question, calculates TF-IDF Cosine Similarity against local CSV,
    and returns matched concept details + Step 1 content.
    """
    if not tutor_engine:
        return jsonify({"error": "Local tutor engine not initialized."}), 500

    data = payload() or {}
    query = str(data.get("query") or data.get("question") or "").strip()[:3000]
    student_id = str(data.get("student_id") or "student_local").strip()[:64] or "student_local"
    history = data.get("history", [])
    if not isinstance(history, list):
        history = []

    if not query:
        return jsonify({"error": "Please provide a query."}), 400

    result = tutor_engine.start_query_session(query=query, student_id=student_id, history=history)
    return jsonify(result)


@app.post("/api/tutor/step")
def tutor_step():
    """
    Step Navigation (Steps 1 to 4):
    Allows student to step-by-step advance through:
    1: Definition -> 2: Mechanism -> 3: NEET Traps -> 4: Diagnostic Micro-Check
    """
    if not tutor_engine:
        return jsonify({"error": "Local tutor engine not initialized."}), 500

    data = payload() or {}
    session_id = str(data.get("session_id") or "").strip()[:64]
    try:
        step_number = int(data.get("step_number") or 1)
    except (TypeError, ValueError):
        return jsonify({"error": "step_number must be an integer 1-4."}), 400

    if not session_id:
        return jsonify({"error": "session_id is required."}), 400
    if step_number < 1 or step_number > 4:
        return jsonify({"error": "step_number must be between 1 and 4."}), 400

    result = tutor_engine.get_step_content(session_id=session_id, step_number=step_number)
    return jsonify(result)


@app.post("/api/tutor/verify")
def tutor_verify():
    """
    Step 4 Quiz Verification & Bayesian Knowledge Tracing (BKT) Update:
    Evaluates student answer, updates mastery score, and writes to data/student_learning_tracker.csv.
    """
    if not tutor_engine:
        return jsonify({"error": "Local tutor engine not initialized."}), 500

    data = payload() or {}
    session_id = str(data.get("session_id") or "").strip()[:64]
    selected_index = data.get("selected_index")

    if not session_id or selected_index is None:
        return jsonify({"error": "session_id and selected_index are required."}), 400
    try:
        selected_index = int(selected_index)
    except (TypeError, ValueError):
        return jsonify({"error": "selected_index must be an integer."}), 400
    if selected_index < 0 or selected_index > 3:
        return jsonify({"error": "selected_index must be between 0 and 3."}), 400

    result = tutor_engine.verify_quiz(session_id=session_id, selected_index=selected_index)
    return jsonify(result)


@app.get("/api/tutor/tracker")
def tutor_tracker():
    """
    Audit / Evaluator Endpoint (ADMIN ONLY):
    Returns the recent entries logged into data/student_learning_tracker.csv.
    """
    _, err = require_admin()
    if err:
        return err
    if not tutor_engine:
        return jsonify({"error": "Local tutor engine not initialized."}), 500

    try:
        limit = int(request.args.get("limit", 25))
    except (TypeError, ValueError):
        limit = 25
    limit = max(1, min(100, limit))
    return jsonify(tutor_engine.get_tracker_summary(limit=limit))


@app.get("/api/tutor/dataset-info")
def tutor_dataset_info():
    """
    Returns metadata about the local knowledge base CSV dataset.
    """
    if not tutor_engine:
        return jsonify({"error": "Local tutor engine not initialized."}), 500

    df = tutor_engine.df
    return jsonify(
        {
            "filename": "neet_knowledge_base.csv",
            "total_records": len(df),
            "columns": list(df.columns),
            "chapters_covered": df["chapter_name"].unique().tolist(),
            "algorithm": "TF-IDF Vector Space Model (Unigram + Bigram) with Cosine Similarity",
            "storage_path": str(tutor_engine.kb_path),
            "vocabulary_size": len(tutor_engine.feature_names)
        }
    )


@app.post("/api/tutor/import-kaggle")
def tutor_import_kaggle():
    """
    ADMIN ONLY: Scans data/kaggle_imports/ or imports new Kaggle dataset CSVs,
    merges them into neet_knowledge_base.csv, and immediately re-trains TF-IDF vector space model.
    """
    _, err = require_admin()
    if err:
        return err
    if not tutor_engine:
        return jsonify({"error": "Local tutor engine not initialized."}), 500

    try:
        from scripts.import_kaggle_dataset import scan_and_import_all
        from retrieval_engine import retrieval_engine
        added = scan_and_import_all()
        retrieval_engine.load_and_index()
        return jsonify({
            "status": "success",
            "newly_added": added,
            "total_records": len(retrieval_engine.df),
            "vocabulary_size": len(retrieval_engine.feature_names),
            "message": f"Successfully loaded {added} new concepts from Kaggle into local engine!"
        })
    except Exception:
        return jsonify({"error": "Dataset import failed."}), 500



# ==========================================
# New Adaptive MCQ & Learner Profile Endpoints
# ==========================================

@app.post("/api/mcq/generate")
def api_mcq_generate():
    """
    On-Demand MCQ Generation Endpoint:
    Generates requested quantity of MCQs (e.g., 5, 20) with difficulty override or adaptive targeting.
    """
    data = payload() or {}
    req_text = str(data.get("request_text") or data.get("query") or "Give me 5 MCQs").strip()
    # Read-only personalization: verified/header identity when present,
    # otherwise anonymous adaptive (never trusts a spoofed id for writes).
    student_id = auth_student_id(data) or "student_local"
    result = mcq_engine.generate_mcqs(req_text, student_id=student_id)
    return jsonify(result)


@app.post("/api/mcq/submit")
def api_mcq_submit():
    """
    STUDENT (authenticated write): evaluates MCQ attempt, updates the CALLER's
    BKT mastery. Identity comes from resolve_identity() — a client student_id
    that mismatches the authenticated user is rejected (403); unauthenticated
    callers are rejected in strict mode (401).
    """
    data = payload() or {}
    student_id, err = resolve_identity(data)
    if err:
        return err
    store_err = require_store()
    if store_err:
        return store_err
    concept_id = str(data.get("concept_id") or "BIO-GEN").strip()[:64] or "BIO-GEN"
    chapter_id = str(data.get("chapter_id") or data.get("chapter") or "general").strip()[:64] or "general"
    topic_id = str(data.get("topic_id") or data.get("topic") or "Unknown").strip()[:128] or "Unknown"
    raw_corr = data.get("is_correct")
    is_correct = (raw_corr is True) or (str(raw_corr).strip().lower() in ("true", "1", "yes"))
    difficulty = str(data.get("difficulty") or "medium").strip()[:16] or "medium"
    cognitive_level = str(data.get("cognitive_level") or "BT2").strip()[:16] or "BT2"
    try:
        time_taken = float(data.get("time_taken") or 0.0)
    except (TypeError, ValueError):
        time_taken = 0.0
    time_taken = max(0.0, min(3600.0, time_taken))
    try:
        normalized_cid = syllabus_validator.normalize_chapter_id(chapter_id)
        if normalized_cid:
            chapter_id = normalized_cid
    except Exception:
        pass

    update_res = learner_manager.record_attempt(
        student_id=student_id,
        concept_id=concept_id,
        chapter_id=chapter_id,
        is_correct=is_correct,
        difficulty=difficulty,
        cognitive_level=cognitive_level,
        response_time_sec=time_taken,
        topic_id=topic_id,
    )
    return jsonify(update_res)


@app.post("/api/mcq/submit-batch")
def api_mcq_submit_batch():
    """Record a whole finished test in one roundtrip (drives mastery →
    coach tips + score predictor). Body: {student_id, attempts: [{
    concept_id, chapter_id, topic_id, is_correct, difficulty,
    cognitive_level, time_taken}]}. STUDENT (authenticated write): identity
    from resolve_identity() — cross-user submission is rejected."""
    data = payload() or {}
    student_id, err = resolve_identity(data)
    if err:
        return err
    store_err = require_store()
    if store_err:
        return store_err
    attempts = data.get("attempts") or []
    recorded = 0
    for a in attempts[:100]:
        if not isinstance(a, dict):
            continue
        raw = a.get("is_correct")
        try:
            learner_manager.record_attempt(
                student_id=student_id,
                concept_id=str(a.get("concept_id") or "BIO-GEN")[:64],
                chapter_id=str(a.get("chapter_id") or a.get("chapter") or "general")[:64],
                is_correct=(raw is True) or (str(raw).strip().lower() in ("true", "1", "yes")),
                difficulty=str(a.get("difficulty") or "medium")[:16],
                cognitive_level=str(a.get("cognitive_level") or "BT2")[:16],
                response_time_sec=max(0.0, min(3600.0, float(a.get("time_taken") or 0.0))),
                topic_id=str(a.get("topic_id") or a.get("topic") or "Unknown")[:128],
            )
            recorded += 1
        except Exception:
            continue
    return jsonify({"student_id": student_id, "recorded": recorded})


@app.get("/api/learner/profile")
def api_learner_profile():
    """
    Returns complete student learning trajectory, concept mastery scores, and repeated mistakes.
    AUTHENTICATED: a student may read only their OWN profile; admins may read any.
    Pass ?student_id=<own id>; a mismatch yields 403.
    """
    caller, err = require_auth_student()
    if err:
        return err
    requested = _sanitize_sid(request.args.get("student_id") or caller)
    hid, hclaims, hkind = _header_identity()
    if hkind == "invalid":
        # Presented credential failed verification: deny rather than serve
        # another student's data.
        return jsonify({"error": "Authentication required. Sign in and retry."}), 401
    if hkind in ("verified", "dev-raw"):
        # Header identity is the trustworthy caller id: the query id must
        # match it unless the caller is an admin.
        if requested != hid and not is_admin_request(hid, hclaims):
            return jsonify({"error": "You may only access your own learner profile."}), 403
        caller = hid
    elif is_strict_auth():
        return jsonify({"error": "Authentication required. Sign in and retry."}), 401
    else:
        # No header (local-dev, no credentials): identity == query id.
        caller = requested
    profile = learner_manager.get_or_create_profile(caller)
    return jsonify(profile)


@app.get("/api/learner/review-due")
def api_review_due():
    """FSRS-lite due reviews for spaced repetition UI."""
    import dialogue_state as _ds
    student_id = auth_student_id()
    return jsonify({"student_id": student_id, "due": _ds.due_reviews(student_id)[:20]})


@app.get("/api/syllabus")
def api_syllabus():
    """
    Returns the rationalized NCERT NEET Biology syllabus hierarchy
    (33 canonical chapters, c01-c10 + c13-c35 sparse numbering).
    """
    return jsonify(syllabus_validator.syllabus)


@app.get("/api/score/predict")
def api_score_predict():
    """
    Predict NEET score based on student's biology mastery profile.
    Optional query params: physics_score, chemistry_score (0-180 each).
    """
    student_id = auth_student_id()
    physics_score = request.args.get("physics_score", type=int)
    chemistry_score = request.args.get("chemistry_score", type=int)
    
    if physics_score is not None:
        physics_score = max(0, min(180, physics_score))
    if chemistry_score is not None:
        chemistry_score = max(0, min(180, chemistry_score))
    
    result = api_predict_score(student_id, physics_score, chemistry_score)
    return jsonify(result)


@app.get("/api/score/history")
def api_score_history():
    """Get historical score predictions for a student."""
    student_id = auth_student_id()
    from score_predictor import get_prediction_history
    history = get_prediction_history(student_id)
    return jsonify({"student_id": student_id, "predictions": history})


# ==========================================
# Coach Tip (Phase 1 / A4) — purpose-built endpoint
# ==========================================

@app.get("/api/coach/tip")
def api_coach_tip():
    """Short encouraging coaching tip from real weak-chapter data.

    Never returns raw retrieval-fallback/error text: with no data we return
    a static onboarding tip; unexpected errors also fall back to static text.
    """
    student_id = auth_student_id()
    try:
        weak = []
        try:
            weak = learner_manager.get_weak_topics(student_id) or []
        except Exception:
            weak = []
        if weak:
            w0 = weak[0]
            chap = w0.get("chapter_id") or w0.get("chapter") or "your weakest chapter"
            try:
                cname = syllabus_validator.get_canonical_chapter_name(chap) or chap
            except Exception:
                cname = chap
            tip = (f"Your focus win today: 25 mins on {cname} (your lowest-mastery area), "
                   f"then 10 MCQs just on that chapter. Small reps, big NEET gains!")
            return jsonify({"student_id": student_id, "tip": tip, "weak_chapter": cname,
                            "personalized": True})
        # No weak-topic data yet — honest onboarding tip, never an error string.
        return jsonify({"student_id": student_id,
                        "tip": ("Welcome! Take your first chapter test and I'll pinpoint "
                                "your weakest area with a daily focus plan."),
                        "weak_chapter": None, "personalized": False})
    except Exception:
        return jsonify({"student_id": student_id,
                        "tip": ("Steady prep beats cramming — pick one NCERT chapter today, "
                                "revise its diagrams, then test yourself with 10 MCQs."),
                        "weak_chapter": None, "personalized": False})


# ==========================================
# Textbook / NCERT PDF delivery (Phase 5)
# ==========================================

def _build_chapter_pdf_map():
    """Canonical chapter_id -> Textbook PDF filename.

    Class XI index CH n -> kebo1{00+n:02d}.pdf, Class XII -> lebo1{...}.pdf.
    Unmatched canonical chapters (e.g. c16 Digestion, absent from the
    rationalized index) map to None — the route returns an honest 404.
    """
    mapping = {}
    try:
        with open(BASE_DIR / "data" / "ncert_textbook_index.json", "r", encoding="utf-8") as f:
            idx = json.load(f)
    except Exception:
        return mapping
    title_to_file = {}
    for ch in idx:
        cls = str(ch.get("class", ""))
        try:
            num = int(ch.get("chapter_number", 0))
        except Exception:
            continue
        title = str(ch.get("chapter_title", "")).strip().lower()
        if "class xi" in cls.lower():
            fn = f"kebo1{num:02d}.pdf"
        elif "class xii" in cls.lower():
            fn = f"lebo1{num:02d}.pdf"
        else:
            continue
        title_to_file[title] = fn

    def norm(s):
        return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()

    norm_index = {norm(t): fn for t, fn in title_to_file.items()}
    try:
        chapters = []
        try:
            sj = syllabus_validator.syllabus
            for cls in ("class_11", "class_12"):
                for unit, ud in (sj.get(cls) or {}).items():
                    for cid, ch in (ud.get("chapters") or {}).items():
                        chapters.append((cid, ch.get("chapter_name", "")))
        except Exception:
            chapters = []
        for cid, cname in chapters:
            n = norm(cname)
            hit = norm_index.get(n)
            if not hit:
                # fuzzy: token-overlap match
                nt = set(n.split())
                best, best_fn = 0.0, None
                for it, fn in norm_index.items():
                    itset = set(it.split())
                    if not nt or not itset:
                        continue
                    ov = len(nt & itset) / max(1, len(nt | itset))
                    if ov > best:
                        best, best_fn = ov, fn
                if best >= 0.5:
                    hit = best_fn
            if hit and (BASE_DIR / "Textbook" / hit).exists():
                mapping[cid.lower()] = hit
    except Exception:
        pass
    return mapping


CHAPTER_PDF_MAP = _build_chapter_pdf_map()


@app.get("/api/textbook/chapters")
def api_textbook_chapters():
    """Canonical chapters with subtopics + PDF availability."""
    try:
        with open(BASE_DIR / "data" / "ncert_textbook_index.json", "r", encoding="utf-8") as f:
            idx = json.load(f)
    except Exception:
        idx = []
    by_title = {}
    for ch in idx:
        by_title.setdefault(str(ch.get("chapter_title", "")).strip().lower(), []).append(ch)
    out = []
    try:
        sj = syllabus_validator.syllabus
        for cls in ("class_11", "class_12"):
            for unit, ud in (sj.get(cls) or {}).items():
                for cid, ch in (ud.get("chapters") or {}).items():
                    cname = ch.get("chapter_name", "")
                    # subtopics: distinct section strings from the index for this chapter
                    # (punctuation-insensitive match: "Cell: X" == "Cell : X").
                    subs = []
                    nc = re.sub(r"[^a-z0-9]+", " ", cname.strip().lower()).strip()
                    for t, chunks in by_title.items():
                        nt = re.sub(r"[^a-z0-9]+", " ", t.strip().lower()).strip()
                        if nc and nt and (nc in nt or nt in nc):
                            for c in chunks:
                                s = str(c.get("section", "")).strip().split("\n")[0][:120]
                                if s and s not in subs:
                                    subs.append(s)
                            break
                    pdf = CHAPTER_PDF_MAP.get(cid.lower())
                    out.append({"chapter_id": cid, "chapter_name": cname,
                                "class": cls, "subtopics": subs[:12],
                                "has_pdf": bool(pdf),
                                "pdf_url": f"/api/textbook/pdf/{cid}" if pdf else None})
    except Exception as e:
        return jsonify({"error": str(e)[:200]}), 500
    return jsonify({"chapters": out, "count": len(out)})


@app.get("/api/textbook/pdf/<chapter_id>")
def api_textbook_pdf(chapter_id: str):
    """Serve the actual NCERT PDF for a canonical chapter."""
    cid = (chapter_id or "").strip().lower()
    try:
        cid = syllabus_validator.normalize_chapter_id(cid) or cid
    except Exception:
        pass
    fn = CHAPTER_PDF_MAP.get(cid.lower())
    if not fn:
        return jsonify({"error": f"No NCERT PDF mapped for chapter '{chapter_id}'.",
                        "chapter_id": chapter_id}), 404
    path = BASE_DIR / "Textbook" / fn
    if not path.exists():
        return jsonify({"error": "PDF file missing on server.", "file": fn}), 404
    return send_file(path, mimetype="application/pdf", as_attachment=False,
                     download_name=fn)


# ==========================================
# Flashcard API (Leitner System)
# ==========================================

@app.post("/api/flashcards")
def api_flashcard_create():
    """Create a new flashcard (STUDENT authenticated write)."""
    data = payload() or {}
    student_id, err = resolve_identity(data)
    if err:
        return err
    store_err = require_store()
    if store_err:
        return store_err
    
    front = str(data.get("front") or "").strip()
    back = str(data.get("back") or "").strip()
    concept_id = str(data.get("concept_id") or "").strip()
    chapter_id = str(data.get("chapter_id") or "").strip()
    tags = data.get("tags", [])
    
    if not front or not back:
        return jsonify({"error": "front and back are required"}), 400
    
    card = create_flashcard(student_id, front, back, concept_id, chapter_id, tags)
    return jsonify(card)


@app.get("/api/flashcards/due")
def api_flashcards_due():
    """Get flashcards due for review."""
    student_id = auth_student_id()
    limit = request.args.get("limit", default=50, type=int)
    limit = max(1, min(100, limit))
    
    due = get_due_flashcards(student_id, limit)
    return jsonify({"student_id": student_id, "due": due, "count": len(due)})


@app.post("/api/flashcards/review")
def api_flashcard_review():
    """Review a flashcard (Leitner algorithm; STUDENT authenticated write)."""
    data = payload() or {}
    student_id, err = resolve_identity(data)
    if err:
        return err
    store_err = require_store()
    if store_err:
        return store_err
    
    card_id = str(data.get("card_id") or "").strip()
    is_correct = data.get("is_correct")
    
    if not card_id:
        return jsonify({"error": "card_id is required"}), 400
    if is_correct is None:
        return jsonify({"error": "is_correct (boolean) is required"}), 400
    
    is_correct = bool(is_correct)
    result = review_flashcard(student_id, card_id, is_correct)
    
    if "error" in result:
        return jsonify(result), 404
    return jsonify(result)


@app.get("/api/flashcards/stats")
def api_flashcard_stats():
    """Get flashcard statistics."""
    student_id = auth_student_id()
    stats = get_flashcard_stats(student_id)
    return jsonify(stats)


@app.get("/api/flashcards")
def api_flashcards_list():
    """List all flashcards for a student."""
    student_id = auth_student_id()
    cards = get_all_flashcards(student_id)
    return jsonify({"student_id": student_id, "cards": cards, "count": len(cards)})


@app.get("/api/mcqs/seed")
def api_mcqs_seed():
    """Paginated full-bank seed for the admin bulk-sync button (frontend schema).

    Query: ?offset=0&limit=100. Returns {total, offset, limit, mcqs:[{q, opts,
    correct, chapter, diff, expl}]}. Lets the admin panel upload the whole
    no-cost bank (1347) into the Firestore `mcqs` collection with dedupe.
    """
    try:
        offset = max(0, int(request.args.get("offset", 0)))
    except Exception:
        offset = 0
    try:
        limit = max(1, min(200, int(request.args.get("limit", 100))))
    except Exception:
        limit = 100
    try:
        with open(BASE_DIR / "data" / "mcq_firestore_seed.json", "r", encoding="utf-8") as f:
            seed = json.load(f)
    except Exception:
        return jsonify({"total": 0, "offset": offset, "limit": limit, "mcqs": []})
    out = []
    for d in seed[offset:offset + limit]:
        opts = d.get("options") or []
        try:
            ci = int(d.get("correct", 0))
        except Exception:
            ci = 0
        if not isinstance(opts, list) or len(opts) != 4 or not (0 <= ci < 4):
            continue
        out.append({"q": d.get("question", ""), "opts": opts, "correct": ci,
                    "chapter": d.get("chapter", "General Biology"),
                    "diff": str(d.get("difficulty", "Medium")).title(),
                    "expl": d.get("explanation", ""),
                    "source_section": d.get("source_section", ""),
                    "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat()})
    return jsonify({"total": len(seed), "offset": offset, "limit": limit, "mcqs": out})


@app.post("/api/mcqs/generate")
def api_mcqs_generate():
    """ADMIN ONLY: no-cost MCQ generation for one chapter (Phase 2).

    Body: {chapter_id, count}. Runs mcq_bank_generator for that chapter,
    reloads the engine pool, returns accepted/rejected numbers.
    """
    _, err = require_admin()
    if err:
        return err
    data = payload() or {}
    chapter = str(data.get("chapter_id") or data.get("chapter") or "").strip()
    try:
        count = max(1, min(50, int(data.get("count", 10))))
    except Exception:
        count = 10
    if not chapter:
        return jsonify({"error": "chapter_id is required"}), 400
    import subprocess
    try:
        proc = subprocess.run(
            [sys.executable, str(BASE_DIR / "mcq_bank_generator.py"),
             "--chapter", chapter, "--count", str(count)],
            capture_output=True, text=True, timeout=120, cwd=str(BASE_DIR))
    except Exception as e:
        return jsonify({"error": f"generator failed: {e}"[:200]}), 500
    # Reload engine pool so new MCQs are immediately available app-wide.
    try:
        mcq_engine._load_or_build_mcq_pool()
    except Exception:
        pass
    log = {}
    try:
        log = json.loads((BASE_DIR / "data" / "mcq_generation_log.json").read_text(
            encoding="utf-8"))
    except Exception:
        pass
    return jsonify({"chapter_id": chapter, "requested": count,
                    "stdout": (proc.stdout or "")[-500:],
                    "pool_total": len(mcq_engine.mcq_pool), "log": log})


@app.delete("/api/flashcards/<card_id>")
def api_flashcard_delete(card_id: str):
    """Delete a flashcard (STUDENT authenticated write)."""
    student_id, err = resolve_identity()
    if err:
        return err
    store_err = require_store()
    if store_err:
        return store_err
    success = delete_flashcard(student_id, card_id)
    if not success:
        return jsonify({"error": "Card not found"}), 404
    return jsonify({"success": True, "card_id": card_id})


@app.patch("/api/flashcards/<card_id>")
def api_flashcard_update(card_id: str):
    """Update flashcard content (STUDENT authenticated write)."""
    data = payload() or {}
    student_id, err = resolve_identity(data)
    if err:
        return err
    store_err = require_store()
    if store_err:
        return store_err
    
    front = data.get("front")
    back = data.get("back")
    tags = data.get("tags")
    
    card = update_flashcard(student_id, card_id, front, back, tags)
    if not card:
        return jsonify({"error": "Card not found"}), 404
    return jsonify(card)


# ==========================================
# Beast Tutor — Unified Single-Brain API (Phase 0)
# One endpoint for step + chat modes. Frontend should migrate here.
# ==========================================

QUERY_LOG = BASE_DIR / "data" / "tutor_query_log.jsonl"


def _sanitize_sid(raw, default="student_local"):
    safe = "".join(c for c in str(raw or "").strip()
                   if c.isalnum() or c in ("-", "_", "@", "."))[:64]
    return safe or default


def _verify_firebase_token(token):
    """Verify a Firebase ID token via firebase-admin.

    Returns (uid, claims_dict) on success, (None, {}) otherwise.
    Never raises. Never logs the token.
    """
    try:
        import firebase_admin
        from firebase_admin import auth as _auth
        if not firebase_admin._apps:
            # Initialise from the same credentials firestore_store uses.
            import firestore_store as _fs
            _fs._init()
        if not firebase_admin._apps:
            return None, {}
        decoded = _auth.verify_id_token(token, check_revoked=False)
        uid = str(decoded.get("uid") or "").strip()
        if not uid:
            return None, {}
        return _sanitize_sid(uid, default=""), decoded
    except Exception:
        return None, {}


def _header_identity():
    """Identity asserted via the Authorization header.

    Returns (uid_or_None, claims_dict, kind) with kind in
    {'verified', 'dev-raw', 'invalid', 'none'}.
    - 'verified': JWT verified via firebase-admin (trustworthy, any mode).
    - 'dev-raw': raw uid Bearer value, honored ONLY when strict mode is off.
    - 'invalid': a credential was presented but cannot be honored
      (bad JWT, or any credential in strict mode that failed verification).
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None, {}, "none"
    token = auth[7:].strip()[:2048]
    if not token:
        return None, {}, "none"
    if "." in token:
        uid, claims = _verify_firebase_token(token)
        if uid:
            return uid, claims, "verified"
        return None, {}, "invalid"
    if is_strict_auth():
        return None, {}, "invalid"
    if len(token) <= 128:
        safe = _sanitize_sid(token, default="")
        if safe:
            return safe, {}, "dev-raw"
    return None, {}, "none"


def auth_student_id(data=None):
    """Resolve the caller identity.

    Priority:
      1. Valid Firebase ID token (JWT, contains '.') in
         `Authorization: Bearer <token>` -> VERIFIED uid via
         firebase_admin.auth.verify_id_token(). Returned uid is trustworthy.
      2. Otherwise: sanitized body/query student_id — used for local
         development ONLY. When REQUIRE_FIREBASE_AUTH=true this fallback is
         disabled and None is returned (callers must 401).
      3. Legacy dev shortcut: a raw uid (no dots) as the Bearer value is
         accepted ONLY when REQUIRE_FIREBASE_AUTH is not true.

    The backend NEVER trusts a caller-supplied uid when strict mode is on.
    """
    data = data or {}
    hid, _hclaims, hkind = _header_identity()
    if hkind == "verified":
        return hid
    if hkind == "invalid":
        # A credential was presented but failed verification: never silently
        # fall back to a caller-supplied id (impersonation vector).
        return None if is_strict_auth() else hid
    if hkind == "dev-raw":
        return hid
    if is_strict_auth():
        return None
    raw = str((data.get("student_id") if isinstance(data, dict) else None)
              or request.args.get("student_id") or "student_local")
    return _sanitize_sid(raw)


def require_auth_student(data=None):
    """Returns (student_id, None) or (None, error_response_401)."""
    sid = auth_student_id(data)
    if not sid:
        return None, (jsonify({"error": "Authentication required. Sign in and retry."}), 401)
    return sid, None


def resolve_identity(data=None):
    """Identity for AUTHENTICATED write operations (MCQ submit, flashcards...).

    - Strict (production): uid comes ONLY from the verified token. If the
      client also sent a student_id (body/query) that DIFFERS, reject 403 —
      a client can never override the authenticated UID.
    - Dev (DEV_AUTH_MODE=true): header identity wins when present; otherwise
      the sanitized body/query id (local testing convenience).
    Returns (uid, None) or (None, error_response).
    """
    data = data if isinstance(data, dict) else {}
    hid, _hclaims, hkind = _header_identity()
    if hkind == "invalid":
        return None, (jsonify({"error": "Authentication required. Sign in and retry."}), 401)
    if hkind in ("verified", "dev-raw"):
        claimed = _sanitize_sid(data.get("student_id") or request.args.get("student_id") or hid)
        if claimed != hid and not is_admin_request(hid, _hclaims):
            return None, (jsonify({"error": "Identity mismatch: body student_id does not match authenticated user."}), 403)
        return hid, None
    if is_strict_auth():
        return None, (jsonify({"error": "Authentication required. Sign in and retry."}), 401)
    return _sanitize_sid(data.get("student_id") or request.args.get("student_id") or "student_local"), None


def is_admin_request(uid=None, claims=None):
    """True only with a VERIFIED admin identity.

    Sources (in order): Firebase custom claim `admin:true` from a verified
    token, or the server-side `users/{uid}` doc with role == 'admin'
    (read via the Admin SDK / local fallback — never from client input).
    """
    claims = claims or {}
    if claims.get("admin") is True:
        return True
    if not uid:
        return False
    # A raw-uid Bearer / body id in dev mode is NOT sufficient for admin.
    auth = request.headers.get("Authorization", "")
    verified_uid, verified_claims = None, {}
    if auth.startswith("Bearer ") and "." in auth[7:]:
        verified_uid, verified_claims = _verify_firebase_token(auth[7:].strip()[:2048])
        if verified_claims.get("admin") is True:
            return True
    strict = is_strict_auth()
    if strict and verified_uid != uid:
        return False
    lookup_uid = verified_uid or uid
    try:
        doc = firestore_store.load_doc("users", lookup_uid, default=None)
        if isinstance(doc, dict) and str(doc.get("role") or "").lower() == "admin":
            # In non-strict (local dev) mode the users-doc role is honored for
            # the matching uid; in strict mode only a verified uid matches.
            if not strict or (verified_uid and verified_uid == lookup_uid):
                return True
    except Exception:
        pass
    return False


def require_admin():
    """Returns (uid, None) for admins or (None, error_response)."""
    data = payload() if request.is_json else {}
    uid = auth_student_id(data if isinstance(data, dict) else {})
    if not uid:
        return None, (jsonify({"error": "Authentication required. Sign in and retry."}), 401)
    auth = request.headers.get("Authorization", "")
    claims = {}
    if auth.startswith("Bearer ") and "." in auth[7:]:
        _uid, claims = _verify_firebase_token(auth[7:].strip()[:2048])
    if not is_admin_request(uid, claims):
        return None, (jsonify({"error": "Admin access required."}), 403)
    return uid, None


def require_store():
    """Production persistence guard for authenticated WRITE endpoints.

    In strict (production) mode Firestore must back authoritative writes:
    if unreachable, return a controlled 503 BEFORE any local file is written
    (never silently persist to ephemeral container disk). In dev mode this is
    a no-op (local-JSON fallback explicitly permitted).
    Returns None when writes may proceed, else (error_response, 503).
    """
    if is_strict_auth():
        try:
            firestore_store.require_firestore()
        except Exception:
            return (jsonify({"error": "Persistence service unavailable. Try again shortly."}), 503)
    return None


def log_query(entry):
    try:
        QUERY_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry["ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with open(QUERY_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def _maybe_chapter_pdf_reply(query, student_id):
    """Handle 'give me the NCERT PDF for <chapter>' chat intent (Phase 5)."""
    try:
        nlp_res = nlp_pipeline.process_query(query, [], student_id=student_id)
    except Exception:
        return None
    if (nlp_res.get("intent") or "") != "request_chapter_pdf":
        return None
    cid = None
    try:
        chk = syllabus_validator.check_query_syllabus(query)
        for key in ("chapter_id", "chapter"):
            v = chk.get(key)
            if isinstance(v, str) and v.lower().startswith("c") and v.lower() != "core":
                cid = v
                break
        if not cid:
            mc = chk.get("matched_chapters") or []
            if mc:
                cid = mc[0]
    except Exception:
        pass
    if not cid:
        # fallback: normalized name match against canonical chapters
        # (punctuation-insensitive: "cell - the unit of life" == "cell: the unit of life")
        import re as _re
        ql = _re.sub(r"[^a-z0-9]+", " ", query.lower()).strip()
        try:
            sj = syllabus_validator.syllabus
            best, best_cid = 0.0, None
            for cls in ("class_11", "class_12"):
                for unit, ud in (sj.get(cls) or {}).items():
                    for _cid, ch in (ud.get("chapters") or {}).items():
                        cn = _re.sub(r"[^a-z0-9]+", " ", ch.get("chapter_name", "").lower()).strip()
                        if not cn:
                            continue
                        if cn in ql:
                            cid = _cid
                            break
                        # token-overlap fallback for partial mentions ("cell unit life")
                        nt, it = set(ql.split()), set(cn.split())
                        ov = len(nt & it) / max(1, len(it))
                        if ov > best:
                            best, best_cid = ov, _cid
                    if cid:
                        break
                if not cid and best >= 0.6:
                    cid = best_cid
        except Exception:
            pass
    if not cid:
        return {"reply": ("Tell me which chapter you want the NCERT PDF for — e.g. "
                          "'give me the PDF for Cell — The Unit of Life'."),
                "mode": "pdf_request", "status": "needs_chapter",
                "chapter_id": None, "student_id": student_id}
    try:
        cid = syllabus_validator.normalize_chapter_id(cid) or cid
    except Exception:
        pass
    fn = CHAPTER_PDF_MAP.get(str(cid).lower())
    if not fn:
        return {"reply": (f"I couldn't find a mapped NCERT PDF for that chapter ({cid}) "
                          "in the rationalized set — try the Lessons page chapters with a "
                          "Download button."),
                "mode": "pdf_request", "status": "no_pdf",
                "chapter_id": cid, "student_id": student_id}
    cname = cid
    try:
        sj = syllabus_validator.syllabus
        for cls in ("class_11", "class_12"):
            for unit, ud in (sj.get(cls) or {}).items():
                ch = (ud.get("chapters") or {}).get(str(cid).lower())
                if ch and ch.get("chapter_name"):
                    cname = ch["chapter_name"]
                    break
    except Exception:
        pass
    return {"reply": (f"Here is the NCERT PDF for **{cname}** — "
                      f"[Download PDF](/api/textbook/pdf/{cid})."),
            "mode": "pdf_request", "status": "success",
            "chapter_id": cid, "pdf_url": f"/api/textbook/pdf/{cid}",
            "student_id": student_id}


def build_unified_answer(query, student_id, history=None, context=None, include_steps=True):
    """Single-brain: adaptive RAG reply + optional step-session for stepper UI."""
    t0 = time.time()
    history = history if isinstance(history, list) else []
    context = context if isinstance(context, dict) else {}

    # 0. Greeting Check: Welcome student warmly with high-yield starting options
    from adaptive_tutor import AdaptiveBiologyTutor
    if AdaptiveBiologyTutor._is_greeting(query):
        greet_res = adaptive_tutor.generate_tutoring_response("Hi", student_id=student_id)
        greet_res["latency_ms"] = int((time.time() - t0) * 1000)
        greet_res["resolved_query"] = query
        log_query({
            "student_id": student_id, "query": query[:300],
            "mode": greet_res.get("mode"), "confidence": greet_res.get("confidence"),
            "concept_id": greet_res.get("concept_id"), "chapter_id": greet_res.get("chapter_id"),
            "strategy": greet_res.get("strategy"), "latency_ms": greet_res.get("latency_ms"),
        })
        return greet_res

    # 0b. Content Classification & Policy Guardrail Gate
    # (evidence-grounded admission for imperfect Off-Topic redirects)
    classif = content_classifier.classify(query, history=history)
    allowed, decision = _apply_policy_decision(classif, query, history)
    if not allowed:
        return {
            "reply": decision.get("reply") or "Request not permitted.",
            "mode": decision.get("mode", "restricted"),
            "status": "policy_restricted",
            "classification": decision.get("classification"),
            "confidence": "REJECTED" if decision.get("action") == "block" else "LOW",
            "resolved_query": query,
            "latency_ms": int((time.time() - t0) * 1000),
            "student_id": student_id,
        }

    # 0b. Chapter-PDF delivery intent (Phase 5) — before generic tutoring.
    pdf_reply = _maybe_chapter_pdf_reply(query, student_id)
    if pdf_reply:
        pdf_reply["latency_ms"] = int((time.time() - t0) * 1000)
        pdf_reply["resolved_query"] = query
        return pdf_reply

    # Normalize focus chapter once
    focus = context.get("chapter") or context.get("chapter_id")
    if focus:
        try:
            norm = syllabus_validator.normalize_chapter_id(str(focus))
            if norm:
                focus = norm
                context["chapter"] = norm
        except Exception:
            pass
    # Main RAG answer (comparison-aware, figures-aware, guardrailed — see adaptive_tutor)
    tutor_res = adaptive_tutor.generate_tutoring_response(
        query=query, student_id=student_id, history=history, focus_chapter_id=focus,
        tone_flag=decision.get("tone_flag"),
    )
    out = dict(tutor_res)
    out["student_id"] = student_id
    out["latency_ms"] = int((time.time() - t0) * 1000)
    try:
        import dialogue_state as _ds
        _ds.record_turn(student_id, out.get("concept_id"), out.get("title"),
                        out.get("strategy"), out.get("concept_mastery"))
        out["due_reviews"] = _ds.due_reviews(student_id)[:5]
        out["dialogue_turns"] = (_ds.load(student_id) or {}).get("turns", 1)
    except Exception:
        pass
    # Attach a step session so the stepper UI keeps working with one call
    # (skipped for MCQ practice/review modes — stepwise explanation doesn't apply).
    if include_steps and tutor_engine is not None and out.get("status") == "success" and out.get("mode") not in ("mcq_practice", "mcq_review"):
        try:
            sess = tutor_engine.start_query_session(query=query, student_id=student_id, history=history)
            if isinstance(sess, dict) and sess.get("session_id"):
                out["step_session"] = sess
                out["session_id"] = sess.get("session_id")
        except Exception as exc:
            out["step_session_error"] = str(exc)[:200]

    # Post-generation response validation
    if out.get("reply"):
        val_res = response_validator.validate_response(out["reply"], concept_id=out.get("concept_id"), student_id=student_id)
        out["reply"] = val_res["sanitized_response"]
        out["compliance_valid"] = val_res["is_valid"]

    log_query({
        "student_id": student_id, "query": query[:300],
        "mode": out.get("mode"), "confidence": out.get("confidence"),
        "concept_id": out.get("concept_id"), "chapter_id": out.get("chapter_id"),
        "strategy": out.get("strategy"), "latency_ms": out.get("latency_ms"),
        "hybrid_score": out.get("hybrid_score"),
    })
    return out


@app.get("/api/safety/metrics")
def safety_metrics():
    """Returns real-time content classifier and response validator safety metrics."""
    return jsonify(response_validator.get_metrics())


@app.post("/api/tutor/answer")
def tutor_answer():
    if rate_limited():
        return jsonify({"error": "Too many requests. Wait a minute and try again."}), 429
    data = payload() or {}
    query = str(data.get("query") or data.get("question") or data.get("message") or "").strip()[:3000]
    if not query:
        return jsonify({"error": "Please provide a query."}), 400
    # Public tutoring endpoint: personalization is best-effort. A caller that
    # presents an UNVERIFIABLE credential is treated as anonymous
    # (student_local) — it is never attributed to a spoofed identity.
    student_id = auth_student_id(data) or "student_local"
    history = data.get("history", [])
    context = data.get("context", {})
    out = build_unified_answer(query, student_id, history, context, include_steps=True)
    try:
        if out.get("reply"):
            _append_chat_turn(student_id, query, out["reply"])
    except Exception:
        pass
    return jsonify(out)


@app.get("/api/chat/thread")
def api_chat_thread():
    """Load persisted chat thread (last turns) for a student."""
    student_id = auth_student_id()
    thread = firestore_store.load_doc("chat_threads", student_id, default=None) or {"turns": []}
    return jsonify({"student_id": student_id, "turns": (thread.get("turns") or [])[-20:]})


@app.delete("/api/chat/thread")
def api_chat_thread_clear():
    """Clear persisted chat thread for a student (STUDENT authenticated write)."""
    student_id, err = resolve_identity()
    if err:
        return err
    store_err = require_store()
    if store_err:
        return store_err
    firestore_store.save_doc("chat_threads", student_id, {"turns": []})
    return jsonify({"success": True, "student_id": student_id})


@app.post("/api/tutor/answer/stream")
def tutor_answer_stream():
    """SSE streaming of the unified answer (paragraph chunks). Falls back gracefully."""
    data = payload() or {}
    query = str(data.get("query") or data.get("question") or data.get("message") or "").strip()[:3000]
    if not query:
        return jsonify({"error": "Please provide a query."}), 400
    student_id = auth_student_id(data)
    history = data.get("history", [])
    context = data.get("context", {})
    out = build_unified_answer(query, student_id, history, context, include_steps=False)

    def generate():
        yield f"data: {json.dumps({'type': 'meta', 'confidence': out.get('confidence'), 'concept_id': out.get('concept_id'), 'chapter_id': out.get('chapter_id'), 'strategy': out.get('strategy')})}\n\n"
        reply = str(out.get("reply", ""))
        # Stream paragraph-by-paragraph for smooth UX without token streaming infra
        for para in reply.split("\n\n"):
            yield f"data: {json.dumps({'type': 'chunk', 'text': para})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'latency_ms': out.get('latency_ms'), 'citations': out.get('citations', []), 'figures': out.get('figures', []), 'check_mcq': out.get('check_mcq')})}\n\n"

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    print("\n" + "=" * 65, flush=True)
    print("  [*] BioNEET Pro AI Tutor Backend is RUNNING!", flush=True)
    print(f"  [*] Open in your browser: http://127.0.0.1:{port}", flush=True)
    print("  [!] KEEP THIS TERMINAL OPEN while using the app!", flush=True)
    print("      (Do NOT press Ctrl+C or close this window)", flush=True)
    print("=" * 65 + "\n", flush=True)
    app.run(host="127.0.0.1", port=port, debug=debug)
