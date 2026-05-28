import os

files = {
    'frontend/src/router/index.js': '''import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Accounts from '../views/Accounts.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: Dashboard },
  { path: '/accounts', component: Accounts },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})
export default router
''',

    'frontend/src/main.js': '''import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)
app.use(router)
app.mount('#app')
''',

    'frontend/src/App.vue': '''<template>
  <div class="app-layout">
    <Sidebar />
    <main class="main-content">
      <header class="header">
        <div class="header-search">
          <span class="search-icon">🔍</span>
          <input type="text" placeholder="Search assets, tasks, logs..." />
        </div>
        <div class="header-actions">
          <div class="header-user">
            <div class="user-info">
              <div class="user-name">IconScout Bot</div>
              <div class="user-email">Ready</div>
            </div>
            <div class="avatar">🤖</div>
          </div>
        </div>
      </header>
      <div class="page-content">
        <router-view></router-view>
      </div>
    </main>
  </div>
</template>

<script setup>
import Sidebar from './components/Sidebar.vue'
</script>
''',

    'frontend/src/components/Sidebar.vue': '''<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <div class="sidebar-logo">iS</div>
      <div class="sidebar-brand">
        <h1>IconScout</h1>
        <span>Bot v2.0 (Vue)</span>
      </div>
    </div>
    <nav class="sidebar-nav">
      <div class="nav-section">
        <div class="nav-section-title">Main</div>
        <router-link to="/dashboard" class="nav-item" active-class="active">
          <span class="nav-icon">📊</span>
          <span>Dashboard</span>
        </router-link>
        <router-link to="/accounts" class="nav-item" active-class="active">
          <span class="nav-icon">👤</span>
          <span>Accounts</span>
        </router-link>
      </div>
    </nav>
  </aside>
</template>
''',

    'frontend/src/views/Dashboard.vue': '''<template>
  <div class="animate-in">
    <div class="page-header">
      <h2 class="page-title">📊 <span class="accent">Dashboard</span></h2>
      <p class="page-subtitle">Overview statistik dan status bot</p>
    </div>
    <div class="dashboard-grid">
      <div class="card stat-card">
        <h3>Total Downloads</h3>
        <div class="stat-value text-primary">--</div>
      </div>
      <div class="card stat-card">
        <h3>Active Accounts</h3>
        <div class="stat-value text-success">--</div>
      </div>
    </div>
  </div>
</template>
''',

    'frontend/src/views/Accounts.vue': '''<template>
  <div class="animate-in">
    <div class="page-header flex justify-between items-center">
      <div>
        <h2 class="page-title">👤 <span class="accent">Account</span> Manager</h2>
        <p class="page-subtitle">Kelola akun IconScout Anda</p>
      </div>
      <button class="btn btn-primary" @click="showAddModal = true">
        ➕ Tambah Account
      </button>
    </div>

    <div class="card">
      <div class="card-body" style="padding:0">
        <div v-if="accounts.length === 0" class="empty-state">
          <div class="empty-icon">👤</div>
          <h3>Belum Ada Account</h3>
          <p>Tambahkan akun IconScout Anda untuk mulai download asset</p>
        </div>
        
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>Email</th>
                <th>Status</th>
                <th>Proxy</th>
                <th>Plan</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="acc in accounts" :key="acc.id">
                <td>
                  <div class="flex items-center gap-1">
                    <div class="avatar" style="width:28px;height:28px;font-size:11px;background:var(--gradient-primary)">{{ acc.email[0].toUpperCase() }}</div>
                    <strong class="text-primary">{{ acc.email }}</strong>
                  </div>
                </td>
                <td>
                  <span class="badge" :class="'badge-' + (acc.status === 'active' ? 'success' : 'danger')">
                    {{ acc.status }}
                  </span>
                </td>
                <td>
                  <span v-if="acc.proxy_url" class="badge badge-success" style="font-size:11px" :title="acc.proxy_url">🛡️ Active</span>
                  <span v-else class="text-muted" style="font-size:11px">Off</span>
                </td>
                <td><span class="text-accent">{{ acc.plan_type }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const accounts = ref([])

const fetchAccounts = async () => {
  try {
    const res = await axios.get('/api/accounts')
    accounts.value = res.data.data || []
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  fetchAccounts()
})
</script>
'''
}

os.makedirs('frontend/src/router', exist_ok=True)
os.makedirs('frontend/src/views', exist_ok=True)
os.makedirs('frontend/src/components', exist_ok=True)

for path, content in files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print('Scaffolded Vue files.')
