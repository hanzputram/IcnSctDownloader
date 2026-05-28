/**
 * Scheduler Component
 * Create and manage cron-based download schedules
 */

async function renderScheduler() {
    const content = document.getElementById('pageContent');
    let schedules = [];

    try {
        const data = await API.get('/api/schedules');
        schedules = data.data || [];
    } catch (e) {
        schedules = [];
    }

    content.innerHTML = `
        <div class="animate-in">
            <div class="page-header flex justify-between items-center">
                <div>
                    <h2 class="page-title">⏰ <span class="accent">Scheduler</span></h2>
                    <p class="page-subtitle">Jadwalkan download otomatis</p>
                </div>
                <button class="btn btn-primary" onclick="showAddScheduleModal()">
                    ➕ Buat Schedule
                </button>
            </div>

            ${schedules.length === 0 ? `
                <div class="card">
                    <div class="card-body">
                        <div class="empty-state">
                            <div class="empty-icon">⏰</div>
                            <h3>Belum Ada Schedule</h3>
                            <p>Buat jadwal download otomatis untuk menghemat waktu</p>
                            <button class="btn btn-primary mt-2" onclick="showAddScheduleModal()">➕ Buat Schedule</button>
                        </div>
                    </div>
                </div>
            ` : `
                <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:18px">
                    ${schedules.map(s => `
                        <div class="card">
                            <div class="card-header">
                                <span class="card-title">
                                    ${s.is_active ? '<span class="dot"></span>' : '<span class="dot" style="background:var(--text-muted);box-shadow:none"></span>'}
                                    ${s.name}
                                </span>
                                <label class="toggle" title="${s.is_active ? 'Aktif' : 'Nonaktif'}">
                                    <input type="checkbox" ${s.is_active ? 'checked' : ''} onchange="toggleSchedule(${s.id})">
                                    <span class="slider"></span>
                                </label>
                            </div>
                            <div class="card-body">
                                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:13px">
                                    <div>
                                        <div class="text-muted" style="font-size:11px;margin-bottom:4px">Source</div>
                                        <div class="text-primary">${s.source_type === 'keyword' ? '🔍 ' : '🔗 '}${truncate(s.source_value, 25)}</div>
                                    </div>
                                    <div>
                                        <div class="text-muted" style="font-size:11px;margin-bottom:4px">Asset Type</div>
                                        <div class="text-primary">${s.asset_type} / ${s.format.toUpperCase()}</div>
                                    </div>
                                    <div>
                                        <div class="text-muted" style="font-size:11px;margin-bottom:4px">Cron Expression</div>
                                        <div class="text-accent"><code>${s.cron_expression}</code></div>
                                    </div>
                                    <div>
                                        <div class="text-muted" style="font-size:11px;margin-bottom:4px">Max Items/Run</div>
                                        <div class="text-primary">${s.max_items}</div>
                                    </div>
                                    <div>
                                        <div class="text-muted" style="font-size:11px;margin-bottom:4px">Total Downloaded</div>
                                        <div class="text-green"><strong>${s.total_downloaded || 0}</strong></div>
                                    </div>
                                    <div>
                                        <div class="text-muted" style="font-size:11px;margin-bottom:4px">Last Run</div>
                                        <div>${formatDate(s.last_run)}</div>
                                    </div>
                                </div>
                                ${s.next_run ? `<div class="mt-1" style="font-size:11px"><span class="text-muted">Next run:</span> <span class="text-cyan">${formatDate(s.next_run)}</span></div>` : ''}
                            </div>
                            <div class="card-footer">
                                <button class="btn btn-sm btn-success" onclick="runScheduleNow(${s.id})">▶️ Run Now</button>
                                <div class="flex gap-1">
                                    <button class="btn btn-sm btn-ghost" onclick="showEditScheduleModal(${s.id})">✏️</button>
                                    <button class="btn btn-sm btn-danger" onclick="deleteSchedule(${s.id})">🗑️</button>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `}
        </div>
    `;
}

function showAddScheduleModal() {
    showModal('➕ Buat Schedule', `
        <div class="form-group">
            <label class="form-label">Nama Schedule</label>
            <input type="text" class="form-input" id="schName" placeholder="e.g. Daily Business Icons">
        </div>
        <div class="form-row">
            <div class="form-group">
                <label class="form-label">Source Type</label>
                <select class="form-select" id="schSourceType" onchange="toggleScheduleSource()">
                    <option value="keyword">Keyword Search</option>
                    <option value="link">Link List</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Asset Type</label>
                <select class="form-select" id="schAssetType">
                    <option value="icon">Icons</option>
                    <option value="illustration">Illustrations</option>
                    <option value="3d">3D Assets</option>
                    <option value="lottie">Lottie</option>
                </select>
            </div>
        </div>
        <div class="form-group" id="schSourceGroup">
            <label class="form-label" id="schSourceLabel">Keyword</label>
            <input type="text" class="form-input" id="schSourceInput" placeholder="e.g. business, finance">
            <textarea class="form-textarea hidden" id="schSourceTextarea" rows="4" placeholder="URL per baris..."></textarea>
        </div>
        <div class="form-row-3">
            <div class="form-group">
                <label class="form-label">Format</label>
                <select class="form-select" id="schFormat">
                    <option value="png">PNG</option>
                    <option value="svg">SVG</option>
                    <option value="eps">EPS</option>
                    <option value="json">Lottie JSON</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Max Items</label>
                <input type="number" class="form-input" id="schMax" value="10" min="1" max="100">
            </div>
            <div class="form-group">
                <label class="form-label">Cron Expression</label>
                <input type="text" class="form-input" id="schCron" value="0 */6 * * *" placeholder="0 */6 * * *">
            </div>
        </div>
        <div class="text-muted" style="font-size:11px;margin-top:-8px">
            Contoh: <code>0 */6 * * *</code> = setiap 6 jam, <code>0 0 * * *</code> = setiap tengah malam, <code>*/30 * * * *</code> = setiap 30 menit
        </div>
        <div class="form-group mt-2">
            <label class="form-label">Account</label>
            <select class="form-select" id="schAccount">
                <option value="">Auto (first active)</option>
            </select>
        </div>
    `, `
        <button class="btn btn-ghost" onclick="closeModal()">Batal</button>
        <button class="btn btn-primary" onclick="submitAddSchedule()">💾 Simpan</button>
    `);

    loadAccountsDropdown('schAccount');
}

function toggleScheduleSource() {
    const type = document.getElementById('schSourceType')?.value;
    const input = document.getElementById('schSourceInput');
    const textarea = document.getElementById('schSourceTextarea');
    const label = document.getElementById('schSourceLabel');

    if (type === 'link') {
        input.classList.add('hidden');
        textarea.classList.remove('hidden');
        label.textContent = 'URLs (satu per baris)';
    } else {
        input.classList.remove('hidden');
        textarea.classList.add('hidden');
        label.textContent = 'Keyword';
    }
}

async function submitAddSchedule() {
    const name = document.getElementById('schName')?.value?.trim();
    const source_type = document.getElementById('schSourceType')?.value;
    const asset_type = document.getElementById('schAssetType')?.value;
    const format = document.getElementById('schFormat')?.value;
    const max_items = parseInt(document.getElementById('schMax')?.value || '10');
    const cron_expression = document.getElementById('schCron')?.value?.trim();
    const accountId = document.getElementById('schAccount')?.value;

    let source_value = '';
    if (source_type === 'keyword') {
        source_value = document.getElementById('schSourceInput')?.value?.trim();
    } else {
        source_value = document.getElementById('schSourceTextarea')?.value?.trim();
    }

    if (!name || !source_value || !cron_expression) {
        showToast('Nama, source, dan cron expression wajib diisi', 'warning');
        return;
    }

    try {
        const body = { name, source_type, source_value, asset_type, format, max_items, cron_expression };
        if (accountId) body.account_id = parseInt(accountId);

        const result = await API.post('/api/schedules', body);
        showToast(result.message || 'Schedule berhasil dibuat', 'success');
        closeModal();
        renderScheduler();
    } catch (e) {
        showToast(e.message || 'Gagal membuat schedule', 'error');
    }
}

function showEditScheduleModal(id) {
    // Simplified edit - just re-use add with pre-filled values
    // In a real app, you'd fetch the schedule and pre-fill
    showToast('Gunakan delete + create untuk edit schedule', 'info');
}

async function toggleSchedule(id) {
    try {
        const result = await API.post(`/api/schedules/${id}/toggle`);
        showToast(result.message || 'Schedule updated', 'success');
        renderScheduler();
    } catch (e) {
        showToast(e.message || 'Gagal toggle schedule', 'error');
    }
}

async function runScheduleNow(id) {
    try {
        const result = await API.post(`/api/schedules/${id}/run-now`);
        showToast(result.message || 'Schedule dijalankan!', 'success');
    } catch (e) {
        showToast(e.message || 'Gagal menjalankan schedule', 'error');
    }
}

async function deleteSchedule(id) {
    if (!confirm('Yakin ingin menghapus schedule ini?')) return;

    try {
        const result = await API.del(`/api/schedules/${id}`);
        showToast(result.message || 'Schedule dihapus', 'success');
        renderScheduler();
    } catch (e) {
        showToast(e.message || 'Gagal menghapus schedule', 'error');
    }
}
