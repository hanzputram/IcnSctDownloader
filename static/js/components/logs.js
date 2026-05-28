/**
 * Logs Viewer Component
 */

async function renderLogs() {
    const content = document.getElementById('pageContent');
    let logs = [];
    let total = 0;

    try {
        const data = await API.get('/api/logs?limit=100');
        logs = data.data || [];
        total = data.total || 0;
    } catch (e) {
        logs = [];
    }

    content.innerHTML = `
        <div class="animate-in">
            <div class="page-header flex justify-between items-center">
                <div>
                    <h2 class="page-title">📋 <span class="accent">Logs</span></h2>
                    <p class="page-subtitle">${total} total log entries</p>
                </div>
                <div class="flex gap-1">
                    <button class="btn btn-ghost" onclick="renderLogs()">🔄 Refresh</button>
                    <button class="btn btn-danger" onclick="clearLogs()">🗑️ Clear All</button>
                </div>
            </div>

            <!-- Filters -->
            <div class="filter-bar mb-2">
                <div class="filter-chips">
                    <button class="chip active" onclick="filterLogs('', this)">Semua</button>
                    <button class="chip" onclick="filterLogs('info', this)">ℹ️ Info</button>
                    <button class="chip" onclick="filterLogs('success', this)">✅ Success</button>
                    <button class="chip" onclick="filterLogs('warning', this)">⚠️ Warning</button>
                    <button class="chip" onclick="filterLogs('error', this)">❌ Error</button>
                </div>
                <div style="margin-left:auto">
                    <input type="text" class="form-input" placeholder="Search logs..." style="width:220px;padding:6px 12px;font-size:12px" id="logSearchInput" onkeyup="searchLogs(event)">
                </div>
            </div>

            <div class="card">
                <div class="card-body" style="padding:0;max-height:600px;overflow-y:auto" id="logsContainer">
                    ${logs.length === 0 ? `
                        <div class="empty-state">
                            <div class="empty-icon">📋</div>
                            <h3>Tidak Ada Log</h3>
                            <p>Log akan muncul saat ada aktivitas download</p>
                        </div>
                    ` : logs.map(log => `
                        <div class="log-entry">
                            <div class="log-level ${log.level}"></div>
                            <div class="log-message">
                                <div>${log.message}</div>
                                ${log.details ? `<div class="text-muted" style="font-size:11px;margin-top:2px">${log.details}</div>` : ''}
                                ${log.task_id ? `<span class="text-muted" style="font-size:10px">Task #${log.task_id}</span>` : ''}
                            </div>
                            <div class="log-time">${formatDate(log.timestamp)}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}

async function filterLogs(level, btn) {
    if (btn) {
        btn.closest('.filter-chips').querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
    }

    try {
        const url = level ? `/api/logs?level=${level}&limit=100` : '/api/logs?limit=100';
        const data = await API.get(url);
        const container = document.getElementById('logsContainer');
        if (container) {
            const logs = data.data || [];
            container.innerHTML = logs.length === 0
                ? '<div class="empty-state" style="padding:32px"><h3>Tidak ada log untuk filter ini</h3></div>'
                : logs.map(log => `
                    <div class="log-entry">
                        <div class="log-level ${log.level}"></div>
                        <div class="log-message">
                            <div>${log.message}</div>
                            ${log.details ? `<div class="text-muted" style="font-size:11px;margin-top:2px">${log.details}</div>` : ''}
                            ${log.task_id ? `<span class="text-muted" style="font-size:10px">Task #${log.task_id}</span>` : ''}
                        </div>
                        <div class="log-time">${formatDate(log.timestamp)}</div>
                    </div>
                `).join('');
        }
    } catch (e) {
        showToast('Gagal filter logs', 'error');
    }
}

async function searchLogs(event) {
    if (event.key === 'Enter') {
        const search = event.target.value.trim();
        try {
            const url = search ? `/api/logs?search=${encodeURIComponent(search)}&limit=100` : '/api/logs?limit=100';
            const data = await API.get(url);
            const container = document.getElementById('logsContainer');
            if (container) {
                const logs = data.data || [];
                container.innerHTML = logs.length === 0
                    ? '<div class="empty-state" style="padding:32px"><h3>Tidak ditemukan</h3></div>'
                    : logs.map(log => `
                        <div class="log-entry">
                            <div class="log-level ${log.level}"></div>
                            <div class="log-message"><div>${log.message}</div></div>
                            <div class="log-time">${formatDate(log.timestamp)}</div>
                        </div>
                    `).join('');
            }
        } catch (e) {
            showToast('Search gagal', 'error');
        }
    }
}

async function clearLogs() {
    if (!confirm('Yakin ingin menghapus semua log?')) return;

    try {
        await API.del('/api/logs');
        showToast('Semua log berhasil dihapus', 'success');
        renderLogs();
        refreshData();
    } catch (e) {
        showToast(e.message || 'Gagal menghapus logs', 'error');
    }
}
