"""
Interactive Web Application & Dashboard for AI Token Optimizer.
Runs on standard Python http.server without requiring external frameworks.
"""
import os
import sys
import json
import cgi
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from optimizer import TokenOptimizer
from tokenizer_utils import count_tokens, calculate_savings, MODEL_PRICING_PER_MILLION

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

HTML_UI = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Token Optimizer & Minifier</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --accent: #38bdf8;
            --accent-gradient: linear-gradient(135deg, #38bdf8, #818cf8);
            --accent-green: #34d399;
            --accent-red: #f87171;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --border: #334155;
            --border-hover: #475569;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.5;
            min-height: 100vh;
            padding: 24px;
        }

        .container {
            max-width: 1300px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            margin-bottom: 32px;
            padding: 24px 0;
            border-bottom: 1px solid var(--border);
        }

        .badge {
            display: inline-block;
            padding: 4px 14px;
            border-radius: 9999px;
            background: rgba(56, 189, 248, 0.1);
            color: var(--accent);
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 12px;
            border: 1px solid rgba(56, 189, 248, 0.25);
        }

        h1 {
            font-size: 32px;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }

        header p {
            color: var(--text-secondary);
            font-size: 16px;
            max-width: 700px;
            margin: 0 auto;
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 32px;
        }

        @media (max-width: 960px) {
            .dashboard-grid { grid-template-columns: 1fr; }
        }

        .card {
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 24px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.25);
        }

        .card-title {
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .tabs {
            display: flex;
            gap: 8px;
            background: #090d16;
            padding: 4px;
            border-radius: 10px;
            margin-bottom: 16px;
        }

        .tab-btn {
            flex: 1;
            padding: 8px 14px;
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.2s;
        }

        .tab-btn.active {
            background: var(--bg-card);
            color: var(--text-primary);
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }

        .drop-area {
            border: 2px dashed var(--border);
            border-radius: 12px;
            padding: 36px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
            background: rgba(15, 23, 42, 0.4);
        }

        .drop-area:hover, .drop-area.dragover {
            border-color: var(--accent);
            background: rgba(56, 189, 248, 0.05);
        }

        .drop-icon {
            font-size: 36px;
            margin-bottom: 10px;
            display: block;
        }

        textarea {
            width: 100%;
            height: 240px;
            background: #090d16;
            border: 1px solid var(--border);
            border-radius: 10px;
            color: var(--text-primary);
            padding: 14px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            resize: vertical;
            outline: none;
        }

        textarea:focus {
            border-color: var(--accent);
        }

        .form-row {
            display: flex;
            gap: 12px;
            margin-top: 14px;
            align-items: center;
        }

        select, button {
            background: #090d16;
            color: var(--text-primary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 14px;
            outline: none;
            cursor: pointer;
            font-family: inherit;
        }

        .btn-primary {
            background: var(--accent-gradient);
            color: #0f172a;
            font-weight: 700;
            border: none;
            flex: 1;
            transition: opacity 0.2s;
        }

        .btn-primary:hover {
            opacity: 0.92;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }

        .stat-box {
            background: #090d16;
            padding: 14px;
            border-radius: 10px;
            border: 1px solid var(--border);
            text-align: center;
        }

        .stat-label {
            font-size: 11px;
            color: var(--text-secondary);
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }

        .stat-value {
            font-size: 22px;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
        }

        .val-red { color: var(--accent-red); }
        .val-green { color: var(--accent-green); }
        .val-accent { color: var(--accent); }

        .pricing-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin-top: 10px;
        }

        .pricing-table th, .pricing-table td {
            padding: 8px 10px;
            text-align: left;
            border-bottom: 1px solid rgba(51, 65, 85, 0.4);
        }

        .pricing-table th {
            color: var(--text-secondary);
            font-weight: 600;
        }

        .pricing-table td:last-child {
            text-align: right;
            font-weight: 700;
            color: var(--accent-green);
            font-family: 'JetBrains Mono', monospace;
        }

        .output-box {
            position: relative;
            margin-top: 16px;
        }

        .copy-btn {
            position: absolute;
            top: 10px;
            right: 10px;
            font-size: 12px;
            padding: 5px 10px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-primary);
        }

        .benchmarks-section {
            margin-top: 32px;
        }

        .bench-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            text-align: left;
        }

        .bench-table th, .bench-table td {
            padding: 12px 14px;
            border-bottom: 1px solid var(--border);
        }

        .bench-table th {
            background: #090d16;
            color: var(--text-secondary);
            font-weight: 700;
        }

        .reduction-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 6px;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
        }

        .reduction-high { background: rgba(52, 211, 153, 0.2); color: var(--accent-green); border: 1px solid var(--accent-green); }
        .reduction-mid { background: rgba(56, 189, 248, 0.2); color: var(--accent); border: 1px solid var(--accent); }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="badge">⚡ Token Minimizer & Semantic Styler</div>
            <h1>AI Token Optimizer</h1>
            <p>Convierte PDFs, Word, Excel, CSV, JSON, HTML y Código a formatos semánticos ultra-eficientes que consumen hasta un 70% menos tokens en tu LLM favorito.</p>
        </header>

        <div class="dashboard-grid">
            <!-- INPUT PANEL -->
            <div class="card">
                <div class="card-title">
                    <span>📥 Entrada de Datos</span>
                    <span style="font-size: 12px; color: var(--text-secondary);">Soporta PDF, DOCX, XLSX, CSV, JSON, HTML, Code</span>
                </div>

                <div class="tabs">
                    <button class="tab-btn active" onclick="switchTab('upload')">Subir Archivo</button>
                    <button class="tab-btn" onclick="switchTab('paste')">Pegar Contenido / Código</button>
                </div>

                <div id="tab-upload">
                    <div class="drop-area" id="drop-zone" onclick="document.getElementById('file-input').click()">
                        <span class="drop-icon">📄</span>
                        <p style="font-weight: 600; margin-bottom: 4px;">Arrastra un archivo aquí o haz clic para seleccionar</p>
                        <p style="font-size: 12px; color: var(--text-secondary);">PDF, DOCX, XLSX, CSV, JSON, XML, HTML, PY, JS, TS, TXT, LOG</p>
                        <input type="file" id="file-input" style="display: none;" onchange="handleFileSelected(this.files[0])">
                    </div>
                    <div id="selected-file-info" style="margin-top: 12px; font-size: 13px; color: var(--accent); font-weight: 600; display: none;"></div>
                </div>

                <div id="tab-paste" style="display: none;">
                    <textarea id="raw-text-input" placeholder="Pega aquí tu código, HTML sucio, JSON extenso, o fragmento de texto..."></textarea>
                    <div class="form-row">
                        <select id="paste-ext" style="flex: 1;">
                            <option value=".json">JSON</option>
                            <option value=".html">HTML</option>
                            <option value=".py">Python</option>
                            <option value=".js">JavaScript / TypeScript</option>
                            <option value=".csv">CSV</option>
                            <option value=".xml">XML</option>
                            <option value=".txt">Texto Plano / Log</option>
                        </select>
                    </div>
                </div>

                <div class="form-row" style="margin-top: 18px;">
                    <select id="table-format" title="Formato para Tablas">
                        <option value="auto">Tablas: Auto (Menor tokens)</option>
                        <option value="markdown">Tablas: Markdown</option>
                        <option value="tsv">Tablas: TSV (Ultra-denso)</option>
                    </select>

                    <button class="btn-primary" onclick="optimizeCurrent()">⚡ Optimizar para IA</button>
                </div>

                <div style="margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--border); display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px; color: var(--text-secondary);">
                    <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                        <input type="checkbox" id="opt-strip-links"> 🔗 Eliminar URLs de enlaces
                    </label>
                    <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                        <input type="checkbox" id="opt-factor-constants" checked> 📊 Factorizar columnas constantes
                    </label>
                    <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                        <input type="checkbox" id="opt-strip-comments"> 💬 Eliminar comentarios de código
                    </label>
                    <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                        <input type="checkbox" id="opt-compact-indent"> 📐 Comprimir sangría (4→2 espacios)
                    </label>
                </div>
            </div>

            <!-- METRICS & OUTPUT PANEL -->
            <div class="card">
                <div class="card-title">
                    <span>📊 Métricas de Eficiencia</span>
                    <span id="opt-status" style="font-size: 12px; color: var(--text-secondary);">Listo</span>
                </div>

                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="stat-label">Tokens Antes</div>
                        <div class="stat-value val-red" id="stat-before">0</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Tokens Después</div>
                        <div class="stat-value val-green" id="stat-after">0</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Ahorro Real</div>
                        <div class="stat-value val-accent" id="stat-savings">0%</div>
                    </div>
                </div>

                <div style="font-size: 13px; font-weight: 700; margin-bottom: 8px;">💰 Ahorro Económico Estimado (por 100k consultas)</div>
                <table class="pricing-table">
                    <thead>
                        <tr><th>Modelo LLM</th><th>Coste Original</th><th>Coste Optimizado</th><th>Ahorro ($)</th></tr>
                    </thead>
                    <tbody id="pricing-body">
                        <tr><td>GPT-4o</td><td>-</td><td>-</td><td>$0.00</td></tr>
                        <tr><td>Claude 3.5 Sonnet</td><td>-</td><td>-</td><td>$0.00</td></tr>
                        <tr><td>Gemini 1.5 Pro</td><td>-</td><td>-</td><td>$0.00</td></tr>
                        <tr><td>Gemini 1.5 Flash</td><td>-</td><td>-</td><td>$0.00</td></tr>
                    </tbody>
                </table>

                <div class="output-box">
                    <div style="position: absolute; top: 10px; right: 10px; display: flex; gap: 6px; z-index: 10;">
                        <button class="copy-btn" onclick="copyOptimized()" style="position: static;">📋 Copiar</button>
                        <button class="copy-btn" onclick="downloadOptimized()" style="position: static; background: var(--accent); color: #0f172a; font-weight: 700;">📥 Descargar .md</button>
                    </div>
                    <textarea id="optimized-output" readonly placeholder="El texto optimizado en formato Markdown semántico aparecerá aquí..."></textarea>
                </div>
            </div>
        </div>

        <!-- BENCHMARKS SECTION -->
        <div class="card benchmarks-section">
            <div class="card-title">
                <span>🧪 Benchmarks Reales de Reducción por Formato</span>
                <button onclick="loadBenchmarks()" style="font-size: 12px; padding: 6px 12px;">🔄 Actualizar</button>
            </div>
            <div style="overflow-x: auto;">
                <table class="bench-table">
                    <thead>
                        <tr>
                            <th>Archivo de Muestra</th>
                            <th>Conversor Aplicado</th>
                            <th>Tokens Crudos</th>
                            <th>Tokens IA</th>
                            <th>Reducción</th>
                            <th>Impacto</th>
                        </tr>
                    </thead>
                    <tbody id="benchmarks-body">
                        <tr><td colspan="6" style="text-align: center; color: var(--text-secondary);">Cargando benchmarks empíricos...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        let selectedFile = null;
        let currentTab = 'upload';

        function switchTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            if (tab === 'upload') {
                event.target.classList.add('active');
                document.getElementById('tab-upload').style.display = 'block';
                document.getElementById('tab-paste').style.display = 'none';
            } else {
                event.target.classList.add('active');
                document.getElementById('tab-upload').style.display = 'none';
                document.getElementById('tab-paste').style.display = 'block';
            }
        }

        function handleFileSelected(file) {
            if (!file) return;
            selectedFile = file;
            const info = document.getElementById('selected-file-info');
            info.style.display = 'block';
            info.textContent = `📁 Archivo seleccionado: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        }

        // Drag and drop setup
        const dropZone = document.getElementById('drop-zone');
        ['dragenter', 'dragover'].forEach(e => dropZone.addEventListener(e, (evt) => { evt.preventDefault(); dropZone.classList.add('dragover'); }));
        ['dragleave', 'drop'].forEach(e => dropZone.addEventListener(e, (evt) => { evt.preventDefault(); dropZone.classList.remove('dragover'); }));
        dropZone.addEventListener('drop', (evt) => {
            const files = evt.dataTransfer.files;
            if (files.length > 0) handleFileSelected(files[0]);
        });

        async function optimizeCurrent() {
            const status = document.getElementById('opt-status');
            status.textContent = "⏳ Optimizando...";
            const tableFormat = document.getElementById('table-format').value;

            try {
                let formData = new FormData();
                formData.append('table_format', tableFormat);
                formData.append('strip_links', document.getElementById('opt-strip-links').checked ? 'true' : 'false');
                formData.append('factor_constants', document.getElementById('opt-factor-constants').checked ? 'true' : 'false');
                formData.append('strip_comments', document.getElementById('opt-strip-comments').checked ? 'true' : 'false');
                formData.append('compact_indent', document.getElementById('opt-compact-indent').checked ? 'true' : 'false');

                if (currentTab === 'upload') {
                    if (!selectedFile) {
                        alert("Por favor selecciona un archivo.");
                        status.textContent = "Listo";
                        return;
                    }
                    formData.append('mode', 'file');
                    formData.append('file', selectedFile);
                } else {
                    const text = document.getElementById('raw-text-input').value;
                    const ext = document.getElementById('paste-ext').value;
                    if (!text.trim()) {
                        alert("Por favor pega texto o código para optimizar.");
                        status.textContent = "Listo";
                        return;
                    }
                    formData.append('mode', 'text');
                    formData.append('content', text);
                    formData.append('extension', ext);
                }

                const res = await fetch('/api/optimize', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();

                if (data.error) {
                    alert("Error: " + data.error);
                    status.textContent = "Error";
                    return;
                }

                // Render metrics
                document.getElementById('stat-before').textContent = data.raw_tokens.toLocaleString();
                document.getElementById('stat-after').textContent = data.optimized_tokens.toLocaleString();
                document.getElementById('stat-savings').textContent = `-${data.reduction_percentage}%`;
                document.getElementById('optimized-output').value = data.optimized_text;

                // Render pricing
                const tbody = document.getElementById('pricing-body');
                tbody.innerHTML = '';
                const models = [
                    { name: 'GPT-4o', key: 'GPT-4o (o200k)', rate: 2.5 },
                    { name: 'Claude 3.5 Sonnet', key: 'Claude 3.5 Sonnet', rate: 3.0 },
                    { name: 'Gemini 1.5 Pro', key: 'Gemini 1.5 Pro', rate: 1.25 },
                    { name: 'Gemini 1.5 Flash', key: 'Gemini 1.5 Flash', rate: 0.075 }
                ];
                models.forEach(m => {
                    const origCost = (data.raw_tokens * 100000 / 1000000) * m.rate;
                    const optCost = (data.optimized_tokens * 100000 / 1000000) * m.rate;
                    const saved = origCost - optCost;
                    const tr = document.createElement('tr');
                    tr.innerHTML = `<td>${m.name}</td><td>$${origCost.toFixed(2)}</td><td>$${optCost.toFixed(2)}</td><td>+$${saved.toFixed(2)}</td>`;
                    tbody.appendChild(tr);
                });

                status.textContent = "✅ ¡Optimización completada!";
            } catch (err) {
                console.error(err);
                alert("Error procesando solicitud: " + err);
                status.textContent = "Error";
            }
        }

        function copyOptimized() {
            const ta = document.getElementById('optimized-output');
            ta.select();
            document.execCommand('copy');
            alert("¡Copiado al portapapeles!");
        }

        function downloadOptimized() {
            const text = document.getElementById('optimized-output').value;
            if (!text.trim()) {
                alert("No hay contenido optimizado para descargar.");
                return;
            }
            const blob = new Blob([text], { type: 'text/markdown;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            const baseName = selectedFile ? selectedFile.name.replace(/\.[^/.]+$/, "") : "contenido";
            link.download = `${baseName}.optimized.md`;
            link.click();
        }

        async function loadBenchmarks() {
            try {
                const res = await fetch('/api/benchmarks');
                const list = await res.json();
                const tbody = document.getElementById('benchmarks-body');
                tbody.innerHTML = '';
                list.forEach(b => {
                    const tr = document.createElement('tr');
                    const badgeClass = b.reduction > 40 ? 'reduction-high' : 'reduction-mid';
                    tr.innerHTML = `
                        <td><strong>${b.filename}</strong></td>
                        <td>${b.converter}</td>
                        <td>${b.raw_tokens.toLocaleString()}</td>
                        <td>${b.optimized_tokens.toLocaleString()}</td>
                        <td><span class="reduction-badge ${badgeClass}">-${b.reduction}%</span></td>
                        <td style="color: var(--accent-green); font-weight: 600;">-${b.saved_tokens} tokens</td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch (err) {
                console.error("Error loading benchmarks", err);
            }
        }

        window.onload = loadBenchmarks;
    </script>
