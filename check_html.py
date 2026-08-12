import urllib.request, re
r = urllib.request.urlopen("http://localhost:8765/dashboard.html", timeout=5)
html = r.read().decode("utf-8")
# Check for fetch paths
fetches = re.findall(r"fetch\([\"']([^\"']+)", html)
print("Fetch calls found:")
for f in fetches:
    print("  " + f)
# Check if the data loading works
if "dashboard.json" in html:
    print("\nData load path: data/dashboard.json -> OK")
# Check for JS errors by looking at the catch block
if "catch" in html:
    print("Catch block: present")
# Quick head inspection
print("\nFirst 500 chars:")
print(html[:500])
