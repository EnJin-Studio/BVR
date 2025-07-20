import time
import requests
import random
import os
import pandas as pd
from datetime import datetime
from html import unescape
import re
import hashlib
import urllib.parse
import csv

# Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Referer": "https://search.bilibili.com",
    "Origin": "https://search.bilibili.com",
    "Accept": "application/json",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cookie": "SESSDATA=74eaeead%2C1768593444%2C6fdc3%2A71CjBk2jKBeb_oknADqnK-oRijK9jBIrxEOus424alZ7AQpSsvcVxInhn7SLeVtAi5QU4SVkxHVV9zendEeDJXOTBITHl4NE5vTEhfTHFpS19CT2VnVEhOMUEzTXRxQ1VDWmpZcDAxWlVVWTlVTlVTdC1rMS1OYnBjV2ZyMnl0N0libG0tRkdJTjRRIIEC; bili_jct=4510afc58694047a4156f944ce24fd91; DedeUserID=3546928264514104; sid=h9n9846p;"
    }

def clean_html(text):
    text = unescape(text)
    return re.sub(r'<[^>]+>', '', text)

def parse_duration_to_seconds(duration_str):
    parts = duration_str.split(":")
    try:
        if len(parts) == 3:
            h, m, s = map(int, parts)
            return h * 3600 + m * 60 + s
        elif len(parts) == 2:
            m, s = map(int, parts)
            return m * 60 + s
    except:
        pass
    return 0

def parse_search_items(data, start_ts, end_ts):
    items = []
    for v in data.get('data', {}).get('result', []):
        pub = v.get('senddate', 0)
        if pub < start_ts or pub >= end_ts: continue
        duration_sec = parse_duration_to_seconds(v.get("duration", "0:00"))
        if duration_sec > 3600:
            continue
        items.append({
            "uploader_name": v.get("author"),
            "uploader_mid": v.get("mid"),
            "uploader_pic": v.get('upic'),
            "type_id": v.get("typeid"),
            "type_name": v.get("typename"),
            "link": v.get("arcurl"),
            "bvid": v.get("bvid"),
            "title": clean_html(v.get("title","")),
            "description": v.get("description"),
            "pic": v.get("pic"),
            "view_count": v.get("play"),
            "danmaku_count": v.get("video_review"),
            "favorites_count": v.get("favorites"),
            "tag": v.get("tag"),
            "review_count": v.get("review"),
            "send_date": v.get('senddate'),
            "duration": duration_sec,
            "like_count" : v.get('like'),
            "pub_seconds_ago": int(time.time() - pub)
        })
    return items

def get_follower_count(mid):
    try:
        resp = requests.get("https://api.bilibili.com/x/relation/stat",
                             params={"vmid": mid}, headers=HEADERS, timeout=5)
        return resp.json().get("data",{}).get("follower")
    except:
        return None

def safe_request(url, params, headers, max_retries=3):
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=20)
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as e:
            print(f"[WARN] 第 {attempt+1} 次请求失败: {e}")
            time.sleep(3 + attempt * 2)
    print(f"[ERROR] 请求失败超过 {max_retries} 次，跳过")
    return None

def fetch_wbi_keys():
    url = "https://api.bilibili.com/x/web-interface/nav"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=5)
        resp.raise_for_status()
        data = resp.json().get("data", {}).get("wbi_img", {})
        img_url = data.get("img_url", "")
        sub_url = data.get("sub_url", "")

        img_key = img_url.split("/")[-1].split(".")[0]
        sub_key = sub_url.split("/")[-1].split(".")[0]

        print(f"[DEBUG] img_key: {img_key} ({len(img_key)})")
        print(f"[DEBUG] sub_key: {sub_key} ({len(sub_key)})")

        if len(img_key) != 32 or len(sub_key) != 32:
            raise ValueError("img_key 或 sub_key 长度不是 32，请检查 API 返回格式")

        return img_key, sub_key

    except Exception as e:
        print(f"[ERROR] 获取 WBI 签名 key 失败: {e}")
        return None, None

# 伪装wbi签名
def encode_wbi(params, img_key, sub_key):
    mixin_source = img_key + sub_key

    table = [46, 47, 18, 2, 8, 36, 12, 23, 25, 13,
             0, 29, 48, 39, 4, 32, 50, 19, 31, 43,
             26, 10, 9, 38, 27, 15, 3, 28, 14, 5,
             35, 11, 37, 1, 34, 41, 16, 49, 7, 42,
             22, 17, 30, 24, 21, 6, 33, 40, 20, 44]

    mixin_key = ''.join([mixin_source[i] for i in table])
    params['wts'] = str(int(time.time()))
    sorted_query = '&'.join(f"{k}={urllib.parse.quote_plus(str(params[k]))}" for k in sorted(params))
    params['w_rid'] = hashlib.md5((sorted_query + mixin_key).encode()).hexdigest()

    return params

    
def main(partition_tid, keywords, start_date, end_date, pages=50, delay=(2, 6)):
    os.makedirs("csv_data", exist_ok=True)
    history = "csv_data/video_wbi.csv"

    seen = set()
    if os.path.exists(history):
        seen = set(pd.read_csv(history)["bvid"].dropna().tolist())

    start_ts = int(datetime.strptime(start_date,"%Y-%m-%d").timestamp())
    end_ts = int(datetime.strptime(end_date,"%Y-%m-%d").timestamp())

    img_key, sub_key = fetch_wbi_keys()
    if not img_key or not sub_key:
        print("[ERROR] 无法获取 WBI 签名 key，终止爬取")
        return

    all_items=[]
    for kw in keywords:
        print(f"[KEYWORD] {kw}")
        for page in range(1, pages+1):
            params={"search_type":"video","keyword":kw,"page":page,"tids": partition_tid}
            full = encode_wbi(params, img_key, sub_key)
            resp = safe_request("https://api.bilibili.com/x/web-interface/wbi/search/type",
                    params=full, headers=HEADERS)
            if resp is None:
                print(f"[ERROR] 第{page}页请求失败，跳过")
                break
            data = resp.json()
            items=parse_search_items(data, start_ts, end_ts)
            added_count = 0
            for it in items:
                bvid = it["bvid"]
                if bvid and bvid not in seen:
                    # it["uploader_follower"]=get_follower_count(it["uploader_mid"])
                    # it.pop("uploader_mid",None)
                    all_items.append(it)
                    seen.add(bvid)
                    added_count += 1
            print(f" → 第{page}页实际新增{added_count}条，原始获取{len(items)}条")


            time.sleep(random.uniform(delay[0], delay[1]))

    df=pd.DataFrame(all_items)
    batch=f"csv_data/wbi_{partition_tid}.csv"
    df.to_csv(batch, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
    print(f"[SAVE] 批次保存: {batch}")

    if os.path.exists(history):
        df_hist=pd.read_csv(history)
        df_all=pd.concat([df,df_hist]).drop_duplicates("bvid")
    else:
        df_all=df
    df_all.to_csv(history, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
    print(f"[DONE] 合并完毕,共 {len(df_all)} 条")

if __name__ == "__main__":
    partition_ids = [65]  
    kw = ["的"]
    for pid in partition_ids:
        print(f"\n[START] 正在爬取分区 {pid} 的数据")
        main(pid, kw, "2010-01-01", "2025-07-02", pages=20, delay=(1, 9))
