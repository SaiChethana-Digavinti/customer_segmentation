// ============================================================
// CUSTOMER MANAGEMENT
// customers.js
// ============================================================

"use strict";

const CUSTOMER_API_BASE = "";

let customersData = [];
let filteredCustomersData = [];


// ============================================================
// HELPERS
// ============================================================

function customerElement(id) {
    return document.getElementById(id);
}


async function customerFetch(url, options = {}) {

    const response = await fetch(url, {
        ...options,
        headers: {
            "Accept": "application/json",
            ...(options.headers || {})
        }
    });

    if (!response.ok) {

        let message =
            `Request failed (${response.status})`;

        try {

            const data = await response.json();

            if (typeof data.detail === "string") {
                message = data.detail;
            }
            else if (data.message) {
                message = data.message;
            }

        }
        catch (error) {
            // Ignore JSON parsing errors
        }

        throw new Error(message);
    }

    return response.json();
}


function customerValue(customer, ...keys) {

    for (const key of keys) {

        if (
            customer &&
            customer[key] !== undefined &&
            customer[key] !== null
        ) {

            return customer[key];
        }
    }

    return "";
}


function customerMoney(value) {

    const amount = Number(value);

    if (!Number.isFinite(amount)) {
        return "₹0.00";
    }

    return (
        "₹" +
        amount.toLocaleString(
            "en-IN",
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        )
    );
}


