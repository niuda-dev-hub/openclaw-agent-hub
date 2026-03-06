# -*- coding: utf-8 -*-
"""获取 4 个 Issues 的详细内容"""
import urllib.request, json

TOKEN = "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"
BASE = "https://api.github.com/repos/niudakok-kok/openclaw-agent-hub"
HEADERS = {"Authorization": "token " + TOKEN, "Accept": "application/vnd.github.v3+json", "User-Agent": "py"}

def get(path):
    req = urllib.request.Request(BASE + path, headers=HEADERS)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))

for n in [27, 28, 32, 34]:
    i = get("/issues/" + str(n))
    print(f"=== #{n}: {i['title']} ===")
    print(i["body"] or "(empty)")
    print()
