<template>
  <div class="animate-in">
    <div class="page-header-row">
      <div>
        <h2 class="page-title">👥 <span class="accent">Accounts</span> Hub</h2>
        <p style="color:var(--text-secondary); font-size:13px; margin-top:4px">Kelola akun premium IconScout Anda untuk download tanpa batas</p>
      </div>
      <div style="display:flex; gap:10px">
        <button class="btn btn-dark" @click="refreshAllProxies" :disabled="refreshingPool">
          {{ refreshingPool ? '🔄 Refreshing...' : '🔄 Refresh Proxy Pool' }}
        </button>
        <button class="btn btn-purple" @click="store.showAddAccountModal = true">
          ➕ Tambah Akun Baru
        </button>
      </div>
    </div>

    <!-- Proxy Pool Stats Banner -->
    <div v-if="proxyStats" class="card" style="padding:16px 20px; margin-bottom:20px; display:flex; align-items:center; gap:24px; flex-wrap:wrap; border-left:3px solid var(--accent-green);">
      <div style="display:flex; align-items:center; gap:8px;">
        <span style="font-size:20px">🛡️</span>
        <span style="font-size:13px; font-weight:600; color:var(--accent-green)">Proxy Pool</span>
      </div>
      <div style="display:flex; gap:20px; font-size:12px; flex-wrap:wrap">
        <span><strong style="color:var(--accent-green)">{{ proxyStats.alive }}</strong> <span style="color:var(--text-secondary)">Alive</span></span>
        <span><strong style="color:var(--accent-red, #ff4d6a)">{{ proxyStats.dead }}</strong> <span style="color:var(--text-secondary)">Dead</span></span>
        <span><strong>{{ proxyStats.assigned }}</strong> <span style="color:var(--text-secondary)">Assigned</span></span>
        <span><strong>{{ proxyStats.total }}</strong> <span style="color:var(--text-secondary)">Total</span></span>
        <span v-if="proxyStats.avg_speed_ms"><strong>{{ proxyStats.avg_speed_ms }}ms</strong> <span style="color:var(--text-secondary)">Avg Speed</span></span>
      </div>
      <div v-if="proxyStats.last_refresh" style="margin-left:auto; font-size:11px; color:var(--text-secondary)">
        Last refresh: {{ formatDate(proxyStats.last_refresh) }}
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="accounts.length === 0" class="card" style="padding:60px 20px; text-align:center; display:flex; flex-direction:column; align-items:center; gap:16px">
      <div style="font-size:48px; filter:drop-shadow(0 0 10px var(--accent-purple))">👤</div>
      <h3 style="font-size:18px; font-weight:700">Belum Ada Akun Terdaftar</h3>
      <p style="color:var(--text-secondary); max-width:360px; font-size:13px; margin:0">
        Tambahkan akun IconScout Anda menggunakan tombol di atas untuk memulai pengunduhan aset premium secara otomatis.
        <br><br>
        <span style="color:var(--accent-green)">🛡️ Proxy akan otomatis di-generate untuk setiap akun baru (Anti-Ban)</span>
      </p>
    </div>

    <!-- Accounts Grid -->
    <div v-else style="display:grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap:20px;">
      <div v-for="acc in accounts" :key="acc.id" class="card account-card" style="display:flex; flex-direction:column; gap:16px">
        <!-- Header: Avatar & Status -->
        <div style="display:flex; justify-content:space-between; align-items:center">
          <div style="display:flex; align-items:center; gap:12px">
            <div style="width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg, var(--accent-purple), var(--accent-green)); display:flex; align-items:center; justify-content:center; font-weight:bold; color:white">
              {{ acc.email[0].toUpperCase() }}
            </div>
            <div style="display:flex; flex-direction:column">
              <strong style="font-size:14px; text-overflow:ellipsis; overflow:hidden; white-space:nowrap; max-width:180px" :title="acc.email">
                {{ acc.email }}
              </strong>
              <span style="font-size:11px; color:var(--text-secondary)">ID: #{{ acc.id }}</span>
            </div>
          </div>
          <!-- Status Pill -->
          <span 
            class="badge-glow" 
            :class="{
              'badge-green': acc.status === 'active',
              'badge-red': acc.status === 'error' || acc.status === 'banned',
              'badge-purple': acc.status === 'inactive'
            }"
            style="text-transform:capitalize"
          >
            {{ acc.status === 'active' ? '🟢 Active' : acc.status === 'error' ? '🔴 Error' : acc.status === 'banned' ? '🚫 Banned' : '⚪ Offline' }}
          </span>
        </div>

        <!-- Details -->
        <div style="background:var(--bg-input); padding:12px; border-radius:12px; border:1px solid var(--border-color); display:flex; flex-direction:column; gap:8px; font-size:12px">
          <div style="display:flex; justify-content:space-between">
            <span style="color:var(--text-secondary)">Plan Type:</span>
            <strong style="color:var(--accent-purple); text-transform:uppercase">{{ acc.plan_type }}</strong>
          </div>
          <div style="display:flex; justify-content:space-between">
            <span style="color:var(--text-secondary)">Downloads:</span>
            <strong>{{ acc.downloads_count }} Aset</strong>
          </div>
          <!-- Proxy Status -->
          <div style="display:flex; justify-content:space-between; align-items:center">
            <span style="color:var(--text-secondary)">Proxy:</span>
            <div style="display:flex; align-items:center; gap:6px">
              <span v-if="acc.proxy_url" class="proxy-badge proxy-active" :title="acc.proxy_url">
                🛡️ {{ maskProxy(acc.proxy_url) }}
              </span>
              <span v-else class="proxy-badge proxy-none">
                ⚠️ No Proxy
              </span>
            </div>
          </div>
          <div style="display:flex; justify-content:space-between" v-if="acc.last_used">
            <span style="color:var(--text-secondary)">Terakhir Digunakan:</span>
            <span>{{ formatDate(acc.last_used) }}</span>
          </div>
        </div>

        <!-- Actions -->
        <div style="display:flex; gap:8px; margin-top:auto; flex-wrap:wrap">
          <button 
            @click="testLogin(acc)" 
            class="btn btn-dark" 
            style="flex:1; font-size:12px; padding:10px"
            :disabled="acc.testing"
          >
            {{ acc.testing ? 'Menguji...' : '🔌 Uji Login' }}
          </button>
          <button 
            @click="refreshProxy(acc)" 
            class="btn btn-dark" 
            style="font-size:12px; padding:10px; min-width:90px"
            :disabled="acc.refreshingProxy"
            :title="acc.proxy_url ? 'Ganti proxy dengan yang baru' : 'Assign proxy baru'"
          >
            {{ acc.refreshingProxy ? '🔄...' : '🔄 Proxy' }}
          </button>
          <button 
            @click="deleteAccount(acc.id)" 
            class="btn btn-red" 
            style="font-size:12px; padding:10px; min-width:70px"
          >
            🗑️
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { store } from '../store.js'