function customerEscape(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


// ============================================================
// GET CUSTOMER ARRAY
// ============================================================

function normalizeCustomersResponse(data) {

    if (Array.isArray(data)) {
        return data;
    }

    if (
        data &&
        Array.isArray(data.customers)
    ) {
        return data.customers;
    }

    if (
        data &&
        Array.isArray(data.data)
    ) {
        return data.data;
    }

    if (
        data &&
        Array.isArray(data.results)
    ) {
        return data.results;
    }

    return [];
}


// ============================================================
// LOAD CUSTOMERS
// ============================================================

async function loadCustomers() {

    console.log(
        "👥 Loading customers..."
    );

    const tableBody =
        customerElement(
            "customersTableBody"
        );

    if (tableBody) {

        tableBody.innerHTML = `
            <tr>
                <td
                    colspan="9"
                    style="text-align:center;"
                >
                    Loading customers...
                </td>
            </tr>
        `;
    }

    try {

        const data =
            await customerFetch(
                "/customers/"
            );

        customersData =
            normalizeCustomersResponse(
                data
            );

        console.log(
            "✅ Customers loaded:",
            customersData
        );

        populateCustomerFilters();

        filterCustomers();
     }

    catch (error) {

        console.error(
            "❌ Customer loading failed:",
            error
        );

        if (tableBody) {

            tableBody.innerHTML = `
                <tr>
                    <td
                        colspan="9"
                        style="text-align:center;"
                    >
                        ❌ Unable to load customers.
                        <br>
                        ${customerEscape(
                            error.message
                        )}
                    </td>
                </tr>
            `;
        }
    }
}


// ============================================================
// CUSTOMER MANAGEMENT LOADER
// ============================================================

async function loadCustomerManagement() {

    await loadCustomers();
}


// ============================================================
// UPDATE CUSTOMER STATISTICS
// ============================================================

function updateCustomerStatistics() {

    const total =
        customersData.length;

    const totalRevenue =
        customersData.reduce(
            (sum, customer) => {

                const monetary =
                    Number(
                        customerValue(
                            customer,
                            "monetary",
                            "Monetary"
                        )
                    ) || 0;

                return sum + monetary;

            },
            0
        );

    const average =
        total > 0
            ? totalRevenue / total
            : 0;


    // --------------------------------------------------------
    // TOTAL CUSTOMERS
    // --------------------------------------------------------

    const totalElements = [
        "totalCustomers",
        "customerTotal",
        "totalCustomerCount",
        "customerCount",
        "totalCustomersCount"
    ];

    totalElements.forEach(
        id => {

            const element =
                customerElement(id);

            if (element) {

                element.textContent =
                    total.toLocaleString(
                        "en-IN"
                    );
            }
        }
    );


    // --------------------------------------------------------
    // TOTAL REVENUE
    // --------------------------------------------------------

    const revenueElements = [
        "totalRevenue",
        "customerRevenue",
        "totalCustomerRevenue"
    ];

    revenueElements.forEach(
        id => {

            const element =
                customerElement(id);

            if (element) {

                element.textContent =
                    customerMoney(
                        totalRevenue
                    );
            }
        }
    );


    // --------------------------------------------------------
    // AVERAGE VALUE
    // --------------------------------------------------------

    const averageElements = [
        "averageCustomerValue",
        "averageValue",
        "customerAverageValue"
    ];

    averageElements.forEach(
        id => {

            const element =
                customerElement(id);

            if (element) {

                element.textContent =
                    customerMoney(
                        average
                    );
            }
        }
    );


    // --------------------------------------------------------
    // RESULT COUNT
    // --------------------------------------------------------

    const resultCount =
        customerElement(
            "customerResultCount"
        );

    if (resultCount) {

        resultCount.textContent =
            filteredCustomersData
                .length
                .toLocaleString(
                    "en-IN"
                );
    }
}


// ============================================================
// POPULATE FILTERS
// ============================================================

function populateCustomerFilters() {

    const segmentFilter =
        customerElement(
            "segmentFilter"
        );

    const priorityFilter =
        customerElement(
            "priorityFilter"
        );


    // --------------------------------------------------------
    // SEGMENT FILTER
    // --------------------------------------------------------

    if (segmentFilter) {

        const oldValue =
            segmentFilter.value;

        const segments =
            [
                ...new Set(
                    customersData
                        .map(
                            customer =>
                                customerValue(
                                    customer,
                                    "segment",
                                    "Segment"
                                )
                        )
                        .filter(
                            value =>
                                String(value)
                                    .trim()
                                    .length > 0
                        )
                )
            ]
                .sort();

        segmentFilter.innerHTML = `
            <option value="">
                All Segments
            </option>
        `;

        segments.forEach(
            segment => {

                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    segment;

                option.textContent =
                    segment;

                segmentFilter.appendChild(
                    option
                );
            }
        );

        if (
            segments.includes(
                oldValue
            )
        ) {

            segmentFilter.value =
                oldValue;
        }
    }


    // --------------------------------------------------------
    // PRIORITY FILTER
    // --------------------------------------------------------

    if (priorityFilter) {

        const oldValue =
            priorityFilter.value;

        const priorities =
            [
                ...new Set(
                    customersData
                        .map(
                            customer =>
                                customerValue(
                                    customer,
                                    "priority",
                                    "Priority"
                                )
                        )
                        .filter(
                            value =>
                                String(value)
                                    .trim()
                                    .length > 0
                        )
                )
            ]
                .sort();

        priorityFilter.innerHTML = `
            <option value="">
                All Priorities
            </option>
        `;

        priorities.forEach(
            priority => {

                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    priority;

                option.textContent =
                    priority;

                priorityFilter.appendChild(
                    option
                );
            }
        );

        if (
            priorities.includes(
                oldValue
            )
        ) {

            priorityFilter.value =
                oldValue;
        }
    }
}


// ============================================================
// FILTER CUSTOMERS
// ============================================================

function filterCustomers() {

    const searchInput =
        customerElement(
            "customerSearch"
        );

    const segmentInput =
        customerElement(
            "segmentFilter"
        );

    const priorityInput =
        customerElement(
            "priorityFilter"
        );

    const search =
        (
            searchInput?.value ||
            ""
        )
            .trim()
            .toLowerCase();

    const selectedSegment =
        (
            segmentInput?.value ||
            ""
        )
            .trim()
            .toLowerCase();

    const selectedPriority =
        (
            priorityInput?.value ||
            ""
        )
            .trim()
            .toLowerCase();


    filteredCustomersData =
        customersData.filter(
            customer => {

                const customerId =
                    String(
                        customerValue(
                            customer,
                            "customer_id",
                            "CustomerID",
                            "id"
                        )
                    )
                        .toLowerCase();

                const segment =
                    String(
                        customerValue(
                            customer,
                            "segment",
                            "Segment"
                        )
                    )
                        .toLowerCase();

                const campaign =
                    String(
                        customerValue(
                            customer,
                            "campaign",
                            "Campaign"
                        )
                    )
                        .toLowerCase();

                const priority =
                    String(
                        customerValue(
                            customer,
                            "priority",
                            "Priority"
                        )
                    )
                        .toLowerCase();


                const matchesSearch =
                    !search ||
                    customerId.includes(
                        search
                    ) ||
                    segment.includes(
                        search
                    ) ||
                    campaign.includes(
                        search
                    );

                const matchesSegment =
                    !selectedSegment ||
                    segment ===
                    selectedSegment;

                const matchesPriority =
                    !selectedPriority ||
                    priority ===
                    selectedPriority;


                return (
                    matchesSearch &&
                    matchesSegment &&
                    matchesPriority
                );
            }
        );

    applyCustomerSort();

    renderCustomers();

    updateCustomerStatistics();
}


// ============================================================
// SORT CUSTOMERS
// ============================================================

function applyCustomerSort() {

    const sortSelect =
        customerElement(
            "customerSort"
        );

    const sort =
        sortSelect?.value ||
        "monetary-desc";


    filteredCustomersData.sort(
        (a, b) => {

            const monetaryA =
                Number(
                    customerValue(
                        a,
                        "monetary",
                        "Monetary"
                    )
                ) || 0;

            const monetaryB =
                Number(
                    customerValue(
                        b,
                        "monetary",
                        "Monetary"
                    )
                ) || 0;

            const frequencyA =
                Number(
                    customerValue(
                        a,
                        "frequency",
                        "Frequency"
                    )
                ) || 0;

            const frequencyB =
                Number(
                    customerValue(
                        b,
                        "frequency",
                        "Frequency"
                    )
                ) || 0;

            const recencyA =
                Number(
                    customerValue(
                        a,
                        "recency",
                        "Recency"
                    )
                ) || 0;

            const recencyB =
                Number(
                    customerValue(
                        b,
                        "recency",
                        "Recency"
                    )
                ) || 0;


            if (
                sort ===
                "monetary-asc"
            ) {

                return (
                    monetaryA -
                    monetaryB
                );
            }


            if (
                sort ===
                "frequency-desc"
            ) {

                return (
                    frequencyB -
                    frequencyA
                );
            }


            if (
                sort ===
                "recency-asc"
            ) {

                return (
                    recencyA -
                    recencyB
                );
            }


            if (
                sort ===
                "recency-desc"
            ) {

                return (
                    recencyB -
                    recencyA
                );
            }


            // Default:
            // highest monetary value first

            return (
                monetaryB -
                monetaryA
            );
        }
    );
}


// ============================================================
// RENDER CUSTOMER TABLE
// ============================================================

function renderCustomers() {

    const tableBody =
        customerElement(
            "customersTableBody"
        );

    if (!tableBody) {

        console.warn(
            "⚠️ customersTableBody not found."
        );

        return;
    }

    tableBody.innerHTML = "";


    if (
        filteredCustomersData.length ===
        0
    ) {

        tableBody.innerHTML = `
            <tr>
                <td
                    colspan="9"
                    style="
                        text-align:center;
                        padding:30px;
                    "
                >
                    No customers found.
                </td>
            </tr>
        `;

        updateCustomerDisplayStats();

        return;
    }


    filteredCustomersData.forEach(
        customer => {

            const customerId =
                customerValue(
                    customer,
                    "customer_id",
                    "CustomerID",
                    "id"
                ) || "-";

            const segment =
                customerValue(
                    customer,
                    "segment",
                    "Segment"
                ) || "-";

            const recency =
                customerValue(
                    customer,
                    "recency",
                    "Recency"
                ) ?? 0;

            const frequency =
                customerValue(
                    customer,
                    "frequency",
                    "Frequency"
                ) ?? 0;

            const monetary =
                Number(
                    customerValue(
                        customer,
                        "monetary",
                        "Monetary"
                    )
                ) || 0;

            const rfmScore =
                customerValue(
                    customer,
                    "rfm_score",
                    "RFM_Score"
                ) || "-";

            const priority =
                customerValue(
                    customer,
                    "priority",
                    "Priority"
                ) || "-";

            const campaign =
                customerValue(
                    customer,
                    "campaign",
                    "Campaign"
                ) || "-";

            const action =
                customerValue(
                    customer,
                    "recommended_action",
                    "Recommended_Action"
                ) || "-";


            const row =
                document.createElement(
                    "tr"
                );


            row.innerHTML = `

                <td>
                    ${customerEscape(
                        customerId
                    )}
                </td>

                <td>
                    ${customerEscape(
                        segment
                    )}
                </td>

                <td>
                    ${customerEscape(
                        recency
                    )}
                </td>

                <td>
                    ${customerEscape(
                        frequency
                    )}
                </td>

                <td>
                    ${customerMoney(
                        monetary
                    )}
                </td>

                <td>
                    ${customerEscape(
                        rfmScore
                    )}
                </td>

                <td>
                    ${customerEscape(
                        priority
                    )}
                </td>

                <td>
                    ${customerEscape(
                        campaign
                    )}
                </td>

                <td>
                    ${customerEscape(
                        action
                    )}
                </td>
            `;


            tableBody.appendChild(
                row
            );
        }
    );


    updateCustomerDisplayStats();
}


// ============================================================
// DISPLAY STATISTICS
// ============================================================

function updateCustomerDisplayStats() {

    const count =
        filteredCustomersData.length;

    const totalSpend =
        filteredCustomersData.reduce(
            (sum, customer) => {

                const monetary =
                    Number(
                        customerValue(
                            customer,
                            "monetary",
                            "Monetary"
                        )
                    ) || 0;

                return (
                    sum +
                    monetary
                );

            },
            0
        );


    const resultCount =
        customerElement(
            "customerResultCount"
        );

    if (resultCount) {

        resultCount.textContent =
            count.toLocaleString(
                "en-IN"
            );
    }


    const totalSpendElement =
        customerElement(
            "customerTotalSpend"
        );

    if (totalSpendElement) {

        totalSpendElement.textContent =
            customerMoney(
                totalSpend
            );
    }


    const status =
        customerElement(
            "customerSearchStatus"
        );

    if (status) {

        status.textContent =
            `Showing ${count} of ${customersData.length} customers`;
    }
}


// ============================================================
// CLEAR FILTERS
// ============================================================

function clearCustomerFilters() {

    const search =
        customerElement(
            "customerSearch"
        );

    const segment =
        customerElement(
            "segmentFilter"
        );

    const priority =
        customerElement(
            "priorityFilter"
        );

    const sort =
        customerElement(
            "customerSort"
        );


    if (search) {
        search.value = "";
    }

    if (segment) {
        segment.value = "";
    }

    if (priority) {
        priority.value = "";
    }

    if (sort) {
        sort.value =
            "monetary-desc";
    }


    filteredCustomersData =
        [...customersData];

    applyCustomerSort();

    renderCustomers();

    updateCustomerStatistics();
}


// ============================================================
// SELECT SEGMENT
// ============================================================
async function setCustomerSegment(segment) {

    console.log("🎯 Quick Action selected:", segment);

    // Open Customers section first
    if (typeof showSection === "function") {
        showSection("customers");
    }

    // Wait until customer data is available
    if (
        !Array.isArray(customersData) ||
        customersData.length === 0
    ) {
        console.log("⏳ Loading customers before applying Quick Action...");

        await loadCustomers();
    }

    const segmentFilter =
        document.getElementById("segmentFilter");

    if (!segmentFilter) {
        console.error("❌ segmentFilter not found.");
        return;
    }

    // Find the actual segment name from loaded data
    const requestedSegment =
        String(segment)
            .trim()
            .toLowerCase();

    const actualSegment =
        customersData
            .map(customer =>
                customerValue(
                    customer,
                    "segment",
                    "Segment"
                )
            )
            .find(value =>
                String(value)
                    .trim()
                    .toLowerCase() ===
                requestedSegment
            );

    console.log(
        "Requested segment:",
        segment
    );

    console.log(
        "Actual segment:",
        actualSegment
    );

    // If segment exists
    if (actualSegment) {

        segmentFilter.value =
            actualSegment;

        filterCustomers();

        console.log(
            `✅ Showing ${actualSegment} customers`
        );

        return;
    }

    // Segment does not exist in current dataset
    console.warn(
        `⚠️ No customers found for segment: ${segment}`
    );

    // Keep the requested segment visible
    // by adding it temporarily if necessary
    let optionExists = Array.from(
        segmentFilter.options
    ).some(
        option =>
            option.value.toLowerCase() ===
            requestedSegment
    );

    if (!optionExists) {

        const option =
            document.createElement("option");

        option.value = segment;
        option.textContent = segment;

        segmentFilter.appendChild(option);
    }

    segmentFilter.value = segment;

    // Filter will correctly produce 0 customers
    filterCustomers();

    console.log(
        `ℹ️ 0 customers belong to "${segment}".`
    );
}


// ============================================================
// VIEW CUSTOMER
// ============================================================

async function viewCustomer(
    customerId
) {

    try {

        const customer =
            await customerFetch(
                `/customers/${encodeURIComponent(
                    customerId
                )}`
            );

        showCustomerModal(
            customer
        );

    }

    catch (error) {

        console.error(
            "Customer details error:",
            error
        );

        alert(
            `Unable to load customer details.\n\n${error.message}`
        );
    }
}


// ============================================================
// CUSTOMER MODAL
// ============================================================

function showCustomerModal(
    customer
) {

    const modal =
        customerElement(
            "customerModal"
        );

    if (!modal) {

        console.log(
            "Customer:",
            customer
        );

        return;
    }


    const customerId =
        customerValue(
            customer,
            "customer_id",
            "CustomerID",
            "id"
        );

    const segment =
        customerValue(
            customer,
            "segment",
            "Segment"
        );

    const recency =
        customerValue(
            customer,
            "recency",
            "Recency"
        );

    const frequency =
        customerValue(
            customer,
            "frequency",
            "Frequency"
        );

    const monetary =
        customerValue(
            customer,
            "monetary",
            "Monetary"
        );

    const priority =
        customerValue(
            customer,
            "priority",
            "Priority"
        );

    const campaign =
        customerValue(
            customer,
            "campaign",
            "Campaign"
        );

    const action =
        customerValue(
            customer,
            "recommended_action",
            "Recommended_Action"
        );


    modal.innerHTML = `

        <div class="customer-modal-content" style="padding: 30px; background: #ffffff; color: #0f172a;">

            <button
                type="button"
                class="modal-close"
                onclick="closeCustomerModal()"
            >
                ×
            </button>

            <h2>
                Customer Details
            </h2>

            <div class="customer-details">

                <p>
                    <strong>
                        Customer ID:
                    </strong>

                    ${customerEscape(
                        customerId
                    )}
                </p>

                <p>
                    <strong>
                        Segment:
                    </strong>

                    ${customerEscape(
                        segment
                    )}
                </p>

                <p>
                    <strong>
                        Recency:
                    </strong>

                    ${customerEscape(
                        recency
                    )}
                </p>

                <p>
                    <strong>
                        Frequency:
                    </strong>

                    ${customerEscape(
                        frequency
                    )}
                </p>

                <p>
                    <strong>
                        Monetary:
                    </strong>

                    ${customerMoney(
                        monetary
                    )}
                </p>

                <p>
                    <strong>
                        Priority:
                    </strong>

                    ${customerEscape(
                        priority
                    )}
                </p>

                <p>
                    <strong>
                        Campaign:
                    </strong>

                    ${customerEscape(
                        campaign
                    )}
                </p>

                <p>
                    <strong>
                        Recommended Action:
                    </strong>

                    ${customerEscape(
                        action
                    )}
                </p>

            </div>

        </div>
    `;

    modal.style.display =
        "flex";
}


// ============================================================
// CLOSE CUSTOMER MODAL
// ============================================================

function closeCustomerModal() {

    const modal =
        customerElement(
            "customerModal"
        );

    if (modal) {

        modal.style.display =
            "none";
    }
}


// ============================================================
// REFRESH CUSTOMERS
// ============================================================

async function refreshCustomers() {

    await loadCustomers();
}


// ============================================================
// GLOBAL FUNCTIONS
// ============================================================

window.loadCustomers =
    loadCustomers;

window.loadCustomerManagement =
    loadCustomerManagement;

window.filterCustomers =
    filterCustomers;

window.clearCustomerFilters =
    clearCustomerFilters;

window.refreshCustomers =
    refreshCustomers;

window.setCustomerSegment =
    setCustomerSegment;

window.viewCustomer =
    viewCustomer;

window.showCustomerModal =
    showCustomerModal;

window.closeCustomerModal =
    closeCustomerModal;

window.getAIRecommendation =
    getAIRecommendation;


// ============================================================
// DATASET UPLOAD
// ============================================================

async function uploadDataset() {

    console.log(
        "========================================"
    );

    console.log(
        "📤 DATASET UPLOAD STARTED"
    );

    console.log(
        "========================================"
    );


    const fileInput =
        document.getElementById(
            "datasetFile"
        );

    const status =
        document.getElementById(
            "datasetStatus"
        );

    const uploadButton =
        document.getElementById(
            "uploadDatasetButton"
        );


    if (!fileInput) {

        console.error(
            "❌ datasetFile element not found."
        );

        alert(
            "❌ File input not found.\n\n" +
            "Please check the HTML id: datasetFile"
        );

        return;
    }


    if (!status) {

        console.error(
            "❌ datasetStatus element not found."
        );
    }


    if (!uploadButton) {

        console.error(
            "❌ uploadDatasetButton element not found."
        );

        alert(
            "❌ Upload button not found.\n\n" +
            "Please check the HTML id: uploadDatasetButton"
        );

        return;
    }


    const file =
        fileInput.files[0];


    if (!file) {

        if (status) {

            status.textContent =
                "⚠️ Please select a dataset file first.";
        }

        alert(
            "⚠️ Please select a dataset file first."
        );

        return;
    }




    console.log(
        "📄 Selected file:",
        file.name
    );

    console.log(
        "📦 File size:",
        file.size,
        "bytes"
    );


    if (status) {

        status.textContent =
            "⏳ Uploading and analyzing dataset...";
    }


    uploadButton.disabled =
        true;

    uploadButton.textContent =
        "⏳ Uploading...";


    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );


    try {

        console.log(
            "📤 Sending file to:",
            "/dataset/segment"
        );


        const response =
            await fetch(
                "/dataset/segment",
                {
                    method: "POST",
                    body: formData
                }
            );


        console.log(
            "📡 Server response:",
            response.status,
            response.statusText
        );


        let data = null;

        const contentType =
            response.headers.get(
                "content-type"
            );


        if (
            contentType &&
            contentType.includes(
                "application/json"
            )
        ) {

            data =
                await response.json();

        }

        else {

            const text =
                await response.text();

            data = {
                message: text
            };
        }


        console.log(
            "📥 Dataset API response:",
            data
        );


        if (!response.ok) {

            let errorMessage =
                `Upload failed (${response.status})`;


            if (
                typeof data?.detail ===
                "string"
            ) {

                errorMessage =
                    data.detail;
            }

            else if (
                data?.detail &&
                typeof data.detail.message ===
                "string"
            ) {

                errorMessage =
                    data.detail.message;
            }

            else if (
                typeof data?.message ===
                "string"
            ) {

                errorMessage =
                    data.message;
            }


            throw new Error(
                errorMessage
            );
        }


        console.log(
            "✅ DATASET UPLOAD SUCCESSFUL"
        );


        const customerCount =
            data?.customer_count;

        const segmentCount =
            data?.segment_count;


        let successMessage =
            `✅ ${file.name} analyzed successfully!`;


        if (
            customerCount !==
            undefined
        ) {

            successMessage +=
                ` ${customerCount} customers processed.`;
        }


        if (status) {

            status.textContent =
                successMessage;

            status.style.color =
                "#16a34a";

            status.style.fontWeight =
                "600";
        }


        alert(
            "✅ Dataset uploaded and analyzed successfully!"
        );


        // ----------------------------------------------------
        // Refresh dashboard
        // ----------------------------------------------------

        try {

            if (
                typeof loadDashboard ===
                "function"
            ) {

                console.log(
                    "🔄 Refreshing dashboard..."
                );

                await loadDashboard();

                console.log(
                    "✅ Dashboard refreshed."
                );
            }

        }

        catch (refreshError) {

            console.error(
                "⚠️ Dashboard refresh error:",
                refreshError
            );
        }


        // ----------------------------------------------------
        // Refresh customer management
        // ----------------------------------------------------

        try {

            if (
                typeof loadCustomerManagement ===
                "function"
            ) {

                console.log(
                    "🔄 Refreshing customers..."
                );

                await loadCustomerManagement();

                console.log(
                    "✅ Customers refreshed."
                );
            }

        }

        catch (refreshError) {

            console.error(
                "⚠️ Customer refresh error:",
                refreshError
            );
        }


        // ----------------------------------------------------
        // Refresh segments
        // ----------------------------------------------------

        try {

            if (
                typeof loadSegments ===
                "function"
            ) {

                console.log(
                    "🔄 Refreshing segments..."
                );

                await loadSegments();

                console.log(
                    "✅ Segments refreshed."
                );
            }

        }

        catch (refreshError) {

            console.error(
                "⚠️ Segment refresh error:",
                refreshError
            );
        }

    }


    catch (error) {

        console.error(
            "❌ DATASET UPLOAD ERROR:",
            error
        );


        if (status) {

            status.textContent =
                `❌ ${error.message}`;

            status.style.color =
                "#dc2626";

            status.style.fontWeight =
                "600";
        }


        alert(
            "❌ Dataset upload failed.\n\n" +
            error.message
        );

    }


    finally {

        uploadButton.disabled =
            false;

        uploadButton.textContent =
            "📊 Upload & Analyze";
    }
}


