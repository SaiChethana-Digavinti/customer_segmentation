(function () {
    "use strict";

    console.log("🚀 segments.js loaded");

    const API_URL = "/customers/segments/summary";


    // =========================================================
    // LOAD SEGMENTS
    // =========================================================

    async function loadSegments() {

        const container =
            document.getElementById("segmentResults");

        if (!container) {

            console.error(
                "❌ segmentResults element not found"
            );

            return;
        }

        console.log("🔄 Loading segments...");


        // Loading state

        container.innerHTML = `
            <div class="segment-loading">
                <div class="loading-spinner"></div>
                <p>Loading customer segments...</p>
            </div>
        `;


        try {

            const response = await fetch(
                API_URL,
                {
                    method: "GET",

                    headers: {
                        "Accept": "application/json"
                    },

                    cache: "no-store"
                }
            );


            console.log(
                "📡 Segment API status:",
                response.status
            );


            if (!response.ok) {

                throw new Error(
                    "API Error: " + response.status
                );

            }


            const data =
                await response.json();


            console.log(
                "✅ Segment API data:",
                data
            );


            // =================================================
            // HANDLE DIFFERENT API RESPONSE FORMATS
            // =================================================

            let segments = [];


            if (Array.isArray(data)) {

                segments = data;

            }

            else if (
                Array.isArray(data.segments)
            ) {

                segments = data.segments;

            }

            else if (
                Array.isArray(data.segment_data)
            ) {

                segments = data.segment_data;

            }


            console.log(
                "📊 Segments found:",
                segments.length
            );


            // =================================================
            // NO DATA
            // =================================================

            if (segments.length === 0) {

                container.innerHTML = `
                    <div class="segment-empty">

                        <div class="empty-icon">
                            📊
                        </div>

                        <h3>
                            No segments found
                        </h3>

                        <p>
                            Segment data is not available.
                        </p>

                    </div>
                `;

                return;
            }


            // =================================================
            // RENDER SEGMENTS
            // =================================================

            renderSegments(
                segments,
                container
            );


        }

        catch (error) {

            console.error(
                "❌ Segment loading error:",
                error
            );


            container.innerHTML = `
                <div class="segment-error">

                    <div class="error-icon">
                        ⚠️
                    </div>

                    <h3>
                        Unable to load segments
                    </h3>

                    <p>
                        ${escapeHtml(error.message)}
                    </p>

                    <button
                        id="segmentRetryButton"
                        class="segment-retry-button"
                    >
                        🔄 Retry
                    </button>

                </div>
            `;


            const retryButton =
                document.getElementById(
                    "segmentRetryButton"
                );


            if (retryButton) {

                retryButton.addEventListener(
                    "click",
                    loadSegments
                );

            }

        }

    }



    // =========================================================
    // RENDER SEGMENTS
    // =========================================================

    function renderSegments(
        segments,
        container
    ) {


        // Sort by customer count
        // Largest segment first

        segments.sort(
            function (a, b) {

                return (
                    Number(
                        b.customer_count || 0
                    )
                    -
                    Number(
                        a.customer_count || 0
                    )
                );

            }
        );


        // IMPORTANT:
        //
        // Do NOT create another .segments-grid here.
        //
        // index.html already has:
        //
        // <div
        //     id="segmentResults"
        //     class="segment-grid"
        // >
        //
        // Therefore cards must be direct children
        // of segmentResults.

        container.innerHTML =
            segments
                .map(
                    function (segment) {

                        return createSegmentCard(
                            segment
                        );

                    }
                )
                .join("");


        // =====================================================
        // CARD CLICK EVENTS
        // =====================================================

        container
        .querySelectorAll(".segment-card")
        .forEach(function (card) {

            card.addEventListener("click", function () {

                const segmentName =
                    this.dataset.segment;

                console.log(
                    "Selected segment:",
                    segmentName
                );

                // Find selected segment data
                const selectedSegment =
                    segments.find(function (item) {

                        return (
                            String(item.segment).toLowerCase() ===
                            String(segmentName).toLowerCase()
                        );

                    });

                if (!selectedSegment) {
                    console.error(
                        "Segment data not found:",
                        segmentName
                    );
                    return;
                }

                showSegmentDetails(selectedSegment);

            });

        });
      }

    // =========================================================
    // CREATE SEGMENT CARD
    // =========================================================

    function createSegmentCard(
        segment
    ) {


        const name =
            segment.segment ||
            "Unknown";


        const count =
            Number(
                segment.customer_count || 0
            );


        const revenue =
            Number(
                segment.total_revenue || 0
            );


        const avgRecency =
            Number(
                segment.avg_recency || 0
            );


        const avgFrequency =
            Number(
                segment.avg_frequency || 0
            );


        const avgMonetary =
            Number(
                segment.avg_monetary || 0
            );


        // =====================================================
        // SEGMENT ICON
        // =====================================================

        let icon = "👥";


        const lowerName =
            name.toLowerCase();


        if (
            lowerName.includes(
                "champion"
            )
        ) {

            icon = "🏆";

        }

        else if (
            lowerName.includes(
                "loyal"
            )
        ) {

            icon = "💎";

        }

        else if (
            lowerName.includes(
                "risk"
            )
        ) {

            icon = "⚠️";

        }

        else if (
            lowerName.includes(
                "lost"
            )
        ) {

            icon = "🔴";

        }

        else if (
            lowerName.includes(
                "new"
            )
        ) {

            icon = "🆕";

        }



        // =====================================================
        // SEGMENT CARD
        // =====================================================

        return `
            <div
                class="segment-card"
                data-segment="${escapeHtml(name)}"
                role="button"
                tabindex="0"
            >

                <!-- ICON -->

                <div class="segment-icon">
                    ${icon}
                </div>


                <!-- CONTENT -->

                <div class="segment-content">


                    <!-- NAME -->

                    <h3>
                        ${escapeHtml(name)}
                    </h3>


                    <!-- CUSTOMER COUNT -->

                    <div class="segment-count">

                        ${count}

                        <span>
                            Customers
                        </span>

                    </div>


                    <!-- STATISTICS -->

                    <div class="segment-stats">


                        <!-- RECENCY -->

                        <div>

                            <span>
                                Avg. Recency
                            </span>

                            <strong>
                                ${avgRecency.toFixed(2)}
                            </strong>

                        </div>


                        <!-- FREQUENCY -->

                        <div>

                            <span>
                                Avg. Frequency
                            </span>

                            <strong>
                                ${avgFrequency.toFixed(2)}
                            </strong>

                        </div>


                        <!-- MONETARY -->

                        <div>

                            <span>
                                Avg. Monetary
                            </span>

                            <strong>
                                ₹${formatMoney(
                                    avgMonetary
                                )}
                            </strong>

                        </div>


                    </div>


                    <!-- TOTAL REVENUE -->

                    <div class="segment-revenue">

                        <span>
                            Total Revenue
                        </span>

                        <strong>
                            ₹${formatMoney(
                                revenue
                            )}
                        </strong>

                    </div>


                </div>


                <!-- ARROW -->

                <div class="segment-arrow">
                    →
                </div>


            </div>
        `;
    }


    async function showSegmentDetails(segment) {

    const details =
        document.getElementById("segmentDetails");

    if (!details) {
        console.error("❌ segmentDetails element not found");
        return;
    }

    const segmentName =
        String(segment.segment || "Unknown");

    // ---------------------------------------------------------
    // SHOW SUMMARY IMMEDIATELY
    // ---------------------------------------------------------

    const count =
        Number(segment.customer_count || 0);

    const avgRecency =
        Number(segment.avg_recency || 0);

    const avgFrequency =
        Number(segment.avg_frequency || 0);

    const avgMonetary =
        Number(segment.avg_monetary || 0);

    const totalRevenue =
        Number(segment.total_revenue || 0);


    details.innerHTML = `
        <div class="segment-detail-content">

            <div class="segment-detail-header">

                <div>
                    <span class="segment-detail-label">
                        SELECTED SEGMENT
                    </span>

                    <h2>
                        ${escapeHtml(segmentName)}
                    </h2>

                    <p>
                        Detailed customer segment information
                    </p>
                </div>

                <button
                    type="button"
                    class="close-button"
                    id="closeSegmentDetails"
                >
                    ✕ Close
                </button>

            </div>


            <div class="segment-detail-stats">

                <div class="detail-stat">
                    <span>Customers</span>
                    <strong>${count}</strong>
                </div>

                <div class="detail-stat">
                    <span>Avg. Recency</span>
                    <strong>${avgRecency.toFixed(2)}</strong>
                </div>

                <div class="detail-stat">
                    <span>Avg. Frequency</span>
                    <strong>${avgFrequency.toFixed(2)}</strong>
                </div>

                <div class="detail-stat">
                    <span>Avg. Monetary</span>
                    <strong>
                        ₹${formatMoney(avgMonetary)}
                    </strong>
                </div>

                <div class="detail-stat">
                    <span>Total Revenue</span>
                    <strong>
                        ₹${formatMoney(totalRevenue)}
                    </strong>
                </div>

            </div>


            <div class="segment-customers-section">

                <div class="segment-customers-title">
                    <h3>
                        Customers in
                        ${escapeHtml(segmentName)}
                    </h3>

                    <span id="segmentCustomerCount">
                        Loading...
                    </span>
                </div>

                <div
                    id="segmentCustomersLoading"
                    class="segment-customers-loading"
                >
                    <div class="loading-spinner"></div>

                    <p>
                        Loading customers...
                    </p>
                </div>

                <div
                    id="segmentCustomersTable"
                    class="segment-customers-table-wrapper"
                ></div>

            </div>

        </div>
    `;


    // ---------------------------------------------------------
    // CLOSE BUTTON
    // ---------------------------------------------------------

    const closeButton =
        document.getElementById("closeSegmentDetails");

    if (closeButton) {

        closeButton.addEventListener(
            "click",
            function () {

                details.innerHTML = "";

            }
        );
    }


    // ---------------------------------------------------------
    // LOAD ACTUAL CUSTOMERS
    // ---------------------------------------------------------

    try {

        const url =
            `/customers/filter/segment?segment=${encodeURIComponent(segmentName)}`;

        console.log(
            "🔍 Loading customers for segment:",
            segmentName
        );

        console.log(
            "📡 Customer API:",
            url
        );


        const response =
            await fetch(
                url,
                {
                    method: "GET",

                    headers: {
                        "Accept": "application/json"
                    },

                    cache: "no-store"
                }
            );


        console.log(
            "📡 Customer API status:",
            response.status
        );


        if (!response.ok) {

            let errorMessage =
                `API Error: ${response.status}`;

            try {

                const errorData =
                    await response.json();

                if (errorData.detail) {
                    errorMessage =
                        errorData.detail;
                }

            }
            catch (error) {

                console.warn(
                    "Could not read API error:",
                    error
                );

            }

            throw new Error(errorMessage);
        }


        const customers =
            await response.json();


        console.log(
            "✅ Segment customers:",
            customers
        );


        const loading =
            document.getElementById(
                "segmentCustomersLoading"
            );

        const table =
            document.getElementById(
                "segmentCustomersTable"
            );

        const customerCount =
            document.getElementById(
                "segmentCustomerCount"
            );


        if (loading) {
            loading.style.display = "none";
        }


        // -----------------------------------------------------
        // NO CUSTOMERS
        // -----------------------------------------------------

        if (
            !Array.isArray(customers) ||
            customers.length === 0
        ) {

            if (customerCount) {
                customerCount.textContent =
                    "0 customers";
            }

            if (table) {

                table.innerHTML = `
                    <div class="segment-no-customers">

                        <div class="empty-icon">
                            👥
                        </div>

                        <h3>
                            No customers found
                        </h3>

                        <p>
                            There are no customers in
                            ${escapeHtml(segmentName)}.
                        </p>

                    </div>
                `;
            }

            return;
        }


        // -----------------------------------------------------
        // CUSTOMER COUNT
        // -----------------------------------------------------

        if (customerCount) {

            customerCount.textContent =
                `${customers.length} customer${
                    customers.length === 1
                        ? ""
                        : "s"
                }`;
        }


        // -----------------------------------------------------
        // CUSTOMER TABLE
        // -----------------------------------------------------

        const html = `
            <div class="customer-table-container">

                <table class="customer-table">

                    <thead>
                        <tr>
                            <th>Customer ID</th>
                            <th>Recency</th>
                            <th>Frequency</th>
                            <th>Monetary</th>
                            <th>RFM Score</th>
                            <th>Priority</th>
                            <th>Campaign</th>
                            <th>Recommended Action</th>
                        </tr>
                    </thead>

                    <tbody>

                        ${customers.map(customer => `
                            <tr>

                                <td>${customer.customer_id}</td>

                                <td>${customer.recency}</td>

                                <td>${customer.frequency}</td>

                                <td>
                                    ₹${Number(customer.monetary).toLocaleString(
                                        "en-IN",
                                        {
                                            minimumFractionDigits: 2,
                                            maximumFractionDigits: 2
                                        }
                                    )}
                                </td>

                                <td>${customer.rfm_score}</td>

                                <td>
                                    <span class="priority-badge priority-${String(
                                        customer.priority || ""
                                    ).toLowerCase()}">
                                        ${customer.priority}
                                    </span>
                                </td>

                                <td>${customer.campaign}</td>

                                <td>${customer.recommended_action}</td>

                            </tr>
                        `).join("")}

                    </tbody>

                </table>

            </div>
        `;

        // IMPORTANT: Put the generated table inside the table container
        if (table) {
            table.innerHTML = html;
        }

        // -----------------------------------------------------
        // SCROLL TO DETAILS
        // -----------------------------------------------------

        details.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    }


    catch (error) {

        console.error(
            "❌ Segment customer loading error:",
            error
        );


        const loading =
            document.getElementById(
                "segmentCustomersLoading"
            );

        const table =
            document.getElementById(
                "segmentCustomersTable"
            );

        const customerCount =
            document.getElementById(
                "segmentCustomerCount"
            );


        if (loading) {
            loading.style.display = "none";
        }


        if (customerCount) {
            customerCount.textContent =
                "Unable to load";
        }


        if (table) {

            table.innerHTML = `

                <div class="segment-error">

                    <div class="error-icon">
                        ⚠️
                    </div>

                    <h3>
                        Unable to load customers
                    </h3>

                    <p>
                        ${escapeHtml(
                            error.message ||
                            "Customer API request failed."
                        )}
                    </p>

                    <button
                        type="button"
                        class="segment-retry-button"
                        onclick="showSegmentDetails(
                            ${JSON.stringify(segment)}
                        )"
                    >
                        🔄 Retry
                    </button>

                </div>

            `;
        }

    }

}

