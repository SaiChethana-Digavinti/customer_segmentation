import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


# ---------------------------------------------------------
# 1. File paths
# ---------------------------------------------------------

INPUT_FILE = Path(
    "data/processed/ml_ready_features.csv"
)


# ---------------------------------------------------------
# 2. Load ML-ready data
# ---------------------------------------------------------

print("Loading ML-ready customer data...")

df = pd.read_csv(INPUT_FILE)

print(f"Customers loaded: {len(df):,}")


# ---------------------------------------------------------
# 3. Select clustering features
# ---------------------------------------------------------

features = [
    "Recency_scaled",
    "Frequency_scaled",
    "Monetary_scaled"
]

X = df[features]


# ---------------------------------------------------------
# 4. Evaluate different values of K
# ---------------------------------------------------------

k_values = range(2, 11)

inertias = []
silhouette_scores = []


print("\nEvaluating cluster counts...")

for k in k_values:

    model = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10
    )

    labels = model.fit_predict(X)

    inertia = model.inertia_

    silhouette = silhouette_score(
        X,
        labels
    )

    inertias.append(inertia)
    silhouette_scores.append(silhouette)

    print(
        f"K = {k:2d} | "
        f"Inertia = {inertia:,.2f} | "
        f"Silhouette Score = {silhouette:.4f}"
    )


# ---------------------------------------------------------
# 5. Create visualization folder
# ---------------------------------------------------------

output_dir = Path(
    "data/processed/model_evaluation"
)

output_dir.mkdir(
    parents=True,
    exist_ok=True
)


# ---------------------------------------------------------
# 6. Elbow Method graph
# ---------------------------------------------------------

plt.figure(figsize=(10, 6))

plt.plot(
    list(k_values),
    inertias,
    marker="o"
)

plt.title(
    "Elbow Method for Optimal Number of Clusters"
)

plt.xlabel("Number of Clusters (K)")
plt.ylabel("Inertia")

plt.xticks(
    list(k_values)
)

plt.grid(True)

elbow_file = (
    output_dir /
    "elbow_method.png"
)

plt.savefig(
    elbow_file,
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ---------------------------------------------------------
# 7. Silhouette Score graph
# ---------------------------------------------------------

plt.figure(figsize=(10, 6))

plt.plot(
    list(k_values),
    silhouette_scores,
    marker="o"
)

plt.title(
    "Silhouette Score by Number of Clusters"
)

plt.xlabel("Number of Clusters (K)")
plt.ylabel("Silhouette Score")

plt.xticks(
    list(k_values)
)

plt.grid(True)

silhouette_file = (
    output_dir /
    "silhouette_scores.png"
)

plt.savefig(
    silhouette_file,
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ---------------------------------------------------------
# 8. Save evaluation results
# ---------------------------------------------------------

results = pd.DataFrame({
    "K": list(k_values),
    "Inertia": inertias,
    "Silhouette_Score": silhouette_scores
})

results_file = (
    output_dir /
    "cluster_evaluation.csv"
)

results.to_csv(
    results_file,
    index=False
)


# ---------------------------------------------------------
# 9. Display best silhouette score
# ---------------------------------------------------------

best_index = (
    silhouette_scores.index(
        max(silhouette_scores)
    )
)

best_k = list(k_values)[best_index]

best_score = silhouette_scores[best_index]


print("\n" + "=" * 60)
print("CLUSTER EVALUATION COMPLETED")
print("=" * 60)

print(
    f"Best Silhouette Score: "
    f"{best_score:.4f}"
)

print(
    f"Best K based on Silhouette Score: "
    f"{best_k}"
)

print("\nGenerated files:")

print(elbow_file)
print(silhouette_file)
print(results_file)