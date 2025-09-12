# -*- coding: utf-8 -*-
import os, json, re, csv, time, random, hashlib, pickle
from urllib.parse import urlencode
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

# ==================== 可配置参数 ====================
CATE_IDS = [17, 19, 20, 21, 22, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 37, 39,
            47, 51, 54, 59, 65, 71, 75, 76, 83, 85, 86, 95, 96, 121, 122, 124,
            126, 127, 130, 131, 136, 137, 138, 145, 146, 147, 152, 153, 154, 156,
            157, 158, 159, 161, 162, 163, 164, 166, 168, 169, 170, 171, 172, 173,
            174, 175, 176, 178, 179, 180, 182, 183, 184, 185, 186, 187, 189, 190,
            191, 193, 194, 195, 197, 198, 199, 200, 201, 203, 204, 205, 206, 207,
            208, 209, 210, 212, 213, 214, 215, 216, 218, 219, 220, 221, 222, 224,
            226, 227, 228, 229, 230, 231, 232, 233, 235, 236, 237, 238, 239, 240,
            241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254,
            255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267]

NDAYS             = 7
MAX_WORKERS       = 3                   # 建议保守
TIMEOUT_S         = 8
RETRIES_PER_REQ   = 4
REQ_PAUSE_RANGE   = (0.35, 0.9)         # 单请求扰动
GROUP_SIZE        = 20                  # 分批数量（每批处理多少个分区）
GROUP_GAP_RANGE   = (15.0, 35.0)        # 批间冷却（秒）
COOLDOWN_LONG_S   = (600, 1200)         # 熔断冷却（10-20 分钟）
FUSE_ERR_RATIO    = 0.3                 # 单批 412/429/403 比例超过即触发熔断
STATE_FILE        = ".bili_state.json"  # 记录上次运行时间
COOKIE_JAR_FILE   = ".bili_cookies.pkl" # 持久化 cookies
USE_FALLBACK      = True                # 大面积 412 时启用备用接口 dynamic/region
FALLBACK_PAGES    = 3                   # 降级时为每分区抓最近 Pn=1..N 页估计量

# 访客态 Cookie（不要放 SESSDATA/bili_ticket/sid）
COOKIE_MINIMAL = (
    "_uuid=810D1082B9-F1073-81106-59101-E759C98F3F6F91420infoc; buvid3=5DCD4719-61DA-AB7F-DAB1-8E4264DDC26A05662infoc; b_nut=1749940793; b_lsid=FCAB59E8_198D3820E49; CURRENT_FNVAL=4048; buvid_fp=451090834bd8ffbd4386870ab62d9198"

)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/137.0.0.0 Safari/537.36")
# ====================================================


def china_dates(n_days: int):
    cn_now = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(hours=8)
    end_date = cn_now.date()
    start_date = end_date - timedelta(days=n_days)
    fmt = "%Y%m%d"
    return start_date.strftime(fmt), end_date.strftime(fmt)


def polite_sleep(a, b):
    time.sleep(random.uniform(a, b))


def save_state(obj: dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(obj, f)
    except Exception:
        pass


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "Referer": "https://www.bilibili.com",
        "Origin": "https://www.bilibili.com",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cookie": COOKIE_MINIMAL,
    })
    # 尝试加载历史 cookies，维持会话连续性
    if os.path.exists(COOKIE_JAR_FILE):
        try:
            with open(COOKIE_JAR_FILE, "rb") as f:
                s.cookies.update(pickle.load(f))
        except Exception:
            pass
    return s


def persist_cookies(session: requests.Session):
    try:
        with open(COOKIE_JAR_FILE, "wb") as f:
            pickle.dump(session.cookies, f)
    except Exception:
        pass


# -------------- WBI 签名 --------------
_WBI_MIXIN_INDEX = [46,47,18,2,53,8,23,32,15,50,10,31,58,3,45,35,27,43,5,49,33,9,42,19,29,28,14,39,12,38,41,13,37,48,7,16,24,55,40,61,26,17,0,1,60,51,30,4,22,25,54,21,56,59,6,57,11,20,34,36,44,52]
_WBI_FILTER_CHARS = set("!()*'")

def _mixin_key(img_key: str, sub_key: str) -> str:
    raw = img_key + sub_key
    return "".join(raw[i] for i in _WBI_MIXIN_INDEX[:32])

