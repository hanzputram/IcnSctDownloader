<template>
  <div class="animate-in">
    <div class="page-header-row">
      <div class="page-title">
        <h2>IconScout Bot Overview</h2>
        <span>Dashboard realtime</span>
      </div>
      <div class="sync-container">
        <button class="btn-sync" @click="fetchData">🔄 Sync Downloads</button>
        <button class="btn btn-purple" style="padding: 10px 20px; border-radius: 20px;">+ Run New Task</button>
      </div>
    </div>

    <!-- 4 Stats Cards -->
    <div class="stat-grid">
      <!-- Total Tasks -->
      <div class="card">
        <div class="card-header">
          <div class="card-icon" style="color:var(--accent-green); background: rgba(0,230,118,0.1)">✓</div>
          <span class="card-title">TOTAL TASKS</span>
        </div>
        <div class="card-value">{{ stats.total_tasks || 0 }}</div>
        <!-- Sparkline simulation using SVG -->
        <svg width="100%" height="30" viewBox="0 0 100 30" preserveAspectRatio="none">
          <path :d="generateSparklinePath(stats.sparklines?.tasks)" fill="none" stroke="var(--accent-green)" stroke-width="2" style="filter: drop-shadow(0 0 3px var(--accent-green))"></path>
        </svg>
        <div class="card-footer">
          <span>{{ stats.today_downloads || 0 }} link done today</span>
          <span class="badge-glow badge-green">Running: {{ stats.running_tasks || 0 }}</span>
        </div>
      </div>

      <!-- Items Downloaded -->
      <div class="card">
        <div class="card-header">
          <div class="card-icon">📦</div>
          <span class="card-title">ITEMS DOWNLOADED</span>
        </div>
        <div class="card-value">{{ stats.items_downloaded || 0 }}</div>
        <svg width="100%" height="30" viewBox="0 0 100 30" preserveAspectRatio="none">
          <path :d="generateSparklinePath(stats.sparklines?.downloads)" fill="none" stroke="var(--accent-purple)" stroke-width="2" style="filter: drop-shadow(0 0 3px var(--accent-purple))"></path>
        </svg>
        <div class="card-footer" style="flex-direction: column; align-items: flex-start; gap: 4px;">
          <div style="display:flex; justify-content:space-between; width:100%">
            <span>Total Aset Tersimpan</span>
          </div>
        </div>
      </div>

      <!-- Accounts Aktif -->
      <div class="card">
        <div class="card-header">
          <div class="card-icon" style="color:var(--accent-red); background: rgba(255,77,77,0.1)">👥</div>
          <span class="card-title">ACCOUNTS AKTIF</span>
        </div>
        <div class="card-value">{{ stats.active_accounts || 0 }}</div>
        <svg width="100%" height="30" viewBox="0 0 100 30" preserveAspectRatio="none">
          <path :d="generateSparklinePath(stats.sparklines?.accounts)" fill="none" stroke="var(--accent-red)" stroke-width="2" style="filter: drop-shadow(0 0 3px var(--accent-red))"></path>
        </svg>
        <div class="card-footer">
          <span class="badge-glow badge-red">Total {{ stats.total_accounts || 0 }} akun</span>
        </div>
      </div>

      <!-- Total Storage -->
      <div class="card">
        <div class="card-header">
          <div class="card-icon" style="color:var(--accent-yellow); background: rgba(255,215,0,0.1)">💾</div>
          <span class="card-title">TOTAL STORAGE</span>
        </div>
        <div class="card-value">{{ stats.total_size_mb || 0 }} MB</div>
        <svg width="100%" height="30" viewBox="0 0 100 30" preserveAspectRatio="none">
          <path :d="generateSparklinePath(stats.sparklines?.storage)" fill="none" stroke="var(--accent-yellow)" stroke-width="2" style="filter: drop-shadow(0 0 3px var(--accent-yellow))"></path>
        </svg>
        <div class="card-footer">
          <span>Kapasitas Digunakan</span>
        </div>
      </div>
    </div>

    <!-- Charts Section -->
    <div class="charts-grid">
      <!-- Line Chart -->
      <div class="card">
        <div class="chart-header">
          <div class="chart-title">Download Activity <span style="color:var(--text-secondary); font-size:12px; margin-left:8px; font-weight:normal">{{ activityTotal }} items</span></div>
          <div style="display:flex; align-items:center; gap: 12px">
            <div class="chart-filters">
              <button class="chart-filter-btn" :class="{active: activityDays === 7}" @click="activityDays = 7; fetchActivity()">7 Hari</button>
              <button class="chart-filter-btn" :class="{active: activityDays === 30}" @click="activityDays = 30; fetchActivity()">30 Hari</button>
              <button class="chart-filter-btn" :class="{active: activityDays === 90}" @click="activityDays = 90; fetchActivity()">90 Hari</button>
            </div>
            <button class="icon-btn" style="width:30px; height:30px" @click="fetchActivity">🔄</button>
          </div>
        </div>
        <div class="chart-container">
          <LineChart v-if="lineChartData" :data="lineChartData" :options="lineOptions" />
        </div>
      </div>

      <!-- Doughnut Chart -->
      <div class="card">
        <div class="chart-header">
          <div class="chart-title">Format Breakdown</div>
        </div>
        <div class="chart-container" style="display:flex; justify-content:center; align-items:center; position:relative">
          <DoughnutChart v-if="doughnutChartData" :data="doughnutChartData" :options="doughnutOptions" style="max-height: 200px" />
          <div style="position:absolute; text-align:center">
             <div style="font-size:10px; color:var(--text-secondary)">TOTAL</div>
             <div style="font-size:24px; font-weight:bold">{{ formatTotal }}</div>
          </div>
        </div>
        <div style="margin-top: 20px; max-height: 100px; overflow-y: auto;">
           <div v-for="(item, index) in formatData" :key="item.format" style="display:flex; justify-content:space-between; background:var(--bg-input); padding:8px 12px; border-radius:12px; font-size:12px; margin-bottom: 4px;">
             <div style="display:flex; align-items:center; gap:8px">
               <div :style="{width:'8px', height:'8px', backgroundColor: getFormatColor(index), borderRadius:'50%', boxShadow:'0 0 5px ' + getFormatColor(index)}"></div>
               <strong>{{ item.format.toUpperCase() }}</strong>
             </div>
             <span>{{ item.count }} <span style="color:var(--text-secondary); margin-left:8px">{{ ((item.count / formatTotal) * 100).toFixed(0) }}%</span></span>
           </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ArcElement
} from 'chart.js'
import { Line as LineChart, Doughnut as DoughnutChart } from 'vue-chartjs'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ArcElement
)

