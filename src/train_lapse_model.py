
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "outputs" / "lapse_features.csv"

data = pd.read_csv(DATA_PATH)

target = "lapsed"
drop_columns = ["customer_id", target]

X = data.drop(columns=drop_columns)
y = data[target]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    stratify=y,
    random_state=42,
)

# Baseline: always predict "not lapsed" (class 0).
baseline_predictions = pd.Series(0, index=y_test.index)

print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))
print("Training lapsed:", int(y_train.sum()))
print("Testing lapsed:", int(y_test.sum()))
print("Test baseline accuracy:",
      round(accuracy_score(y_test, baseline_predictions), 3))
print("Test baseline lapsed-class F1:",
      round(f1_score(y_test, baseline_predictions, zero_division=0), 3))
print("Baseline confusion matrix:")
print(confusion_matrix(y_test, baseline_predictions))


from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline

categorical_features = ["city", "gender", "favourite_category"]
numeric_features = [
    col for col in X.columns
    if col not in categorical_features
]

preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            StandardScaler(),
            numeric_features,
        ),
        (
            "categorical",
            OneHotEncoder(drop="first", handle_unknown="ignore"),
            categorical_features,
        ),
    ]
)

# Fit preprocessing on training rows only.
X_train_transformed = preprocessor.fit_transform(X_train)

# Apply the already-fitted transformations to test rows.
X_test_transformed = preprocessor.transform(X_test)

print("\nPreprocessing verification")
print("Train transformed shape:", X_train_transformed.shape)
print("Test transformed shape:", X_test_transformed.shape)

# Compare fitted training frequency mean with the full-cohort mean.
frequency_index = numeric_features.index("frequency")
train_frequency_mean = preprocessor.named_transformers_[
    "numeric"
].mean_[frequency_index]

print("Training scaler frequency mean:", round(train_frequency_mean, 4))
print("Full-cohort frequency mean:", round(data["frequency"].mean(), 4))

print("Missing values in feature data:", int(X.isna().sum().sum()))
assert not X.isna().any().any()
