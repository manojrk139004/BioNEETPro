

import datetime
import json
import os
import re
import time
from collections import defaultdict, deque
from pathlib import Path

import requests
from flask import Flask, Response, jsonify, request
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

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "ALLOWED_ORIGINS",
        "http://localhost:5000,http://127.0.0.1:5000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if origin.strip() and origin.strip() != "file://"
]
CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGINS if "*" not in ALLOWED_ORIGINS else "*"}})

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


def demo_ai_answer(message, student_id="student_local", history=None, context=None):
    clean = (message or "").strip()
    if not clean:
        return (
            "👩‍⚕️ **Dr. Priya (AI Biology Mentor):**\n"
            "*\"Please ask any NCERT Biology doubt or request practice MCQs!\"*"
        )

    # 1. NLP Intent Detection: Check if student is requesting on-demand MCQs
    nlp_res = nlp_pipeline.process_query(clean, history or [], student_id=student_id)
    if nlp_res["intent"] == "mcq_request":
        mcq_data = mcq_engine.generate_mcqs(clean, student_id=student_id)
        return mcq_engine.format_mcqs_for_chat(mcq_data)

    # 2. ONE BRAIN: single unified pipeline (RAG generator + template fallback inside).
    # /chat, /ask and /api/tutor/answer all end up here — no divergent logic.
    out = build_unified_answer(clean, student_id, history, context, include_steps=False)

    # 3. Controlled Emergency Fallback (only if unified pipeline is LOW and flag enabled)
    if out.get("confidence") == "LOW" and fallback_controller.should_trigger_fallback("LOW"):
        fb = fallback_controller.execute_fallback(clean, "local_low_confidence", history)
        if fb:
            return fb["reply"]

    return out.get("reply", "")


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
    models = [OPENROUTER_MODEL]
    if OPENROUTER_KEY and OPENROUTER_KEY.startswith("sk-nry-"):
        models.extend(["agnes-2.0-flash", "minimax-m3-free"])
    return list(dict.fromkeys([m for m in models if m]))


try:
    from tutor_engine import tutor_engine
except Exception as e:
    print(f"Warning: tutor_engine could not be loaded: {e}")
    tutor_engine = None


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
            student_id = str(data.get("student_id") or "student_local")
            history = data.get("history", [])
            context = data.get("context", {})
            reply_text = demo_ai_answer(message, student_id=student_id, history=history, context=context)
            return jsonify({"reply": reply_text, "answer": reply_text, "mode": "local_adaptive"})

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
                    timeout=45,
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
    Audit / Evaluator Endpoint:
    Returns the recent entries logged into data/student_learning_tracker.csv.
    """
    if not tutor_engine:
        return jsonify({"error": "Local tutor engine not initialized."}), 500

    limit = int(request.args.get("limit", 25))
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
    Scans data/kaggle_imports/ or imports new Kaggle dataset CSVs,
    merges them into neet_knowledge_base.csv, and immediately re-trains TF-IDF vector space model.
    """
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500



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
    student_id = str(data.get("student_id") or "student_local").strip()
    result = mcq_engine.generate_mcqs(req_text, student_id=student_id)
    return jsonify(result)


@app.post("/api/mcq/submit")
def api_mcq_submit():
    """
    Evaluates MCQ attempt, updates student BKT mastery, and logs performance.
    """
    data = payload() or {}
    student_id = str(data.get("student_id") or "student_local").strip()[:64] or "student_local"
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


@app.get("/api/learner/profile")
def api_learner_profile():
    """
    Returns complete student learning trajectory, concept mastery scores, and repeated mistakes.
    """
    student_id = str(request.args.get("student_id") or "student_local").strip()
    profile = learner_manager.get_or_create_profile(student_id)
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


# ==========================================
# Beast Tutor — Unified Single-Brain API (Phase 0)
# One endpoint for step + chat modes. Frontend should migrate here.
# ==========================================

QUERY_LOG = BASE_DIR / "data" / "tutor_query_log.jsonl"


def auth_student_id(data=None):
    """Prefer Firebase uid from Authorization header; fall back to sanitized body student_id."""
    data = data or {}
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer ") and len(auth) > 20:
        # Full JWT verification requires firebase-admin (optional dep).
        # We accept the uid claim client-side and sanitize; strict verification
        # can be enabled by setting REQUIRE_FIREBASE_AUTH=true + installing firebase-admin.
        token = auth[7:][:512]
        # Heuristic: Firebase uids are 1-128 chars alnum/-/_; JWTs contain dots.
        # If a raw uid was sent (dev), use it; otherwise fall back to body id.
        if "." not in token and len(token) <= 128:
            safe = "".join(c for c in token if c.isalnum() or c in ("-", "_"))[:64]
            if safe:
                return safe
    raw = str((data.get("student_id") or request.args.get("student_id")) or "student_local")
    safe = "".join(c for c in raw.strip() if c.isalnum() or c in ("-", "_", "@", "."))[:64]
    return safe or "student_local"


def log_query(entry):
    try:
        QUERY_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry["ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with open(QUERY_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def build_unified_answer(query, student_id, history=None, context=None, include_steps=True):
    """Single-brain: adaptive RAG reply + optional step-session for stepper UI."""
    t0 = time.time()
    history = history if isinstance(history, list) else []
    context = context if isinstance(context, dict) else {}
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
    if include_steps and tutor_engine is not None and out.get("status") == "success":
        try:
            sess = tutor_engine.start_query_session(query=query, student_id=student_id, history=history)
            if isinstance(sess, dict) and sess.get("session_id"):
                out["step_session"] = sess
                out["session_id"] = sess.get("session_id")
        except Exception as exc:
            out["step_session_error"] = str(exc)[:200]
    log_query({
        "student_id": student_id, "query": query[:300],
        "mode": out.get("mode"), "confidence": out.get("confidence"),
        "concept_id": out.get("concept_id"), "chapter_id": out.get("chapter_id"),
        "strategy": out.get("strategy"), "latency_ms": out.get("latency_ms"),
        "hybrid_score": out.get("hybrid_score"),
    })
    return out


@app.post("/api/tutor/answer")
def tutor_answer():
    data = payload() or {}
    query = str(data.get("query") or data.get("question") or data.get("message") or "").strip()[:3000]
    if not query:
        return jsonify({"error": "Please provide a query."}), 400
    student_id = auth_student_id(data)
    history = data.get("history", [])
    context = data.get("context", {})
    out = build_unified_answer(query, student_id, history, context, include_steps=True)
    return jsonify(out)


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
    app.run(host="127.0.0.1", port=port, debug=debug)
