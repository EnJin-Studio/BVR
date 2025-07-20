# 🔍 Bilibili Video View Count Predictor
111
A multimodal machine learning pipeline to predict Bilibili homepage video view counts. Designed to support content ranking, scoring, and performance forecasting.

---

## 🎯 Project Goals

- 📥 Crawl Bilibili homepage video metadata and thumbnails  
- 📈 Train and evaluate a regression model
- 📊 Provide predictions, content insights, and ranking capabilities  

---

## 📁 Project Structure

```
python_files/
├── csv_data/                       # CSV data files (e.g., video_wbi.csv)
│   └── ...
├── web_crawler_search_wbi.py      # crawler for tag-based search(video & uploader info)
.gitignore
README.md
```

---

## 📌 Input Feature Vector

---

## 🎯 Prediction Target

- `view_count`

---

## 🔧 Installation

Key dependencies:
- `numpy`, `pandas`
- `requests`

---

## 🚀 Usage

### 1. Crawl Bilibili videos

```bash
python python_files/web_crawler_search_wbi.py
```

---

## 🧠 Potential Applications

- Predict the popularity of a new video before upload  
- Assist Bilibili creators in thumbnail/title optimization  
- Rank candidate videos in a homepage recommender  
- Visualize latent features of popular content  

---

## 🧪 Future Work

- Build a Website for easier use  

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
