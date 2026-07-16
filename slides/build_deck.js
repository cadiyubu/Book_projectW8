// 🤖 AI-generated deck builder — Words4You, Ironhack Week 9 (theme = app colors)
const pptxgen = require("pptxgenjs");
const path = require("path");

const ROOT = "/Users/dianayule/Documents/03_RESOURCES/Learning/DataAnalytics Ironhack/Week9/Project_W9";
const FIG = (p) => path.join(ROOT, "figures", p);
const OUT = path.join(ROOT, "slides", "Words4You_Week9.pptx");

// App palette (app/app.py CSS)
const C = {
  bg: "14171B", panel: "1A1D21", panel2: "181B1F", border: "2C333B",
  teal: "26A69A", tealDark: "0E4F4A", purple: "7E57C2", purpleLt: "9C6ADE",
  text: "E8EDF2", muted: "8A94A0", amber: "FFC107",
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.author = "Diana (Caro) Yule";
pres.title = "Words4You - Mood-based Book Recommender";

function baseSlide() {
  const s = pres.addSlide();
  s.background = { color: C.bg };
  return s;
}
function header(s, txt, sub) {
  s.addText(txt, { x: 0.6, y: 0.32, w: 12.1, h: 0.72, fontSize: 34, bold: true,
    color: C.text, fontFace: "Arial", margin: 0 });
  if (sub) s.addText(sub, { x: 0.6, y: 1.0, w: 12.1, h: 0.4, fontSize: 15,
    italic: true, color: C.teal, fontFace: "Arial", margin: 0 });
}

function card(s, x, y, w, h, fill) {
  s.addShape("roundRect", { x, y, w, h, rectRadius: 0.12,
    fill: { color: fill || C.panel }, line: { color: C.border, width: 1 } });
}
function pill(s, x, y, w, txt, o) {
  o = o || {};
  s.addShape("roundRect", { x, y, w, h: 0.44, rectRadius: 0.22,
    fill: { color: o.fill || C.bg }, line: { color: o.line || C.border, width: 1 } });
  s.addText(txt, { x: x + 0.05, y, w: w - 0.1, h: 0.44, align: "center", valign: "middle",
    fontSize: o.fs || 11.5, bold: true, color: o.color || C.text, fontFace: "Arial", margin: 0 });
}
function bigStat(s, x, y, w, num, label, numColor) {
  s.addText(num, { x, y, w, h: 1.0, fontSize: 60, bold: true, color: numColor || C.amber,
    align: "center", fontFace: "Arial", margin: 0 });
  s.addText(label, { x, y: y + 1.0, w, h: 0.4, fontSize: 13, color: C.muted,
    align: "center", fontFace: "Arial", margin: 0 });
}

// ---------------------------------------------------------- SLIDE 1 — TITLE
let s = baseSlide();
s.addImage({ path: FIG("backgroundlibrary.png"), x: 0, y: 0, w: 13.333, h: 7.5,
  sizing: { type: "cover", w: 13.333, h: 7.5 } });
s.addShape("rect", { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: "0A0C10", transparency: 30 } });
s.addText([
  { text: "Words", options: { color: C.text } },
  { text: "4", options: { color: C.amber } },
  { text: "You", options: { color: C.teal } },
], { x: 1.5, y: 2.15, w: 10.33, h: 1.35, fontSize: 72, bold: true, align: "center",
  fontFace: "Arial", margin: 0 });
s.addText("Find your next book by how you want to FEEL",
  { x: 1.5, y: 3.55, w: 10.33, h: 0.55, fontSize: 22, italic: true, color: C.text,
    align: "center", fontFace: "Arial", margin: 0 });
pill(s, 3.92, 4.45, 5.5, "Ironhack Data Analytics  ·  Week 9  ·  Diana (Caro) Yule",
  { fill: C.panel, fs: 13 });
