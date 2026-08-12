# -*- coding: utf-8 -*-
"""HTTP server + Bilibili search proxy with proper browser emulation"""
import http.server, urllib.request, urllib.parse, json, sys, io, os
import ssl

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BILI_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.bilibili.com/",
    "Origin": "https://www.bilibili.com",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Sec-Ch-Ua": '"Chromium";v="130", "Google Chrome";v="130"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Connection": "keep-alive",
}

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

        url = ("https://api.bilibili.com/x/web-interface/search/type?"
               "search_type=video&order=pubdate&duration=2&page=1&keyword="
               + urllib.parse.quote(keyword))

        try:
            # Use unverified SSL context to avoid cert issues
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(url, headers=BILI_HEADERS)
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                data = resp.read()

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "public, max-age=300")
            self.end_headers()
            self.wfile.write(data)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            print("  [BILI] HTTP {} for keyword='{}': {}".format(e.code, keyword, error_body[:100]))
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"code": -1, "message": "Bilibili API returned " + str(e.code), "error_body": error_body[:200]}).encode())
        except Exception as e:
            print("  [BILI] Error for keyword='{}': {}".format(keyword, e))
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"code": -1, "message": str(e)}).encode())

    def log_message(self, format, *args):
        if "bilibili" in str(args[0]):
            print("  [BILI] " + str(args[0]))

if __name__ == "__main__":
    port = 8765
    os.chdir("C:/Users/qiyanxi/Bitto/default/ai-hotboard")
    print("=" * 50)
    print("  AI Hotboard Server")
    print("  http://localhost:{}".format(port))
    print("=" * 50)
    http.server.HTTPServer(("", port), ProxyHandler).serve_forever()
