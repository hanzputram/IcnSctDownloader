<template>
  <div class="app-layout">
    <Sidebar />
    <main class="main-content">
      <header class="header">
        <div class="header-search">
          <span class="search-icon">🔍</span>
          <input type="text" placeholder="Search Management..." />
        </div>
        <div class="header-actions">
          <button class="icon-btn">✉️</button>
          <button class="icon-btn">🔔</button>
          <div class="user-profile">
            <div class="user-avatar">KG</div>
            <div class="user-details">
              <strong>kaserstudio</strong>
              <span>kaserstudio@gmail.com</span>
            </div>
          </div>
        </div>
      </header>
      <div class="page-content">
        <router-view :key="store.refreshTrigger"></router-view>
      </div>
    </main>

    <!-- Global Modal: Tambah Akun -->
    <div v-if="store.showAddAccountModal" class="modal-overlay" @click.self="store.showAddAccountModal = false">
      <div class="modal-content animate-in">
        <div class="modal-header">
          <h3>➕ Tambah Akun Premium</h3>
          <button class="close-btn" @click="store.showAddAccountModal = false">&times;</button>
        </div>
        <form @submit.prevent="submitAccount" class="modal-form">
          <div class="form-group">
            <label>Email IconScout</label>
            <input v-model="accountForm.email" type="email" placeholder="contoh@email.com" required />
          </div>
          <div class="form-group">
            <label>Password</label>
            <input v-model="accountForm.password" type="password" placeholder="Masukkan password" required />
          </div>
          <div class="form-group">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px">
              <label style="margin:0">🛡️ Auto-Proxy (Anti-Ban)</label>
              <label class="toggle-switch">
                <input type="checkbox" v-model="accountForm.auto_proxy" />
                <span class="toggle-slider"></span>
              </label>
            </div>
            <small style="color:var(--accent-green); font-size:10px; display:block; margin-bottom:8px" v-if="accountForm.auto_proxy">
              ✅ Proxy akan otomatis di-generate dari pool proxy gratis saat akun dibuat
            </small>
          </div>
          <div class="form-group" v-if="!accountForm.auto_proxy">
            <label>Proxy URL (Manual)</label>
            <input v-model="accountForm.proxy_url" type="text" placeholder="http://user:pass@ip:port" />
            <small style="color:var(--text-secondary); font-size:10px">Mendukung SOCKS5 / HTTP Proxy</small>
          </div>
          <div class="form-group">
            <label>Tipe Paket (Plan)</label>
            <select v-model="accountForm.plan_type">
              <option value="unlimited">Unlimited Plan</option>
              <option value="daily_limit">Daily Limit Plan</option>
              <option value="free">Free Account</option>
            </select>
          </div>
          <div v-if="accountError" class="error-msg">{{ accountError }}</div>
          <div class="modal-actions">
            <button type="button" class="btn btn-dark" @click="store.showAddAccountModal = false">Batal</button>
            <button type="submit" class="btn btn-purple" :disabled="submittingAccount">
              {{ submittingAccount ? 'Menyimpan...' : 'Simpan Akun' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Global Modal: Tambah Link / Schedule -->
    <div v-if="store.showAddLinkModal" class="modal-overlay" @click.self="store.showAddLinkModal = false">
      <div class="modal-content animate-in" style="max-width: 550px">
        <div class="modal-header">
          <h3>➕ Tambah Target & Penjadwalan</h3>
          <button class="close-btn" @click="store.showAddLinkModal = false">&times;</button>
        </div>
        <form @submit.prevent="submitLink" class="modal-form">
          <div class="form-group">
            <label>Nama Konfigurasi / Tugas</label>
            <input v-model="linkForm.name" type="text" placeholder="Contoh: Download Aset 3D Bisnis" required />
          </div>
          <div class="form-group">
            <label>Tipe Sumber Konten</label>
            <div style="display:flex; gap:16px; margin-top:4px">
              <label style="display:flex; align-items:center; gap:6px; cursor:pointer; font-weight:normal">
                <input type="radio" value="link" v-model="linkForm.source_type" /> Daftar Tautan (URL)
              </label>
              <label style="display:flex; align-items:center; gap:6px; cursor:pointer; font-weight:normal">
                <input type="radio" value="keyword" v-model="linkForm.source_type" /> Grup Kata Kunci (Search)
              </label>
            </div>
          </div>

          <div class="form-group" v-if="linkForm.source_type === 'link'">
            <label>Daftar Tautan IconScout (Satu baris per URL)</label>
            <textarea v-model="linkForm.source_value" rows="4" placeholder="https://iconscout.com/3d/business-character..." required></textarea>
          </div>
          <div class="form-group" v-else>
            <label>Kata Kunci Pencarian</label>
            <input v-model="linkForm.source_value" type="text" placeholder="Contoh: business, technology, heart" required />
          </div>

          <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px">
            <div class="form-group">
              <label>Jenis Aset</label>
              <select v-model="linkForm.asset_type" :disabled="linkForm.source_type === 'link'">
                <option value="icon">Icon</option>
                <option value="illustration">Illustration</option>
                <option value="3d">3D Asset</option>
                <option value="lottie">Lottie Animation</option>
              </select>
            </div>
            <div class="form-group">
              <label>Format File</label>
              <select v-model="linkForm.format">
                <option value="png">PNG</option>
                <option value="svg">SVG</option>
                <option value="jpg">JPG</option>
                <option value="eps">EPS</option>
              </select>
            </div>
          </div>

          <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px">
            <div class="form-group">
              <label>Maksimal Aset</label>
              <input v-model.number="linkForm.max_items" type="number" min="1" max="100" required />
            </div>
            <div class="form-group">
              <label>Interval Download</label>
              <select v-model="cronPreset" @change="updateCronExpression">
                <option value="manual">Sekali Jalan / Manual</option>
                <option value="hourly">Setiap Jam</option>
                <option value="every_6">Setiap 6 Jam</option>
                <option value="daily">Setiap Hari (Tengah Malam)</option>
                <option value="custom">Kustom Cron Expression</option>
              </select>
            </div>
          </div>

          <div class="form-group" v-if="cronPreset === 'custom'">
            <label>Cron Expression (5 part)</label>
            <input v-model="linkForm.cron_expression" type="text" placeholder="0 */6 * * *" required />
            <small style="color:var(--text-secondary); font-size:10px">Format: menit jam hari bulan hari_minggu</small>
          </div>

          <div v-if="linkError" class="error-msg">{{ linkError }}</div>
          <div class="modal-actions" style="margin-top:20px">
            <button type="button" class="btn btn-dark" @click="store.showAddLinkModal = false">Batal</button>
            <button type="submit" class="btn btn-purple" :disabled="submittingLink">
              {{ submittingLink ? 'Menyimpan...' : 'Tambah Target' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from 'axios'
import Sidebar from './components/Sidebar.vue'
import { store } from './store.js'

// --- Tambah Akun ---
const submittingAccount = ref(false)
const accountError = ref('')
const accountForm = reactive({
  email: '',
  password: '',
  proxy_url: '',
  plan_type: 'unlimited',
  auto_proxy: true
})

const submitAccount = async () => {
  submittingAccount.value = true
  accountError.value = ''
  try {
    await axios.post('/api/accounts', {
      email: accountForm.email,
      password: accountForm.password,
      plan_type: accountForm.plan_type,
      proxy_url: accountForm.auto_proxy ? null : (accountForm.proxy_url || null),
      auto_proxy: accountForm.auto_proxy
    })
    store.showAddAccountModal = false
    // Reset form
    accountForm.email = ''
    accountForm.password = ''
    accountForm.proxy_url = ''
    accountForm.plan_type = 'unlimited'
    accountForm.auto_proxy = true
    // Refresh active view
    store.triggerRefresh()
  } catch (e) {
    accountError.value = e.response?.data?.detail || "Gagal menyimpan akun"
  } finally {
    submittingAccount.value = false
  }
}

// --- Tambah Link / Schedule ---
const submittingLink = ref(false)
const linkError = ref('')
const cronPreset = ref('manual')
const linkForm = reactive({
  name: '',
  source_type: 'link',
  source_value: '',
  asset_type: 'icon',
  format: 'png',
  max_items: 10,
  cron_expression: '0 0 1 1 *' // manual dummy placeholder
})

const updateCronExpression = () => {
  if (cronPreset.value === 'manual') {
    // APScheduler trigger once: we can set dummy date cron that never runs automatically,
    // and let users trigger manual Run Now.
    linkForm.cron_expression = '0 0 1 1 *' 
  } else if (cronPreset.value === 'hourly') {
    linkForm.cron_expression = '0 * * * *'
  } else if (cronPreset.value === 'every_6') {
    linkForm.cron_expression = '0 */6 * * *'
  } else if (cronPreset.value === 'daily') {
    linkForm.cron_expression = '0 0 * * *'
  } else {
    linkForm.cron_expression = '0 */6 * * *'
  }
}

const submitLink = async () => {
  submittingLink.value = true
  linkError.value = ''
  try {
    updateCronExpression()
    await axios.post('/api/schedules', {
      name: linkForm.name,
      source_type: linkForm.source_type,
      source_value: linkForm.source_value,
      asset_type: linkForm.asset_type,
      format: linkForm.format,
      max_items: linkForm.max_items,
      cron_expression: linkForm.cron_expression
    })
    store.showAddLinkModal = false
    // Reset form
    linkForm.name = ''
    linkForm.source_type = 'link'
    linkForm.source_value = ''
    linkForm.asset_type = 'icon'
    linkForm.format = 'png'
    linkForm.max_items = 10
    cronPreset.value = 'manual'
    // Refresh active view
    store.triggerRefresh()
  } catch (e) {
    linkError.value = e.response?.data?.detail || "Gagal membuat schedule target"
  } finally {
    submittingLink.value = false
  }
}
</script>

