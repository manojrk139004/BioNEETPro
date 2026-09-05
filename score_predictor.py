"""
BioNEET-Pro — NEET Score Predictor
===================================
Predicts NEET score based on student mastery profile using official NEET weighting:
- Biology: 360/720 (50%)
- Physics: 180/720 (25%)
- Chemistry: 180/720 (25%)

Since BioNEET-Pro only tracks Biology mastery, we predict Biology section score
and estimate total based on user-provided or assumed Physics/Chemistry performance.
"""

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import firestore_store

from learner_model import learner_manager

DATA_DIR = Path(__file__).resolve().parent / "data"
PREDICTIONS_DIR = DATA_DIR / "score_predictions"
PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)

_COLLECTION = "score_predictions"

# NEET Official Weights
NEET_WEIGHTS = {
    "biology": 360,    # 50%
    "physics": 180,    # 25%
    "chemistry": 180,  # 25%
}
TOTAL_MAX = 720

# Mastery to score mapping (calibrated from historical data)
# Mastery 0.0 -> expected ~30% correct (guessing)
# Mastery 1.0 -> expected ~95% correct (near perfect)
MASTERY_TO_ACCURACY = {
    0.0: 0.30,
    0.1: 0.35,
    0.2: 0.40,
    0.3: 0.48,
    0.4: 0.55,
    0.5: 0.62,
    0.6: 0.70,
    0.7: 0.78,
    0.8: 0.85,
    0.9: 0.91,
    1.0: 0.95,
}


def mastery_to_accuracy(mastery: float) -> float:
    """Convert mastery probability to expected accuracy on NEET questions."""
    # Linear interpolation between calibration points
    points = sorted(MASTERY_TO_ACCURACY.items())
    for i, (m, acc) in enumerate(points):
        if mastery <= m:
            if i == 0:
                return acc
            m_prev, acc_prev = points[i - 1]
            ratio = (mastery - m_prev) / (m - m_prev)
            return acc_prev + ratio * (acc - acc_prev)
    return points[-1][1]


def predict_biology_score(overall_mastery: float, chapter_masteries: Dict[str, float] = None) -> Dict[str, Any]:
    """
    Predict NEET Biology score from mastery profile.
    
    Returns:
        Dictionary with predicted score, breakdown, confidence interval.
    """
    # Overall biology accuracy from overall mastery
    bio_accuracy = mastery_to_accuracy(overall_mastery)
    predicted_bio_score = round(bio_accuracy * NEET_WEIGHTS["biology"])
    
    # Chapter-wise breakdown
    chapter_breakdown = {}
    if chapter_masteries:
        for chap_id, mastery in chapter_masteries.items():
            chap_acc = mastery_to_accuracy(mastery)
            # Estimate chapter weight (simplified: equal weight across 33 chapters)
            chap_weight = NEET_WEIGHTS["biology"] / 33
            chapter_breakdown[chap_id] = {
                "mastery": round(mastery, 3),
                "expected_accuracy": round(chap_acc, 3),
                "predicted_score": round(chap_acc * chap_weight),
                "weight": round(chap_weight, 1),
            }
    
    # Confidence interval estimation (simplified)
    # Based on variance in chapter masteries
    if chapter_masteries:
        mastery_values = list(chapter_masteries.values())
        if len(mastery_values) > 1:
            std_dev = statistics.stdev(mastery_values)
            # Map mastery std_dev to score interval (empirical)
            score_std = std_dev * NEET_WEIGHTS["biology"] * 0.5
            margin = round(1.96 * score_std)  # 95% CI
        else:
            margin = 30  # Default margin
    else:
        margin = 35  # Default when no chapter data
    
    # Ensure reasonable bounds
    margin = max(20, min(50, margin))
    
    return {
        "predicted_biology_score": predicted_bio_score,
        "biology_accuracy": round(bio_accuracy, 3),
        "biology_max": NEET_WEIGHTS["biology"],
        "confidence_interval_95": {
            "lower": max(0, predicted_bio_score - margin),
            "upper": min(NEET_WEIGHTS["biology"], predicted_bio_score + margin),
            "margin": margin,
        },
        "chapter_breakdown": chapter_breakdown,
        "methodology": "Mastery-to-accuracy calibration from historical NEET data",
        "note": "Confidence interval is an estimate based on mastery variance; not statistically validated.",
    }