pill(s, 2.72, 6.55, 1.9, "1,077 books", { fill: C.tealDark, color: "DFF6F3" });
pill(s, 4.72, 6.55, 1.9, "2 sources", { fill: C.tealDark, color: "DFF6F3" });
pill(s, 6.72, 6.55, 1.9, "11 clusters", { fill: C.tealDark, color: "DFF6F3" });
pill(s, 8.72, 6.55, 1.9, "7 moods", { fill: C.tealDark, color: "DFF6F3" });
s.addNotes("~30 s. Hook: 'How many of you know exactly WHAT you want to read tonight? Probably few. But everyone knows how they want to FEEL.' Introduce Words4You: a book recommender that filters by mood, not just genre.");

// ---------------------------------------------------- SLIDE 2 — THE PROBLEM
s = baseSlide();
header(s, "The problem: too many books, wrong question", "Genre tells you what a book IS. Mood tells you how it FEELS.");
card(s, 0.6, 1.7, 6.1, 4.3, C.panel2);
s.addText('"I don\u2019t know what to read next \u2014 I just know I want something uplifting."',
  { x: 1.0, y: 2.1, w: 5.3, h: 1.7, fontSize: 22, italic: true, color: C.purpleLt,
    fontFace: "Arial", margin: 0 });
s.addText("A reader in a bookshop, every single day.",
  { x: 1.0, y: 3.9, w: 5.3, h: 0.4, fontSize: 12, color: C.muted, fontFace: "Arial", margin: 0 });
s.addText("Catalogues answer with 1,000-item lists sorted by genre. Nobody browses 1,000 items.",
  { x: 1.0, y: 4.5, w: 5.3, h: 1.2, fontSize: 15, color: C.text, fontFace: "Arial", margin: 0 });
const rows2 = [
  ["\u274C", "Endless lists", "1,077 books is already too many to scan"],
  ["\u274C", "Genre \u2260 feeling", "'Fantasy' can be cozy, dark, funny or tragic"],
  ["\u2705", "One book at a time", "picked by mood, rating, length \u2014 your call"],
];
rows2.forEach((r, i) => {
  const y = 1.7 + i * 1.5;
  card(s, 7.0, y, 5.7, 1.3, C.panel);
  s.addText(r[0], { x: 7.25, y: y + 0.25, w: 0.7, h: 0.8, fontSize: 26, align: "center",
    valign: "middle", fontFace: "Arial", margin: 0 });
  s.addText(r[1], { x: 8.05, y: y + 0.18, w: 4.5, h: 0.45, fontSize: 17, bold: true,
    color: C.text, fontFace: "Arial", margin: 0 });
  s.addText(r[2], { x: 8.05, y: y + 0.66, w: 4.5, h: 0.5, fontSize: 12.5,
    color: C.muted, fontFace: "Arial", margin: 0 });
});
s.addNotes("~60 s. Frame the user story (rubric: use cases drive the build). The product idea: shrink 1,077 books to ONE suggestion the user can accept or reroll \u2014 and let mood be a first-class filter.");

// ------------------------------------------------------- SLIDE 3 — PIPELINE
s = baseSlide();
header(s, "How it\u2019s built: a one-way pipeline", "Six stages \u2014 each notebook consumes the previous one\u2019s output. No stage ever writes backwards.");
const stages = [
  ["1", "Scrape", "GoodReads lists", "goodreads.csv"],
  ["2", "API", "Google Books", "google_books.csv"],
  ["3", "Merge", "+ 3-source backfill", "booksDB.csv"],
  ["4", "Cluster", "KMeans on genres", "streamlitcatalog.csv"],
  ["5", "Mood", "RoBERTa emotions", "catalog_mood.csv"],
  ["6", "App", "Streamlit UI", "app.py"],
];
stages.forEach((st, i) => {
  const x = 0.6 + i * 2.08;
  card(s, x, 2.5, 1.88, 2.0, i === 5 ? C.tealDark : C.panel);
  s.addText(st[0], { x: x, y: 2.62, w: 1.88, h: 0.5, fontSize: 22, bold: true,
    color: C.amber, align: "center", fontFace: "Arial", margin: 0 });
  s.addText(st[1], { x: x, y: 3.12, w: 1.88, h: 0.45, fontSize: 16, bold: true,
    color: C.text, align: "center", fontFace: "Arial", margin: 0 });
  s.addText(st[2], { x: x + 0.08, y: 3.58, w: 1.72, h: 0.55, fontSize: 10.5,
    color: C.muted, align: "center", fontFace: "Arial", margin: 0 });
  s.addText(st[3], { x: x + 0.08, y: 4.1, w: 1.72, h: 0.35, fontSize: 9,
    color: C.teal, align: "center", fontFace: "Arial", margin: 0 });
  if (i < 5) s.addText("\u25B6", { x: x + 1.82, y: 3.2, w: 0.32, h: 0.5, fontSize: 14,
    color: C.purpleLt, align: "center", valign: "middle", fontFace: "Arial", margin: 0 });
});
pill(s, 2.87, 5.3, 7.6, "Every path lives in config.yaml \u2014 nothing hard-coded, fully re-runnable", { fill: C.panel, fs: 12.5 });
s.addNotes("~60 s. Beginner framing: think of it as an assembly line. Raw books go in on the left, a finished app comes out on the right. Key discipline: one-directional flow \u2014 notebook 5 never touches notebook 4\u2019s output. That is what makes it reproducible (rubric: full automation).");

