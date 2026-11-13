with open("found_script.txt", "r", encoding="utf-8") as f:
    text = f.read()

pos = text.find("7628998554282970388")
while pos != -1:
    print("MATCH AT POS:", pos)
    start = max(0, pos - 500)
    end = min(len(text), pos + 1000)
    print(text[start:end])
    print("=" * 60)
    pos = text.find("7628998554282970388", pos + 1)