// ============================================================
// FILE SELECTION EVENT
// ============================================================

function setupDatasetUpload() {

    console.log(
        "🔧 Setting up dataset upload..."
    );


    const fileInput =
        document.getElementById(
            "datasetFile"
        );

    const uploadButton =
        document.getElementById(
            "uploadDatasetButton"
        );

    const status =
        document.getElementById(
            "datasetStatus"
        );


    if (!fileInput) {

        console.error(
            "❌ datasetFile not found."
        );

        return;
    }


    if (!uploadButton) {

        console.error(
            "❌ uploadDatasetButton not found."
        );

        return;
    }


    if (!status) {

        console.error(
            "❌ datasetStatus not found."
        );
    }


    console.log(
        "✅ Dataset upload elements found."
    );


    fileInput.onchange =
        function () {

            const file =
                fileInput.files[0];


            if (!file) {

                if (status) {

                    status.textContent =
                        "Select a dataset file to begin.";

                    status.style.color =
                        "";
                }

                return;
            }


            console.log(
                "📄 File selected:",
                file.name
            );




            if (status) {

                status.textContent =
                    `📄 Ready to analyze: ${file.name}`;

                status.style.color =
                    "#2563eb";

                status.style.fontWeight =
                    "600";
            }

        };


    // IMPORTANT:
    // Use onclick to prevent duplicate handlers.

    uploadButton.onclick =
        function (event) {

            event.preventDefault();

            console.log(
                "🖱️ Upload & Analyze button clicked."
            );

            uploadDataset();
        };


    console.log(
        "✅ Upload button connected successfully."
    );
}

