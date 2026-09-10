// ============================================================
// CUSTOMER SEGMENTATION DASHBOARD
// core.js
// Global navigation + common UI functions
// ============================================================


// ============================================================
// GLOBAL API CONFIGURATION
// ============================================================

const API_BASE = "";


// ============================================================
// COMMON HELPERS
// ============================================================

function getElement(id) {

    return document.getElementById(id);

}


// ============================================================
// API FETCH HELPER
// ============================================================

async function apiFetch(
    url,
    options = {}
) {

    const response =
        await fetch(
            url,
            {
                ...options,

                headers: {
                    "Accept": "application/json",
                    ...(options.headers || {})
                }
            }
        );


    if (!response.ok) {

        let message =
            `API request failed (${response.status})`;


        try {

            const data =
                await response.json();


            if (
                typeof data.detail ===
                "string"
            ) {

                message =
                    data.detail;

            }

            else if (
                data.message
            ) {

                message =
                    data.message;

            }

        }

        catch (error) {

            console.warn(
                "Could not parse API error:",
                error
            );

        }


        const apiError =
            new Error(
                message
            );


        apiError.status =
            response.status;


        throw apiError;
    }


    return response.json();
}


// ============================================================
// HTML ESCAPE
// ============================================================

function escapeHTML(value) {

    return String(
        value ?? ""
    )
    .replaceAll(
        "&",
        "&amp;"
    )
    .replaceAll(
        "<",
        "&lt;"
    )
    .replaceAll(
        ">",
        "&gt;"
    )
    .replaceAll(
        '"',
        "&quot;"
    )
    .replaceAll(
        "'",
        "&#039;"
    );
}


// ============================================================
// ATTRIBUTE ESCAPE
// ============================================================

function escapeAttribute(value) {

    return String(
        value ?? ""
    )
    .replaceAll(
        "\\",
        "\\\\"
    )
    .replaceAll(
        "'",
        "\\'"
    )
    .replaceAll(
        '"',
        "&quot;"
    );
}


// ============================================================
// CURRENCY FORMAT
// ============================================================

function formatCurrency(
    value
) {

    const number =
        Number(value);


    if (
        !Number.isFinite(
            number
        )
    ) {

        return "₹0.00";
    }


    return (
        "₹" +
        number.toLocaleString(
            "en-IN",
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        )
    );
}


// ============================================================
// NUMBER FORMAT
// ============================================================

function formatNumber(
    value
) {

    const number =
        Number(value);


    if (
        !Number.isFinite(
            number
        )
    ) {

        return "0";
    }


    return number.toLocaleString(
        "en-IN"
    );
}


// ============================================================
// PRIORITY CLASS
// ============================================================

function getPriorityClass(
    priority
) {

    const value =
        String(
            priority ?? ""
        )
        .trim()
        .toLowerCase();


    if (
        value.includes(
            "very high"
        )
    ) {

        return "priority-very-high";
    }


    if (
        value === "high" ||
        value.includes("high")
    ) {

        return "priority-high";
    }


    if (
        value.includes(
            "medium"
        )
    ) {

        return "priority-medium";
    }


    if (
        value.includes(
            "low"
        )
    ) {

        return "priority-low";
    }


    return "priority-default";
}


// ============================================================
// NAVIGATION
// ============================================================

function showSection(
    sectionId
) {

    console.log(
        "📌 Opening section:",
        sectionId
    );


    // --------------------------------------------------------
    // Hide all sections
    // --------------------------------------------------------

    document
        .querySelectorAll(
            ".section"
        )
        .forEach(
            section => {

                section.classList.remove(
                    "active"
                );

            }
        );


    // --------------------------------------------------------
    // Remove active navigation
    // --------------------------------------------------------

    document
        .querySelectorAll(
            ".nav-item, .sidebar-link, .nav-link, .nav-button"
        )
        .forEach(
            link => {

                link.classList.remove(
                    "active"
                );

            }
        );


    // --------------------------------------------------------
    // Show selected section
    // --------------------------------------------------------

    const section =
        getElement(
            sectionId
        );


    if (!section) {

        console.error(
            "❌ Section not found:",
            sectionId
        );

        return;
    }


    section.classList.add(
        "active"
    );


    // --------------------------------------------------------
    // Find matching navigation item
    // --------------------------------------------------------

    const navItem =
        document.querySelector(
            `[data-section="${sectionId}"]`
        );


    if (navItem) {

        navItem.classList.add(
            "active"
        );
    }


    // --------------------------------------------------------
    // Load section data
    // --------------------------------------------------------

    switch (
        sectionId
    ) {

        case "dashboard":

            if (
                typeof loadDashboard ===
                "function"
            ) {

                loadDashboard();
            }

            break;


        case "customers":

            if (
                typeof loadCustomerManagement ===
                "function"
            ) {

                loadCustomerManagement();
            }

            else if (
                typeof loadCustomers ===
                "function"
            ) {

                loadCustomers();
            }

            break;


        case "segments":

            if (
                typeof loadSegments ===
                "function"
            ) {

                loadSegments();
            }

            break;


        case "campaigns":

            if (
                typeof loadCampaigns ===
                "function"
            ) {

                loadCampaigns();
            }

            break;


        case "ai":

            if (
                typeof clearAIResult ===
                "function"
            ) {

                clearAIResult();
            }

            break;


        case "dataset":

            console.log(
                "📁 Dataset section opened."
            );

            break;


        case "history":

            if (
                typeof loadAnalysisHistory ===
                "function"
            ) {
                loadAnalysisHistory(1);
            }

            break;


        case "admin":

            if (
                typeof loadAdminDashboard ===
                "function"
            ) {
                loadAdminDashboard();
            }

            break;


        default:

            console.log(
                "No special loader for:",
                sectionId
            );
    }
}


