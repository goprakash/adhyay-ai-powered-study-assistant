from datetime import datetime, timedelta

# Confidence update delta matrix based on Specification Sections 4.6 & 9
MASTERY_DELTAS = {
    # (is_correct, confidence_level): delta
    (True, "Confident"): 15.0,
    (True, "Somewhat Sure"): 8.0,
    (True, "Guessed"): 2.0,
    (False, "Confident"): -18.0,       # Severe penalty for false confidence / misconception!
    (False, "Somewhat Sure"): -10.0,
    (False, "Guessed"): -5.0,
}

# Decay configuration (Section 10: Mastery Decay)
GRACE_PERIOD_DAYS = 2        # Days before decay kicks in
DAILY_DECAY_RATE = 1.5       # Percentage dropped per day past grace period
DECAY_FLOOR = 35.0           # Minimum score decay cannot drop below

def calculate_new_mastery(current_score, is_correct, confidence):
    """
    Calculates updated mastery score based on correctness and confidence.
    Clamps between 5.0% and 100.0%.
    """
    key = (bool(is_correct), confidence)
    delta = MASTERY_DELTAS.get(key, 5.0 if is_correct else -8.0)
    new_score = current_score + delta
    return max(5.0, min(100.0, round(new_score, 1)))

def calculate_decay(raw_score, last_reviewed_str):
    """
    Calculates the decayed mastery score based on elapsed time since last review.
    Returns:
        dict: {
            "effective_score": float,
            "days_elapsed": int,
            "decay_amount": float,
            "is_decayed": bool
        }
    """
    if not last_reviewed_str:
        return {
            "effective_score": raw_score,
            "days_elapsed": 0,
            "decay_amount": 0.0,
            "is_decayed": False
        }

    try:
        if isinstance(last_reviewed_str, str):
            # Parse SQLite timestamp format
            last_dt = datetime.strptime(last_reviewed_str[:19], "%Y-%m-%d %H:%M:%S")
        else:
            last_dt = last_reviewed_str

        days_elapsed = (datetime.now() - last_dt).days
        if days_elapsed <= GRACE_PERIOD_DAYS:
            return {
                "effective_score": raw_score,
                "days_elapsed": days_elapsed,
                "decay_amount": 0.0,
                "is_decayed": False
            }

        unprotected_days = days_elapsed - GRACE_PERIOD_DAYS
        decay_amount = round(unprotected_days * DAILY_DECAY_RATE, 1)
        effective_score = max(DECAY_FLOOR, round(raw_score - decay_amount, 1))

        return {
            "effective_score": effective_score,
            "days_elapsed": days_elapsed,
            "decay_amount": round(raw_score - effective_score, 1),
            "is_decayed": decay_amount > 0 and raw_score > DECAY_FLOOR
        }
    except Exception:
        return {
            "effective_score": raw_score,
            "days_elapsed": 0,
            "decay_amount": 0.0,
            "is_decayed": False
        }

def classify_topic_health(effective_score):
    """
    Returns categorization and color indicators for topic mastery.
    """
    if effective_score < 50.0:
        return {
            "category": "Critical Focus",
            "badge_color": "red",
            "emoji": "🔴",
            "status_text": "Weak: Urgent revision needed",
            "is_weak": True
        }
    elif effective_score < 65.0:
        return {
            "category": "Needs Review",
            "badge_color": "orange",
            "emoji": "🟠",
            "status_text": "Review needed to build retention",
            "is_weak": True
        }
    elif effective_score < 80.0:
        return {
            "category": "Reinforcing",
            "badge_color": "gold",
            "emoji": "🟡",
            "status_text": "Good foundation; reinforce with quizzes",
            "is_weak": False
        }
    else:
        return {
            "category": "Mastered",
            "badge_color": "green",
            "emoji": "🟢",
            "status_text": "Strong conceptual understanding",
            "is_weak": False
        }
