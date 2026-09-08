import streamlit as st

def render_header(title, subtitle=None):
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(f"<p class='subdued-text'>{subtitle}</p>", unsafe_allow_html=True)

def render_mastery_bar(score, topic_name=None, decay_info=None):
    score = max(0.0, min(100.0, score))
    if score < 50:
        color = "#EF4444" # red
        status = "🔴 Critical Focus"
    elif score < 65:
        color = "#F59E0B" # orange
        status = "🟠 Needs Review"
    elif score < 80:
        color = "#6366F1" # indigo/blue
        status = "🟡 Reinforcing"
    else:
        color = "#10B981" # green
        status = "🟢 Mastered"

    decay_badge = ""
    if decay_info and decay_info.get("is_decayed"):
        decay_badge = f"<span class='badge-pill badge-warning' title='Score decayed by {decay_info['decay_amount']:.0f}% over {decay_info['days_elapsed']} days'>⏳ Stale (-{decay_info['decay_amount']:.0f}%)</span>"

    header_html = f"""
    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 4px;">
        <span style="font-weight: 500; font-size: 0.95rem;">{topic_name or ''} {decay_badge}</span>
        <span style="font-weight: 600; font-size: 0.95rem; color: {color};">{score:.0f}% <span style="font-weight: normal; font-size: 0.8rem; color: #64748B;">({status})</span></span>
    </div>
    """
    meter_html = f"""
    <div class="meter-container">
        <div class="meter-fill" style="width: {score}%; background-color: {color};"></div>
    </div>
    """
    st.markdown(f"{header_html}{meter_html}", unsafe_allow_html=True)

def render_recommendation_card(rec, index=1):
    health = rec['health']
    downstream_txt = ""
    if rec['downstream_weak']:
        downstream_txt = f"<p style='margin: 4px 0 0 0; font-size: 0.85rem; color: #DC2626;'><strong>Prerequisite blocker:</strong> Essential for {', '.join(rec['downstream_weak'])}</p>"

    html = f"""
    <div class="adhyay-card" style="border-left: 5px solid {'#EF4444' if rec['effective_score'] < 50 else '#F59E0B' if rec['effective_score'] < 65 else '#10B981'};">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h4 style="margin: 0; font-size: 1.1rem;">#{index}. {rec['topic_name']}</h4>
            <span style="font-weight: 700; font-size: 1.1rem;">{rec['effective_score']:.0f}% <span style="font-size: 0.8rem; font-weight: normal; color: #64748B;">mastery</span></span>
        </div>
        <p style="margin: 6px 0 0 0; color: #475569; font-size: 0.95rem;"><strong>Why study this:</strong> {rec['primary_reason']}</p>
        {downstream_txt}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
