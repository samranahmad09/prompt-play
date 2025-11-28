import os
import json
import shutil
import platform
import subprocess
import urllib.request
import urllib.error
import socket
from flask import Flask, render_template_string, request, jsonify, send_file

# ==========================================
# CONFIGURATION
# ==========================================
OUTPUT_DIR = "generated_extension"
OPENAI_MODEL = "gpt-5"  # GPT-5 ONLY
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Simple in-memory context for the current server session
conversation_history = []  # list of {"role": "user"/"assistant", "content": "..."}

app = Flask(__name__)


# ==========================================
# OPENAI BACKEND (SERVER-SIDE ONLY)
# ==========================================

# This is your ORIGINAL systemPrompt (unchanged in meaning / structure)
SYSTEM_PROMPT = """
You are ChromeForge, running on the ${model} engine.

OBJECTIVE:
Create a Chrome Extension (Manifest V3) with a "Mind-Blowing", Modern UI using ONLY Vanilla CSS and JS.

STRICT CONSTRAINTS (CRITICAL):
1. NO EXTERNAL CDNs (No Bootstrap, No Tailwind).
2. ALL STYLING must be in a generated 'styles.css' file.
3. OUTPUT FORMAT: A single valid JSON object.

DESIGN RULES (Pure CSS Artistry):
- Theme: Dark Mode / Cyberpunk / Clean Glass.
- Techniques: Use CSS Variables, Backdrop Filters, Flexbox/Grid.
- Animations: Create @keyframes for entrance animations (e.g., slide-up, fade-in).
- UX: Buttons should transform on hover. Inputs should have glowing borders on focus.

JSON STRUCTURE:
{
    "analysis": "Brief technical summary.",
    "manifest": { ...Manifest V3... },
    "files": {
        "popup.html": "<!DOCTYPE html><html><head><link rel='stylesheet' href='styles.css'></head><body>...</body></html>",
        "styles.css": "/* All CSS Here */",
        "popup.js": "...",
        "content.js": "...",
        "background.js": "...",
        "icon.svg": "..."
    },
    "readme": "..."
}
"""