def _filter_value(s: str) -> str:
    return "".join(ch for ch in s if ch not in _WBI_FILTER_CHARS)

def get_wbi_keys(session: requests.Session):
    r = session.get("https://api.bilibili.com/x/web-interface/nav", timeout=TIMEOUT_S)
    r.raise_for_status()
    j = r.json()
    wi = (j.get("data", {}) or {}).get("wbi_img", {}) or {}
    img_url = wi.get("img_url", "")
    sub_url = wi.get("sub_url", "")
    if not img_url or not sub_url:
        wi2 = (j.get("data", {}) or {}).get("wbi_sub", {}) or {}
        img_url = img_url or wi2.get("img_url", "")
        sub_url = sub_url or wi2.get("sub_url", "")
    img_key = re.split(r"[/.]", img_url)[-2] if img_url else ""
    sub_key = re.split(r"[/.]", sub_url)[-2] if sub_url else ""
    if not img_key or not sub_key:
        raise RuntimeError("无法从 /nav 提取 WBI keys（检查 Cookie/网络/频率）")
    return img_key, sub_key

def wbi_sign(params: dict, img_key: str, sub_key: str) -> dict:
    p = {k: str(v) for k, v in params.items()}
    p["wts"] = str(int(time.time()))
    for k in list(p.keys()):
        p[k] = _filter_value(p[k])
    p_sorted = dict(sorted(p.items()))
    query = urlencode(p_sorted)
    mixin = _mixin_key(img_key, sub_key)
    w_rid = hashlib.md5((query + mixin).encode("utf-8")).hexdigest()
    p_sorted["w_rid"] = w_rid
    return p_sorted
# -------------------------------------


def fetch_count_newlist(session, keys, cate_id, tf, tt):
    """主接口：newlist_rank → 返回 numResults"""
    url = "https://api.bilibili.com/x/web-interface/newlist_rank"
    base = {
        "search_type": "video",
        "view_type": "hot_rank",
        "cate_id": cate_id,
        "time_from": tf,
        "time_to": tt,
        "pagesize": 30,
        "page": 1,
    }
    for attempt in range(1, RETRIES_PER_REQ + 1):
        try:
            signed = wbi_sign(base, *keys)
            r = session.get(url, params=signed, timeout=TIMEOUT_S)
            if r.status_code in (412, 429, 403):
                backoff = (2 ** (attempt - 1)) * random.uniform(1.8, 2.8)
                print(f"[{r.status_code}] cate_id={cate_id} attempt {attempt}/{RETRIES_PER_REQ}, sleep {backoff:.1f}s")
                time.sleep(backoff)
                continue
            r.raise_for_status()
            data = r.json().get("data", {})
            total = data.get("numResults", None)
            if total is None:
                polite_sleep(0.6, 1.2)
                continue
            return int(total), None
        except requests.RequestException as e:
            backoff = (2 ** (attempt - 1)) * random.uniform(1.8, 2.8)
            print(f"[ERR] cate_id={cate_id} attempt {attempt}/{RETRIES_PER_REQ}: {e}; sleep {backoff:.1f}s")
            time.sleep(backoff)
        except Exception as e:
            print(f"[PARSE] cate_id={cate_id}: {e}")
            polite_sleep(0.6, 1.2)
    return None, "blocked"


def fetch_count_fallback(session, cate_id, pages=3):
    """
    备用接口：分区最新投稿列表，估计“近几页数量”作为近似强度
    GET /x/web-interface/dynamic/region?rid=<tid>&pn=<1..N>&ps=30
    返回每页条数（一般 30），累加 pages 页作为 proxy（仅用于兜底）
    """
    total = 0
    for pn in range(1, pages + 1):
        url = "https://api.bilibili.com/x/web-interface/dynamic/region"
        params = {"rid": cate_id, "pn": pn, "ps": 30}
        try:
            r = session.get(url, params=params, timeout=TIMEOUT_S)
            if r.status_code in (412, 429, 403):
                polite_sleep(2.0, 4.0)
                continue
            r.raise_for_status()
            j = r.json()
            arr = (j.get("data", {}) or {}).get("archives", []) or []
            total += len(arr)
            polite_sleep(0.3, 0.7)
        except Exception as e:
            print(f"[FB-ERR] cate_id={cate_id} pn={pn}: {e}")
    return total


