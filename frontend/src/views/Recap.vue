<template>
  <div class="animate-in">
    <div class="page-header-row">
      <div class="page-title">
        <h2>📋 <span class="accent">Recap</span> & Analytics</h2>
        <p style="color:var(--text-secondary); font-size:13px; margin-top:4px">Analisis mendalam dan riwayat aktivitas bot</p>
      </div>
      <button class="btn btn-purple" @click="fetchData">🔄 Refresh Data</button>
    </div>

    <!-- Analytics Cards -->
    <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:20px; margin-bottom:24px;">
      <div class="card" style="display:flex; flex-direction:column; gap:10px">
        <span style="font-size:11px; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.5px">Rasio Keberhasilan</span>
        <div style="font-size:28px; font-weight:bold; color:var(--accent-green)">
          {{ successRate }}%
        </div>
        <div style="width:100%; height:6px; background:rgba(255,255,255,0.05); border-radius:3px; overflow:hidden">
          <div :style="{width: successRate + '%', height:'100%', background:'var(--accent-green)', boxShadow:'0 0 8px var(--accent-green)'}"></div>
        </div>
        <span style="font-size:11px; color:var(--text-secondary)">{{ stats.items_downloaded || 0 }} sukses dari {{ stats.total_tasks || 0 }} tugas</span>
      </div>

      <div class="card" style="display:flex; flex-direction:column; gap:10px">
        <span style="font-size:11px; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.5px">Total Data Terunduh</span>
        <div style="font-size:28px; font-weight:bold; color:var(--accent-purple)">
          {{ stats.total_size_mb || 0 }} MB
        </div>
        <div style="font-size:11px; color:var(--text-secondary)">Rata-rata: {{ averageSize }} MB per aset</div>
      </div>

      <div class="card" style="display:flex; flex-direction:column; gap:10px">
        <span style="font-size:11px; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.5px">Beban Kerja Harian</span>
        <div style="font-size:28px; font-weight:bold; color:var(--accent-yellow)">
          {{ stats.today_downloads || 0 }} Aset
        </div>
        <div style="font-size:11px; color:var(--text-secondary)">Selesai hari ini</div>
      </div>
    </div>

    <!-- Details Grid -->
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
      <!-- Format Breakdown -->
      <div class="card">
        <h3 style="font-size:16px; font-weight:600; margin-bottom:20px; display:flex; align-items:center; gap:8px">
          <span style="width:6px; height:6px; background:var(--accent-purple); border-radius:50%; box-shadow:0 0 10px var(--accent-purple)"></span>
          Format Rekapitulasi
        </h3>
        <div v-if="formats.length === 0" style="padding:20px; text-align:center; color:var(--text-secondary)">
          Belum ada data format tersedia.
        </div>
        <div v-else style="display:flex; flex-direction:column; gap:12px">
          <div v-for="(f, i) in formats" :key="f.format" style="background:var(--bg-input); padding:14px; border-radius:12px; border:1px solid var(--border-color)">
            <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:13px">
              <strong>{{ f.format.toUpperCase() }}</strong>
              <span>{{ f.count }} unduhan ({{ ((f.count / formatTotal) * 100).toFixed(1) }}%)</span>
            </div>
            <div style="width:100%; height:6px; background:rgba(255,255,255,0.05); border-radius:3px; overflow:hidden">
              <div :style="{width: ((f.count / formatTotal) * 100) + '%', height:'100%', background: getFormatColor(i), boxShadow: '0 0 8px ' + getFormatColor(i)}"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Task Status Recap -->
      <div class="card">
        <h3 style="font-size:16px; font-weight:600; margin-bottom:20px; display:flex; align-items:center; gap:8px">
          <span style="width:6px; height:6px; background:var(--accent-purple); border-radius:50%; box-shadow:0 0 10px var(--accent-purple)"></span>
          Status Tugas Bot
        </h3>
        <div style="display:flex; flex-direction:column; gap:12px">
          <div style="display:flex; justify-content:space-between; background:var(--bg-input); padding:14px; border-radius:12px; border:1px solid var(--border-color)">
            <span style="display:flex; align-items:center; gap:8px">🟢 Selesai (Completed)</span>
            <strong>{{ stats.items_downloaded || 0 }}</strong>
          </div>
          <div style="display:flex; justify-content:space-between; background:var(--bg-input); padding:14px; border-radius:12px; border:1px solid var(--border-color)">
            <span style="display:flex; align-items:center; gap:8px">🟡 Berjalan (Running)</span>
            <strong>{{ stats.running_tasks || 0 }}</strong>
          </div>
          <div style="display:flex; justify-content:space-between; background:var(--bg-input); padding:14px; border-radius:12px; border:1px solid var(--border-color)">
            <span style="display:flex; align-items:center; gap:8px">⏳ Menunggu (Pending)</span>
            <strong>{{ stats.pending_tasks || 0 }}</strong>
          </div>
          <div style="display:flex; justify-content:space-between; background:var(--bg-input); padding:14px; border-radius:12px; border:1px solid var(--border-color)">
            <span style="display:flex; align-items:center; gap:8px">🔴 Gagal (Failed)</span>
            <strong style="color:var(--accent-red)">{{ stats.failed_tasks || 0 }}</strong>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const stats = ref({})
const formats = ref([])
const formatTotal = ref(0)

const successRate = computed(() => {
  if (!stats.value.total_tasks) return 0
  return ((stats.value.items_downloaded / stats.value.total_tasks) * 100).toFixed(1)
})

const averageSize = computed(() => {
  if (!stats.value.items_downloaded) return 0
  return (stats.value.total_size_mb / stats.value.items_downloaded).toFixed(2)
})

const formatColors = ['#7B5CFF', '#00E676', '#FF4D4D', '#FFD700', '#00BFFF', '#FF8C00']
const getFormatColor = (i) => formatColors[i % formatColors.length]

const fetchData = async () => {
  try {
    const sRes = await axios.get('/api/dashboard/stats')
    stats.value = sRes.data
    
    const fRes = await axios.get('/api/dashboard/format-breakdown')
    formats.value = fRes.data.data || []
    formatTotal.value = fRes.data.total || 0
  } catch (e) {
    console.error("Gagal mengambil data rekap", e)
  }
}

onMounted(() => fetchData())
</script>