def call_openai_json(messages):
    """
    Call OpenAI Chat Completions API and return a parsed JSON object
    from the assistant's message content (response_format=json_object).
    Uses GPT-5 ONLY (no fallback).
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is not set. "
            "Export it before running the server."
        )

    payload = {
        "model": OPENAI_MODEL,
        "messages": messages,
        # Old code did not specify temperature, default is 1.0 -> we keep that.
        "temperature": 1.0,
        "response_format": {"type": "json_object"},
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OPENAI_API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            resp_data = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"OpenAI HTTPError {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"OpenAI URLError: {e.reason}") from e

    try:
        parsed = json.loads(resp_data)
        content = parsed["choices"][0]["message"]["content"].strip()
        # In case the model wraps JSON in ```json ... ```
        if content.startswith("```"):
            # Remove first ```... line
            content = content.split("```", 2)[1]
        return json.loads(content)
    except Exception as e:
        raise RuntimeError(
            f"Failed to parse OpenAI response as JSON: {e}\nRaw: {resp_data[:400]}"
        ) from e


# ==========================================
# EXTENSION FILE HANDLING (OLD BACKEND BEHAVIOR)
# ==========================================

PNG_ICON_BYTES = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
    b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)


def write_extension(data):
    """
    This is effectively your OLD /save backend behavior, turned into a helper.
    - data is the JSON from GPT-5: { manifest, files, readme }
    - returns (abs_path, written_files_list)
    """
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    written_files = []

    manifest = data.get('manifest', {})
    # Old backend: if icons not present, add defaults
    if 'icons' not in manifest:
        manifest['icons'] = {"16": "icon.png", "48": "icon.png", "128": "icon.png"}

    # manifest.json
    manifest_path = os.path.join(OUTPUT_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    written_files.append("manifest.json")

    # files
    files = data.get('files', {})
    for filename, content in files.items():
        path = os.path.join(OUTPUT_DIR, filename)
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        if filename.endswith(".svg"):
            # Same as OLD code
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            if "icon.png" not in files:
                with open(os.path.join(OUTPUT_DIR, "icon.png"), "wb") as f:
                    f.write(PNG_ICON_BYTES)
                written_files.append("icon.png")
        else:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

        written_files.append(filename)

    # README
    if 'readme' in data:
        readme_path = os.path.join(OUTPUT_DIR, "README.md")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(data['readme'])
        written_files.append("README.md")

    return os.path.abspath(OUTPUT_DIR), sorted(set(written_files))


def make_zip():
    """
    Create a ZIP of the generated_extension folder.
    Returns the absolute path to the zip file.
    """
    if not os.path.isdir(OUTPUT_DIR):
        raise RuntimeError("No generated_extension directory to zip.")
    zip_base = os.path.abspath("generated_extension")
    zip_path = shutil.make_archive(zip_base, 'zip', OUTPUT_DIR)
    return zip_path


# ==========================================
# OPTIONAL: CHROME LAUNCH HELPERS
# ==========================================

def find_chrome_executable():
    env_path = os.environ.get("CHROME_PATH")
    if env_path and (os.path.isfile(env_path) or shutil.which(env_path)):
        return env_path

    system = platform.system()
    candidates = []

    if system == "Windows":
        pf = os.environ.get("PROGRAMFILES", r"C:\Program Files")
        pf86 = os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")
        local_appdata = os.environ.get("LOCALAPPDATA", r"C:\Users\%USERNAME%\AppData\Local")
        candidates = [
            os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(pf86, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(local_appdata, "Google", "Chrome", "Application", "chrome.exe"),
        ]
    elif system == "Darwin":
        candidates = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    else:  # Linux
        candidates = [
            "google-chrome",
            "google-chrome-stable",
            "chromium-browser",
            "chromium",
        ]

    for c in candidates:
        if os.path.isfile(c) or shutil.which(c):
            return c

    return None


def launch_chrome_with_extension():
    chrome_path = find_chrome_executable()
    if not chrome_path:
        raise RuntimeError(
            "Could not locate Chrome/Chromium. "
            "Set CHROME_PATH to the chrome executable if you want auto-launch."
        )
    if not os.path.isdir(OUTPUT_DIR):
        raise RuntimeError("generated_extension does not exist. Generate first.")

    abs_ext = os.path.abspath(OUTPUT_DIR)
    args = [
        chrome_path,
        f"--load-extension={abs_ext}",
        "--new-window",
        "chrome://extensions/",
    ]
    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ==========================================
# UI TEMPLATE (NEW DESIGN, UNCHANGED)
# ==========================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChromeForge | Extension Generator</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
   
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        forge: {
                            dark: '#0f172a',
                            panel: '#1e293b',
                            accent: '#06b6d4',
                            purple: '#8b5cf6',
                            success: '#10b981'
                        }
                    },
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                        mono: ['JetBrains Mono', 'monospace'],
                    },
                    animation: {
                        'pulse-fast': 'pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                        'spin-slow': 'spin 3s linear infinite',
                    }
                }
            }
        }
    </script>

    <style>
        body { background-color: #0f172a; color: #e2e8f0; }
        .glass-panel {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .glow-text { text-shadow: 0 0 20px rgba(6, 182, 212, 0.5); }
        .scan-line {
            width: 100%;
            height: 2px;
            background: linear-gradient(to right, transparent, #06b6d4, transparent);
            position: absolute;
            animation: scan 2s linear infinite;
            opacity: 0.5;
        }
        @keyframes scan {
            0% { top: 0%; }
            100% { top: 100%; }
        }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #06b6d4; }
    </style>
</head>
<body class="min-h-screen flex flex-col relative overflow-x-hidden selection:bg-forge-accent selection:text-black">

    <div class="fixed inset-0 pointer-events-none">
        <div class="absolute top-[-10%] left-[-10%] w-96 h-96 bg-forge-accent/20 rounded-full blur-3xl"></div>
        <div class="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-forge-purple/20 rounded-full blur-3xl"></div>
    </div>

    <nav class="w-full p-6 flex justify-between items-center z-10 glass-panel border-b border-white/5 sticky top-0">
        <div class="flex items-center gap-3">
            <i class="fa-brands fa-chrome text-3xl text-forge-accent animate-pulse-fast"></i>
            <h1 class="text-2xl font-bold font-mono tracking-tighter">CHROME<span class="text-forge-accent glow-text">FORGE</span></h1>
        </div>
        <div class="flex gap-4 text-sm font-mono text-slate-400">
            <span class="flex items-center gap-2"><div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div> System Online · GPT-5</span>
            <span>v1.0.4 Prototype</span>
        </div>
    </nav>

    <main class="flex-grow container mx-auto px-4 py-12 z-10 grid lg:grid-cols-2 gap-12 items-start">
       
        <div class="space-y-8">
            <div class="space-y-2">
                <h2 class="text-4xl font-extrabold text-white leading-tight">
                    Forge Extensions <br>
                    with <span class="text-transparent bg-clip-text bg-gradient-to-r from-forge-accent to-forge-purple">Natural Language</span>
                </h2>
                <p class="text-slate-400 text-lg">
                    Describe functionality. We generate the manifest, scripts, UI and keep context for refinements.
                </p>
            </div>

            <div class="glass-panel rounded-2xl p-1 relative overflow-hidden group hover:border-forge-accent/50 transition-all duration-300">
                <div class="absolute inset-0 bg-gradient-to-r from-forge-accent/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
               
                <div class="bg-slate-900/90 rounded-xl p-6 relative z-10">
                    <label class="block text-xs font-mono text-forge-accent mb-2 uppercase tracking-widest">
                        <i class="fa-solid fa-terminal mr-2"></i>User Prompt
                    </label>
                    <textarea id="userPrompt" rows="5"
                        class="w-full bg-transparent text-lg text-white placeholder-slate-600 outline-none resize-none font-mono"
                        placeholder="e.g. Create an extension that blocks Facebook and shows a popup with a productivity timer..."></textarea>
                   
                    <div class="flex justify-between items-center mt-4 border-t border-slate-800 pt-4">
                        <div class="text-xs text-slate-500 font-mono">
                            <i class="fa-solid fa-bolt text-yellow-500 mr-1"></i> GPT-5 Model Running Server-Side
                        </div>
                        <button id="forgeButton" onclick="startForge()" class="bg-forge-accent hover:bg-cyan-400 text-slate-900 font-bold py-2 px-6 rounded-lg shadow-[0_0_20px_rgba(6,182,212,0.3)] hover:shadow-[0_0_30px_rgba(6,182,212,0.6)] transition-all flex items-center gap-2 group-active:scale-95">
                            <i class="fa-solid fa-hammer group-hover:rotate-45 transition-transform"></i>
                            INITIATE FORGE
                        </button>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
                <div class="p-4 rounded-xl border border-slate-700 bg-slate-800/50 flex items-center gap-3">
                    <div class="p-2 rounded-lg bg-purple-500/20 text-purple-400"><i class="fa-solid fa-file-code"></i></div>
                    <div>
                        <h4 class="font-bold text-sm">Manifest V3</h4>
                        <p class="text-xs text-slate-400">Auto-Generated JSON</p>
                    </div>
                </div>
                <div class="p-4 rounded-xl border border-slate-700 bg-slate-800/50 flex items-center gap-3">
                    <div class="p-2 rounded-lg bg-green-500/20 text-green-400"><i class="fa-solid fa-shield-halved"></i></div>
                    <div>
                        <h4 class="font-bold text-sm">Smart Permissions</h4>
                        <p class="text-xs text-slate-400">Contextual Detection</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="relative">
            <div class="glass-panel rounded-xl overflow-hidden shadow-2xl h-[500px] flex flex-col border border-slate-700">
                <div class="bg-slate-900 p-3 flex items-center gap-4 border-b border-slate-700">
                    <div class="flex gap-2">
                        <div class="w-3 h-3 rounded-full bg-red-500"></div>
                        <div class="w-3 h-3 rounded-full bg-yellow-500"></div>
                        <div class="w-3 h-3 rounded-full bg-green-500"></div>
                    </div>
                    <div class="text-xs font-mono text-slate-500 flex-grow text-center">chrome_forge_server.py — Execution</div>
                </div>

                <div class="flex-grow bg-black/80 p-6 font-mono text-sm overflow-y-auto relative" id="terminalBody">
                    <div class="scan-line pointer-events-none"></div>
                   
                    <div class="text-slate-500 mb-2">Microsoft Windows [Version 10.0.19045.4206]</div>
                    <div class="text-slate-500 mb-4">(c) FAST University Tech Society. All rights reserved.</div>
                   
                    <div class="mb-2">C:\\Users\\Dev\\ChromeForge&gt; <span class="text-forge-accent">waiting for input...</span></div>
                   
                    <div id="logOutput" class="space-y-2"></div>
                </div>

                <div id="filePreview" class="bg-slate-800 p-4 border-t border-slate-700 hidden transition-all">
                    <div class="text-xs font-bold text-slate-400 uppercase mb-2">Generated Assets</div>
                    <div class="flex gap-3 overflow-x-auto pb-2" id="fileIcons"></div>
                    <div class="flex gap-3 mt-3">
                        <button onclick="downloadExtension()" class="flex-1 bg-green-600 hover:bg-green-500 text-white font-mono text-sm py-2 rounded flex items-center justify-center gap-2">
                            <i class="fa-solid fa-download"></i> Download Unpacked Extension (ZIP)
                        </button>
                    </div>
                    <p class="mt-2 text-[11px] text-slate-400">
                        Tip: You can send another prompt like "change the popup button text" or "add a badge counter".
                        ChromeForge keeps context for this browser session.
                    </p>
                </div>
            </div>
        </div>

    </main>

    <script>
        const logOutput = document.getElementById('logOutput');
        const filePreview = document.getElementById('filePreview');
        const fileIcons = document.getElementById('fileIcons');
        const promptInput = document.getElementById('userPrompt');
        const forgeButton = document.getElementById('forgeButton');

        function delay(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }

        function logToTerminal(text, classes = "text-slate-300") {
            const line = document.createElement('div');
            line.className = classes;
            line.innerHTML = `<span class="opacity-50 text-xs mr-2">${new Date().toLocaleTimeString()}</span> ${text}`;
            logOutput.appendChild(line);
            const terminalBody = document.getElementById('terminalBody');
            terminalBody.scrollTop = terminalBody.scrollHeight;
        }

        function addFileIcon(filename) {
            let iconClass = "fa-file-code";
            let colorClass = "text-slate-400";
           
            if (filename.endsWith('html')) { iconClass = "fa-html5"; colorClass = "text-orange-500"; }
            if (filename.endsWith('css')) { iconClass = "fa-css3-alt"; colorClass = "text-blue-500"; }
            if (filename.endsWith('js')) { iconClass = "fa-js"; colorClass = "text-yellow-400"; }
            if (filename.includes('manifest')) { iconClass = "fa-gear"; colorClass = "text-slate-300"; }

            const div = document.createElement('div');
            div.className = "flex flex-col items-center bg-slate-900 p-2 rounded min-w-[60px] border border-slate-700 animate-pulse";
            div.innerHTML = `<i class="fa-brands ${iconClass} ${colorClass} text-xl mb-1"></i><span class="text-[10px] text-slate-400">${filename}</span>`;
            fileIcons.appendChild(div);
        }

        async function typeLine(text) {
            const div = document.createElement('div');
            div.className = "text-white font-bold";
            div.innerText = "C:\\\\Users\\\\Dev\\\\ChromeForge> ";
            logOutput.appendChild(div);
           
            for (let i = 0; i < text.length; i++) {
                div.innerHTML = "C:\\\\Users\\\\Dev\\\\ChromeForge> " + text.substring(0, i+1) + "<span class='animate-pulse'>_</span>";
                await delay(25);
            }
            div.innerHTML = "C:\\\\Users\\\\Dev\\\\ChromeForge> " + text;
        }

        async function startForge() {
            const text = promptInput.value.trim();
            if (!text) {
                logToTerminal("Error: Prompt cannot be empty.", "text-red-500");
                return;
            }

            const short = text.length > 48 ? text.substring(0, 48) + "..." : text;

            // Visual feedback
            await typeLine(`forge_extension "${short}"`);
            logToTerminal(">> DISPATCHING_TO_AI_BACKEND (GPT-5)...", "text-blue-400");
            logToTerminal(">> MODEL THINKING (using previous context if any)...", "text-purple-400 italic");

            filePreview.classList.add('hidden');

            const originalHTML = forgeButton.innerHTML;
            forgeButton.disabled = true;
            forgeButton.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> FORGING...';

            try {
                const res = await fetch("/forge", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ prompt: text })
                });

                if (!res.ok) {
                    const errText = await res.text();
                    throw new Error(`HTTP ${res.status}: ${errText}`);
                }

                const data = await res.json();
                if (data.status !== "success") {
                    throw new Error(data.message || "Unknown error from backend");
                }

                if (data.analysis) {
                    logToTerminal(`[AI_ANALYSIS] ${data.analysis}`, "text-cyan-300");
                }

                if (Array.isArray(data.files)) {
                    logToTerminal(">> WRITING_SOURCE_FILES...", "text-yellow-400");
                    fileIcons.innerHTML = "";
                    for (const file of data.files) {
                        addFileIcon(file);
                        logToTerminal(`   + created generated_extension/${file}`, "text-slate-300");
                        await delay(60);
                    }
                    filePreview.classList.remove('hidden');
                }

                logToTerminal(">> BUILD_SUCCESSFUL", "text-green-400 font-bold");
                if (data.path) {
                    logToTerminal(`Directory ready at: ${data.path}`, "text-slate-400");
                }
                if (data.tip) {
                    logToTerminal(data.tip, "text-slate-400 italic");
                }

            } catch (err) {
                logToTerminal(`❌ BACKEND ERROR: ${err.message}`, "text-red-400");
            } finally {
                forgeButton.disabled = false;
                forgeButton.innerHTML = originalHTML;
            }
        }

        async function downloadExtension() {
            try {
                const res = await fetch("/download");
                if (!res.ok) {
                    const errText = await res.text();
                    throw new Error(`HTTP ${res.status}: ${errText}`);
                }
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "generated_extension.zip";
                document.body.appendChild(a);
                a.click();
                a.remove();
                URL.revokeObjectURL(url);
                logToTerminal("ZIP downloaded: generated_extension.zip", "text-green-400");
            } catch (err) {
                logToTerminal(`Download error: ${err.message}`, "text-red-400");
            }
        }
    </script>
</body>
</html>
"""


