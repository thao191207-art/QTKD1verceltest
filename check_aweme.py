import requests
import json

url = 'https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/?aweme_id=7628998554282970388'
headers = {'User-Agent': 'okhttp/3.14.9'}
r = requests.get(url, headers=headers)
print("Status:", r.status_code, "Len:", len(r.text))
try:
    data = r.json()
    print("Keys in response:", list(data.keys()))
    aweme_list = data.get("aweme_list", [])
    print("Aweme count:", len(aweme_list))
    if aweme_list:
        aweme = aweme_list[0]
        print("Author:", aweme.get("author", {}).get("nickname"), "@" + aweme.get("author", {}).get("unique_id", ""))
        print("Desc:", aweme.get("desc"))
        images = aweme.get("image_post_info", {}).get("images", [])
        print("Images count:", len(images))
        for idx, img in enumerate(images):
            url_list = img.get("display_image", {}).get("url_list", [])
            print(f"Img {idx}:", url_list[0] if url_list else "None")
except Exception as e:
    print("Error parsing JSON:", e)

