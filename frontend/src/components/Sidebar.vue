<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <div class="sidebar-logo">i</div>
      <div class="sidebar-brand">
        <h1>IconScout</h1>
        <span>Bot</span>
      </div>
    </div>
    
    <nav class="sidebar-nav">
      <router-link to="/dashboard" class="nav-item" active-class="active">
        <span class="nav-icon">⚄</span>
        <span>Dashboard</span>
        <span class="nav-badge">{{ stats.running_tasks || 0 }}</span>
      </router-link>
      <router-link to="/manager" class="nav-item" active-class="active">
        <span class="nav-icon">📦</span>
        <span>Manager</span>
        <span class="nav-badge">{{ stats.total_tasks || 0 }}</span>
      </router-link>
      <router-link to="/accounts" class="nav-item" active-class="active">
        <span class="nav-icon">👥</span>
        <span>Accounts</span>
        <span class="nav-badge">{{ stats.active_accounts || 0 }}</span>
      </router-link>
      <router-link to="/links" class="nav-item" active-class="active">
        <span class="nav-icon">🔗</span>
        <span>Links</span>
        <span class="nav-badge">{{ stats.active_schedules || 0 }}</span>
      </router-link>
      <router-link to="/recap" class="nav-item" active-class="active">
        <span class="nav-icon">📋</span>
        <span>Recap</span>
        <span class="nav-badge">{{ stats.today_downloads || 0 }}</span>
      </router-link>
      <router-link to="/logs" class="nav-item" active-class="active">
        <span class="nav-icon">📝</span>
        <span>Logs</span>
        <span class="nav-badge">{{ stats.total_logs || 0 }}</span>
      </router-link>
      <router-link to="/contributor" class="nav-item" active-class="active">
        <span class="nav-icon">👤</span>
        <span>Contributor</span>
        <span class="nav-badge">1</span>
      </router-link>
    </nav>

    <div class="sidebar-bottom-actions">
      <button class="btn btn-purple" @click="store.showAddAccountModal = true">
        <span style="font-size:18px">+</span> Tambah Akun
      </button>
      <button class="btn btn-dark" @click="store.showAddLinkModal = true">
        <span style="font-size:18px">+</span> Tambah Link
      </button>
      <button 
        class="btn" 
        :class="store.botRunning ? 'btn-red' : 'btn-green-glow'" 
        @click="toggleBot"
        :disabled="toggling"
      >
        <span style="font-size:12px">{{ store.botRunning ? '■' : '▶' }}</span>
        {{ store.botRunning ? 'Stop Bot' : 'Start Bot' }}
      </button>
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import { store } from '../store.js'

const stats = ref({
  running_tasks: 0,
  total_tasks: 0,
  active_accounts: 0,
  active_schedules: 0,
  today_downloads: 0,
  total_logs: 0
})

const toggling = ref(false)
let intervalId = null

const fetchStats = async () => {
  try {
    const res = await axios.get('/api/dashboard/stats')
    stats.value = res.data
  } catch (e) {
    console.error("Gagal mengambil statistik sidebar", e)
  }
}

const fetchBotStatus = async () => {
  try {
    const res = await axios.get('/api/dashboard/bot-status')
    store.botRunning = res.data.status === 'running'
  } catch (e) {
    console.error("Gagal membaca status aktif bot", e)
  }
}

const toggleBot = async () => {
  toggling.value = true
  try {
    const res = await axios.post('/api/dashboard/bot-toggle')
    store.botRunning = res.data.status === 'running'
    // Refresh stats immediately
    fetchStats()
    store.triggerRefresh()
  } catch (e) {
    console.error("Gagal mengubah status aktif bot", e)
  } finally {
    toggling.value = false
  }
}

onMounted(() => {
  fetchStats()
  fetchBotStatus()
  // Poll every 10 seconds to keep stats updated
  intervalId = setInterval(() => {
    fetchStats()
    fetchBotStatus()
  }, 10000)
})

onBeforeUnmount(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>