# ==========================================
# FLASK ROUTES
# ==========================================

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/forge", methods=["POST"])
def forge():
    """
    Main forge endpoint:
    - Uses GPT-5 with your ORIGINAL system prompt.
    - Keeps contextual memory (conversation_history).
    - Writes extension using OLD backend behavior.
    """
    global conversation_history
    payload = request.get_json(silent=True) or {}
    prompt = (payload.get("prompt") or "").strip()

    if not prompt:
        return jsonify({"status": "error", "message": "Prompt is required"}), 400

    # Build messages with memory (same idea as OLD frontend: system + full history)
    conversation_history.append({"role": "user", "content": prompt})
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    try:
        ai_result = call_openai_json(messages)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    # Store assistant result in memory (JSON string, same as old code)
    conversation_history.append({"role": "assistant", "content": json.dumps(ai_result)})

    try:
        path, files = write_extension(ai_result)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to save files: {e}"}), 500

    tip = (
        "Tip: You can now send another prompt to refine this extension "
        '(e.g. "change the popup text", "highlight links instead of phone numbers"). '
        "ChromeForge remembers this session."
    )

    return jsonify({
        "status": "success",
        "analysis": ai_result.get("analysis", ""),
        "files": files,
        "path": path,
        "tip": tip,
    })


# Optional: keep /save for compatibility with your OLD backend contract
@app.route("/save", methods=["POST"])
def save_files():
    try:
        data = request.json or {}
        path, _ = write_extension(data)
        return jsonify({"status": "success", "path": path})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/download")
def download():
    try:
        zip_path = make_zip()
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    return send_file(zip_path, mimetype="application/zip",
                     as_attachment=True, download_name="generated_extension.zip")


@app.route("/launch", methods=["POST"])
def launch():
    try:
        launch_chrome_with_extension()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)
