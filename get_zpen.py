import requests
import re
import json

url = "https://www.tiktok.com/@zpen_cer/photo/7628998554282970388"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
m = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
if m:
    with open("zpen_data.json", "w", encoding="utf-8") as f:
        f.write(m.group(1))
    print("Saved zpen_data.json, size:", len(m.group(1)))
else:
    print("No rehydration script")

