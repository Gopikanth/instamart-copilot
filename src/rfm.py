import pandas as pd


orders = pd.read_csv("data/clean/orders.csv", parse_dates=["order_ts"])
completed = orders[orders["status"] == "completed"]
snapshot = pd.Timestamp("2025-10-01 00:00:00")

g = completed.groupby("customer_id").agg(
    last_order_ts=("order_ts", "max"),
    frequency=("order_id", "nunique"),
    monetary=("order_amount", "sum"),
)
g["recency"] = (snapshot - g["last_order_ts"]).dt.days
rfm = g[["recency", "frequency", "monetary"]].reset_index()

print(len(rfm))
print(rfm["recency"].median(), rfm["recency"].min(), rfm["recency"].max())
print(round(rfm["frequency"].mean(), 2), rfm["frequency"].max())
print(round(rfm["monetary"].mean(), 2), round(rfm["monetary"].max(), 2))
print(rfm.head())

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

X = StandardScaler().fit_transform(rfm[["recency", "frequency", "monetary"]])
print(X.shape)
print(X.mean(axis=0).round(3), X.std(axis=0).round(3))

import pandas as pd

rows = []
for k in range(2, 9):
    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
    rows.append((k, round(km.inertia_, 1), round(silhouette_score(X, km.labels_), 3)))

table = pd.DataFrame(rows, columns=["K", "inertia", "silhouette"])
print(table.to_string(index=False))