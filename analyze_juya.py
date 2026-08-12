import sys, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import urllib.request, feedparser

url = "https://daily.juya.uk/rss.xml"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
raw = urllib.request.urlopen(req, timeout=15).read()
f = feedparser.parse(raw)

# Analyze the most recent issue content to find original sources
latest = f.entries[0]
content = latest.get("summary", "") + latest.get("content", [{}])[0].get("value", "")

print("=" * 55)
print("  最新一期: {}".format(latest.get("title", "")))
print("=" * 55)

# Find all links
links = re.findall(r'href="(https?://[^"]+)"', content)
print("\nAll linked sources in this issue:")
seen = set()
for l in links:
    if l not in seen:
        seen.add(l)
        # Truncate long URLs
        short = l[:100] + "..." if len(l) > 100 else l
        print("  {}".format(short))

# Also extract source domain
print("\nDomains:")
domains = {}
for l in links:
    m = re.match(r"https?://([^/]+)", l)
    if m:
        d = m.group(1).replace("www.", "")
        domains[d] = domains.get(d, 0) + 1
for d, c in sorted(domains.items(), key=lambda x: -x[1]):
    print("  {}: {}".format(d, c))

# Show the first 1000 chars of content
print("\n--- Content snippet (first 1500 chars) ---")
clean = re.sub(r"<[^>]+>", " ", content)
clean = re.sub(r"\s+", " ", clean)
print(clean[:1500])
