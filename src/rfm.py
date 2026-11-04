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