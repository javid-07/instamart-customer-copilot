from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
RFM_PATH = ROOT / "outputs" / "rfm.csv"

rfm = pd.read_csv(RFM_PATH)
features = ["recency", "frequency", "monetary"]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(rfm[features])

model = KMeans(
    n_clusters=4,
    n_init=10,
    random_state=42,
)

rfm["segment_id"] = model.fit_predict(X_scaled)

profiles = (
    rfm.groupby("segment_id")
    .agg(
        customer_count=("customer_id", "count"),
        mean_recency=("recency", "mean"),
        mean_frequency=("frequency", "mean"),
        mean_monetary=("monetary", "mean"),
    )
    .round(2)
    .sort_values("customer_count", ascending=False)
)

print("\nK=4 segment profiles")
print(profiles.to_string())

print("\nSegment sizes:")
print(rfm["segment_id"].value_counts().sort_index())
