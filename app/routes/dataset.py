from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

import pandas as pd

from io import BytesIO
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.services.rfm_service import calculate_rfm
from app.services.segmentation_service import segment_customers
from app.services.clustering_service import cluster_customers
from app.services.customer_services import reload_customer_data

from app.database.connection import SessionLocal
from app.database.customer_repository import CustomerRepository


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/dataset",
    tags=["Dataset"]
)


# =========================================================
async def read_dataset(
    file: UploadFile
) -> pd.DataFrame:

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Please upload a file."
        )

    filename = file.filename.lower()

    try:
        file_content = await file.read()

        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty."
            )

        df = None

        # Strategy 1: Excel formats (.xlsx, .xls, .xlsm, .xlsb, .ods)
        if any(filename.endswith(ext) for ext in [".xlsx", ".xls", ".xlsm", ".xlsb", ".ods"]):
            try:
                df = pd.read_excel(BytesIO(file_content))
            except Exception:
                pass

        # Strategy 2: Parquet formats (.parquet, .pq)
        elif any(filename.endswith(ext) for ext in [".parquet", ".pq"]):
            try:
                df = pd.read_parquet(BytesIO(file_content))
            except Exception:
                pass

        # Strategy 3: JSON format (.json or json-like content)
        elif filename.endswith(".json"):
            df = _try_parse_json(file_content)

        # Strategy 4: Delimited text (CSV, TSV, TXT, DAT, DATA, etc.)
        if df is None:
            # Try Python CSV engine with auto-sniffer
            try:
                df = pd.read_csv(BytesIO(file_content), sep=None, engine="python")
            except Exception:
                pass

        # Strategy 5: Standard comma separated with encoding fallbacks
        if df is None or (df is not None and len(df.columns) <= 1 and "," in file_content[:2048].decode("utf-8", errors="ignore")):
            for enc in ["utf-8", "utf-8-sig", "latin1", "cp1252"]:
                try:
                    candidate = pd.read_csv(BytesIO(file_content), sep=",", encoding=enc)
                    if candidate is not None and len(candidate.columns) > 1:
                        df = candidate
                        break
                except Exception:
                    continue

        # Strategy 6: Tab separated (TSV)
        if df is None or (df is not None and len(df.columns) <= 1 and "\t" in file_content[:2048].decode("utf-8", errors="ignore")):
            try:
                candidate = pd.read_csv(BytesIO(file_content), sep="\t")
                if candidate is not None and len(candidate.columns) > 1:
                    df = candidate
            except Exception:
                pass

        # Strategy 7: Semicolon separated
        if df is None or (df is not None and len(df.columns) <= 1 and ";" in file_content[:2048].decode("utf-8", errors="ignore")):
            try:
                candidate = pd.read_csv(BytesIO(file_content), sep=";")
                if candidate is not None and len(candidate.columns) > 1:
                    df = candidate
            except Exception:
                pass

        # Strategy 8: Pipe separated (|)
        if df is None or (df is not None and len(df.columns) <= 1 and "|" in file_content[:2048].decode("utf-8", errors="ignore")):
            try:
                candidate = pd.read_csv(BytesIO(file_content), sep="|")
                if candidate is not None and len(candidate.columns) > 1:
                    df = candidate
            except Exception:
                pass

        # Strategy 9: Fallback Excel attempt (in case file has unexpected extension)
        if df is None:
            try:
                df = pd.read_excel(BytesIO(file_content))
            except Exception:
                pass

        # Strategy 10: Fallback JSON attempt (in case file has unexpected extension)
        if df is None:
            df = _try_parse_json(file_content)

        # Strategy 11: Final generic CSV read fallback
        if df is None:
            try:
                df = pd.read_csv(BytesIO(file_content), encoding="latin1")
            except Exception:
                pass

        if df is None or df.empty:
            raise HTTPException(
                status_code=400,
                detail=f"Unable to parse dataset from '{file.filename}'. Please verify the file contains valid tabular data."
            )

        # Clean column names
        df.columns = [
            str(column).strip()
            for column in df.columns
        ]

        return df

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to read dataset: {str(e)}"
        )