const stats = ref({})
const activityDays = ref(30)
const activityTotal = ref(0)
const lineChartData = ref(null)

const formatData = ref([])
const formatTotal = ref(0)
const doughnutChartData = ref(null)

const formatColors = ['#7B5CFF', '#00E676', '#FF4D4D', '#FFD700', '#00BFFF', '#FF8C00']

const getFormatColor = (index) => {
  return formatColors[index % formatColors.length]
}

const lineOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false }
  },
  scales: {
    x: {
      grid: { display: false, color: 'rgba(255,255,255,0.05)' },
      ticks: { color: '#8F8F9A' }
    },
    y: {
      display: false,
      grid: { display: false }
    }
  },
  elements: {
    line: {
      tension: 0.3, // slight curve
      borderWidth: 2,
      borderColor: '#7B5CFF',
      shadowBlur: 10,
      shadowColor: 'rgba(123, 92, 255, 0.5)'
    },
    point: {
      radius: 3,
      backgroundColor: '#7B5CFF'
    }
  }
}

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '70%',
  plugins: {
    legend: { display: false },
    tooltip: { enabled: true }
  }
}

const fetchStats = async () => {
  try {
    const res = await axios.get('/api/dashboard/stats')
    stats.value = res.data
  } catch (e) {
    console.error("Failed to fetch stats", e)
  }
}

const fetchActivity = async () => {
  try {
    const res = await axios.get(`/api/dashboard/activity?days=${activityDays.value}`)
    const data = res.data
    activityTotal.value = data.total
    
    // Create gradient
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const gradient = ctx.createLinearGradient(0, 0, 0, 300)
    gradient.addColorStop(0, 'rgba(123, 92, 255, 0.4)')
    gradient.addColorStop(1, 'rgba(123, 92, 255, 0.0)')

    // For better display, only show day number for labels
    const displayLabels = data.labels.map(l => {
      const parts = l.split('-')
      return parts.length === 3 ? parts[2] : l
    })

    lineChartData.value = {
      labels: displayLabels,
      datasets: [
        {
          label: 'Downloads',
          data: data.values,
          fill: true,
          backgroundColor: gradient,
          borderColor: '#7B5CFF',
        }
      ]
    }
  } catch (e) {
    console.error("Failed to fetch activity", e)
  }
}

const fetchFormatBreakdown = async () => {
  try {
    const res = await axios.get('/api/dashboard/format-breakdown')
    const data = res.data
    
    formatData.value = data.data
    formatTotal.value = data.total
    
    if (formatData.value.length === 0) {
      // Empty state
       doughnutChartData.value = {
        labels: ['No Data'],
        datasets: [{
          data: [1],
          backgroundColor: ['#1A1723'],
          borderWidth: 0
        }]
      }
      return
    }

    doughnutChartData.value = {
      labels: formatData.value.map(d => d.format.toUpperCase()),
      datasets: [
        {
          data: formatData.value.map(d => d.count),
          backgroundColor: formatData.value.map((_, i) => getFormatColor(i)),
          borderWidth: 0,
          hoverOffset: 4
        }
      ]
    }
  } catch (e) {
    console.error("Failed to fetch format breakdown", e)
  }
}

const generateSparklinePath = (dataArray) => {
  if (!dataArray || dataArray.length === 0) return 'M0,20 L100,20'
  const min = Math.min(...dataArray)
  const max = Math.max(...dataArray)
  const range = max - min
  
  const points = dataArray.map((val, index) => {
    const x = (index / (dataArray.length - 1)) * 100
    const y = range === 0 ? 20 : 25 - ((val - min) / range) * 20
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  
  return 'M' + points.map((p, i) => (i === 0 ? p : 'L' + p)).join(' ')
}

const fetchData = () => {
  fetchStats()
  fetchActivity()
  fetchFormatBreakdown()
}

onMounted(() => {
  fetchData()
})
</script>
