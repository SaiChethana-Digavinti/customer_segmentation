// ============================================================
// CUSTOMER AI - ADMINISTRATION MANAGEMENT
// frontend/js/admin.js
// ============================================================

let currentAdminTab = "users";

// ------------------------------------------------------------
// LOAD FULL ADMIN DASHBOARD
// ------------------------------------------------------------

async function loadAdminDashboard() {
    console.log("🛡️ Loading Admin Center...");
    const currentUser = getCurrentUser();
    if (!currentUser || (currentUser.role || "").toLowerCase() !== "admin") {
        console.warn("⚠️ Non-admin access attempt blocked.");
        if (typeof showSection === "function") {
            showSection("dashboard");
        }
        return;
    }

    await Promise.allSettled([
        loadAdminStats(),
        loadAdminUsers(),
        loadAdminAuditLogs(),
        loadAdminDatasetRuns(),
    ]);
}

// ------------------------------------------------------------
// ADMIN STATS / KPIS
// ------------------------------------------------------------

async function loadAdminStats() {
    try {
        const response = await fetch("/admin/stats");
        if (!response.ok) throw new Error("Failed to load admin statistics.");
        const data = await response.json();

        // Update KPI values
        const totalUsersEl = document.getElementById("adminTotalUsers");
        const activeUsersEl = document.getElementById("adminActiveUsers");
        const roleDistEl = document.getElementById("adminRoleDist");
        const totalCustEl = document.getElementById("adminTotalCustomers");
        const totalRunsEl = document.getElementById("adminTotalRuns");
        const dbStatusEl = document.getElementById("adminDbStatus");
        const systemStatusEl = document.getElementById("adminSystemStatus");

        if (totalUsersEl) totalUsersEl.textContent = data.total_users ?? 0;
        if (activeUsersEl) activeUsersEl.textContent = `${data.active_users ?? 0} active`;
        if (roleDistEl) roleDistEl.textContent = `${data.admin_users ?? 0} Admin / ${data.analyst_users ?? 0} Analyst`;
        if (totalCustEl) totalCustEl.textContent = (data.total_customers ?? 0).toLocaleString();
        if (totalRunsEl) totalRunsEl.textContent = data.total_dataset_runs ?? 0;
        if (dbStatusEl) {
            dbStatusEl.textContent = data.db_status || "Healthy";
            dbStatusEl.className = data.db_status.includes("Healthy") ? "status-healthy" : "status-warning";
        }
        if (systemStatusEl) systemStatusEl.textContent = data.system_status || "Operational";
    } catch (err) {
        console.error("Admin stats error:", err);
    }
}

// ------------------------------------------------------------
// USER MANAGEMENT - LOAD USERS
// ------------------------------------------------------------