// ============================================================
// AI RECOMMENDATION
// ============================================================

async function getAIRecommendation() {

    const input =
        document.getElementById("aiCustomerId");

    const result =
        document.getElementById("aiResult");

    if (!input) {
        console.error("❌ aiCustomerId element not found.");
        return;
    }

    if (!result) {
        console.error("❌ aiResult element not found.");
        return;
    }

    const customerId =
        input.value.trim();

    if (!customerId) {

        result.innerHTML = `
            <p>
                ⚠️ Please enter a customer ID.
            </p>
        `;

        return;
    }

    console.log(
        "🤖 Generating AI recommendation for customer:",
        customerId
    );

    result.innerHTML = `
        <div class="ai-loading">
            🤖 Generating AI recommendation...
        </div>
    `;

    try {

        const response =
            await fetch(
                `/customers/${encodeURIComponent(customerId)}/ai-recommendation`,
                {
                    method: "GET",
                    headers: {
                        "Accept": "application/json"
                    }
                }
            );

        console.log(
            "📡 AI API response:",
            response.status,
            response.statusText
        );

        const data =
            await response.json();

        console.log(
            "🤖 AI recommendation data:",
            data
        );

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to generate AI recommendation."
            );
        }

        result.innerHTML = `
            <div class="ai-recommendation-card">

                <h3>
                    🤖 AI Marketing Recommendation
                </h3>

                <p>
                    <strong>Customer ID:</strong>
                    ${customerEscape(data.customer_id ?? customerId)}
                </p>

                <p>
                    <strong>Segment:</strong>
                    ${customerEscape(data.segment ?? "-")}
                </p>

                <p>
                    <strong>Campaign:</strong>
                    ${customerEscape(data.campaign ?? "-")}
                </p>

                <p>
                    <strong>Priority:</strong>
                    ${customerEscape(data.priority ?? "-")}
                </p>

                <p>
                    <strong>Marketing Strategy:</strong>
                    ${customerEscape(
                        data.marketing_strategy ?? "-"
                    )}
                </p>

                <p>
                    <strong>Recommended Action:</strong>
                    ${customerEscape(
                        data.recommended_action ?? "-"
                    )}
                </p>

                <div class="ai-message">

                    <strong>
                        AI Recommendation:
                    </strong>

                    <p>
                        ${customerEscape(
                            data.ai_message ?? 
                            "No AI recommendation generated."
                        )}
                    </p>

                </div>

            </div>
        `;

        console.log(
            "✅ AI recommendation rendered successfully."
        );

    }

    catch (error) {

        console.error(
            "❌ AI recommendation error:",
            error
        );

        result.innerHTML = `
            <div class="ai-error">

                ❌ Failed to generate recommendation.

                <p>
                    ${customerEscape(
                        error.message
                    )}
                </p>

            </div>
        `;
    }
}

