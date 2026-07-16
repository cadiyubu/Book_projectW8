"""Shared helper functions — Book Recommendation System.

Every function here was written inside a notebook first and hoisted afterwards.

Source map
----------
read_file, out_csv, summarise_dataframe  -> used across all notebooks
go_url                                   -> 1_Webscraping_books.ipynb
extract_fields, fetch_list               -> 2_GoogleBooks_API.ipynb
norm, sim, find_gr_match                 -> 3_Merge_cleaning.ipynb  (GoodReads backfill)
ol_lookup                                -> 3_Merge_cleaning.ipynb  (Open Library backfill)
hc_search, hc_best_match, _pick, _norm   -> 3_Merge_cleaning.ipynb  (Hardcover backfill)
norm_tag, map_tag_to_canonicals          -> 4_EDA_clustering.ipynb
scale_features, sweep_k, decision_plot   -> 4_EDA_clustering.ipynb
cluster_genre_heatmap,
cluster_pca_scatter,
cluster_numeric_boxplot                  -> 4_EDA_clustering.ipynb
chunk_token_ids, score_texts             -> 5_Sentiment_mood.ipynb

Heavy / environment-specific imports (torch, transformers) are done lazily inside
the function that needs them, so importing this module from notebook 1 does not
require the `sentiment` conda environment.
"""

import os
import re
import time
from difflib import SequenceMatcher, get_close_matches

import numpy as np
import pandas as pd
import requests
import yaml


# =============================================================================
# 1. DATA LOADING / SAVING
# =============================================================================

def read_file(yaml_path, inp_data_section, file_name):
    """Load a CSV whose path is stored in a YAML config.
    Returns a DataFrame, or None on a handled error.

    sep=None + engine='python' lets pandas sniff the delimiter, which also
    absorbs Windows CRLF/BOM exports without choking.
    """
    # Read the YAML config
    try:
        with open(yaml_path, "r") as file:
            cfg = yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Config file not found: {yaml_path}")
        return None
    except yaml.YAMLError as e:
        print(f"Could not parse YAML: {e}")
        return None

    # Look up the CSV path inside the config
    try:
        csv_path = cfg[inp_data_section][file_name]
    except KeyError as e:
        print(f"Missing key in config: {e}")
        return None

    # Load the CSV
    return pd.read_csv(csv_path, sep=None, engine="python")


def out_csv(df, yaml_path, output_section_yaml, file_name):
    """Write a DataFrame to the CSV path stored under
    cfg[output_section_yaml][file_name] in the YAML config.

    """
    try:
        with open(yaml_path, "r") as file:
            cfg = yaml.safe_load(file)
    except:
        print("Yaml configuration file not found!")
        return None

    df.to_csv(cfg[output_section_yaml][file_name], index=False)
    print(f"File saved to: {cfg[output_section_yaml][file_name]}")


def summarise_dataframe(df):
    """Print shape, dtypes, null counts, and basic stats."""
    print(f"Shape: {df.shape}")
    print("\n--- Null counts ---")
    print(df.isnull().sum()[df.isnull().sum() > 0])
    print("\n--- Dtypes ---")
    print(df.dtypes)


# =============================================================================
# 2. WEB SCRAPING — GoodReads  (1_Webscraping_books.ipynb)
# =============================================================================

BASE = "https://www.goodreads.com"
HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    )
}


def go_url(url, headers=HEADERS, timeout=10):
    """Fetch URL, return BeautifulSoup or None on failure"""
    from bs4 import BeautifulSoup  # lazy: only the scraping notebook needs bs4

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            print(f"⚠️ status {resp.status_code} — {url}")
            return None
        return BeautifulSoup(resp.content, "html.parser")
    except requests.RequestException as e:
        print(f"⚠️ request failed — {url} — {e}")
        return None


# =============================================================================
# 3. GOOGLE BOOKS API  (2_GoogleBooks_API.ipynb)
# =============================================================================

GB_BASE_URL = "https://www.googleapis.com/books/v1/volumes"


