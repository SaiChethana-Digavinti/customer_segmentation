import io
import json
import csv
import openpyxl
from docx import Document
import os
import sys
from pathlib import Path
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_csv_download():
    response = client.get("/customers/export/csv")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "text/csv" in response.headers.get("content-type", "")
    assert "customer_segmentation_report_all.csv" in response.headers.get("content-disposition", "")

    reader = csv.DictReader(io.StringIO(response.text))
    rows = list(reader)
    assert len(rows) > 0, "CSV has no data rows"
    assert "CustomerID" in reader.fieldnames
    assert "Segment" in reader.fieldnames
    assert "RFM_Score" in reader.fieldnames
    print(f"✅ CSV Test Passed ({len(rows)} records)")


def test_xlsx_download():
    response = client.get("/customers/export/xlsx")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers.get("content-type", "")
    assert "customer_segmentation_report_all.xlsx" in response.headers.get("content-disposition", "")

    wb = openpyxl.load_workbook(io.BytesIO(response.content))
    assert "Customer Segmentation" in wb.sheetnames, "Sheet 1 missing"
    assert "Segment Summary" in wb.sheetnames, "Sheet 2 missing"
    ws = wb["Customer Segmentation"]
    assert ws.max_row > 4, "No customer rows in Excel"
    print(f"✅ XLSX Test Passed ({len(wb.sheetnames)} sheets, {ws.max_row} rows)")


def test_pdf_download():
    response = client.get("/customers/export/pdf")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "application/pdf" in response.headers.get("content-type", "")
    assert "customer_segmentation_report_all.pdf" in response.headers.get("content-disposition", "")
    assert response.content.startswith(b"%PDF-"), "Invalid PDF signature"
    assert len(response.content) > 1000, "PDF content suspiciously small"
    print(f"✅ PDF Test Passed ({len(response.content)} bytes)")


def test_docx_download():
    response = client.get("/customers/export/docx")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in response.headers.get("content-type", "")
    assert "customer_segmentation_report_all.docx" in response.headers.get("content-disposition", "")

    doc = Document(io.BytesIO(response.content))
    assert len(doc.tables) >= 2, f"Expected at least 2 tables, found {len(doc.tables)}"
    assert len(doc.paragraphs) > 0, "No paragraphs found in docx"
    print(f"✅ DOCX Test Passed ({len(doc.tables)} tables, {len(doc.paragraphs)} paragraphs)")


def test_json_download():
    response = client.get("/customers/export/json")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "application/json" in response.headers.get("content-type", "")
    assert "customer_segmentation_report_all.json" in response.headers.get("content-disposition", "")

    data = json.loads(response.text)
    assert "report_title" in data
    assert "summary" in data
    assert "customers" in data
    assert len(data["customers"]) > 0
    print(f"✅ JSON Test Passed ({len(data['customers'])} customers, total rev: {data['summary']['total_portfolio_revenue']})")


def test_unified_and_filter_downloads():
    # Test unified endpoint with filter
    response = client.get("/customers/export/xlsx?segment=Champions")
    assert response.status_code == 200
    assert "customer_segmentation_report_champions.xlsx" in response.headers.get("content-disposition", "")

    wb = openpyxl.load_workbook(io.BytesIO(response.content))
    ws = wb["Customer Segmentation"]
    # Check that rows have Champions
    found_champ = False
    for row in ws.iter_rows(min_row=5, values_only=True):
        if row and row[0] != "Total Portfolio" and row[1]:
            assert row[1] == "Champions", f"Expected Champions, got {row[1]}"
            found_champ = True
    assert found_champ, "No Champions rows found in filtered report"
    print("✅ Filtered XLSX Test Passed")

    # Test invalid format returns 400
    r_bad = client.get("/customers/export/invalid_ext")
    assert r_bad.status_code == 400
    print("✅ Invalid format handled gracefully (HTTP 400)")


if __name__ == "__main__":
    test_csv_download()
    test_xlsx_download()
    test_pdf_download()
    test_docx_download()
    test_json_download()
    test_unified_and_filter_downloads()
    print("\n🎉 ALL 5 REPORT DOWNLOAD TESTS PASSED SUCCESSFULLY!")