// --------------------------------------------------- SLIDE 4 — DATA SOURCING
s = baseSlide();
header(s, "Two independent ways to get data", "Rubric requirement: at least two retrieval methods \u2014 we used scraping AND a REST API.");
card(s, 0.6, 1.7, 6.0, 3.6, C.panel2);
s.addText("WEB SCRAPING", { x: 0.95, y: 1.95, w: 5.3, h: 0.45, fontSize: 17, bold: true,
  color: C.teal, fontFace: "Arial", margin: 0 });
bigStat(s, 0.95, 2.45, 5.3, "617", "books \u00B7 GoodReads Listopia lists \u2192 detail pages");
s.addText("requests + BeautifulSoup \u2014 parse the HTML humans see",
  { x: 0.95, y: 4.35, w: 5.3, h: 0.6, fontSize: 13, color: C.text, align: "center",
    fontFace: "Arial", margin: 0 });
card(s, 6.85, 1.7, 6.0, 3.6, C.panel2);
s.addText("REST API", { x: 7.2, y: 1.95, w: 5.3, h: 0.45, fontSize: 17, bold: true,
  color: C.purpleLt, fontFace: "Arial", margin: 0 });
bigStat(s, 7.2, 2.45, 5.3, "460", "books \u00B7 Google Books volumes endpoint, paginated");
s.addText("requests \u2014 structured JSON straight from the source",
  { x: 7.2, y: 4.35, w: 5.3, h: 0.6, fontSize: 13, color: C.text, align: "center",
    fontFace: "Arial", margin: 0 });
pill(s, 0.6, 5.75, 3.9, "Polite: random 1\u20136 s sleeps", { fs: 12 });
pill(s, 4.7, 5.75, 3.9, "Resumable: checkpoint every 25 books", { fs: 12 });
pill(s, 8.8, 5.75, 3.9, "None-safe: missing element \u2192 None", { fs: 12 });
s.addNotes("~60 s. Beginner framing: scraping = reading the webpage like a human and extracting facts; API = asking the server politely for structured data. Neither source alone is complete \u2014 that motivates the next slide. Mention the scraper is polite (random delays) and resumable (checkpoints), so a crash never loses work.");

