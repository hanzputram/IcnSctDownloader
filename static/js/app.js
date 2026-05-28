/**
 * IconScout Bot - Main Application
 * SPA Router, API Client, State Management, Utilities
 */

// =========================================================
// API Client
// =========================================================
const API = {
    base: '',

    async get(path) {
        try {
            const res = await fetch(`${this.base}${path}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (e) {
            console.error(`GET ${path}:`, e);
            throw e;
        }
    },

    async post(path, body = {}) {
        try {
            const res = await fetch(`${this.base}${path}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || `HTTP ${res.status}`);
            }
            return await res.json();
        } catch (e) {
            console.error(`POST ${path}:`, e);
            throw e;
        }
    },

    async put(path, body = {}) {
        try {
            const res = await fetch(`${this.base}${path}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.detail || `HTTP ${res.status}`);
            }
            return await res.json();
        } catch (e) {
            console.error(`PUT ${path}:`, e);
            throw e;
        }
    },

    async del(path) {
        try {
            const res = await fetch(`${this.base}${path}`, { method: 'DELETE' });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch (e) {
            console.error(`DELETE ${path}:`, e);
            throw e;
        }
    },
};


// =========================================================
// State
// =========================================================
const State = {
    currentPage: 'dashboard',
    stats: null,
    accounts: [],
    tasks: [],
    schedules: [],
    logs: [],
    refreshInterval: null,
};


// =========================================================
// Router
// =========================================================
function navigate(page) {
    State.currentPage = page;

    // Update sidebar
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.page === page);
    });

    // Render page
    const pageContent = document.getElementById('pageContent');
    pageContent.innerHTML = '<div class="loading-overlay"><div class="spinner spinner-lg"></div><span>Loading...</span></div>';

    setTimeout(() => {
        switch (page) {
            case 'dashboard': renderDashboard(); break;
            case 'accounts': renderAccounts(); break;
            case 'tasks': renderTasks(); break;
            case 'scheduler': renderScheduler(); break;
            case 'logs': renderLogs(); break;
            case 'settings': renderSettings(); break;
            default: renderDashboard();
        }
    }, 100);

    // Update URL hash
    window.location.hash = page;
}


// =========================================================
// Toast Notifications
// =========================================================
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}


// =========================================================
// Modal
// =========================================================
function showModal(title, bodyHtml, footerHtml = '') {
    const overlay = document.getElementById('modalOverlay');
    const content = document.getElementById('modalContent');

    content.innerHTML = `
        <div class="modal-header">
            <h3 class="modal-title">${title}</h3>
            <button class="modal-close" onclick="closeModal()">✕</button>
        </div>
        <div class="modal-body">${bodyHtml}</div>
        ${footerHtml ? `<div class="modal-footer">${footerHtml}</div>` : ''}
    `;

    overlay.classList.add('show');
}

function closeModal(e) {
    if (e && e.target !== e.currentTarget) return;
    document.getElementById('modalOverlay').classList.remove('show');
}


// =========================================================
// Utilities
// =========================================================
function formatDate(isoStr) {
    if (!isoStr) return '—';
    const d = new Date(isoStr);
    return d.toLocaleDateString('id-ID', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
    });
}

function formatSize(bytes) {
    if (!bytes) return '—';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(2)} MB`;
}

function truncate(str, len = 40) {
    if (!str) return '—';
    return str.length > len ? str.substring(0, len) + '…' : str;
}

function statusBadge(status) {
    return `<span class="badge ${status}">${status}</span>`;
}


// =========================================================
// Quick Download (Sidebar shortcut)
// =========================================================
function quickDownload() {
    showModal('⚡ Quick Download', `
        <div class="form-group">
            <label class="form-label">IconScout URL</label>
            <input type="text" class="form-input" id="quickUrl" placeholder="https://iconscout.com/icon/...">
        </div>
        <div class="form-row">
            <div class="form-group">
                <label class="form-label">Format</label>
                <select class="form-select" id="quickFormat">
                    <option value="png">PNG</option>
                    <option value="svg">SVG</option>
                    <option value="eps">EPS</option>
                    <option value="pdf">PDF</option>
                    <option value="json">Lottie JSON</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Account</label>
                <select class="form-select" id="quickAccount">
                    <option value="">Auto (first active)</option>
                </select>
            </div>
        </div>
    `, `
        <button class="btn btn-ghost" onclick="closeModal()">Batal</button>
        <button class="btn btn-primary" onclick="submitQuickDownload()">🚀 Download</button>
    `);

    // Load accounts into dropdown
    loadAccountsDropdown('quickAccount');
}

async function loadAccountsDropdown(selectId) {
    try {
        const data = await API.get('/api/accounts');
        const select = document.getElementById(selectId);
        if (!select) return;

        // Keep the first option
        const firstOption = select.querySelector('option');
        select.innerHTML = '';
        if (firstOption) select.appendChild(firstOption);

        (data.data || []).forEach(acc => {
            const opt = document.createElement('option');
            opt.value = acc.id;
            opt.textContent = `${acc.email} (${acc.status})`;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error('Load accounts dropdown:', e);
    }
}

async function submitQuickDownload() {
    const url = document.getElementById('quickUrl')?.value?.trim();
    const format = document.getElementById('quickFormat')?.value;
    const accountId = document.getElementById('quickAccount')?.value;

    if (!url) {
        showToast('Masukkan URL IconScout', 'warning');
        return;
    }

    try {
        const body = { url, format };
        if (accountId) body.account_id = parseInt(accountId);

        const result = await API.post('/api/tasks/download', body);
        showToast(result.message || 'Download dimulai!', 'success');
        closeModal();
    } catch (e) {
        showToast(e.message || 'Gagal memulai download', 'error');
    }
}


// =========================================================
// Global Search
// =========================================================
function handleGlobalSearch(event) {
    if (event.key === 'Enter') {
        const query = event.target.value.trim();
        if (query) {
            navigate('tasks');
            // The tasks page can handle search
        }
    }
}


// =========================================================
// Data Refresh
// =========================================================
async function refreshData() {
    try {
        const [stats, accounts, tasks, logs] = await Promise.all([
            API.get('/api/dashboard/stats').catch(() => null),
            API.get('/api/accounts').catch(() => ({ data: [], total: 0 })),
            API.get('/api/tasks?limit=50').catch(() => ({ data: [], total: 0 })),
            API.get('/api/logs?limit=50').catch(() => ({ data: [], total: 0 })),
        ]);

        if (stats) State.stats = stats;
        State.accounts = accounts.data || [];
        State.tasks = tasks.data || [];
        State.logs = logs.data || [];

        // Update badges
        document.getElementById('nav-badge-accounts').textContent = accounts.total || 0;
        document.getElementById('nav-badge-tasks').textContent = tasks.total || 0;
        document.getElementById('nav-badge-logs').textContent = logs.total || 0;

        // Update header status
        const activeCount = State.accounts.filter(a => a.status === 'active').length;
        document.getElementById('headerUserEmail').textContent =
            `${activeCount} active account${activeCount !== 1 ? 's' : ''} | ${stats?.items_downloaded || 0} downloaded`;

    } catch (e) {
        console.error('Refresh error:', e);
    }
}


// =========================================================
// Init
// =========================================================
document.addEventListener('DOMContentLoaded', async () => {
    // Load initial data
    await refreshData();

    // Route from hash
    const hash = window.location.hash.replace('#', '') || 'dashboard';
    navigate(hash);

    // Auto-refresh every 15 seconds
    State.refreshInterval = setInterval(refreshData, 15000);

    // Handle hash changes
    window.addEventListener('hashchange', () => {
        const page = window.location.hash.replace('#', '') || 'dashboard';
        if (page !== State.currentPage) navigate(page);
    });
});
