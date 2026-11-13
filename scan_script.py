import requests
import re
import json

url = "https://www.tiktok.com/@zpen_cer/photo/7628998554282970388"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

resp = requests.get(url, headers=headers)
print("Status:", resp.status_code)
# Search for JSON objects in script tags
scripts = re.findall(r'<script[^>]*>(.*?)</script>', resp.text, re.DOTALL)
for s in scripts:
    if "7628998554282970388" in s:
        print("Found ID in script length:", len(s))
        with open("found_script.txt", "w", encoding="utf-8") as f:
            f.write(s)
        break
    if "webapp.video-detail" in s:
        print("Found video-detail in script")

print("Done scanning scripts")

