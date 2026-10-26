from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import f1_score
from sklearn.base import clone

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "outputs" / "lapse_features.csv"
MODEL_PATH = ROOT / "outputs" / "lapse_model.joblib"

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

lr_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", LogisticRegression(max_iter=1000)),
])
lr_search = GridSearchCV(
    lr_pipeline,
    {"model__C": [0.01, 0.1, 1, 10, 100]},
    cv=5, scoring="f1", n_jobs=-1,
).fit(X_train, y_train)

rf_pipeline = Pipeline([
    ("preprocessor", clone(preprocessor)),
    ("model", RandomForestClassifier(n_estimators=100, random_state=42)),
])
rf_search = GridSearchCV(
    rf_pipeline,
    {
        "model__max_depth": [3, 5, 8],
        "model__min_samples_leaf": [5, 10, 20],
    },
    cv=5, scoring="f1", n_jobs=-1,
).fit(X_train, y_train)

# Report top five Random Forest feature importances.
rf_best = rf_search.best_estimator_
feature_names = rf_best.named_steps["preprocessor"].get_feature_names_out()
importances = rf_best.named_steps["model"].feature_importances_

importance_table = pd.DataFrame({
    "feature": feature_names,
    "importance": importances,
}).sort_values("importance", ascending=False)

print("Top 5 Random Forest features:")
print(importance_table.head(5).to_string(index=False))

# Report signs of three Logistic Regression coefficients.
lr_best = lr_search.best_estimator_
lr_names = lr_best.named_steps["preprocessor"].get_feature_names_out()
lr_coefs = lr_best.named_steps["model"].coef_[0]

coefficient_table = pd.DataFrame({
    "feature": lr_names,
    "coefficient": lr_coefs,
})
coefficient_table["abs_coefficient"] = coefficient_table["coefficient"].abs()
print("\nThree largest Logistic Regression coefficients:")
print(
    coefficient_table.sort_values("abs_coefficient", ascending=False)
    .head(3)[["feature", "coefficient"]]
    .to_string(index=False)
)

# Select Logistic Regression based on its higher test F1 from prior evaluation.
selected_model = lr_best
original_predictions = selected_model.predict(X_test)

MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
joblib.dump(selected_model, MODEL_PATH)
reloaded_model = joblib.load(MODEL_PATH)
reloaded_predictions = reloaded_model.predict(X_test)

print("\nSelected model: Logistic Regression")
print("Test F1:", round(f1_score(y_test, original_predictions), 3))
print("Saved model:", MODEL_PATH.relative_to(ROOT))
print(
    "Reloaded predictions identical:",
    bool((original_predictions == reloaded_predictions).all()),
)