def extract_fields(item: dict, source_list: str) -> dict:
    """
    Parse a single Google Books API volume item into the project schema.

    Parameters
    ----------
    item : dict
        A single element from the API response 'items' list.
    source_list : str
        The list label to inject (mirrors GoodReads source_list values).

    Returns
    -------
    dict with keys matching goodreads.csv column names.
    Missing fields are None — not dropped here.
    """
    vi = item.get('volumeInfo', {})   # if missing, return an empty dict so the next .get() cannot crash

    # authors: take first only, matching GoodReads single-author format
    authors = vi.get('authors', [])
    author = authors[0] if authors else None

    # genres: pipe-separated string, matching GoodReads format
    categories = vi.get('categories', [])
    genres = '|'.join(categories) if categories else None

    # thumbnail image
    img_links = vi.get('imageLinks', {})
    img_url = img_links.get('thumbnail') or img_links.get('smallThumbnail')

    return {
        'book_name': vi.get('title'),
        'book_url': vi.get('infoLink'),        # Google Books page (no list URL equivalent)
        'source_list': source_list,
        'author': author,
        'rating': vi.get('averageRating'),     # float or None
        'synopsis': vi.get('description'),
        'pages': vi.get('pageCount'),          # int or None
        'pub_date': vi.get('publishedDate'),   # variable precision: YYYY / YYYY-MM / YYYY-MM-DD
        'genres': genres,
        'img_url': img_url,
        'data_source': 'google_books',
    }


def fetch_list(list_name: str, query: str, api_key: str, log,
               target: int = 500, max_results: int = 40,
               delay_seconds: float = 1.0, base_url: str = GB_BASE_URL) -> list:
    """
    Fetch up to `target` books for one list from the Google Books API.

    Pagination: startIndex increments by the number of items returned.
    Stops early if the API returns no items (end of results).
    Retries up to 3 times on 5xx errors with exponential backoff.
    Backs off 60 s on 429 (quota exceeded).

    In 2_GoogleBooks_API.ipynb this function read API_KEY, MAX_RESULTS,
    TARGET_PER_LIST, DELAY_SECONDS, BASE_URL and `log` from the notebook globals.
    Here they are explicit parameters. The body is unchanged.

    Parameters
    ----------
    list_name : str    Human-readable label injected as source_list.
    query     : str    Subject search string sent to the API.
    api_key   : str    Google Books API key.
    log       : logging.Logger  Logger configured in the notebook.
    target    : int    Maximum books to retrieve for this list.

    Returns
    -------
    list of dicts (one per book, schema from extract_fields)
    """
    records = []
    start_index = 0

    while len(records) < target:
        params = {
            'q': query,
            'maxResults': max_results,
            'startIndex': start_index,
            'printType': 'books',
            'langRestrict': 'en',
            'key': api_key,
        }

        # Retry loop for transient server errors
        for attempt in range(3):
            try:
                resp = requests.get(base_url, params=params, timeout=10)

                if resp.status_code == 429:
                    log.warning('Rate limit hit — sleeping 60 s')
                    time.sleep(60)
                    continue

                if resp.status_code >= 500:
                    wait = 2 ** attempt
                    log.warning(f'Server error {resp.status_code} — retry {attempt+1}/3 in {wait}s')
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                break  # success

            except requests.exceptions.RequestException as e:
                log.error(f'Request failed: {e}')
                if attempt == 2:
                    log.error(f'Giving up on list "{list_name}" at startIndex={start_index}')
                    return records
                time.sleep(2 ** attempt)

        data = resp.json()
        items = data.get('items', [])

        if not items:
            log.info(f'[{list_name}] No more results at startIndex={start_index}')
            break

        for item in items:
            records.append(extract_fields(item, list_name))
            if len(records) >= target:
                break

        log.info(f'[{list_name}] Fetched {len(records)} / {target}')

        start_index += len(items)
        time.sleep(delay_seconds)

    return records


# =============================================================================
# 4. MATCHING & BACKFILL  (3_Merge_cleaning.ipynb)
# =============================================================================

TITLE_CUTOFF = 0.90
TITLE_CUTOFF_STRICT = 0.97
AUTHOR_CUTOFF = 0.85

FILL_COLS = ['author', 'rating', 'synopsis', 'pages', 'pub_date', 'genres', 'img_url']


def norm(s: str) -> str:
    """Normalise a title/author string for fuzzy matching.

    Lowercase, drop parenthesised subtitles, strip punctuation, collapse
    whitespace.
    """
    if pd.isna(s):
        return ""
    s = str(s).lower()
    s = re.sub(r'\([^)]*\)', '', s)
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    for art in ('the ', 'a ', 'an '):
        if s.startswith(art):
            s = s[len(art):]
    return s


