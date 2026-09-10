import pandas as pd
import numpy as np

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import (
    KMeans,
    AgglomerativeClustering,
    DBSCAN
)
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA


# ============================================================
# CLUSTERING SERVICE
# ============================================================
#
# Responsibilities:
# 1. Prepare RFM features
# 2. Scale features
# 3. Run multiple clustering algorithms
# 4. Compare algorithms using Silhouette Score
# 5. Select the best clustering method
# 6. Generate PCA coordinates
# 7. Return production-ready clustering metadata
#
# ============================================================


def cluster_customers(
    rfm: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:

    # ========================================================
    # 1. COPY INPUT
    # ========================================================

    data = rfm.copy()

    # ========================================================
    # 2. VALIDATE REQUIRED COLUMNS
    # ========================================================

    required_columns = [
        "CustomerID",
        "Recency",
        "Frequency",
        "Monetary"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    if len(data) < 3:

        raise ValueError(
            "At least 3 customers are required "
            "for clustering."
        )

    # ========================================================
    # 3. PREPARE RFM FEATURES
    # ========================================================

    features = data[
        [
            "Recency",
            "Frequency",
            "Monetary"
        ]
    ].copy()

    # Convert to numeric

    for column in [
        "Recency",
        "Frequency",
        "Monetary"
    ]:

        features[column] = pd.to_numeric(
            features[column],
            errors="coerce"
        )

    # Replace invalid values

    features = features.replace(
        [np.inf, -np.inf],
        np.nan
    )

    features = features.fillna(0)

    # ========================================================
    # 4. SCALE FEATURES
    # ========================================================

    scaler = StandardScaler()

    scaled_features = scaler.fit_transform(
        features
    )

    # ========================================================
    # 5. DETERMINE POSSIBLE K VALUES
    # ========================================================

    customer_count = len(data)

    max_k = min(
        8,
        customer_count - 1
    )

    k_values = range(
        2,
        max_k + 1
    )

    # ========================================================
    # 6. STORE MODEL RESULTS
    # ========================================================

    results = []

    model_outputs = {}

    # ========================================================
    # 7. K-MEANS
    # ========================================================

    for k in k_values:

        try:

            model = KMeans(
                n_clusters=k,
                random_state=42,
                n_init=20
            )

            labels = model.fit_predict(
                scaled_features
            )

            unique_labels = len(
                np.unique(labels)
            )

            if unique_labels >= 2:

                score = silhouette_score(
                    scaled_features,
                    labels
                )

                results.append({
                    "method": "K-Means",
                    "clusters": int(k),
                    "silhouette_score": float(
                        score
                    )
                })

                model_outputs[
                    f"K-Means-{k}"
                ] = {
                    "labels": labels,
                    "score": score
                }

        except Exception:

            continue

    # ========================================================
    # 8. HIERARCHICAL / AGGLOMERATIVE CLUSTERING
    # ========================================================

    for k in k_values:

        try:

            model = AgglomerativeClustering(
                n_clusters=k
            )

            labels = model.fit_predict(
                scaled_features
            )

            unique_labels = len(
                np.unique(labels)
            )

            if unique_labels >= 2:

                score = silhouette_score(
                    scaled_features,
                    labels
                )

                results.append({
                    "method": "Hierarchical",
                    "clusters": int(k),
                    "silhouette_score": float(
                        score
                    )
                })

                model_outputs[
                    f"Hierarchical-{k}"
                ] = {
                    "labels": labels,
                    "score": score
                }

        except Exception:

            continue

    # ========================================================
    # 9. DBSCAN
    # ========================================================

    dbscan_configs = [
        {
            "eps": 0.5,
            "min_samples": 2
        },
        {
            "eps": 0.7,
            "min_samples": 2
        },
        {
            "eps": 1.0,
            "min_samples": 2
        },
        {
            "eps": 1.2,
            "min_samples": 2
        }
    ]

    for config in dbscan_configs:

        try:

            model = DBSCAN(
                eps=config["eps"],
                min_samples=config["min_samples"]
            )

            labels = model.fit_predict(
                scaled_features
            )

            # Ignore noise points (-1)
            valid_mask = labels != -1

            valid_labels = labels[
                valid_mask
            ]

            unique_labels = len(
                np.unique(valid_labels)
            )

            valid_samples = (
                valid_mask.sum()
            )

            if (
                unique_labels >= 2
                and valid_samples >= 3
            ):

                score = silhouette_score(
                    scaled_features[
                        valid_mask
                    ],
                    valid_labels
                )

                results.append({
                    "method": "DBSCAN",
                    "clusters": int(
                        unique_labels
                    ),
                    "silhouette_score": float(
                        score
                    ),
                    "eps": config["eps"],
                    "min_samples":
                        config["min_samples"]
                })

                model_outputs[
                    f"DBSCAN-{config['eps']}"
                ] = {
                    "labels": labels,
                    "score": score
                }

        except Exception:

            continue

    # ========================================================
    # 10. CHECK WHETHER ANY MODEL WORKED
    # ========================================================

    if not results:

        raise ValueError(
            "Unable to generate valid clustering "
            "results for this dataset."
        )

    # ========================================================
    # 11. FIND BEST MODEL
    # ========================================================

    best_result = max(
        results,
        key=lambda item:
            item["silhouette_score"]
    )

    best_method = (
        best_result["method"]
    )

    best_clusters = (
        best_result["clusters"]
    )

    best_score = (
        best_result["silhouette_score"]
    )

    # ========================================================
    # 12. GET BEST LABELS
    # ========================================================

    if best_method == "K-Means":

        key = (
            f"K-Means-{best_clusters}"
        )

    elif best_method == "Hierarchical":

        key = (
            f"Hierarchical-{best_clusters}"
        )

    else:

        key = (
            f"DBSCAN-{best_result['eps']}"
        )

    best_labels = model_outputs[
        key
    ]["labels"]

    # ========================================================
    # 13. SAVE CLUSTER INFORMATION
    # ========================================================

    data["Cluster"] = best_labels

    data["Clustering_Method"] = (
        best_method
    )

    data["Silhouette_Score"] = (
        round(
            float(best_score),
            4
        )
    )

    # ========================================================
    # 14. PCA FOR VISUALIZATION
    # ========================================================

    pca = PCA(
        n_components=2,
        random_state=42
    )

    pca_features = pca.fit_transform(
        scaled_features
    )

    data["PCA1"] = (
        pca_features[:, 0]
    )

    data["PCA2"] = (
        pca_features[:, 1]
    )

    # ========================================================
    # 15. MODEL COMPARISON
    # ========================================================

    comparison = []

    for result in results:

        comparison.append({
            "method":
                result["method"],

            "clusters":
                result["clusters"],

            "silhouette_score":
                round(
                    result[
                        "silhouette_score"
                    ],
                    4
                )
        })

    comparison = sorted(
        comparison,
        key=lambda item:
            item["silhouette_score"],
        reverse=True
    )

    # ========================================================
    # 16. CLUSTER SUMMARY
    # ========================================================

    cluster_summary = (
        data
        .groupby("Cluster")
        .agg(
            customer_count=(
                "CustomerID",
                "count"
            ),

            avg_recency=(
                "Recency",
                "mean"
            ),

            avg_frequency=(
                "Frequency",
                "mean"
            ),

            avg_monetary=(
                "Monetary",
                "mean"
            )
        )
        .reset_index()
    )

    # ========================================================
    # 17. ROUND SUMMARY
    # ========================================================

    cluster_summary[
        "avg_recency"
    ] = cluster_summary[
        "avg_recency"
    ].round(2)

    cluster_summary[
        "avg_frequency"
    ] = cluster_summary[
        "avg_frequency"
    ].round(2)

    cluster_summary[
        "avg_monetary"
    ] = cluster_summary[
        "avg_monetary"
    ].round(2)

    # ========================================================
    # 18. METADATA
    # ========================================================

    metadata = {

        "best_method":
            best_method,

        "best_clusters":
            int(best_clusters),

        "best_silhouette_score":
            round(
                float(best_score),
                4
            ),

        "comparison":
            comparison,

        "cluster_summary":
            cluster_summary.to_dict(
                orient="records"
            ),

        "pca_explained_variance":
            [
                round(
                    float(value),
                    4
                )
                for value in
                pca.explained_variance_ratio_
            ]
    }

    # ========================================================
    # 19. RETURN
    # ========================================================

    return data, metadata