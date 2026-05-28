/**
 * Tasks / Downloads Component
 * Single download, bulk download, search-and-download
 */

async function renderTasks() {
    const content = document.getElementById('pageContent');
    let tasks = [];
    let total = 0;

    try {
        const data = await API.get('/api/tasks?limit=50');
        tasks = data.data || [];
        total = data.total || 0;
    } catch (e) {
        tasks = [];
    }

    content.innerHTML = `
        <div class="animate-in">
            <div class="page-header flex justify-between items-center">
                <div>
                    <h2 class="page-title">📥 <span class="accent">Downloads</span></h2>
                    <p class="page-subtitle">${total} total download tasks</p>
                </div>
                <div class="flex gap-1">
                    <button class="btn btn-ghost" onclick="showSearchDownloadModal()">🔍 Search & Download</button>
                    <button class="btn btn-ghost" onclick="showBulkDownloadModal()">📋 Bulk Download</button>
                    <button class="btn btn-primary" onclick="showSingleDownloadModal()">📥 Single Download</button>
                </div>
            </div>

            <!-- Status filter -->
            <div class="filter-bar mb-2">
                <div class="filter-chips">
                    <button class="chip active" onclick="filterTasks('', this)">Semua</button>
                    <button class="chip" onclick="filterTasks('pending', this)">⏳ Pending</button>
                    <button class="chip" onclick="filterTasks('running', this)">🔄 Running</button>
                    <button class="chip" onclick="filterTasks('completed', this)">✅ Completed</button>
                    <button class="chip" onclick="filterTasks('failed', this)">❌ Failed</button>
                </div>
            </div>

            <div class="card">
                <div class="card-body" style="padding:0">
                    ${tasks.length === 0 ? `
                        <div class="empty-state">
                            <div class="empty-icon">📥</div>
                            <h3>Belum Ada Download</h3>
                            <p>Mulai download dengan klik tombol di atas</p>
                        </div>
                    ` : `
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>Asset</th>
                                        <th>Source</th>
                                        <th>Format</th>
                                        <th>Status</th>
                                        <th>Size</th>
                                        <th>Waktu</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="tasksTableBody">
                                    ${tasks.map(t => renderTaskRow(t)).join('')}
                                </tbody>
                            </table>
                        </div>
                    `}
                </div>
            </div>
        </div>
    `;
}

function renderTaskRow(t) {
    return `
        <tr>
            <td class="text-muted">${t.id}</td>
            <td>
                <div class="truncate" style="max-width:200px" title="${t.asset_name || t.source_value}">
                    <strong class="text-primary">${t.asset_name || '—'}</strong>
                </div>
                <div class="text-muted" style="font-size:11px">${t.asset_type || t.source_type}</div>
            </td>
            <td>
                <div class="truncate" style="max-width:200px" title="${t.source_value}">
                    ${truncate(t.source_value, 35)}
                </div>
            </td>
            <td><span class="text-accent">${(t.format || '—').toUpperCase()}</span></td>
            <td>${statusBadge(t.status)}</td>
            <td>${formatSize(t.file_size)}</td>
            <td class="text-muted" style="font-size:11px">${formatDate(t.completed_at || t.created_at)}</td>
            <td>
                <div class="flex gap-1">
                    ${t.cloud_url ? `<a href="${t.cloud_url}" target="_blank" class="btn btn-sm btn-ghost" title="Cloud">☁️</a>` : ''}
                    ${t.status === 'pending' || t.status === 'running' ? `<button class="btn btn-sm btn-danger" onclick="cancelTask(${t.id})" title="Cancel">✕</button>` : ''}
                </div>
            </td>
        </tr>
    `;
}

async function filterTasks(status, btn) {
    if (btn) {
        btn.closest('.filter-chips').querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
    }

    try {
        const url = status ? `/api/tasks?status=${status}&limit=50` : '/api/tasks?limit=50';
        const data = await API.get(url);
        const tbody = document.getElementById('tasksTableBody');
        if (tbody) {
            tbody.innerHTML = (data.data || []).map(t => renderTaskRow(t)).join('');
        }
    } catch (e) {
        showToast('Gagal filter tasks', 'error');
    }
}

// --- Single Download Modal ---
function showSingleDownloadModal() {
    showModal('📥 Single Download', `
        <div class="form-group">
            <label class="form-label">IconScout URL</label>
            <input type="text" class="form-input" id="dlUrl" placeholder="https://iconscout.com/icon/example-12345">
        </div>
        <div class="form-row">
            <div class="form-group">
                <label class="form-label">Format</label>
                <select class="form-select" id="dlFormat">
                    <option value="png">PNG</option>
                    <option value="svg">SVG</option>
                    <option value="eps">EPS</option>
                    <option value="pdf">PDF</option>
                    <option value="json">Lottie JSON</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Account</label>
                <select class="form-select" id="dlAccount">
                    <option value="">Auto (first active)</option>
                </select>
            </div>
        </div>
    `, `
        <button class="btn btn-ghost" onclick="closeModal()">Batal</button>
        <button class="btn btn-primary" onclick="submitSingleDownload()">🚀 Download</button>
    `);

    loadAccountsDropdown('dlAccount');
}

