import time
import csv
import requests
import random
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com"
}

# 从首页获取 bvid 列表
def fetch_recommend_page(ps=30, fresh_idx=1):
    url = "https://api.bilibili.com/x/web-interface/index/top/feed/rcmd"
    params = {"ps": ps, "fresh_idx": fresh_idx, "fresh_type": 4}
    resp = requests.get(url, params=params, headers=HEADERS, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    bvids = [v.get("bvid") for v in data.get("data", {}).get("item", []) if v.get("bvid")]
    return bvids

# 根据 bvid 获取详细数据
def fetch_video_detail(bvid):
    url = "https://api.bilibili.com/x/web-interface/view"
    params = {"bvid": bvid}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=5)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        stat = data.get("stat", {})
        owner = data.get("owner", {})
        
        return {
            "bvid": bvid,
            "aid": data.get("aid"),
            "videos": data.get("videos"),
            "tid": data.get("tid"),
            "tid_v2": data.get("tid_v2"),
            "tname": data.get("tname"),
            "tname_v2": data.get("tname_v2"),
            "pic": data.get("pic"),
            "title": data.get("title"),
            "pubdate": data.get("pubdate"),
            "duration": data.get("duration"),
            "mid": owner.get("mid"),
            "name": owner.get("name"),
            "face": owner.get("face"),
            "view": stat.get("view"),
            "danmaku": stat.get("danmaku"),
            "reply": stat.get("reply"),
            "favorite": stat.get("favorite"),
            "coin": stat.get("coin"),
            "share": stat.get("share"),
            "now_rank": stat.get("now_rank"),
            "his_rank": stat.get("his_rank"),
            "like": stat.get("like"),
        }
    except Exception as e:
        print(f"[ERROR] 获取 {bvid} 失败: {e}")
        return None

def fetch_all_details(bvid_list, max_workers=5):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_video_detail, bvid): bvid for bvid in bvid_list}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Fetching details"):
            res = future.result()
            if res:
                results.append(res)
    return results

fieldnames = [
    "bvid", "aid", "videos", "tid", "tid_v2", "tname", "tname_v2",
    "pic", "title", "pubdate", "duration", "mid", "name", "face",
    "view", "danmaku", "reply", "favorite", "coin", "share", "now_rank", "his_rank", "like"
]


# 主逻辑
def main(pages=5, ps=30, delay=1, max_workers=5):
    # Step 1: 获取所有 bvid
    all_bvids = set()
    for idx in range(1, pages + 1):
        print(f"[INFO] 正在抓取首页第 {idx} 页 bvid")
        try:
            bvids = fetch_recommend_page(ps=ps, fresh_idx=idx)
            all_bvids.update(bvids)
        except Exception as e:
            print(f"[ERROR] 首页第 {idx} 页失败: {e}")
        time.sleep(random.uniform(delay, 2))
    print(f"[INFO] 共获取到 {len(all_bvids)} 个唯一 bvid")

    # Step 2: 并发获取详细数据（带进度条）
    results = fetch_all_details(all_bvids, max_workers=max_workers)

    # Step 3: 保存 CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("main_page_data", exist_ok=True)
    batch_filename = os.path.join("main_page_data", f"data_batch_{timestamp}.csv")
    with open(batch_filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"[DONE] 已保存到 {batch_filename}")


if __name__ == "__main__":
    # max_workers=5 比较安全，不容易被封，速度也可以
    main(pages=60, ps=30, delay=1, max_workers=5)