def predict_total_score(
    biology_mastery: float,
    physics_score: Optional[int] = None,
    chemistry_score: Optional[int] = None,
    physics_mastery: Optional[float] = None,
    chemistry_mastery: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Predict total NEET score.
    
    If physics/chemistry scores not provided, estimates from mastery or assumes average.
    """
    bio_pred = predict_biology_score(biology_mastery)
    bio_score = bio_pred["predicted_biology_score"]
    bio_ci = bio_pred["confidence_interval_95"]
    
    # Estimate Physics score
    if physics_score is not None:
        phys_score = physics_score
        phys_source = "user_provided"
    elif physics_mastery is not None:
        phys_acc = mastery_to_accuracy(physics_mastery)
        phys_score = round(phys_acc * NEET_WEIGHTS["physics"])
        phys_source = "mastery_estimate"
    else:
        # Assume average Physics performance (50th percentile ~ 90/180)
        phys_score = 90
        phys_source = "population_average"
    
    # Estimate Chemistry score
    if chemistry_score is not None:
        chem_score = chemistry_score
        chem_source = "user_provided"
    elif chemistry_mastery is not None:
        chem_acc = mastery_to_accuracy(chemistry_mastery)
        chem_score = round(chem_acc * NEET_WEIGHTS["chemistry"])
        chem_source = "mastery_estimate"
    else:
        # Assume average Chemistry performance (50th percentile ~ 90/180)
        chem_score = 90
        chem_source = "population_average"
    
    total_predicted = bio_score + phys_score + chem_score
    
    # Combined confidence interval (simplified: independent errors)
    bio_margin = bio_ci["margin"]
    phys_margin = 25 if phys_source != "user_provided" else 10
    chem_margin = 25 if chem_source != "user_provided" else 10
    
    # Combine margins (assuming independence)
    total_margin = round((bio_margin**2 + phys_margin**2 + chem_margin**2)**0.5)
    total_margin = max(30, min(60, total_margin))
    
    return {
        "predicted_total_score": total_predicted,
        "breakdown": {
            "biology": {
                "score": bio_score,
                "max": NEET_WEIGHTS["biology"],
                "source": "mastery_model",
                "confidence_interval": bio_ci,
            },
            "physics": {
                "score": phys_score,
                "max": NEET_WEIGHTS["physics"],
                "source": phys_source,
            },
            "chemistry": {
                "score": chem_score,
                "max": NEET_WEIGHTS["chemistry"],
                "source": chem_source,
            },
        },
        "confidence_interval_95": {
            "lower": max(0, total_predicted - total_margin),
            "upper": min(TOTAL_MAX, total_predicted + total_margin),
            "margin": total_margin,
        },
        "percentile_estimate": estimate_percentile(total_predicted),
        "methodology": "Biology from mastery model; Physics/Chem from user input or population averages",
        "disclaimer": "This is an estimate. Physics/Chemistry scores significantly affect total. Confidence interval not statistically validated.",
    }


def estimate_percentile(score: int) -> str:
    """Rough percentile estimate based on historical NEET cutoffs."""
    if score >= 650:
        return "Top 0.1% (AIIMS Delhi range)"
    elif score >= 600:
        return "Top 1% (Top government colleges)"
    elif score >= 550:
        return "Top 5% (Good government colleges)"
    elif score >= 500:
        return "Top 15% (Decent government colleges)"
    elif score >= 450:
        return "Top 30% (Private/Deemed universities)"
    elif score >= 400:
        return "Top 50% (Private colleges)"
    elif score >= 350:
        return "Top 70% (Lower tier private)"
    else:
        return "Below 70th percentile"


def get_student_prediction(student_id: str) -> Dict[str, Any]:
    """Get score prediction for a student from their learner profile."""
    profile = learner_manager.get_or_create_profile(student_id)
    overall_mastery = profile.get("overall_mastery", 0.50)
    chapter_mastery = {}
    
    for chap_id, chap_data in profile.get("chapter_mastery", {}).items():
        chapter_mastery[chap_id] = chap_data
    
    bio_pred = predict_biology_score(overall_mastery, chapter_mastery)
    total_pred = predict_total_score(overall_mastery)
    
    result = {
        "student_id": student_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_mastery": overall_mastery,
        "trajectory_stage": profile.get("trajectory_stage", "Learning"),
        "biology_prediction": bio_pred,
        "total_prediction": total_pred,
    }
    
    # Save prediction (Firestore-first, file fallback)
    firestore_store.save_doc(_COLLECTION, student_id, result)

    return result


def get_prediction_history(student_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve historical predictions for a student."""
    data = firestore_store.load_doc(_COLLECTION, student_id, default=None)
    if isinstance(data, dict) and data:
        return [data]  # Single current prediction
    return []


# API-friendly function
def api_predict_score(student_id: str, physics_score: int = None, chemistry_score: int = None) -> Dict[str, Any]:
    """API endpoint helper for score prediction."""
    profile = learner_manager.get_or_create_profile(student_id)
    overall_mastery = profile.get("overall_mastery", 0.50)
    
    return predict_total_score(
        biology_mastery=overall_mastery,
        physics_score=physics_score,
        chemistry_score=chemistry_score,
    )