function getPriorityClassForSegment(priority) {

    const value =
        String(priority || "")
            .toLowerCase()
            .trim();

    if (value.includes("very high")) {
        return "priority-very-high";
    }

    if (
        value === "high" ||
        value.includes("high")
    ) {
        return "priority-high";
    }

    if (value.includes("medium")) {
        return "priority-medium";
    }

    if (value.includes("low")) {
        return "priority-low";
    }

    return "priority-default";
}

    // =========================================================
    // FORMAT MONEY
    // =========================================================

    function formatMoney(value) {

        return Number(
            value || 0
        ).toLocaleString(
            "en-IN",
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        );

    }



    // =========================================================
    // ESCAPE HTML
    // =========================================================

    function escapeHtml(value) {

        return String(
            value ?? ""
        )

            .replace(
                /&/g,
                "&amp;"
            )

            .replace(
                /</g,
                "&lt;"
            )

            .replace(
                />/g,
                "&gt;"
            )

            .replace(
                /"/g,
                "&quot;"
            )

            .replace(
                /'/g,
                "&#039;"
            );

    }



    // =========================================================
    // KEYBOARD ACCESSIBILITY
    // =========================================================

    function handleKeyboardNavigation(event) {

        if (
            event.key !== "Enter" &&
            event.key !== " "
        ) {

            return;
        }


        const card =
            event.target.closest(
                ".segment-card"
            );


        if (!card) {

            return;

        }


        event.preventDefault();


        const segment =
            card.dataset.segment;


        console.log(
            "Selected segment:",
            segment
        );

    }



    // =========================================================
    // GLOBAL FUNCTION
    // =========================================================

    window.loadSegments =
        loadSegments;



    // =========================================================
    // INITIALIZE
    // =========================================================

    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            function () {

                loadSegments();

                document.addEventListener(
                    "keydown",
                    handleKeyboardNavigation
                );

            }
        );

    }

    else {

        loadSegments();

        document.addEventListener(
            "keydown",
            handleKeyboardNavigation
        );

    }

})();