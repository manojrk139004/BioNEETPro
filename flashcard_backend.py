"""
BioNEET-Pro — Leitner Flashcard Backend
========================================
Server-side persistence for Leitner flashcard system with 1/3/7/14/30-day intervals.
Integrates with existing learner_model.py mastery system — does NOT create a second mastery system.
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import firestore_store

from learner_model import learner_manager

DATA_DIR = Path(__file__).resolve().parent / "data"
FLASHCARD_DIR = DATA_DIR / "flashcard_state"
FLASHCARD_DIR.mkdir(parents=True, exist_ok=True)

_COLLECTION = "flashcards"

# Leitner intervals in days
LEITNER_INTERVALS = [1, 3, 7, 14, 30]
MAX_BOX = len(LEITNER_INTERVALS) - 1  # Box 4 (30 days)


def _student_flashcard_path(student_id: str) -> Path:
    safe_id = "".join(c for c in student_id if c.isalnum() or c in ("-", "_")) or "student_local"
    return FLASHCARD_DIR / f"{safe_id}.json"


def _default_state(student_id: str) -> Dict[str, Any]:
    return {
        "student_id": student_id,
        "cards": {},  # card_id -> {front, back, box, next_review, created_at, updated_at}
        "stats": {
            "total_reviews": 0,
            "correct_reviews": 0,
            "current_streak": 0,
            "longest_streak": 0,
        },
    }


def _load_flashcards(student_id: str) -> Dict[str, Any]:
    """Load flashcard state for a student (Firestore-first, file fallback)."""
    state = firestore_store.load_doc(_COLLECTION, student_id, default=None)
    if isinstance(state, dict) and "cards" in state:
        return state
    return _default_state(student_id)


def _save_flashcards(student_id: str, state: Dict[str, Any]):
    """Save flashcard state for a student (file cache + Firestore)."""
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    firestore_store.save_doc(_COLLECTION, student_id, state)


def create_flashcard(
    student_id: str,
    front: str,
    back: str,
    concept_id: str = "",
    chapter_id: str = "",
    tags: List[str] = None,
) -> Dict[str, Any]:
    """Create a new flashcard in box 0 (1-day interval)."""
    state = _load_flashcards(student_id)
    
    # Generate card ID
    import uuid
    card_id = f"fc_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    next_review = now + timedelta(days=LEITNER_INTERVALS[0])
    
    card = {
        "card_id": card_id,
        "front": front,
        "back": back,
        "concept_id": concept_id,
        "chapter_id": chapter_id,
        "tags": tags or [],
        "box": 0,
        "next_review": next_review.isoformat(),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "review_history": [],
    }
    
    state["cards"][card_id] = card
    _save_flashcards(student_id, state)
    
    return card


def get_due_flashcards(student_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get flashcards due for review."""
    state = _load_flashcards(student_id)
    now = datetime.now(timezone.utc)
    
    due = []
    for card in state["cards"].values():
        try:
            if datetime.fromisoformat(card["next_review"]) <= now:
                due.append(card)
        except Exception:
            # If date parsing fails, include it
            due.append(card)
    
    # Sort by next_review (oldest first)
    due.sort(key=lambda c: c.get("next_review", ""))
    return due[:limit]


