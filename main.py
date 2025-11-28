import os
import json
import sys
from flask import Flask, render_template_string, request, jsonify

# ==========================================
# CONFIGURATION
# ==========================================
OUTPUT_DIR = "generated_extension"
app = Flask(__name__)

# ==========================================
# 1. THE AGENTIC UI (Visualizes the hidden steps)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChromeForge | Self-Correcting Engine</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600&family=JetBrains+Mono:wght@400;700&display=swap');
        
        body { font-family: 'Space Grotesk', sans-serif; background-color: #020617; color: #f8fafc; overflow: hidden; }
        
        .stars { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: -1; background: radial-gradient(circle at center, #1e293b 0%, #020617 100%); opacity: 0.5; }
        
        .glass-panel { 
            background: rgba(30, 41, 59, 0.4); 
            backdrop-filter: blur(12px); 
            border: 1px solid rgba(255, 255, 255, 0.05); 
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
        }

        .step-active { color: #4ade80; border-color: #4ade80; background: rgba(74, 222, 128, 0.1); }
        .step-pending { color: #64748b; border-color: #334155; }
        
        .msg-user { background: #172554; border: 1px solid #1e40af; border-radius: 12px 12px 0 12px; }
        .msg-ai { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); border: 1px solid #334155; border-radius: 12px 12px 12px 0; }
        
        /* Loading Bar Animation */
        .progress-container { width: 100%; height: 2px; background: #1e293b; position: absolute; top: 0; left: 0; }
        .progress-bar { height: 100%; background: #60a5fa; width: 0%; transition: width 0.5s ease; box-shadow: 0 0 10px #60a5fa; }
    </style>
</head>
<body class="h-screen flex flex-col">

    <div class="stars"></div>
    <div class="progress-container"><div id="progressBar" class="progress-bar"></div></div>

    <header class="h-16 border-b border-white/5 bg-slate-950/50 flex items-center justify-between px-6 z-20">
        <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded bg-blue-600 flex items-center justify-center text-white">
                <i class="fa-solid fa-shield-halved"></i>
            </div>
            <div>
                <h1 class="text-lg font-bold tracking-tight">ChromeForge <span class="text-blue-400">v6.0</span></h1>
                <p class="text-[10px] text-slate-400 font-mono">SELF-CORRECTING CORE</p>
            </div>
        </div>
        <div class="flex gap-4 text-xs font-mono">
             <div id="step1" class="px-3 py-1 border rounded-full step-pending transition-all"><i class="fa-solid fa-pen-ruler"></i> Draft</div>
             <div id="step2" class="px-3 py-1 border rounded-full step-pending transition-all"><i class="fa-solid fa-bug"></i> Audit</div>
             <div id="step3" class="px-3 py-1 border rounded-full step-pending transition-all"><i class="fa-solid fa-check"></i> Finalize</div>
        </div>
    </header>

    <main class="flex-1 flex overflow-hidden relative">
        
        <aside class="w-80 glass-panel border-r-0 border-white/5 flex flex-col z-10 hidden md:flex">
            <div class="p-6 space-y-6">
                <div>
                    <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">API Key</label>
                    <input type="password" id="apiKey" placeholder="sk-..." class="w-full bg-slate-900/50 border border-slate-700 rounded p-2 text-xs text-white focus:border-blue-500 outline-none font-mono">
                </div>
                <div>
                    <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Engine</label>
                    <select id="modelSelect" class="w-full bg-slate-900/50 border border-slate-700 rounded p-2 text-xs text-slate-300 outline-none">
                        <option value="gpt-5">GPT-5 (Auto-Fallback)</option>
                        <option value="gpt-4o">GPT-4o (High Speed)</option>
                    </select>
                </div>
                
                <div class="p-4 rounded border border-blue-500/20 bg-blue-500/5 mt-4">
                    <h3 class="text-xs font-bold text-blue-300 mb-2"><i class="fa-solid fa-rotate"></i> Two-Pass Verification</h3>
                    <ul class="text-[10px] text-slate-400 space-y-2 list-disc list-inside">
                        <li><strong>Pass 1:</strong> Generates creative logic & CSS.</li>
                        <li><strong>Pass 2:</strong> A separate AI agent audits the code for V3 compliance and functionality bugs.</li>
                    </ul>
                </div>
            </div>
            
            <div class="mt-auto p-6 border-t border-white/5">
                <div id="statusText" class="text-xs font-mono text-slate-500 truncate">System Idle.</div>
            </div>
        </aside>

        <section class="flex-1 flex flex-col relative bg-transparent">
            <div id="chatHistory" class="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth pb-32">
                <div class="flex justify-start animate-fade-in-up">
                    <div class="msg-ai p-5 max-w-xl shadow-lg">
                        <div class="flex items-center gap-2 mb-2 text-blue-400 text-xs font-bold uppercase">
                            <i class="fa-solid fa-robot"></i> System
                        </div>
                        <p class="text-sm text-slate-300 leading-relaxed">
                            <strong>Robust Mode Engaged.</strong><br>
                            I will now perform a logic check on every extension I generate. 
                            I will silently fix manifest errors and JS variable mismatches before showing you the result.
                        </p>
                    </div>
                </div>
            </div>

            <div class="absolute bottom-6 left-0 right-0 px-6 flex justify-center">
                <div class="w-full max-w-3xl glass-panel rounded-2xl p-2 flex items-end gap-2 transition-all">
                    <textarea id="promptInput" rows="1" 
                        class="w-full bg-transparent border-none text-white placeholder-slate-500 text-sm focus:ring-0 p-3 resize-none max-h-32"
                        placeholder="Describe the extension logic..."></textarea>
                    
                    <button onclick="runAgenticWorkflow()" id="sendBtn" class="mb-1 mr-1 bg-blue-600 hover:bg-blue-500 text-white p-2.5 rounded-xl transition-all flex items-center justify-center">
                        <i class="fa-solid fa-bolt text-sm"></i>
                    </button>
                </div>
            </div>
        </section>
    </main>

    <script>
        let conversationHistory = [];
        const chatContainer = document.getElementById('chatHistory');
        const promptInput = document.getElementById('promptInput');

        promptInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); runAgenticWorkflow(); }
        });

        function appendMessage(role, text) {
            const div = document.createElement('div');
            div.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`;
            div.innerHTML = `
                <div class="${role === 'user' ? 'msg-user' : 'msg-ai'} p-5 max-w-xl shadow-lg">
                    <div class="text-[10px] font-bold uppercase mb-1 ${role === 'user' ? 'text-blue-300 text-right' : 'text-blue-400'}">
                        ${role === 'user' ? 'You' : 'Architect'}
                    </div>
                    <div class="prose prose-invert prose-sm leading-relaxed whitespace-pre-wrap font-sans text-slate-200">${text}</div>
                </div>
            `;
            chatContainer.appendChild(div);
            chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: 'smooth' });
        }

        function updateProgress(step, pct) {
            document.getElementById('progressBar').style.width = pct + '%';
            if(step === 1) {
                document.getElementById('step1').className = "px-3 py-1 border rounded-full step-active transition-all";
                document.getElementById('statusText').innerText = "Phase 1: Generative Drafting...";
            }
            if(step === 2) {
                document.getElementById('step2').className = "px-3 py-1 border rounded-full step-active transition-all";
                document.getElementById('statusText').innerText = "Phase 2: Automated Code Audit...";
            }
            if(step === 3) {
                document.getElementById('step3').className = "px-3 py-1 border rounded-full step-active transition-all";
                document.getElementById('statusText').innerText = "Phase 3: Finalizing Files...";
            }
        }

        function resetProgress() {
            document.getElementById('progressBar').style.width = '0%';
            ['step1', 'step2', 'step3'].forEach(id => {
                document.getElementById(id).className = "px-3 py-1 border rounded-full step-pending transition-all";
            });
        }

        async function callAI(model, messages, apiKey) {
            try {
                const response = await fetch("https://api.openai.com/v1/chat/completions", {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "Authorization": `Bearer ${apiKey}` },
                    body: JSON.stringify({
                        model: model,
                        messages: messages,
                        response_format: { type: "json_object" }
                    })
                });

                if (!response.ok) {
                    // Fallback Logic
                    if(model.includes('gpt-5')) {
                        console.warn("GPT-5 unavailable. Falling back to GPT-4o");
                        return callAI('gpt-4o', messages, apiKey);
                    }
                    throw new Error((await response.json()).error.message);
                }
                return await response.json();
            } catch (e) {
                throw e;
            }
        }

        async function runAgenticWorkflow() {
            const apiKey = document.getElementById('apiKey').value;
            const prompt = promptInput.value.trim();
            const model = document.getElementById('modelSelect').value;
            const btn = document.getElementById('sendBtn');
            
            if (!apiKey) { alert("API Key Required"); return; }
            if (!prompt) return;

            appendMessage('user', prompt);
            promptInput.value = '';
            btn.disabled = true;
            btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i>`;
            
            resetProgress();
            
            try {
                // PHASE 1: DRAFTING
                updateProgress(1, 30);
                
                const draftSystemPrompt = `
                    You are ChromeForge Generator.
                    Create a Manifest V3 Chrome Extension based on user request.
                    
                    DESIGN:
                    - Use Pure CSS (No External CDNs).
                    - Create a 'styles.css' with glassmorphism/dark mode.
                    
                    OUTPUT: Valid JSON of files.
                `;

                const draftMessages = [
                    { role: "system", content: draftSystemPrompt },
                    ...conversationHistory,
                    { role: "user", content: prompt }
                ];

                const draftData = await callAI(model, draftMessages, apiKey);
                const draftJson = JSON.parse(draftData.choices[0].message.content);

                // PHASE 2: AUDITING (The Magic Step)
                updateProgress(2, 60);

                const auditSystemPrompt = `
                    You are a Senior Code Auditor for Chrome Extensions.
                    Review the INPUT JSON carefully.
                    
                    YOUR TASKS:
                    1. Check 'manifest.json' for V3 compliance (no 'background': {'scripts': ...}, use 'service_worker').
                    2. Check logic: Does content.js try to access elements that exist?
                    3. Check Message Passing: Do sendResponse/onMessage signatures match?
                    4. Check HTML/JS linking: Do IDs in document.getElementById match the HTML?
                    5. Fix any bugs found.
                    
                    OUTPUT: The CORRECTED JSON object.
                `;
                
                const auditMessages = [
                    { role: "system", content: auditSystemPrompt },
                    { role: "user", content: `Review and fix this code structure:\n${JSON.stringify(draftJson)}` }
                ];

                const auditData = await callAI('gpt-4o', auditMessages, apiKey); // Use 4o for fast auditing
                const finalJson = JSON.parse(auditData.choices[0].message.content);

                // PHASE 3: SAVING
                updateProgress(3, 90);
                
                // Add to history (we only add the FINAL valid code to history to keep context clean)
                conversationHistory.push({ role: "user", content: prompt });
                conversationHistory.push({ role: "assistant", content: JSON.stringify(finalJson) });

                const saveRes = await fetch("/save", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(finalJson)
                });
                const saveResult = await saveRes.json();

                if (saveResult.status === "success") {
                    updateProgress(3, 100);
                    appendMessage('assistant', `✅ **Extension Verified & Built.**\n${finalJson.analysis || "Code audit complete."}\n\n📂 **Path:** \`${saveResult.path}\``);
                } else {
                    throw new Error(saveResult.message);
                }

            } catch (error) {
                appendMessage('assistant', `❌ Workflow Error: ${error.message}`);
                document.getElementById('statusText').innerText = "Failed.";
                document.getElementById('progressBar').style.backgroundColor = '#ef4444';
            } finally {
                btn.disabled = false;
                btn.innerHTML = `<i class="fa-solid fa-bolt"></i>`;
                setTimeout(resetProgress, 5000);
            }
        }
    </script>
</body>
</html>
"""

# ==========================================
# 2. FLASK BACKEND
# ==========================================
@app.route('/')
def index(): return render_template_string(HTML_TEMPLATE)

@app.route('/save', methods=['POST'])
def save_files():
    try:
        data = request.json
        if os.path.exists(OUTPUT_DIR):
            import shutil
            shutil.rmtree(OUTPUT_DIR)
        os.makedirs(OUTPUT_DIR)

        manifest = data.get('manifest', {})
        if 'icons' not in manifest: manifest['icons'] = {"16": "icon.png", "48": "icon.png", "128": "icon.png"}
        with open(os.path.join(OUTPUT_DIR, "manifest.json"), "w") as f: json.dump(manifest, f, indent=2)

        files = data.get('files', {})
        for filename, content in files.items():
            path = os.path.join(OUTPUT_DIR, filename)
            if filename.endswith(".svg"):
                with open(path, "w") as f: f.write(content)
                if "icon.png" not in files:
                    with open(os.path.join(OUTPUT_DIR, "icon.png"), "wb") as f: f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
            else:
                with open(path, "w", encoding="utf-8") as f: f.write(content)

        if 'readme' in data:
            with open(os.path.join(OUTPUT_DIR, "README.md"), "w") as f: f.write(data['readme'])

        return jsonify({"status": "success", "path": os.path.abspath(OUTPUT_DIR)})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)