// ============================================================
// CUSTOMER AI - AUTHENTICATION & SESSION MANAGEMENT
// frontend/js/auth.js
// ============================================================

const AUTH_TOKEN_KEY = "customer_ai_token";
const AUTH_USER_KEY = "customer_ai_user";

// ------------------------------------------------------------
// STATE HELPERS
// ------------------------------------------------------------

function getAuthToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

function getCurrentUser() {
    const raw = localStorage.getItem(AUTH_USER_KEY);
    if (!raw) return null;
    try {
        return JSON.parse(raw);
    } catch {
        return null;
    }
}

function setAuthSession(token, user) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

function clearAuthSession() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
}

// ------------------------------------------------------------
// GLOBAL FETCH INTERCEPTOR
// Injects Authorization Bearer Token automatically
// ------------------------------------------------------------

(function setupFetchInterceptor() {
    const originalFetch = window.fetch;
    window.fetch = async function(resource, config = {}) {
        const token = getAuthToken();
        const newConfig = { ...config };

        newConfig.headers = new Headers(newConfig.headers || {});
        if (token && !newConfig.headers.has("Authorization")) {
            newConfig.headers.set("Authorization", `Bearer ${token}`);
        }

        try {
            const response = await originalFetch(resource, newConfig);

            // Handle unauthorized responses (token expired / invalid)
            if (response.status === 401) {
                const url = typeof resource === "string" ? resource : resource.url || "";
                if (!url.includes("/auth/login") && !url.includes("/auth/register")) {
                    console.warn("🔒 Session expired. Redirecting to login...");
                    clearAuthSession();
                    updateAuthUI(null);
                    showAuthError("Session expired. Please sign in again.");
                }
            }

            return response;
        } catch (err) {
            throw err;
        }
    };
})();

// ------------------------------------------------------------
// UPDATE AUTH UI STATE
// ------------------------------------------------------------

function updateAuthUI(user) {
    const authOverlay = document.getElementById("authOverlay");
    const userProfileWidget = document.getElementById("userProfileWidget");
    const adminNavBtn = document.getElementById("adminNavButton");
    const userNameDisplay = document.getElementById("userNameDisplay");
    const userRoleBadge = document.getElementById("userRoleBadge");
    const userAvatarText = document.getElementById("userAvatarText");

    if (user && user.username) {
        // Logged In
        if (authOverlay) {
            authOverlay.classList.remove("visible");
            authOverlay.style.display = "none";
        }
        if (userProfileWidget) {
            userProfileWidget.style.display = "flex";
        }

        // Display user details
        if (userNameDisplay) {
            userNameDisplay.textContent = user.full_name || user.username;
        }
        if (userAvatarText) {
            const initial = (user.full_name || user.username || "U").charAt(0).toUpperCase();
            userAvatarText.textContent = initial;
        }

        const isAdmin = (user.role || "").toLowerCase() === "admin";
        if (userRoleBadge) {
            userRoleBadge.textContent = isAdmin ? "ADMIN" : "ANALYST";
            userRoleBadge.className = `role-pill ${isAdmin ? "role-admin" : "role-analyst"}`;
        }

        // Show/Hide Admin Tab in Sidebar
        if (adminNavBtn) {
            adminNavBtn.style.display = isAdmin ? "block" : "none";
        }
    } else {
        // Logged Out
        if (authOverlay) {
            authOverlay.style.display = "flex";
            authOverlay.classList.add("visible");
        }
        if (userProfileWidget) {
            userProfileWidget.style.display = "none";
        }
        if (adminNavBtn) {
            adminNavBtn.style.display = "none";
        }
    }
}

// ------------------------------------------------------------
// ROLE & VIEW SWITCHER (Role Select, Admin Login, Analyst Login, Register)
// ------------------------------------------------------------

function selectAuthRole(role = "select") {
    clearAuthMessages();
    const views = {
        select: document.getElementById("authRoleSelectView"),
        admin: document.getElementById("authAdminLoginView"),
        analyst: document.getElementById("authAnalystLoginView"),
        register: document.getElementById("authRegisterView"),
    };

    // Hide all views
    Object.values(views).forEach(v => {
        if (v) {
            v.style.display = "none";
            v.classList.remove("active-view");
        }
    });

    // Show targeted view
    const activeView = views[role] || views.select;
    if (activeView) {
        activeView.style.display = "block";
        // Trigger smooth entry animation
        activeView.classList.add("active-view");
    }

    // Auto-focus first input in active form
    setTimeout(() => {
        if (role === "admin") {
            document.getElementById("adminUsername")?.focus();
        } else if (role === "analyst") {
            document.getElementById("analystUsername")?.focus();
        } else if (role === "register") {
            document.getElementById("regFullName")?.focus();
        }
    }, 100);
}

