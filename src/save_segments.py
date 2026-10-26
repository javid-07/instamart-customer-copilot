
from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
RFM_PATH = ROOT / "outputs" / "rfm.csv"
OUTPUT_PATH = ROOT / "outputs" / "customer_segments.csv"

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

# Name segments using their measured profiles, not cluster number order.
profiles = rfm.groupby("segment_id")["monetary"].mean()
premium_id = profiles.idxmax()

segment_names = {
    0: "Occasional Shoppers",
    1: "Premium Spenders",
    2: "Loyal Frequent Buyers",
    3: "At-Risk Inactive Customers",
}

# Verify names correspond to this fitted model's segment profiles.
profile_table = rfm.groupby("segment_id").agg(
    mean_recency=("recency", "mean"),
    mean_frequency=("frequency", "mean"),
    mean_monetary=("monetary", "mean"),
)

# Apply names based on profile characteristics, since cluster IDs
# are labels and can change if the data or model changes.
name_by_id = {}
for segment_id, row in profile_table.iterrows():
    if segment_id == premium_id:
        name_by_id[segment_id] = "Premium Spenders"
    elif row["mean_frequency"] >= 15:
        name_by_id[segment_id] = "Loyal Frequent Buyers"
    elif row["mean_recency"] >= 60:
        name_by_id[segment_id] = "At-Risk Inactive Customers"
    else:
        name_by_id[segment_id] = "Occasional Shoppers"

rfm["segment_name"] = rfm["segment_id"].map(name_by_id)
rfm["is_premium"] = rfm["segment_id"].eq(premium_id)

# PCA on the standardized RFM matrix
pca = PCA(n_components=2)
pca.fit(X_scaled)

print("PCA explained variance ratios:",
      pca.explained_variance_ratio_.round(3).tolist())
print("PCA total explained variance:",
      round(pca.explained_variance_ratio_.sum(), 3))
print("Premium segment ID:", premium_id)
print("\nSegment profile:")
print(profile_table.round(2).to_string())

rfm[
    [
        "customer_id",
        "recency",
        "frequency",
        "monetary",
        "segment_id",
        "segment_name",
        "is_premium",
    ]
].to_csv(OUTPUT_PATH, index=False)

print(f"\nSaved: {OUTPUT_PATH.relative_to(ROOT)}")
print("Premium customers:", int(rfm["is_premium"].sum()))
