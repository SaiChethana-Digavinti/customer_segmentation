from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from app.database.models import (
    Customer,
    RFMAnalysis,
    CustomerSegmentation,
    AIRecommendation,
    DatasetRun,
    SegmentSnapshot,
)


# ============================================================
# CUSTOMER REPOSITORY
# ============================================================

class CustomerRepository:

    # ========================================================
    # CUSTOMER
    # ========================================================

    @staticmethod
    def get_customer(
        db: Session,
        customer_id: str
    ) -> Optional[Customer]:

        return (
            db.query(Customer)
            .filter(
                Customer.customer_id == str(customer_id)
            )
            .first()
        )

    # ========================================================
    # CREATE / UPDATE CUSTOMER
    # ========================================================

    @staticmethod
    def upsert_customer(
        db: Session,
        customer_id: str,
        recency: float,
        frequency: float,
        monetary: float,
        rfm_score: Optional[int] = None,
        segment: Optional[str] = None,
        priority: Optional[str] = None,
        campaign: Optional[str] = None,
        action: Optional[str] = None,
        cluster: Optional[int] = None,
        clustering_method: Optional[str] = None,
        silhouette_score: Optional[float] = None,
        pca1: Optional[float] = None,
        pca2: Optional[float] = None,
    ) -> Customer:

        customer = (
            db.query(Customer)
            .filter(
                Customer.customer_id == str(customer_id)
            )
            .first()
        )

        # ----------------------------------------------------
        # CREATE
        # ----------------------------------------------------

        if customer is None:

            customer = Customer(
                customer_id=str(customer_id)
            )

            db.add(customer)

        # ----------------------------------------------------
        # UPDATE
        # ----------------------------------------------------

        customer.recency = float(recency or 0)
        customer.frequency = float(frequency or 0)
        customer.monetary = float(monetary or 0)

        customer.rfm_score = rfm_score
        customer.segment = segment
        customer.priority = priority
        customer.campaign = campaign
        customer.action = action

        customer.cluster = cluster
        customer.clustering_method = clustering_method
        customer.silhouette_score = silhouette_score

        customer.pca1 = pca1
        customer.pca2 = pca2

        db.flush()

        return customer

    # ========================================================
    # SAVE RFM ANALYSIS
    # ========================================================

    @staticmethod
    def save_rfm_analysis(
        db: Session,
        customer: Customer,
        recency: float,
        frequency: float,
        monetary: float,
        rfm_score: Optional[str] = None,
    ) -> RFMAnalysis:

        rfm = RFMAnalysis(
            customer_id=customer.id,
            recency=float(recency or 0),
            frequency=float(frequency or 0),
            monetary=float(monetary or 0),
            rfm_score=rfm_score,
        )

        db.add(rfm)

        db.flush()

        return rfm

    # ========================================================
    # SAVE SEGMENTATION
    # ========================================================

    @staticmethod
    def save_segmentation(
        db: Session,
        customer: Customer,
        segment: str,
        priority: Optional[str] = None,
        campaign: Optional[str] = None,
        marketing_strategy: Optional[str] = None,
        recommended_action: Optional[str] = None,
    ) -> CustomerSegmentation:

        segmentation = CustomerSegmentation(
            customer_id=customer.id,
            segment=segment,
            priority=priority,
            campaign=campaign,
            marketing_strategy=marketing_strategy,
            recommended_action=recommended_action,
        )

        db.add(segmentation)

        db.flush()

        return segmentation

    # ========================================================
    # SAVE AI RECOMMENDATION
    # ========================================================

    @staticmethod
    def save_ai_recommendation(
        db: Session,
        customer: Customer,
        message: Optional[str] = None,
        marketing_strategy: Optional[str] = None,
        recommended_action: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> AIRecommendation:

        recommendation = AIRecommendation(
            customer_id=customer.id,
            message=message,
            marketing_strategy=marketing_strategy,
            recommended_action=recommended_action,
            model_name=model_name,
        )

        db.add(recommendation)

        db.flush()

        return recommendation

    # ========================================================
    # SAVE DATASET RUN
    # ========================================================

    @staticmethod
    def save_dataset_run(
        db: Session,
        filename: str,
        row_count: int,
        status: str,
        best_method: Optional[str] = None,
        comparison: Optional[Dict[str, Any]] = None,
    ) -> DatasetRun:

        dataset_run = DatasetRun(
            filename=filename,
            row_count=int(row_count),
            status=status,
            best_method=best_method,
            comparison=comparison,
        )

        db.add(dataset_run)

        db.flush()

        return dataset_run

    # ========================================================
    # SAVE SEGMENT SNAPSHOT
    # ========================================================

    @staticmethod
    def save_segment_snapshot(
        db: Session,
        segment: str,
        customer_count: int,
        avg_recency: float,
        avg_frequency: float,
        avg_monetary: float,
    ) -> SegmentSnapshot:

        snapshot = SegmentSnapshot(
            segment=segment,
            customer_count=int(customer_count),
            avg_recency=float(avg_recency or 0),
            avg_frequency=float(avg_frequency or 0),
            avg_monetary=float(avg_monetary or 0),
        )

        db.add(snapshot)

        db.flush()

        return snapshot

    # ========================================================
    # GET ALL CUSTOMERS
    # ========================================================

    @staticmethod
    def get_all_customers(
        db: Session
    ) -> List[Customer]:

        return (
            db.query(Customer)
            .order_by(Customer.id.asc())
            .all()
        )

    # ========================================================
    # GET CUSTOMERS BY SEGMENT
    # ========================================================

    @staticmethod
    def get_customers_by_segment(
        db: Session,
        segment: str
    ) -> List[Customer]:

        return (
            db.query(Customer)
            .filter(
                Customer.segment == segment
            )
            .order_by(
                Customer.monetary.desc()
            )
            .all()
        )

    # ========================================================
    # SEARCH CUSTOMERS
    # ========================================================

    @staticmethod
    def search_customers(
        db: Session,
        query: str
    ) -> List[Customer]:

        search_value = f"%{query}%"

        return (
            db.query(Customer)
            .filter(
                (
                    Customer.customer_id.like(
                        search_value
                    )
                )
                |
                (
                    Customer.segment.like(
                        search_value
                    )
                )
                |
                (
                    Customer.campaign.like(
                        search_value
                    )
                )
                |
                (
                    Customer.priority.like(
                        search_value
                    )
                )
            )
            .order_by(
                Customer.monetary.desc()
            )
            .all()
        )

    # ========================================================
    # GET CUSTOMER COUNT
    # ========================================================

    @staticmethod
    def get_customer_count(
        db: Session
    ) -> int:

        return (
            db.query(Customer)
            .count()
        )