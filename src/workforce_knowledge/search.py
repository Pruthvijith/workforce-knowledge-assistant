"""Small-corpus BM25 retrieval with access filtering before scoring."""

import json
import math
import re
from collections import Counter
from importlib.resources import files

STOP = set("the a an to for and is of in on how can my do i what when does are after with from by it".split())


def terms(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


def catalog() -> list[dict]:
    return json.loads(files("workforce_knowledge").joinpath("data/passages.json").read_text())


def retrieve(query: str, support: bool = False) -> list[dict]:
    docs = [p for p in catalog() if p["scope"] == "public" or support]
    tokens = [terms(p["title"]+" "+p["title"]+" "+p["text"]) for p in docs]
    mean_size = sum(map(len, tokens))/len(tokens)
    q = set(terms(query))
    ranked = []
    for doc, words in zip(docs, tokens):
        counts = Counter(words)
        matched = q.intersection(counts)
        if len(matched) < 2 or len(matched) / max(1, len(q)) < 0.35:
            continue
        score = 0.0
        for word in sorted(matched):
            frequency = sum(word in bag for bag in tokens)
            idf = math.log1p((len(docs)-frequency+0.5)/(frequency+0.5))
            tf = counts[word]
            score += idf*tf*2.2/(tf+1.2*(0.25+0.75*len(words)/mean_size))
        if score >= 4.0:
            ranked.append(dict(**doc, score=round(score, 5)))
    return sorted(ranked, key=lambda d: (-d["score"], d["id"]))[:3]
