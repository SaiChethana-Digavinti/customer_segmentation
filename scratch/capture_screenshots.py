import os
import time
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = r"c:\Users\saich\Desktop\customer-segmentation\docs\screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1.5
        )
        page = context.new_page()

        print("Navigating to http://127.0.0.1:8000/ ...")
        page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        time.sleep(2)

        # -----------------------------------------------------------------
        # 1. Role Selection Portal
        # -----------------------------------------------------------------
        print("Capturing 01_role_selection_portal.png...")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_role_selection_portal.png"))

        # -----------------------------------------------------------------
        # 2. Admin Login Portal
        # -----------------------------------------------------------------
        print("Switching to Admin login view...")
        page.evaluate("selectAuthRole('admin')")
        time.sleep(0.5)
        page.fill("#adminUsername", "admin")
        page.fill("#adminPassword", "admin123")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "02_admin_login_portal.png"))

        # -----------------------------------------------------------------
        # 3. Analyst Login Portal
        # -----------------------------------------------------------------
        print("Switching to Analyst login view...")
        page.evaluate("selectAuthRole('analyst')")
        time.sleep(0.5)
        page.fill("#analystUsername", "analyst")
        page.fill("#analystPassword", "user123")
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03_analyst_login_portal.png"))

        # -----------------------------------------------------------------
        # Login as Admin
        # -----------------------------------------------------------------
        print("Logging in as Admin...")
        page.evaluate("selectAuthRole('admin')")
        time.sleep(0.3)
        page.fill("#adminUsername", "admin")
        page.fill("#adminPassword", "admin123")
        page.click("#adminSubmitBtn")
        time.sleep(3)

        # -----------------------------------------------------------------
        # 4. Executive Dashboard Overview & KPIs
        # -----------------------------------------------------------------
        print("Capturing 04_executive_dashboard_kpis.png...")
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "04_executive_dashboard_kpis.png"))

        # -----------------------------------------------------------------
        # 5. Dashboard Charts & Visualizations
        # -----------------------------------------------------------------
        print("Capturing 05_dashboard_charts_analytics.png...")
        page.evaluate("window.scrollTo(0, 550)")
        time.sleep(1)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "05_dashboard_charts_analytics.png"))

        # -----------------------------------------------------------------
        # 6. Customer Directory
        # -----------------------------------------------------------------
        print("Navigating to Customers section...")
        page.evaluate("showSection('customers')")
        time.sleep(2)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "06_customer_directory_table.png"))

        # -----------------------------------------------------------------
        # 7. Customer Dossier Modal (Customer 17841)
        # -----------------------------------------------------------------
        print("Opening Customer 17841 dossier modal...")
        page.evaluate("viewCustomer(17841)")
        time.sleep(2)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "07_customer_dossier_modal.png"))
        page.evaluate("closeCustomerModal()")
        time.sleep(0.5)

        # -----------------------------------------------------------------
        # 8. AI Recommendations Engine
        # -----------------------------------------------------------------
        print("Navigating to AI Recommendations...")
        page.evaluate("showSection('ai')")
        time.sleep(1)
        page.fill("#aiCustomerId", "17841")
        print("Triggering AI recommendation generation...")
        page.click("button.ai-button")
        # Wait up to 30s for AI recommendation card to render
        for i in range(30):
            time.sleep(1)
            content = page.inner_text("#aiResult")
            if content and ("Generating" not in content) and len(content.strip()) > 30:
                print(f"AI result generated in {i+1}s!")
                break
        time.sleep(2)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "08_ai_recommendation_engine.png"))

        # -----------------------------------------------------------------
        # 9. Campaign Strategic Actions
        # -----------------------------------------------------------------
        print("Navigating to Campaigns...")
        page.evaluate("showSection('campaigns')")
        time.sleep(1.5)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "09_campaigns_strategic_actions.png"))

        # -----------------------------------------------------------------
        # 10. Analysis History
        # -----------------------------------------------------------------
        print("Navigating to Analysis History...")
        page.evaluate("showSection('history')")
        time.sleep(2)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "10_analysis_history_repository.png"))

        # -----------------------------------------------------------------
        # 11. Platform Admin & Audit Trail
        # -----------------------------------------------------------------
        print("Navigating to Admin Center...")
        page.evaluate("showSection('admin')")
        time.sleep(1.5)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "11_admin_user_management.png"))

        # Switch to Audit Logs tab
        print("Switching to Security Audit Trail tab...")
        page.evaluate("switchAdminTab('logs')")
        time.sleep(1.5)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "11_admin_audit_logs.png"))

        # -----------------------------------------------------------------
        # 12. Segments & Clustering
        # -----------------------------------------------------------------
        print("Navigating to Segments...")
        page.evaluate("showSection('segments')")
        time.sleep(2)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "12_segments_clustering_overview.png"))

        # -----------------------------------------------------------------
        # 13. Multi-Format Export Center (Scroll down on Dashboard)
        # -----------------------------------------------------------------
        print("Capturing Multi-Format Export Center...")
        page.evaluate("showSection('dashboard')")
        time.sleep(1)
        page.evaluate("document.querySelector('.quick-action-download-card')?.scrollIntoView({behavior: 'instant', block: 'center'})")
        time.sleep(1)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "13_multiformat_export_center.png"))

        browser.close()
        print("\nAll screenshots successfully captured!")

if __name__ == "__main__":
    run()
