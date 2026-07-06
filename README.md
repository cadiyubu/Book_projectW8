# Book Recommendation System — Week 9

## Description
End-to-end book recommendation system: dual-sourced data (web scraping + API,
500 books each) from GoodReads, cleaned and explored, feeding a recommendation
model deployed as a Streamlit proof-of-concept.

## Data source
GoodReads — via popular user lists, top-200-by-year lists, and award pages
(scraping), plus GoodReads API (interaction-focused endpoints).

## Project structure
```
.
├── .gitignore
├── README.md
├── config.yaml
├── pyproject.toml
├── uv.lock
├── data/
│   ├── raw/
│   │   ├── scraped/    # web-scraped books, untouched
│   │   └── api/        # API-sourced books, untouched
│   └── clean/          # cleaned/merged dataset
├── figures/            # plots
├── models/             # trained recommender artifacts (.pkl)
├── app/
│   └── app.py          # Streamlit POC
├── notebooks/
│   ├── .env
│   └── functions.py
└── slides/
```

## Installation
See environment setup steps below (uv + Jupyter kernel).

## Usage
Work through notebooks in order (scrape → API → clean → explore → model),
then run `streamlit run app/app.py`.

## Key findings
_TBD as project progresses._

## Contributors
Diana Yule (Caro)
