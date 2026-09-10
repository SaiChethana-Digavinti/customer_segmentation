// ============================================================
// ANALYSIS HISTORY CONTROLLER
// CUSTOMER SEGMENTATION & AI MARKETING
// ============================================================

(function () {
    console.log("📜 history.js loaded");

    let currentHistoryPage = 1;
    const historyPageSize = 10;
    let historySearchTimer = null;
    let pendingDeleteId = null;
    let cachedHistoryRecords = {};

    // --------------------------------------------------------
    // HELPER: ESCAPE HTML
    // --------------------------------------------------------
    function escapeHtml(str) {
        if (str === null || str === undefined) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // --------------------------------------------------------
    // HELPER: FORMAT CURRENCY
    // --------------------------------------------------------
    function formatSpend(val) {
        const num = parseFloat(val);
        if (isNaN(num)) return "₹0.00";
        return "₹" + num.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    // --------------------------------------------------------
    // HELPER: FORMAT DATE
    // --------------------------------------------------------
    function formatDateTime(isoStr) {
        if (!isoStr) return "-";
        try {
            const dt = new Date(isoStr);
            if (isNaN(dt.getTime())) return isoStr;
            return dt.toLocaleDateString("en-US", {
                year: "numeric",
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
            });
        } catch (e) {
            return isoStr;
        }
    }

    // --------------------------------------------------------
    // HELPER: SEGMENT BADGE CLASS
    // --------------------------------------------------------
    function getSegmentBadgeClass(segment) {
        if (!segment) return "badge-default";
        const s = segment.toLowerCase();
        if (s.includes("champion")) return "badge-champion";
        if (s.includes("loyal")) return "badge-loyal";
        if (s.includes("potential")) return "badge-potential";
        if (s.includes("risk")) return "badge-atrisk";
        if (s.includes("lose")) return "badge-cantlose";
        if (s.includes("hibernat")) return "badge-hibernating";
        if (s.includes("lost")) return "badge-lost";
        if (s.includes("promis")) return "badge-promising";
        return "badge-general";
    }

    // --------------------------------------------------------
    // LOAD ANALYSIS HISTORY RECORDS
    // --------------------------------------------------------
    async function loadAnalysisHistory(page = 1) {
        currentHistoryPage = page;
        const tbody = document.getElementById("historyTableBody");
        const emptyState = document.getElementById("historyEmptyState");
        const paginationBar = document.getElementById("historyPaginationBar");
        const recordStats = document.getElementById("historyRecordStats");

        if (!tbody) return;

        // Show loading spinner
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="table-loading">
                    <div class="history-spinner"></div>
                    <span style="margin-left: 10px;">Loading analysis history records...</span>
                </td>
            </tr>
        `;
        if (emptyState) emptyState.style.display = "none";
        if (paginationBar) paginationBar.style.display = "none";

        // Gather search and filter values
        const searchInput = document.getElementById("historySearchInput");
        const segmentFilter = document.getElementById("historySegmentFilter");
        const startDateInput = document.getElementById("historyStartDate");
        const endDateInput = document.getElementById("historyEndDate");
        const recFilter = document.getElementById("historyRecFilter");

        const params = new URLSearchParams();
        params.set("page", page);
        params.set("page_size", historyPageSize);

        if (searchInput && searchInput.value.trim()) {
            params.set("search", searchInput.value.trim());
        }
        if (segmentFilter && segmentFilter.value.trim()) {
            params.set("segment", segmentFilter.value.trim());
        }
        if (startDateInput && startDateInput.value.trim()) {
            params.set("start_date", startDateInput.value.trim());
        }
        if (endDateInput && endDateInput.value.trim()) {
            params.set("end_date", endDateInput.value.trim());
        }
        if (recFilter && recFilter.value.trim()) {
            params.set("recommendation_type", recFilter.value.trim());
        }

        try {
            const response = await fetch(`/history?${params.toString()}`);
            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || `Server returned HTTP ${response.status}`);
            }

            const data = await response.json();
            const records = data.records || [];
            const total = data.total || 0;
            const totalPages = data.total_pages || 1;

            cachedHistoryRecords = {};
            records.forEach(r => { cachedHistoryRecords[r.id] = r; });

            if (recordStats) {
                recordStats.textContent = total === 1
                    ? "1 analysis record found"
                    : `${total} analysis records found`;
            }

            if (records.length === 0) {
                tbody.innerHTML = "";
                if (emptyState) emptyState.style.display = "flex";
                if (paginationBar) paginationBar.style.display = "none";
                return;
            }

            if (emptyState) emptyState.style.display = "none";
            renderHistoryRows(records);
            renderPaginationControls(data);

        } catch (error) {
            console.error("❌ Failed to load analysis history:", error);
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="table-error-cell">
                        <div class="history-error-banner">
                            ⚠️ Unable to load analysis history: ${escapeHtml(error.message)}
                            <button type="button" class="btn-retry-history" onclick="loadAnalysisHistory(${page})">
                                ↻ Try Again
                            </button>
                        </div>
                    </td>
                </tr>
            `;
            if (recordStats) recordStats.textContent = "Error loading records";
        }
    }

    // --------------------------------------------------------
    // RENDER TABLE ROWS
    // --------------------------------------------------------
    function renderHistoryRows(records) {
        const tbody = document.getElementById("historyTableBody");
        if (!tbody) return;

        tbody.innerHTML = "";

        records.forEach(record => {
            const tr = document.createElement("tr");
            tr.className = "history-row";

            const segmentClass = getSegmentBadgeClass(record.predicted_segment);
            const formattedDate = formatDateTime(record.analysis_date);
            const recSnippet = record.ai_recommendation_snippet || "Customer segmentation completed.";

            tr.innerHTML = `
                <td>
                    <span class="history-id-badge">#${record.id}</span>
                </td>
                <td>
                    <div class="history-customer-cell">
                        <strong class="cust-name">${escapeHtml(record.customer_name)}</strong>
                        <span class="cust-id-pill">ID: ${escapeHtml(record.customer_id)}</span>
                    </div>
                </td>
                <td>
                    <span class="history-segment-badge ${segmentClass}">
                        ${escapeHtml(record.predicted_segment || "Standard")}
                    </span>
                </td>
                <td>
                    <span class="history-date-cell">
                        📅 ${formattedDate}
                    </span>
                </td>
                <td>
                    <div class="history-rec-cell" title="${escapeHtml(recSnippet)}">
                        <span class="ai-spark-icon">🤖</span>
                        <span class="rec-text">${escapeHtml(recSnippet)}</span>
                    </div>
                </td>
                <td>
                    <span class="history-status-pill status-completed">
                        ✓ ${escapeHtml(record.report_status || "Completed")}
                    </span>
                </td>
                <td>
                    <div class="history-actions-cell">
                        <button
                            type="button"
                            class="action-btn-view"
                            onclick="openViewAnalysisModal(${record.id})"
                            title="View complete analysis details and stored AI recommendations"
                        >
                            👁 View
                        </button>

                        <div class="history-export-dropdown">
                            <button
                                type="button"
                                class="action-btn-download"
                                onclick="toggleHistoryExportMenu(event, ${record.id})"
                                title="Download historical report"
                            >
                                ⬇️ Report ▾
                            </button>
                            <div class="history-export-menu" id="historyExportMenu_${record.id}">
                                <button type="button" onclick="downloadHistoryReport(${record.id}, 'csv')">📄 CSV (.csv)</button>
                                <button type="button" onclick="downloadHistoryReport(${record.id}, 'xlsx')">📊 Excel (.xlsx)</button>
                                <button type="button" onclick="downloadHistoryReport(${record.id}, 'pdf')">📑 PDF (.pdf)</button>
                                <button type="button" onclick="downloadHistoryReport(${record.id}, 'docx')">📝 Word (.docx)</button>
                                <button type="button" onclick="downloadHistoryReport(${record.id}, 'json')">🏷️ JSON (.json)</button>
                            </div>
                        </div>

                        <button
                            type="button"
                            class="action-btn-delete"
                            onclick="openDeleteHistoryModal(${record.id}, '${escapeHtml(record.customer_name)}', '${escapeHtml(record.customer_id)}')"
                            title="Delete this historical analysis record"
                        >
                            🗑️
                        </button>
                    </div>
                </td>
            `;

            tbody.appendChild(tr);
        });
    }

    // --------------------------------------------------------
    // TOGGLE REPORT DOWNLOAD DROPDOWN
    // --------------------------------------------------------
    function toggleHistoryExportMenu(event, recordId) {
        event.stopPropagation();
        // Close other open export menus
        document.querySelectorAll(".history-export-menu.open").forEach(menu => {
            if (menu.id !== `historyExportMenu_${recordId}`) {
                menu.classList.remove("open");
            }
        });

        const targetMenu = document.getElementById(`historyExportMenu_${recordId}`);
        if (targetMenu) {
            targetMenu.classList.toggle("open");
        }
    }

    // Close export menus on window click
    window.addEventListener("click", () => {
        document.querySelectorAll(".history-export-menu.open").forEach(menu => {
            menu.classList.remove("open");
        });
    });

    // --------------------------------------------------------
    // RENDER PAGINATION CONTROLS
    // --------------------------------------------------------
    function renderPaginationControls(data) {
        const paginationBar = document.getElementById("historyPaginationBar");
        const paginationInfo = document.getElementById("historyPaginationInfo");
        const buttonsContainer = document.getElementById("historyPaginationButtons");

        if (!paginationBar || !buttonsContainer) return;

        const total = data.total || 0;
        const page = data.page || 1;
        const totalPages = data.total_pages || 1;

        if (total === 0) {
            paginationBar.style.display = "none";
            return;
        }

        paginationBar.style.display = "flex";

        const startIdx = (page - 1) * historyPageSize + 1;
        const endIdx = Math.min(page * historyPageSize, total);

        if (paginationInfo) {
            paginationInfo.textContent = `Showing ${startIdx}–${endIdx} of ${total} records`;
        }

        buttonsContainer.innerHTML = "";

        // Previous button
        const prevBtn = document.createElement("button");
        prevBtn.type = "button";
        prevBtn.className = "page-nav-btn";
        prevBtn.disabled = page <= 1;
        prevBtn.innerHTML = "« Previous";
        prevBtn.onclick = () => loadAnalysisHistory(page - 1);
        buttonsContainer.appendChild(prevBtn);

        // Page numbers
        let startPage = Math.max(1, page - 2);
        let endPage = Math.min(totalPages, startPage + 4);
        if (endPage - startPage < 4) {
            startPage = Math.max(1, endPage - 4);
        }

        if (startPage > 1) {
            const firstBtn = document.createElement("button");
            firstBtn.type = "button";
            firstBtn.className = "page-num-btn";
            firstBtn.textContent = "1";
            firstBtn.onclick = () => loadAnalysisHistory(1);
            buttonsContainer.appendChild(firstBtn);

            if (startPage > 2) {
                const ellipsis = document.createElement("span");
                ellipsis.className = "page-ellipsis";
                ellipsis.textContent = "…";
                buttonsContainer.appendChild(ellipsis);
            }
        }

        for (let p = startPage; p <= endPage; p++) {
            const pageBtn = document.createElement("button");
            pageBtn.type = "button";
            pageBtn.className = `page-num-btn ${p === page ? "active" : ""}`;
            pageBtn.textContent = p;
            pageBtn.onclick = () => loadAnalysisHistory(p);
            buttonsContainer.appendChild(pageBtn);
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                const ellipsis = document.createElement("span");
                ellipsis.className = "page-ellipsis";
                ellipsis.textContent = "…";
                buttonsContainer.appendChild(ellipsis);
            }
            const lastBtn = document.createElement("button");
            lastBtn.type = "button";
            lastBtn.className = "page-num-btn";
            lastBtn.textContent = totalPages;
            lastBtn.onclick = () => loadAnalysisHistory(totalPages);
            buttonsContainer.appendChild(lastBtn);
        }

        // Next button
        const nextBtn = document.createElement("button");
        nextBtn.type = "button";
        nextBtn.className = "page-nav-btn";
        nextBtn.disabled = page >= totalPages;
        nextBtn.innerHTML = "Next »";
        nextBtn.onclick = () => loadAnalysisHistory(page + 1);
        buttonsContainer.appendChild(nextBtn);
    }

    // --------------------------------------------------------
    // SEARCH & FILTER EVENTS
    // --------------------------------------------------------
    function debounceHistorySearch() {
        if (historySearchTimer) clearTimeout(historySearchTimer);
        historySearchTimer = setTimeout(() => {
            loadAnalysisHistory(1);
        }, 300);
    }

    function applyHistoryFilters() {
        loadAnalysisHistory(1);
    }

    function clearHistoryFilters() {
        const searchInput = document.getElementById("historySearchInput");
        const segmentFilter = document.getElementById("historySegmentFilter");
        const startDateInput = document.getElementById("historyStartDate");
        const endDateInput = document.getElementById("historyEndDate");
        const recFilter = document.getElementById("historyRecFilter");

        if (searchInput) searchInput.value = "";
        if (segmentFilter) segmentFilter.value = "";
        if (startDateInput) startDateInput.value = "";
        if (endDateInput) endDateInput.value = "";
        if (recFilter) recFilter.value = "";

        loadAnalysisHistory(1);
    }

    // --------------------------------------------------------
    // VIEW DETAILED ANALYSIS MODAL
    // --------------------------------------------------------
    async function openViewAnalysisModal(historyId) {
        const modal = document.getElementById("viewAnalysisModal");
        const body = document.getElementById("viewAnalysisModalBody");
        if (!modal || !body) return;

        modal.style.display = "flex";
        body.innerHTML = `
            <div class="history-detail-loading">
                <div class="history-spinner"></div>
                <p>Loading historical analysis details...</p>
            </div>
        `;

        try {
            const response = await fetch(`/history/${historyId}`);
            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail || "Unable to fetch analysis details.");
            }

            const data = await response.json();
            const seg = data.segmentation_data || {};
            const details = data.customer_details || {};
            const segmentClass = getSegmentBadgeClass(data.predicted_segment);
            const formattedDate = formatDateTime(data.analysis_date);

            body.innerHTML = `
                <!-- MODAL HEADER -->
                <div class="history-modal-header">
                    <div>
                        <div class="history-modal-badges">
                            <span class="history-id-badge-lg">Analysis #${data.id}</span>
                            <span class="history-segment-badge ${segmentClass}">${escapeHtml(data.predicted_segment)}</span>
                            <span class="history-status-pill status-completed">✓ Saved Snapshot</span>
                        </div>
                        <h2 class="history-modal-title">
                            ${escapeHtml(data.customer_name || `Customer #${data.customer_id}`)}
                        </h2>
                        <p class="history-modal-sub">
                            Saved on ${formattedDate} • Analyzed by ${escapeHtml(data.username || "System")}
                        </p>
                    </div>
                </div>

                <!-- HISTORICAL NOTICE BANNER -->
                <div class="history-snapshot-banner">
                    <span class="banner-icon">💾</span>
                    <div>
                        <strong>Historical Snapshot Preserved</strong>
                        <p>This view displays the exact customer analysis, RFM scores, and AI recommendations saved on ${formattedDate}. Gemini AI is <em>not</em> re-executed.</p>
                    </div>
                </div>

                <!-- GRID: DETAILS & METRICS -->
                <div class="history-modal-grid">

                    <!-- CARD 1: CUSTOMER DETAILS -->
                    <div class="history-detail-card">
                        <div class="card-header">
                            <span class="card-icon">👤</span>
                            <h4>Customer Details</h4>
                        </div>
                        <div class="detail-rows">
                            <div class="detail-row">
                                <span class="label">Customer ID:</span>
                                <span class="value font-mono">${escapeHtml(data.customer_id)}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Customer Name:</span>
                                <span class="value">${escapeHtml(data.customer_name || "-")}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Age:</span>
                                <span class="value">${details.age ? escapeHtml(details.age) + " yrs" : "Not specified"}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Gender:</span>
                                <span class="value">${details.gender ? escapeHtml(details.gender) : "Not specified"}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Location:</span>
                                <span class="value">${escapeHtml(details.location || "Global")}</span>
                            </div>
                        </div>
                    </div>

                    <!-- CARD 2: RFM METRICS -->
                    <div class="history-detail-card">
                        <div class="card-header">
                            <span class="card-icon">📊</span>
                            <h4>Customer Analysis (RFM)</h4>
                        </div>
                        <div class="detail-metrics-grid">
                            <div class="metric-box">
                                <span class="metric-label">Recency</span>
                                <strong class="metric-val">${seg.recency !== undefined ? seg.recency : "-"}</strong>
                                <span class="metric-unit">days ago</span>
                            </div>
                            <div class="metric-box">
                                <span class="metric-label">Frequency</span>
                                <strong class="metric-val">${seg.frequency !== undefined ? seg.frequency : "-"}</strong>
                                <span class="metric-unit">orders</span>
                            </div>
                            <div class="metric-box">
                                <span class="metric-label">Monetary Spend</span>
                                <strong class="metric-val">${formatSpend(seg.monetary)}</strong>
                                <span class="metric-unit">total spend</span>
                            </div>
                            <div class="metric-box">
                                <span class="metric-label">RFM Score</span>
                                <strong class="metric-val font-mono">${escapeHtml(seg.rfm_score || "-")}</strong>
                                <span class="metric-unit">score</span>
                            </div>
                        </div>
                        <div class="detail-rows" style="margin-top: 14px;">
                            <div class="detail-row">
                                <span class="label">Assigned Campaign:</span>
                                <span class="value">${escapeHtml(seg.campaign || "-")}</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Customer Priority:</span>
                                <span class="value priority-tag priority-${String(seg.priority || 'medium').toLowerCase()}">
                                    ${escapeHtml(seg.priority || "Medium")}
                                </span>
                            </div>
                        </div>
                    </div>

                </div>

                <!-- CARD 3: SEGMENTATION EXPLANATION -->
                <div class="history-detail-card full-width-card" style="margin-top: 16px;">
                    <div class="card-header">
                        <span class="card-icon">🎯</span>
                        <h4>Segmentation Result & Cohort Strategy</h4>
                    </div>
                    <div class="segment-strategy-content">
                        <p class="segment-desc-text">
                            <strong>Predicted Segment:</strong>
                            <span class="history-segment-badge ${segmentClass}" style="margin-left: 6px;">
                                ${escapeHtml(data.predicted_segment)}
                            </span>
                        </p>
                        ${data.segment_explanation ? `
                            <p class="segment-explanation-text">${escapeHtml(data.segment_explanation)}</p>
                        ` : ""}
                        ${data.marketing_strategy ? `
                            <div class="strategy-callout">
                                <strong>Marketing Strategy:</strong>
                                <span>${escapeHtml(data.marketing_strategy)}</span>
                            </div>
                        ` : ""}
                        ${data.recommended_action ? `
                            <div class="action-callout">
                                <strong>Recommended Action:</strong>
                                <span>${escapeHtml(data.recommended_action)}</span>
                            </div>
                        ` : ""}
                    </div>
                </div>

                <!-- CARD 4: AI MARKETING RECOMMENDATION -->
                <div class="history-detail-card full-width-card ai-recommendation-detail-card" style="margin-top: 16px;">
                    <div class="card-header ai-header">
                        <span class="card-icon">🤖</span>
                        <h4>Saved AI Marketing Recommendation</h4>
                        <span class="ai-model-tag">Gemini AI Output</span>
                    </div>
                    <div class="ai-recommendation-body">
                        ${data.ai_recommendation ? `
                            <div class="ai-message-formatted">
                                ${escapeHtml(data.ai_recommendation).replace(/\n/g, '<br>')}
                            </div>
                        ` : `
                            <p class="no-ai-msg">No AI recommendation was recorded for this historical analysis.</p>
                        `}
                    </div>
                </div>

                <!-- MODAL FOOTER & EXPORT OPTIONS -->
                <div class="history-modal-footer">
                    <div class="modal-export-group">
                        <span class="export-label">📥 Download Historical Report:</span>
                        <button type="button" class="btn-format-export" onclick="downloadHistoryReport(${data.id}, 'csv')">
                            📄 CSV
                        </button>
                        <button type="button" class="btn-format-export" onclick="downloadHistoryReport(${data.id}, 'xlsx')">
                            📊 Excel
                        </button>
                        <button type="button" class="btn-format-export" onclick="downloadHistoryReport(${data.id}, 'pdf')">
                            📑 PDF
                        </button>
                        <button type="button" class="btn-format-export" onclick="downloadHistoryReport(${data.id}, 'docx')">
                            📝 Word
                        </button>
                        <button type="button" class="btn-format-export" onclick="downloadHistoryReport(${data.id}, 'json')">
                            🏷️ JSON
                        </button>
                    </div>
                    <button type="button" class="btn-close-modal" onclick="closeViewAnalysisModal()">
                        Close
                    </button>
                </div>
            `;

        } catch (error) {
            console.error("❌ Error fetching analysis detail:", error);
            body.innerHTML = `
                <div class="history-modal-error">
                    <h3>⚠️ Error Loading Analysis</h3>
                    <p>${escapeHtml(error.message)}</p>
                    <button type="button" class="btn-close-modal" onclick="closeViewAnalysisModal()">Close</button>
                </div>
            `;
        }
    }

    function closeViewAnalysisModal() {
        const modal = document.getElementById("viewAnalysisModal");
        if (modal) modal.style.display = "none";
    }

    // --------------------------------------------------------
    // DELETE HISTORY MODAL & ACTION
    // --------------------------------------------------------
    function openDeleteHistoryModal(historyId, customerName, customerId) {
        pendingDeleteId = historyId;
        const modal = document.getElementById("deleteHistoryModal");
        const targetInfo = document.getElementById("deleteHistoryTargetInfo");

        if (targetInfo) {
            targetInfo.innerHTML = `
                <strong>Analysis #${historyId}</strong>
                <span>Customer: ${escapeHtml(customerName)} (ID: ${escapeHtml(customerId)})</span>
            `;
        }

        if (modal) modal.style.display = "flex";
    }

    function closeDeleteHistoryModal() {
        pendingDeleteId = null;
        const modal = document.getElementById("deleteHistoryModal");
        if (modal) modal.style.display = "none";
    }

    async function executeDeleteHistory() {
        if (!pendingDeleteId) return;

        const deleteBtn = document.getElementById("confirmDeleteHistoryBtn");
        const originalText = deleteBtn ? deleteBtn.innerHTML : "Delete";

        if (deleteBtn) {
            deleteBtn.disabled = true;
            deleteBtn.innerHTML = "⏳ Deleting...";
        }

        try {
            const response = await fetch(`/history/${pendingDeleteId}`, {
                method: "DELETE",
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail || `Server returned HTTP ${response.status}`);
            }

            closeDeleteHistoryModal();
            showHistoryToast("✅ Analysis history record deleted successfully.");
            loadAnalysisHistory(currentHistoryPage);

        } catch (error) {
            console.error("❌ Delete failed:", error);
            alert(`Unable to delete analysis record:\n\n${error.message}`);
        } finally {
            if (deleteBtn) {
                deleteBtn.disabled = false;
                deleteBtn.innerHTML = originalText;
            }
        }
    }

    // --------------------------------------------------------
    // DOWNLOAD HISTORICAL REPORT
    // --------------------------------------------------------
    function downloadHistoryReport(historyId, format) {
        // Close export menus if open
        document.querySelectorAll(".history-export-menu.open").forEach(m => m.classList.remove("open"));

        showHistoryToast(`📥 Generating historical ${format.toUpperCase()} report...`);
        const downloadUrl = `/history/${historyId}/export/${encodeURIComponent(format)}`;

        // Trigger native download
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.style.display = "none";
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
            document.body.removeChild(a);
        }, 1000);
    }

    // --------------------------------------------------------
    // NOTIFICATION TOAST
    // --------------------------------------------------------
    function showHistoryToast(message) {
        let toast = document.getElementById("historyToast");
        if (!toast) {
            toast = document.createElement("div");
            toast.id = "historyToast";
            toast.className = "history-toast";
            document.body.appendChild(toast);
        }

        toast.textContent = message;
        toast.classList.add("visible");

        setTimeout(() => {
            toast.classList.remove("visible");
        }, 3500);
    }

    // --------------------------------------------------------
    // EXPOSE GLOBALLY TO WINDOW
    // --------------------------------------------------------
    window.loadAnalysisHistory = loadAnalysisHistory;
    window.debounceHistorySearch = debounceHistorySearch;
    window.applyHistoryFilters = applyHistoryFilters;
    window.clearHistoryFilters = clearHistoryFilters;
    window.openViewAnalysisModal = openViewAnalysisModal;
    window.closeViewAnalysisModal = closeViewAnalysisModal;
    window.openDeleteHistoryModal = openDeleteHistoryModal;
    window.closeDeleteHistoryModal = closeDeleteHistoryModal;
    window.executeDeleteHistory = executeDeleteHistory;
    window.downloadHistoryReport = downloadHistoryReport;
    window.toggleHistoryExportMenu = toggleHistoryExportMenu;

})();
