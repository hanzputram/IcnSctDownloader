<template>
  <div class="animate-in">
    <!-- Header -->
    <div class="page-header-row">
      <div>
        <h2 class="page-title">📦 <span class="accent">Download</span> Manager</h2>
        <p style="color:var(--text-secondary); font-size:13px; margin-top:4px">Pantau progres dan status unduhan seluruh aset IconScout premium</p>
      </div>
      <button class="btn btn-purple" @click="fetchTasks">🔄 Segarkan Data</button>
    </div>

    <!-- Summary Stats Cards -->
    <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:16px; margin-bottom:24px">
      <div class="card" style="padding:16px; text-align:center">
        <span style="font-size:11px; color:var(--text-secondary)">TOTAL TUGAS</span>
        <div style="font-size:24px; font-weight:bold; margin-top:4px">{{ totalTasks }}</div>
      </div>
      <div class="card" style="padding:16px; text-align:center">
        <span style="font-size:11px; color:var(--text-secondary)">COMPLETED</span>
        <div style="font-size:24px; font-weight:bold; color:var(--accent-green); margin-top:4px">{{ completedTasks }}</div>
      </div>
      <div class="card" style="padding:16px; text-align:center">
        <span style="font-size:11px; color:var(--text-secondary)">RUNNING / PENDING</span>
        <div style="font-size:24px; font-weight:bold; color:var(--accent-purple); margin-top:4px">{{ activeTasksCount }}</div>
      </div>
      <div class="card" style="padding:16px; text-align:center">
        <span style="font-size:11px; color:var(--text-secondary)">FAILED</span>
        <div style="font-size:24px; font-weight:bold; color:var(--accent-red); margin-top:4px">{{ failedTasks }}</div>
      </div>
    </div>

    <!-- Filters & Search Toolbar -->
    <div class="card" style="padding:16px; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center; gap:20px; flex-wrap:wrap">
      <!-- Search Input -->
      <div class="header-search" style="width:300px">
        <span class="search-icon">🔍</span>
        <input v-model="searchQuery" type="text" placeholder="Cari nama aset atau kata kunci..." @input="filterTasks" />
      </div>

      <!-- Filters Buttons -->
      <div class="chart-filters">
        <button 
          v-for="f in filterOptions" 
          :key="f.value" 
          class="chart-filter-btn" 
          :class="{ active: activeFilter === f.value }"
          @click="activeFilter = f.value; fetchTasks()"
        >
          {{ f.label }}
        </button>
      </div>
    </div>

    <!-- Tasks Grid/Table -->
    <div class="card" style="padding:0">
      <div v-if="loading" style="padding:40px; text-align:center; color:var(--text-secondary)">
        Menghubungkan ke server...
      </div>
      <div v-else-if="filteredTasks.length === 0" style="padding:40px; text-align:center; color:var(--text-secondary)">
        Tidak ada tugas unduhan yang ditemukan.
      </div>
      <div v-else class="table-container">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Sumber & Jenis Aset</th>
              <th>Format</th>
              <th>Status</th>
              <th>Ukuran File</th>
              <th>Tanggal</th>
              <th>Aksi</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in filteredTasks" :key="t.id">
              <td><span style="color:var(--text-secondary)">#{{ t.id }}</span></td>
              <td>
                <div style="display:flex; flex-direction:column; gap:4px; max-width:400px">
                  <strong style="text-overflow:ellipsis; overflow:hidden; white-space:nowrap" :title="t.asset_name || t.source_value">
                    {{ t.asset_name || t.source_value }}
                  </strong>
                  <span style="font-size:11px; color:var(--text-secondary); display:flex; align-items:center; gap:6px">
                    <span>{{ t.source_type === 'link' ? '🔗 Link' : '🔍 Keyword' }}</span>
                    <span style="opacity:0.3">•</span>
                    <span style="text-transform:capitalize">{{ t.asset_type || 'Aset' }}</span>
                  </span>
                </div>
              </td>
              <td>
                <span class="format-badge" :class="'format-' + t.format">{{ t.format.toUpperCase() }}</span>
              </td>
              <td>
                <span 
                  class="badge-glow" 
                  :class="{
                    'badge-green': t.status === 'completed',
                    'badge-purple': t.status === 'running',
                    'badge-red': t.status === 'failed',
                    'badge-yellow': t.status === 'pending'
                  }"
                  style="text-transform:capitalize"
                  :title="t.error_message"
                >
                  {{ t.status === 'completed' ? '🟢 Completed' : t.status === 'running' ? '🔵 Running...' : t.status === 'failed' ? '🔴 Failed' : '⏳ Pending' }}
                </span>
              </td>
              <td>
                <span>{{ formatBytes(t.file_size) }}</span>
              </td>
              <td>
                <span style="font-size:12px">{{ formatDate(t.created_at) }}</span>
              </td>
              <td>
                <div style="display:flex; gap:8px">
                  <a 
                    v-if="t.cloud_url" 
                    :href="t.cloud_url" 
                    target="_blank" 
                    class="btn btn-purple" 
                    style="padding:6px 10px; font-size:11px"
                  >
                    ☁️ Drive
                  </a>
                  <button 
                    @click="deleteTask(t.id)" 
                    class="btn btn-red" 
                    style="padding:6px 10px; font-size:11px"
                  >
                    🗑️
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { store } from '../store.js'

