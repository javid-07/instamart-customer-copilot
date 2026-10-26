
from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
RFM_PATH = ROOT / "outputs" / "rfm.csv"

rfm = pd.read_csv(RFM_PATH)

features = ["recency", "frequency", "monetary"]
X = rfm[features]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

results = []

for k in range(2, 9):
    model = KMeans(
        n_clusters=k,
        n_init=10,
        random_state=42,
    )
    labels = model.fit_predict(X_scaled)

    results.append({
        "k": k,
        "inertia": model.inertia_,
        "silhouette": silhouette_score(X_scaled, labels),
    })

results_df = pd.DataFrame(results)

print("\nK-means evaluation")
print(results_df.to_string(
    index=False,
    formatters={
        "inertia": "{:.1f}".format,
        "silhouette": "{:.3f}".format,
    },
))

output_path = ROOT / "outputs" / "kmeans_evaluation.csv"
results_df.to_csv(output_path, index=False)
print(f"\nSaved: {output_path.relative_to(ROOT)}")
