"""Words4You — Streamlit book discovery app.

🤖 AI-generated (CREATE mode) — review and adapt in your own words before submitting.
Run from project root:  uv run streamlit run app/app.py
"""

import base64
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------- 1. CONFIG
st.set_page_config(page_title="Words4You", page_icon="📚", layout="wide")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "clean" / "catalog_mood.csv"
FIGURES_DIR = BASE_DIR / "figures"
BACKGROUND_PATH = FIGURES_DIR / "backgroundlibrary.png"
MISSING_COVER_PATH = FIGURES_DIR / "missingcover.png"

APP_COLS = [
    "book_name", "author", "book_url", "img_url", "rating", "pages",
    "pub_date", "genres_clean", "synopsis", "data_source", "source_list",
    "cluster_f1b", "cluster_name", "clusterable", "mood_scored", "mood",
    "mood_secondary", "emotion", "emotion_secondary", "emotion_conf",
    "mood_low_conf",
]

# Spec asks for #6A1B9A — lightened for legibility on dark panels.
ACCENT = "#9C6ADE"


# ---------------------------------------------------------------- 2. HELPERS
def img_to_base64(path: Path) -> str:
    """Return base64 for a local image, or '' when the file is unreadable."""
    try:
        return base64.b64encode(path.read_bytes()).decode()
    except OSError:
        return ""


