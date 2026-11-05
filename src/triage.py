import os
import random
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import re
import time
import random
from mock_llm import est_tokens, reset, chat, TransientLLMError

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

ZERO_SHOT = ('CLASSIFY the support ticket into one category: billing, delivery, technical or fraud. '
             'Reply with JSON only: {"category": "...", "reason": "..."}')

FEW_SHOT = ZERO_SHOT + """
EXAMPLES:
Ticket: I was charged twice for one order. -> {"category": "billing", "reason": "double charge"}
Ticket: The rider has not arrived yet. -> {"category": "delivery", "reason": "late rider"}
Ticket: The app crashes when I log in. -> {"category": "technical", "reason": "app crash"}
Ticket: Someone used my card without permission. -> {"category": "fraud", "reason": "unauthorized use"}"""

CATEGORIES = ["billing", "delivery", "technical", "fraud"]
for prompt in (ZERO_SHOT, FEW_SHOT):
    assert "CLASSIFY" in prompt
    assert all(c in prompt for c in CATEGORIES)
assert "EXAMPLES:" not in ZERO_SHOT
assert "EXAMPLES:" in FEW_SHOT
print(est_tokens(ZERO_SHOT), est_tokens(FEW_SHOT))
reset()
sample = tickets.loc[0, "redacted"]
response = chat([
    {"role": "system", "content": ZERO_SHOT},
    {"role": "user", "content": sample},
])
print(response.choices[0].message.content)
print(response.usage.total_tokens)

BASE_DELAY = 0.05
MAX_RETRIES = 3

retry_stats = {"errors": 0}
waits = []


def call_with_retry(messages, ticket_id):
    for attempt in range(MAX_RETRIES + 1):
        try:
            return chat(messages)
        except TransientLLMError:
            retry_stats["errors"] += 1
            if attempt == MAX_RETRIES:
                raise
            wait = BASE_DELAY * 2 ** attempt * random.uniform(0.9, 1.15)
            low = BASE_DELAY * 2 ** attempt * 0.9
            high = BASE_DELAY * 2 ** attempt * 1.15
            assert low <= wait <= high, "wait outside the allowed jitter range"
            waits.append(wait)
            print(f"retry {attempt} for {ticket_id}: waiting {wait:.4f}s")
            time.sleep(wait)
random.seed(42)
reset()

done = 0
for _, row in tickets[~is_empty & ~is_long].iterrows():
    call_with_retry(
        [{"role": "system", "content": ZERO_SHOT},
         {"role": "user", "content": row["redacted"]}],
        row["ticket_id"],
    )
    done += 1

print(done, retry_stats["errors"], len(waits), round(min(waits), 4), round(max(waits), 4))