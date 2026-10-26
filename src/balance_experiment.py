
from pathlib import Path

import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "outputs" / "lapse_features.csv"

data = pd.read_csv(DATA_PATH)
X = data.drop(columns=["customer_id", "lapsed"])
y = data["lapsed"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

categorical = ["city", "gender", "favourite_category"]
numeric = [c for c in X.columns if c not in categorical]

preprocessor = ColumnTransformer([
    ("numeric", StandardScaler(), numeric),
    ("categorical",
     OneHotEncoder(drop="first", handle_unknown="ignore"),
     categorical),
])

# Best logistic regression found by GridSearchCV.
base_model = Pipeline([
    ("preprocessor", preprocessor),
    ("model", LogisticRegression(C=0.1, max_iter=1000)),
])

base_model.fit(X_train, y_train)
base_pred = base_model.predict(X_test)

# Oversample lapsed training rows only, with replacement.
train = X_train.copy()
train["lapsed"] = y_train.to_numpy()

majority_count = int((train["lapsed"] == 0).sum())
minority = train[train["lapsed"] == 1]
needed = majority_count - len(minority)

extra = minority.sample(
    n=needed,
    replace=True,
    random_state=42,
)

balanced = pd.concat([train, extra], ignore_index=True)
X_balanced = balanced.drop(columns="lapsed")
y_balanced = balanced["lapsed"]

print("Balanced training counts:")
print(y_balanced.value_counts().sort_index())

balanced_model = clone(base_model)
balanced_model.fit(X_balanced, y_balanced)
balanced_pred = balanced_model.predict(X_test)

for name, predictions in [
    ("Original training", base_pred),
    ("Balanced training", balanced_pred),
]:
    print(f"\n{name}")
    print("Precision:", round(
        precision_score(y_test, predictions, zero_division=0), 3
    ))
    print("Recall:", round(
        recall_score(y_test, predictions, zero_division=0), 3
    ))
    print("F1:", round(
        f1_score(y_test, predictions, zero_division=0), 3
    ))