// Backward-compatible alias for existing callers
function switchAuthTab(tab) {
    if (tab === "register") {
        selectAuthRole("register");
    } else {
        selectAuthRole("analyst");
    }
}

// ------------------------------------------------------------
// PASSWORD VISIBILITY TOGGLE
// ------------------------------------------------------------

function togglePasswordVisibility(inputId, btnId) {
    const input = document.getElementById(inputId);
    const btn = document.getElementById(btnId);
    if (!input) return;

    if (input.type === "password") {
        input.type = "text";
        if (btn) {
            btn.innerHTML = "🙈";
            btn.setAttribute("title", "Hide password");
            btn.setAttribute("aria-label", "Hide password");
        }
    } else {
        input.type = "password";
        if (btn) {
            btn.innerHTML = "👁️";
            btn.setAttribute("title", "Show password");
            btn.setAttribute("aria-label", "Show password");
        }
    }
}

// ------------------------------------------------------------
// ERROR & MESSAGE HELPERS
// ------------------------------------------------------------

function showAuthError(message) {
    const errorEl = document.getElementById("authError");
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.style.display = "block";
        errorEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
}

function showAuthSuccess(message) {
    const successEl = document.getElementById("authSuccess");
    if (successEl) {
        successEl.textContent = message;
        successEl.style.display = "block";
    }
}

function clearAuthMessages() {
    const errorEl = document.getElementById("authError");
    const successEl = document.getElementById("authSuccess");
    if (errorEl) errorEl.style.display = "none";
    if (successEl) successEl.style.display = "none";
}

// ------------------------------------------------------------
// LOGIN HANDLER (Supports Admin, Analyst, or General Login)
// ------------------------------------------------------------

async function handleRoleLogin(event, role = "analyst") {
    if (event) event.preventDefault();
    clearAuthMessages();

    let usernameInput = null;
    let passwordInput = null;
    let submitBtn = null;

    if (role === "admin") {
        usernameInput = document.getElementById("adminUsername");
        passwordInput = document.getElementById("adminPassword");
        submitBtn = document.getElementById("adminSubmitBtn");
    } else if (role === "analyst") {
        usernameInput = document.getElementById("analystUsername");
        passwordInput = document.getElementById("analystPassword");
        submitBtn = document.getElementById("analystSubmitBtn");
    } else {
        usernameInput = document.getElementById("loginUsername") || document.getElementById("analystUsername");
        passwordInput = document.getElementById("loginPassword") || document.getElementById("analystPassword");
        submitBtn = document.getElementById("loginSubmitBtn") || document.getElementById("analystSubmitBtn");
    }

    const username = usernameInput?.value.trim();
    const password = passwordInput?.value;

    if (!username || !password) {
        showAuthError("Please enter both username and password.");
        return;
    }

    const origBtnHtml = submitBtn ? submitBtn.innerHTML : "Sign In";

    try {
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = "⏳ Authenticating...";
        }

        const response = await fetch("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Authentication failed. Please check your credentials.");
        }

        // Save session
        setAuthSession(data.access_token, data.user);
        updateAuthUI(data.user);

        // Clear sensitive inputs
        if (passwordInput) passwordInput.value = "";

        showAuthSuccess(`Welcome back, ${data.user.full_name || data.user.username}!`);

        setTimeout(() => {
            if (typeof showSection === "function") {
                showSection("dashboard");
            }
        }, 500);

    } catch (err) {
        showAuthError(err.message);
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = origBtnHtml;
        }
    }
}

// Backward compatibility alias for handleLogin
async function handleLogin(event) {
    // Check which view is currently active
    const adminView = document.getElementById("authAdminLoginView");
    if (adminView && adminView.style.display !== "none") {
        return handleRoleLogin(event, "admin");
    }
    return handleRoleLogin(event, "analyst");
}