// ============================================================
// CLEAR AI RESULT
// ============================================================

function clearAIResult() {

    const result =
        document.getElementById(
            "aiResult"
        );

    if (result) {

        result.innerHTML =
            "";
    }
}


// ============================================================
// DOWNLOAD REPORTS (MULTI-FORMAT: CSV, XLSX, PDF, DOCX, JSON)
// ============================================================

function downloadCustomerReport(format = "csv") {
    try {
        const cleanFormat = String(format || "csv").toLowerCase().trim().replace(/^\./, "");
        const validFormats = ["csv", "xlsx", "pdf", "docx", "json"];
        const selectedFormat = validFormats.includes(cleanFormat) ? cleanFormat : "csv";

        const segment = document.getElementById("segmentFilter")?.value || "";
        const priority = document.getElementById("priorityFilter")?.value || "";
        const search = document.getElementById("customerSearch")?.value || "";

        const params = new URLSearchParams();
        if (segment && segment.trim()) params.append("segment", segment.trim());
        if (priority && priority.trim()) params.append("priority", priority.trim());
        if (search && search.trim()) params.append("search", search.trim());

        const query = params.toString() ? `?${params.toString()}` : "";
        const downloadUrl = `/customers/export/${selectedFormat}${query}`;

        const safeSegment = segment ? segment.trim().toLowerCase().replace(/\s+/g, "_") : "all";
        const filename = `customer_segmentation_report_${safeSegment}.${selectedFormat}`;

        const link = document.createElement("a");
        link.href = downloadUrl;
        link.setAttribute("download", filename);
        document.body.appendChild(link);
        link.click();
        link.remove();

        console.log(`📥 Download initiated (${selectedFormat.toUpperCase()}): ${filename}`);
    } catch (error) {
        console.error(`❌ Failed to download customer report (${format}):`, error);
        alert(`Failed to download report (${format}): ` + (error.message || error));
    }
}

