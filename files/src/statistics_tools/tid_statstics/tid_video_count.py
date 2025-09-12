import requests, time, random, csv
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----------- 可自行调整的参数 -----------
CATE_IDS = [17, 19, 20, 21, 22, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 37, 39, 
            47, 51, 54, 59, 65, 71, 75, 76, 83, 85, 86, 95, 96, 121, 122, 124, 
            126, 127, 130, 131, 136, 137, 138, 145, 146, 147, 152, 153, 154, 156, 
            157, 158, 159, 161, 162, 163, 164, 166, 168, 169, 170, 171, 172, 173, 
            174, 175, 176, 178, 179, 180, 182, 183, 184, 185, 186, 187, 189, 190, 
            191, 193, 194, 195, 197, 198, 199, 200, 201, 203, 204, 205, 206, 207, 
            208, 209, 210, 212, 213, 214, 215, 216, 218, 219, 220, 221, 222, 224, 
            226, 227, 228, 229, 230, 231, 232, 233, 235, 236, 237, 238, 239, 240, 
            241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 
            255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267]   # 动画, 音乐, 电子竞技, …  ← 换成完整 tid 列表
NDAYS     = 7          # 想统计“近 N 天”，填 1=近一天，7=近一周
MAX_WORKERS = 5        # 并发数
PAUSE_MIN, PAUSE_MAX = 0.2, 0.6   # 请求间抖动（秒）
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com",
    "Origin": "https://www.bilibili.com",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    # ↓ Cookie 部分你需要自己在浏览器里复制
    "Cookie": "_uuid=810D1082B9-F1073-81106-59101-E759C98F3F6F91420infoc; buvid3=5DCD4719-61DA-AB7F-DAB1-8E4264DDC26A05662infoc; b_nut=1749940793; b_lsid=FCAB59E8_198D3820E49; CURRENT_FNVAL=4048; buvid_fp=451090834bd8ffbd4386870ab62d9198"
}
# ----------------------------------------

def build_dates(n):
    end   = datetime.today()
    start = end - timedelta(days=n)
    fmt   = "%Y%m%d"
    return start.strftime(fmt), end.strftime(fmt)

def fetch_count(cate_id, time_from, time_to):
    url = "https://api.bilibili.com/x/web-interface/newlist_rank"
    params = {
        "search_type": "video",
        "view_type": "hot_rank",
        "cate_id": cate_id,
        "time_from": time_from,
        "time_to": time_to,
        "pagesize": 30,
        "page": 3,
    }
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=5)
        r.raise_for_status()
        data = r.json().get("data", {})
        total = data.get("numResults", 0)      # 官方返回的总条数
        return total
    except Exception as e:
        print(f"[ERR] cate_id={cate_id}: {e}")
        return None

def main():
    tf, tt = build_dates(NDAYS)
    print(f"统计时间窗: {tf} ~ {tt}")

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        fut2cid = {pool.submit(fetch_count, cid, tf, tt): cid for cid in CATE_IDS}
        for fut in as_completed(fut2cid):
            cid = fut2cid[fut]
            cnt = fut.result()
            if cnt is not None:
                results.append((cid, cnt))
            time.sleep(random.uniform(PAUSE_MIN, PAUSE_MAX))  # 抖动

    # 按条数排序方便看
    results.sort(key=lambda x: x[1], reverse=True)

    # 打印汇总
    total_all = sum(c for _, c in results)
    for cid, c in results:
        print(f"cate_id {cid:>4}: {c:>6} 条（占 {c/total_all:.2%}）")

    # 写 CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_csv = f"category_counts_{timestamp}.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["cate_id", "count", "time_from", "time_to"])
        for cid, c in results:
            writer.writerow([cid, c, tf, tt])
    print(f"结果已保存到 {out_csv}")

if __name__ == "__main__":
    main()
