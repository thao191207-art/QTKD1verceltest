import requests
import re
import json

r = requests.get('https://www.tiktok.com/embed/v2/7628998554282970388', headers={'User-Agent': 'Mozilla/5.0'})
html = r.text

print("Length of embed:", len(html))

# Search for SIGI_STATE or __DEFAULT_SCOPE__ or video data
m = re.search(r'<script id="__FRONTITY_CONNECT_STATE__"[^>]*>(.*?)</script>', html, re.DOTALL)
if m:
    print("Found FRONTITY")

scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
for s in scripts:
    if "7628998554282970388" in s or "zpen_cer" in s or "desc" in s:
        # search for author, title, desc
        titles = re.findall(r'"title":"([^"]+)"', s)
        descs = re.findall(r'"desc":"([^"]+)"', s)
        authors = re.findall(r'"uniqueId":"([^"]+)"', s)
        nicknames = re.findall(r'"nickname":"([^"]+)"', s)
        print("Titles:", titles[:5])
        print("Descs:", descs[:5])
        print("Authors:", authors[:5])
        print("Nicknames:", nicknames[:5])
        if descs or titles or authors:
            with open("embed_data.txt", "w", encoding="utf-8") as f:
                f.write(s)
            break