</body>
</html>
"""

class OptimizerRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_UI.encode('utf-8'))
        elif self.path == '/api/benchmarks':
            self._handle_benchmarks()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/optimize':
            self._handle_optimize()
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_benchmarks(self):
        samples_dir = os.path.join(os.path.dirname(__file__), "samples")
        optimizer = TokenOptimizer()
        results = []
        if os.path.exists(samples_dir):
            for fname in sorted(os.listdir(samples_dir)):
                if fname.endswith('.optimized.md'):
                    continue
                fpath = os.path.join(samples_dir, fname)
                if os.path.isfile(fpath):
                    try:
                        res = optimizer.optimize_file(fpath, add_metadata_header=False)
                        results.append({
                            "filename": fname,
                            "converter": res["converter"],
                            "raw_tokens": res["raw_tokens"],
                            "optimized_tokens": res["optimized_tokens"],
                            "reduction": res["reduction_percentage"],
                            "saved_tokens": res["tokens_saved"],
                        })
                    except Exception as e:
                        pass
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(results).encode('utf-8'))

    def _handle_optimize(self):
        content_type = self.headers.get('content-type', '')
        if not content_type.startswith('multipart/form-data'):
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Expected multipart/form-data"}).encode('utf-8'))
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']}
        )

        mode = form.getvalue('mode', 'text')
        table_format = form.getvalue('table_format', 'auto')
        strip_links = form.getvalue('strip_links', 'false').lower() == 'true'
        factor_constants = form.getvalue('factor_constants', 'true').lower() == 'true'
        strip_comments = form.getvalue('strip_comments', 'false').lower() == 'true'
        compact_indent = form.getvalue('compact_indent', 'false').lower() == 'true'

        optimizer = TokenOptimizer()

        temp_path = None
        try:
            if mode == 'file' and 'file' in form:
                file_item = form['file']
                orig_name = file_item.filename
                _, ext = os.path.splitext(orig_name)
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tf:
                    tf.write(file_item.file.read())
                    temp_path = tf.name
            else:
                raw_text = form.getvalue('content', '')
                ext = form.getvalue('extension', '.txt')
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False, mode='w', encoding='utf-8') as tf:
                    tf.write(raw_text)
                    temp_path = tf.name

            out_temp = temp_path + ".out.md"
            res = optimizer.optimize_file(
                temp_path,
                output_path=out_temp,
                table_format=table_format,
                strip_links=strip_links,
                factor_constants=factor_constants,
                strip_comments=strip_comments,
                compact_indent=compact_indent
            )

            with open(out_temp, 'r', encoding='utf-8') as f:
                opt_content = f.read()

            response_payload = {
                "raw_tokens": res["raw_tokens"],
                "optimized_tokens": res["optimized_tokens"],
                "reduction_percentage": res["reduction_percentage"],
                "tokens_saved": res["tokens_saved"],
                "converter": res["converter"],
                "optimized_text": opt_content,
                "cost_savings": res["cost_savings"],
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response_payload).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        finally:
            if temp_path and os.path.exists(temp_path):
                try: os.remove(temp_path)
                except: pass
            if temp_path and os.path.exists(temp_path + ".out.md"):
                try: os.remove(temp_path + ".out.md")
                except: pass

def run_server(port: int = 8765):
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, OptimizerRequestHandler)
    print(f"🚀 Servidor de AI Token Optimizer activo en: http://127.0.0.1:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    run_server(port)