def review_flashcard(
    student_id: str,
    card_id: str,
    is_correct: bool,
) -> Dict[str, Any]:
    """
    Process a flashcard review using Leitner algorithm.
    Updates box level and next_review date.
    Also updates learner_model mastery for the associated concept.
    """
    state = _load_flashcards(student_id)
    
    if card_id not in state["cards"]:
        return {"error": "Card not found", "card_id": card_id}
    
    card = state["cards"][card_id]
    current_box = card.get("box", 0)
    
    # Update Leitner box
    if is_correct:
        new_box = min(current_box + 1, MAX_BOX)
    else:
        new_box = 0  # Reset to box 0 on failure
    
    # Calculate next review
    interval_days = LEITNER_INTERVALS[new_box]
    next_review = datetime.now(timezone.utc) + timedelta(days=interval_days)
    
    # Update card
    card["box"] = new_box
    card["next_review"] = next_review.isoformat()
    card["updated_at"] = datetime.now(timezone.utc).isoformat()
    card["review_history"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_correct": is_correct,
        "previous_box": current_box,
        "new_box": new_box,
    })
    
    # Update stats
    state["stats"]["total_reviews"] += 1
    if is_correct:
        state["stats"]["correct_reviews"] += 1
        state["stats"]["current_streak"] += 1
        state["stats"]["longest_streak"] = max(
            state["stats"]["longest_streak"],
            state["stats"]["current_streak"]
        )
    else:
        state["stats"]["current_streak"] = 0
    
    _save_flashcards(student_id, state)
    
    # Integrate with learner_model if concept_id exists
    mastery_update = None
    if card.get("concept_id"):
        try:
            mastery_update = learner_manager.record_attempt(
                student_id=student_id,
                concept_id=card["concept_id"],
                chapter_id=card.get("chapter_id") or "general",
                is_correct=is_correct,
                difficulty="medium",
                cognitive_level="BT2",
                topic_id=card.get("chapter_id") or "Flashcard Review",
            )
        except Exception as e:
            mastery_update = {"error": str(e)}
    
    return {
        "card_id": card_id,
        "is_correct": is_correct,
        "previous_box": current_box,
        "new_box": new_box,
        "interval_days": interval_days,
        "next_review": next_review.isoformat(),
        "mastery_update": mastery_update,
    }


def get_flashcard_stats(student_id: str) -> Dict[str, Any]:
    """Get flashcard statistics for a student."""
    state = _load_flashcards(student_id)
    now = datetime.now(timezone.utc)
    
    total = len(state["cards"])
    due_count = 0
    box_distribution = {i: 0 for i in range(len(LEITNER_INTERVALS))}
    
    for card in state["cards"].values():
        box = card.get("box", 0)
        box_distribution[box] = box_distribution.get(box, 0) + 1
        try:
            if datetime.fromisoformat(card["next_review"]) <= now:
                due_count += 1
        except Exception:
            due_count += 1
    
    stats = state.get("stats", {})
    accuracy = 0.0
    if stats.get("total_reviews", 0) > 0:
        accuracy = stats["correct_reviews"] / stats["total_reviews"]
    
    return {
        "student_id": student_id,
        "total_cards": total,
        "due_cards": due_count,
        "box_distribution": box_distribution,
        "interval_days": LEITNER_INTERVALS,
        "total_reviews": stats.get("total_reviews", 0),
        "correct_reviews": stats.get("correct_reviews", 0),
        "accuracy": round(accuracy, 3),
        "current_streak": stats.get("current_streak", 0),
        "longest_streak": stats.get("longest_streak", 0),
    }


def get_all_flashcards(student_id: str) -> List[Dict[str, Any]]:
    """Get all flashcards for a student (for management UI)."""
    state = _load_flashcards(student_id)
    cards = list(state["cards"].values())
    cards.sort(key=lambda c: c.get("created_at", ""), reverse=True)
    return cards


def delete_flashcard(student_id: str, card_id: str) -> bool:
    """Delete a flashcard."""
    state = _load_flashcards(student_id)
    if card_id in state["cards"]:
        del state["cards"][card_id]
        _save_flashcards(student_id, state)
        return True
    return False


def update_flashcard(
    student_id: str,
    card_id: str,
    front: str = None,
    back: str = None,
    tags: List[str] = None,
) -> Optional[Dict[str, Any]]:
    """Update flashcard content."""
    state = _load_flashcards(student_id)
    
    if card_id not in state["cards"]:
        return None
    
    card = state["cards"][card_id]
    if front is not None:
        card["front"] = front
    if back is not None:
        card["back"] = back
    if tags is not None:
        card["tags"] = tags
    card["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    _save_flashcards(student_id, state)
    return card