// ------------------------------------------------------ SLIDE 5 — BACKFILL
s = baseSlide();
header(s, "Merging: fill the holes, don\u2019t add rows", "Three extra services patch missing values \u2014 match once, fill many, flag the provenance.");
const passes = [
  ["GoodReads cross-fill", "fuzzy title \u2265 0.90 + author \u2265 0.85", "gr_matched"],
  ["Open Library", "search.json \u2014 title (+ author when present)", "ol_matched"],
  ["Hardcover (GraphQL)", "best title match \u2265 0.90", "hc_matched"],
];
passes.forEach((p, i) => {
  const y = 1.75 + i * 1.42;
  card(s, 0.6, y, 7.1, 1.22, C.panel);
  s.addText(p[0], { x: 0.95, y: y + 0.13, w: 4.3, h: 0.45, fontSize: 16, bold: true,
    color: C.text, fontFace: "Arial", margin: 0 });
  s.addText(p[1], { x: 0.95, y: y + 0.6, w: 4.6, h: 0.45, fontSize: 11.5,
    color: C.muted, fontFace: "Arial", margin: 0 });
  pill(s, 5.6, y + 0.38, 1.85, p[2], { fill: C.tealDark, color: "DFF6F3", fs: 10.5 });
});
card(s, 8.0, 1.75, 4.75, 4.28, C.panel2);
s.addText("Golden rules", { x: 8.3, y: 1.95, w: 4.15, h: 0.45, fontSize: 16, bold: true,
  color: C.amber, fontFace: "Arial", margin: 0 });
s.addText([
  { text: "Only nulls are filled \u2014 an existing value is never overwritten by a lower-trust source.", options: { bullet: true, breakLine: true, paraSpaceAfter: 10 } },
  { text: "Zero-rating gate: Hardcover returns 0.0 for unrated books \u2014 accepted only when ratings_count > 0.", options: { bullet: true, breakLine: true, paraSpaceAfter: 10 } },
  { text: "Remaining nulls are documented, not papered over.", options: { bullet: true } },
], { x: 8.3, y: 2.5, w: 4.2, h: 3.3, fontSize: 12.5, color: C.text, fontFace: "Arial", margin: 0 });
s.addNotes("~60 s. Analogy: the merge is like completing a puzzle with pieces from three extra boxes \u2014 but you only take a piece if YOUR box has a hole there. The zero-rating gate is the war story: an API returning 0.0 for 'no rating' would silently drag every average down. Data cleaning is mostly about not trusting your sources.");

// ----------------------------------------------------- SLIDE 6 — CLUSTERING
s = baseSlide();
header(s, "Finding the shelves: clustering by genre", "Unsupervised KMeans on a binary genre matrix \u2014 after one crucial fix.");
card(s, 0.6, 1.7, 4.7, 5.2, C.panel2);
s.addText("83%", { x: 0.9, y: 1.95, w: 4.1, h: 0.95, fontSize: 54, bold: true,
  color: C.amber, fontFace: "Arial", margin: 0 });
s.addText("of books carry the tag \u2018fiction\u2019 \u2014 a stopword, not a segment. It alone defined a giant junk cluster.",
  { x: 0.9, y: 2.95, w: 4.1, h: 1.05, fontSize: 13.5, color: C.text, fontFace: "Arial", margin: 0 });
s.addText("Fix: drop it \u2192 KMeans, k = 11, hand-labelled clusters like \u2018Romance + Fantasy\u2019.",
  { x: 0.9, y: 4.05, w: 4.1, h: 0.85, fontSize: 13.5, color: C.text, fontFace: "Arial", margin: 0 });
pill(s, 0.9, 5.05, 4.1, "612 clusterable \u00B7 465 served via filters", { fs: 11, fill: C.tealDark, color: "DFF6F3" });
s.addText("Validation: genre heatmaps + min cluster size 30 \u2014 silhouette is meaningless on sparse binary data.",
  { x: 0.9, y: 5.7, w: 4.1, h: 1.0, fontSize: 11, italic: true, color: C.muted, fontFace: "Arial", margin: 0 });
s.addImage({ path: FIG("cluster_f1b_genre_heatmap.png"), x: 5.6, y: 1.85, w: 7.15, h: 4.09 });
s.addText("Which genres define each cluster \u2014 the heatmap that picked the model",
  { x: 5.6, y: 6.05, w: 7.15, h: 0.4, fontSize: 11, italic: true, color: C.muted,
    align: "center", fontFace: "Arial", margin: 0 });
s.addNotes("~75 s. Beginner framing: clustering = letting the computer sort books onto shelves without being told the shelf names. The 'fiction' story is the teaching moment: the most frequent tag carries the least information \u2014 same reason search engines ignore the word 'the'. Point at the heatmap: dark cells = the genres that define each shelf. We named the shelves by reading this map.");