// ============================================================
// MOBILE SIDEBAR
// ============================================================

function toggleSidebar() {

    const sidebar =
        document.querySelector(
            ".sidebar"
        );


    if (!sidebar) {
        return;
    }


    sidebar.classList.toggle(
        "open"
    );
}


// ============================================================
// CLOSE MOBILE SIDEBAR
// ============================================================

function closeSidebar() {

    const sidebar =
        document.querySelector(
            ".sidebar"
        );


    if (
        sidebar &&
        sidebar.classList.contains(
            "open"
        )
    ) {

        sidebar.classList.remove(
            "open"
        );
    }
}


// ============================================================
// GLOBAL CLICK HANDLER
// ============================================================

document.addEventListener(
    "click",
    function(event) {

        const navigationElement =
            event.target.closest(
                "[data-section]"
            );


        if (
            navigationElement
        ) {

            const sectionId =
                navigationElement.dataset.section;


            if (sectionId) {

                event.preventDefault();

                showSection(
                    sectionId
                );

                closeSidebar();
            }
        }

    }
);


// ============================================================
// ESC KEY
// ============================================================

document.addEventListener(
    "keydown",
    function(event) {

        if (
            event.key ===
            "Escape"
        ) {

            closeSidebar();


            if (
                typeof closeCustomerModal ===
                "function"
            ) {

                closeCustomerModal();
            }

            if (
                typeof closeAddUserModal ===
                "function"
            ) {

                closeAddUserModal();
            }
        }

    }
);


// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function() {

        console.log(
            "🚀 Customer Segmentation Dashboard initialized."
        );


        // ----------------------------------------------------
        // Make dashboard active initially
        // ----------------------------------------------------

        const activeSection =
            document.querySelector(
                ".section.active"
            );


        if (!activeSection) {

            const dashboard =
                getElement(
                    "dashboard"
                );


            if (dashboard) {

                dashboard.classList.add(
                    "active"
                );
            }
        }


        // ----------------------------------------------------
        // Initial dashboard load
        // ----------------------------------------------------

        if (
            typeof loadDashboard ===
            "function"
        ) {

            loadDashboard();
        }


        // ----------------------------------------------------
        // Mobile menu button
        // ----------------------------------------------------

        const menuButton =
            getElement(
                "menuButton"
            );


        if (menuButton) {

            menuButton.addEventListener(
                "click",
                toggleSidebar
            );
        }


        // ----------------------------------------------------
        // Alternative menu buttons
        // ----------------------------------------------------

        const menuButtons =
            document.querySelectorAll(
                ".menu-toggle, .sidebar-toggle"
            );


        menuButtons.forEach(
            button => {

                button.addEventListener(
                    "click",
                    toggleSidebar
                );

            }
        );

    }
);


// ============================================================
// GLOBAL EXPORTS
// ============================================================

window.API_BASE =
    API_BASE;

window.getElement =
    getElement;

window.apiFetch =
    apiFetch;

window.escapeHTML =
    escapeHTML;

window.escapeAttribute =
    escapeAttribute;

window.formatCurrency =
    formatCurrency;

window.formatNumber =
    formatNumber;

window.getPriorityClass =
    getPriorityClass;

window.showSection =
    showSection;

window.toggleSidebar =
    toggleSidebar;

window.closeSidebar =
    closeSidebar;