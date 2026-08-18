# -*- coding: utf-8 -*-
"""HTTP server + Bilibili search proxy using curl_cffi + wbi signature"""
import http.server, urllib.parse, json, sys, io, os, threading, time, hashlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from curl_cffi import requests

# Global session for Bilibili (reuse cookies)
_bili_session = None
_bili_lock = threading.Lock()
_mixin_key = None
_mixin_lock = threading.Lock()

MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40, 61,
    26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36,
    20, 34, 44, 52
]

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def get_bili_session():
    global _bili_session
    if _bili_session is None:
        _bili_session = requests.Session(impersonate="chrome")
        _bili_session.headers.update({"User-Agent": UA})
        try:
            _bili_session.get("https://www.bilibili.com/", timeout=10)
        except Exception:
            pass
    return _bili_session

def get_mixin_key():
    """Fetch wbi keys from nav API and compute mixin key (cached)."""
    global _mixin_key
    with _mixin_lock:
        if _mixin_key is not None:
            return _mixin_key
        session = get_bili_session()
        try:
            nav = session.get("https://api.bilibili.com/x/web-interface/nav", timeout=10).json()
            img_key = nav["data"]["wbi_img"]["img_url"].rsplit("/", 1)[1].split(".")[0]
            sub_key = nav["data"]["wbi_img"]["sub_url"].rsplit("/", 1)[1].split(".")[0]
            raw = img_key + sub_key
            _mixin_key = "".join(raw[i] for i in MIXIN_KEY_ENC_TAB)[:32]
        except Exception:
            _mixin_key = ""
        return _mixin_key

def enc_wbi(params):
    """Add wts + w_rid signature to params (returns fresh copy)."""
    mixin_key = get_mixin_key()
    p = dict(params)
    p["wts"] = int(time.time())
    p = dict(sorted(p.items()))
    query = urllib.parse.urlencode(p)
    filtered = "".join(ch for ch in query if ch not in "!'()*")
    w_rid = hashlib.md5((filtered + mixin_key).encode()).hexdigest()
    return w_rid, p["wts"]

def bili_search(keyword):
    """Search Bilibili videos via wbi-signed API with real search-page referer."""
    session = get_bili_session()
    url = "https://api.bilibili.com/x/web-interface/wbi/search/type"

    base = {
        "search_type": "video",
        "order": "pubdate",
        "page": "1",
        "keyword": keyword,
    }
    w_rid, wts = enc_wbi(base)
    base["w_rid"] = w_rid
    base["wts"] = wts

    # 动态设置 Referer 为真实搜索页，避免 412 / voucher 风控
    session.headers["Referer"] = "https://search.bilibili.com/all?keyword=" + urllib.parse.quote(keyword)

    resp = session.get(url, params=base, timeout=15)
    if resp.status_code != 200:
        return {"code": -1, "message": "HTTP " + str(resp.status_code)}

    data = resp.json()

    # 偶发两步 voucher 流程：第一次响应只带 v_voucher
    tries = 0
    while (data.get("code") == 0 and "v_voucher" in data.get("data", {})
           and not data.get("data", {}).get("result") and tries < 2):
        tries += 1
        voucher = data["data"]["v_voucher"]
        base2 = dict(base)
        base2["v_voucher"] = voucher
        w_rid2, wts2 = enc_wbi(base2)
        base2["w_rid"] = w_rid2
        base2["wts"] = wts2
        resp2 = session.get(url, params=base2, timeout=15)
        if resp2.status_code != 200:
            return {"code": -1, "message": "HTTP " + str(resp2.status_code)}
        data = resp2.json()

    return data

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/bilibili-search"):
            self.proxy_bilibili()
        else:
            super().do_GET()

    def proxy_bilibili(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        keyword = params.get("keyword", [""])[0]

        try:
            with _bili_lock:
                data = bili_search(keyword)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "public, max-age=300")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        except Exception as e:
            print("  [BILI] Error for '{}': {}".format(keyword, e))
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"code": -1, "message": str(e)}).encode("utf-8"))

    def log_message(self, format, *args):
        if "bilibili" in str(args[0]):
            print("  [BILI] " + str(args[0]))

if __name__ == "__main__":
    port = 8765
    os.chdir("C:/Users/qiyanxi/Bitto/default/ai-hotboard")
    print("=" * 50)
    print("  AI Hotboard Server (wbi-signed Bilibili proxy)")
    print("  http://localhost:{}".format(port))
    print("=" * 50)
    http.server.HTTPServer(("", port), ProxyHandler).serve_forever()
