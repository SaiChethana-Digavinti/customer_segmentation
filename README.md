# Customer Segmentation & AI Marketing Recommendation

An enterprise-grade customer analytics and AI marketing recommendation platform powered by **FastAPI**, **MySQL**, **Scikit-learn**, **Pandas**, and **Google Gemini AI**.

---

##  Key Features

1. **Automated RFM Analysis**: Calculates Recency, Frequency, and Monetary metrics across transactional datasets.
2. **Unsupervised Machine Learning**: K-Means clustering with optimal cluster determination via Silhouette and Elbow evaluation ($K=4$).
3. **Behavioral Cohort Tagging**:
   - **Champions**: Highest spenders, high engagement (VIP marketing).
   - **Loyal Customers**: Consistent buyers, cross-sell and up-sell candidates.
   - **At Risk**: High-spend or previously active buyers with lapsed recency.
   - **Lost Customers**: Lapsed low-frequency customers for re-activation.
4. **AI-Driven Campaign Strategy**: Dynamic, personalized marketing recommendations generated via Google Gemini AI.
5. **Interactive Analytics Dashboard**:
   - Visual segment revenue distributions and customer metrics.
   - Real-time customer search, segment filters, and priority sorting.
   - Dynamic dataset upload pipeline (supporting CSV, Excel, JSON, TSV, Parquet).
   - Instant programmatic and UI-based report exports.
6. **Role-Based Authentication**: Secure JWT-based access control with Argon2id password hashing (Admin & Analyst roles).

---

##  Quick Start

### 1. Environment Setup
```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies (if needed)
pip install -r requirements.txt
```

### 2. Run Application
```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Open your browser at: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

### 3. Default Credentials
| Username | Password | Role | Permissions |
| :--- | :--- | :--- | :--- |
| `admin` | `admin123` | Administrator | Full Access + Admin Center |
| `analyst` | `user123` | Data Analyst | Analytics, Customers, Segmentation |

---

## Downloadable Reports

Reports are stored in the [`reports/`](./reports/) directory:

- **[`customer_segmentation_report.csv`](./reports/customer_segmentation_report.csv)**: Complete customer level report with RFM scores, segment tags, priorities, campaigns, and recommended actions.
- **[`customer_segments_summary_report.csv`](./reports/customer_segments_summary_report.csv)**: High-level segment financial metrics, customer count, spend averages, and revenue contribution.
- **[`full_model_customer_segments_report.csv`](./reports/full_model_customer_segments_report.csv)**: Full ML model dataset containing 4,338 customer records.
- **[`executive_customer_segmentation_report.md`](./reports/executive_customer_segmentation_report.md)**: Executive documentation, clustering evaluation, and strategic marketing playbooks.

---

##  Programmatic Export Endpoints


- `GET /customers/export/csv`: Export customer table as CSV (supports `?segment=...`, `?priority=...`, `?search=...`).
- `GET /customers/export/segments-summary/csv`: Export segment metrics summary as CSV.
- `GET /customers/statistics`: Aggregated platform statistics.
- `GET /customers/{customer_id}/ai-recommendation`: Dynamic AI marketing copy.
- `POST /dataset/segment`: Upload new dataset file to re-calculate segmentation dynamically.
 ## Author
 
1.Digavinti Sai Chethana <br>
2.Dulam Gnanadeepika

