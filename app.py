"""
app.py — Verite Research Chatbot UI (rebuilt)
Run with: streamlit run app.py
"""

import io
import os
import uuid
import base64
import requests
import streamlit as st
from PIL import Image
from chatbot import VeriteChatbot

VERITE_LOGO_PATH = "Logos/Verite logo.png"
SEARCH_ICON_PATH = "Logos/search.png"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Veri — Verite Research",
    page_icon=Image.open(VERITE_LOGO_PATH),
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Logo / icon loaders ───────────────────────────────────────────────────────
COMMIT = "da12781eb151c723490f62acff1b76f218683600"
RAW    = f"https://raw.githubusercontent.com/nethulinarathota/veriteresearch101/{COMMIT}"

# Commit for the new logos (book, stack, shield, search, document, warning)
COMMIT2 = "1b442727a7a1ace5a05705bc3fe54601df5df8eb"
RAW2    = f"https://raw.githubusercontent.com/nethulinarathota/veriteresearch101/{COMMIT2}"

@st.cache_data(show_spinner=False)
def _fetch_b64(url: str) -> str | None:
    """Fetch a remote file and return its base64 string, or None on failure."""
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode()
    except Exception:
        return None

@st.cache_data(show_spinner=False)
def _fetch_inverted_b64(url: str) -> str | None:
    """
    Fetch a black-on-transparent PNG and invert it to white-on-transparent,
    then return as base64.  Falls back to None on any error.
    """
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        r, g, b, a = img.split()
        # Invert only the RGB channels; leave alpha intact
        inv = Image.merge("RGBA", (
            r.point(lambda x: 255 - x),
            g.point(lambda x: 255 - x),
            b.point(lambda x: 255 - x),
            a,
        ))
        buf = io.BytesIO()
        inv.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None

