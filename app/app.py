"""Words4You — Streamlit book discovery app.

Run from project root:  uv run streamlit run app/app.py
"""

import base64 #to convert local images into text format for webbrowser to display
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


@st.cache_data   # to load book file once and save it in memory, avois re-read every time user clicks
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
    f'background-image: url("data:image/png;base64,{bg_b64}") !important;'
    if bg_b64
    else "background-color: #0A0C10 !important;"
)

st.markdown(
    f"""
    <style>
    /* Set the background image on the main application viewport */
    [data-testid="stAppViewContainer"] {{
        {bg_css}
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
        
    }}

    /* force intermediate Streamlit structural wrappers to be completely transparent */
    [data-testid="stApp"], .main, [data-testid="stHeader"] {{
        background-color: transparent !important;
    }}

    /* light dark mask (20%) so the library details remain beautiful */
    [data-testid="stAppViewContainer"]::before {{
        content: "";
        position: fixed;
        inset: 0;
        background: rgba(10, 12, 16, 0.20) !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
        z-index: 0 !important;
        pointer-events: none;
    }}

    /* style the central block container to float over the background */
    [data-testid="stBlockContainer"] {{
        position: relative !important;
        z-index: 99 !important;
        background-color: rgba(20, 23, 27, 0.90) !important; /* Slightly darker and more opaque for crisp text contrast */
        border: 1px solid #2C333B !important;
        border-radius: 20px !important;
        padding: 40px !important;
        margin: 40px auto !important;
        box-shadow: 0px 15px 40px rgba(0, 0, 0, 0.6) !important;
        max-width: 1200px !important;
    }}

    /* clean, dark panels that group widgets cleanly together */
    .panel {{
        background: #181B1F; 
        border: 1px solid #2C333B;
        border-radius: 14px; 
        padding: 1.2rem; 
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }}
    .panel h4 {{ color: #E8EDF2; margin: 0; font-weight: 600; }}

    /* increase legibility of Streamlit Sliders */
    /* Target the slider labels (e.g., 'Rating', 'Pages') */
    [data-testid="stWidgetLabel"] p {{
        color: #E8EDF2 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }}
    /* Target the small numbers under/over the sliders */
    [data-testid="stSlider"] div {{
        color: #E8EDF2 !important; /* Forces them from red to crisp off-white */
    }}
    /* Make the base track darker so the active red/orange track pops cleanly */
    [data-testid="stSlider"] [data-baseweb="slider"] {{
        background-color: #2D333B !important;
    }}

    /* Design Elements */
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
        background: #181B1F;
        border-left: 6px solid #26A69A;
        border-radius: 14px;
        box-shadow: 14px 14px 45px rgba(126, 87, 194, 0.25);
        padding: 1.4rem;
    }}
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
    .book-title {{ color: {ACCENT}; font-size: 1.9rem; font-weight: 800; margin: 0; }}
    .justify-note {{ color: #B9A7D8; font-size: 0.85rem; }}
    .blurb {{ color: #C9D2DB; font-size: 0.93rem; line-height: 1.5; }}

    /* cinematic spotlight cover — larger, centralized, teal/purple glow */
    .cover-glow {{
        border-radius: 12px;
        box-shadow: 0 0 30px rgba(38, 166, 154, 0.45),
                    0 0 60px rgba(126, 87, 194, 0.30);
        border: 2px solid #2C333B;
    }}
    .data-flair {{
        display: inline-flex; align-items: center; gap: 0.4rem;
        background: #14171B; border: 1px solid #2C333B;
        border-radius: 20px; padding: 0.3rem 0.9rem;
        color: #E8EDF2; font-size: 0.9rem; font-weight: 600;
    }}
    .flair-icon {{ font-size: 1.05rem; }}

    /* similar-reads visual matrix covers in a grid */
    .similar-matrix {{
        display: grid; grid-template-columns: repeat(4, 1fr);
        gap: 1rem; margin-top: 0.6rem;
    }}
    .similar-item {{
        text-align: center; background: #14171B;
        border: 1px solid #2C333B; border-radius: 10px;
        padding: 0.7rem; transition: transform 0.15s ease;
    }}
    .similar-item:hover {{ transform: translateY(-4px); }}
    .similar-item img {{
        width: 100%; height: 150px; object-fit: cover;
        border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    }}
    .similar-item-title {{
        color: #E8EDF2; font-size: 0.82rem; font-weight: 600;
        margin-top: 0.5rem; overflow: hidden;
        text-overflow: ellipsis; white-space: nowrap;
    }}
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
# ---------------------------------------------------------------- 5. HEADER
st.markdown(
    """
    <div class="disclaimer-bar">
        <span class="disclaimer-icon">💡</span>
        <span class="disclaimer-text">
            <strong>Data Notice:</strong> This discovery engine aggregates ratings, genre tags, and mood classifications (which are generated from publisher synopses). These filters are designed to guide your exploration and should be treated as helpful aids rather than absolute ground truths.
        </span>
    </div>
    
    <style>
    .disclaimer-bar {
        background-color: #14171B; /* Matches your dark background */
        border-left: 4px solid #26A69A; /* Elegant teal stripe on the left */
        border-radius: 8px;
        padding: 0.8rem 1.2rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.2);
    }
    .disclaimer-icon {
        font-size: 1.2rem;
        margin-right: 0.8rem;
    }
    .disclaimer-text {
        font-size: 0.85rem;
        color: #8A94A0; /* Soft gray color so it doesn't distract too much */
        line-height: 1.4;
    }
    .disclaimer-text strong {
        color: #26A69A; /* Highlighting "Data Notice" in teal */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="app-header">{LOGO_SVG}'
    '<h1>'
    '<span class="w4y-words">Words</span>'
    '<span class="w4y-four">4</span>'
    '<span class="w4y-you">You</span>'
    '<span class="w4y-tag">: Your Curated Book Discovery Engine</span>'
    '</h1></div>',
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

# ---------------------------------------------------------------- 6. SIDEBAR FILTERS
st.markdown(
    """
    <style>
    /* Sidebar surface + bordered filter containers */
    [data-testid="stSidebar"] {
        background-color: rgba(20, 23, 27, 0.95) !important;
        border-right: 1px solid #2C333B;
    }
    div[data-testid="stVerticalBlockBorderContainer"] {
        background-color: #1A1D21 !important;
        border: 1px solid #2C333B !important;
        border-radius: 14px !important;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4) !important;
        padding: 1.2rem !important;
    }
    .filter-title {
        color: #E8EDF2;
        font-size: 1.15rem;
        font-weight: 700;
        margin-top: 0;
        margin-bottom: 1rem;
        line-height: 1.3;
    }
    /* Tri-color app title — colors reuse existing palette (stars amber + primary teal) */
    .w4y-words { color: #E8EDF2; }   /* off-white — matches app body text */
    .w4y-four  { color: #FFC107; }   /* amber — same as your star ratings */
    .w4y-you   { color: #26A69A; }   /* teal — your primary accent */
    .w4y-tag   { color: #E8EDF2; font-weight: 400; }  /* subtitle, lighter weight so title dominates */
    </style>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.markdown(
        '<p class="greeting" style="font-size:1.5rem; margin-top:0;">Discovery Center</p>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown('<p class="filter-title">Recommendation by Mood</p>', unsafe_allow_html=True)

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

    with st.container(border=True):
        st.markdown('<p class="filter-title">Dynamic Filters</p>', unsafe_allow_html=True)

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

    with st.container(border=True):
        st.markdown(
            '<p class="filter-title">No idea what you look for? Lucky guess with RoUleTte!</p>',
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

# ---------------------------------------------------------------- 7. MAIN ROW
col_main, col_right = st.columns([2.2, 1], gap="large")

with col_right:
    # groupping by source_list and find the top 2 lists based on average rating
    list_avg = (
        app_df.groupby("source_list")["rating"].mean().sort_values(ascending=False)
    )
    
    for source in list_avg.head(2).index:
        # We create a unique key in memory to store the 3 books for this specific list
        books_key = f"saved_books_{source}"
        
        # Filter our main database to get a pool of highly-rated books from this source list
        # (We use >= 4.0 so the recommendations stay high-quality, but still random!)
        high_rated_pool = app_df[
            (app_df["source_list"] == source) & (app_df["rating"] >= 4.0)
        ]
        
        # Safety check: If the pool is too small, just use all books from that list
        if len(high_rated_pool) < 3:
            high_rated_pool = app_df[app_df["source_list"] == source]

        # if we don't have 3 books saved in memory yet, let's pick them!
        #    Cap sample size at pool length so tiny lists can't raise ValueError.
        n_pick = min(3, len(high_rated_pool))
        if books_key not in st.session_state:
            st.session_state[books_key] = high_rated_pool.sample(n_pick)
            
        # Grab our saved books from memory
        current_books = st.session_state[books_key]
        
        # build the list of books in HTML with hyperlinks!
        list_items = []
        for row in current_books.itertuples():
            # Check if we have a valid string URL
            url = row.book_url if isinstance(row.book_url, str) and row.book_url.strip() else None
            
            if url:
                # If there's a link, wrap the title in an <a> tag that opens in a new tab (_blank)
                # We style it to inherit colors so it looks native to your panel
                title_html = f'<a href="{url}" target="_blank" style="color: #DFF6F3; text-decoration: underline; font-weight: bold;">{row.book_name}</a>'
            else:
                # Fallback if there is no URL
                title_html = f'<b>{row.book_name}</b>'
                
            # combine the title link, author, and rating into a single list item
            list_items.append(f"<li>{title_html} — {row.author} (★ {row.rating:.2f})</li>")
            
        items = "".join(list_items)
        
        # render the panel
        st.markdown(
            f'<div class="panel"><h4>{source}</h4>'
            f'<div class="teal-list"><ol>{items}</ol></div></div>',
            unsafe_allow_html=True,
        )
        
        #shuffle Button
        # When clicked, we select 3 brand new random books and refresh the page
        if st.button("Shuffle books 🎲", key=f"btn_shuffle_{source}"):
            st.session_state[books_key] = high_rated_pool.sample(n_pick)
            st.rerun()

with col_main:
    if st.session_state.no_match:
        st.warning("No books match that selection — try widening your filters.")
    
    book = app_df.loc[st.session_state.selected_idx]
    cover_src = resolve_cover(book["img_url"])
    
    # Resolve synopsis text before rendering the block
    synopsis = (
        book["synopsis"]
        if isinstance(book["synopsis"], str)
        else "No synopsis available."
    )
    clean_edges = str(book['genres_clean']).strip("[]")
    book_genre_clean = clean_edges.replace("'", "")
    
    # render the dark spotlight container with BOTH details and the synopsis inside it
    st.markdown(
        f"""
        <div class="spotlight">
          <div style="display:flex; gap:1.8rem; align-items:flex-start;">
            <img src="{cover_src}" width="220" class="cover-glow"/>
            <div>
              <p class="book-title">{book['book_name']}</p>
              <p style="color:#AAB4BF; margin:0.2rem 0; font-size:1.15rem;">{book['author']}</p>
              <p class="stars">{star_string(book['rating'])}
                 <span style="color:#E8EDF2; font-size:1rem; margin-left:5px;">{book['rating']:.1f}/5.0</span></p>
              <p class="justify-note" style="margin-top:0.8rem;">Based on your preference for: <span style="color:#26A69A; font-weight:600;">{st.session_state.justification}</span></p>
              <div style="display:flex; gap:0.7rem; flex-wrap:wrap; margin-top:1rem;">
                <span class="data-flair"><span class="flair-icon">📖</span>{book['pages']:.0f} pages</span>
                <span class="data-flair"><span class="flair-icon">📅</span>{book['pub_date']:.0f}</span>
                <span class="data-flair"><span class="flair-icon">🏷️</span>{book_genre_clean}</span>
              </div>
            </div>
          </div>
          <!-- Divider line to cleanly separate header from synopsis -->
          <hr style="border: 0; border-top: 1px solid #2C333B; margin: 1.2rem 0 0.8rem 0;" />
          <p class="blurb" style="margin: 0; padding: 0.2rem 0;">{synopsis}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # spacing helper
    st.write("") 
    
    # buttons row (now sits neatly below the main block)
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
            st.session_state.show_similar = not st.session_state.show_similar
            st.rerun()
    with b3:
        url = book["book_url"] if isinstance(book["book_url"], str) else ""
        if url:
            st.link_button(
                f"View on {book['data_source']}", url, use_container_width=True
            )

#similar books — visual recommendation matrix (4 covers with hyperlinked cards)
    if st.session_state.show_similar:
        st.write("")
        others = [
            i for i in st.session_state.pool_idx
            if i != st.session_state.selected_idx
        ]
        similar = app_df.loc[others].nlargest(4, "rating")
        if similar.empty:
            st.info("Only one book matches this selection — nothing similar to show.")
        else:
            st.markdown("**Similar Reads**")
            cards = ""
            for row in similar.itertuples():
                sim_cover = resolve_cover(row.img_url)
                
                # Retrieve URL safely; default to '#' if not available
                book_link = row.book_url if isinstance(row.book_url, str) and row.book_url.strip() else "#"
                target_attr = 'target="_blank"' if book_link != "#" else ""
                
                # We wrap the entire .similar-item block inside a styled anchor link
                cards += (
                    f'<a href="{book_link}" {target_attr} class="similar-card-link">'
                    '<div class="similar-item">'
                    f'<img src="{sim_cover}"/>'
                    f'<p class="similar-item-title">{row.book_name}</p>'
                    f'<p class="stars" style="font-size:0.8rem; margin:2px 0;">'
                    f'{star_string(row.rating)}</p>'
                    '</div>'
                    '</a>'
                )
            st.markdown(
                f'<div class="similar-matrix">{cards}</div>',
                unsafe_allow_html=True,
            )