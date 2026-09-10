(function () {
    "use strict";

    console.log("🚀 campaigns.js loaded");

    const API_URL = "/customers/campaigns/summary";

    async function loadCampaigns() {

        const container = document.getElementById("campaignResults");

        if (!container) {
            console.error("❌ campaignResults element not found");
            return;
        }

        console.log("🔄 Loading campaign analytics...");

        container.innerHTML = `
            <div class="campaign-loading">
                <div class="loading-spinner"></div>
                <p>Loading campaigns...</p>
            </div>
        `;

        try {

            const response = await fetch(API_URL, {
                method: "GET",
                headers: {
                    "Accept": "application/json"
                },
                cache: "no-store"
            });

            console.log("📡 Campaign API status:", response.status);

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }

            const data = await response.json();

            console.log("✅ FULL CAMPAIGN API RESPONSE:");
            console.log(data);

            let campaigns = [];

            // -----------------------------------------
            // RESPONSE FORMAT 1
            // [ {...}, {...} ]
            // -----------------------------------------

            if (Array.isArray(data)) {

                campaigns = data;

            }

            // -----------------------------------------
            // RESPONSE FORMAT 2
            // { campaigns: [...] }
            // -----------------------------------------

            else if (Array.isArray(data?.campaigns)) {

                campaigns = data.campaigns;

            }

            // -----------------------------------------
            // RESPONSE FORMAT 3
            // { data: [...] }
            // -----------------------------------------

            else if (Array.isArray(data?.data)) {

                campaigns = data.data;

            }

            // -----------------------------------------
            // RESPONSE FORMAT 4
            // { results: [...] }
            // -----------------------------------------

            else if (Array.isArray(data?.results)) {

                campaigns = data.results;

            }

            // -----------------------------------------
            // RESPONSE FORMAT 5
            // Object containing campaign objects
            // -----------------------------------------

            else if (data && typeof data === "object") {

                const possibleCampaigns = Object.entries(data)
                    .filter(([key, value]) => {
                        return (
                            value &&
                            typeof value === "object" &&
                            !Array.isArray(value)
                        );
                    })
                    .map(([key, value]) => {

                        return {
                            campaign: key,
                            ...value
                        };

                    });

                if (possibleCampaigns.length > 0) {
                    campaigns = possibleCampaigns;
                }
            }

            console.log("📊 Campaigns found:", campaigns);

            // -----------------------------------------
            // NO DATA
            // -----------------------------------------

            if (!campaigns || campaigns.length === 0) {

                container.innerHTML = `
                    <div class="campaign-empty">

                        <div class="empty-icon">📢</div>

                        <h3>No Campaigns Found</h3>

                        <p>
                            No campaign information is available
                            for the current dataset.
                        </p>

                    </div>
                `;

                return;
            }

            // -----------------------------------------
            // RENDER
            // -----------------------------------------

            container.innerHTML = campaigns
                .map(campaign => createCampaignCard(campaign))
                .join("");

            console.log("✅ Campaigns rendered successfully");

        }

        catch (error) {

            console.error("❌ Campaign loading error:", error);

            container.innerHTML = `
                <div class="campaign-error">

                    <div class="error-icon">⚠️</div>

                    <h3>Unable to Load Campaigns</h3>

                    <p>
                        ${escapeHTML(
                            error.message ||
                            "Campaign API request failed."
                        )}
                    </p>

                    <button
                        type="button"
                        class="campaign-retry-button"
                        id="campaignRetryButton"
                    >
                        🔄 Retry
                    </button>

                </div>
            `;

            const retryButton =
                document.getElementById("campaignRetryButton");

            if (retryButton) {
                retryButton.addEventListener(
                    "click",
                    loadCampaigns
                );
            }
        }
    }


    // =========================================================
    // CREATE CAMPAIGN CARD
    // =========================================================

    function createCampaignCard(campaign) {

        const name =
            campaign.campaign ??
            campaign.Campaign ??
            campaign.name ??
            campaign.campaign_name ??
            campaign.Campaign_Name ??
            "Unknown Campaign";


        const customerCount =
            Number(
                campaign.customer_count ??
                campaign.Customer_Count ??
                campaign.customerCount ??
                campaign.count ??
                campaign.customers ??
                0
            );


        const totalRevenue =
            Number(
                campaign.total_revenue ??
                campaign.Total_Revenue ??
                campaign.totalRevenue ??
                campaign.revenue ??
                0
            );


        return `
            <div class="campaign-card">

                <div class="campaign-card-header">

                    <div class="campaign-icon">
                        📢
                    </div>

                    <div>
                        <h3>
                            ${escapeHTML(name)}
                        </h3>
                    </div>

                </div>


                <div class="campaign-stat">

                    <span>Customers</span>

                    <strong>
                        ${customerCount.toLocaleString("en-IN")}
                    </strong>

                </div>


                <div class="campaign-stat">

                    <span>Total Revenue</span>

                    <strong>
                        ₹${totalRevenue.toLocaleString(
                            "en-IN",
                            {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2
                            }
                        )}
                    </strong>

                </div>


                <div class="campaign-arrow">
                    →
                </div>

            </div>
        `;
    }


    // =========================================================
    // ESCAPE HTML
    // =========================================================

    function escapeHTML(value) {

        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }


    // =========================================================
    // GLOBAL FUNCTION
    // =========================================================

    window.loadCampaigns = loadCampaigns;


    // =========================================================
    // INITIALIZE
    // =========================================================

    document.addEventListener("DOMContentLoaded", function () {

        console.log("📢 Campaign page initialized");

        loadCampaigns();

    });

})();