def sim(a: str, b: str) -> float:
    """Similarity ratio between two already-normalised strings."""
    return SequenceMatcher(None, a, b).ratio()


def find_gr_match(q_title, q_author, gr_titles_norm, gr_authors_norm):
    """Locate a GoodReads row index matching a normalised title (+ author).

    Two-tier rule: with an author available, accept a looser title match
    (TITLE_CUTOFF) provided the author also clears AUTHOR_CUTOFF. Without an
    author, demand a near-exact title (TITLE_CUTOFF_STRICT).

    """
    if not q_title:
        return None
    if q_author:
        for cand in get_close_matches(q_title, gr_titles_norm, n=5, cutoff=TITLE_CUTOFF):
            gr_idx = gr_titles_norm.index(cand)
            if sim(q_author, gr_authors_norm[gr_idx]) >= AUTHOR_CUTOFF:
                return gr_idx
        return None
    else:
        cand = get_close_matches(q_title, gr_titles_norm, n=1, cutoff=TITLE_CUTOFF_STRICT)
        return gr_titles_norm.index(cand[0]) if cand else None


# --- Open Library -------------------------------------------------------------

OL_URL = "https://openlibrary.org/search.json"
OL_HEADERS = {"User-Agent": "IronhackW9-BookRec/1.0 (student project)"}
OL_SLEEP = 1.1

# synopsis excluded: not available via search.json
OL_FIELDS = ['author', 'rating', 'pages', 'pub_date', 'genres', 'img_url']


def ol_lookup(title: str, author: str) -> dict:
    """One OL query -> dict of available fields (only keys OL returned)."""
    params = {
        "title": str(title),
        "fields": "ratings_average,number_of_pages_median,first_publish_year,"
                  "author_name,subject,cover_i",
        "limit": 1,
    }
    if pd.notna(author):
        params["author"] = str(author)
    out = {}
    try:
        r = requests.get(OL_URL, params=params, headers=OL_HEADERS, timeout=15)
        r.raise_for_status()
        docs = r.json().get("docs", [])
        if not docs:
            return out
        d = docs[0]
        if d.get("ratings_average") is not None:
            out['rating'] = round(float(d["ratings_average"]), 2)
        if d.get("number_of_pages_median") is not None:
            out['pages'] = float(d["number_of_pages_median"])
        if d.get("first_publish_year") is not None:
            out['pub_date'] = str(d["first_publish_year"])      # year only
        if d.get("author_name"):
            out['author'] = d["author_name"][0]
        if d.get("subject"):
            out['genres'] = "|".join(d["subject"][:15])         # noisy, cap it
        if d.get("cover_i") is not None:
            out['img_url'] = f"https://covers.openlibrary.org/b/id/{d['cover_i']}-L.jpg"
    except Exception as e:
        print(f"  ⚠️ {str(title)[:40]!r}: {e}")
    return out


# --- Hardcover ------------------------------------------------------

HC_URL = "https://api.hardcover.app/v1/graphql"
HC_SLEEP = 1.1   # 60 req/min hard limit
HC_FIELDS = ['author', 'rating', 'synopsis', 'pages', 'pub_date', 'genres', 'img_url']

HC_SEARCH_Q = """
query Search($q: String!) {
  search(query: $q, query_type: "Book", per_page: 5, page: 1) { results }
}
"""


def hc_search(title):
    """POST one search query to the Hardcover endpoint and return the raw JSON.

    The token is read from the HARDCOVER_API_TOKEN environment variable.
    """
    headers = {
        "authorization": os.environ["HARDCOVER_API_TOKEN"],
        "content-type": "application/json",
    }
    r = requests.post(HC_URL, headers=headers,
                      json={"query": HC_SEARCH_Q, "variables": {"q": title}}, timeout=30)
    r.raise_for_status()
    return r.json()


def _norm(s):
    """Light normaliser used only for Hardcover title scoring."""
    return str(s).strip().lower() if s is not None else ""