async function submitSingleDownload() {
    const url = document.getElementById('dlUrl')?.value?.trim();
    const format = document.getElementById('dlFormat')?.value;
    const accountId = document.getElementById('dlAccount')?.value;

    if (!url) { showToast('URL wajib diisi', 'warning'); return; }

    try {
        const body = { url, format };
        if (accountId) body.account_id = parseInt(accountId);

        const result = await API.post('/api/tasks/download', body);
        showToast(result.message || 'Download dimulai!', 'success');
        closeModal();
        setTimeout(() => renderTasks(), 1000);
    } catch (e) {
        showToast(e.message || 'Gagal memulai download', 'error');
    }
}

// --- Bulk Download Modal ---
function showBulkDownloadModal() {
    showModal('📋 Bulk Download', `
        <div class="form-group">
            <label class="form-label">IconScout URLs (satu per baris)</label>
            <textarea class="form-textarea" id="bulkUrls" rows="8" placeholder="https://iconscout.com/icon/example-1&#10;https://iconscout.com/icon/example-2&#10;https://iconscout.com/icon/example-3"></textarea>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label class="form-label">Format</label>
                <select class="form-select" id="bulkFormat">
                    <option value="png">PNG</option>
                    <option value="svg">SVG</option>
                    <option value="eps">EPS</option>
                    <option value="pdf">PDF</option>
                    <option value="json">Lottie JSON</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Account</label>
                <select class="form-select" id="bulkAccount">
                    <option value="">Auto (first active)</option>
                </select>
            </div>
        </div>
    `, `
        <button class="btn btn-ghost" onclick="closeModal()">Batal</button>
        <button class="btn btn-primary" onclick="submitBulkDownload()">🚀 Start Bulk Download</button>
    `);

    loadAccountsDropdown('bulkAccount');
}

async function submitBulkDownload() {
    const raw = document.getElementById('bulkUrls')?.value?.trim();
    const format = document.getElementById('bulkFormat')?.value;
    const accountId = document.getElementById('bulkAccount')?.value;

    if (!raw) { showToast('URLs wajib diisi', 'warning'); return; }

    const urls = raw.split('\n').map(u => u.trim()).filter(u => u.length > 0);
    if (urls.length === 0) { showToast('Tidak ada URL valid', 'warning'); return; }

    try {
        const body = { urls, format };
        if (accountId) body.account_id = parseInt(accountId);

        const result = await API.post('/api/tasks/bulk-download', body);
        showToast(result.message || `Bulk download dimulai: ${urls.length} items`, 'success');
        closeModal();
        setTimeout(() => renderTasks(), 1000);
    } catch (e) {
        showToast(e.message || 'Gagal memulai bulk download', 'error');
    }
}

// --- Search & Download Modal ---
function showSearchDownloadModal() {
    showModal('🔍 Search & Download', `
        <div class="form-group">
            <label class="form-label">Keyword</label>
            <input type="text" class="form-input" id="searchKeyword" placeholder="e.g. business, cat, arrow, finance">
        </div>
        <div class="form-row-3">
            <div class="form-group">
                <label class="form-label">Asset Type</label>
                <select class="form-select" id="searchType">
                    <option value="icon">Icons</option>
                    <option value="illustration">Illustrations</option>
                    <option value="3d">3D Assets</option>
                    <option value="lottie">Lottie</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Format</label>
                <select class="form-select" id="searchFormat">
                    <option value="png">PNG</option>
                    <option value="svg">SVG</option>
                    <option value="eps">EPS</option>
                    <option value="json">Lottie JSON</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Max Items</label>
                <input type="number" class="form-input" id="searchMax" value="10" min="1" max="50">
            </div>
        </div>
        <div class="form-group">
            <label class="form-label">Account</label>
            <select class="form-select" id="searchAccount">
                <option value="">Auto (first active)</option>
            </select>
        </div>
    `, `
        <button class="btn btn-ghost" onclick="closeModal()">Batal</button>
        <button class="btn btn-primary" onclick="submitSearchDownload()">🚀 Search & Download</button>
    `);

    loadAccountsDropdown('searchAccount');
}

async function submitSearchDownload() {
    const keyword = document.getElementById('searchKeyword')?.value?.trim();
    const asset_type = document.getElementById('searchType')?.value;
    const format = document.getElementById('searchFormat')?.value;
    const max_items = parseInt(document.getElementById('searchMax')?.value || '10');
    const accountId = document.getElementById('searchAccount')?.value;

    if (!keyword) { showToast('Keyword wajib diisi', 'warning'); return; }

    try {
        const body = { keyword, asset_type, format, max_items };
        if (accountId) body.account_id = parseInt(accountId);

        const result = await API.post('/api/tasks/search-download', body);
        showToast(result.message || 'Search & download dimulai!', 'success');
        closeModal();
        setTimeout(() => renderTasks(), 2000);
    } catch (e) {
        showToast(e.message || 'Gagal memulai search download', 'error');
    }
}

async function cancelTask(id) {
    try {
        const result = await API.del(`/api/tasks/${id}`);
        showToast(result.message || 'Task dibatalkan', 'success');
        renderTasks();
    } catch (e) {
        showToast(e.message || 'Gagal cancel task', 'error');
    }
}
