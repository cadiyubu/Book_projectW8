# Words4You — Book Recommender 

A book discovery tool for readers who know **how they want to feel**, not what they want to read.
The catalogue is built from two independent sources, backfilled from three more, clustered by
genre co-occurrence, tagged with a transformer-derived *mood*, and served as a Streamlit app.

**Final catalogue: 1,077 books × 29 columns** (`data/clean/catalog_mood.csv`).

---

## Use cases & user stories

| # | User story | Implemented by |
|---|---|---|
| 1 | *As a reader who doesn't know what to read next, I want one concrete book suggested to me, so I don't have to browse a list of 1,000.* | Spotlight card — a single book at a time, with a "Another book" reroll. |
| 2 | *As a reader in a specific emotional state, I want to filter books by **mood** rather than genre, so the recommendation matches how I want to feel.* | Mood filter (sidebar "Discovery Center") — 7 reader-facing moods derived from the synopsis (see §Mood). Low-confidence books are excluded from the pool; the random pick is **weighted by `emotion_conf`**, so higher-confidence classifications surface more often. |
| 3 | *As a reader with practical constraints, I want to bound the suggestion by rating, length and publication year, so I don't get a 900-page 1890s novel on a commute.* | Range sliders on `rating`, `pages`, `pub_date`. |
| 4 | *As a reader who knows what they **don't** like, I want to exclude genres and be surprised within what's left.* | "Roulette" — multiselect exclusion of `cluster_name` values, then a random pick. |
| 5 | *As a reader who liked the suggested book, I want more books like it.* | "See Similar Books" — a toggleable 4-cover visual grid of the top-rated books in the active pool. |
| 6 | *As a reader who trusts curated lists, I want quick picks from the best lists, so I can grab something proven without filtering at all.* | Source shelves — the two `source_list`s with the highest average rating each show 3 random books rated ≥ 4.0, with hyperlinked titles and a "Shuffle" reroll. |

---

## Pipeline

```
1_Webscraping_books   GoodReads Listopia + book detail pages   -> data/raw/goodreads.csv
2_GoogleBooks_API     Google Books API, paginated per subject  -> data/raw/google_books.csv
3_Merge_cleaning      concat + dedupe + 3-source backfill      -> data/clean/booksDB.csv
4_EDA_clustering      genre canonicalisation + KMeans          -> data/clean/streamlitcatalog.csv
5_Sentiment_mood      emotion model -> reader-facing mood      -> data/clean/catalog_mood.csv
app/app.py            Streamlit UI (reads catalog_mood.csv)
```

The pipeline is **strictly one-directional**: no notebook writes to a file an earlier notebook
produced. 

---

## Data sourcing (two independent methods)

| Method | Source | Rows in final catalogue |
|---|---|---|
| Web scraping (`requests` + BeautifulSoup) | GoodReads — Listopia popular lists → book detail pages | 617 |
| REST API (`requests`) | Google Books `volumes` endpoint, paginated by subject | 460 |

Scraping is randomised 1–6 s sleeps, real user-agent,with checkpoints every
25 books, reloads already-scraped URLs on restart.

### Backfill (filling nulls, not adding rows)

Neither source is complete. Three backfill passes run in `3_Merge_cleaning`, each using a
**match-once, fill-many** pattern with a boolean flag:

| Pass | Endpoint | Match rule | Flag |
|---|---|---|---|
| GoodReads cross-fill | the scraped frame itself | fuzzy title ≥ 0.90 **and** author ≥ 0.85; title ≥ 0.97 if no author | `gr_matched` |
| Open Library | API `search.json` | title (+ author when present) | `ol_matched` |
| Hardcover | API `search` | best title match ≥ 0.90 | `hc_matched` |

Design rules that cost time and are worth stating:
- **Only nulls are filled.** An existing value is never overwritten by a lower-trust source.
- **Hardcover's `rating` is gated on `ratings_count > 0`** — the API returns `0.0` for unrated
  books, which would otherwise be backfilled as a real zero and drag every average down.

---

## Clustering (unsupervised)

Feature matrix: **binary genre matrix only.** Four candidate models were built and three rejected:

| Model | Features | Verdict |
|---|---|---|
| f1 | genres | Rejected — `fiction` appears on 83% of books, acting as a stopword; it alone defined a 30.5% cluster. |
| **f1b** | genres, `fiction` dropped, books with <2 remaining tags excluded | **Selected.** k = 11, KMeans. |
| f2 / f3 / f4 | genres + pages / + rating / + year | Rejected — those axes are exposed as *user filters* in the app. |

**On silhouette:** on sparse binary data it is close to meaningless, and the PCA scatter shows no
visual separation — both expected, neither disqualifying. Model choice rests on the **genre
composition heatmaps** (`figures/cluster_f1b_genre_heatmap.png`) plus a **minimum cluster-size floor of 30**.

11  clusters, hand-labelled: Romance + Fantasy · Fantasy + Science Fiction · Contemporary + Young
Adult · Historical, Classics · Literary + Classics · Childrens + Fantasy · Contemporary +
Historical · Mystery + Contemporary · Young Adult, Classics · Adventure + Fantasy · Romance +
Contemporary.

**612 books are `clusterable`; 465 are not** (too few genre tags after the stopword drop). They
are not hidden — the app serves them through the non-cluster filters.


---

## Mood (transformer sentiment)

Model: **`j-hartmann/emotion-english-distilroberta-base`** — 7 Ekman classes, not VADER's
positive/negative axis. A book is not "positive"; it is *melancholic* or *twisty*.

- Synopses shorter than 60 characters are excluded (`mood_scored = False`).
- Synopses longer than RoBERTa's 512-token window are **chunked, scored per chunk, and
  mean-pooled** back into one probability vector — not truncated.
