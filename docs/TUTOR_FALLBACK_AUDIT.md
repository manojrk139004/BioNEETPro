# BioNEETPro V1 — External LLM Fallback Architecture & Audit Report
**Date:** 2026-09-05  
**System:** BioNEETPro AI Biology Tutor (`Dr. Priya`)  
**Status:** VERIFIED & PRODUCTION READY  

---

## 1. Executive Summary & Root Cause Analysis

### 1.1 The Shipped Bug
When users submitted queries on valid NCERT Biology topics that had low or zero indexed local textbook chunks (reproduced on `"explain parts of flower"`, `"explain me parts of flower"`, and `"explain biofertilizers"`), the tutor returned a hard refusal:
> *"I couldn't find enough verified NCERT evidence for that specific Biology question in my local textbook knowledge base. Try asking about an NCERT topic such as Mitochondria, Cell Division, Photosynthesis, or Human Neural Control."*

### 1.2 Root Causes Identified
1. **Missing Tier 3 External LLM Fallback for Unindexed Concepts:**
   When local dual-corpus retrieval returned 0 chunks, `adaptive_tutor.py` only checked whether the query was an anaphoric follow-up. If not, it immediately aborted to a static string refusal (`controlled_refusal`), completely ignoring the configured OpenRouter LLM capabilities.
2. **Strict RAG Gating on Partial Evidence:**
   Even when local retrieval returned partial evidence (`hybrid_score < 0.55`), `_generate_api_grounded_response` required strict cite-or-refuse against the evidence pack, instructing the LLM: *"If the question cannot be answered purely from this text, say CANNOT ANSWER"*, triggering immediate fallback to refusal instead of allowing curriculum synthesis.
3. **Stale UI Context Interference:**
   If the student had previously selected a chapter (or the frontend passed default `focus_chapter_id="c13"` for Photosynthesis), the retrieval filter forced queries about other chapters to search only within that chapter, artificially reducing retrieval score to 0.
4. **404 Endpoint Failure on Default Model:**
   The default model `agnes-2.0-flash` returned `404 Not Found` on `router.bynara.id`. The system lacked a multi-model failover chain to seamlessly escalate to available models like `agnes-2.5-flash`.
5. **HTML / Cloudflare Gateway Error Parsing:**
   Proxy 502/504 errors returned HTML pages (`<html><body>502 Bad Gateway</body></html>`) which caused JSON parsing exceptions instead of triggering clean failover to the next candidate model.

---

## 2. Principled 4-Tier Fallback Hierarchy

The tutor architecture has been redesigned with a strict, principled 4-tier hierarchy:

| Tier | Condition | Engine / Action | Source Mode | Fallback Tier |
|---|---|---|---|---|
| **Tier 1** | Strong local NCERT evidence (`score >= 0.55`) | Dual-corpus RAG grounded strictly in textbook evidence chunks | `local_ncert` | `tier_1` |
| **Tier 2** | Partial local evidence (`0.35 <= score < 0.55`) | LLM prompt combines retrieved evidence chunks with verified NCERT Class 11/12 facts | `local_plus_llm` | `tier_2` |
| **Tier 3** | Valid NCERT Biology query, 0 or insufficient local evidence | Model failover chain calls external LLM with Dr. Priya NCERT persona | `external_llm_fallback` | `tier_3` |
| **Tier 4** | Out-of-syllabus, policy violation, or all external models fail | Safe educational refusal / boundary notice | `safe_fallback` | `tier_4` |

---

## 3. Multi-Model Failover Mechanics

### 3.1 Model Chain Resolution
The fallback engine queries candidate models sequentially:
1. Model specified in `OPENROUTER_MODEL` environment variable (defaulted to `agnes-2.5-flash`).
2. `agnes-2.5-flash` (confirmed working on `router.bynara.id` with 200 OK).
3. `agnes-2.0-flash` (legacy fallback).
4. `google/gemini-2.5-flash` / `openai/gpt-4o-mini` (provider fallback).

### 3.2 Robust Network & Error Resilience
The model caller checks:
- **HTTP Status Code:** Fails over immediately on 4xx or 5xx status codes without throwing uncaught exceptions.
- **Content-Type & HTML Detection:** Inspects `Content-Type` header and raw response text. If the proxy returns HTML (e.g. `<html><body>502 Bad Gateway</body></html>`), it skips to the next candidate model.
- **Empty / Short Output Detection:** Ensures choices exist, content length is >= 60 characters, and avoids "cannot answer" loops.
- **Post-Generation Sanitization:** Passes external LLM output through `ResponseValidator`. If prompt leakage or safety flags occur, the text is replaced with `SAFE_FALLBACK_TEMPLATE` or cleaned before delivery.
- **Offline / Disconnected Grace:** If network connection fails or no API keys exist, Tier 1 falls back to local deterministic templates, and Tier 3 gracefully returns Tier 4 safe refusal.

