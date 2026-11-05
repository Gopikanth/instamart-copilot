import os
import sys
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mock_llm import chat


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

def make_retriever(chunk_list):
    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform([c["text"] for c in chunk_list])

    def retrieve(query, k=3):
        q = vectorizer.transform([query])
        scores = cosine_similarity(q, matrix)[0]
        top = scores.argsort()[::-1][:k]
        return [{"source": chunk_list[i]["source"],
                 "score": float(scores[i]),
                 "text": chunk_list[i]["text"]} for i in top]

    return retrieve, matrix


retrieve, matrix = make_retriever(chunks)
print(matrix.shape)
for r in retrieve("refund policy late delivery"):
    print(r["source"], round(r["score"], 3), r["text"][:60])

SYSTEM_PROMPT = ("You are a POLICY ASSISTANT. Answer ONLY from the supplied CONTEXT. "
                 "If the context does not contain the answer, say that you could not "
                 "find the information in the policy documents.")


def build_user_message(question, results):
    parts = ["CONTEXT:"]
    for r in results:
        parts.append(f"[{r['source']}]")
        parts.append(r["text"])
    parts.append("QUESTION:")
    parts.append(question)
    return "\n".join(parts)


def answer(question, retriever=None):
    retriever = retriever or retrieve
    results = retriever(question, k=3)
    response = chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_message(question, results)},
    ])
    return {"answer": response.choices[0].message.content,
            "sources": [r["source"] for r in results]}


print(answer("What delivery time makes a completed order eligible for a full refund?"))
print(answer("What is the capital of France?"))