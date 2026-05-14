"""
app.py — Verite Research Chatbot UI (rebuilt)
Run with: streamlit run app.py
"""

import uuid
import base64
import streamlit as st
from chatbot import VeriteChatbot

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Veri — Verite Research",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

/* ── Palette
   Porcelain:       #FBFEF9
   Brown Red:       #9E2B25
   Graphite:        #272B28
   Deep Space Blue: #283B53
   Deep Crimson:    #921124
── */

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #272B28;
    color: #FBFEF9;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #1e211f !important;
    border-right: 1px solid rgba(251,254,249,0.07);
}
[data-testid="stSidebar"] * { color: rgba(251,254,249,0.7) !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #FBFEF9 !important; }

/* ── Main content area ── */
.main .block-container { padding: 1.5rem 2rem; max-width: 900px; }

/* ── Logo ── */
.veri-logo {
    display: flex; align-items: center; gap: 10px;
    padding: 1rem 0 1.5rem 0;
}
.veri-logo-mark {
    width: 36px; height: 36px; background: #9E2B25;
    border-radius: 6px; display: flex; align-items: center;
    justify-content: center; font-weight: 700; font-size: 15px;
    color: #FBFEF9; flex-shrink: 0;
}
.veri-logo-text { line-height: 1.2; }
.veri-logo-title { font-size: 17px; font-weight: 600; color: #FBFEF9; }
.veri-logo-sub   { font-size: 12px; color: rgba(251,254,249,0.35); }

/* ── Status pill ── */
.status-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(40,59,83,0.35); border: 1px solid rgba(40,59,83,0.7);
    color: #7fa8d0; font-size: 12px; padding: 4px 12px;
    border-radius: 20px; margin-bottom: 1.2rem;
}
.status-dot { width: 6px; height: 6px; background: #7fa8d0; border-radius: 50%; }

/* ── Building pill ── */
.building-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(158,43,37,0.1); border: 1px solid rgba(158,43,37,0.3);
    color: #c45550; font-size: 12px; padding: 4px 12px;
    border-radius: 20px; margin-bottom: 1.2rem;
}

/* ── Chat bubbles ── */
.chat-user {
    background: #283B53;
    border: 1px solid rgba(40,59,83,0.9);
    color: #FBFEF9;
    padding: 0.85rem 1.1rem;
    border-radius: 16px 16px 4px 16px;
    margin: 0.6rem 0 0.6rem 18%;
    font-size: 0.93rem; line-height: 1.6;
}
.chat-bot {
    background: #1e211f;
    border: 1px solid rgba(251,254,249,0.08);
    color: rgba(251,254,249,0.88);
    padding: 0.9rem 1.1rem;
    border-radius: 4px 16px 16px 16px;
    margin: 0.6rem 18% 0.3rem 0;
    font-size: 0.93rem; line-height: 1.7;
}
.chat-bot p { margin: 0 0 0.5rem 0; }

/* ── Citation tag ── */
.citation-tag {
    display: inline-flex; align-items: center; gap: 5px;
    background: rgba(146,17,36,0.12); border: 1px solid rgba(146,17,36,0.3);
    color: #c45550; font-size: 11px; padding: 3px 10px;
    border-radius: 12px; margin-top: 8px; font-weight: 500;
}

/* ── Warning tag ── */
.faith-warn {
    display: inline-flex; align-items: center; gap: 5px;
    background: rgba(255,165,0,0.08); border: 1px solid rgba(255,165,0,0.2);
    color: #e6a030; font-size: 11px; padding: 3px 10px;
    border-radius: 12px; margin-top: 6px;
}

/* ── Score bar ── */
.score-bar-wrap { display: flex; align-items: center; gap: 8px; margin-top: 6px; }
.score-bar-bg   { flex: 1; height: 3px; background: rgba(251,254,249,0.08); border-radius: 2px; max-width: 100px; }
.score-bar-fill { height: 3px; background: #283B53; border-radius: 2px; }
.score-label    { font-size: 11px; color: rgba(251,254,249,0.28); }

/* ── Suggestions ── */
.suggestions-wrap { margin: 0.4rem 0 1rem 0; display: flex; flex-wrap: wrap; gap: 6px; }
.suggestion-btn {
    background: rgba(40,59,83,0.2);
    border: 1px solid rgba(40,59,83,0.55);
    color: #7fa8d0; font-size: 12px;
    padding: 5px 12px; border-radius: 14px;
    cursor: pointer; transition: all 0.2s;
}
.suggestion-btn:hover { background: rgba(40,59,83,0.4); }

/* ── Input ── */
.stTextInput input {
    background: #1e211f !important;
    border: 1px solid rgba(251,254,249,0.12) !important;
    color: #FBFEF9 !important;
    border-radius: 10px !important;
    font-size: 14px !important;
    padding: 0.7rem 1rem !important;
}
.stTextInput input:focus {
    border-color: rgba(158,43,37,0.5) !important;
    box-shadow: 0 0 0 2px rgba(158,43,37,0.12) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: #9E2B25 !important;
    color: #FBFEF9 !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: background 0.2s !important;
}
.stButton > button:hover { background: #7a2019 !important; }

/* ── Divider ── */
hr { border-color: rgba(251,254,249,0.07) !important; }

/* ── Ticker ── */
@keyframes ticker { 0%{transform:translateX(0)} 100%{transform:translateX(-50%)} }
.ticker-wrap {
    overflow: hidden;
    border-top: 1px solid rgba(251,254,249,0.05);
    border-bottom: 1px solid rgba(251,254,249,0.05);
    padding: 8px 0; margin-bottom: 1.2rem;
    background: rgba(0,0,0,0.15);
}
.ticker-inner {
    display: flex; gap: 48px; width: max-content;
    animation: ticker 20s linear infinite;
}
.ticker-item {
    font-size: 11px; color: rgba(251,254,249,0.22);
    letter-spacing: 0.08em; text-transform: uppercase;
    white-space: nowrap; display: flex; align-items: center; gap: 6px;
}
.ticker-dot { width: 4px; height: 4px; background: #9E2B25; border-radius: 50%; }

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: #1e211f !important;
    border: 1px solid rgba(251,254,249,0.12) !important;
    color: #FBFEF9 !important;
    border-radius: 8px !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: #1e211f !important;
    border: 1px dashed rgba(158,43,37,0.35) !important;
    border-radius: 10px !important;
}

/* ── Rewritten query pill ── */
.rewrite-pill {
    font-size: 11px; color: rgba(251,254,249,0.28);
    margin-bottom: 4px; font-style: italic;
}

/* ── Export link ── */
.export-link {
    display: block; text-align: center;
    background: rgba(251,254,249,0.04);
    border: 1px solid rgba(251,254,249,0.1);
    border-radius: 8px; padding: 8px;
    color: rgba(251,254,249,0.55); font-size: 13px; text-decoration: none;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }

/* ── Landing page ── */
@keyframes fadeUp { from { opacity: 0; transform: translateY(18px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pulse-ring { 0% { transform: scale(1); opacity: 0.35; } 100% { transform: scale(1.65); opacity: 0; } }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-9px); } }

.lp-nav { display: flex; align-items: center; justify-content: space-between; padding: 14px 36px; border-bottom: 0.5px solid rgba(251,254,249,0.07); background: #1e211f; animation: fadeUp 0.4s ease both; }
.lp-nav-logo { display: flex; align-items: center; gap: 9px; }
.lp-nav-mark { width: 30px; height: 30px; background: #9E2B25; border-radius: 5px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 13px; color: #FBFEF9; }
.lp-nav-name { font-size: 15px; font-weight: 600; color: #FBFEF9; }
.lp-nav-links { display: flex; gap: 24px; }
.lp-nav-links a { color: rgba(251,254,249,0.38); font-size: 13px; text-decoration: none; position: relative; padding-bottom: 2px; transition: color 0.2s; }
.lp-nav-links a::after { content: ''; position: absolute; bottom: 0; left: 0; width: 0; height: 1px; background: #9E2B25; transition: width 0.28s; }
.lp-nav-links a:hover { color: #FBFEF9; }
.lp-nav-links a:hover::after { width: 100%; }

.lp-hero { padding: 56px 36px 48px; display: flex; align-items: center; justify-content: space-between; gap: 32px; }
.lp-hero-text { flex: 1; animation: fadeUp 0.5s ease 0.1s both; }
.lp-tag { display: inline-block; background: rgba(158,43,37,0.12); border: 0.5px solid rgba(158,43,37,0.35); color: #c45550; font-size: 11px; padding: 4px 12px; border-radius: 20px; margin-bottom: 18px; letter-spacing: 0.06em; text-transform: uppercase; }
.lp-h1 { font-size: 34px; font-weight: 600; line-height: 1.22; margin-bottom: 15px; color: #FBFEF9; }
.lp-h1 .accent { color: #9E2B25; }
.lp-sub { color: rgba(251,254,249,0.42); font-size: 14px; line-height: 1.75; max-width: 400px; margin-bottom: 26px; }
.lp-btns { display: flex; gap: 10px; }
.lp-btn-p { background: #9E2B25; color: #FBFEF9; border: none; padding: 10px 22px; border-radius: 7px; font-size: 13px; cursor: pointer; transition: background 0.2s, transform 0.15s; }
.lp-btn-p:hover { background: #7a2019; transform: translateY(-2px); }
.lp-btn-o { background: transparent; color: #FBFEF9; border: 0.5px solid rgba(251,254,249,0.22); padding: 10px 22px; border-radius: 7px; font-size: 13px; cursor: pointer; transition: all 0.2s; }
.lp-btn-o:hover { border-color: rgba(251,254,249,0.5); background: rgba(251,254,249,0.04); transform: translateY(-2px); }

.lp-hero-vis { flex: 0 0 190px; display: flex; align-items: center; justify-content: center; animation: fadeUp 0.6s ease 0.25s both; }
.lp-orb-wrap { position: relative; width: 136px; height: 136px; display: flex; align-items: center; justify-content: center; animation: float 4s ease-in-out infinite; }
.lp-orb { width: 84px; height: 84px; background: #9E2B25; border-radius: 50%; display: flex; align-items: center; justify-content: center; position: relative; z-index: 2; font-size: 32px; }
.lp-ring { position: absolute; width: 84px; height: 84px; border-radius: 50%; border: 1.5px solid #9E2B25; animation: pulse-ring 2.4s ease-out infinite; }
.lp-ring:nth-child(2) { animation-delay: 0.8s; }
.lp-ring:nth-child(3) { animation-delay: 1.6s; }

.lp-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; background: rgba(251,254,249,0.06); border-top: 0.5px solid rgba(251,254,249,0.06); }
.lp-stat { background: #272B28; padding: 24px 28px; }
.lp-stat-num { font-size: 28px; font-weight: 600; color: #FBFEF9; margin-bottom: 3px; }
.lp-stat-num span { color: #9E2B25; }
.lp-stat-label { font-size: 11px; color: rgba(251,254,249,0.32); letter-spacing: 0.04em; }

.lp-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; background: rgba(251,254,249,0.06); border-top: 0.5px solid rgba(251,254,249,0.06); }
.lp-card { background: #1e211f; padding: 24px 20px; cursor: pointer; transition: background 0.22s; position: relative; overflow: hidden; }
.lp-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: #9E2B25; transform: scaleX(0); transform-origin: left; transition: transform 0.28s ease; border-radius: 0; }
.lp-card:hover { background: #252a26; }
.lp-card:hover::before { transform: scaleX(1); }
.lp-card-icon { width: 38px; height: 38px; background: rgba(158,43,37,0.1); border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-bottom: 12px; font-size: 18px; transition: background 0.22s; }
.lp-card:hover .lp-card-icon { background: rgba(158,43,37,0.2); }
.lp-card h3 { font-size: 13px; font-weight: 500; margin-bottom: 7px; color: #FBFEF9; }
.lp-card p { font-size: 12px; color: rgba(251,254,249,0.38); line-height: 1.6; }
.lp-card-arrow { margin-top: 14px; color: #9E2B25; font-size: 12px; opacity: 0; transform: translateX(-6px); transition: opacity 0.22s, transform 0.22s; display: flex; align-items: center; gap: 4px; }
.lp-card:hover .lp-card-arrow { opacity: 1; transform: translateX(0); }

.lp-main-cta { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Init chatbot ──────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading knowledge base…")
def load_bot():
    bot = VeriteChatbot()
    bot.build_knowledge_base()
    return bot

bot = load_bot()

# ── Session state ─────────────────────────────────────────────────────────────
if "messages"   not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "prefill"    not in st.session_state:
    st.session_state.prefill = ""
if "page"       not in st.session_state:
    st.session_state.page = "home"

chunk_count = bot.get_chunk_count()
pub_list    = bot.get_publication_list()

# ══════════════════════════════════════════════════════════════════════════════
# LANDING PAGE
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "home":

    # Hide sidebar on landing page
    st.markdown("<style>[data-testid='stSidebar']{display:none}</style>", unsafe_allow_html=True)

    topics = ["Budget Analysis 2026", "Anti-Corruption Law", "Youth Employment",
              "Private Sector Governance", "Sri Lanka Fiscal Policy", "Supply Chain Audits",
              "Budget Analysis 2026", "Anti-Corruption Law", "Youth Employment",
              "Private Sector Governance", "Sri Lanka Fiscal Policy", "Supply Chain Audits"]
    ticker_items = "".join(
        f'<div class="ticker-item"><div class="ticker-dot"></div>{t}</div>' for t in topics
    )

    st.markdown(f"""
    <div style="background:#272B28; border-radius:12px; overflow:hidden; font-family:'Inter',sans-serif;">

      <!-- Nav -->
      <nav class="lp-nav">
        <div class="lp-nav-logo">
          <div class="lp-nav-mark">V</div>
          <div class="lp-nav-name">Verité Research</div>
        </div>
        <div class="lp-nav-links">
          <a href="https://www.veriteresearch.org/services-and-products/research-outputs/" target="_blank">Research</a>
          <a href="https://www.veriteresearch.org/services-and-products/research-outputs/" target="_blank">Publications</a>
          <a href="https://www.veriteresearch.org/about/" target="_blank">About</a>
        </div>
      </nav>

      <!-- Hero -->
      <section class="lp-hero">
        <div class="lp-hero-text">
          <div class="lp-tag">AI-powered research assistant</div>
          <div class="lp-h1">Insight from<br><span class="accent">evidence.</span><br>Answers from data.</div>
          <div class="lp-sub">Veri draws from Verité Research publications to answer your questions on Sri Lanka's budget, anti-corruption law, and youth employment.</div>
        </div>
        <div class="lp-hero-vis">
          <div class="lp-orb-wrap">
            <div class="lp-ring"></div>
            <div class="lp-ring"></div>
            <div class="lp-ring"></div>
            <div class="lp-orb">📚</div>
          </div>
        </div>
      </section>

      <!-- Ticker -->
      <div class="ticker-wrap">
        <div class="ticker-inner">{ticker_items}</div>
      </div>

      <!-- Stats -->
      <div class="lp-stats">
        <div class="lp-stat">
          <div class="lp-stat-num">{len(pub_list)}<span>+</span></div>
          <div class="lp-stat-label">Publications indexed</div>
        </div>
        <div class="lp-stat">
          <div class="lp-stat-num">{chunk_count}<span>+</span></div>
          <div class="lp-stat-label">Knowledge chunks</div>
        </div>
        <div class="lp-stat">
          <div class="lp-stat-num">0<span>ms</span></div>
          <div class="lp-stat-label">Hallucinations (by design)</div>
        </div>
      </div>

      <!-- Topic cards -->
      <div class="lp-cards">
        <div class="lp-card" id="card-corruption">
          <div class="lp-card-icon">🛡️</div>
          <h3>Anti-corruption</h3>
          <p>Gaps in Sri Lanka's private sector legal framework and international benchmarks.</p>
          <div class="lp-card-arrow">→ Explore</div>
        </div>
        <div class="lp-card" id="card-budget">
          <div class="lp-card-icon">📊</div>
          <h3>Budget 2026</h3>
          <p>Revenue projections, tax policy changes, and fiscal targets for the year ahead.</p>
          <div class="lp-card-arrow">→ Explore</div>
        </div>
        <div class="lp-card" id="card-youth">
          <div class="lp-card-icon">👥</div>
          <h3>Youth employment</h3>
          <p>Why social contacts fail unemployed youth and what actually works instead.</p>
          <div class="lp-card-arrow">→ Explore</div>
        </div>
      </div>

    </div>
    """, unsafe_allow_html=True)

    # Streamlit buttons that drive navigation (styled to blend with landing page)
    st.markdown("<div style='height:1px;background:rgba(251,254,249,0.06);'></div>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        if st.button("🔍  Start asking →", use_container_width=True, key="lp_start"):
            st.session_state.page = "chat"
            st.rerun()
    with col2:
        if st.button("Anti-corruption", use_container_width=True, key="lp_card1"):
            st.session_state.prefill = "What gaps does Verite identify in Sri Lanka's anti-corruption laws?"
            st.session_state.page = "chat"
            st.rerun()
    with col3:
        if st.button("Budget 2026", use_container_width=True, key="lp_card2"):
            st.session_state.prefill = "What does the State of the Budget 2026 say about government revenue?"
            st.session_state.page = "chat"
            st.rerun()
    with col4:
        if st.button("Youth employment", use_container_width=True, key="lp_card3"):
            st.session_state.prefill = "What job search methods work best for unemployed youth in Sri Lanka?"
            st.session_state.page = "chat"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# CHAT PAGE
# ══════════════════════════════════════════════════════════════════════════════
else:

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
        <div class="veri-logo">
          <div class="veri-logo-mark">V</div>
          <div class="veri-logo-text">
            <div class="veri-logo-title">Veri</div>
            <div class="veri-logo-sub">Verite Research Assistant</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("← Back to home", use_container_width=True, key="back_home"):
            st.session_state.page = "home"
            st.rerun()

        st.markdown("---")

        st.markdown("### Filter by publication")
        filter_opt   = ["All publications"] + pub_list
        selected     = st.selectbox("Search within", filter_opt, label_visibility="collapsed")
        filter_title = None if selected == "All publications" else selected

        st.markdown("---")

        # Upload paper
        st.markdown("### Add a publication")
        uploaded = st.file_uploader("Upload a PDF", type="pdf", label_visibility="collapsed")
        if uploaded:
            col1, col2 = st.columns(2)
            with col1:
                new_title = st.text_input("Title", placeholder="Paper title")
            with col2:
                new_year  = st.text_input("Year",  placeholder="2025")
            new_url = st.text_input("URL (optional)", placeholder="https://...")
            if st.button("Add to knowledge base", use_container_width=True):
                if new_title and new_year:
                    bot.add_paper_async(
                        uploaded.read(), new_title.strip(), new_year.strip(), new_url.strip()
                    )
                    st.success(f"Indexing started! '{new_title}' will be ready in a moment.")
                else:
                    st.warning("Please enter a title and year.")

        if bot.is_building():
            st.markdown(f'<div class="building-pill">⟳ {bot.build_progress()}</div>', unsafe_allow_html=True)

        st.markdown("---")

        # Export
        if st.session_state.messages:
            st.markdown("### Export")
            lines = []
            for m in st.session_state.messages:
                role = "You" if m["role"] == "user" else "Veri"
                lines.append(f"**{role}:** {m['content']}")
                if m.get("citation"):
                    lines.append(f"*Source: {m['citation']}*")
                lines.append("")
            md_export = "\n".join(lines)
            b64 = base64.b64encode(md_export.encode()).decode()
            st.markdown(
                f'<a href="data:text/markdown;base64,{b64}" download="veri_conversation.md" '
                f'style="display:block;text-align:center;background:rgba(255,255,255,0.05);'
                f'border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:8px;'
                f'color:rgba(255,255,255,0.6);font-size:13px;text-decoration:none;">'
                f'⬇ Download as Markdown</a>',
                unsafe_allow_html=True
            )

        st.markdown("---")

        st.markdown(f"""
        <div style="font-size:12px; color:rgba(255,255,255,0.3); line-height:1.8;">
          Session: <code style="color:rgba(255,255,255,0.5)">{st.session_state.session_id}</code><br>
          Chunks indexed: <strong style="color:rgba(255,255,255,0.6)">{chunk_count}</strong><br>
          Publications: <strong style="color:rgba(255,255,255,0.6)">{len(pub_list)}</strong>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.messages:
            st.markdown("")
            if st.button("🗑 Clear conversation", use_container_width=True):
                st.session_state.messages = []
                st.session_state.prefill  = ""
                st.rerun()

    # ── Main chat area ────────────────────────────────────────────────────────

    if bot.is_building():
        st.markdown('<div class="building-pill">⟳ Indexing new paper in background…</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="status-pill"><div class="status-dot"></div>'
            f'{chunk_count} chunks · {len(pub_list)} publications · hybrid search active</div>',
            unsafe_allow_html=True
        )

    topics = ["Budget Analysis 2026", "Anti-Corruption Law", "Youth Employment",
              "Private Sector Governance", "Sri Lanka Fiscal Policy", "Supply Chain Audits",
              "Budget Analysis 2026", "Anti-Corruption Law", "Youth Employment",
              "Private Sector Governance", "Sri Lanka Fiscal Policy", "Supply Chain Audits"]
    ticker_items = "".join(
        f'<div class="ticker-item"><div class="ticker-dot"></div>{t}</div>' for t in topics
    )
    st.markdown(
        f'<div class="ticker-wrap"><div class="ticker-inner">{ticker_items}</div></div>',
        unsafe_allow_html=True
    )

    # ── Render messages ───────────────────────────────────────────────────────
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            content     = msg["content"]
            citation    = msg.get("citation")
            faithful    = msg.get("faithful", True)
            score       = msg.get("score", 0)
            rewritten   = msg.get("rewritten_query", "")
            suggestions = msg.get("suggestions", [])

            if rewritten and rewritten != msg.get("original_query", rewritten):
                st.markdown(
                    f'<div class="rewrite-pill">🔍 Interpreted as: "{rewritten}"</div>',
                    unsafe_allow_html=True
                )

            extras = ""
            if citation:
                extras += f'<div class="citation-tag">📄 {citation}</div>'
            if not faithful:
                extras += f'<div class="faith-warn">⚠️ Parts may go beyond source documents</div>'
            if score and score < 1.0:
                pct = int(score * 100)
                extras += f'''<div class="score-bar-wrap">
                  <div class="score-bar-bg"><div class="score-bar-fill" style="width:{pct}%"></div></div>
                  <span class="score-label">relevance {pct}%</span>
                </div>'''

            st.markdown(f'<div class="chat-bot">{content}{extras}</div>', unsafe_allow_html=True)

            if suggestions:
                btns_html = "".join(
                    f'<span class="suggestion-btn" onclick="window.parent.postMessage({{type:\'streamlit:setComponentValue\', value:\'{s}\'}}, \'*\')">{s}</span>'
                    for s in suggestions
                )
                st.markdown(f'<div class="suggestions-wrap">{btns_html}</div>', unsafe_allow_html=True)
                for s in suggestions:
                    if st.button(s, key=f"sug_{hash(s)}_{len(st.session_state.messages)}"):
                        st.session_state.prefill = s
                        st.rerun()

    # ── Input ─────────────────────────────────────────────────────────────────
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Ask Veri",
            value=st.session_state.prefill,
            placeholder="e.g. What gaps exist in Sri Lanka's anti-corruption laws?",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Send →", use_container_width=True)

    if submitted and user_input.strip():
        st.session_state.prefill = ""
        query = user_input.strip()

        st.session_state.messages.append({"role": "user", "content": query})

        with st.spinner("Veri is thinking…"):
            result = bot.chat(
                user_input=query,
                history=st.session_state.messages[:-1],
                session_id=st.session_state.session_id,
                filter_title=filter_title,
            )

        st.session_state.messages.append({
            "role":             "assistant",
            "content":          result["response"],
            "citation":         result["citation"],
            "faithful":         result["faithful"],
            "score":            result["score"],
            "rewritten_query":  result["rewritten_query"],
            "original_query":   query,
            "suggestions":      result["suggestions"],
        })

        st.rerun()