def get_custom_css():
    return """
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&display=swap');

    /* Calm & Peaceful Study Notebook Theme */
    .stApp {
        background-color: #FBFBFA;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #2D3748;
    }

    /* Distraction-free typography */
    h1, h2, h3 {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 600;
        color: #1A202C;
        letter-spacing: -0.02em;
    }

    .subdued-text {
        color: #718096;
        font-size: 0.95rem;
        margin-top: -0.4rem;
        margin-bottom: 1.2rem;
    }

    /* Paper-like card styling */
    .adhyay-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.3rem 1.6rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03), 0 2px 6px rgba(0, 0, 0, 0.02);
    }

    /* Notebook selector shelf card */
    .notebook-shelf-card {
        background-color: #FFFFFF;
        border: 1.5px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.8rem;
        transition: all 0.2s ease;
    }
    .notebook-shelf-card.active {
        border-color: #0D9488;
        background-color: #F0FDFA;
    }

    /* Hero Recommendation Card */
    .adhyay-hero-card {
        background: linear-gradient(135deg, #F0FDF4 0%, #FFFFFF 100%);
        border: 1.5px solid #86EFAC;
        border-radius: 14px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
    }

    .adhyay-weak-card {
        background: linear-gradient(135deg, #FFF1F2 0%, #FFFFFF 100%);
        border: 1.5px solid #FECDD3;
        border-radius: 14px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
    }

    /* Clean Badges */
    .badge-pill {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-critical { background-color: #FEE2E2; color: #991B1B; }
    .badge-warning { background-color: #FEF3C7; color: #92400E; }
    .badge-progress { background-color: #E0E7FF; color: #3730A3; }
    .badge-mastered { background-color: #D1FAE5; color: #065F46; }

    /* Flashcard presentation */
    .flashcard-box {
        background-color: #FFFFFF;
        border: 1.5px solid #E2E8F0;
        border-radius: 16px;
        padding: 2.5rem 2rem;
        text-align: center;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        margin: 1.5rem 0;
    }

    /* Progress meter */
    .meter-container {
        width: 100%;
        background-color: #EDF2F7;
        border-radius: 8px;
        height: 9px;
        overflow: hidden;
        margin: 0.35rem 0;
    }
    .meter-fill {
        height: 100%;
        border-radius: 8px;
        transition: width 0.3s ease;
    }

    /* Buttons */
    div.stButton > button {
        border-radius: 8px;
        font-weight: 500;
        border: 1px solid #CBD5E1;
        background-color: #FFFFFF;
        color: #334155;
        transition: all 0.15s ease;
    }
    div.stButton > button:hover {
        border-color: #94A3B8;
        background-color: #F8FAFC;
    }

    /* User pill in sidebar */
    .user-pill {
        background-color: #F1F5F9;
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
        font-size: 0.85rem;
        color: #334155;
        margin-bottom: 0.8rem;
    }
</style>
"""