def run_group(session, keys, cate_ids):
    results = []
    blocked_count = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        fut2cid = {
            pool.submit(fetch_count_newlist, session, keys, cid, TF, TT): cid
            for cid in cate_ids
        }
        for fut in as_completed(fut2cid):
            cid = fut2cid[fut]
            cnt, flag = fut.result()
            if flag == "blocked":
                blocked_count += 1
            if cnt is not None:
                results.append((cid, cnt))
            polite_sleep(*REQ_PAUSE_RANGE)
    return results, blocked_count, len(cate_ids)


def main():
    # ---- 时间窗（建议用北京时间自然日）----
    global TF, TT
    TF, TT = china_dates(NDAYS)
    print(f"统计时间窗: {TF} ~ {TT}")

    # ---- 会话&WBI key ----
    session = make_session()
    img_key, sub_key = get_wbi_keys(session)
    keys = (img_key, sub_key)

    # ---- 载入上次运行时间，防止“立刻第二轮” ----
    state = load_state()
    last_end_ts = state.get("last_end_ts", 0)
    now_ts = time.time()
    if now_ts - last_end_ts < 180:  # 上次结束不足 3 分钟，先主动抖一下
        wait_s = random.uniform(60, 180)
        print(f"[WARMUP] 与上次运行间隔过短，先冷却 {wait_s:.0f}s")
        time.sleep(wait_s)

    # ---- 打散顺序，分批渐进抓取 ----
    cate_list = CATE_IDS[:]
    random.shuffle(cate_list)
    results = []
    total_blocked = 0
    total_sent = 0

    for i in range(0, len(cate_list), GROUP_SIZE):
        batch = cate_list[i:i+GROUP_SIZE]
        print(f"\n== 批次 {i//GROUP_SIZE + 1} / { (len(cate_list)-1)//GROUP_SIZE + 1 }，分区数={len(batch)} ==")
        group_res, blocked, sent = run_group(session, keys, batch)
        results.extend(group_res)
        total_blocked += blocked
        total_sent += sent

        # 批间熔断检测
        if sent > 0 and (blocked / sent) >= FUSE_ERR_RATIO:
            # 触发熔断：长时间冷却，必要时启用 fallback
            cool = random.uniform(*COOLDOWN_LONG_S)
            print(f"[FUSE] 本批阻断率 {blocked}/{sent} >= {FUSE_ERR_RATIO:.0%}，长冷却 {int(cool)}s")
            time.sleep(cool)
            # 再次刷新 WBI key（有时 key 变更）
            img_key, sub_key = get_wbi_keys(session)
            keys = (img_key, sub_key)

        else:
            # 正常批间冷却
            polite_sleep(*GROUP_GAP_RANGE)

    # ---- 如果阻断占比太高，降级尝试（可选）----
    if USE_FALLBACK and total_sent > 0 and (total_blocked / total_sent) >= 0.5:
        print("\n[DOWNGRADE] 阻断占比过高，启用备用接口 dynamic/region 估计分区强度")
        # 为没有结果的分区补值
        have = set(cid for cid, _ in results)
        missing = [cid for cid in CATE_IDS if cid not in have]
        for cid in missing:
            val = fetch_count_fallback(session, cid, pages=FALLBACK_PAGES)
            results.append((cid, val))
            polite_sleep(0.3, 0.7)

    # ---- 汇总输出 ----
    # 若有重复（不应有），聚合一下
    agg = {}
    for cid, cnt in results:
        agg[cid] = agg.get(cid, 0) + (cnt or 0)

    ordered = sorted(agg.items(), key=lambda x: x[1], reverse=True)
    total_all = sum(c for _, c in ordered) or 1

    for cid, c in ordered:
        print(f"cate_id {cid:>4}: {c:>6} 条（占 {c/total_all:.2%}）")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_csv = f"category_counts_{ts}.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cate_id", "count", "time_from", "time_to"])
        for cid, c in ordered:
            w.writerow([cid, c, TF, TT])
    print(f"\n结果已保存到 {out_csv}")

    # ---- 持久化 cookies & 状态 ----
    persist_cookies(session)
    save_state({"last_end_ts": time.time()})


if __name__ == "__main__":
    main()