- The 7 emotions are mapped 1:1 onto reader-facing labels:

| Emotion | Mood | Books |
|---|---|---|
| fear | **Suspenseful** | 325 |
| neutral | **Contemplative** | 308 |
| sadness | **Melancholic** | 119 |
| joy | **Uplifting** | 111 |
| anger | **Intense** | 81 |
| disgust | **Gritty** | 76 |
| surprise | **Twisty** | 35 |
| — | not scored | 22 |

**Two flags, two questions — never collapsed:** `clusterable` answers *"was this book eligible for
genre clustering?"*; `mood_scored` answers *"did it have a usable synopsis?"*. A book can be one
and not the other.

### Honest limitations
1. **Domain shift.** The model was fine-tuned on tweets and dialogue, not publisher marketing copy.
   The shift is real and unmeasured.
2. **The synopsis is not the book.** classification is on how a book was *sold*, not what it contains.
3. **No ground truth → no accuracy figure.** Validation is three pre-registered *consistency*
   checks (variance across all 7 moods; median confidence 0.673 vs a 0.143 chance baseline;
   manual face-validity review), not a correctness measurement. 90 books (8.5%) fall below the
   0.40 confidence threshold and carry `mood_low_conf = True` — they are excluded from the mood
   filter pool.
4. Face validity is uneven: `Twisty` reads well; `Uplifting` and `Contemplative` produce visible
   misses. Documented in notebook 5, §11.


---

## The app — Words4You

Layout:

- **Sidebar "Discovery Center"** — three filter groups, each ending in its own action button:
  *Recommendation by Mood* (confidence-weighted pick), *Dynamic Filters* (rating / year / pages
  sliders) and *RoUleTte* (exclude genre clusters, get a random pick).
- **Spotlight** — one book at a time: cover, star rating, pages / year / genre pills, the
  full synopsis and a note explaining *why* this book was picked. "Another book" rerolls within
  the same pool; "See Similar Books" toggles a 4-cover grid of the pool's top-rated titles;
  "View on …" links to the source page.
- **Source shelves** — the two best-rated `source_list`s, 3 random books ≥ 4.0 each,
  hyperlinked, with a Shuffle button.

Robustness details worth noting: covers fall back to a bundled placeholder when the remote URL is
missing; sample sizes are capped at pool length (`min(3, len(pool))`) so tiny lists cannot raise;
an empty filter result shows a warning instead of crashing.

---

## Project structure

```
.
├── README.md
├── config.yaml              # every I/O path + sentiment params — no hard-coded paths in code
├── pyproject.toml           # uv-managed dependencies
├── uv.lock
├── .python-version          # 3.13
├── app/
│   └── app.py               # Streamlit app "Words4You"
├── data/
│   ├── raw/
│   │   ├── goodreads.csv        # scraped
│   │   ├── google_books.csv     # API
│   │   ├── combined_books.csv   # concatenated
│   │   └── all_books.csv        # concatenated + backfilled
│   └── clean/
│       ├── booksDB.csv           # cleaned master
│       ├── streamlitcatalog.csv  # + cluster_f1b, cluster_name, clusterable
│       └── catalog_mood.csv      # + mood columns  <- the file the app reads
├── figures/                 # heatmaps, PCA scatters, boxplots, mood distributions
├── notebooks/
│   ├── .env                     # HARDCOVER_API_TOKEN, GOOGLE_BOOKS_API_KEY (git-ignored)
│   ├── functions.py             # all shared helpers, hoisted from the notebooks
│   ├── 1_Webscraping_books.ipynb
│   ├── 2_GoogleBooks_API.ipynb
│   ├── 3_Merge_cleaning.ipynb
│   ├── 4_EDA_clustering.ipynb
│   └── 5_Sentiment_mood.ipynb
├── models/
└── slides/
    ├── Words4You_Week9.pptx  # 10-slide presentation (10 min incl. live demo)
    └── build_deck.js         # deck generator (pptxgenjs) — regenerate after edits
```

---

## Installation

**Notebook 5 runs in a separate environment.** `torch` + `transformers` are heavy and
platform-specific, so they live in an isolated `sentiment` conda env rather
than in `.venv`.

## Usage

```bash
# reproduce the pipeline (in order — each notebook consumes the previous one's output)
uv run jupyter lab       # run notebooks 1 -> 4
#                          run notebook 5 on the `sentiment` kernel

# launch the app
uv run streamlit run app/app.py
```

Every notebook reads and writes through `config.yaml`. 

## Key findings

- **A single source is never enough.** GoodReads scraping gives rich synopses but no reliable
  structured metadata; Google Books gives clean metadata but sparse ratings. The interesting work
  was the three-source backfill, not the retrieval.
- **Genre is a weak signal on its own.** 83% of books carry the tag `fiction` — a stopword, not a
  segment. Removing it is what turned clustering from a data artifact into a taste map.
- **Mood ≠ sentiment.** A 7-class emotion model separates *melancholic* from *gritty*; a
  positive/negative sentiment score cannot. But it classifies the *marketing copy*, not the book —
  a discovery aid, not ground truth.
- **Design constraint discovered late:** anything the user is meant to control (pages, rating,
  year) must stay *out* of the model, or the model quietly overrides the user.

## Contributors

Diana Yule (Caro) — Ironhack Data Analytics, Week 9.
Presentation link: [https://docs.google.com/presentation/d/1K2lg2DF18auJ1MVzhS6gWnm73jOiJEkb/edit?slide=id.p7#slide=id.p7]
Online Streamlink app: [https://bookappwords4you.streamlit.app/]
