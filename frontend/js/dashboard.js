// ============================================================
// CUSTOMER AI DASHBOARD
// FINAL DASHBOARD.JS
// ============================================================

let segmentSummary = [];

let segmentChartInstance = null;
let revenueChartInstance = null;


// ============================================================
// HELPER - GET ELEMENT
// ============================================================

function getElement(id) {
    return document.getElementById(id);
}


// ============================================================
// HELPER - SET TEXT
// ============================================================

function setText(id, value) {

    const element = document.getElementById(id);

    if (element) {
        element.textContent = value;
    }
}


// ============================================================
// HELPER - NUMBER
// ============================================================

function toNumber(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return 0;
    }

    const number = Number(
        String(value)
            .replace(/₹/g, "")
            .replace(/,/g, "")
            .trim()
    );

    return Number.isFinite(number) ? number : 0;
}


// ============================================================
// FORMAT NUMBER
// ============================================================

function formatNumber(value) {

    return toNumber(value).toLocaleString("en-IN");
}


// ============================================================
// FORMAT CURRENCY
// ============================================================

function formatCurrency(value) {

    return (
        "₹" +
        toNumber(value).toLocaleString("en-IN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        })
    );
}


// ============================================================
// FETCH API
// ============================================================

async function fetchDashboardData() {

    try {

        console.log("🔄 Loading dashboard overview...");

        const response = await fetch(
            "/dashboard/overview",
            {
                cache: "no-store"
            }
        );

        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}: ${response.statusText}`
            );
        }

        const data = await response.json();

        console.log("✅ Dashboard API Response:");
        console.log(data);

        return data;

    } catch (error) {

        console.error(
            "❌ Dashboard API Error:",
            error
        );

        return null;
    }
}


// ============================================================
// NORMALIZE SEGMENT
// ============================================================

function normalizeSegment(item) {

    if (!item) {
        return null;
    }

    const segment = String(
        item.segment ??
        item.Segment ??
        item.name ??
        "Unknown"
    );

    const customerCount = toNumber(
        item.customer_count ??
        item.Customer_Count ??
        item.count ??
        item.customerCount
    );

    const avgRecency = toNumber(
        item.avg_recency ??
        item.Avg_Recency ??
        item.average_recency ??
        item.averageRecency
    );

    const avgFrequency = toNumber(
        item.avg_frequency ??
        item.Avg_Frequency ??
        item.average_frequency ??
        item.averageFrequency
    );

    const avgMonetary = toNumber(
        item.avg_monetary ??
        item.Avg_Monetary ??
        item.average_monetary ??
        item.averageMonetary
    );

    let totalRevenue = toNumber(
        item.total_revenue ??
        item.Total_Revenue ??
        item.revenue ??
        item.Revenue
    );

    // If backend does not send revenue,
    // calculate it from average monetary × customers.

    if (
        item.total_revenue === undefined &&
        item.Total_Revenue === undefined &&
        item.revenue === undefined &&
        item.Revenue === undefined
    ) {

        totalRevenue =
            avgMonetary * customerCount;
    }

    return {

        segment: segment,

        customer_count: customerCount,

        avg_recency: avgRecency,

        avg_frequency: avgFrequency,

        avg_monetary: avgMonetary,

        total_revenue: totalRevenue
    };
}


// ============================================================
// LOAD DASHBOARD
// ============================================================

async function loadDashboard() {

    console.log(
        "=========================================="
    );

    console.log(
        "🚀 LOADING CUSTOMER AI DASHBOARD"
    );

    console.log(
        "=========================================="
    );


    const data = await fetchDashboardData();


    if (!data) {

        showDashboardError();

        return;
    }


    // ========================================================
    // TOTAL CUSTOMERS
    // ========================================================

    const totalCustomers = toNumber(
        data.total_customers
    );


    setText(
        "totalCustomersCount",
        formatNumber(totalCustomers)
    );


    setText(
        "totalCustomers",
        formatNumber(totalCustomers)
    );


    // ========================================================
    // TOTAL REVENUE
    // ========================================================

    setText(
        "totalRevenue",
        formatCurrency(data.total_revenue)
    );


    // ========================================================
    // AVERAGE CUSTOMER VALUE
    // ========================================================

    let averageCustomerValue =
        toNumber(
            data.average_customer_value
        );


    if (
        averageCustomerValue === 0 &&
        totalCustomers > 0
    ) {

        averageCustomerValue =
            toNumber(data.total_revenue) /
            totalCustomers;
    }


    setText(
        "averageCustomerValue",
        formatCurrency(
            averageCustomerValue
        )
    );


    setText(
        "averageValue",
        formatCurrency(
            averageCustomerValue
        )
    );


    // ========================================================
    // TOTAL SEGMENTS
    // ========================================================

    setText(
        "totalSegments",
        formatNumber(
            data.total_segments
        )
    );


    // ========================================================
    // GET SEGMENTS
    // ========================================================

    let segments = [];


    if (
        Array.isArray(data.segments)
    ) {

        segments = data.segments;

    }

    else if (
        Array.isArray(data.segment_data)
    ) {

        segments = data.segment_data;

    }

    else if (
        Array.isArray(data.data)
    ) {

        segments = data.data;

    }


    console.log(
        "📊 Raw segments:",
        segments
    );


    // ========================================================
    // NORMALIZE
    // ========================================================

    segmentSummary =
        segments
            .map(normalizeSegment)
            .filter(Boolean);


    console.log(
        "📊 Normalized segments:",
        segmentSummary
    );


    if (
        segmentSummary.length === 0
    ) {

        console.error(
            "❌ No segment data found."
        );

        showDashboardError();

        return;
    }


    // ========================================================
    // UPDATE INSIGHT CARDS
    // ========================================================

    updateInsightCards();


    // ========================================================
    // CREATE CHARTS
    // ========================================================

    createSegmentChart();

    createRevenueChart();


    console.log(
        "=========================================="
    );

    console.log(
        "✅ DASHBOARD LOADED SUCCESSFULLY"
    );

    console.log(
        "=========================================="
    );
}


// ============================================================
// UPDATE INSIGHT CARDS
// ============================================================

function updateInsightCards() {

    if (
        !Array.isArray(segmentSummary) ||
        segmentSummary.length === 0
    ) {
        return;
    }


    // ========================================================
    // TOP SEGMENT
    // ========================================================

    const topSegment =
        [...segmentSummary]
            .sort(
                (a, b) =>
                    b.customer_count -
                    a.customer_count
            )[0];


    setText(
        "topSegment",
        topSegment
            ? topSegment.segment
            : "N/A"
    );


    // ========================================================
    // HIGHEST REVENUE
    // ========================================================

    const highestRevenue =
        [...segmentSummary]
            .sort(
                (a, b) =>
                    b.total_revenue -
                    a.total_revenue
            )[0];


    setText(
        "highestRevenue",
        highestRevenue
            ? highestRevenue.segment
            : "N/A"
    );


    // ========================================================
    // FIND SEGMENT COUNT
    // ========================================================

    function getSegmentCount(name) {

        const found =
            segmentSummary.find(
                item =>
                    String(item.segment)
                        .trim()
                        .toLowerCase()
                    ===
                    String(name)
                        .trim()
                        .toLowerCase()
            );


        return found
            ? found.customer_count
            : 0;
    }


    // ========================================================
    // AT RISK
    // ========================================================

    const atRisk =
        getSegmentCount("At Risk");


    setText(
        "atRiskCount",
        formatNumber(atRisk)
    );


    // ========================================================
    // CHAMPIONS
    // ========================================================

    const champions =
        getSegmentCount("Champions");


    setText(
        "championsCount",
        formatNumber(champions)
    );


    // ========================================================
    // LOYAL CUSTOMERS
    // ========================================================

    const loyal =
        getSegmentCount(
            "Loyal Customers"
        );


    setText(
        "loyalCount",
        formatNumber(loyal)
    );


    // ========================================================
    // TOTAL CUSTOMERS
    // ========================================================

    const calculatedTotal =
        segmentSummary.reduce(
            (total, item) =>
                total +
                toNumber(
                    item.customer_count
                ),
            0
        );


    setText(
        "totalCustomersCount",
        formatNumber(
            calculatedTotal
        )
    );


    console.log(
        "🏆 Top Segment:",
        topSegment?.segment
    );

    console.log(
        "💰 Highest Revenue:",
        highestRevenue?.segment
    );

    console.log(
        "⚠️ At Risk:",
        atRisk
    );

    console.log(
        "⭐ Champions:",
        champions
    );

    console.log(
        "💎 Loyal Customers:",
        loyal
    );

    console.log(
        "👥 Total Customers:",
        calculatedTotal
    );
}


// ============================================================
// CREATE SEGMENT DISTRIBUTION CHART
// ============================================================

function createSegmentChart() {

    const canvas =
        getElement(
            "segmentChart"
        );


    if (!canvas) {

        console.error(
            "❌ segmentChart not found."
        );

        return;
    }


    if (
        typeof Chart ===
        "undefined"
    ) {

        console.error(
            "❌ Chart.js is not loaded."
        );

        return;
    }


    // Destroy old chart

    if (
        segmentChartInstance
    ) {

        segmentChartInstance.destroy();

        segmentChartInstance =
            null;
    }


    const wrapper =
        canvas.parentElement;


    if (wrapper) {

        wrapper.style.height =
            "360px";

        wrapper.style.position =
            "relative";
    }


    const labels =
        segmentSummary.map(
            item =>
                item.segment
        );


    const values =
        segmentSummary.map(
            item =>
                item.customer_count
        );


    segmentChartInstance =
        new Chart(
            canvas,
            {

                type: "doughnut",

                data: {

                    labels: labels,

                    datasets: [

                        {

                            label:
                                "Customers",

                            data:
                                values,

                            backgroundColor: [

                                "#42A5D5",

                                "#D94B78",

                                "#E49B22",

                                "#10B981",

                                "#8B5CF6",

                                "#14B8A6",

                                "#F97316",

                                "#6366F1"

                            ],

                            borderColor:
                                "#ffffff",

                            borderWidth: 3
                        }
                    ]
                },

                options: {

                    responsive: true,

                    maintainAspectRatio:
                        false,

                    cutout: "55%",

                    plugins: {

                        legend: {

                            display: true,

                            position: "bottom"
                        },

                        tooltip: {

                            callbacks: {

                                label:
                                    function(
                                        context
                                    ) {

                                        return (
                                            context.label +
                                            ": " +
                                            formatNumber(
                                                context.raw
                                            ) +
                                            " customers"
                                        );
                                    }
                            }
                        }
                    }
                }
            }
        );


    console.log(
        "✅ Segment chart created."
    );
}


// ============================================================
// CREATE REVENUE CHART
// ============================================================

function createRevenueChart() {

    const canvas =
        getElement(
            "revenueChart"
        );


    if (!canvas) {

        console.error(
            "❌ revenueChart not found."
        );

        return;
    }


    if (
        typeof Chart ===
        "undefined"
    ) {

        console.error(
            "❌ Chart.js is not loaded."
        );

        return;
    }


    // Destroy old chart

    if (
        revenueChartInstance
    ) {

        revenueChartInstance.destroy();

        revenueChartInstance =
            null;
    }


    const wrapper =
        canvas.parentElement;


    if (wrapper) {

        wrapper.style.height =
            "360px";

        wrapper.style.position =
            "relative";
    }


    const labels =
        segmentSummary.map(
            item =>
                item.segment
        );


    const values =
        segmentSummary.map(
            item =>
                item.total_revenue
        );


    revenueChartInstance =
        new Chart(
            canvas,
            {

                type: "bar",

                data: {

                    labels: labels,

                    datasets: [

                        {

                            label:
                                "Revenue (₹)",

                            data:
                                values,

                            backgroundColor:
                                "#42A5D5",

                            borderColor:
                                "#3498DB",

                            borderWidth: 1,

                            borderRadius: 8,

                            borderSkipped:
                                false
                        }
                    ]
                },

                options: {

                    responsive: true,

                    maintainAspectRatio:
                        false,

                    scales: {

                        x: {

                            ticks: {

                                autoSkip: false
                            },

                            grid: {

                                display: false
                            }
                        },

                        y: {

                            beginAtZero: true,

                            ticks: {

                                callback:
                                    function(
                                        value
                                    ) {

                                        return (
                                            "₹" +
                                            formatNumber(
                                                value
                                            )
                                        );
                                    }
                            }
                        }
                    },

                    plugins: {

                        legend: {

                            display: false
                        },

                        tooltip: {

                            callbacks: {

                                label:
                                    function(
                                        context
                                    ) {

                                        return (
                                            "Revenue: " +
                                            formatCurrency(
                                                context.raw
                                            )
                                        );
                                    }
                            }
                        }
                    }
                }
            }
        );


    console.log(
        "✅ Revenue chart created."
    );
}


// ============================================================
// DESTROY CHARTS
// ============================================================

function destroyCharts() {

    if (
        segmentChartInstance
    ) {

        segmentChartInstance.destroy();

        segmentChartInstance =
            null;
    }


    if (
        revenueChartInstance
    ) {

        revenueChartInstance.destroy();

        revenueChartInstance =
            null;
    }
}


// ============================================================
// SHOW ERROR
// ============================================================

function showDashboardError() {

    setText(
        "topSegment",
        "No data"
    );

    setText(
        "highestRevenue",
        "No data"
    );

    setText(
        "atRiskCount",
        "0"
    );

    setText(
        "championsCount",
        "0"
    );

    setText(
        "loyalCount",
        "0"
    );

    setText(
        "totalCustomersCount",
        "0"
    );
}


// ============================================================
// REFRESH DASHBOARD
// ============================================================

async function refreshDashboard() {

    console.log(
        "🔄 Refreshing dashboard..."
    );

    destroyCharts();

    await loadDashboard();
}


// ============================================================
// INITIALIZE
// ============================================================

function initializeDashboard() {

    console.log(
        "🚀 Initializing Customer AI Dashboard..."
    );

    loadDashboard();
}


// ============================================================
// DOM READY
// ============================================================

if (
    document.readyState ===
    "loading"
) {

    document.addEventListener(
        "DOMContentLoaded",
        initializeDashboard
    );

} else {

    initializeDashboard();
}