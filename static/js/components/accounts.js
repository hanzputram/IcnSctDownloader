/**
 * Accounts Management Component
 */

async function renderAccounts() {
    const content = document.getElementById('pageContent');
    let accounts = [];

    try {
        const data = await API.get('/api/accounts');
        accounts = data.data || [];
    } catch (e) {
        accounts = [];
    }

    content.innerHTML = `
        <div class="animate-in">
            <div class="page-header flex justify-between items-center">
                <div>
                    <h2 class="page-title">👤 <span class="accent">Account</span> Manager</h2>
                    <p class="page-subtitle">Kelola akun IconScout Anda</p>
                </div>
                <button class="btn btn-primary" onclick="showAddAccountModal()">
                    ➕ Tambah Account
                </button>
            </div>

            <div class="card">
                <div class="card-body" style="padding:0">
                    ${accounts.length === 0 ? `
                        <div class="empty-state">
                            <div class="empty-icon">👤</div>
                            <h3>Belum Ada Account</h3>
                            <p>Tambahkan akun IconScout Anda untuk mulai download asset</p>
                            <button class="btn btn-primary mt-2" onclick="showAddAccountModal()">➕ Tambah Account</button>
                        </div>
                    ` : `
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Email</th>
                                        <th>Status</th>
                                        <th>Plan</th>
                                        <th>Downloads</th>
                                        <th>Terakhir Digunakan</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${accounts.map(acc => `
                                        <tr>
                                            <td>
                                                <div class="flex items-center gap-1">
                                                    <div class="avatar" style="width:28px;height:28px;font-size:11px;background:var(--gradient-primary)">${acc.email[0].toUpperCase()}</div>
                                                    <strong class="text-primary">${acc.email}</strong>
                                                </div>
                                            </td>
                                            <td>${statusBadge(acc.status)}</td>
                                            <td><span class="text-accent">${acc.plan_type}</span></td>
                                            <td><strong>${(acc.downloads_count || 0).toLocaleString()}</strong></td>
                                            <td class="text-muted">${formatDate(acc.last_used)}</td>
                                            <td>
                                                <div class="flex gap-1">
                                                    <button class="btn btn-sm btn-success" onclick="testAccount(${acc.id})" title="Test Login">🔌 Test</button>
                                                    <button class="btn btn-sm btn-ghost" onclick="showEditAccountModal(${acc.id})" title="Edit">✏️</button>
                                                    <button class="btn btn-sm btn-danger" onclick="deleteAccount(${acc.id})" title="Hapus">🗑️</button>
                                                </div>
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    `}
                </div>
            </div>
        </div>
    `;
}

function showAddAccountModal() {
    showModal('➕ Tambah Account IconScout', `
        <div class="form-group">
            <label class="form-label">Email</label>
            <input type="email" class="form-input" id="accEmail" placeholder="email@example.com">
        </div>
        <div class="form-group">
            <label class="form-label">Password</label>
            <input type="password" class="form-input" id="accPassword" placeholder="Password IconScout">
        </div>
        <div class="form-group">
            <label class="form-label">Plan Type</label>
            <select class="form-select" id="accPlan">
                <option value="unlimited">Unlimited</option>
                <option value="pro">Pro</option>
                <option value="basic">Basic</option>
            </select>
        </div>
    `, `
        <button class="btn btn-ghost" onclick="closeModal()">Batal</button>
        <button class="btn btn-primary" onclick="submitAddAccount()">💾 Simpan</button>
    `);
}

async function submitAddAccount() {
    const email = document.getElementById('accEmail')?.value?.trim();
    const password = document.getElementById('accPassword')?.value;
    const plan_type = document.getElementById('accPlan')?.value;

    if (!email || !password) {
        showToast('Email dan password wajib diisi', 'warning');
        return;
    }

    try {
        const result = await API.post('/api/accounts', { email, password, plan_type });
        showToast(result.message || 'Account berhasil ditambahkan', 'success');
        closeModal();
        renderAccounts();
        refreshData();
    } catch (e) {
        showToast(e.message || 'Gagal menambahkan account', 'error');
    }
}

function showEditAccountModal(id) {
    const acc = State.accounts.find(a => a.id === id);
    if (!acc) return;

    showModal('✏️ Edit Account', `
        <div class="form-group">
            <label class="form-label">Email</label>
            <input type="email" class="form-input" id="editAccEmail" value="${acc.email}">
        </div>
        <div class="form-group">
            <label class="form-label">Password Baru (kosongkan jika tidak diubah)</label>
            <input type="password" class="form-input" id="editAccPassword" placeholder="Password baru...">
        </div>
        <div class="form-row">
            <div class="form-group">
                <label class="form-label">Plan Type</label>
                <select class="form-select" id="editAccPlan">
                    <option value="unlimited" ${acc.plan_type === 'unlimited' ? 'selected' : ''}>Unlimited</option>
                    <option value="pro" ${acc.plan_type === 'pro' ? 'selected' : ''}>Pro</option>
                    <option value="basic" ${acc.plan_type === 'basic' ? 'selected' : ''}>Basic</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Status</label>
                <select class="form-select" id="editAccStatus">
                    <option value="active" ${acc.status === 'active' ? 'selected' : ''}>Active</option>
                    <option value="inactive" ${acc.status === 'inactive' ? 'selected' : ''}>Inactive</option>
                    <option value="error" ${acc.status === 'error' ? 'selected' : ''}>Error</option>
                </select>
            </div>
        </div>
    `, `
        <button class="btn btn-ghost" onclick="closeModal()">Batal</button>
        <button class="btn btn-primary" onclick="submitEditAccount(${id})">💾 Update</button>
    `);
}

async function submitEditAccount(id) {
    const body = {};
    const email = document.getElementById('editAccEmail')?.value?.trim();
    const password = document.getElementById('editAccPassword')?.value;
    const plan_type = document.getElementById('editAccPlan')?.value;
    const status = document.getElementById('editAccStatus')?.value;

    if (email) body.email = email;
    if (password) body.password = password;
    if (plan_type) body.plan_type = plan_type;
    if (status) body.status = status;

    try {
        const result = await API.put(`/api/accounts/${id}`, body);
        showToast(result.message || 'Account updated', 'success');
        closeModal();
        renderAccounts();
        refreshData();
    } catch (e) {
        showToast(e.message || 'Gagal update account', 'error');
    }
}

async function testAccount(id) {
    showToast('🔌 Testing login...', 'info');
    try {
        const result = await API.post(`/api/accounts/${id}/test`);
        if (result.success) {
            showToast('✅ ' + (result.message || 'Login berhasil!'), 'success');
        } else {
            showToast('❌ ' + (result.message || 'Login gagal'), 'error');
        }
        renderAccounts();
        refreshData();
    } catch (e) {
        showToast('❌ ' + (e.message || 'Test gagal'), 'error');
    }
}

async function deleteAccount(id) {
    if (!confirm('Yakin ingin menghapus account ini?')) return;

    try {
        const result = await API.del(`/api/accounts/${id}`);
        showToast(result.message || 'Account dihapus', 'success');
        renderAccounts();
        refreshData();
    } catch (e) {
        showToast(e.message || 'Gagal menghapus account', 'error');
    }
}
