from mastery_engine import calculate_decay, classify_topic_health

def get_study_recommendations(user_id, notebook_id, topics_list, prereqs_list):
    """
    Computes prioritized 'What Should I Study Next?' recommendations based on:
    1. Effective (decayed) mastery scores
    2. Prerequisite blockers (knowledge graph)
    3. Time since last review
    
    Returns a sorted list of topic recommendations with clear pedagogical explanations.
    """
    if not topics_list:
        return []

    # Map topics and prereqs
    topic_map = {t['topic_id']: t for t in topics_list}
    
    # Build forward graph (topic -> dependents) and backward graph (topic -> prerequisites)
    dependents = {t['topic_id']: [] for t in topics_list}
    prerequisites = {t['topic_id']: [] for t in topics_list}

    for p in prereqs_list:
        tid = p['topic_id']
        pid = p['prereq_topic_id']
        if tid in dependents and pid in dependents:
            dependents[pid].append(tid)
            prerequisites[tid].append(pid)

    scored_items = []

    for t in topics_list:
        tid = t['topic_id']
        raw_score = t.get('score', 50.0)
        last_reviewed = t.get('last_reviewed_at')

        decay_info = calculate_decay(raw_score, last_reviewed)
        effective_score = decay_info['effective_score']
        health = classify_topic_health(effective_score)

        # Base urgency score (lower mastery = higher urgency, scale 0 to 100)
        urgency = 100.0 - effective_score
        reasons = []

        # 1. Prerequisite Blocker Analysis
        # Check if this topic is a prerequisite for other topics that are weak
        downstream_weak = []
        for dep_id in dependents.get(tid, []):
            dep_topic = topic_map.get(dep_id)
            if dep_topic:
                dep_decay = calculate_decay(dep_topic.get('score', 50.0), dep_topic.get('last_reviewed_at'))
                if dep_decay['effective_score'] < 65.0:
                    downstream_weak.append(dep_topic['topic_name'])

        if downstream_weak:
            # Huge pedagogical multiplier: you cannot fix downstream topics without fixing prerequisites!
            urgency += 25.0 * len(downstream_weak)
            reasons.append(f"Prerequisite for weak topic{'s' if len(downstream_weak) > 1 else ''}: {', '.join(downstream_weak[:2])}")

        # 2. Performance-based urgency
        if effective_score < 50.0:
            reasons.append(f"Recent quiz performance was critically weak ({effective_score:.0f}%)")
        elif effective_score < 65.0:
            reasons.append(f"Understanding is unstable ({effective_score:.0f}% mastery)")
        elif decay_info['is_decayed']:
            reasons.append(f"Decayed by {decay_info['decay_amount']:.0f}% due to inactivity ({decay_info['days_elapsed']} days since review)")
        elif effective_score < 80.0:
            reasons.append("Needs reinforcement to reach strong mastery")
        else:
            reasons.append("Topic well understood; maintain periodic review")

        # 3. Check if this topic has unmastered prerequisites itself
        # If prerequisite is severely weak, this topic should wait until prereq is addressed!
        prereq_blockers = []
        for pid in prerequisites.get(tid, []):
            pr_topic = topic_map.get(pid)
            if pr_topic:
                pr_decay = calculate_decay(pr_topic.get('score', 50.0), pr_topic.get('last_reviewed_at'))
                if pr_decay['effective_score'] < 55.0:
                    prereq_blockers.append(pr_topic['topic_name'])

        if prereq_blockers:
            # Dampen urgency slightly so the earlier prerequisite is suggested first!
            urgency -= 15.0
            reasons.insert(0, f"⚠️ Consider reviewing foundational '{prereq_blockers[0]}' first")

        scored_items.append({
            "topic_id": tid,
            "topic_name": t['topic_name'],
            "order_index": t.get('order_index', 0),
            "effective_score": effective_score,
            "raw_score": raw_score,
            "decay_info": decay_info,
            "health": health,
            "urgency_score": round(urgency, 1),
            "primary_reason": reasons[0] if reasons else "Recommended review",
            "all_reasons": reasons,
            "downstream_weak": downstream_weak,
            "prerequisites": [topic_map[pid]['topic_name'] for pid in prerequisites.get(tid, []) if pid in topic_map]
        })

    # Sort primarily by urgency descending
    scored_items.sort(key=lambda x: x['urgency_score'], reverse=True)
    return scored_items