---

## 4. Query Dominance & Context Isolation

To fix the stale context bug where a selected chapter in the UI prevented retrieving concepts from other chapters:
- When a student query contains its own explicit NCERT keywords (`matched_keywords` in `syllabus_validator`), `effective_focus` is set to `None`.
- The user's explicit query dominates over sticky UI dropdowns (`focus_chapter_id`) and conversational history (`focal_concept`).

---

## 5. Security & Grounding Guardrails

All external fallback paths strictly preserve safety and pedagogical guardrails:
1. **Pre-flight Injection Gate:** Regex filters block jailbreak phrases (`"ignore previous instructions"`, `"reveal system prompt"`, etc.) before any network request is issued.
2. **Syllabus Boundary Gate:** Non-biology queries (e.g. `"Explain Newton's laws of motion"`, `"Who won the cricket world cup"`, Python code, math formulas) are rejected at the syllabus boundary with `status: "out_of_syllabus"`, `confidence: "REJECTED"`, and `source_mode: "safe_fallback"`. They **NEVER** reach Tier 3 external LLMs.
3. **Sensitive Topic Medical Tone:** Topics involving human reproduction or anatomy trigger clinical/medical educational phrasing without euphemisms or moralizing.
4. **Dr. Priya Persona:** All Tier 3 outputs format under the Dr. Priya persona:
   - Core Definition & Overview
   - Key Mechanisms / Structural Details
   - ⚠️ NEET Traps & High-Yield Exam Points (3 points)
   - 💬 Diagnostic Check Question (1 question)
   - NCERT Source Reference footer

---

## 6. Verification Results

### 6.1 Targeted Fallback Test Suite (`tests/test_tutor_external_fallback.py`)
All 19 Scenarios (A through S) PASSED:

| Scenario | Description | Result |
|---|---|---|
| **Scenario A** | Strong local evidence -> Tier 1 (`local_ncert`) | **PASS** |
| **Scenario B** | Partial local evidence -> Tier 2 (`local_plus_llm`) | **PASS** |
| **Scenario C** | Zero local evidence -> Tier 3 (`external_llm_fallback`) | **PASS** |
| **Scenario D** | Stale context vs explicit query dominance | **PASS** |
| **Scenario E** | Out-of-scope query rejected (syllabus boundary preserved) | **PASS** |
| **Scenario F** | Non-academic / off-topic rejected (content classifier) | **PASS** |
| **Scenario G** | Prompt injection blocked (pre-flight + policy) | **PASS** |
| **Scenario H** | Primary model 404/500 -> Secondary model failover | **PASS** |
| **Scenario I** | Primary model HTML response -> Model failover | **PASS** |
| **Scenario J** | All models fail / offline -> Tier 4 safe refusal | **PASS** |
| **Scenario K** | Response validation enforced on external output | **PASS** |
| **Scenario L** | Observability metadata present; zero internal leakage | **PASS** |
| **Scenario M** | Shipped queries (`"explain parts of flower"`, `"explain me parts of flower"`) | **PASS** |
| **Scenario N** | `"explain biofertilizers"` answered via external fallback | **PASS** |
| **Scenario O** | Multi-turn topic switch dominance | **PASS** |
| **Scenario P** | Generic unindexed biology concept fallback (no hardcoding) | **PASS** |
| **Scenario Q** | Sensitive topic medical educational tone flag | **PASS** |
| **Scenario R** | Local offline mode works without network/API key | **PASS** |
| **Scenario S** | Stepper UI session compatibility preserved | **PASS** |

**Test Execution:** `Ran 19 tests in 132.461s — OK`

### 6.2 Regression Verification Across Existing Suites
- **`test_master_suite.py`:** `Ran 17 tests in 25.830s — OK (17/17 PASS)`
- **`tests/test_v1_security_hardening.py`:** `Ran 18 tests in 112.284s — OK (18/18 PASS)`
- **`evaluate_tutor_beast.py`:** `98/98 PASS (Biology: 91/91, Out-of-Syllabus: 7/7, Faithfulness: 0.525)`
  - Gate verdict: **GREEN - SHIP IT**

---

## 7. Manual Browser Verification Guide

To verify in the live application:
1. Start the backend:
   ```bash
   .\.venv\Scripts\python.exe app.py
   ```
2. Open `BioNeet-Pro.html` in a web browser.
3. Submit the reported queries:
   - Input: `"explain parts of flower"`
     - *Expected:* Comprehensive breakdown of Calyx, Corolla, Androecium, and Gynoecium with Dr. Priya persona and NEET traps.
   - Input: `"explain biofertilizers"`
     - *Expected:* Detailed explanation of Rhizobium, Azotobacter, mycorrhizae, and cyanobacteria with Dr. Priya persona.
   - Input: `"Explain Newton's laws of motion"`
     - *Expected:* Immediate polite syllabus refusal notice directing student to NEET Biology topics.