const accounts = ref([])
const proxyStats = ref(null)
const refreshingPool = ref(false)

const fetchAccounts = async () => {
  try {
    const res = await axios.get('/api/accounts')
    accounts.value = (res.data.data || []).map(acc => ({
      ...acc,
      testing: false,
      refreshingProxy: false
    }))
  } catch (e) {
    console.error("Gagal mengambil data akun", e)
  }
}

const fetchProxyStats = async () => {
  try {
    const res = await axios.get('/api/proxy/stats')
    proxyStats.value = res.data
  } catch (e) {
    console.error("Gagal mengambil proxy stats", e)
  }
}

const testLogin = async (acc) => {
  acc.testing = true
  try {
    const res = await axios.post(`/api/accounts/${acc.id}/test`)
    if (res.data.success) {
      alert(`Login berhasil untuk ${acc.email}! Cookie tersinkronisasi.`)
    } else {
      alert(`Login gagal untuk ${acc.email}: ${res.data.message}`)
    }
    fetchAccounts()
  } catch (e) {
    alert("Koneksi gagal atau akun mengalami error.")
  } finally {
    acc.testing = false
  }
}

const refreshProxy = async (acc) => {
  acc.refreshingProxy = true
  try {
    const res = await axios.post(`/api/accounts/${acc.id}/refresh-proxy`)
    if (res.data.success) {
      alert(`✅ Proxy berhasil diperbarui: ${res.data.proxy_url}`)
    } else {
      alert(`⚠️ ${res.data.message}`)
    }
    fetchAccounts()
    fetchProxyStats()
  } catch (e) {
    alert("Gagal refresh proxy. Coba refresh pool terlebih dahulu.")
  } finally {
    acc.refreshingProxy = false
  }
}

const refreshAllProxies = async () => {
  refreshingPool.value = true
  try {
    const res = await axios.post('/api/proxy/refresh')
    alert(`✅ Proxy pool berhasil di-refresh!\nAlive: ${res.data.alive} | Total: ${res.data.total_pool}`)
    fetchProxyStats()
  } catch (e) {
    alert("Gagal refresh proxy pool.")
  } finally {
    refreshingPool.value = false
  }
}

const deleteAccount = async (id) => {
  if (!confirm("Apakah Anda yakin ingin menghapus akun ini dari sistem?")) return
  try {
    await axios.delete(`/api/accounts/${id}`)
    fetchAccounts()
    fetchProxyStats()
  } catch (e) {
    console.error("Gagal menghapus akun", e)
  }
}

const maskProxy = (url) => {
  if (!url) return ''
  try {
    // Show abbreviated proxy: e.g. "http://1.2.x.x:8080"
    const clean = url.replace(/^https?:\/\//, '')
    const parts = clean.split(':')
    if (parts.length >= 2) {
      const host = parts[0]
      const port = parts[parts.length - 1]
      const hostParts = host.split('.')
      if (hostParts.length === 4) {
        return `${hostParts[0]}.${hostParts[1]}.x.x:${port}`
      }
      return `${host}:${port}`
    }
    return clean.substring(0, 20) + '...'
  } catch {
    return url.substring(0, 20) + '...'
  }
}

const formatDate = (isoStr) => {
  if (!isoStr) return '-'
  const date = new Date(isoStr)
  return date.toLocaleString('id-ID', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })
}

onMounted(() => {
  fetchAccounts()
  fetchProxyStats()
})
</script>

<style scoped>
.account-card {
  transition: all 0.3s cubic-bezier(0.165, 0.84, 0.44, 1);
}
.account-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 20px rgba(123, 92, 255, 0.15);
  border-color: rgba(123, 92, 255, 0.3);
}

.proxy-badge {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 20px;
  font-weight: 600;
  white-space: nowrap;
}
.proxy-active {
  background: rgba(0, 230, 118, 0.12);
  color: var(--accent-green);
  border: 1px solid rgba(0, 230, 118, 0.25);
}
.proxy-none {
  background: rgba(255, 77, 106, 0.12);
  color: #ff4d6a;
  border: 1px solid rgba(255, 77, 106, 0.25);
}
</style>
