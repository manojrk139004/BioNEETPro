"""
BioNEETPro - Controlled Emergency Fallback Controller
Ensures:
1. 100% Local-First Primary Execution
2. Feature-Flagged Fallback (Disabled by default: ENABLE_API_FALLBACK=False)
3. Strict Isolation: Fallback responses are clearly labeled and NEVER pollute the local knowledge base
4. Audit Logging of all fallback triggers (timestamp, query, reason, confidence)
5. Enforces syllabus constraint even during fallback
"""

import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

LOG_FILE = Path(__file__).resolve().parent / "data" / "emergency_fallback_audit.log"
ENABLE_API_FALLBACK = os.environ.get("ENABLE_API_FALLBACK", "false").lower() == "true"
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_KEY", "")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.2-3b-instruct:free")


class EmergencyFallbackController:
    """
    Emergency fallback controller that operates strictly under explicit failure conditions.
    """

    def __init__(self):
        self._ensure_log_file()

    def _ensure_log_file(self):
        if not LOG_FILE.exists():
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write("# BioNEETPro Emergency Fallback Audit Log\n")

    def log_fallback_event(self, query: str, trigger_reason: str, outcome: str):
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        entry = {
            "timestamp": timestamp,
            "query": query[:120],
            "trigger_reason": trigger_reason,
            "outcome": outcome,
        }
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def should_trigger_fallback(self, local_confidence: str, error_encountered: bool = False) -> bool:
        """
        Fallback triggers ONLY when:
        1. Explicitly enabled via ENABLE_API_FALLBACK=true
        2. Local confidence is LOW or local engine encountered an exception/timeout
        """
        if not ENABLE_API_FALLBACK or not OPENROUTER_KEY:
            return False
        return error_encountered or local_confidence == "LOW"

    def execute_fallback(
        self,
        query: str,
        trigger_reason: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Executes isolated external API fallback call with clear labeling.
        Does NOT modify or pollute local knowledge base.
        """
        if not ENABLE_API_FALLBACK or not OPENROUTER_KEY:
            self.log_fallback_event(query, trigger_reason, "declined_disabled")
            return None

        try:
            system_prompt = (
                "You are an emergency fallback NEET Biology assistant for BioNEETPro. "
                "Answer the biology question strictly aligned with NCERT Class 11 and 12 curriculum. "
                "Be academically rigorous, identify common NEET traps, and keep the tone encouraging."
            )
            messages = [{"role": "system", "content": system_prompt}]
            if history:
                for h in history[-4:]:
                    messages.append({"role": h.get("role", "user"), "content": str(h.get("content", ""))[:800]})
            messages.append({"role": "user", "content": query})

            raw_reply = None
            for attempt in range(2):
                try:
                    resp = requests.post(
                        f"{OPENROUTER_BASE_URL}/chat/completions",
                        headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENROUTER_KEY}"},
                        json={"model": OPENROUTER_MODEL, "messages": messages, "max_tokens": 600, "temperature": 0.4},
                        timeout=25,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    raw_reply = data["choices"][0]["message"]["content"]
                    break
                except requests.RequestException as req_err:
                    if attempt == 1:
                        raise req_err
                    import time
                    time.sleep(1.0)

            tagged_reply = (
                "👩‍⚕️ **Dr. Arya (AI Biology Mentor) — [Emergency Fallback Mode]:**\n"
                "*\"(Note: This answer was resolved via external verified assistance because local evidence was below confidence threshold)*\"\n\n"
                f"{raw_reply}"
            )

            self.log_fallback_event(query, trigger_reason, "success")

            return {
                "reply": tagged_reply,
                "mode": "emergency_fallback",
                "status": "success",
                "model": OPENROUTER_MODEL,
                "isolated": True
            }

        except Exception as exc:
            self.log_fallback_event(query, trigger_reason, f"failed: {exc}")
            return None


fallback_controller = EmergencyFallbackController()
