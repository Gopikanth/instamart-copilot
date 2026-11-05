import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import re
from mock_llm import est_tokens

MAX_INPUT_TOKENS = 400

tickets = pd.read_csv("data/raw/tickets.csv", keep_default_na=False)
tickets["est_tokens"] = tickets["text"].map(est_tokens)

is_empty = tickets["text"].str.strip() == ""
is_long = tickets["est_tokens"] > MAX_INPUT_TOKENS

print(len(tickets), is_empty.sum(), is_long.sum(), tickets.loc[is_long, "est_tokens"].unique())
print((~is_empty & ~is_long).sum())

PATTERNS = [
    ("EMAIL", r"[\w.+-]+@[\w-]+\.[\w.]+", "[EMAIL]"),
    ("PHONE", r"\b[6-9]\d{9}\b", "[PHONE]"),
    ("ORDER_ID", r"ORD-\d{6}", "[ORDER_ID]"),
]


def redact(text, counts=None):
    for name, pattern, placeholder in PATTERNS:
        text, n = re.subn(pattern, placeholder, text)
        if counts is not None:
            counts[name] += n
    return text


counts = {"EMAIL": 0, "PHONE": 0, "ORDER_ID": 0}
tickets["redacted"] = [redact(t, counts) for t in tickets["text"]]
print(counts, sum(counts.values()))

left = sum(len(re.findall(p, t)) for t in tickets["redacted"] for _, p, _ in PATTERNS)
print(left)
assert left == 0, "personal information is still present"