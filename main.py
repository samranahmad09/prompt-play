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
# 1. THE WEB INTERFACE
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChromeForge | GPT-5 Architecture Node</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&family=JetBrains+Mono:wght@400;700&display=swap');
        
        body { font-family: 'Outfit', sans-serif; background-color: #000000; color: #f8fafc; overflow: hidden; }
        
        /* Starfield Background */
        .stars { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: -1; background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%); }
        
        .glass-panel { 
            background: rgba(255, 255, 255, 0.02); 
            backdrop-filter: blur(16px); 
            border: 1px solid rgba(255, 255, 255, 0.08); 
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        }

        .neon-border { border: 1px solid rgba(139, 92, 246, 0.5); box-shadow: 0 0 15px rgba(139, 92, 246, 0.2); }
        .gradient-text { background: linear-gradient(135deg, #a78bfa 0%, #2dd4bf 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        
        /* Chat Styles */
        .msg-user { background: #1e1b4b; border: 1px solid #4338ca; border-radius: 16px 16px 0 16px; }
        .msg-ai { background: linear-gradient(180deg, #111827 0%, #0f172a 100%); border: 1px solid #334155; border-radius: 16px 16px 16px 0; }
        
        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-thumb { background: #475569; border-radius: 3px; }
    </style>
</head>
<body class="h-screen flex flex-col">

    <div class="stars"></div>

    <header class="h-16 border-b border-white/10 bg-black/50 backdrop-blur-md flex items-center justify-between px-6 z-20">
        <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-600 to-teal-500 flex items-center justify-center shadow-lg shadow-violet-500/20">
                <i class="fa-solid fa-brain text-white text-xs"></i>
            </div>
            <h1 class="text-xl font-bold tracking-tight">Chrome<span class="gradient-text">Forge</span> <span class="text-[10px] text-gray-500 border border-gray-700 px-1 rounded ml-2">NEXT-GEN ENGINE</span></h1>
        </div>
        <div class="flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-teal-500 animate-pulse"></span>
            <span class="text-xs font-mono text-teal-500">ONLINE</span>
        </div>
    </header>

    <main class="flex-1 flex overflow-hidden relative">
        
        <aside class="w-80 glass-panel border-r-0 border-white/10 flex flex-col z-10 hidden md:flex">
            <div class="p-6 space-y-6">
                <div>
                    <label class="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">API Key</label>
                    <input type="password" id="apiKey" placeholder="sk-..." class="w-full bg-white/5 border border-white/10 rounded p-3 text-xs text-white focus:border-violet-500 focus:outline-none transition font-mono">
                </div>
                <div>
                    <label class="block text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-2">Model Selection</label>
                    <div class="relative">
                        <select id="modelSelect" class="w-full bg-white/5 border border-white/10 rounded p-3 text-xs text-white focus:border-violet-500 focus:outline-none appearance-none cursor-pointer">
                            <option value="gpt-5">GPT-5 (Frontier)</option>
                            <option value="gpt-5-preview">GPT-5 Preview</option>
                            <option value="gpt-4o" selected>GPT-4o (Stable)</option>
                            <option value="gpt-4-turbo">GPT-4 Turbo</option>
                        </select>
                        <i class="fa-solid fa-chevron-down absolute right-3 top-3.5 text-xs text-gray-500 pointer-events-none"></i>
                    </div>
                </div>
                
                <div class="p-4 rounded border border-violet-500/20 bg-violet-500/5 mt-4">
                    <h3 class="text-xs font-bold text-violet-300 mb-1"><i class="fa-solid fa-palette"></i> Design Engine: Pure CSS</h3>
                    <p class="text-[10px] text-gray-400 leading-relaxed">
                        Generating high-fidelity glassmorphism, keyframe animations, and responsive layouts without external CDNs.
                    </p>
                </div>
            </div>
            
            <div class="mt-auto p-6 border-t border-white/5">
                <div id="statusText" class="text-xs font-mono text-gray-500 truncate">System Idle.</div>
            </div>
        </aside>

        <section class="flex-1 flex flex-col relative bg-transparent">
            <div id="chatHistory" class="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth pb-32">
                <div class="flex justify-start animate-fade-in-up">
                    <div class="msg-ai p-5 max-w-xl shadow-2xl">
                        <div class="flex items-center gap-2 mb-2 text-violet-400 text-xs font-bold uppercase">
                            <i class="fa-solid fa-robot"></i> System Architect
                        </div>
                        <p class="text-sm text-gray-300 leading-relaxed">
                            Welcome. I am the <strong>ChromeForge Architect</strong>.
                            <br><br>
                            I build extensions using <strong>Pure CSS3 & Vanilla JS</strong> to ensure maximum performance and strict Content Security Policy (CSP) compliance.
                            <br><br>
                            Select <strong>GPT-5</strong> from the sidebar for the most advanced UI reasoning capabilities.
                        </p>
                    </div>
                </div>
            </div>

            <div class="absolute bottom-6 left-0 right-0 px-6 flex justify-center">
                <div class="w-full max-w-3xl glass-panel rounded-2xl p-2 flex items-end gap-2 neon-border transition-all focus-within:shadow-[0_0_30px_rgba(139,92,246,0.3)]">
                    <textarea id="promptInput" rows="1" 
                        class="w-full bg-transparent border-none text-white placeholder-gray-500 text-sm focus:ring-0 p-3 resize-none max-h-32"
                        placeholder="Describe your extension..."></textarea>
                    
                    <button onclick="sendMessage()" id="sendBtn" class="mb-1 mr-1 bg-violet-600 hover:bg-violet-500 text-white p-2.5 rounded-xl transition-all shadow-lg shadow-violet-500/20 flex items-center justify-center">
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

        promptInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });

        promptInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
        });

        function appendMessage(role, text) {
            const div = document.createElement('div');
            div.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`;
            div.innerHTML = `
                <div class="${role === 'user' ? 'msg-user' : 'msg-ai'} p-5 max-w-xl shadow-lg">
                    <div class="text-[10px] font-bold uppercase mb-1 ${role === 'user' ? 'text-indigo-300 text-right' : 'text-violet-400'}">
                        ${role === 'user' ? 'You' : 'Architect'}
                    </div>
                    <div class="prose prose-invert prose-sm leading-relaxed whitespace-pre-wrap font-sans text-gray-200">${text}</div>
                </div>
            `;
            chatContainer.appendChild(div);
            chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: 'smooth' });
        }

        async function sendMessage() {
            const apiKey = document.getElementById('apiKey').value;
            const prompt = promptInput.value.trim();
            const model = document.getElementById('modelSelect').value;
            const btn = document.getElementById('sendBtn');
            
            if (!apiKey) { alert("Please enter API Key."); return; }
            if (!prompt) return;

            appendMessage('user', prompt);
            promptInput.value = '';
            btn.disabled = true;
            btn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i>`;
            document.getElementById('statusText').innerText = `Forging with ${model}...`;

            conversationHistory.push({ role: "user", content: prompt });

            // ======================================================
            // SYSTEM PROMPT: PURE CSS + MODERN UI
            // ======================================================
            const systemPrompt = `
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
            `;

            try {
                // 1. Try with selected model (e.g., gpt-5)
                let usedModel = model;
                let data;
                
                try {
                    const response = await fetch("https://api.openai.com/v1/chat/completions", {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${apiKey}` },
                        body: JSON.stringify({
                            model: model,
                            messages: [{ role: "system", content: systemPrompt }, ...conversationHistory],
                            response_format: { type: "json_object" }
                        })
                    });

                    if (!response.ok) {
                        const err = await response.json();
                        throw new Error(err.error?.message || "API Error");
                    }
                    data = await response.json();
                    
                } catch (apiError) {
                    // FALLBACK LOGIC: If GPT-5 fails (404), switch to GPT-4o automatically
                    if (model.includes("gpt-5")) {
                        console.warn("GPT-5 unavailable, falling back to GPT-4o");
                        document.getElementById('statusText').innerText = "Rerouting to GPT-4o Backbone...";
                        
                        const fallbackResponse = await fetch("https://api.openai.com/v1/chat/completions", {
                            method: "POST",
                            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${apiKey}` },
                            body: JSON.stringify({
                                model: "gpt-4o",
                                messages: [{ role: "system", content: systemPrompt }, ...conversationHistory],
                                response_format: { type: "json_object" }
                            })
                        });
                        if (!fallbackResponse.ok) throw new Error("Fallback Failed.");
                        data = await fallbackResponse.json();
                        usedModel = "gpt-4o (Fallback)";
                    } else {
                        throw apiError;
                    }
                }
                
                const aiResult = JSON.parse(data.choices[0].message.content);
                conversationHistory.push({ role: "assistant", content: data.choices[0].message.content });

                // Save Files
                const saveRes = await fetch("/save", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(aiResult)
                });
                const saveResult = await saveRes.json();

                if (saveResult.status === "success") {
                    appendMessage('assistant', `✅ **Forged Successfully** using ${usedModel}\n${aiResult.analysis}\n\n📂 Saved to: \`${saveResult.path}\``);
                    document.getElementById('statusText').innerText = "Ready.";
                } else {
                    throw new Error(saveResult.message);
                }

            } catch (error) {
                appendMessage('assistant', `❌ Error: ${error.message}`);
                document.getElementById('statusText').innerText = "Error.";
            } finally {
                btn.disabled = false;
                btn.innerHTML = `<i class="fa-solid fa-bolt"></i>`;
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