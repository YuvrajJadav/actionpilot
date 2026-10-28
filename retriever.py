"""Tiny dependency-free RAG retriever: paragraph chunks + TF-IDF + cosine similarity."""
import math, re
from collections import Counter
from pathlib import Path

STOP = {"the", "a", "an", "and", "or", "to", "of", "for", "in", "on", "at", "by", "is", "are", "be", "we", "it",
        "this", "that", "with", "will", "should", "needs", "need", "must", "from", "as", "status"}


def tokenize(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words if w not in STOP and len(w) > 1]


class KnowledgeBase:
    def __init__(self, chunks):
        self.chunks = chunks  # [{"source": filename, "text": paragraph}]
        docs = [Counter(tokenize(c["text"])) for c in chunks]
        df = Counter(t for d in docs for t in d)
        n = len(docs)
        self.idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}
        self.vecs = [self._vector(d) for d in docs]

    def _vector(self, counts):
        v = {t: (1 + math.log(c)) * self.idf[t] for t, c in counts.items() if t in self.idf}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / norm for t, x in v.items()}

    def search(self, query, k=3, min_score=0.15, source=None):
        q = self._vector(Counter(tokenize(query)))
        scored = [(sum(w * vec.get(t, 0.0) for t, w in q.items()), i) for i, vec in enumerate(self.vecs)
                  if source is None or self.chunks[i]["source"] == source]
        return [{**self.chunks[i], "score": round(s, 3)}
                for s, i in sorted(scored, reverse=True)[:k] if s >= min_score]


def load_kb(folder=None):
    """Load every .md file in the knowledge folder. Missing folder -> empty KB (app still works)."""
    folder = Path(folder) if folder else Path(__file__).parent / "knowledge"
    chunks = []
    for path in sorted(folder.glob("*.md")) if folder.exists() else []:
        for para in re.split(r"\n\s*\n", path.read_text(encoding="utf-8")):
            para = para.strip()
            if len(para) > 15 and not all(l.startswith("#") for l in para.splitlines()):
                chunks.append({"source": path.name, "text": para})
    return KnowledgeBase(chunks)
