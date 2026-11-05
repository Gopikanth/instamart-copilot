import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

POLICY_DIR = "data/policies"
CHUNK_SIZE = 40
OVERLAP = 10


def chunk_text(text, size=CHUNK_SIZE, overlap=OVERLAP):
    words = text.split()
    step = size - overlap
    chunks = []
    start = 0
    while True:
        chunks.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break
        start += step
    return chunks


def build_chunks(size=CHUNK_SIZE, overlap=OVERLAP):
    chunks = []
    for name in sorted(os.listdir(POLICY_DIR)):
        if name.endswith(".txt"):
            with open(os.path.join(POLICY_DIR, name), encoding="utf-8") as f:
                text = f.read()
            for piece in chunk_text(text, size, overlap):
                chunks.append({"source": name, "text": piece})
    return chunks


chunks = build_chunks()
print(len(chunks))
print(Counter(c["source"] for c in chunks))