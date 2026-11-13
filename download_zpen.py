import requests
import json
import os

os.makedirs("zpen_screens", exist_ok=True)

with open("zpen_screens/metadata.json", "w", encoding="utf-8") as f:
    pass

url = "https://www.tikwm.com/api/?url=https://www.tiktok.com/@zpen_cer/photo/7628998554282970388"
r = requests.get(url, timeout=10)
data = r.json().get("data", {})
images = data.get("images", [])

for i, img_url in enumerate(images):
    img_resp = requests.get(img_url, timeout=15)
    img_path = f"zpen_screens/screen_{i+1}.jpg"
    with open(img_path, "wb") as f:
        f.write(img_resp.content)
    print(f"Downloaded screen_{i+1}.jpg, size: {len(img_resp.content)} bytes")

print("Done downloading all screenshots!")

