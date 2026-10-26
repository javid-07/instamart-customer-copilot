
from pathlib import Path

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "outputs" / "lapse_model.joblib"
FEATURES_PATH = ROOT / "outputs" / "lapse_features.csv"
SEGMENTS_PATH = ROOT / "outputs" / "customer_segments.csv"
OUTPUT_PATH = ROOT / "outputs" / "retention_list.csv"

model = joblib.load(MODEL_PATH)
data = pd.read_csv(FEATURES_PATH)
segments = pd.read_csv(SEGMENTS_PATH)

# Reproduce the original stratified split exactly.
X = data.drop(columns=["customer_id", "lapsed"])
y = data["lapsed"]

_, X_test, _, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    stratify=y,
    random_state=42,
)

# Recover test customer IDs using the same split indices.
_, test_data = train_test_split(
    data,
    test_size=0.2,
    stratify=data["lapsed"],
    random_state=42,
)

test_data = test_data.copy()
test_data["actually_lapsed"] = y_test.to_numpy()

# Premium flag is defined by the whole-window RFM segmentation.
premium_ids = set(
    segments.loc[segments["is_premium"].astype(bool), "customer_id"]
)
premium_test = test_data[
    test_data["customer_id"].isin(premium_ids)
].copy()

X_premium_test = premium_test.drop(
    columns=["customer_id", "lapsed", "actually_lapsed"]
)

premium_test["lapse_probability"] = model.predict_proba(
    X_premium_test
)[:, 1]

retention_list = (
    premium_test.sort_values("lapse_probability", ascending=False)
    .head(10)
    [["customer_id", "lapse_probability", "actually_lapsed"]]
)

retention_list.to_csv(OUTPUT_PATH, index=False)

print("Premium customers in test set:", len(premium_test))
print("Retention list rows:", len(retention_list))
print("Truly lapsed in top 10:",
      int(retention_list["actually_lapsed"].sum()))
print(f"Saved: {OUTPUT_PATH.relative_to(ROOT)}")
print("\nRetention list:")
print(retention_list.to_string(index=False))