@st.cache_data(show_spinner=False)
def _local_b64(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None

@st.cache_data(show_spinner=False)
def _local_inverted_b64(path: str) -> str | None:
    try:
        img = Image.open(path).convert("RGBA")
        r, g, b, a = img.split()
        inv = Image.merge("RGBA", (
            r.point(lambda x: 255 - x),
            g.point(lambda x: 255 - x),
            b.point(lambda x: 255 - x),
            a,
        ))
        buf = io.BytesIO()
        inv.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None

# Load Verite logo (used as nav/sidebar/orb image and favicon source)
logo_b64 = _local_b64(VERITE_LOGO_PATH)

icon_corruption_b64 = _fetch_inverted_b64(f"{RAW}/Logos/anti-corruption.png")
icon_budget_b64     = _fetch_inverted_b64(f"{RAW}/Logos/calculator.png")
icon_employee_b64   = _fetch_inverted_b64(f"{RAW}/Logos/employee.png")

# Load stat icons — same inversion (black outlines → white)
icon_book_b64    = _fetch_inverted_b64(f"{RAW2}/Logos/book.png")
icon_stack_b64   = _fetch_inverted_b64(f"{RAW2}/Logos/stack.png")
icon_shield_b64  = _fetch_inverted_b64(f"{RAW2}/Logos/shield.png")

# Load inline icons — same inversion
icon_search_b64   = _local_inverted_b64(SEARCH_ICON_PATH) or _fetch_inverted_b64(f"{RAW2}/Logos/search.png")
icon_document_b64 = _fetch_inverted_b64(f"{RAW2}/Logos/document.png")
icon_warning_b64  = _fetch_inverted_b64(f"{RAW2}/Logos/warning.png")

def _img_tag(b64: str | None, style: str, fallback: str = "") -> str:
    if b64:
        return f'<img src="data:image/png;base64,{b64}" style="{style}" />'
    return f'<span>{fallback}</span>'

logo_img = _img_tag(
    logo_b64,
    "width:32px;height:32px;border-radius:50%;object-fit:cover;flex-shrink:0;",
    '<div class="lp-nav-mark">V</div>',
)
logo_sidebar = _img_tag(
    logo_b64,
    "width:36px;height:36px;border-radius:50%;object-fit:cover;flex-shrink:0;",
    '<div class="veri-logo-mark">V</div>',
)
logo_orb = _img_tag(
    logo_b64,
    "width:84px;height:84px;border-radius:50%;object-fit:cover;",
    "📚",
)

# Card icon helpers — white, no border-radius so the icon shape shows cleanly
icon_corruption = _img_tag(icon_corruption_b64, "width:22px;height:22px;object-fit:contain;", "🛡️")
icon_budget     = _img_tag(icon_budget_b64,     "width:22px;height:22px;object-fit:contain;", "📊")
icon_employee   = _img_tag(icon_employee_b64,   "width:22px;height:22px;object-fit:contain;", "👥")

# Stat icons — sit beside the number in the stats strip
icon_book   = _img_tag(icon_book_b64,   "width:22px;height:22px;object-fit:contain;vertical-align:middle;margin-right:6px;", "📚")
icon_stack  = _img_tag(icon_stack_b64,  "width:22px;height:22px;object-fit:contain;vertical-align:middle;margin-right:6px;", "📦")
icon_shield = _img_tag(icon_shield_b64, "width:22px;height:22px;object-fit:contain;vertical-align:middle;margin-right:6px;", "🛡️")

# Inline icons for chat message extras
icon_search_inline   = _img_tag(icon_search_b64,   "width:13px;height:13px;object-fit:contain;vertical-align:middle;margin-right:4px;", "🔍")
icon_document_inline = _img_tag(icon_document_b64, "width:13px;height:13px;object-fit:contain;vertical-align:middle;margin-right:4px;", "📄")
icon_warning_inline  = _img_tag(icon_warning_b64,  "width:13px;height:13px;object-fit:contain;vertical-align:middle;margin-right:4px;", "⚠️")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

/* ── Refined Palette
   Porcelain:       #F5F5F0  (warmer white)
   Brown Red:       #8B1E1A  (deeper maroon to match logo)
   Graphite:        #1C1F1D  (richer near-black)
   Surface:         #161918  (deeper surface)
   Deep Space Blue: #1E3048  (cooler, more contrast)
   Hover Red:       #6B1614
── */

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #1C1F1D;
    color: #F5F5F0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #161918 !important;
    border-right: 1px solid rgba(245,245,240,0.07);
}
[data-testid="stSidebar"] * { color: rgba(245,245,240,0.7) !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #F5F5F0 !important; }

/* ── Main content area ── */
.main .block-container { padding: 1.5rem 2rem; max-width: 900px; }

/* ── Logo ── */
.veri-logo {
    display: flex; align-items: center; gap: 10px;
    padding: 1rem 0 1.5rem 0;
}
.veri-logo-mark {
    width: 36px; height: 36px; background: #8B1E1A;
    border-radius: 50%; display: flex; align-items: center;
    justify-content: center; font-weight: 700; font-size: 15px;
    color: #F5F5F0; flex-shrink: 0;
}
.veri-logo-text { line-height: 1.2; }
.veri-logo-title { font-size: 17px; font-weight: 600; color: #F5F5F0; }
.veri-logo-sub   { font-size: 12px; color: rgba(245,245,240,0.35); }

/* ── Status pill ── */
.status-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(30,48,72,0.35); border: 1px solid rgba(30,48,72,0.7);
    color: #7fa8d0; font-size: 12px; padding: 4px 12px;
    border-radius: 20px; margin-bottom: 1.2rem;
}
.status-dot { width: 6px; height: 6px; background: #7fa8d0; border-radius: 50%; }

/* ── Building pill ── */
.building-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(139,30,26,0.1); border: 1px solid rgba(139,30,26,0.3);
    color: #c45550; font-size: 12px; padding: 4px 12px;
    border-radius: 20px; margin-bottom: 1.2rem;
}

/* ── Chat bubbles ── */
.chat-user {
    background: #1E3048;
    border: 1px solid rgba(30,48,72,0.9);
    color: #F5F5F0;
    padding: 0.85rem 1.1rem;
    border-radius: 16px 16px 4px 16px;
    margin: 0.6rem 0 0.6rem 18%;
    font-size: 0.93rem; line-height: 1.6;
}
.chat-bot {
    background: #161918;
    border: 1px solid rgba(245,245,240,0.08);
    color: rgba(245,245,240,0.88);
    padding: 0.9rem 1.1rem;
    border-radius: 4px 16px 16px 16px;
    margin: 0.6rem 18% 0.3rem 0;
    font-size: 0.93rem; line-height: 1.7;
}
.chat-bot p { margin: 0 0 0.5rem 0; }

/* ── Citation tag ── */
.citation-tag {
    display: inline-flex; align-items: center; gap: 5px;
    background: rgba(139,30,26,0.12); border: 1px solid rgba(139,30,26,0.3);
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

/* ── Source excerpt ── */
.source-excerpt {
    margin-top: 8px;
    padding: 8px 10px;
    border: 1px solid rgba(245,245,240,0.12);
    background: rgba(245,245,240,0.03);
    border-radius: 8px;
    font-size: 12px;
    line-height: 1.6;
    color: rgba(245,245,240,0.78);
}

/* ── Score bar ── */
.score-bar-wrap { display: flex; align-items: center; gap: 8px; margin-top: 6px; }
.score-bar-bg   { flex: 1; height: 3px; background: rgba(245,245,240,0.08); border-radius: 2px; max-width: 100px; }
.score-bar-fill { height: 3px; background: #1E3048; border-radius: 2px; }
.score-label    { font-size: 11px; color: rgba(245,245,240,0.28); }

/* ── Suggestions ── */
.suggestions-wrap { margin: 0.4rem 0 1rem 0; display: flex; flex-wrap: wrap; gap: 6px; }
.suggestion-btn {
    background: rgba(30,48,72,0.2);
    border: 1px solid rgba(30,48,72,0.55);
    color: #7fa8d0; font-size: 12px;
    padding: 5px 12px; border-radius: 14px;
    cursor: pointer; transition: all 0.2s;
}
.suggestion-btn:hover { background: rgba(30,48,72,0.4); }

/* ── Input ── */
.stTextInput input {
    background: #161918 !important;
    border: 1px solid rgba(245,245,240,0.12) !important;
    color: #F5F5F0 !important;
    border-radius: 10px !important;
    font-size: 14px !important;
    padding: 0.7rem 1rem !important;
}
.stTextInput input:focus {
    border-color: rgba(139,30,26,0.5) !important;
    box-shadow: 0 0 0 2px rgba(139,30,26,0.12) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: #8B1E1A !important;
    color: #F5F5F0 !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: background 0.2s !important;
}
.stButton > button:hover { background: #6B1614 !important; }

/* ── Divider ── */
hr { border-color: rgba(245,245,240,0.07) !important; }

/* ── Ticker ── */
@keyframes ticker { 0%{transform:translateX(0)} 100%{transform:translateX(-50%)} }
.ticker-wrap {
    overflow: hidden;
    border-top: 1px solid rgba(245,245,240,0.05);
    border-bottom: 1px solid rgba(245,245,240,0.05);
    padding: 8px 0; margin-bottom: 1.2rem;
    background: rgba(0,0,0,0.15);
}
.ticker-inner {
    display: flex; gap: 48px; width: max-content;
    animation: ticker 20s linear infinite;
}
.ticker-item {
    font-size: 11px; color: rgba(245,245,240,0.22);
    letter-spacing: 0.08em; text-transform: uppercase;
    white-space: nowrap; display: flex; align-items: center; gap: 6px;
}
.ticker-dot { width: 4px; height: 4px; background: #8B1E1A; border-radius: 50%; }

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: #161918 !important;
    border: 1px solid rgba(245,245,240,0.12) !important;
    color: #F5F5F0 !important;
    border-radius: 8px !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: #161918 !important;
    border: 1px dashed rgba(139,30,26,0.35) !important;
    border-radius: 10px !important;
}

/* ── Rewritten query pill ── */
.rewrite-pill {
    font-size: 11px; color: rgba(245,245,240,0.28);
    margin-bottom: 4px; font-style: italic;
    display: flex; align-items: center; gap: 4px;
}

/* ── Export link ── */
.export-link {
    display: block; text-align: center;
    background: rgba(245,245,240,0.04);
    border: 1px solid rgba(245,245,240,0.1);
    border-radius: 8px; padding: 8px;
    color: rgba(245,245,240,0.55); font-size: 13px; text-decoration: none;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }

/* ── Landing page ── */
@keyframes fadeUp { from { opacity: 0; transform: translateY(18px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pulse-ring { 0% { transform: scale(1); opacity: 0.35; } 100% { transform: scale(1.65); opacity: 0; } }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-9px); } }

.lp-nav { display: flex; align-items: center; justify-content: space-between; padding: 14px 36px; border-bottom: 0.5px solid rgba(245,245,240,0.07); background: #161918; animation: fadeUp 0.4s ease both; }
.lp-nav-logo { display: flex; align-items: center; gap: 9px; }
.lp-nav-mark { width: 30px; height: 30px; background: #8B1E1A; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 13px; color: #F5F5F0; }
.lp-nav-name { font-size: 15px; font-weight: 600; color: #F5F5F0; }
.lp-nav-links { display: flex; gap: 24px; }
.lp-nav-links a { color: rgba(245,245,240,0.38); font-size: 13px; text-decoration: none; position: relative; padding-bottom: 2px; transition: color 0.2s; }
.lp-nav-links a::after { content: ''; position: absolute; bottom: 0; left: 0; width: 0; height: 1px; background: #8B1E1A; transition: width 0.28s; }
.lp-nav-links a:hover { color: #F5F5F0; }
.lp-nav-links a:hover::after { width: 100%; }

.lp-hero { padding: 56px 36px 48px; display: flex; align-items: center; justify-content: space-between; gap: 32px; }
.lp-hero-text { flex: 1; animation: fadeUp 0.5s ease 0.1s both; }
.lp-tag { display: inline-block; background: rgba(139,30,26,0.12); border: 0.5px solid rgba(139,30,26,0.35); color: #c45550; font-size: 11px; padding: 4px 12px; border-radius: 20px; margin-bottom: 18px; letter-spacing: 0.06em; text-transform: uppercase; }
.lp-h1 { font-size: 34px; font-weight: 600; line-height: 1.22; margin-bottom: 15px; color: #F5F5F0; }
.lp-h1 .accent { color: #8B1E1A; }
.lp-sub { color: rgba(245,245,240,0.42); font-size: 14px; line-height: 1.75; max-width: 400px; margin-bottom: 26px; }
.lp-btns { display: flex; gap: 10px; }
.lp-btn-p { background: #8B1E1A; color: #F5F5F0; border: none; padding: 10px 22px; border-radius: 7px; font-size: 13px; cursor: pointer; transition: background 0.2s, transform 0.15s; }
.lp-btn-p:hover { background: #6B1614; transform: translateY(-2px); }
.lp-btn-o { background: transparent; color: #F5F5F0; border: 0.5px solid rgba(245,245,240,0.22); padding: 10px 22px; border-radius: 7px; font-size: 13px; cursor: pointer; transition: all 0.2s; }
.lp-btn-o:hover { border-color: rgba(245,245,240,0.5); background: rgba(245,245,240,0.04); transform: translateY(-2px); }

.lp-hero-vis { flex: 0 0 190px; display: flex; align-items: center; justify-content: center; animation: fadeUp 0.6s ease 0.25s both; }
.lp-orb-wrap { position: relative; width: 136px; height: 136px; display: flex; align-items: center; justify-content: center; animation: float 4s ease-in-out infinite; }
.lp-orb { width: 84px; height: 84px; background: transparent; border-radius: 50%; display: flex; align-items: center; justify-content: center; position: relative; z-index: 2; font-size: 32px; overflow: hidden; }
.lp-ring { position: absolute; width: 84px; height: 84px; border-radius: 50%; border: 1.5px solid #8B1E1A; animation: pulse-ring 2.4s ease-out infinite; }
.lp-ring:nth-child(2) { animation-delay: 0.8s; }
.lp-ring:nth-child(3) { animation-delay: 1.6s; }

.lp-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; background: rgba(245,245,240,0.06); border-top: 0.5px solid rgba(245,245,240,0.06); }
.lp-stat { background: #1C1F1D; padding: 24px 28px; }
.lp-stat-num { font-size: 28px; font-weight: 600; color: #F5F5F0; margin-bottom: 3px; display: flex; align-items: center; gap: 4px; }
.lp-stat-num span { color: #8B1E1A; }
.lp-stat-label { font-size: 11px; color: rgba(245,245,240,0.32); letter-spacing: 0.04em; }

.lp-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; background: rgba(245,245,240,0.06); border-top: 0.5px solid rgba(245,245,240,0.06); }
.lp-card { background: #161918; padding: 24px 20px; cursor: pointer; transition: background 0.22s; position: relative; overflow: hidden; }
.lp-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: #8B1E1A; transform: scaleX(0); transform-origin: left; transition: transform 0.28s ease; border-radius: 0; }
.lp-card:hover { background: #1a1d1b; }
.lp-card:hover::before { transform: scaleX(1); }
.lp-card-icon { width: 38px; height: 38px; background: rgba(139,30,26,0.1); border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-bottom: 12px; font-size: 18px; transition: background 0.22s; }
.lp-card:hover .lp-card-icon { background: rgba(139,30,26,0.2); }
.lp-card h3 { font-size: 13px; font-weight: 500; margin-bottom: 7px; color: #F5F5F0; }
.lp-card p { font-size: 12px; color: rgba(245,245,240,0.38); line-height: 1.6; }
.lp-card-arrow { margin-top: 14px; color: #8B1E1A; font-size: 12px; opacity: 0; transform: translateX(-6px); transition: opacity 0.22s, transform 0.22s; display: flex; align-items: center; gap: 4px; }
.lp-card:hover .lp-card-arrow { opacity: 1; transform: translateX(0); }

.lp-cards a { display: contents; }

.lp-main-cta { display: none; }

/* ── Start asking button icon ── */
.start-asking-btn {
    display: flex; align-items: center; justify-content: center; gap: 8px;
    background: #8B1E1A; color: #F5F5F0;
    border: none; border-radius: 8px;
    padding: 10px 22px; font-size: 13px; font-weight: 500;
    cursor: pointer; transition: background 0.2s, transform 0.15s;
    width: 100%;
}
.start-asking-btn:hover { background: #6B1614; transform: translateY(-2px); }
</style>
""", unsafe_allow_html=True)

# ── Init chatbot ──────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading knowledge base…")
def load_bot(_bot_version: float):
    bot = VeriteChatbot()
    bot.build_knowledge_base()
    return bot

BOT_VERSION = os.path.getmtime("chatbot.py")
bot = load_bot(BOT_VERSION)

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

if "selected_publication" not in st.session_state:
    st.session_state.selected_publication = "All publications"
if "last_selected_publication" not in st.session_state:
    st.session_state.last_selected_publication = st.session_state.selected_publication

def _set_selected_publication(match_terms: list[str]) -> None:
    for title in pub_list:
        low = title.lower()
        if all(term in low for term in match_terms):
            st.session_state.selected_publication = title
            st.session_state.last_selected_publication = title
            return
    st.session_state.selected_publication = "All publications"
    st.session_state.last_selected_publication = "All publications"


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
    <div style="background:#1C1F1D; border-radius:12px; overflow:hidden; font-family:'Inter',sans-serif;">

      <!-- Nav -->
      <nav class="lp-nav">
        <div class="lp-nav-logo">
          {logo_img}
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
            <div class="lp-orb">{logo_orb}</div>
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
          <div class="lp-stat-num">{icon_book}{len(pub_list)}<span>+</span></div>
          <div class="lp-stat-label">Publications indexed</div>
        </div>
        <div class="lp-stat">
          <div class="lp-stat-num">{icon_stack}{chunk_count}<span>+</span></div>
          <div class="lp-stat-label">Knowledge chunks</div>
        </div>
        <div class="lp-stat">
          <div class="lp-stat-num">{icon_shield}0<span>ms</span></div>
          <div class="lp-stat-label">Hallucinations (by design)</div>
        </div>
      </div>

      <!-- Topic cards -->
      <div class="lp-cards">
        <a href="https://www.veriteresearch.org/wp-content/uploads/2025/02/11022025_Gaps_in_the_Guardrails_A_Review_of_Laws_on_Private_Sector_Corruption_in_Sri_Lanka.pdf"
           target="_blank" style="text-decoration:none;">
          <div class="lp-card" id="card-corruption">
            <div class="lp-card-icon">{icon_corruption}</div>
            <h3>Anti-corruption</h3>
            <p>Gaps in Sri Lanka's private sector legal framework and international benchmarks.</p>
            <div class="lp-card-arrow">→ Explore</div>
          </div>
        </a>
        <a href="https://www.veriteresearch.org/wp-content/uploads/2026/02/20260217_VeriteResearch_StateOfTheBudget2026.pdf"
           target="_blank" style="text-decoration:none;">
          <div class="lp-card" id="card-budget">
            <div class="lp-card-icon">{icon_budget}</div>
            <h3>Budget 2026</h3>
            <p>Revenue projections, tax policy changes, and fiscal targets for the year ahead.</p>
            <div class="lp-card-arrow">→ Explore</div>
          </div>
        </a>
        <a href="https://www.veriteresearch.org/wp-content/uploads/2024/05/VR-Working-Paper_The-Inefficiency-of-Social-Contacts-for-Unemployed-Youth-Working-Paper_June-2020-01.pdf"
           target="_blank" style="text-decoration:none;">
          <div class="lp-card" id="card-youth">
            <div class="lp-card-icon">{icon_employee}</div>
            <h3>Youth employment</h3>
            <p>Why social contacts fail unemployed youth and what actually works instead.</p>
            <div class="lp-card-arrow">→ Explore</div>
          </div>
        </a>
      </div>

    </div>
    """, unsafe_allow_html=True)

    # Streamlit buttons that drive navigation (styled to blend with landing page)
    st.markdown("<div style='height:1px;background:rgba(245,245,240,0.06);'></div>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        clicked = st.button(
            "Start asking ->",
            key="lp_start",
            use_container_width=True,
        )
        st.markdown(
            f"""
            <style>
            div[data-testid="column"]:first-child .stButton > button {{
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 7px !important;
            }}
            div[data-testid="column"]:first-child .stButton > button::before {{
                content: "";
                width: 15px;
                height: 15px;
                display: inline-block;
                background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'><circle cx='11' cy='11' r='7'/><line x1='21' y1='21' x2='16.65' y2='16.65'/></svg>");
                background-size: contain;
                background-repeat: no-repeat;
                background-position: center;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )
        if clicked:
            if st.session_state.last_selected_publication in (["All publications"] + pub_list):
                st.session_state.selected_publication = st.session_state.last_selected_publication
            st.session_state.page = "chat"
            st.rerun()
    with col2:
        if st.button("Anti-corruption", use_container_width=True, key="lp_card1"):
            st.session_state.prefill = "What gaps does Verite identify in Sri Lanka's anti-corruption laws?"
            _set_selected_publication(["gaps", "guardrails"])
            st.session_state.page = "chat"
            st.rerun()
    with col3:
        if st.button("Budget 2026", use_container_width=True, key="lp_card2"):
            st.session_state.prefill = "What does the State of the Budget 2026 say about government revenue?"
            _set_selected_publication(["budget", "2026"])
            st.session_state.page = "chat"
            st.rerun()
    with col4:
        if st.button("Youth employment", use_container_width=True, key="lp_card3"):
            st.session_state.prefill = "What job search methods work best for unemployed youth in Sri Lanka?"
            _set_selected_publication(["social", "contacts", "youth"])
            st.session_state.page = "chat"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# CHAT PAGE
# ══════════════════════════════════════════════════════════════════════════════
else:

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"""
        <div class="veri-logo">
          {logo_sidebar}
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
        filter_opt = ["All publications"] + pub_list
        if st.session_state.selected_publication not in filter_opt:
            st.session_state.selected_publication = "All publications"
        selected = st.selectbox(
            "Search within",
            filter_opt,
            index=filter_opt.index(st.session_state.selected_publication),
            key="selected_publication",
            label_visibility="collapsed",
        )
        st.session_state.last_selected_publication = selected
        filter_title = None if selected == "All publications" else selected

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
        <div style="font-size:12px; color:rgba(245,245,240,0.3); line-height:1.8;">
          Session: <code style="color:rgba(245,245,240,0.5)">{st.session_state.session_id}</code><br>
          Chunks indexed: <strong style="color:rgba(245,245,240,0.6)">{chunk_count}</strong><br>
          Publications: <strong style="color:rgba(245,245,240,0.6)">{len(pub_list)}</strong>
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
            source_excerpt = msg.get("source_excerpt", "")
            rewritten   = msg.get("rewritten_query", "")
            suggestions = msg.get("suggestions", [])

            if rewritten and rewritten != msg.get("original_query", rewritten):
                st.markdown(
                    f'<div class="rewrite-pill">{icon_search_inline} Interpreted as: "{rewritten}"</div>',
                    unsafe_allow_html=True
                )

            extras = ""
            if citation:
                extras += f'<div class="citation-tag">{icon_document_inline} {citation}</div>'
            if not faithful:
                extras += f'<div class="faith-warn">{icon_warning_inline} Parts may go beyond source documents</div>'
            if score and score < 1.0:
                pct = int(score * 100)
                extras += f'''<div class="score-bar-wrap">
                  <div class="score-bar-bg"><div class="score-bar-fill" style="width:{pct}%"></div></div>
                  <span class="score-label">relevance {pct}%</span>
                </div>'''
            if source_excerpt:
                excerpt = source_excerpt[:600] + ("..." if len(source_excerpt) > 600 else "")
                extras += f'<div class="source-excerpt"><strong>Source excerpt:</strong><br>{excerpt}</div>'

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
            "source_excerpt":   result.get("source_excerpt", ""),
            "rewritten_query":  result["rewritten_query"],
            "original_query":   query,
            "suggestions":      result["suggestions"],
        })

        st.rerun()


