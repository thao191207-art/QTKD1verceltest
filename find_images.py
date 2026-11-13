import re

with open("found_script.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Find any image URLs (p16-sign, byteimg, etc.)
img_urls = re.findall(r'https:\u002F\u002F[^\"]+?\.(?:jpeg|jpg|png|webp)', text)
if not img_urls:
    img_urls = re.findall(r'https://[^\"]+?\.(?:jpeg|jpg|png|webp)', text)

print("Found image URLs:", len(img_urls))
for u in set(img_urls[:20]):
    print(u.replace(r"\u002F", "/"))

