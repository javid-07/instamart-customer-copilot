
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "outputs" / "lapse_model.joblib"
FEATURES_PATH = ROOT / "outputs" / "lapse_features.csv"
OUTPUT_PATH = ROOT / "outputs" / "retention_list.csv"

model = joblib.load(MODEL_PATH)
data = pd.read_csv(FEATURES_PATH)

X = data.drop(columns=["customer_id", "lapsed"])

# Predict lapse probability for the existing cohort.
data["lapse_probability"] = model.predict_proba(X)[:, 1]
data["predicted_lapsed"] = model.predict(X)

# Rank highest predicted risk first.
retention_list = data.sort_values(
    "lapse_probability",
    ascending=False,
).copy()

retention_list["risk_rank"] = range(1, len(retention_list) + 1)

retention_list.to_csv(OUTPUT_PATH, index=False)

print("Retention list rows:", len(retention_list))
print("Saved:", OUTPUT_PATH.relative_to(ROOT))
print("\nTop 10 highest-risk customers:")
print(
    retention_list[
        [
            "customer_id",
            "lapse_probability",
            "predicted_lapsed",
            "risk_rank",
        ]
    ].head(10).to_string(index=False)
)
