import requests
import json

url = "https://www.tikwm.com/api/?url=https://www.tiktok.com/@zpen_cer/photo/7628998554282970388"
r = requests.get(url, timeout=10)
print("Status:", r.status_code)
try:
    data = r.json()
    print("Code:", data.get("code"), "Msg:", data.get("msg"))
    res_data = data.get("data", {})
    print("Title / Desc:", res_data.get("title"))
    print("Author:", res_data.get("author", {}).get("nickname"), res_data.get("author", {}).get("unique_id"))
    images = res_data.get("images", [])
    print("Images:", len(images))
    for i, img in enumerate(images):
        print(f"Img {i}: {img}")
except Exception as e:
    print("Error:", e)