// ----------------------------------------------------------- SLIDE 7 — MOOD
s = baseSlide();
header(s, "Teaching the catalogue to feel: mood", "A transformer reads every synopsis and assigns one of 7 emotions \u2014 mapped to reader-facing moods.");
card(s, 0.6, 1.7, 5.3, 5.2, C.panel2);
s.addText("emotion-english-distilroberta-base", { x: 0.9, y: 1.95, w: 4.7, h: 0.7,
  fontSize: 15, bold: true, color: C.purpleLt, fontFace: "Courier New", margin: 0 });
s.addText([
  { text: "7 Ekman emotions \u2192 7 moods: fear\u2192Suspenseful, joy\u2192Uplifting, sadness\u2192Melancholic\u2026", options: { bullet: true, breakLine: true, paraSpaceAfter: 10 } },
  { text: "Not positive/negative sentiment \u2014 \u2018melancholic\u2019 and \u2018gritty\u2019 are different feelings.", options: { bullet: true, breakLine: true, paraSpaceAfter: 10 } },
  { text: "Long synopses: chunked, scored per chunk, mean-pooled \u2014 never truncated.", options: { bullet: true, breakLine: true, paraSpaceAfter: 10 } },
  { text: "1,055 of 1,077 books scored; picks are weighted by model confidence.", options: { bullet: true } },
], { x: 0.9, y: 2.75, w: 4.7, h: 3.9, fontSize: 13, color: C.text, fontFace: "Arial", margin: 0 });
s.addImage({ path: FIG("mood_distribution.png"), x: 6.25, y: 2.15, w: 6.5, h: 3.25 });
s.addText("Suspenseful (325) and Contemplative (308) dominate \u2014 publishers sell tension and depth",
  { x: 6.25, y: 5.55, w: 6.5, h: 0.4, fontSize: 11, italic: true, color: C.muted,
    align: "center", fontFace: "Arial", margin: 0 });
s.addNotes("~75 s. Beginner framing: the model is a reader that has seen millions of texts and learned what fear, joy or sadness sound like. It reads each synopsis and outputs 7 probabilities; we take the strongest one. Why not classic sentiment analysis? Because positive/negative is one axis \u2014 a thriller and a tragedy are both 'negative' but feel completely different.");

// ---------------------------------------------------- SLIDE 8 — LIMITATIONS
s = baseSlide();
header(s, "What this model can\u2019t promise", "Honest limitations \u2014 stated up front, not hidden in a footnote.");
const lims = [
  ["Synopsis \u2260 book", "We classify how a book was SOLD, not what it contains. A cheerfully marketed tragedy scores as Uplifting."],
  ["Domain shift", "The model was fine-tuned on tweets and dialogue \u2014 publisher marketing copy is different territory. The shift is real and unmeasured."],
  ["No ground truth", "Nobody labelled the \u2018true\u2019 mood \u2192 no accuracy figure. Instead: 3 pre-registered consistency checks (median confidence 0.673 vs 0.143 chance)."],
];
lims.forEach((l, i) => {
  const x = 0.6 + i * 4.28;
  card(s, x, 1.85, 4.08, 3.7, C.panel);
  s.addText(l[0], { x: x + 0.3, y: 2.15, w: 3.5, h: 0.55, fontSize: 18, bold: true,
    color: C.teal, fontFace: "Arial", margin: 0 });
  s.addText(l[1], { x: x + 0.3, y: 2.8, w: 3.5, h: 2.5, fontSize: 12.5,
    color: C.text, fontFace: "Arial", margin: 0 });
});
pill(s, 3.17, 6.0, 7.0, "90 low-confidence books (8.5%) are excluded from the mood filter", { fill: C.panel2, fs: 12.5 });
s.addNotes("~60 s. This slide is deliberate: knowing WHERE a model fails is as valuable as building it. The app reflects this \u2014 a Data Notice bar tells users the moods are aids, not truth, and low-confidence books never enter the mood pool. Honest limits beat inflated accuracy claims.");

