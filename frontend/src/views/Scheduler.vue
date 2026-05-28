<template>
  <div class="animate-in">
    <div class="page-header-row">
      <div>
        <h2 class="page-title">🔗 <span class="accent">Target</span> & Automations</h2>
        <p style="color:var(--text-secondary); font-size:13px; margin-top:4px">Konfigurasikan target link unduhan atau grup kata kunci pencarian otomatis</p>
      </div>
      <button class="btn btn-purple" @click="store.showAddLinkModal = true">
        ➕ Tambah Target Baru
      </button>
    </div>

    <!-- Empty State -->
    <div v-if="schedules.length === 0" class="card" style="padding:60px 20px; text-align:center; display:flex; flex-direction:column; align-items:center; gap:16px">
      <div style="font-size:48px; filter:drop-shadow(0 0 10px var(--accent-purple))">🔗</div>
      <h3 style="font-size:18px; font-weight:700">Belum Ada Target Unduhan</h3>
      <p style="color:var(--text-secondary); max-width:380px; font-size:13px; margin:0">
        Konfigurasikan target kata kunci grup pencarian atau tempelkan daftar link IconScout premium Anda untuk mengaktifkan pengunduhan terjadwal.
      </p>
      <button class="btn btn-purple" @click="store.showAddLinkModal = true" style="margin-top:10px">
        Buat Target Pertama
      </button>
    </div>

    <!-- Schedules Grid -->
    <div v-else style="display:grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap:20px;">
      <div 
        v-for="s in schedules" 
        :key="s.id" 
        class="card schedule-card" 
        style="display:flex; flex-direction:column; gap:16px; position:relative"
      >
        <!-- Header -->
        <div style="display:flex; justify-content:space-between; align-items:flex-start">
          <div style="display:flex; flex-direction:column; gap:4px">
            <strong style="font-size:15px; color:white">{{ s.name }}</strong>
            <span style="font-size:11px; color:var(--text-secondary)">ID: #{{ s.id }}</span>
          </div>
          <!-- Active Toggle Pill -->
          <span 
            class="badge-glow" 
            :class="s.is_active ? 'badge-green' : 'badge-purple'"
            style="cursor:pointer"
            @click="toggleSchedule(s)"
          >
            {{ s.is_active ? '🟢 Active' : '⏸ Paused' }}
          </span>
        </div>

        <!-- Target Source Value -->
        <div style="background:var(--bg-input); padding:12px; border-radius:12px; border:1px solid var(--border-color); display:flex; flex-direction:column; gap:8px">
          <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--text-secondary)">
            <span>TIPE SUMBER</span>
            <strong style="color:white; text-transform:uppercase">{{ s.source_type === 'link' ? '🔗 Link List' : '🔍 Keyword Group' }}</strong>
          </div>
          <div style="font-size:12px; line-height:1.5; max-height:60px; overflow-y:auto; color:var(--text-secondary); word-break:break-all">
            <span style="color:white; font-weight:600">{{ s.source_type === 'link' ? 'URLs:' : 'Search:' }}</span>
            {{ s.source_value }}
          </div>
        </div>

        <!-- Specifications -->
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; font-size:11px">
          <div style="background:rgba(255,255,255,0.02); padding:8px; border-radius:8px; border:1px solid var(--border-color)">
            <span style="color:var(--text-secondary)">ASSET / FORMAT</span>
            <div style="font-weight:bold; margin-top:4px; text-transform:uppercase; display:flex; align-items:center; gap:6px">
              <span>{{ s.asset_type }}</span>
              <span style="font-size:10px; background:rgba(123,92,255,0.15); color:var(--accent-purple); padding:1px 4px; border-radius:4px">{{ s.format }}</span>
            </div>
          </div>
          <div style="background:rgba(255,255,255,0.02); padding:8px; border-radius:8px; border:1px solid var(--border-color)">
            <span style="color:var(--text-secondary)">LIMIT / TOTAL</span>
            <div style="font-weight:bold; margin-top:4px">
              Max {{ s.max_items }} <span style="color:var(--accent-green)">({{ s.total_downloaded }} done)</span>
            </div>
          </div>
        </div>

        <!-- Schedule / Cron Details -->
        <div style="font-size:12px; color:var(--text-secondary); display:flex; align-items:center; gap:8px">
          <span>⏰ Schedule:</span>
          <strong style="color:white">{{ translateCron(s.cron_expression) }}</strong>
        </div>

        <!-- Actions -->
        <div style="display:flex; gap:10px; margin-top:auto; border-top:1px solid var(--border-color); padding-top:14px">
          <button 
            @click="toggleSchedule(s)" 
            class="btn btn-dark" 
            style="flex:1; font-size:11px; padding:8px"
          >
            {{ s.is_active ? '⏸ Pause' : '▶ Resume' }}
          </button>
          <button 
            @click="runNow(s)" 
            class="btn btn-purple" 
            style="flex:1.2; font-size:11px; padding:8px"
            :disabled="s.running"
          >
            {{ s.running ? 'Running...' : '🚀 Run Now' }}
          </button>
          <button 
            @click="deleteSchedule(s.id)" 
            class="btn btn-red" 
            style="font-size:11px; padding:8px; min-width:40px"
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

const schedules = ref([])

const fetchSchedules = async () => {
  try {
    const res = await axios.get('/api/schedules')
    schedules.value = (res.data.data || []).map(s => ({
      ...s,
      running: false
    }))
  } catch (e) {
    console.error("Gagal mengambil schedules", e)
  }
}

const toggleSchedule = async (s) => {
  try {
    const res = await axios.post(`/api/schedules/${s.id}/toggle`)
    s.is_active = res.data.is_active
    fetchSchedules()
  } catch (e) {
    console.error(e)
  }
}

const runNow = async (s) => {
  s.running = true
  try {
    await axios.post(`/api/schedules/${s.id}/run-now`)
    alert(`Target '${s.name}' dipicu berjalan di background!`)
    fetchSchedules()
  } catch (e) {
    alert("Gagal memicu pengunduhan target.")
  } finally {
    s.running = false
  }
}

const deleteSchedule = async (id) => {
  if (!confirm("Apakah Anda yakin ingin menghapus konfigurasi target ini?")) return
  try {
    await axios.delete(`/api/schedules/${id}`)
    fetchSchedules()
  } catch (e) {
    console.error(e)
  }
}

const translateCron = (expr) => {
  if (expr === '0 0 1 1 *') return 'Manual Only'
  if (expr === '0 * * * *') return 'Setiap Jam'
  if (expr === '0 */6 * * *') return 'Setiap 6 Jam'
  if (expr === '0 0 * * *') return 'Setiap Hari'
  return expr // fallback raw expression
}

onMounted(() => fetchSchedules())
</script>

<style scoped>
.schedule-card {
  transition: all 0.3s cubic-bezier(0.165, 0.84, 0.44, 1);
}
.schedule-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 20px rgba(123, 92, 255, 0.15);
  border-color: rgba(123, 92, 255, 0.3);
}
</style>

