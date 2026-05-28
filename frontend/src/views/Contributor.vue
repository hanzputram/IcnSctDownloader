<template>
  <div class="animate-in">
    <div class="page-header-row">
      <div class="page-title">
        <h2>👤 <span class="accent">Contributor</span> Hub</h2>
        <p style="color:var(--text-secondary); font-size:13px; margin-top:4px">Profil pengembang dan spesifikasi sistem IconScout Bot</p>
      </div>
    </div>

    <div style="display:grid; grid-template-columns: 1fr 2fr; gap:30px; margin-top:10px">
      <!-- Profile Card -->
      <div class="card" style="display:flex; flex-direction:column; align-items:center; text-align:center; padding:30px 20px; gap:16px">
        <div style="width:100px; height:100px; border-radius:50%; background:linear-gradient(135deg, var(--accent-purple), var(--accent-green)); display:flex; align-items:center; justify-content:center; font-size:36px; font-weight:bold; color:white; box-shadow:0 0 20px rgba(123, 92, 255, 0.4)">
          KG
        </div>
        <div>
          <h3 style="font-size:18px; font-weight:700">kaserstudio</h3>
          <span style="font-size:12px; color:var(--text-secondary)">kaserstudio@gmail.com</span>
        </div>
        <div style="display:flex; gap:8px">
          <span class="badge-glow badge-purple" style="font-size:11px">Lead Developer</span>
          <span class="badge-glow badge-green" style="font-size:11px">Active Creator</span>
        </div>
        <div style="width:100%; border-top:1px solid var(--border-color); padding-top:16px; margin-top:10px">
          <p style="font-size:12px; color:var(--text-secondary); line-height:1.6">
            Mengembangkan otomasi pengunduh aset terintegrasi untuk mendownload secara instan dari IconScout dengan dukungan API dan simulasi Playwright.
          </p>
        </div>
      </div>

      <!-- System specifications & credits -->
      <div class="card" style="display:flex; flex-direction:column; gap:20px; padding:30px">
        <h3 style="font-size:16px; font-weight:600; display:flex; align-items:center; gap:8px">
          <span style="width:6px; height:6px; background:var(--accent-purple); border-radius:50%; box-shadow:0 0 10px var(--accent-purple)"></span>
          Sistem & Lisensi
        </h3>
        
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px">
          <div style="background:var(--bg-input); padding:16px; border-radius:12px; border:1px solid var(--border-color); display:flex; flex-direction:column; gap:6px">
            <span style="font-size:11px; color:var(--text-secondary)">VERSI APLIKASI</span>
            <strong style="font-size:14px; color:white">v1.0.0 (Production)</strong>
          </div>
          <div style="background:var(--bg-input); padding:16px; border-radius:12px; border:1px solid var(--border-color); display:flex; flex-direction:column; gap:6px">
            <span style="font-size:11px; color:var(--text-secondary)">TEKNOLOGI INTI</span>
            <strong style="font-size:14px; color:white">FastAPI + Vue 3 + SQLite</strong>
          </div>
          <div style="background:var(--bg-input); padding:16px; border-radius:12px; border:1px solid var(--border-color); display:flex; flex-direction:column; gap:6px">
            <span style="font-size:11px; color:var(--text-secondary)">STATUS SERVER</span>
            <strong style="font-size:14px; color:var(--accent-green)">🟢 Online & Realtime</strong>
          </div>
          <div style="background:var(--bg-input); padding:16px; border-radius:12px; border:1px solid var(--border-color); display:flex; flex-direction:column; gap:6px">
            <span style="font-size:11px; color:var(--text-secondary)">LISENSI PROYEK</span>
            <strong style="font-size:14px; color:white">MIT License</strong>
          </div>
        </div>

        <div style="margin-top:10px">
          <h4 style="font-size:13px; font-weight:600; margin-bottom:10px">Kontributor Repositori</h4>
          <div style="display:flex; align-items:center; gap:12px; background:var(--bg-input); padding:12px 16px; border-radius:12px; border:1px solid var(--border-color)">
            <div style="width:32px; height:32px; border-radius:50%; background:var(--accent-purple); display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:12px">
              H
            </div>
            <div style="display:flex; flex-direction:column">
              <strong style="font-size:13px">hanzputram</strong>
              <span style="font-size:11px; color:var(--text-secondary)">Pembuat Repositori Utama / IcnSctDownloader</span>
            </div>
            <span style="margin-left:auto; font-size:12px; color:var(--text-secondary)">Owner</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// No complex reactive logic needed for Contributor page
</script>
