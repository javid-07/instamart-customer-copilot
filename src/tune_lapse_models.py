
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "outputs" / "lapse_features.csv"

data = pd.read_csv(DATA_PATH)

X = data.drop(columns=["customer_id", "lapsed"])
y = data["lapsed"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

categorical_features = ["city", "gender", "favourite_category"]
numeric_features = [c for c in X.columns if c not in categorical_features]

preprocessor = ColumnTransformer(
    [
        ("numeric", StandardScaler(), numeric_features),
        ("categorical",
         OneHotEncoder(drop="first", handle_unknown="ignore"),
         categorical_features),
    ]
)

# Logistic Regression: preprocessing is fitted inside each CV fold.
lr_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", LogisticRegression(max_iter=1000)),
])

lr_search = GridSearchCV(
    lr_pipeline,
    {"model__C": [0.01, 0.1, 1, 10, 100]},
    cv=5,
    scoring="f1",
    n_jobs=-1,
)
lr_search.fit(X_train, y_train)

print("Logistic Regression best parameters:", lr_search.best_params_)
print("Logistic Regression best CV F1:", round(lr_search.best_score_, 3))

# Random Forest: same train-only preprocessing discipline.
rf_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", RandomForestClassifier(n_estimators=100, random_state=42)),
])

rf_search = GridSearchCV(
    rf_pipeline,
    {
        "model__max_depth": [3, 5, 8],
        "model__min_samples_leaf": [5, 10, 20],
    },
    cv=5,
    scoring="f1",
    n_jobs=-1,
)
rf_search.fit(X_train, y_train)

print("\nRandom Forest best parameters:", rf_search.best_params_)
print("Random Forest best CV F1:", round(rf_search.best_score_, 3))

# Evaluate each tuned model on the untouched test set only after tuning.
for name, search in [
    ("Logistic Regression", lr_search),
    ("Random Forest", rf_search),
]:
    predictions = search.predict(X_test)
    print(f"\n{name} test results")
    print("Confusion matrix:")
    print(confusion_matrix(y_test, predictions))
    print(classification_report(
        y_test, predictions, labels=[1], target_names=["lapsed"],
        zero_division=0,
    ))
    print("Test accuracy:", round(accuracy_score(y_test, predictions), 3))
    print("Lapsed-class F1:", round(
        f1_score(y_test, predictions, zero_division=0), 3
    ))
