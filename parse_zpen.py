import json

with open("zpen_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

scope = data.get("__DEFAULT_SCOPE__", {})
print("Scope keys:", list(scope.keys()))

def find_interesting(obj, depth=0):
    if depth > 7: return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if any(term in k.lower() for term in ["iteminfo", "itemstruct", "desc", "author", "title", "image", "photo", "caption", "text", "summary"]):
                val_str = str(v)
                if len(val_str) < 500 and not val_str.startswith("http") and not val_str.startswith("{") and not val_str.startswith("["):
                    print(f"{'  '*depth}{k}: {val_str}")
            find_interesting(v, depth+1)
    elif isinstance(obj, list):
        for item in obj[:3]:
            find_interesting(item, depth+1)

find_interesting(scope)

