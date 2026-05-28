<template>
  <div class="animate-in">
    <!-- Header -->
    <div class="page-header-row">
      <div>
        <h2 class="page-title">📝 <span class="accent">System</span> Logs</h2>
        <p style="color:var(--text-secondary); font-size:13px; margin-top:4px">Catatan aktivitas, debug, dan status otomasi bot secara real-time</p>
      </div>
      <div style="display:flex; gap:10px">
        <button class="btn btn-purple" @click="fetchLogs">🔄 Segarkan Logs</button>
        <button class="btn btn-red" @click="clearLogs">🗑️ Bersihkan Database Log</button>
      </div>
    </div>

    <!-- Filters & Search Toolbar -->
    <div class="card" style="padding:16px; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center; gap:20px; flex-wrap:wrap">
      <!-- Search Input -->
      <div class="header-search" style="width:300px">
        <span class="search-icon">🔍</span>
        <input v-model="searchQuery" type="text" placeholder="Cari pesan log..." @input="fetchLogs" />
      </div>

      <!-- Filters Buttons -->
      <div class="chart-filters">
        <button 
          v-for="l in levelOptions" 
          :key="l.value" 
          class="chart-filter-btn" 
          :class="{ active: activeLevel === l.value }"
          @click="activeLevel = l.value; fetchLogs()"
        >
          {{ l.label }}
        </button>
      </div>
    </div>

    <!-- Terminal Console View -->
    <div class="terminal-container">
      <div class="terminal-header">
        <div class="terminal-dots">
          <span class="dot dot-red"></span>
          <span class="dot dot-yellow"></span>
          <span class="dot dot-green"></span>
        </div>
        <span class="terminal-title">iconscout_downloader_bot.log</span>
      </div>
      <div class="terminal-body" ref="terminalBody">
        <div v-if="loading" class="terminal-line" style="color:var(--text-secondary)">
          [SYSTEM] Mengambil rekaman log aktivitas...
        </div>
        <div v-else-if="logs.length === 0" class="terminal-line" style="color:var(--text-secondary)">
          [SYSTEM] Database log kosong. Belum ada aktivitas.
        </div>
        <div v-else v-for="log in logs" :key="log.id" class="terminal-line">
          <span class="log-time">[{{ formatTime(log.timestamp) }}]</span>
          <span class="log-level" :class="'level-' + log.level">[{{ log.level.toUpperCase() }}]</span>
          <span class="log-msg">{{ log.message }}</span>
          <div class="log-details" v-if="log.details">{{ log.details }}</div>
        </div>
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