// ------------------------------------------------------------
// REGISTER HANDLER (With Confirm Password & Validation)
// ------------------------------------------------------------

async function handleRegister(event) {
    if (event) event.preventDefault();
    clearAuthMessages();

    const fullNameInput = document.getElementById("regFullName");
    const usernameInput = document.getElementById("regUsername");
    const emailInput = document.getElementById("regEmail");
    const passwordInput = document.getElementById("regPassword");
    const confirmPasswordInput = document.getElementById("regConfirmPassword");
    const roleSelect = document.getElementById("regRole");
    const submitBtn = document.getElementById("regSubmitBtn");

    const full_name = fullNameInput?.value.trim();
    const username = usernameInput?.value.trim();
    const email = emailInput?.value.trim();
    const password = passwordInput?.value;
    const confirmPassword = confirmPasswordInput?.value;
    const role = roleSelect?.value || "analyst";

    if (!full_name || !username || !email || !password) {
        showAuthError("Please fill out all required fields.");
        return;
    }

    if (password.length < 6) {
        showAuthError("Password must be at least 6 characters long.");
        return;
    }

    if (confirmPassword !== undefined && password !== confirmPassword) {
        showAuthError("Passwords do not match. Please re-enter your password.");
        return;
    }

    const origBtnHtml = submitBtn ? submitBtn.innerHTML : "Create Account";

    try {
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = "⏳ Creating Account...";
        }

        const response = await fetch("/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ full_name, username, email, password, role })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Registration failed.");
        }

        // Save session
        setAuthSession(data.access_token, data.user);
        updateAuthUI(data.user);

        showAuthSuccess("🎉 Account created successfully! Launching dashboard...");
        setTimeout(() => {
            if (typeof showSection === "function") {
                showSection("dashboard");
            }
        }, 700);
    } catch (err) {
        showAuthError(err.message);
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = origBtnHtml;
        }
    }
}

// ------------------------------------------------------------
// LOGOUT HANDLER
// ------------------------------------------------------------

async function handleLogout() {
    try {
        await fetch("/auth/logout", { method: "POST" });
    } catch (err) {
        console.warn("Logout notification error:", err);
    }

    clearAuthSession();
    updateAuthUI(null);
    selectAuthRole("select");
    clearAuthMessages();
}

// ------------------------------------------------------------
// DEMO CREDENTIALS QUICK FILL
// ------------------------------------------------------------

function fillDemoCredentials(role) {
    if (role === "admin") {
        selectAuthRole("admin");
        const usernameInput = document.getElementById("adminUsername");
        const passwordInput = document.getElementById("adminPassword");
        if (usernameInput) usernameInput.value = "admin";
        if (passwordInput) passwordInput.value = "admin123";
        // Auto sign in for instant convenience
        handleRoleLogin(null, "admin");
    } else {
        selectAuthRole("analyst");
        const usernameInput = document.getElementById("analystUsername");
        const passwordInput = document.getElementById("analystPassword");
        if (usernameInput) usernameInput.value = "analyst";
        if (passwordInput) passwordInput.value = "user123";
        // Auto sign in for instant convenience
        handleRoleLogin(null, "analyst");
    }
}

// ------------------------------------------------------------
// SESSION CHECK ON LOAD
// ------------------------------------------------------------

async function checkAuthSession() {
    const token = getAuthToken();
    if (!token) {
        updateAuthUI(null);
        return;
    }

    try {
        const response = await fetch("/auth/me");
        if (!response.ok) {
            throw new Error("Session invalid");
        }
        const user = await response.json();
        // Update stored profile
        localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
        updateAuthUI(user);
    } catch (err) {
        console.warn("Session check failed, clearing token:", err);
        clearAuthSession();
        updateAuthUI(null);
    }
}

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
    checkAuthSession();
});

// Window exports
window.getAuthToken = getAuthToken;
window.getCurrentUser = getCurrentUser;
window.selectAuthRole = selectAuthRole;
window.togglePasswordVisibility = togglePasswordVisibility;
window.handleLogin = handleLogin;
window.handleRoleLogin = handleRoleLogin;
window.handleRegister = handleRegister;
window.handleLogout = handleLogout;
window.fillDemoCredentials = fillDemoCredentials;
window.switchAuthTab = switchAuthTab;
