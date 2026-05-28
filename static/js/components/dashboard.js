/**
 * Dashboard Page Component
 * Shows overview stats, activity chart, format breakdown, recent activity
 */

let activityChart = null;
let formatChart = null;

async function renderDashboard() {
    const content = document.getElementById('pageContent');

    // Fetch data
    const [stats, activity, formats, recent] = await Promise.all([
        API.get('/api/dashboard/stats').catch(() => ({})),
        API.get('/api/dashboard/activity?days=30').catch(() => ({ labels: [], values: [] })),
        API.get('/api/dashboard/format-breakdown').catch(() => ({ data: [], total: 0 })),
        API.get('/api/dashboard/recent-activity?limit=15').catch(() => ({ data: [] })),
    ]);

    content.innerHTML = `
        <div class="animate-in">
            <div class="page-header">
                <h2 class="page-title">📊 <span class="accent">Dashboard</span> Overview</h2>
                <p class="page-subtitle">Ringkasan aktivitas IconScout Bot</p>
            </div>

            <!-- Stat Cards -->
            <div class="stats-grid">
                <div class="stat-card purple">
                    <div class="stat-icon">✅</div>
                    <div class="stat-label">Total Tasks</div>
                    <div class="stat-value">${stats.total_tasks || 0}</div>
                    <div class="stat-change up">📈 ${stats.today_downloads || 0} hari ini</div>
                </div>
                <div class="stat-card cyan">
                    <div class="stat-icon">📥</div>
                    <div class="stat-label">Items Downloaded</div>
                    <div class="stat-value">${(stats.items_downloaded || 0).toLocaleString()}</div>
                    <div class="stat-change up">💾 ${stats.total_size_mb || 0} MB</div>
                </div>
                <div class="stat-card green">
                    <div class="stat-icon">👤</div>
                    <div class="stat-label">Active Accounts</div>
                    <div class="stat-value">${stats.active_accounts || 0}</div>
                    <div class="stat-change up">${stats.total_accounts || 0} total</div>
                </div>
                <div class="stat-card yellow">
                    <div class="stat-icon">⏰</div>
                    <div class="stat-label">Active Schedules</div>
                    <div class="stat-value">${stats.active_schedules || 0}</div>
                    <div class="stat-change ${stats.running_tasks > 0 ? 'up' : ''}">${stats.running_tasks || 0} running</div>
                </div>
            </div>

            <!-- Charts Row -->
            <div class="grid-2 mb-3">
                <!-- Activity Chart -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title"><span class="dot"></span> Download Activity</span>
                        <div class="filter-chips">
                            <button class="chip active" onclick="loadActivity(7, this)">7 Hari</button>
                            <button class="chip" onclick="loadActivity(30, this)">30 Hari</button>
                            <button class="chip" onclick="loadActivity(90, this)">90 Hari</button>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="activityChart"></canvas>
                        </div>
                    </div>
                    <div class="card-footer">
                        <span class="text-muted" style="font-size:12px">Total: ${activity.total || 0} downloads</span>
                        <button class="btn btn-sm btn-ghost" onclick="navigate('tasks')">Lihat Semua →</button>
                    </div>
                </div>

                <!-- Format Breakdown -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title"><span class="dot" style="background:var(--accent-primary)"></span> Format Breakdown</span>
                    </div>
                    <div class="card-body">
                        <div class="donut-container">
                            <div style="width:200px;height:200px;position:relative">
                                <canvas id="formatChart"></canvas>
                                <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center">
                                    <div style="font-size:10px;color:var(--text-muted)">TOTAL</div>
                                    <div style="font-size:26px;font-weight:800">${formats.total || 0}</div>
                                </div>
                            </div>
                            <div class="donut-legend" id="formatLegend"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Recent Activity -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title"><span class="dot" style="background:var(--accent-cyan)"></span> Aktivitas Terakhir</span>
                    <button class="btn btn-sm btn-ghost" onclick="navigate('logs')">Lihat Semua →</button>
                </div>
                <div class="card-body" style="padding:0;max-height:320px;overflow-y:auto">
                    ${(recent.data || []).length === 0 ? `
                        <div class="empty-state" style="padding:32px">
                            <div class="empty-icon">📭</div>
                            <h3>Belum Ada Aktivitas</h3>
                            <p>Mulai download pertama Anda untuk melihat aktivitas di sini</p>
                        </div>
                    ` : (recent.data || []).map(log => `
                        <div class="log-entry">
                            <div class="log-level ${log.level}"></div>
                            <div class="log-message">${log.message}</div>
                            <div class="log-time">${formatDate(log.timestamp)}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;

    // Render charts
    renderActivityChart(activity);
    renderFormatChart(formats);
}

function renderActivityChart(data) {
    const ctx = document.getElementById('activityChart');
    if (!ctx) return;

    if (activityChart) activityChart.destroy();

    // Shorten labels
    const labels = (data.labels || []).map(d => {
        const parts = d.split('-');
        return `${parts[2]}/${parts[1]}`;
    });

    activityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Downloads',
                data: data.values || [],
                borderColor: '#7c3aed',
                backgroundColor: 'rgba(124, 58, 237, 0.08)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 6,
                pointBackgroundColor: '#7c3aed',
                pointBorderColor: 'transparent',
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15,15,35,0.95)',
                    borderColor: 'rgba(124,58,237,0.3)',
                    borderWidth: 1,
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    cornerRadius: 8,
                    padding: 12,
                },
            },
            scales: {
                x: {
                    grid: { color: 'rgba(148,163,184,0.06)', drawBorder: false },
                    ticks: { color: '#64748b', font: { size: 10 }, maxTicksLimit: 10 },
                },
                y: {
                    grid: { color: 'rgba(148,163,184,0.06)', drawBorder: false },
                    ticks: { color: '#64748b', font: { size: 10 }, precision: 0 },
                    beginAtZero: true,
                },
            },
            interaction: { intersect: false, mode: 'index' },
        },
    });
}

function renderFormatChart(data) {
    const ctx = document.getElementById('formatChart');
    if (!ctx) return;

    if (formatChart) formatChart.destroy();

    const formatData = data.data || [];
    const colors = ['#7c3aed', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#3b82f6', '#8b5cf6'];

    if (formatData.length === 0) {
        formatData.push({ format: 'none', count: 1 });
    }

    formatChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: formatData.map(f => f.format.toUpperCase()),
            datasets: [{
                data: formatData.map(f => f.count),
                backgroundColor: colors.slice(0, formatData.length),
                borderColor: 'rgba(10,10,26,0.8)',
                borderWidth: 3,
                hoverOffset: 8,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            cutout: '72%',
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15,15,35,0.95)',
                    borderColor: 'rgba(124,58,237,0.3)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 10,
                },
            },
        },
    });

    // Render legend
    const legend = document.getElementById('formatLegend');
    if (legend) {
        legend.innerHTML = formatData.map((f, i) => `
            <div class="donut-legend-item">
                <div class="dot" style="background:${colors[i % colors.length]}"></div>
                <span>${f.format.toUpperCase()}</span>
                <strong>${f.count}</strong>
            </div>
        `).join('');
    }
}

async function loadActivity(days, btn) {
    // Update active chip
    if (btn) {
        btn.closest('.filter-chips').querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
    }

    const data = await API.get(`/api/dashboard/activity?days=${days}`).catch(() => ({ labels: [], values: [] }));
    renderActivityChart(data);

    // Update footer
    const footer = btn?.closest('.card')?.querySelector('.card-footer span');
    if (footer) footer.textContent = `Total: ${data.total || 0} downloads`;
}