// ------------------------------------------------------ SLIDE 9 — LIVE DEMO
s = baseSlide();
header(s, "Words4You \u2014 live demo", "One Streamlit app, four ways to discover.");
const feats = [
  ["Discovery Center", "Sidebar filters: pick a mood, bound rating / year / pages, or play RoUleTte by excluding genre clusters."],
  ["Spotlight", "One book at a time \u2014 glowing cover, stars, data pills, full synopsis, and WHY it was picked."],
  ["Similar Reads", "One click \u2192 a 4-cover grid of the top-rated books in your current pool."],
  ["Shelves + Shuffle", "The two best-rated source lists, three random \u2265 4.0 picks each, reroll anytime."],
];
feats.forEach((f, i) => {
  const x = 0.6 + (i % 2) * 6.25, y = 1.8 + Math.floor(i / 2) * 2.4;
  card(s, x, y, 6.0, 2.15, C.panel);
  s.addText(f[0], { x: x + 0.3, y: y + 0.22, w: 5.4, h: 0.5, fontSize: 17, bold: true,
    color: C.purpleLt, fontFace: "Arial", margin: 0 });
  s.addText(f[1], { x: x + 0.3, y: y + 0.75, w: 5.4, h: 1.25, fontSize: 12.5,
    color: C.text, fontFace: "Arial", margin: 0 });
});
pill(s, 4.87, 6.55, 3.6, "\u25B6  switching to the app", { fill: C.tealDark, color: "DFF6F3", fs: 13 });
s.addNotes("~2.5 min INCLUDING the demo. Script: (1) type a name \u2192 greeting; (2) pick 'Uplifting' \u2192 Recommend by mood; (3) 'Another book' to reroll; (4) 'See Similar Books' \u2192 4-cover grid; (5) Shuffle a shelf. Keep the demo to 4 clicks \u2014 rehearse it. If wifi/app fails, this slide IS the fallback.");

// --------------------------------------------- SLIDE 10 — FINDINGS + Q&A
s = baseSlide();
header(s, "What the data taught me", "Four findings that outlive this project.");
const finds = [
  ["One source is never enough", "The interesting work was the three-source backfill, not the retrieval."],
  ["Frequent tags are stopwords", "83% \u2018fiction\u2019 carried zero information \u2014 dropping it created real clusters."],
  ["Mood \u2260 sentiment", "7 emotions separate melancholic from gritty; positive/negative cannot."],
  ["Keep user controls out of the model", "Pages, rating, year stay as filters \u2014 or the model silently overrides the user."],
];
finds.forEach((f, i) => {
  const x = 0.6 + (i % 2) * 6.25, y = 1.75 + Math.floor(i / 2) * 1.75;
  card(s, x, y, 6.0, 1.5, C.panel);
  s.addText(f[0], { x: x + 0.3, y: y + 0.15, w: 5.4, h: 0.45, fontSize: 15.5, bold: true,
    color: C.teal, fontFace: "Arial", margin: 0 });
  s.addText(f[1], { x: x + 0.3, y: y + 0.63, w: 5.4, h: 0.8, fontSize: 12,
    color: C.muted, fontFace: "Arial", margin: 0 });
});
s.addText([
  { text: "Thank you", options: { color: C.text, bold: true } },
  { text: "  \u2014  questions?", options: { color: C.purpleLt, bold: true } },
], { x: 0.6, y: 5.75, w: 12.1, h: 0.85, fontSize: 32, align: "center", fontFace: "Arial", margin: 0 });
s.addText("1,077 books  \u00B7  2 sources + 3 backfills  \u00B7  11 clusters  \u00B7  7 moods  \u00B7  1 app",
  { x: 0.6, y: 6.6, w: 12.1, h: 0.45, fontSize: 14, color: C.amber, align: "center",
    fontFace: "Arial", margin: 0 });
s.addNotes("~60 s, then Q&A. Close the loop: started with a reader who knew a feeling, not a title \u2014 ended with an app that answers exactly that. Total talk ~7.5 min + 2.5 min demo = 10 min, leaving Q&A after.");

pres.writeFile({ fileName: OUT }).then(() => console.log("WROTE:", OUT));