async function loadAdminUsers() {
    const tbody = document.getElementById("adminUsersTableBody");
    if (!tbody) return;

    try {
        tbody.innerHTML = `<tr><td colspan="7" class="table-loading">⏳ Loading users...</td></tr>`;
        const response = await fetch("/admin/users");
        if (!response.ok) throw new Error("Could not fetch users list.");
        const users = await response.json();

        if (!users || users.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="table-empty">No users found.</td></tr>`;
            return;
        }

        const currentLoggedInUser = getCurrentUser();

        tbody.innerHTML = users.map(user => {
            const isSelf = currentLoggedInUser && currentLoggedInUser.id === user.id;
            const isAdmin = (user.role || "").toLowerCase() === "admin";
            const initial = (user.full_name || user.username || "U").charAt(0).toUpperCase();

            const createdDate = user.created_at
                ? new Date(user.created_at).toLocaleDateString("en-IN", { month: "short", day: "numeric", year: "numeric" })
                : "N/A";

            const lastLoginDate = user.last_login
                ? new Date(user.last_login).toLocaleString("en-IN", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
                : "Never";

            return `
                <tr>
                    <td>
                        <div class="user-meta-cell">
                            <div class="user-avatar-sm">${escapeHTML(initial)}</div>
                            <div>
                                <div class="user-fullname">${escapeHTML(user.full_name || user.username)} ${isSelf ? '<span class="self-tag">(You)</span>' : ''}</div>
                                <div class="user-handle">@${escapeHTML(user.username)}</div>
                            </div>
                        </div>
                    </td>
                    <td>${escapeHTML(user.email)}</td>
                    <td>
                        <span class="role-pill ${isAdmin ? 'role-admin' : 'role-analyst'}">
                            ${isAdmin ? '👑 ADMIN' : '📊 ANALYST'}
                        </span>
                    </td>
                    <td>
                        <span class="status-pill ${user.is_active ? 'status-active' : 'status-disabled'}">
                            ${user.is_active ? '● Active' : '○ Disabled'}
                        </span>
                    </td>
                    <td><span class="date-text">${createdDate}</span></td>
                    <td><span class="date-text">${lastLoginDate}</span></td>
                    <td>
                        <div class="admin-actions-cell">
                            <button 
                                type="button" 
                                class="btn-action btn-role" 
                                title="Change Role"
                                onclick="toggleUserRole(${user.id}, '${user.role}')"
                                ${isSelf && isAdmin ? 'disabled title="Cannot demote yourself"' : ''}
                            >
                                🔄 ${isAdmin ? 'Make Analyst' : 'Make Admin'}
                            </button>
                            <button 
                                type="button" 
                                class="btn-action ${user.is_active ? 'btn-deactivate' : 'btn-activate'}" 
                                title="${user.is_active ? 'Disable account' : 'Enable account'}"
                                onclick="toggleUserStatus(${user.id}, ${user.is_active})"
                                ${isSelf ? 'disabled title="Cannot disable your own account"' : ''}
                            >
                                ${user.is_active ? '🚫 Deactivate' : '✅ Activate'}
                            </button>
                            <button 
                                type="button" 
                                class="btn-action btn-delete" 
                                title="Delete user"
                                onclick="deleteUser(${user.id}, '${escapeAttribute(user.username)}')"
                                ${isSelf ? 'disabled title="Cannot delete yourself"' : ''}
                            >
                                🗑️
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="table-error">⚠️ ${escapeHTML(err.message)}</td></tr>`;
    }
}

// ------------------------------------------------------------
// TOGGLE USER ROLE
// ------------------------------------------------------------

async function toggleUserRole(userId, currentRole) {
    const newRole = currentRole.toLowerCase() === "admin" ? "analyst" : "admin";
    const roleLabel = newRole === "admin" ? "Administrator" : "Analyst";

    if (!confirm(`Are you sure you want to change this user's role to ${roleLabel}?`)) {
        return;
    }

    try {
        const response = await fetch(`/admin/users/${userId}/role`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ role: newRole })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Failed to update role.");

        await Promise.all([loadAdminUsers(), loadAdminStats(), loadAdminAuditLogs()]);
    } catch (err) {
        alert(`Error updating role: ${err.message}`);
    }
}

// ------------------------------------------------------------
// TOGGLE USER STATUS (ACTIVE/DISABLED)
// ------------------------------------------------------------

async function toggleUserStatus(userId, currentStatus) {
    const newStatus = !currentStatus;
    const actionLabel = newStatus ? "activate" : "deactivate";

    if (!confirm(`Are you sure you want to ${actionLabel} this user account?`)) {
        return;
    }

    try {
        const response = await fetch(`/admin/users/${userId}/status`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_active: newStatus })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Failed to update status.");

        await Promise.all([loadAdminUsers(), loadAdminStats(), loadAdminAuditLogs()]);
    } catch (err) {
        alert(`Error updating status: ${err.message}`);
    }
}

// ------------------------------------------------------------
// DELETE USER
// ------------------------------------------------------------

