from mastery_engine import calculate_decay, classify_topic_health


def get_study_recommendations(user_id, notebook_id, topics_list, prereqs_list):
    """Prioritize only topics already identified as incorrect by the student."""
    if not topics_list:
        return []

    topic_map = {t["topic_id"]: t for t in topics_list}
    dependents = {t["topic_id"]: [] for t in topics_list}
    prerequisites = {t["topic_id"]: [] for t in topics_list}

    for p in prereqs_list:
        tid = p["topic_id"]
        pid = p["prereq_topic_id"]
        if tid in dependents and pid in dependents:
            dependents[pid].append(tid)
            prerequisites[tid].append(pid)

    scored_items = []

    for t in topics_list:
        tid = t["topic_id"]
        raw_score = t.get("score", 0.0)
        last_reviewed = t.get("last_reviewed_at")
        decay_info = calculate_decay(raw_score, last_reviewed)
        effective_score = decay_info["effective_score"]
        health = classify_topic_health(effective_score)

        urgency = 100.0 - effective_score
        reasons = ["Answered incorrectly; targeted revision recommended"]

        downstream_weak = []
        for dep_id in dependents.get(tid, []):
            dep = topic_map.get(dep_id)
            if dep:
                d = calculate_decay(dep.get("score", 0.0), dep.get("last_reviewed_at"))
                if d["effective_score"] < 65.0:
                    downstream_weak.append(dep["topic_name"])

        if downstream_weak:
            urgency += 25.0 * len(downstream_weak)
            reasons.append(
                f"Prerequisite for weak topic{'s' if len(downstream_weak) > 1 else ''}: "
                f"{', '.join(downstream_weak[:2])}"
            )

        if effective_score < 50.0:
            reasons.append(f"Mastery is currently low ({effective_score:.0f}%)")
        elif effective_score < 65.0:
            reasons.append(f"Understanding is unstable ({effective_score:.0f}% mastery)")
        elif decay_info["is_decayed"]:
            reasons.append(
                f"Decayed by {decay_info['decay_amount']:.0f}% due to inactivity "
                f"({decay_info['days_elapsed']} days since review)"
            )
        elif effective_score < 80.0:
            reasons.append("Needs reinforcement to reach strong mastery")

        scored_items.append({
            "topic_id": tid,
            "topic_name": t["topic_name"],
            "order_index": t.get("order_index", 0),
            "effective_score": effective_score,
            "raw_score": raw_score,
            "decay_info": decay_info,
            "health": health,
            "urgency_score": round(urgency, 1),
            "primary_reason": reasons[0],
            "all_reasons": reasons,
            "downstream_weak": downstream_weak,
            "prerequisites": [
                topic_map[pid]["topic_name"]
                for pid in prerequisites.get(tid, [])
                if pid in topic_map
            ],
        })

    scored_items.sort(key=lambda x: x["urgency_score"], reverse=True)
    return scored_items
