# 🔍 Bilibili Video View & Quality Predictor
A multimodal ML pipeline that predicts Bilibili homepage video views **and** benchmarks each video against ideal style profiles. Built for ranking, scoring, edit guidance, and performance forecasting.

---

## 👥 Who It’s For
- **Individual creators** — clear, quantitative feedback on style-profile fit and where to focus the next edits.
- **Marketing & analytics teams** — objective, high-throughput evaluation of large libraries and engagement prediction.
- **Platform curators & researchers** — detailed reports to inform recommendations, optimize algorithms, and study content trends.

---

## 🎯 Project Goals
- 📥 Crawl Bilibili homepage video metadata and thumbnails  
- 📈 Train and evaluate regression models for view prediction  
- 🧭 Generate per-video diagnostics: style-fit scores and actionable edit suggestions  
- 📊 Provide predictions, content insights, and batch ranking capabilities

---

## 📁 Project Structure

```
.
├── files/
│   ├── csv_data_big_division/ 
│   │   ├── video_wbi.csv
│   │   └── wbi_*.csv
│   ├── csv_data_game_division/ 
│   │   ├── video_game_division.csv
│   │   └── wbi_*.csv
│   └── test_data/  
│       ├── summary_metrics.csv
│       ├── test.csv
│       └── video_level_results.csv
├── asw_test.py
├── web_crawler_search_wbi.py
├── .gitignore
└── README.md
```

---

## 🧩 Input Feature Vector

**Metadata**
- Title, duration, publish date, video ID, etc.
- Cover image
- Uploader name, follower count,

**Tags**
- Original tags from uploader  
- Model-generated tags (topic/style)  
- Tag alignment metrics

**Style & Dimensions**
- User-desired style profile
- Dimension weights (Teaching Clarity, Aesthetics, Emotional Impact, Humor, Trend References)  
- Model-detected proportions for each dimension

---

## 🎯 Prediction Targets

- `view_count`
- Optional engagement: `likes`, `favorites`, `shares` 
- `home_page_recommendation_prob`
- Per-dimension scores (0–10) and final weighted composite score (0–10)  
- Tag-match status (`matched` / `partial` / `mismatched`) + brief rationale

---

## 🔧 Installation

Key dependencies:
- `numpy`, `pandas`, `requests`
- `scikit-learn`
- `sentence-transformers`, `torch` 

---

## 🚀 Usage

### 1) Crawl Bilibili videos
    python web_crawler_search_wbi.py
Outputs CSVs under `files/csv_data_*`.

### 2) Run analysis & scoring
    python asw_test.py
Reads CSVs from `files/csv_data_*` and writes to `files/test_data/`

---

## 🧠 Potential Applications

- Pre-upload performance prediction & edit guidance for creators  
- High-throughput batch evaluation for marketing/analytics teams  
- Curator/research tooling: trend diagnostics, ranking, and reports

---

## 🧪 Future Work

- Web UI for interactive style profiles & what-if edits  
- Add key-frame visual analysis
- Expand trend/keyword detectors and topic taxonomies

---

## 👥 Authors

**Ziyuan Chu (Eric)**  
Boston University · Computer Engineering  
📧 [czyuan@bu.edu](mailto:czyuan@bu.edu)

**Feng Tai (Jimmy)**  
Boston University · Computer Engineering  
📧 [jimmytai@bu.edu](mailto:jimmytai@bu.edu)

**Weizhou Zhang**  
The University of Hong Kong · Computer Engineering  
📧 [u3609832@connect.hku.hk](mailto:u3609832@connect.hku.hk)

---

## 📄 License

MIT License. Free to use with attribution.
