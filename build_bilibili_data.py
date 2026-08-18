# -*- coding: utf-8 -*-
"""Build static Bilibili recommendations for the GitHub Pages dashboard."""
import html
import json
import re
import sys
import io
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

try:
    from curl_cffi import requests
except ImportError:
    print("请先安装 curl_cffi: python -m pip install curl_cffi", file=sys.stderr)
    raise

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DASHBOARD_PATH = DATA_DIR / "dashboard.json"
OUTPUT_PATH = DATA_DIR / "bilibili.json"


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    return re.sub(r"<[^>]+>", "", value).strip()


def normalize_cover(value: str) -> str:
    if not value:
        return ""
    if value.startswith("//"):
        return "https:" + value
    if value.startswith("http:"):
        return value.replace("http:", "https:", 1)
    return value


def search_videos(session, keyword: str, cutoff_ms: int) -> list[dict]:
    endpoint = "https://api.bilibili.com/x/web-interface/search/type"
    collected = {}
    for page in range(1, 4):
        params = {
            "search_type": "video",
            "order": "pubdate",
            "duration": "2",
            "page": page,
            "keyword": keyword,
        }
        response = session.get(endpoint, params=params, timeout=20)
        if response.status_code == 412:
            print(f"  [WARN] B站 HTTP 412, rebuilding session: {keyword}")
            session.get("https://www.bilibili.com/", timeout=20)
            time.sleep(1.5)
            response = session.get(endpoint, params=params, timeout=20)
        if response.status_code != 200:
            print(f"  [WARN] B站 HTTP {response.status_code}: {keyword}")
            break
        payload = response.json()
        if payload.get("code") != 0:
            print(f"  [WARN] B站 code={payload.get('code')}: {keyword}")
            break
        for raw in (payload.get("data") or {}).get("result") or []:
            pubdate_ms = int(raw.get("pubdate", 0)) * 1000
            if pubdate_ms < cutoff_ms:
                continue
            bvid = raw.get("bvid")
            if not bvid:
                continue
            collected[bvid] = {
                "bvid": bvid,
                "title": clean_text(raw.get("title", "")),
                "author": clean_text(raw.get("author", "")),
                "pic": normalize_cover(raw.get("pic", "")),
                "play": int(raw.get("play", 0) or 0),
                "pubdate": int(raw.get("pubdate", 0) or 0),
                "url": f"https://www.bilibili.com/video/{bvid}",
            }
        time.sleep(0.4)
    return sorted(collected.values(), key=lambda item: item["play"], reverse=True)[:10]


def main() -> None:
    dashboard = json.loads(DASHBOARD_PATH.read_text(encoding="utf-8"))
    cutoff_ms = int((datetime.now(timezone.utc) - timedelta(hours=48)).timestamp() * 1000)
    session = requests.Session(impersonate="chrome")
    # Warm up the session; B站搜索接口对首次请求更敏感。
    session.get("https://www.bilibili.com/", timeout=20)

    topics = {}
    for topic in dashboard.get("hot_topics", []):
        query = topic.get("search_query") or topic.get("event", "")[:30]
        try:
            videos = search_videos(session, query, cutoff_ms)
            topics[str(topic["rank"])] = {
                "query": query,
                "videos": videos,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            print(f"  [OK] #{topic['rank']} {query}: {len(videos)} videos")
        except Exception as exc:
            topics[str(topic["rank"])] = {
                "query": query,
                "videos": [],
                "error": str(exc),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            print(f"  [FAIL] #{topic['rank']} {query}: {exc}")

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_hours": 48,
        "topics": topics,
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
