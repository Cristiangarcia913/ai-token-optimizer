# 🚀 AI Token Optimizer & Document Minifier

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Token Savings](https://img.shields.io/badge/Token%20Reduction-Up%20to%2070%25-brightgreen.svg)](#-benchmarks-reales)
[![LLM Support](https://img.shields.io/badge/LLM-GPT--4o%20%7C%20Claude%203.5%20%7C%20Gemini%201.5-purple.svg)](#-ahorro-económico-estimado)

Herramienta modular de alto rendimiento diseñada para **convertir, sanitizar y condensar archivos de todo tipo** (PDF, Word DOCX, Excel XLSX, CSV, JSON, XML, HTML, Código Fuente y Logs) hacia un formato semántico optimizado (**Clean Markdown / Compact TSV / YAML**).

Reduce el consumo de tokens entre un **15% y un 70%**, elimina el fenómeno *"Lost in the Middle"*, previene el truncamiento en ventanas de contexto y recorta radicalmente la factura de inferencia en modelos como **GPT-4o**, **Claude 3.5 Sonnet**, **Gemini 1.5 Pro** y **DeepSeek V3**.

> 📖 **Informe Completo**: Para un análisis exhaustivo sobre los fundamentos de tokenización BPE, distracción del Transformer y modelado financiero de costes, consulta [INFORME_TECNICO.md](INFORME_TECNICO.md).

---

## 🌟 Características Principales

- **🧹 HTML & Web Semántico**: Elimina scripts, estilos CSS, tags de maquetación (`<div>`, `<span>`), cookies banners, metadatos y tracking, transformando el contenido central a Markdown limpio (**~70% de ahorro**).
- **📊 JSON / XML / YAML**:
  - Transforma colecciones homogéneas de objetos (típicas de APIs REST y bases de datos) en tablas Markdown o TSV (**~58-62% de ahorro**).
  - **Factorización de Constantes**: Detecta columnas que tienen el mismo valor en todos los registros y las extrae a una cabecera global única.
  - **Poda Recursiva de Nulos**: Elimina campos vacíos (`null`, `""`, `[]`) que saturan el contexto sin aportar señal.
- **📄 PDF Inteligente**: Deduplica cabeceras y pies de página recurrentes en cada página, une palabras cortadas por guiones (`inter- \n nacional` -> `internacional`) y corrige saltos de línea arbitrarios.
- **📝 Word (DOCX)**: Preserva jerarquías de títulos (`#`, `##`), listas con viñetas y tablas sin la sobrecarga visual o de formato XML.
- **📈 Excel (XLSX) & CSV**: Poda filas y columnas vacías residuales a la derecha, formateando automáticamente a la estructura tabular con menor coste de tokens (`tsv` o `markdown`).
- **💻 Código Fuente**: Elimina bloques de licencias de 30 líneas (Apache 2.0, MIT), comentarios prescindibles (`--strip-comments`), docstrings extensos (`--strip-docstrings`) y sangrías redundantes (`--compact-indent`).
- **⚡ Procesamiento Concurrente**: Procesamiento paralelo multihilo para optimizar carpetas masivas a alta velocidad.
- **🖥️ Dashboard Web + CLI**: Incluye tanto una interfaz de línea de comandos para terminal como una aplicación web interactiva con drag-and-drop.

---

## 🧪 Benchmarks Reales

Mediciones obtenidas empíricamente con el codificador BPE oficial de OpenAI (`o200k_base`):

| Formato Origen | Conversor | Tokens Originales | Tokens Optimizados | Reducción Real | Tokens Ahorrados |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **HTML (Web con scripts y ads)** | `HTMLConverter` | 1.048 | 301 | **-71.3%** | 747 |
| **JSON (40 clientes API)** | `StructuredDataConverter` | 4.389 | 1.669 | **-62.0%** | 2.720 |
| **Código Python (con licencia)** | `CodeConverter` | 402 | 241 | **-40.0%** | 161 |
| **PDF (Informe de 2 págs)** | `PDFConverter` | 181 | 147 | **-18.8%** | 34 |
| **CSV (Pipeline de ventas)** | `SheetConverter` | 1.076 | 1.040 | **-3.4%** | 36 |

---

## 💰 Ahorro Económico Estimado

Ahorro financiero directo proyectado por volumen de llamadas procesando lotes documentales típicos (~3.000 tokens ahorrados por consulta):

| Modelo | Tarifa Entrada (1M Tok) | Ahorro en 10.000 llamadas | Ahorro en 100.000 llamadas | Ahorro en 1.000.000 llamadas |
| :--- | :---: | :---: | :---: | :---: |
| **Claude 3.5 Sonnet** | \$3.00 | \$90.72 | **\$907.20** | **\$9.072.00** |
| **GPT-4o (o200k)** | \$2.50 | \$75.60 | **\$756.00** | **\$7.560.00** |
| **Gemini 1.5 Pro** | \$1.25 | \$37.80 | **\$378.00** | **\$3.780.00** |
| **GPT-4o-mini** | \$0.15 | \$4.54 | **\$45.36** | **\$453.60** |
| **DeepSeek V3** | \$0.14 | \$4.23 | **\$42.34** | **\$423.36** |

---

## 📦 Instalación

Requiere Python 3.9+:

```bash
git clone https://github.com/Cristiangarcia913/ai-token-optimizer.git
cd ai-token-optimizer
pip install -r requirements.txt
```

---

## 💻 Uso por Línea de Comandos (CLI)

### 1. Optimizar un archivo individual:
```bash
python cli.py documento.pdf
# Genera documento.optimized.md con reporte de tokens y coste
```

### 2. Procesar un directorio completo en lote (Batch Multihilo):
```bash
python cli.py ./mis_documentos/ -o ./documentos_optimizados/ --threads 8
```

### 3. Modo Máximo Ahorro para Tablas y JSON:
```bash
python cli.py datos.json --table-format tsv
```

### 4. Opciones Avanzadas de Reducción:
```bash
# Eliminar URLs de enlaces en Markdown/HTML (conservando el texto)
python cli.py articulo.html --strip-links

# Optimización profunda de código fuente
python cli.py script.py --strip-comments --strip-docstrings --compact-indent
```

---

## 🖥️ Interfaz Web Interactiva (Dashboard)

Lanza el servidor web local ligero:

```bash
python app.py
```

Abre en tu navegador: `http://127.0.0.1:8765`

- 📥 **Arrastra y suelta** cualquier archivo o pega fragmentos de texto/código.
- ⚡ **Ajusta parámetros** en tiempo real (formato de tablas, eliminación de enlaces o comentarios).
- 📊 **Visualiza la reducción** y el ahorro económico para GPT-4o, Claude y Gemini.
- 💾 **Descarga el archivo `.md` optimizado** o cópialo con un solo clic.

---

## 🤖 Integración con Claude (Desktop, Code, Web & API)

Puedes integrar este optimizador directamente con **Claude** para que cualquier documento sea pre-procesado automáticamente antes de llegar a su contexto:

### 1. Claude Desktop & Claude Code (Nativo vía MCP)
Anthropic soporta el **Model Context Protocol (MCP)**. Configura el servidor en tu `claude_desktop_config.json` (ubicado en `%APPDATA%\Claude\claude_desktop_config.json` en Windows o `~/Library/Application Support/Claude/` en macOS):

```json
{
  "mcpServers": {
    "token-optimizer": {
      "command": "python",
      "args": [
        "C:\\Users\\crist\\.gemini\\antigravity\\scratch\\ai-token-optimizer\\mcp_server.py"
      ]
    }
  }
}
```

Una vez configurado, Claude dispondrá automáticamente de la herramienta `read_and_optimize_file`. Puedes añadir a sus instrucciones personalizadas:
> *"Siempre que vayas a analizar o leer archivos locales, utiliza la herramienta `read_and_optimize_file` para procesar la información de forma compacta y ahorrar tokens."*

### 2. Claude Web (claude.ai en el navegador)
Para la versión web, utiliza el vigilante de carpetas automático:
```bash
python folder_watcher.py --watch ./claude_inbox
```
Cualquier PDF, Word, Excel o JSON que arrastres a la carpeta `claude_inbox/` se convertirá en cuestión de milisegundos en un `.optimized.md` listo para arrastrar directamente al chat de Claude.

### 3. Claude API (Python SDK)
```python
import anthropic
from optimizer import TokenOptimizer

client = anthropic.Anthropic()
optimizer = TokenOptimizer()

# Pre-procesar antes de enviar a Claude
doc_opt = optimizer.optimize_file("informe_financiero.pdf")["optimized_text"]

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": f"Analiza el siguiente documento:\n\n{doc_opt}"}
    ]
)
print(message.content[0].text)
```

---

## 🧩 Integración en Python (RAG & Agentes)

```python
from optimizer import TokenOptimizer

optimizer = TokenOptimizer(encoding_name="o200k_base")

# Optimizar archivo antes de inyectarlo en el contexto del LLM
res = optimizer.optimize_file(
    "informe_complejo.docx",
    output_path="contexto_ia.md",
    table_format="auto",
    strip_links=True
)

print(f"Tokens reducidos: {res['raw_tokens']} -> {res['optimized_tokens']} (-{res['reduction_percentage']}%)")
```

---

## 🧪 Ejecución de Tests

La suite de pruebas automatizadas valida la integridad de todos los conversores:

```bash
python tests/test_optimizer.py
```

---

## 📄 Licencia

Distribuido bajo la Licencia MIT. Consulta `LICENSE` para más información.
