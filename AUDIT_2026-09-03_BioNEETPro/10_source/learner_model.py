"""
BioNEETPro - Individual Student Learner Model & Bayesian Knowledge Tracing (BKT)
Tracks:
1. Latent Concept Mastery P(L_t) via Bayesian Knowledge Tracing
2. Chapter & Topic Level Mastery Aggregation
3. Difficulty & Bloom's Cognitive Level Performance
4. Repeated Mistake Detection & Remedial Flags
5. Longitudinal Learning Trajectory (Novice -> Learning -> Developing -> Competent -> Strong -> NEET Ready)
6. Dynamic Learning Trend Detection (improving, stable, declining, repeated_weakness)
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DATA_DIR = Path(__file__).resolve().parent / "data"
PROFILES_DIR = DATA_DIR / "student_profiles"
TRACKER_CSV = DATA_DIR / "student_learning_tracker.csv"


class BayesianKnowledgeTracer:
    """
    Standard Corbett-Anderson Bayesian Knowledge Tracing (BKT) Engine.
    Models latent mastery probability P(L_t) given evidence of correct/incorrect performance.
    """

    def __init__(
        self,
        p_l0: float = 0.50,  # Prior probability of knowing concept
        p_t: float = 0.15,   # Probability of learning transition
        p_s: float = 0.10,   # Probability of slip (knows, but errs)
        p_g: float = 0.25,   # Probability of guess (doesn't know, but correct)
    ):
        self.p_l0 = p_l0
        self.p_t = p_t
        self.p_s = p_s
        self.p_g = p_g

    def update_mastery(self, prior_mastery: float, is_correct: bool) -> float:
        p_l = max(0.01, min(0.99, prior_mastery))
        if is_correct:
            p_posterior = (p_l * (1.0 - self.p_s)) / (
                (p_l * (1.0 - self.p_s)) + ((1.0 - p_l) * self.p_g)
            )
        else:
            p_posterior = (p_l * self.p_s) / (
                (p_l * self.p_s) + ((1.0 - p_l) * (1.0 - self.p_g))
            )
        p_next = p_posterior + (1.0 - p_posterior) * self.p_t
        return round(float(min(0.99, max(0.01, p_next))), 3)


class LearnerProfileManager:
    """
    Manages student learning profiles, mastery trajectories, and repeated mistakes.
    """

    TRAJECTORY_STAGES = [
        (0.90, "NEET Ready", "Mastery level is exceptionally strong. Focus on high-speed simulated full mock tests."),
        (0.80, "Strong", "Strong conceptual command. Target tricky assertion-reason and exception traps."),
        (0.65, "Competent", "Good working understanding. Consolidate biochemical pathways and numerical ratios."),
        (0.50, "Developing", "Progressing steadily. Strengthen step-by-step biological mechanisms."),
        (0.35, "Learning", "Actively building foundations. Review NCERT definitions and diagrams."),
        (0.00, "Novice", "Initial orientation stage. Focus on core NCERT definitions and basic concepts."),
    ]

    def __init__(self, profiles_dir: Path = PROFILES_DIR):
        self.profiles_dir = profiles_dir
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.bkt = BayesianKnowledgeTracer()

    def _get_profile_path(self, student_id: str) -> Path:
        safe_id = "".join(c for c in student_id if c.isalnum() or c in ("-", "_")) or "student_local"
        return self.profiles_dir / f"{safe_id}.json"

    def get_or_create_profile(self, student_id: str = "student_local") -> Dict[str, Any]:
        path = self._get_profile_path(student_id)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        default_profile = {
            "student_id": student_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_active": datetime.now(timezone.utc).isoformat(),
            "overall_mastery": 0.50,
            "trajectory_stage": "Learning",
            "trajectory_advice": "Actively building foundations. Review NCERT definitions and diagrams.",
            "trend": "stable",
            "concept_mastery": {},
            "chapter_mastery": {},
            "topic_mastery": {},
            "difficulty_stats": {"easy": {"correct": 0, "total": 0}, "medium": {"correct": 0, "total": 0}, "hard": {"correct": 0, "total": 0}},
            "cognitive_stats": {"BT1": {"correct": 0, "total": 0}, "BT2": {"correct": 0, "total": 0}, "BT3": {"correct": 0, "total": 0}, "BT4": {"correct": 0, "total": 0}},
            "repeated_mistakes": {},
            "history_log": [],
        }
        self.save_profile(student_id, default_profile)
        return default_profile

    def save_profile(self, student_id: str, profile: Dict[str, Any]):
        path = self._get_profile_path(student_id)
        profile["last_active"] = datetime.now(timezone.utc).isoformat()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)

    def record_attempt(
        self,
        student_id: str,
        concept_id: str,
        chapter_id: str,
        is_correct: bool,
        difficulty: str = "medium",
        cognitive_level: str = "BT2",
        response_time_sec: float = 0.0,
        topic_id: str = "Unknown",
    ) -> Dict[str, Any]:
        """
        Records an MCQ or micro-quiz attempt, updates BKT mastery, tracks repeated mistakes,
        and recalculates the student's learning trajectory.
        """
        profile = self.get_or_create_profile(student_id)

        # Response time analysis
        speed_category = "normal"
        if response_time_sec > 0:
            if is_correct and response_time_sec < 15:
                speed_category = "fast_correct" # strong grasp
            elif is_correct and response_time_sec > 30:
                speed_category = "slow_correct" # developing
            elif not is_correct and response_time_sec < 10:
                speed_category = "fast_incorrect" # guessing

        # 1. Update concept mastery with BKT
        concept_data = profile["concept_mastery"].get(concept_id, {
            "mastery": 0.50,
            "attempts": 0,
            "correct": 0,
            "incorrect": 0,
            "last_attempt": None,
            "topic_id": topic_id,
            "chapter_id": chapter_id,
        })
        prior = concept_data["mastery"]
        new_mastery = self.bkt.update_mastery(prior, is_correct)
        concept_data["mastery"] = new_mastery
        concept_data["attempts"] += 1
        if is_correct:
            concept_data["correct"] += 1
        else:
            concept_data["incorrect"] += 1
        concept_data["last_attempt"] = datetime.now(timezone.utc).isoformat()
        concept_data["topic_id"] = topic_id
        concept_data["chapter_id"] = chapter_id
        profile["concept_mastery"][concept_id] = concept_data

        # 2. Track repeated mistakes
        if not is_correct:
            mistake_entry = profile["repeated_mistakes"].get(concept_id, {
                "mistake_count": 0,
                "first_mistake": datetime.now(timezone.utc).isoformat(),
                "last_mistake": None,
                "severity": "mild",
            })
            mistake_entry["mistake_count"] += 1
            mistake_entry["last_mistake"] = datetime.now(timezone.utc).isoformat()
            if mistake_entry["mistake_count"] >= 4:
                mistake_entry["severity"] = "critical"
            elif mistake_entry["mistake_count"] >= 2:
                mistake_entry["severity"] = "warning"
            profile["repeated_mistakes"][concept_id] = mistake_entry
        else:
            # If student answers correctly, de-escalate mistake count
            if concept_id in profile["repeated_mistakes"]:
                profile["repeated_mistakes"][concept_id]["mistake_count"] = max(
                    0, profile["repeated_mistakes"][concept_id]["mistake_count"] - 1
                )
                if profile["repeated_mistakes"][concept_id]["mistake_count"] == 0:
                    del profile["repeated_mistakes"][concept_id]

        # 3. Update chapter and topic mastery average (strictly filtered by chapter_id)
        chap_concepts = [c for c in profile["concept_mastery"].values() if c.get("chapter_id") == chapter_id]
        if chap_concepts:
            chap_avg = sum(c["mastery"] for c in chap_concepts) / len(chap_concepts)
            profile["chapter_mastery"][chapter_id] = round(chap_avg, 3)
            
        # Topic mastery average
        if "topic_mastery" not in profile:
            profile["topic_mastery"] = {}
        topic_concepts = [c for c in profile["concept_mastery"].values() if c.get("topic_id") == topic_id]
        if topic_concepts:
            topic_avg = sum(c["mastery"] for c in topic_concepts) / len(topic_concepts)
            profile["topic_mastery"][topic_id] = round(topic_avg, 3)

        # 4. Update difficulty & cognitive stats
        diff_key = difficulty.lower() if difficulty.lower() in profile["difficulty_stats"] else "medium"
        profile["difficulty_stats"][diff_key]["total"] += 1
        if is_correct:
            profile["difficulty_stats"][diff_key]["correct"] += 1

        cog_key = cognitive_level.upper() if cognitive_level.upper() in profile["cognitive_stats"] else "BT2"
        profile["cognitive_stats"][cog_key]["total"] += 1
        if is_correct:
            profile["cognitive_stats"][cog_key]["correct"] += 1

        # 5. Overall mastery and trajectory
        all_masteries = [c["mastery"] for c in profile["concept_mastery"].values()]
        overall = sum(all_masteries) / len(all_masteries) if all_masteries else 0.50
        profile["overall_mastery"] = round(overall, 3)

        # Determine trajectory stage
        for thresh, stage, advice in self.TRAJECTORY_STAGES:
            if overall >= thresh:
                profile["trajectory_stage"] = stage
                profile["trajectory_advice"] = advice
                break

        # 6. Trend calculation
        history = profile.setdefault("history_log", [])
        history.append({
            "concept_id": concept_id,
            "is_correct": is_correct,
            "mastery_after": new_mastery,
            "time_taken": response_time_sec,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if len(history) > 50:
            profile["history_log"] = history[-50:]

        recent = history[-5:]
        if len(recent) >= 4:
            recent_acc = sum(1 for h in recent if h["is_correct"]) / len(recent)
            if recent_acc >= 0.80:
                profile["trend"] = "rapidly_improving" if recent_acc == 1.0 else "improving"
            elif recent_acc <= 0.25:
                profile["trend"] = "declining"
            else:
                profile["trend"] = "stable"

        self.save_profile(student_id, profile)

        return {
            "student_id": student_id,
            "concept_id": concept_id,
            "prior_mastery": prior,
            "new_mastery": new_mastery,
            "overall_mastery": profile["overall_mastery"],
            "trajectory_stage": profile["trajectory_stage"],
            "trajectory_advice": profile["trajectory_advice"],
            "trend": profile["trend"],
            "is_repeated_weakness": concept_id in profile["repeated_mistakes"],
            "mistake_severity": profile["repeated_mistakes"].get(concept_id, {}).get("severity", "none"),
            "speed_category": speed_category,
        }

    def get_weak_topics(self, student_id: str = "student_local", threshold: float = 0.60) -> List[Dict[str, Any]]:
        """
        Returns concepts where student has mastery < threshold or repeated mistakes >= 1.
        """
        profile = self.get_or_create_profile(student_id)
        weak = []
        for cid, cdata in profile.get("concept_mastery", {}).items():
            mistakes = profile.get("repeated_mistakes", {}).get(cid, {}).get("mistake_count", 0)
            mastery = cdata.get("mastery", 0.50)
            if mastery < threshold or mistakes >= 1:
                weak.append({
                    "concept_id": cid,
                    "topic_id": cdata.get("topic_id", "General"),
                    "chapter_id": cdata.get("chapter_id", "General"),
                    "mastery": mastery,
                    "mistakes": mistakes
                })
        weak.sort(key=lambda x: (x["mastery"], -x["mistakes"]))
        return weak


learner_manager = LearnerProfileManager()
