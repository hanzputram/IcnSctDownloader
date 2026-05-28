/**
 * Settings Component
 */

function renderSettings() {
    const content = document.getElementById('pageContent');

    content.innerHTML = `
        <div class="animate-in">
            <div class="page-header">
                <h2 class="page-title">⚙️ <span class="accent">Settings</span></h2>
                <p class="page-subtitle">Konfigurasi IconScout Bot</p>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:18px">
                <!-- Download Settings -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">📥 Download Settings</span>
                    </div>
                    <div class="card-body">
                        <div class="form-group">
                            <label class="form-label">Default Format</label>
                            <select class="form-select" id="settingsFormat">
                                <option value="png">PNG</option>
                                <option value="svg">SVG</option>
                                <option value="eps">EPS</option>
                                <option value="pdf">PDF</option>
                                <option value="json">Lottie JSON</option>
                            </select>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Min Delay (detik)</label>
                                <input type="number" class="form-input" id="settingsDelayMin" value="3" min="1" max="30">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Max Delay (detik)</label>
                                <input type="number" class="form-input" id="settingsDelayMax" value="6" min="1" max="60">
                            </div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Max Concurrent Downloads</label>
                            <input type="number" class="form-input" id="settingsMaxConcurrent" value="2" min="1" max="5">
                        </div>
                        <p class="text-muted" style="font-size:11px">⚠️ Delay lebih rendah = risiko rate limit lebih tinggi. Direkomendasikan minimal 3 detik.</p>
                    </div>
                </div>

                <!-- Cloud Storage -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">☁️ Cloud Storage</span>
                    </div>
                    <div class="card-body">
                        <div class="form-group">
                            <label class="form-label">Google Drive</label>
                            <div class="flex items-center gap-2">
                                <label class="toggle">
                                    <input type="checkbox" id="settingsGdrive">
                                    <span class="slider"></span>
                                </label>
                                <span class="text-muted" style="font-size:12px">Upload otomatis ke Google Drive</span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Credentials File Path</label>
                            <input type="text" class="form-input" id="settingsGdriveCredentials" value="./credentials.json" placeholder="./credentials.json">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Google Drive Folder ID (optional)</label>
                            <input type="text" class="form-input" id="settingsGdriveFolderId" placeholder="Kosongkan untuk root folder">
                        </div>
                        <p class="text-muted" style="font-size:11px">
                            📖 Untuk setup Google Drive:
                            <br>1. Buat project di <a href="https://console.cloud.google.com" target="_blank">Google Cloud Console</a>
                            <br>2. Enable Google Drive API
                            <br>3. Buat OAuth 2.0 credentials
                            <br>4. Download credentials.json ke folder project
                        </p>
                    </div>
                </div>

                <!-- IconScout API -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">🔑 IconScout API (Optional)</span>
                    </div>
                    <div class="card-body">
                        <div class="form-group">
                            <label class="form-label">Client ID</label>
                            <input type="text" class="form-input" id="settingsApiClientId" placeholder="Your Client-ID">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Client Secret</label>
                            <input type="password" class="form-input" id="settingsApiClientSecret" placeholder="Your Client-Secret">
                        </div>
                        <p class="text-muted" style="font-size:11px">
                            API credentials bersifat opsional. Bot menggunakan browser automation sebagai metode utama.
                            API digunakan sebagai fallback jika tersedia.
                        </p>
                    </div>
                </div>

                <!-- Browser Settings -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">🌐 Browser Settings</span>
                    </div>
                    <div class="card-body">
                        <div class="form-group">
                            <label class="form-label">Headless Mode</label>
                            <div class="flex items-center gap-2">
                                <label class="toggle">
                                    <input type="checkbox" id="settingsHeadless" checked>
                                    <span class="slider"></span>
                                </label>
                                <span class="text-muted" style="font-size:12px">Jalankan browser tanpa tampilan visual</span>
                            </div>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Browser Timeout (ms)</label>
                            <input type="number" class="form-input" id="settingsTimeout" value="30000" min="5000" max="120000" step="1000">
                        </div>
                        <p class="text-muted" style="font-size:11px">
                            Nonaktifkan headless untuk debug. Timeout tinggi dibutuhkan untuk koneksi lambat.
                        </p>
                    </div>
                </div>
            </div>

            <!-- System Info -->
            <div class="card mt-2">
                <div class="card-header">
                    <span class="card-title">ℹ️ System Info</span>
                </div>
                <div class="card-body">
                    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;font-size:13px">
                        <div>
                            <div class="text-muted" style="font-size:11px">Version</div>
                            <div class="text-primary"><strong>1.0.0</strong></div>
                        </div>
                        <div>
                            <div class="text-muted" style="font-size:11px">Engine</div>
                            <div class="text-primary">Playwright + FastAPI</div>
                        </div>
                        <div>
                            <div class="text-muted" style="font-size:11px">Database</div>
                            <div class="text-primary">SQLite</div>
                        </div>
                        <div>
                            <div class="text-muted" style="font-size:11px">API Docs</div>
                            <div><a href="/docs" target="_blank" class="text-cyan">Open Swagger UI →</a></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="mt-2 text-muted" style="font-size:11px;text-align:center">
                ⚠️ Settings disimpan di file <code>.env</code>. Edit manual untuk perubahan permanen, lalu restart server.
            </div>
        </div>
    `;
}