def _try_parse_json(file_content: bytes) -> Optional[pd.DataFrame]:
    import json
    try:
        return pd.read_json(BytesIO(file_content))
    except Exception:
        pass
    try:
        return pd.read_json(BytesIO(file_content), lines=True)
    except Exception:
        pass
    try:
        raw = json.loads(file_content.decode("utf-8", errors="ignore"))
        if isinstance(raw, list):
            return pd.DataFrame(raw)
        elif isinstance(raw, dict):
            for key in ["data", "customers", "records", "rows", "items", "results"]:
                if key in raw and isinstance(raw[key], list):
                    return pd.DataFrame(raw[key])
            return pd.DataFrame([raw])
    except Exception:
        pass
    return None


# =========================================================
# DETECT IMPORTANT COLUMNS
# =========================================================

def detect_columns(
    df: pd.DataFrame
):

    detected_columns = {

        "customer_id": None,

        "date": None,

        "amount": None,

        "quantity": None
    }

    # -----------------------------------------------------
    # Keywords
    # -----------------------------------------------------

    customer_keywords = [

        "customer_id",
        "customerid",
        "customer id",
        "customer",

        "client_id",
        "clientid",
        "client id",
        "client",

        "user_id",
        "userid",
        "user id",
        "user",

        "customer_number",
        "customer_no",

        "client_code",

        "account_id",
        "account_number"
    ]

    date_keywords = [

        "date",
        "datetime",
        "timestamp",

        "order_date",
        "order date",

        "purchase_date",
        "purchase date",

        "transaction_date",
        "transaction date",

        "invoice_date",
        "invoice date",

        "created_at",
        "created at",

        "order_time",
        "transaction_time"
    ]

    amount_keywords = [

        "amount",
        "revenue",

        "sales",
        "sale",

        "price",

        "total",

        "spend",
        "spent",

        "value",

        "income",

        "profit",

        "net_value",
        "net value",

        "total_amount",
        "total amount",

        "order_value",
        "order value"
    ]

    quantity_keywords = [

        "quantity",
        "qty",

        "units",
        "unit",

        "count",

        "items",
        "item_count"
    ]

    # -----------------------------------------------------
    # Normalize helper
    # -----------------------------------------------------

    def normalize(
        column
    ):

        return (
            str(column)
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

    # -----------------------------------------------------
    # Detect columns
    # -----------------------------------------------------

    for column in df.columns:

        normalized_name = normalize(
            column
        )

        # -----------------------------------------------
        # Customer ID
        # -----------------------------------------------

        if detected_columns[
            "customer_id"
        ] is None:

            for keyword in customer_keywords:

                normalized_keyword = normalize(
                    keyword
                )

                if (
                    normalized_name
                    == normalized_keyword
                ):

                    detected_columns[
                        "customer_id"
                    ] = str(column)

                    break

        # -----------------------------------------------
        # Date
        # -----------------------------------------------

        if detected_columns[
            "date"
        ] is None:

            for keyword in date_keywords:

                normalized_keyword = normalize(
                    keyword
                )

                if (
                    normalized_name
                    == normalized_keyword
                ):

                    detected_columns[
                        "date"
                    ] = str(column)

                    break

        # -----------------------------------------------
        # Amount
        # -----------------------------------------------

        if detected_columns[
            "amount"
        ] is None:

            for keyword in amount_keywords:

                normalized_keyword = normalize(
                    keyword
                )

                if (
                    normalized_name
                    == normalized_keyword
                ):

                    detected_columns[
                        "amount"
                    ] = str(column)

                    break

        # -----------------------------------------------
        # Quantity
        # -----------------------------------------------

        if detected_columns[
            "quantity"
        ] is None:

            for keyword in quantity_keywords:

                normalized_keyword = normalize(
                    keyword
                )

                if (
                    normalized_name
                    == normalized_keyword
                ):

                    detected_columns[
                        "quantity"
                    ] = str(column)

                    break

    # =====================================================
    # FALLBACK CUSTOMER ID
    # =====================================================

    if detected_columns[
        "customer_id"
    ] is None:

        for column in df.columns:

            name = normalize(
                column
            )

            if (
                "customer" in name
                or "client" in name
                or "user_id" in name
                or name == "user"
            ):

                detected_columns[
                    "customer_id"
                ] = str(column)

                break

    # =====================================================
    # FALLBACK DATE
    # =====================================================

    if detected_columns[
        "date"
    ] is None:

        for column in df.columns:

            name = normalize(
                column
            )

            if (
                "date" in name
                or "time" in name
                or "timestamp" in name
            ):

                detected_columns[
                    "date"
                ] = str(column)

                break

    # =====================================================
    # FALLBACK AMOUNT
    # =====================================================

    if detected_columns[
        "amount"
    ] is None:

        numeric_columns = (
            df.select_dtypes(
                include="number"
            ).columns
        )

        for column in numeric_columns:

            if str(column) != (
                detected_columns[
                    "customer_id"
                ]
            ):

                detected_columns[
                    "amount"
                ] = str(column)

                break

    # =====================================================
    # FALLBACK QUANTITY
    # =====================================================

    if detected_columns[
        "quantity"
    ] is None:

        numeric_columns = (
            df.select_dtypes(
                include="number"
            ).columns
        )

        for column in numeric_columns:

            if (
                str(column)
                != detected_columns["customer_id"]
                and
                str(column)
                != detected_columns["amount"]
            ):

                detected_columns[
                    "quantity"
                ] = str(column)

                break

    return detected_columns


# =========================================================
# NORMALIZE RFM OUTPUT
# =========================================================

def normalize_rfm_columns(
    rfm: pd.DataFrame,
    customer_id_column: str
):

    data = rfm.copy()

    # -----------------------------------------------------
    # Customer ID
    # -----------------------------------------------------

    if "CustomerID" not in data.columns:

        possible_customer_columns = [

            customer_id_column,

            "customer_id",

            "Customer_ID",

            "Client_ID",

            "ClientID",

            "client_id",

            "customerid"
        ]

        for column in possible_customer_columns:

            if column in data.columns:

                data = data.rename(
                    columns={
                        column: "CustomerID"
                    }
                )

                break

    # -----------------------------------------------------
    # RFM columns
    # -----------------------------------------------------

    rename_map = {}

    for column in data.columns:

        normalized = (
            str(column)
            .strip()
            .lower()
            .replace(" ", "_")
        )

        if normalized == "recency":

            rename_map[column] = "Recency"

        elif normalized == "frequency":

            rename_map[column] = "Frequency"

        elif normalized in [
            "monetary",
            "monetary_value",
            "monetaryvalue"
        ]:

            rename_map[column] = "Monetary"

        elif normalized in [
            "rfm_score",
            "rfmscore"
        ]:

            rename_map[column] = "RFM_Score"

        elif normalized in [
            "rfm_total",
            "rfmtotal"
        ]:

            rename_map[column] = "RFM_Total"

    if rename_map:

        data = data.rename(
            columns=rename_map
        )

    # -----------------------------------------------------
    # Validate
    # -----------------------------------------------------

    required_columns = [

        "CustomerID",

        "Recency",

        "Frequency",

        "Monetary"
    ]

    missing = [

        column

        for column in required_columns

        if column not in data.columns
    ]

    if missing:

        raise ValueError(
            "RFM output is missing required "
            f"columns: {missing}. "
            f"Available columns: "
            f"{list(data.columns)}"
        )

    # -----------------------------------------------------
    # Numeric conversion
    # -----------------------------------------------------

    data["Recency"] = pd.to_numeric(
        data["Recency"],
        errors="coerce"
    ).fillna(0)

    data["Frequency"] = pd.to_numeric(
        data["Frequency"],
        errors="coerce"
    ).fillna(0)

    data["Monetary"] = pd.to_numeric(
        data["Monetary"],
        errors="coerce"
    ).fillna(0)

    return data


# =========================================================
# MARKETING STRATEGY
# =========================================================

def marketing_strategy(
    segment
):

    strategies = {

        "Champions":
            "Reward and retain high-value customers",

        "Loyal Customers":
            "Build loyalty with exclusive offers",

        "Potential Loyalists":
            "Encourage repeat purchases",

        "Big Spenders":
            "Promote premium products and services",

        "New Customers":
            "Create onboarding and welcome campaigns",

        "At Risk":
            "Launch win-back campaigns",

        "Lost Customers":
            "Reactivate inactive customers",

        "Other Customers":
            "Use personalized engagement campaigns"
    }

    return strategies.get(
        segment,
        "Use personalized engagement campaigns"
    )


# =========================================================
# RECOMMENDED ACTION
# =========================================================

def recommended_action(
    segment
):

    actions = {

        "Champions":
            "Offer VIP rewards and early access",

        "Loyal Customers":
            "Provide loyalty discounts",

        "Potential Loyalists":
            "Send personalized product recommendations",

        "New Customers":
            "Send welcome offers",

        "At Risk":
            "Send win-back offers",

        "Lost Customers":
            "Launch reactivation campaign",

        "Big Spenders":
            "Promote premium and high-value products",

        "Other Customers":
            "Send personalized promotions"
    }

    return actions.get(
        segment,
        "Send personalized promotions"
    )


# =========================================================
# CAMPAIGN
# =========================================================

def campaign_name(
    segment
):

    campaigns = {

        "Champions":
            "VIP Rewards Campaign",

        "Loyal Customers":
            "Loyalty Program Campaign",

        "Potential Loyalists":
            "Repeat Purchase Campaign",

        "Big Spenders":
            "Premium Customer Campaign",

        "New Customers":
            "Welcome Campaign",

        "At Risk":
            "Win-Back Campaign",

        "Lost Customers":
            "Reactivation Campaign",

        "Other Customers":
            "Personalized Engagement Campaign"
    }

    return campaigns.get(
        segment,
        "Personalized Engagement Campaign"
    )


# =========================================================
# PRIORITY
# =========================================================

def priority_level(
    segment
):

    priorities = {

        "Champions":
            "High",

        "Loyal Customers":
            "High",

        "Potential Loyalists":
            "Medium",

        "Big Spenders":
            "High",

        "New Customers":
            "Medium",

        "At Risk":
            "High",

        "Lost Customers":
            "Medium",

        "Other Customers":
            "Low"
    }

    return priorities.get(
        segment,
        "Low"
    )


# =========================================================
# PREPARE MARKETING DATA
# =========================================================

def prepare_marketing_data(
    segmented_data: pd.DataFrame
):

    data = segmented_data.copy()

    # -----------------------------------------------------
    # Ensure Segment exists
    # -----------------------------------------------------

    if "Segment" not in data.columns:

        raise ValueError(
            "Segment column is missing."
        )

    # -----------------------------------------------------
    # Marketing Strategy
    # -----------------------------------------------------

    data["Marketing_Strategy"] = (
        data["Segment"]
        .apply(
            marketing_strategy
        )
    )

    # -----------------------------------------------------
    # Recommended Action
    # -----------------------------------------------------

    data["Recommended_Action"] = (
        data["Segment"]
        .apply(
            recommended_action
        )
    )

    # -----------------------------------------------------
    # Campaign
    # -----------------------------------------------------

    data["Campaign"] = (
        data["Segment"]
        .apply(
            campaign_name
        )
    )

    # -----------------------------------------------------
    # Priority
    # -----------------------------------------------------

    data["Priority"] = (
        data["Segment"]
        .apply(
            priority_level
        )
    )

    return data


# =========================================================
# SAVE ACTIVE DATASET
# =========================================================

def save_active_customer_dataset(
    segmented_data: pd.DataFrame
):

    data = prepare_marketing_data(
        segmented_data
    )

    required_columns = [

        "CustomerID",

        "Segment",

        "Recency",

        "Frequency",

        "Monetary",

        "RFM_Score",

        "RFM_Total",

        "Marketing_Strategy",

        "Recommended_Action",

        "Campaign",

        "Priority"
    ]

    available_columns = [

        column

        for column in required_columns

        if column in data.columns
    ]

    data = data[
        available_columns
    ]

    output_path = Path(
        "data/processed/"
        "customer_recommendations.csv"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    data.to_csv(
        output_path,
        index=False
    )

    # Reload customer service
    reload_customer_data()

    return data


# =========================================================
# SAVE DATA TO MYSQL
# =========================================================

def save_dataset_to_database(
    filename: str,
    segmented_data: pd.DataFrame,
    clustering_method: str = "K-Means",
    clustering_metadata: dict | None = None
):

    db: Session = SessionLocal()

    try:

        data = prepare_marketing_data(
            segmented_data
        )

        clustering_metadata = (
            clustering_metadata
            or {}
        )

        # =================================================
        # DATASET RUN
        # =================================================

        dataset_run = (
            CustomerRepository.save_dataset_run(

                db=db,

                filename=filename,

                row_count=len(data),

                status="processing",

                best_method=clustering_method,

                comparison=clustering_metadata
            )
        )

        # =================================================
        # SAVE CUSTOMERS
        # =================================================

        for _, row in data.iterrows():

            customer_id = str(
                row["CustomerID"]
            )

            # -------------------------------------------------
            # RFM SCORE
            # -------------------------------------------------

            rfm_score = row.get(
                "RFM_Score"
            )

            if pd.isna(rfm_score):

                rfm_score = None

            else:

                try:

                    rfm_score = int(
                        float(rfm_score)
                    )

                except Exception:

                    pass

            # -------------------------------------------------
            # CLUSTER
            # -------------------------------------------------

            cluster = row.get(
                "Cluster"
            )

            if pd.isna(cluster):

                cluster = None

            else:

                try:

                    cluster = int(
                        float(cluster)
                    )

                except Exception:

                    cluster = None

            # -------------------------------------------------
            # SILHOUETTE
            # -------------------------------------------------

            silhouette_score = row.get(
                "Silhouette_Score"
            )

            if pd.isna(
                silhouette_score
            ):

                silhouette_score = None

            else:

                try:

                    silhouette_score = float(
                        silhouette_score
                    )

                except Exception:

                    silhouette_score = None

            # -------------------------------------------------
            # PCA
            # -------------------------------------------------

            pca1 = row.get(
                "PCA1"
            )

            pca2 = row.get(
                "PCA2"
            )

            try:

                pca1 = (
                    None
                    if pd.isna(pca1)
                    else float(pca1)
                )

            except Exception:

                pca1 = None

            try:

                pca2 = (
                    None
                    if pd.isna(pca2)
                    else float(pca2)
                )

            except Exception:

                pca2 = None

            # =================================================
            # CUSTOMER
            # =================================================

            customer = (
                CustomerRepository.upsert_customer(

                    db=db,

                    customer_id=customer_id,

                    recency=float(
                        row.get(
                            "Recency",
                            0
                        ) or 0
                    ),

                    frequency=float(
                        row.get(
                            "Frequency",
                            0
                        ) or 0
                    ),

                    monetary=float(
                        row.get(
                            "Monetary",
                            0
                        ) or 0
                    ),

                    rfm_score=rfm_score,

                    segment=str(
                        row.get(
                            "Segment",
                            "Other Customers"
                        )
                    ),

                    priority=str(
                        row.get(
                            "Priority",
                            "Low"
                        )
                    ),

                    campaign=str(
                        row.get(
                            "Campaign",
                            ""
                        )
                    ),

                    action=str(
                        row.get(
                            "Recommended_Action",
                            ""
                        )
                    ),

                    cluster=cluster,

                    clustering_method=clustering_method,

                    silhouette_score=silhouette_score,

                    pca1=pca1,

                    pca2=pca2
                )
            )

            # =================================================
            # RFM RECORD
            # =================================================

            CustomerRepository.save_rfm_analysis(

                db=db,

                customer=customer,

                recency=float(
                    row.get(
                        "Recency",
                        0
                    ) or 0
                ),

                frequency=float(
                    row.get(
                        "Frequency",
                        0
                    ) or 0
                ),

                monetary=float(
                    row.get(
                        "Monetary",
                        0
                    ) or 0
                ),

                rfm_score=(
                    str(
                        row.get(
                            "RFM_Score"
                        )
                    )
                    if not pd.isna(
                        row.get(
                            "RFM_Score",
                            None
                        )
                    )
                    else None
                )
            )

            # =================================================
            # SEGMENTATION RECORD
            # =================================================

            CustomerRepository.save_segmentation(

                db=db,

                customer=customer,

                segment=str(
                    row.get(
                        "Segment",
                        "Other Customers"
                    )
                ),

                priority=str(
                    row.get(
                        "Priority",
                        "Low"
                    )
                ),

                campaign=str(
                    row.get(
                        "Campaign",
                        ""
                    )
                ),

                marketing_strategy=str(
                    row.get(
                        "Marketing_Strategy",
                        ""
                    )
                ),

                recommended_action=str(
                    row.get(
                        "Recommended_Action",
                        ""
                    )
                )
            )

        # =================================================
        # SEGMENT SNAPSHOTS
        # =================================================

        summary = (
            data
            .groupby("Segment")
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

        for _, row in summary.iterrows():

            CustomerRepository.save_segment_snapshot(

                db=db,

                segment=str(
                    row["Segment"]
                ),

                customer_count=int(
                    row["customer_count"]
                ),

                avg_recency=float(
                    row["avg_recency"] or 0
                ),

                avg_frequency=float(
                    row["avg_frequency"] or 0
                ),

                avg_monetary=float(
                    row["avg_monetary"] or 0
                )
            )

        # =================================================
        # COMPLETE DATASET RUN
        # =================================================

        dataset_run.status = "completed"

        db.commit()

        return {

            "dataset_run_id":
                dataset_run.id,

            "customers_saved":
                len(data),

            "segments_saved":
                len(summary),

            "clustering_method":
                clustering_method,

            "status":
                "completed"
        }

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# =========================================================
# POST /dataset/analyze
# =========================================================

@router.post("/analyze")
async def analyze_dataset(
    file: UploadFile = File(...)
):

    df = await read_dataset(
        file
    )

    detected_columns = (
        detect_columns(df)
    )

    columns = []

    for column in df.columns:

        columns.append({

            "name":
                str(column),

            "data_type":
                str(
                    df[column].dtype
                ),

            "missing_values":
                int(
                    df[column].isna().sum()
                ),

            "unique_values":
                int(
                    df[column].nunique()
                )
        })

    return {

        "filename":
            file.filename,

        "rows":
            int(len(df)),

        "columns_count":
            int(len(df.columns)),

        "detected_columns":
            detected_columns,

        "columns":
            columns
    }


# =========================================================
# POST /dataset/rfm
# =========================================================

@router.post("/rfm")
async def calculate_dataset_rfm(
    file: UploadFile = File(...)
):

    df = await read_dataset(
        file
    )

    detected_columns = (
        detect_columns(df)
    )

    customer_id_column = (
        detected_columns[
            "customer_id"
        ]
    )

    date_column = (
        detected_columns[
            "date"
        ]
    )

    amount_column = (
        detected_columns[
            "amount"
        ]
    )

    missing = []

    if customer_id_column is None:

        missing.append(
            "Customer ID"
        )

    if date_column is None:

        missing.append(
            "Date"
        )

    if amount_column is None:

        missing.append(
            "Amount/Revenue"
        )

    if missing:

        raise HTTPException(

            status_code=400,

            detail={

                "message":
                    "Unable to detect required columns.",

                "missing_columns":
                    missing,

                "available_columns": [

                    str(column)

                    for column in df.columns
                ]
            }
        )

    try:

        rfm = calculate_rfm(

            df,

            customer_id_column,

            date_column,

            amount_column
        )

        rfm = normalize_rfm_columns(
            rfm,
            customer_id_column
        )

        return {

            "filename":
                file.filename,

            "detected_columns": {

                "customer_id":
                    customer_id_column,

                "date":
                    date_column,

                "amount":
                    amount_column
            },

            "customer_count":
                int(len(rfm)),

            "rfm":
                rfm.to_dict(
                    orient="records"
                )
        }

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=
                f"Unable to calculate RFM: {str(e)}"
        )


# =========================================================
# POST /dataset/segment
# =========================================================

@router.post("/segment")
async def segment_dataset(
    file: UploadFile = File(...)
):

    # =====================================================
    # READ DATASET
    # =====================================================

    df = await read_dataset(
        file
    )

    # =====================================================
    # DETECT COLUMNS
    # =====================================================

    detected_columns = (
        detect_columns(df)
    )

    customer_id_column = (
        detected_columns[
            "customer_id"
        ]
    )

    date_column = (
        detected_columns[
            "date"
        ]
    )

    amount_column = (
        detected_columns[
            "amount"
        ]
    )

    # =====================================================
    # VALIDATE
    # =====================================================

    missing = []

    if customer_id_column is None:

        missing.append(
            "Customer ID"
        )

    if date_column is None:

        missing.append(
            "Date"
        )

    if amount_column is None:

        missing.append(
            "Amount/Revenue"
        )

    if missing:

        raise HTTPException(

            status_code=400,

            detail={

                "message":
                    "Unable to detect required columns.",

                "missing_columns":
                    missing,

                "available_columns": [

                    str(column)

                    for column in df.columns
                ]
            }
        )

    try:

        # =================================================
        # STEP 1 — RFM ANALYSIS
        # =================================================

        rfm = calculate_rfm(

            df,

            customer_id_column,

            date_column,

            amount_column
        )

        # -------------------------------------------------
        # IMPORTANT:
        # Normalize RFM output before clustering
        # -------------------------------------------------

        rfm = normalize_rfm_columns(
            rfm,
            customer_id_column
        )

        print(
            f"✅ RFM analysis completed for "
            f"{len(rfm)} customers."
        )

        # =================================================
        # STEP 2 — ADVANCED CLUSTERING
        # =================================================

        clustering_result = (
            cluster_customers(
                rfm
            )
        )

        # -------------------------------------------------
        # CURRENT clustering_service RETURNS:
        #
        # data, metadata
        # -------------------------------------------------

        if not isinstance(
            clustering_result,
            tuple
        ):

            raise ValueError(
                "Clustering service must return "
                "(data, metadata)."
            )

        if len(
            clustering_result
        ) != 2:

            raise ValueError(
                "Clustering service returned an "
                "unexpected result."
            )

        clustered_data, clustering_metadata = (
            clustering_result
        )

        if not isinstance(
            clustered_data,
            pd.DataFrame
        ):

            raise ValueError(
                "Clustering service did not "
                "return a DataFrame."
            )

        print(
            "✅ Advanced clustering completed."
        )

        # =================================================
        # CLUSTERING METADATA
        # =================================================

        clustering_method = (
            clustering_metadata.get(
                "best_method",
                "K-Means"
            )
        )

        # =================================================
        # ADD CLUSTER METADATA TO DATA
        # =================================================

        if (
            "best_silhouette_score"
            in clustering_metadata
        ):

            clustered_data[
                "Silhouette_Score"
            ] = clustering_metadata[
                "best_silhouette_score"
            ]

        # -------------------------------------------------
        # PCA values
        # -------------------------------------------------

        # Your clustering service may already provide
        # PCA1 / PCA2. We keep them if present.

        # =================================================
        # STEP 3 — CUSTOMER SEGMENTATION
        # =================================================

        segmented_data = (
            segment_customers(
                clustered_data
            )
        )

        print(
            "✅ Customer segmentation completed."
        )

        # =================================================
        # STEP 4 — MARKETING DATA
        # =================================================

        active_data = (
            save_active_customer_dataset(
                segmented_data
            )
        )

        print(
            "✅ Marketing data prepared."
        )

        # =================================================
        # STEP 5 — SAVE TO MYSQL
        # =================================================

        database_result = (
            save_dataset_to_database(

                filename=file.filename,

                segmented_data=segmented_data,

                clustering_method=
                    clustering_method,

                clustering_metadata=
                    clustering_metadata
            )
        )

        print(
            "✅ Dataset saved to MySQL."
        )

        # =================================================
        # STEP 6 — SEGMENT SUMMARY
        # =================================================

        segment_summary = (

            segmented_data

            .groupby("Segment")

            .agg(

                customer_count=(
                    "CustomerID",
                    "count"
                ),

                total_revenue=(
                    "Monetary",
                    "sum"
                ),

                average_recency=(
                    "Recency",
                    "mean"
                ),

                average_frequency=(
                    "Frequency",
                    "mean"
                ),

                average_monetary=(
                    "Monetary",
                    "mean"
                )
            )

            .reset_index()
        )

        # =================================================
        # ROUND VALUES
        # =================================================

        segment_summary[
            "average_recency"
        ] = (
            segment_summary[
                "average_recency"
            ].round(2)
        )

        segment_summary[
            "average_frequency"
        ] = (
            segment_summary[
                "average_frequency"
            ].round(2)
        )

        segment_summary[
            "average_monetary"
        ] = (
            segment_summary[
                "average_monetary"
            ].round(2)
        )

        segment_summary[
            "total_revenue"
        ] = (
            segment_summary[
                "total_revenue"
            ].round(2)
        )

        # =================================================
        # RESPONSE
        # =================================================

        return {

            "success":
                True,

            "message":
                "Dataset analyzed, clustered, segmented "
                "and saved successfully.",

            "filename":
                file.filename,

            "detected_columns": {

                "customer_id":
                    customer_id_column,

                "date":
                    date_column,

                "amount":
                    amount_column
            },

            "customer_count":
                int(
                    len(segmented_data)
                ),

            "segment_count":
                int(
                    segmented_data[
                        "Segment"
                    ].nunique()
                ),

            "clustering": {

                "best_method":
                    clustering_method,

                "best_clusters":
                    clustering_metadata.get(
                        "best_clusters"
                    ),

                "best_silhouette_score":
                    clustering_metadata.get(
                        "best_silhouette_score"
                    ),

                "comparison":
                    clustering_metadata.get(
                        "comparison",
                        {}
                    ),

                "pca_explained_variance":
                    clustering_metadata.get(
                        "pca_explained_variance",
                        []
                    )
            },

            "database":
                database_result,

            "segments":
                segment_summary.to_dict(
                    orient="records"
                ),

            "customers":
                active_data.to_dict(
                    orient="records"
                )
        }

    except ValueError as e:

        raise HTTPException(

            status_code=400,

            detail=str(e)
        )

    except Exception as e:

        print(
            "❌ Dataset segmentation error:",
            str(e)
        )

        raise HTTPException(

            status_code=500,

            detail=
                f"Unable to segment dataset: {str(e)}"
        )


# =========================================================
# DOWNLOAD SAMPLE INDUSTRIAL DATASETS
# =========================================================

SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "samples"


@router.get(
    "/sample/industrial-transactions",
    summary="Download industrial retail transactions sample dataset (CSV)",
)
def download_industrial_transactions_sample():
    """
    Download real-world industrial retail dataset (10,000 transactions across 2,693 customers)
    compatible with the Customer AI segmentation engine.
    """
    file_path = SAMPLES_DIR / "industrial_online_retail_sample.csv"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Sample dataset file not found.")
    return FileResponse(
        path=str(file_path),
        filename="industrial_online_retail_sample.csv",
        media_type="text/csv",
    )


@router.get(
    "/sample/industrial-transactions-excel",
    summary="Download industrial retail transactions sample dataset (Excel .xlsx)",
)
def download_industrial_transactions_excel():
    """
    Download real-world industrial retail dataset as Excel workbook (.xlsx).
    """
    file_path = SAMPLES_DIR / "industrial_online_retail_sample.xlsx"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Sample Excel dataset not found.")
    return FileResponse(
        path=str(file_path),
        filename="industrial_online_retail_sample.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get(
    "/sample/customer-rfm",
    summary="Download industrial customer RFM benchmark dataset (CSV)",
)
def download_industrial_customer_rfm():
    """
    Download 4,338 customer-level RFM metrics dataset.
    """
    file_path = SAMPLES_DIR / "industrial_customer_rfm_benchmark.csv"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Customer RFM dataset not found.")
    return FileResponse(
        path=str(file_path),
        filename="industrial_customer_rfm_benchmark.csv",
        media_type="text/csv",
    )


@router.get(
    "/sample/full-retail",
    summary="Download complete UCI online retail dataset (392k transactions CSV)",
)
def download_full_retail_dataset():
    """
    Download full 392,692-transaction industrial dataset.
    """
    file_path = SAMPLES_DIR / "online_retail_full_transactions.csv"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Full dataset file not found.")
    return FileResponse(
        path=str(file_path),
        filename="online_retail_full_transactions.csv",
        media_type="text/csv",
    )