@st.cache_data
def load_catalog(path: str) -> pd.DataFrame:
    """Load the cleaned catalog, keep app-facing columns, coerce numerics."""
    df = pd.read_csv(path)
    df = df[APP_COLS].copy()
    for col in ("rating", "pages", "pub_date"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def resolve_cover(img_url) -> str:
    """Return a display source for a cover: remote URL or base64 data URI."""
    if isinstance(img_url, str) and img_url.startswith("http"):
        return img_url
    local = MISSING_COVER_PATH
    if isinstance(img_url, str) and img_url.strip():
        candidate = BASE_DIR / img_url
        if candidate.exists():
            local = candidate
    b64 = img_to_base64(local)
    return f"data:image/png;base64,{b64}" if b64 else ""


def star_string(rating: float) -> str:
    """Map a 0–5 rating to a five-character star string."""
    full = int(round(min(max(float(rating), 0.0), 5.0)))
    return "★" * full + "☆" * (5 - full)


def pick_book(pool: pd.DataFrame, justification: str, weights=None) -> None:
    """Pick one random book from `pool`, optionally weighted by a column."""
    if pool.empty:
        st.session_state.no_match = True
        return
    st.session_state.no_match = False
    st.session_state.selected_idx = int(pool.sample(1, weights=weights).index[0])
    st.session_state.pool_idx = pool.index.tolist()
    st.session_state.justification = justification
    st.session_state.show_similar = False


# ---------------------------------------------------------------- 3. DATA
app_df = load_catalog(str(DATA_PATH))

if "selected_idx" not in st.session_state:
    st.session_state.selected_idx = int(app_df["rating"].idxmax())
    st.session_state.pool_idx = app_df.index.tolist()
    st.session_state.justification = "our overall top-rated pick"
    st.session_state.show_similar = False
    st.session_state.no_match = False

# ---------------------------------------------------------------- 4. THEME CSS
bg_b64 = img_to_base64(BACKGROUND_PATH)
bg_css = (
    f'background: url("data:image/png;base64,{bg_b64}") center/cover fixed;'
    if bg_b64
    else "background: #0A0C10;"
)

st.markdown(
    f"""
    <style>
    [data-testid="stAppViewContainer"] {{ {bg_css} }}
    [data-testid="stAppViewContainer"]::before {{
        content: ""; position: fixed; inset: 0;
        background: rgba(10, 12, 16, 0.75); z-index: 0;
        pointer-events: none;
    }}
    [data-testid="stHeader"] {{ background: transparent; }}
    [data-testid="stBlockContainer"], .block-container {{
        position: relative; z-index: 1;
        background-color: rgba(26, 29, 33, 0.95);
        border: 1px solid #2C333B;
        border-radius: 20px;
        padding: 40px !important;
        margin: 30px auto;
        box-shadow: 0px 10px 30px rgba(0, 0, 0, 0.5);
        max-width: 1200px;
    }}
    .top-bar {{
        display: flex; justify-content: flex-end; gap: 1rem;
        background: #14171B; border-radius: 10px;
        padding: 0.3rem 1rem; margin-bottom: 1rem;
        font-size: 0.9rem; color: #8A94A0;
    }}
    .app-header {{ display: flex; align-items: center; gap: 0.8rem; }}
    .app-header h1 {{
        font-family: "Segoe UI", "Helvetica Neue", sans-serif;
        font-size: 1.9rem; margin: 0; color: #E8EDF2;
    }}
    .greeting {{
        font-size: 1.4rem; font-weight: 700; color: #E8EDF2;
        margin: 0.8rem 0 0.4rem;
    }}
    .spotlight {{
        background: #23282E;
        border-left: 6px solid #26A69A;
        border-radius: 14px;
        box-shadow: 14px 14px 45px rgba(126, 87, 194, 0.35);
        padding: 1.4rem;
    }}
    .panel {{
        background: #23282E; border: 1px solid #2C333B;
        border-radius: 14px; padding: 1rem 1.2rem; margin-bottom: 1rem;
        box-shadow: 0 0 18px rgba(0, 0, 0, 0.35);
    }}
    .panel h4 {{ color: #E8EDF2; margin: 0 0 0.6rem; }}
    .teal-list {{
        background: #0E4F4A; border-radius: 10px;
        padding: 0.7rem 1rem; color: #DFF6F3; font-size: 0.92rem;
    }}
    .teal-list ol {{ margin: 0; padding-left: 1.2rem; }}
    .stButton > button, .stLinkButton > a {{
        background: linear-gradient(90deg, #26A69A, #7E57C2) !important;
        color: white !important; border: none !important;
        border-radius: 10px !important; font-weight: 600 !important;
    }}
    [data-testid="stSlider"] [role="slider"] {{
        background: linear-gradient(135deg, #26A69A, #FF5722) !important;
        border: none !important;
    }}
    .stars {{ color: #FFC107; font-size: 1.1rem; letter-spacing: 2px; }}
    .book-title {{ color: {ACCENT}; font-size: 1.7rem; font-weight: 800; margin: 0; }}
    .justify-note {{ color: #B9A7D8; font-size: 0.85rem; }}
    .blurb {{ color: #C9D2DB; font-size: 0.93rem; line-height: 1.5; }}
    </style>
    """,
    unsafe_allow_html=True,
)

LOGO_SVG = """
<svg width="46" height="46" viewBox="0 0 46 46" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="wv" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#26A69A"/><stop offset="100%" stop-color="#4FC3F7"/>
  </linearGradient></defs>
  <path d="M4 30 C 12 14, 20 14, 26 26 S 40 34, 42 18"
        stroke="url(#wv)" stroke-width="5" fill="none" stroke-linecap="round"/>
  <path d="M6 38 C 14 26, 24 26, 30 34 S 40 40, 42 30"
        stroke="url(#wv)" stroke-width="3" fill="none" stroke-linecap="round" opacity="0.7"/>
</svg>
"""

# ---------------------------------------------------------------- 5. HEADER
st.markdown(
    '<div class="top-bar"><span>🔍</span><span>👤</span><span>⚙️</span></div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="app-header">{LOGO_SVG}'
    "<h1>Words4You: Your Curated Book Discovery Engine</h1></div>",
    unsafe_allow_html=True,
)

name = st.text_input(
    "Your name", placeholder="Type your name…", label_visibility="collapsed"
)
display_name = name.strip() if name and name.strip() else "reader"
st.markdown(
    f'<p class="greeting">Hi {display_name}! Let&#39;s find your next great read.</p>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- 6. FILTER ROW
f1, f2, f3 = st.columns(3, gap="large")

with f1:
    st.markdown(
        '<div class="panel"><h4>Recommendation by Mood</h4></div>',
        unsafe_allow_html=True,
    )
    moods = sorted(
        app_df.loc[app_df["mood_scored"] == True, "mood"].dropna().unique()
    )
    sel_mood = st.selectbox("What mood are you in?", moods, key="mood_sel")
    if st.button("Recommend by mood", use_container_width=True):
        pool = app_df[
            (app_df["mood_scored"] == True)
            & (app_df["mood"] == sel_mood)
            & (app_df["mood_low_conf"] == False)
        ]
        pick_book(pool, f"the mood '{sel_mood}'", weights="emotion_conf")
        st.rerun()

with f2:
    st.markdown(
        '<div class="panel"><h4>Dynamic Filters</h4></div>',
        unsafe_allow_html=True,
    )
    r_lo, r_hi = float(app_df["rating"].min()), float(app_df["rating"].max())
    rating_rng = st.slider("Rating", r_lo, r_hi, (r_lo, r_hi), 0.05, key="f_rating")
    y_lo, y_hi = int(app_df["pub_date"].min()), int(app_df["pub_date"].max())
    year_rng = st.slider("Publication year", y_lo, y_hi, (y_lo, y_hi), key="f_year")
    p_lo, p_hi = int(app_df["pages"].min()), int(app_df["pages"].max())
    pages_rng = st.slider("Pages", p_lo, p_hi, (p_lo, p_hi), key="f_pages")
    if st.button("Apply filters", use_container_width=True):
        pool = app_df[
            app_df["rating"].between(*rating_rng)
            & app_df["pub_date"].between(*year_rng)
            & app_df["pages"].between(*pages_rng)
        ]
        pick_book(pool, "your dynamic filters (rating, year, pages)")
        st.rerun()

with f3:
    st.markdown(
        '<div class="panel"><h4>No idea what you look for? '
        "Lucky guess with RoUleTte!</h4></div>",
        unsafe_allow_html=True,
    )
    clusters = sorted(app_df["cluster_name"].dropna().unique())
    excluded = st.multiselect(
        "Genre clusters to EXCLUDE", clusters, key="roulette_excl"
    )
    if st.button("Play RoUleTte 🎰", use_container_width=True):
        pool = app_df[~app_df["cluster_name"].isin(excluded)]
        pick_book(pool, "pure luck — RoUleTte!")
        st.rerun()

st.markdown("---")

# ---------------------------------------------------------------- 7. MAIN ROW
col_main, col_right = st.columns([2.2, 1], gap="large")

with col_right:
    list_avg = (
        app_df.groupby("source_list")["rating"].mean().sort_values(ascending=False)
    )
    for source in list_avg.head(2).index:
        more_key = f"more_{source}"
        if more_key not in st.session_state:
            st.session_state[more_key] = False
        n_show = 6 if st.session_state[more_key] else 3
        top_books = app_df[app_df["source_list"] == source].nlargest(
            n_show, "rating"
        )
        items = "".join(
            f"<li><b>{row.book_name}</b> — {row.author} (★ {row.rating:.2f})</li>"
            for row in top_books.itertuples()
        )
        st.markdown(
            f'<div class="panel"><h4>{source}</h4>'
            f'<div class="teal-list"><ol>{items}</ol></div></div>',
            unsafe_allow_html=True,
        )
        if not st.session_state[more_key]:
            if st.button("See more", key=f"btn_{more_key}"):
                st.session_state[more_key] = True
                st.rerun()

with col_main:
    if st.session_state.no_match:
        st.warning("No books match that selection — try widening your filters.")
    book = app_df.loc[st.session_state.selected_idx]
    cover_src = resolve_cover(book["img_url"])
    st.markdown(
        f"""
        <div class="spotlight">
          <div style="display:flex; gap:1.4rem; align-items:flex-start;">
            <img src="{cover_src}" width="170" style="border-radius:8px;"/>
            <div>
              <p class="book-title">{book['book_name']}</p>
              <p style="color:#AAB4BF; margin:0.2rem 0;">{book['author']}</p>
              <p class="stars">{star_string(book['rating'])}
                 <span style="color:#E8EDF2;">{book['rating']:.1f}/5.0</span></p>
              <p class="justify-note">Based on your preference for
                 {st.session_state.justification}</p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    b1, b2, b3 = st.columns([1.2, 1, 1])
    with b1:
        if st.button("Another book", use_container_width=True):
            pick_book(
                app_df.loc[st.session_state.pool_idx],
                st.session_state.justification,
            )
            st.rerun()
    with b2:
        if st.button("See Similar Books", use_container_width=True):
            st.session_state.show_similar = True
    with b3:
        url = book["book_url"] if isinstance(book["book_url"], str) else ""
        if url:
            st.link_button(
                f"View on {book['data_source']}", url, use_container_width=True
            )

    synopsis = (
        book["synopsis"]
        if isinstance(book["synopsis"], str)
        else "No synopsis available."
    )
    st.markdown(f'<p class="blurb">{synopsis}</p>', unsafe_allow_html=True)

    if st.session_state.show_similar:
        others = [
            i for i in st.session_state.pool_idx
            if i != st.session_state.selected_idx
        ]
        similar = app_df.loc[others].nlargest(4, "rating")
        if similar.empty:
            st.info("Only one book matches this selection — nothing similar to show.")
        else:
            st.markdown("**More books from the same selection:**")
            for row in similar.itertuples():
                st.markdown(
                    f"- **{row.book_name}** — {row.author} (★ {row.rating:.2f})"
                )


