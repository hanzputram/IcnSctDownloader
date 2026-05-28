import os

files = {
    'frontend/src/style.css': '''
:root {
  --bg-main: #13111C;
  --bg-sidebar: #0E0C15;
  --bg-card: #1E1B29;
  --bg-input: #1A1723;
  --accent-purple: #7B5CFF;
  --accent-green: #00E676;
  --accent-red: #FF4D4D;
  --accent-yellow: #FFD700;
  
  --text-primary: #FFFFFF;
  --text-secondary: #8F8F9A;
  --border-color: rgba(255, 255, 255, 0.08);
  
  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: var(--font-family);
  background-color: var(--bg-main);
  color: var(--text-primary);
  min-height: 100vh;
  display: flex;
}

#app {
  width: 100%;
}

.app-layout {
  display: flex;
  height: 100vh;
  width: 100%;
}

/* Sidebar */
.sidebar {
  width: 260px;
  background-color: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  padding: 24px 20px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 40px;
}

.sidebar-logo {
  background: var(--accent-purple);
  color: white;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 18px;
  box-shadow: 0 0 15px rgba(123, 92, 255, 0.4);
}

.sidebar-brand h1 {
  font-size: 16px;
  font-weight: 700;
  margin: 0;
}

.sidebar-brand span {
  font-size: 12px;
  color: var(--text-secondary);
}

.sidebar-nav {
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin-bottom: 4px;
  border-radius: 10px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.nav-item:hover, .nav-item.active {
  background: rgba(123, 92, 255, 0.1);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--accent-purple);
  box-shadow: 0 4px 15px rgba(123, 92, 255, 0.3);
}

.nav-badge {
  margin-left: auto;
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
}

.sidebar-bottom-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 20px;
}

.btn {
  padding: 12px;
  border-radius: 10px;
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s ease;
}

.btn-purple {
  background: var(--accent-purple);
  color: white;
  box-shadow: 0 4px 15px rgba(123, 92, 255, 0.3);
}

.btn-purple:hover {
  filter: brightness(1.1);
}

.btn-dark {
  background: var(--bg-card);
  color: white;
  border: 1px solid var(--border-color);
}

.btn-dark:hover {
  background: rgba(255, 255, 255, 0.05);
}

.btn-red {
  background: rgba(255, 77, 77, 0.15);
  color: var(--accent-red);
  border: 1px solid rgba(255, 77, 77, 0.3);
}

.btn-red:hover {
  background: rgba(255, 77, 77, 0.25);
}


/* Main Content */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 40px;
  border-bottom: 1px solid var(--border-color);
}

.header-search {
  position: relative;
  width: 400px;
}

.header-search input {
  width: 100%;
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  padding: 12px 16px 12px 40px;
  border-radius: 20px;
  color: white;
  outline: none;
  font-size: 14px;
}

.header-search input:focus {
  border-color: var(--accent-purple);
}

.search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-secondary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}

.icon-btn {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--bg-input);
  padding: 6px 16px 6px 6px;
  border-radius: 25px;
  border: 1px solid var(--border-color);
}

.user-avatar {
  background: var(--accent-purple);
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.user-details strong {
  font-size: 14px;
}

.user-details span {
  font-size: 11px;
  color: var(--text-secondary);
}

.page-content {
  flex: 1;
  overflow-y: auto;
  padding: 30px 40px;
}

/* Page Headers */
.page-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 30px;
}

.page-title h2 {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
}

.page-title span {
  color: var(--accent-green);
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.page-title span::before {
  content: '';
  display: block;
  width: 8px;
  height: 8px;
  background: var(--accent-green);
  border-radius: 50%;
  box-shadow: 0 0 10px var(--accent-green);
}

.sync-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.select-account {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  color: white;
  padding: 10px 16px;
  border-radius: 20px;
  outline: none;
  min-width: 200px;
}

.btn-sync {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  color: white;
  padding: 10px 16px;
  border-radius: 20px;
  cursor: pointer;
}

.btn-sync:hover {
  background: rgba(255, 255, 255, 0.05);
}

/* Grid & Cards */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  position: relative;
  overflow: hidden;
}

.card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.card-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(123, 92, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-purple);
}

.card-title {
  font-size: 11px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.card-value {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 16px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 16px;
}

.badge-glow {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 600;
}

.badge-green { background: rgba(0, 230, 118, 0.1); color: var(--accent-green); border: 1px solid rgba(0, 230, 118, 0.3); }
.badge-red { background: rgba(255, 77, 77, 0.1); color: var(--accent-red); border: 1px solid rgba(255, 77, 77, 0.3); }
.badge-purple { background: rgba(123, 92, 255, 0.1); color: var(--accent-purple); border: 1px solid rgba(123, 92, 255, 0.3); }

/* Charts Layout */
.charts-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.chart-title::before {
  content: '';
  display: block;
  width: 6px;
  height: 6px;
  background: var(--accent-purple);
  border-radius: 50%;
  box-shadow: 0 0 10px var(--accent-purple);
}

.chart-filters {
  display: flex;
  background: var(--bg-input);
  border-radius: 20px;
  padding: 4px;
}

.chart-filter-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  padding: 4px 12px;
  font-size: 12px;
  border-radius: 16px;
  cursor: pointer;
}

.chart-filter-btn.active {
  background: var(--accent-purple);
  color: white;
}

.chart-container {
  position: relative;
  height: 250px;
  width: 100%;
}
''',

    'frontend/src/App.vue': '''<template>
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
        <span class="nav-badge">0</span>
      </router-link>
      <router-link to="/manager" class="nav-item" active-class="active">
        <span class="nav-icon">📦</span>
        <span>Manager</span>
        <span class="nav-badge">70</span>
      </router-link>
      <router-link to="/accounts" class="nav-item" active-class="active">
        <span class="nav-icon">👥</span>
        <span>Accounts</span>
        <span class="nav-badge">1</span>
      </router-link>
      <router-link to="/links" class="nav-item" active-class="active">
        <span class="nav-icon">🔗</span>
        <span>Links</span>
        <span class="nav-badge">7</span>
      </router-link>
      <router-link to="/recap" class="nav-item" active-class="active">
        <span class="nav-icon">📋</span>
        <span>Recap</span>
        <span class="nav-badge">8</span>
      </router-link>
      <router-link to="/logs" class="nav-item" active-class="active">
        <span class="nav-icon">📝</span>
        <span>Logs</span>
        <span class="nav-badge">93</span>
      </router-link>
      <router-link to="/contributor" class="nav-item" active-class="active">
        <span class="nav-icon">👤</span>
        <span>Contributor</span>
        <span class="nav-badge">1</span>
      </router-link>
    </nav>

    <div class="sidebar-bottom-actions">
      <button class="btn btn-purple">
        <span style="font-size:18px">+</span> Tambah Akun
      </button>
      <button class="btn btn-dark">
        <span style="font-size:18px">+</span> Tambah Link
      </button>
      <button class="btn btn-red">
        <span style="font-size:12px">■</span> Stop Bot
      </button>
    </div>
  </aside>
</template>
''',

    'frontend/src/views/Dashboard.vue': '''<template>
  <div class="animate-in">
    <div class="page-header-row">
      <div class="page-title">
        <h2>IconScout Bot Overview</h2>
        <span>Dashboard akun: groupy_PRO</span>
      </div>
      <div class="sync-container">
        <select class="select-account">
          <option>groupy_PRO (cookie)</option>
        </select>
        <button class="btn-sync">🔄 Sync Downloads</button>
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
        <div class="card-value">77</div>
        <!-- Sparkline simulation using SVG -->
        <svg width="100%" height="30" viewBox="0 0 100 30" preserveAspectRatio="none">
          <path d="M0,25 L20,20 L40,22 L60,15 L80,18 L100,10" fill="none" stroke="var(--accent-green)" stroke-width="2" style="filter: drop-shadow(0 0 3px var(--accent-green))"></path>
        </svg>
        <div class="card-footer">
          <span>532 link done</span>
          <span class="badge-glow badge-green">Per akun</span>
        </div>
      </div>

      <!-- Items Downloaded -->
      <div class="card">
        <div class="card-header">
          <div class="card-icon">📦</div>
          <span class="card-title">ITEMS DOWNLOADED</span>
        </div>
        <div class="card-value">23,273</div>
        <svg width="100%" height="30" viewBox="0 0 100 30" preserveAspectRatio="none">
          <path d="M0,20 L20,22 L40,18 L60,20 L80,15 L100,12" fill="none" stroke="var(--accent-purple)" stroke-width="2" style="filter: drop-shadow(0 0 3px var(--accent-purple))"></path>
        </svg>
        <div class="card-footer" style="flex-direction: column; align-items: flex-start; gap: 4px;">
          <div style="display:flex; justify-content:space-between; width:100%">
            <span>IconScout: 12,880</span>
            <span style="color:var(--accent-green)">+10,393</span>
          </div>
          <span style="font-size:9px">10,393 pack</span>
        </div>
      </div>

      <!-- Accounts Aktif -->
      <div class="card">
        <div class="card-header">
          <div class="card-icon" style="color:var(--accent-red); background: rgba(255,77,77,0.1)">👥</div>
          <span class="card-title">ACCOUNTS AKTIF</span>
        </div>
        <div class="card-value">1</div>
        <svg width="100%" height="30" viewBox="0 0 100 30" preserveAspectRatio="none">
          <path d="M0,25 L20,22 L40,24 L60,20 L80,22 L100,18" fill="none" stroke="var(--accent-red)" stroke-width="2" style="filter: drop-shadow(0 0 3px var(--accent-red))"></path>
        </svg>
        <div class="card-footer">
          <span class="badge-glow badge-red">1 IP/VPN ready</span>
          <span>per akun</span>
        </div>
      </div>

      <!-- Real Earnings -->
      <div class="card">
        <div class="card-header">
          <div class="card-icon" style="color:var(--accent-yellow); background: rgba(255,215,0,0.1)">$</div>
          <span class="card-title">REAL EARNINGS</span>
        </div>
        <div class="card-value">$52.5728</div>
        <svg width="100%" height="30" viewBox="0 0 100 30" preserveAspectRatio="none">
          <path d="M0,25 L20,20 L40,22 L60,18 L80,12 L100,8" fill="none" stroke="var(--accent-yellow)" stroke-width="2" style="filter: drop-shadow(0 0 3px var(--accent-yellow))"></path>
        </svg>
        <div class="card-footer">
          <span>$0.00 hari ini</span>
          <span>518 dl</span>
        </div>
      </div>
    </div>

    <!-- Charts Section -->
    <div class="charts-grid">
      <!-- Line Chart -->
      <div class="card">
        <div class="chart-header">
          <div class="chart-title">Download Activity <span style="color:var(--text-secondary); font-size:12px; margin-left:8px; font-weight:normal">204 items</span></div>
          <div style="display:flex; align-items:center; gap: 12px">
            <div class="chart-filters">
              <button class="chart-filter-btn">7 Hari</button>
              <button class="chart-filter-btn active">30 Hari</button>
              <button class="chart-filter-btn">90 Hari</button>
            </div>
            <button class="icon-btn" style="width:30px; height:30px">🔄</button>
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
             <div style="font-size:24px; font-weight:bold">77</div>
          </div>
        </div>
        <div style="margin-top: 20px; display:flex; justify-content:space-between; background:var(--bg-input); padding:8px 12px; border-radius:12px; font-size:12px">
           <div style="display:flex; align-items:center; gap:8px">
             <div style="width:8px; height:8px; background:var(--accent-purple); border-radius:50%; box-shadow:0 0 5px var(--accent-purple)"></div>
             <strong>PNG</strong>
           </div>
           <span>77 <span style="color:var(--text-secondary); margin-left:8px">100%</span></span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
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

const lineChartData = ref(null)
const doughnutChartData = ref(null)

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
      tension: 0,
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
    tooltip: { enabled: false }
  }
}

onMounted(() => {
  // Setup Area Line Chart Data
  const ctx = document.createElement('canvas').getContext('2d')
  const gradient = ctx.createLinearGradient(0, 0, 0, 300)
  gradient.addColorStop(0, 'rgba(123, 92, 255, 0.4)')
  gradient.addColorStop(1, 'rgba(123, 92, 255, 0.0)')

  lineChartData.value = {
    labels: ['1', '3', '5', '7', '9', '11', '13'],
    datasets: [
      {
        label: 'Downloads',
        data: [40, 15, 65, 12, 40, 40, 10, 40, 10],
        fill: true,
        backgroundColor: gradient,
        borderColor: '#7B5CFF',
      }
    ]
  }

  // Setup Doughnut Chart Data
  doughnutChartData.value = {
    labels: ['PNG'],
    datasets: [
      {
        data: [100],
        backgroundColor: ['#7B5CFF'],
        borderWidth: 0,
        hoverOffset: 4
      }
    ]
  }
})
</script>
'''
}

for path, content in files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print('Redesign scaffold completed.')