def _pick(doc):
    """Project one Hardcover document onto the project schema.

    Rating is gated on ratings_count > 0 — Hardcover returns 0.0 for books with
    no ratings at all, which would otherwise be backfilled as a real zero.
    """
    authors = doc.get("author_names") or []
    image = doc.get("image") or {}
    genres = doc.get("genres") or []

    rating = doc.get("rating")
    if rating is not None and doc.get("ratings_count", 0) == 0:
        rating = None   # no real data on Hardcover

    return {
        "author": authors[0] if authors else None,
        "rating": rating,                           # now gated
        "synopsis": doc.get("description"),
        "pages": doc.get("pages"),
        "pub_date": doc.get("release_year"),
        "genres": "|".join(genres) if genres else None,
        "img_url": image.get("url"),
    }


def hc_best_match(title):
    """Return the best-scoring Hardcover hit for `title`, or None below TITLE_CUTOFF."""
    try:
        hits = hc_search(title)["data"]["search"]["results"]["hits"]
    except Exception as e:
        print(f"  ! search failed for {title!r}: {e}")
        return None
    tnorm, best, best_score = _norm(title), None, 0.0
    for h in hits:
        doc = h.get("document", {})
        score = SequenceMatcher(None, tnorm, _norm(doc.get("title"))).ratio()
        if score > best_score:
            best_score, best = score, doc
    return _pick(best) if best_score >= TITLE_CUTOFF else None


# =============================================================================
# 5. GENRE CLEANING  (4_EDA_clustering.ipynb)
# =============================================================================

# Keyword rules collapsing ~1.6k messy raw tags into 12 canonical genres.
# A raw tag can map to several canonicals; a tag matching nothing is dropped.
GENRE_RULES = {
    'science_fiction':  ['science fiction', 'sci-fi', 'scifi', 'post apocalyptic', 'dystopia', 'post-communism'],

    'fantasy':          ['fantasy', 'fae', 'magic', 'vampire', 'paranormal', 'demonology', 'angels', 'merlin (legendary character)', 'ancient guardians', 'earth (planet)'],

    'romance':          ['romance', 'romantasy', 'chick lit', 'dating', 'love only', 'yours until dawn', 'love', 'love stories', 'abused wives', 'bodyguards', 'divorced women', 'blind', 'bachelors', 'scotland', 'boy trouble', 'family life'],

    'mystery':          ['mystery', 'crime', 'detective', 'noir', 'blessing and cursing', 'thriller', 'suspense', 'sudden death', 'horror', 'fear street'],

    'historical':       ['historical fiction', 'historical', 'war', 'false imprisonment', 'veterans', 'monarchy', 'aristocracy', 'inheritance and succession', 'cossacks', 'rum shop', 'great britain', 'south with endurance', 'guy mannering', 'antarctica', 'astrologers'],

    'young_adult':      ['young adult', 'ya', 'juvenile', 'college students', 'school', 'adolescent', 'adolescents', 'youth', 'emerging adults', 'emerging adulthood', 'social media and youth', 'cerebral ischemia in young adults', 'media exposure', 'child psychiatry', 'brain'],

    'childrens':        ['children', 'childrens', 'picture book', 'middle grade', 'kids', 'brothers and sisters', 'five children', 'dogs', 'behavior', 'brothers', 'toys', 'melody'],

    'literary':         ['literary', 'literature', 'novels', 'general', 'tuesdays with morrie', 'autumn', 'criticism', 'essays', 'books and reading', 'africa', 'fathers and daughters', 'the house of mirth', 'new york (n.y.)'],

    'classics':         ['classic', 'classics', 'barchester', 'annotated edition', 'illustrated edition', 'annotated', 'illustrated', 'americans', 'accident victims', "anne's house of dreams", 'the castle', 'families', 'authority'],

    'contemporary':     ['contemporary', 'book club', 'savor the moment', 'bakers', 'domestic fiction', 'modern', 'state of the union'],

    'adventure':        ['adventure', 'pirates', 'survival', 'voyages'],

    'fiction':          [
        'fiction', 'fictitious character', 'humor', 'poetry', 'graphic novel', 'comic', 'manga', 'boys',
        'philosophy', 'philosophie', 'psychology', 'amyotrophic lateral sclerosis', 'autism spectrum disorders',
        'history', 'geschichte', 'england', 'brazil', 'brasyl', 'physics', 'biology', 'chemistry',
        'popular science', 'elephants', 'medical', 'health & fitness', 'self-help', 'self help', 'personal development',
        'family & relationships', 'business', 'economics', 'finance', 'religion', 'religious',
        'spirituality', 'christian', 'nonfiction', 'non-fiction', 'memoir', 'biography', 'autobiography',
        'large print', 'foreign language study', 'large type books', 'trauma', 'pedagogy', 'oncology',
        'musical groups', 'education', 'bays', 'computers', 'electronic books', 'orchestra',
        'the billboard', 'the soda fountain', 'the readers’ advisory guide', 'tuning in', 'sociology',
        "john brookes' natural landscapes", 'kurzgeschichten', "the author's annual", 'music', 'soda fountains',
        "nullification (states' rights)", 'language arts & disciplines', 'audiobooks', 'political science',
        'gardening', 'allemand (langue)', 'authorship'
    ]
}


