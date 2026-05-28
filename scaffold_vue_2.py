import os

files = {
    'frontend/src/router/index.js': '''import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Accounts from '../views/Accounts.vue'
import Tasks from '../views/Tasks.vue'
import Scheduler from '../views/Scheduler.vue'
import Logs from '../views/Logs.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: Dashboard },
  { path: '/accounts', component: Accounts },
  { path: '/tasks', component: Tasks },
  { path: '/scheduler', component: Scheduler },
  { path: '/logs', component: Logs },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})
export default router
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
        <router-link to="/tasks" class="nav-item" active-class="active">
          <span class="nav-icon">📥</span>
          <span>Downloads</span>
        </router-link>
        <router-link to="/scheduler" class="nav-item" active-class="active">
          <span class="nav-icon">⏰</span>
          <span>Scheduler</span>
        </router-link>
      </div>
      <div class="nav-section">
        <div class="nav-section-title">System</div>
        <router-link to="/logs" class="nav-item" active-class="active">
          <span class="nav-icon">📋</span>
          <span>Logs</span>
        </router-link>
      </div>
    </nav>
  </aside>
</template>
''',

    'frontend/src/views/Tasks.vue': '''<template>
  <div class="animate-in">
    <div class="page-header flex justify-between items-center">
      <div>
        <h2 class="page-title">📥 <span class="accent">Downloads</span></h2>
        <p class="page-subtitle">Pantau progress download aset</p>
      </div>
      <button class="btn btn-primary" @click="fetchTasks">🔄 Refresh</button>
    </div>
    <div class="card">
      <div class="card-body">
        <p v-if="tasks.length === 0">Belum ada task download.</p>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>URL / Search</th>
                <th>Status</th>
                <th>Progress</th>
                <th>Tanggal</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="task in tasks" :key="task.id">
                <td>{{ task.target_url || task.search_query }}</td>
                <td>{{ task.status }}</td>
                <td>{{ task.downloaded_items }} / {{ task.max_items || '?' }}</td>
                <td>{{ task.created_at }}</td>
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

const tasks = ref([])

const fetchTasks = async () => {
  try {
    const res = await axios.get('/api/tasks')
    tasks.value = res.data.data || []
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => fetchTasks())
</script>
''',

    'frontend/src/views/Scheduler.vue': '''<template>
  <div class="animate-in">
    <div class="page-header">
      <h2 class="page-title">⏰ <span class="accent">Scheduler</span></h2>
      <p class="page-subtitle">Konfigurasi otomatisasi download</p>
    </div>
    <div class="card">
      <div class="card-body">
        <p>Scheduler belum aktif di Vue UI. Akan segera hadir!</p>
      </div>
    </div>
  </div>
</template>
''',

    'frontend/src/views/Logs.vue': '''<template>
  <div class="animate-in">
    <div class="page-header">
      <h2 class="page-title">📋 <span class="accent">System Logs</span></h2>
      <p class="page-subtitle">Log aktivitas sistem terbaru</p>
    </div>
    <div class="card">
      <div class="card-body">
        <pre v-if="logs.length > 0" class="log-viewer">{{ logs.join('\\n') }}</pre>
        <p v-else>Loading logs...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const logs = ref([])

const fetchLogs = async () => {
  try {
    const res = await axios.get('/api/logs')
    logs.value = res.data.data || []
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => fetchLogs())
</script>
'''
}

for path, content in files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print('Scaffolded remaining Vue files.')