function downloadCustomerReportCSV() { downloadCustomerReport("csv"); }
function downloadCustomerReportXLSX() { downloadCustomerReport("xlsx"); }
function downloadCustomerReportPDF() { downloadCustomerReport("pdf"); }
function downloadCustomerReportDOCX() { downloadCustomerReport("docx"); }
function downloadCustomerReportJSON() { downloadCustomerReport("json"); }

function downloadSegmentSummaryReport() {
    try {
        const downloadUrl = "/customers/export/segments-summary/csv";
        const filename = "customer_segments_summary_report.csv";

        const link = document.createElement("a");
        link.href = downloadUrl;
        link.setAttribute("download", filename);
        document.body.appendChild(link);
        link.click();
        link.remove();

        console.log(`📥 Download initiated: ${filename}`);
    } catch (error) {
        console.error("❌ Failed to download segment summary report:", error);
        alert("Failed to download report: " + (error.message || error));
    }
}

window.downloadCustomerReport = downloadCustomerReport;
window.downloadCustomerReportCSV = downloadCustomerReportCSV;
window.downloadCustomerReportXLSX = downloadCustomerReportXLSX;
window.downloadCustomerReportPDF = downloadCustomerReportPDF;
window.downloadCustomerReportDOCX = downloadCustomerReportDOCX;
window.downloadCustomerReportJSON = downloadCustomerReportJSON;
window.downloadSegmentSummaryReport = downloadSegmentSummaryReport;