def norm_tag(tag):
    """Lowercase + strip a single raw genre tag."""
    return tag.strip().lower()


def map_tag_to_canonicals(tag):
    """Return the set of canonical genres a raw tag maps to (possibly empty)."""
    return {canon for canon, kws in GENRE_RULES.items() if any(kw in str(tag).lower() for kw in kws)}


# =============================================================================
# 6. CLUSTERING  (4_EDA_clustering.ipynb)
# =============================================================================

def scale_features(X):
    """Min-max scale a feature matrix, preserving column names and index."""
    from sklearn.preprocessing import MinMaxScaler

    return pd.DataFrame(
        MinMaxScaler().fit_transform(X), columns=X.columns, index=X.index)


def sweep_k(X, k_range=range(2, 25), min_size=30):
    """Fit KMeans across a range of k and report the metrics used to choose one.

    min_cluster / n_below_floor implement the minimum-cluster-size floor: on
    sparse binary genre data the silhouette score is unreliable, so cluster
    viability is judged on size, not separation.
    """
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    results = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        sizes = np.bincount(labels)
        results.append({
            'k': k,
            'inertia': km.inertia_,                     # elbow method: sum of squared distances to the nearest centroid
            'silhouette': silhouette_score(X, labels),  # separation (-1..1): <0 misallocated, 0 overlapping, 1 well separated
            'min_cluster': sizes.min(),
            'n_below_floor': (sizes < min_size).sum(),
        })
    return pd.DataFrame(results)


def decision_plot(df):
    """Plot elbow + silhouette from a sweep_k result and print the largest viable k."""
    import matplotlib.pyplot as plt

    survivors = df[df['n_below_floor'] == 0]
    k_ceiling = survivors['k'].max()
    print(f"Largest k with all clusters ≥ floor: {k_ceiling}")

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(df['k'], df['inertia'], marker='o')
    ax[0].set_title('Elbow (inertia)')
    ax[1].plot(df['k'], df['silhouette'], marker='o')
    ax[1].set_title('Silhouette')
    plt.show()


# =============================================================================
# 7. CLUSTER VISUALISATION  (4_EDA_clustering.ipynb)
# =============================================================================

def cluster_genre_heatmap(books, genre_matrix, cluster_col):
    """Rows = clusters, cols = genres, value = share of cluster's books with that genre."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    labels = books[cluster_col].dropna().astype(int)
    gm = genre_matrix.loc[labels.index]          # align: only clustered rows
    comp = gm.groupby(labels).mean()             # mean of 0/1 = share

    plt.figure(figsize=(14, 0.6 * comp.shape[0] + 2))
    sns.heatmap(comp, annot=True, fmt='.2f', cmap='Blues',
                cbar_kws={'label': 'share of books with genre'})
    plt.title(f'{cluster_col} — genre composition per cluster')
    plt.ylabel('cluster')
    plt.xlabel('genre')
    plt.tight_layout()
    plt.savefig(f'../figures/{cluster_col}_genre_heatmap.png', dpi=150)
    plt.show()


def cluster_pca_scatter(X_scaled, labels, name):
    """Project scaled feature matrix to 2D, color by cluster."""
    import matplotlib.pyplot as plt
    from sklearn.decomposition import PCA

    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X_scaled)
    var = pca.explained_variance_ratio_.sum()

    plt.figure(figsize=(8, 6))
    sc = plt.scatter(coords[:, 0], coords[:, 1],
                     c=labels.astype(int), cmap='tab10', s=18, alpha=0.7)
    plt.legend(*sc.legend_elements(), title='cluster', bbox_to_anchor=(1.02, 1))
    plt.title(f'{name} — PCA 2D ({var:.0%} variance explained)')
    plt.tight_layout()
    plt.savefig(f'../figures/{name}_pca_scatter.png', dpi=150)
    plt.show()


def cluster_numeric_boxplot(books, cluster_col, num_col):
    """Distribution of a numeric column per cluster (used for the f2/f3/f4 experiments)."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    sub = books.dropna(subset=[cluster_col])
    plt.figure(figsize=(8, 4))
    sns.boxplot(data=sub, x=cluster_col, y=num_col)
    plt.title(f'{cluster_col} — {num_col} distribution per cluster')
    plt.tight_layout()
    plt.savefig(f'../figures/{cluster_col}_{num_col}_boxplot.png', dpi=150)
    plt.show()