const tasks = ref([])
const loading = ref(false)
const searchQuery = ref('')
const activeFilter = ref('all')

const filterOptions = [
  { label: 'Semua', value: 'all' },
  { label: 'Completed', value: 'completed' },
  { label: 'Running', value: 'running' },
  { label: 'Pending', value: 'pending' },
  { label: 'Failed', value: 'failed' }
]

// Stats calculations
const totalTasks = computed(() => tasks.value.length)
const completedTasks = computed(() => tasks.value.filter(t => t.status === 'completed').length)
const failedTasks = computed(() => tasks.value.filter(t => t.status === 'failed').length)
const activeTasksCount = computed(() => tasks.value.filter(t => t.status === 'running' || t.status === 'pending').length)

const fetchTasks = async () => {
  loading.value = true
  try {
    const statusParam = activeFilter.value === 'all' ? '' : `?status=${activeFilter.value}`
    const res = await axios.get(`/api/tasks${statusParam}`)
    tasks.value = res.data.data || []
  } catch (e) {
    console.error("Gagal mengambil data tasks", e)
  } finally {
    loading.value = false
  }
}

const deleteTask = async (id) => {
  if (!confirm("Hapus catatan tugas unduhan ini?")) return
  try {
    await axios.delete(`/api/tasks/${id}`)
    fetchTasks()
  } catch (e) {
    console.error(e)
  }
}

// Search filtration
const filteredTasks = computed(() => {
  if (!searchQuery.value) return tasks.value
  const query = searchQuery.value.toLowerCase()
  return tasks.value.filter(t => 
    (t.asset_name && t.asset_name.toLowerCase().includes(query)) ||
    (t.source_value && t.source_value.toLowerCase().includes(query))
  )
})

const formatBytes = (bytes) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  const kb = bytes / 1024
  if (kb < 1024) return kb.toFixed(1) + ' KB'
  const mb = kb / 1024
  return mb.toFixed(1) + ' MB'
}

const formatDate = (isoStr) => {
  if (!isoStr) return '-'
  const date = new Date(isoStr)
  return date.toLocaleString('id-ID', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })
}

onMounted(() => fetchTasks())
</script>

<style scoped>
.format-badge {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: bold;
}
.format-png { background: rgba(0, 230, 118, 0.1); color: var(--accent-green); border: 1px solid rgba(0, 230, 118, 0.2); }
.format-svg { background: rgba(123, 92, 255, 0.1); color: var(--accent-purple); border: 1px solid rgba(123, 92, 255, 0.2); }
.format-jpg { background: rgba(255, 215, 0, 0.1); color: var(--accent-yellow); border: 1px solid rgba(255, 215, 0, 0.2); }
.format-eps { background: rgba(255, 77, 77, 0.1); color: var(--accent-red); border: 1px solid rgba(255, 77, 77, 0.2); }
</style>