// ============================================================
// INITIALIZE FRONTEND
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        console.log(
            "🚀 Customer Segmentation frontend started."
        );


        // ----------------------------------------------------
        // Dataset upload
        // ----------------------------------------------------

        setupDatasetUpload();


        // ----------------------------------------------------
        // Refresh customers
        // ----------------------------------------------------

        const refreshCustomers =
            document.getElementById(
                "refreshCustomers"
            );

        if (refreshCustomers) {

            refreshCustomers.addEventListener(
                "click",
                loadCustomerManagement
            );
        }

        // ----------------------------------------------------
        // Customer filters
        // ----------------------------------------------------

        const customerSearch =
            document.getElementById("customerSearch");

        const segmentFilter =
            document.getElementById("segmentFilter");

        const priorityFilter =
            document.getElementById("priorityFilter");

        const customerSort =
            document.getElementById("customerSort");


        // Search while typing
        if (customerSearch) {
            customerSearch.addEventListener(
                "input",
                filterCustomers
            );
        }


        // Segment filter
        if (segmentFilter) {
            segmentFilter.addEventListener(
                "change",
                filterCustomers
            );
        }


        // Priority filter
        if (priorityFilter) {
            priorityFilter.addEventListener(
                "change",
                filterCustomers
            );
        }


        // Sort filter
        if (customerSort) {
            customerSort.addEventListener(
                "change",
                function () {
                    filterCustomers();
                }
            );
        }

        // ----------------------------------------------------
        // AI recommendation Enter key
        // ----------------------------------------------------

        const aiCustomerId =
            document.getElementById(
                "aiCustomerId"
            );

        if (aiCustomerId) {

            aiCustomerId.addEventListener(
                "keydown",
                function (event) {

                    if (
                        event.key === "Enter"
                    ) {

                        if (
                            typeof getAIRecommendation ===
                            "function"
                        ) {

                            getAIRecommendation();
                        }
                    }
                }
            );
        }


        // ----------------------------------------------------
        // Initial dashboard
        // ----------------------------------------------------

        if (
            typeof loadDashboard ===
            "function"
        ) {

            loadDashboard();
        }


        console.log(
            "✅ Frontend initialization completed."
        );

    }
);