import pandas as pd

orders = pd.read_csv("data/clean/orders.csv", parse_dates=["order_ts"])
customers = pd.read_csv("data/clean/customers.csv", parse_dates=["signup_date"])
products = pd.read_csv("data/clean/products.csv")

cutoff = pd.Timestamp("2025-09-01")
window_end = pd.Timestamp("2025-10-01")

completed = orders[orders["status"] == "completed"]
history = completed[completed["order_ts"] < cutoff]
window = completed[(completed["order_ts"] >= cutoff) & (completed["order_ts"] < window_end)]

cohort = pd.DataFrame({"customer_id": history["customer_id"].unique()})
cohort["lapsed"] = (~cohort["customer_id"].isin(window["customer_id"])).astype(int)
print(len(cohort), cohort["lapsed"].sum(), round(cohort["lapsed"].mean() * 100, 2))
all_before = orders[orders["order_ts"] < cutoff]
hist = history.merge(products[["product_id", "category"]], on="product_id")

feat = hist.groupby("customer_id").agg(
    last_order_ts=("order_ts", "max"),
    frequency=("order_id", "nunique"),
    monetary=("order_amount", "sum"),
    avg_discount=("discount_pct", "mean"),
    avg_delivery=("delivery_minutes", "mean"),
    fav_category=("category", lambda s: s.mode().iloc[0]),
)
feat["recency"] = (cutoff - feat["last_order_ts"]).dt.days
feat = feat.drop(columns="last_order_ts")

cancel_rate = (all_before.groupby("customer_id")["status"]
               .apply(lambda s: (s == "cancelled").mean())
               .rename("cancel_rate"))

data = (cohort.merge(feat.reset_index(), on="customer_id")
              .merge(cancel_rate.reset_index(), on="customer_id")
              .merge(customers, on="customer_id"))
data["tenure_days"] = (cutoff - data["signup_date"]).dt.days
data = data.drop(columns="signup_date")
print(data.shape)
print(data.isna().sum().sum())
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

y = data["lapsed"]
X_feat = data.drop(columns=["customer_id", "lapsed"])
X_train, X_test, y_train, y_test = train_test_split(
    X_feat, y, test_size=0.2, stratify=y, random_state=42)
print(len(X_train), len(X_test))

baseline = [0] * len(y_test)
print(round(accuracy_score(y_test, baseline), 3), f1_score(y_test, baseline, zero_division=0))

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

cat_cols = ["city", "gender", "fav_category"]
num_cols = [c for c in X_feat.columns if c not in cat_cols]

preprocessor = ColumnTransformer([
    ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), cat_cols),
    ("num", StandardScaler(), num_cols),
])

preprocessor.fit(X_train)
X_train_t = preprocessor.transform(X_train)
X_test_t = preprocessor.transform(X_test)
print(num_cols)
print(X_train_t.shape, X_test_t.shape)

scaler = preprocessor.named_transformers_["num"]
i = num_cols.index("frequency")
print(round(scaler.mean_[i], 3), round(data["frequency"].mean(), 3))
print(X_feat.isna().sum().sum())
assert X_feat.isna().sum().sum() == 0, "missing values found"

from lapse_data import X_train, X_test, y_train, y_test, cat_cols, num_cols

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score


def make_pre():
    return ColumnTransformer([
        ("cat", OneHotEncoder(drop="first", handle_unknown="ignore"), cat_cols),
        ("num", StandardScaler(), num_cols),
    ])


lr_grid = GridSearchCV(
    Pipeline([("pre", make_pre()), ("model", LogisticRegression(max_iter=1000))]),
    param_grid={"model__C": [0.01, 0.1, 1, 10, 100]},
    cv=5, scoring="f1",
).fit(X_train, y_train)
print("LR best:", lr_grid.best_params_, round(lr_grid.best_score_, 3))

rf_grid = GridSearchCV(
    Pipeline([("pre", make_pre()),
              ("model", RandomForestClassifier(n_estimators=100, random_state=42))]),
    param_grid={"model__max_depth": [3, 5, 8], "model__min_samples_leaf": [5, 10, 20]},
    cv=5, scoring="f1",
).fit(X_train, y_train)
print("RF best:", rf_grid.best_params_, round(rf_grid.best_score_, 3))

for name, grid in [("Logistic regression", lr_grid), ("Random forest", rf_grid)]:
    pred = grid.predict(X_test)
    print(name)
    print(confusion_matrix(y_test, pred))
    print("precision", round(precision_score(y_test, pred, zero_division=0), 3),
          "recall", round(recall_score(y_test, pred, zero_division=0), 3),
          "F1", round(f1_score(y_test, pred, zero_division=0), 3))
import pandas as pd
from sklearn.base import clone

minority = X_train[y_train == 1]
n_extra = (y_train == 0).sum() - (y_train == 1).sum()
extra = minority.sample(n=n_extra, replace=True, random_state=42)

X_bal = pd.concat([X_train, extra])
y_bal = pd.concat([y_train, pd.Series(1, index=extra.index)])
print(len(X_bal), y_bal.value_counts().to_dict())

balanced_lr = clone(lr_grid.best_estimator_).fit(X_bal, y_bal)

def scores(model):
    pred = model.predict(X_test)
    return (round(precision_score(y_test, pred, zero_division=0), 3),
            round(recall_score(y_test, pred, zero_division=0), 3),
            round(f1_score(y_test, pred, zero_division=0), 3))

print("original  precision, recall, F1:", scores(lr_grid))
print("balanced  precision, recall, F1:", scores(balanced_lr))
print(confusion_matrix(y_test, balanced_lr.predict(X_test)))

rf_best = rf_grid.best_estimator_
importance = pd.Series(
    rf_best.named_steps["model"].feature_importances_,
    index=rf_best.named_steps["pre"].get_feature_names_out(),
).sort_values(ascending=False)
print(importance.head(5).round(3))

lr_best = lr_grid.best_estimator_
coefs = pd.Series(
    lr_best.named_steps["model"].coef_[0],
    index=lr_best.named_steps["pre"].get_feature_names_out(),
)
print(coefs[["num__frequency", "cat__fav_category_Electronics", "num__cancel_rate"]].round(3))
import os
import joblib

os.makedirs("outputs", exist_ok=True)
selected = lr_grid.best_estimator_
joblib.dump(selected, "outputs/lapse_model.joblib")

reloaded = joblib.load("outputs/lapse_model.joblib")
print((reloaded.predict(X_test) == selected.predict(X_test)).all())

segments = pd.read_csv("outputs/customer_segments.csv")

test = data.loc[X_test.index, ["customer_id", "lapsed"]].copy()
test["lapse_probability"] = reloaded.predict_proba(X_test)[:, 1]
test = test.merge(segments[["customer_id", "is_premium"]], on="customer_id", how="left")

premium_test = test[test["is_premium"] == True]
top = premium_test.sort_values("lapse_probability", ascending=False).head(10)

retention = top.rename(columns={"lapsed": "actually_lapsed"})[
    ["customer_id", "lapse_probability", "actually_lapsed"]]
retention["lapse_probability"] = retention["lapse_probability"].round(4)
retention.to_csv("outputs/retention_list.csv", index=False)

print(len(premium_test), retention["actually_lapsed"].sum())
print(retention) 

#recommit