# =============================================================================
# 8. SENTIMENT / MOOD  (5_Sentiment_mood.ipynb)
#
# torch / transformers / tqdm are imported INSIDE the functions on purpose:
# these run in the isolated `sentiment` conda env, and importing this module
# from notebooks 1-4 must not require them.
# =============================================================================

# The seven Ekman classes returned by j-hartmann/emotion-english-distilroberta-base,
# mapped to the single-word, reader-facing labels used in the Streamlit dropdown.
MOOD_MAP = {
    "joy": "Uplifting",
    "sadness": "Melancholic",
    "fear": "Suspenseful",
    "anger": "Intense",
    "surprise": "Twisty",
    "disgust": "Gritty",
    "neutral": "Contemplative",
}


def chunk_token_ids(text: str, tokenizer, max_tokens: int = 510) -> list[list[int]]:
    """Split `text` into token-id chunks that fit inside RoBERTa's 512-token window.

    Args:
        text: Raw synopsis text.
        tokenizer: The HuggingFace tokenizer paired with the emotion model.
        max_tokens: Maximum tokens per chunk (512 minus the two special tokens).

    Returns:
        A list of token-id lists. Always at least one chunk, even for empty text.
    """
    token_ids = tokenizer.encode(text, add_special_tokens=False)
    chunks = [token_ids[i:i + max_tokens] for i in range(0, len(token_ids), max_tokens)]
    return chunks or [[]]


def score_texts(texts: list[str], tokenizer, model, device,
                batch_size: int = 16, max_tokens: int = 510) -> np.ndarray:
    """Score texts with the emotion model, mean-pooling across chunks.

    Long texts are split into chunks; each chunk is scored independently and the
    resulting probability vectors are averaged back into one vector per text.

    Args:
        texts: Synopsis strings, one per book.
        tokenizer: HuggingFace tokenizer.
        model: Sequence-classification model in eval mode.
        device: torch device the model lives on ("mps", "cuda" or "cpu").
        batch_size: Number of chunks per forward pass.
        max_tokens: Chunk size passed to chunk_token_ids.

    Returns:
        Array of shape (len(texts), n_emotions) — each row a probability
        distribution over the emotion classes, summing to 1.
    """
    import torch
    from tqdm.auto import tqdm

    # Flatten every text into its chunks, tracking which text each chunk belongs to.
    chunk_texts: list[str] = []
    chunk_owner: list[int] = []

    for text_idx, text in enumerate(texts):
        for token_ids in chunk_token_ids(str(text), tokenizer, max_tokens):
            chunk_texts.append(tokenizer.decode(token_ids))
            chunk_owner.append(text_idx)

    batch_probs = []
    with torch.no_grad():
        for start in tqdm(range(0, len(chunk_texts), batch_size), desc="Scoring chunks"):
            batch = chunk_texts[start:start + batch_size]
            encoded = tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            ).to(device)

            logits = model(**encoded).logits
            batch_probs.append(torch.softmax(logits, dim=-1).cpu().numpy())

    chunk_probs = np.vstack(batch_probs)
    chunk_owner_arr = np.array(chunk_owner)

    # Mean-pool chunk probabilities back up to one vector per text.
    pooled = np.zeros((len(texts), chunk_probs.shape[1]))
    for text_idx in range(len(texts)):
        pooled[text_idx] = chunk_probs[chunk_owner_arr == text_idx].mean(axis=0)

    return pooled