async function deleteUser(userId, username) {
    if (!confirm(`⚠️ Are you sure you want to permanently delete user "@${username}"? This action cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`/admin/users/${userId}`, {
            method: "DELETE"
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Failed to delete user.");

        await Promise.all([loadAdminUsers(), loadAdminStats(), loadAdminAuditLogs()]);
    } catch (err) {
        alert(`Error deleting user: ${err.message}`);
    }
}

// ------------------------------------------------------------
// ADD USER MODAL CONTROLS
// ------------------------------------------------------------

function openAddUserModal() {
    const modal = document.getElementById("adminAddUserModal");
    const errorEl = document.getElementById("adminAddUserError");
    if (errorEl) errorEl.style.display = "none";
    if (modal) {
        modal.style.display = "flex";
        document.body.style.overflow = "hidden";
        setTimeout(() => {
            document.getElementById("adminNewFullName")?.focus();
        }, 50);
    }
}

function closeAddUserModal() {
    const modal = document.getElementById("adminAddUserModal");
    if (modal) {
        modal.style.display = "none";
        document.body.style.overflow = "";
    }
    const form = document.getElementById("adminAddUserForm");
    if (form) form.reset();
}

// Close modal when clicking outside the content card on the backdrop
document.addEventListener("click", function(event) {
    const modal = document.getElementById("adminAddUserModal");
    if (modal && event.target === modal) {
        closeAddUserModal();
    }
});

async function handleAdminCreateUser(event) {
    if (event) event.preventDefault();
    const errorEl = document.getElementById("adminAddUserError");
    const submitBtn = document.getElementById("adminAddUserSubmitBtn");
    if (errorEl) errorEl.style.display = "none";

    const full_name = document.getElementById("adminNewFullName")?.value.trim();
    const username = document.getElementById("adminNewUsername")?.value.trim();
    const email = document.getElementById("adminNewEmail")?.value.trim();
    const password = document.getElementById("adminNewPassword")?.value;
    const role = document.getElementById("adminNewRole")?.value || "analyst";

    if (!full_name || !username || !email || !password) {
        if (errorEl) {
            errorEl.textContent = "Please fill in all required fields.";
            errorEl.style.display = "block";
        }
        return;
    }

    try {
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = "⏳ Creating...";
        }

        const response = await fetch("/admin/users", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ full_name, username, email, password, role, is_active: true })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Failed to create user.");

        closeAddUserModal();
        await Promise.all([loadAdminUsers(), loadAdminStats(), loadAdminAuditLogs()]);
    } catch (err) {
        if (errorEl) {
            errorEl.textContent = err.message;
            errorEl.style.display = "block";
        }
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = "✨ Create User";
        }
    }
}

// ------------------------------------------------------------
// AUDIT LOGS TRAIL
// ------------------------------------------------------------

async function loadAdminAuditLogs(actionFilter = "") {
    const tbody = document.getElementById("adminAuditLogsTableBody");
    if (!tbody) return;

    try {
        tbody.innerHTML = `<tr><td colspan="5" class="table-loading">⏳ Loading audit logs...</td></tr>`;
        const url = actionFilter
            ? `/admin/audit-logs?limit=50&action=${encodeURIComponent(actionFilter)}`
            : `/admin/audit-logs?limit=50`;

        const response = await fetch(url);
        if (!response.ok) throw new Error("Could not fetch audit logs.");
        const logs = await response.json();

        if (!logs || logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="table-empty">No activity logs recorded yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = logs.map(log => {
            const timeStr = log.created_at
                ? new Date(log.created_at).toLocaleString("en-IN", {
                    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit"
                })
                : "N/A";

            let actionBadgeClass = "badge-info";
            if (log.action.includes("LOGIN")) actionBadgeClass = "badge-login";
            if (log.action.includes("USER")) actionBadgeClass = "badge-user";
            if (log.action.includes("DELETE") || log.action.includes("BLOCK")) actionBadgeClass = "badge-danger";
            if (log.action.includes("DATASET") || log.action.includes("SEGMENT")) actionBadgeClass = "badge-dataset";

            return `
                <tr>
                    <td><span class="date-text font-mono">${timeStr}</span></td>
                    <td><strong>@${escapeHTML(log.username)}</strong></td>
                    <td><span class="log-badge ${actionBadgeClass}">${escapeHTML(log.action)}</span></td>
                    <td>
                        <span class="status-indicator ${log.status === 'SUCCESS' ? 'text-success' : 'text-danger'}">
                            ${log.status === 'SUCCESS' ? '✓ Success' : '✗ ' + escapeHTML(log.status)}
                        </span>
                    </td>
                    <td class="log-details-cell">${escapeHTML(log.details || "-")}</td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="5" class="table-error">⚠️ ${escapeHTML(err.message)}</td></tr>`;
    }
}

// ------------------------------------------------------------
// DATASET RUNS HISTORY
// ------------------------------------------------------------

async function loadAdminDatasetRuns() {
    const tbody = document.getElementById("adminDatasetRunsTableBody");
    if (!tbody) return;

    try {
        tbody.innerHTML = `<tr><td colspan="6" class="table-loading">⏳ Loading dataset runs...</td></tr>`;
        const response = await fetch("/admin/dataset-runs?limit=20");
        if (!response.ok) throw new Error("Could not fetch dataset runs.");
        const runs = await response.json();

        if (!runs || runs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="table-empty">No dataset runs recorded yet. Upload a dataset to see history.</td></tr>`;
            return;
        }

        tbody.innerHTML = runs.map(run => {
            const timeStr = run.created_at
                ? new Date(run.created_at).toLocaleString("en-IN", {
                    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"
                })
                : "N/A";

            return `
                <tr>
                    <td>#${run.id}</td>
                    <td><strong>📁 ${escapeHTML(run.filename)}</strong></td>
                    <td>${(run.row_count || 0).toLocaleString()} rows</td>
                    <td><span class="status-pill status-active">${escapeHTML(run.status || "COMPLETED")}</span></td>
                    <td><span class="model-badge">${escapeHTML(run.best_method || "K-Means")}</span></td>
                    <td><span class="date-text">${timeStr}</span></td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="table-error">⚠️ ${escapeHTML(err.message)}</td></tr>`;
    }
}

// ------------------------------------------------------------
// SYSTEM MAINTENANCE - CLEAR CACHE
// ------------------------------------------------------------

async function triggerClearCache() {
    if (!confirm("Flush system application cache and refresh database connections?")) {
        return;
    }

    try {
        const response = await fetch("/admin/maintenance/clear-cache", { method: "POST" });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Failed to clear cache.");
        alert("✅ " + (data.message || "System cache refreshed successfully."));
        await Promise.all([loadAdminStats(), loadAdminAuditLogs()]);
    } catch (err) {
        alert("⚠️ " + err.message);
    }
}

// ------------------------------------------------------------
// EXPORT CUSTOMER DATA TO JSON
// ------------------------------------------------------------

async function exportCustomerData() {
    try {
        const response = await fetch("/customers/all?limit=1000");
        if (!response.ok) throw new Error("Could not fetch customers data.");
        const data = await response.json();

        const jsonStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
        const downloadAnchor = document.createElement("a");
        downloadAnchor.setAttribute("href", jsonStr);
        downloadAnchor.setAttribute("download", `customer_export_${new Date().toISOString().slice(0, 10)}.json`);
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
    } catch (err) {
        alert("Export failed: " + err.message);
    }
}

// ------------------------------------------------------------
// ADMIN TAB SWITCHER
// ------------------------------------------------------------

function switchAdminTab(tabName) {
    currentAdminTab = tabName;
    const tabButtons = document.querySelectorAll(".admin-tab-btn");
    const tabPanels = document.querySelectorAll(".admin-tab-panel");

    tabButtons.forEach(btn => {
        btn.classList.toggle("active", btn.dataset.tab === tabName);
    });

    tabPanels.forEach(panel => {
        panel.classList.toggle("active", panel.id === `adminTabPanel-${tabName}`);
    });
}

// Window exports
window.loadAdminDashboard = loadAdminDashboard;
window.loadAdminStats = loadAdminStats;
window.loadAdminUsers = loadAdminUsers;
window.toggleUserRole = toggleUserRole;
window.toggleUserStatus = toggleUserStatus;
window.deleteUser = deleteUser;
window.openAddUserModal = openAddUserModal;
window.closeAddUserModal = closeAddUserModal;
window.handleAdminCreateUser = handleAdminCreateUser;
window.loadAdminAuditLogs = loadAdminAuditLogs;
window.loadAdminDatasetRuns = loadAdminDatasetRuns;
window.triggerClearCache = triggerClearCache;
window.exportCustomerData = exportCustomerData;
window.switchAdminTab = switchAdminTab;
