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