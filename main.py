import os
import json
import sys
import uuid
from flask import Flask, render_template_string, request, jsonify

# ==========================================
# CONFIGURATION
# ==========================================
OUTPUT_DIR = "generated_extension"
app = Flask(__name__)

# ==========================================
# 1. THE "MIND-BLOWING" UI (HTML/JS)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChromeForge AI v3 | Context-Aware Architect</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
        body { font-family: 'Inter', sans-serif; background-color: #0b0f19; color: #e2e8f0; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .glass { background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .gradient-text { background: linear-gradient(135deg, #60a5fa 0%, #a855f7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        
        /* Chat Bubble Styles */
        .msg-user { background: #1e293b; border: 1px solid #334155; border-radius: 12px 12px 0 12px; }
        .msg-ai { background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); border: 1px solid #1d4ed8; border-radius: 12px 12px 12px 0; }
        
        .loader { border-top-color: #a855f7; -webkit-animation: spinner 1s linear infinite; animation: spinner 1s linear infinite; }
        @keyframes spinner { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body class="h-screen flex flex-col relative overflow-hidden">

    <header class="h-16 border-b border-slate-800 flex items-center justify-between px-6 glass z-20">
        <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <i class="fa-solid fa-cube text-white text-sm"></i>
            </div>
            <h1 class="text-xl font-bold tracking-tight">Chrome<span class="gradient-text">Forge</span> <span class="text-xs text-slate-500 font-mono ml-2 border border-slate-700 px-1 rounded">v3.0</span></h1>
        </div>
        <div class="flex gap-4 text-xs font-mono text-slate-400">
            <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                <span>System Online</span>
            </div>
        </div>
    </header>

    <main class="flex-1 flex overflow-hidden">
        
        <aside class="w-80 border-r border-slate-800 bg-slate-900/50 p-6 flex flex-col gap-6 z-10 hidden md:flex">
            <div>
                <label class="block text-xs font-bold text-slate-500 uppercase mb-2">OpenAI API Key</label>
                <input type="password" id="apiKey" placeholder="sk-..." class="w-full bg-slate-800 border border-slate-700 rounded p-2.5 text-sm focus:border-purple-500 focus:outline-none transition text-white font-mono">
            </div>
            <div>
                <label class="block text-xs font-bold text-slate-500 uppercase mb-2">Model</label>
                <select id="modelSelect" class="w-full bg-slate-800 border border-slate-700 rounded p-2.5 text-sm text-slate-300 focus:border-purple-500 focus:outline-none">
                    <option value="gpt-4o">GPT-4o (Recommended)</option>
                    <option value="gpt-4-turbo">GPT-4 Turbo</option>
                </select>
            </div>
            
            <div class="mt-auto">
                <div class="p-4 rounded bg-slate-800/50 border border-slate-700">
                    <h3 class="text-xs font-bold text-slate-400 mb-2">Current Status</h3>
                    <div id="statusText" class="text-sm text-green-400 font-mono">Ready to Forge.</div>
                    <div id="pathDisplay" class="text-xs text-slate-500 mt-2 break-all font-mono hidden"></div>
                </div>
            </div>
        </aside>

        <section class="flex-1 flex flex-col relative bg-[#0b0f19]">
            
            <div id="chatHistory" class="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth">
                <div class="flex justify-start">
                    <div class="msg-ai p-4 max-w-2xl shadow-lg">
                        <div class="flex items-center gap-2 mb-1 text-blue-200 text-xs font-bold uppercase tracking-wider">
                            <i class="fa-solid fa-robot"></i> Architect AI
                        </div>
                        <p class="text-sm leading-relaxed text-blue-50">
                            Hello! I am your Chrome Extension Architect. I can build full Manifest V3 extensions with modern UIs.
                            <br><br>
                            Try: <em>"Create a Pomodoro timer with a dark mode UI."</em>
                        </p>
                    </div>
                </div>
            </div>

            <div class="p-4 border-t border-slate-800 glass">
                <div class="max-w-4xl mx-auto relative">
                    <textarea id="promptInput" rows="1" 
                        class="w-full bg-slate-800/80 border border-slate-600 rounded-xl py-3 pl-4 pr-32 text-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500 focus:outline-none transition resize-none text-white shadow-xl"
                        placeholder="Describe your extension or ask for changes..."></textarea>
                    
                    <button onclick="sendMessage()" id="sendBtn" class="absolute right-2 top-1.5 bottom-1.5 bg-purple-600 hover:bg-purple-500 text-white px-4 rounded-lg font-medium text-xs transition flex items-center gap-2">
                        <span>Forge</span> <i class="fa-solid fa-bolt"></i>
                    </button>
                </div>
                <div class="text-center mt-2">
                     <span class="text-[10px] text-slate-600">AI output is generated locally in the <code>/generated_extension</code> folder.</span>
                </div>
            </div>

        </section>
    </main>

    <script>
        // Store conversation history
        let conversationHistory = [];

        const chatContainer = document.getElementById('chatHistory');
        const promptInput = document.getElementById('promptInput');

        // Auto-resize textarea
        promptInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
            if(this.value === '') this.style.height = 'auto';
        });

        function appendMessage(role, text) {
            const div = document.createElement('div');
            div.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in-up`;
            
            const isUser = role === 'user';
            
            div.innerHTML = `
                <div class="${isUser ? 'msg-user bg-slate-700' : 'msg-ai'} p-4 max-w-2xl shadow-lg">
                    <div class="flex items-center gap-2 mb-1 ${isUser ? 'text-slate-400 justify-end' : 'text-blue-200'} text-xs font-bold uppercase tracking-wider">
                        ${isUser ? 'You <i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i> Architect AI'}
                    </div>
                    <div class="text-sm leading-relaxed ${isUser ? 'text-slate-200' : 'text-blue-50'} whitespace-pre-wrap">${text}</div>
                </div>
            `;
            chatContainer.appendChild(div);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        async function sendMessage() {
            const apiKey = document.getElementById('apiKey').value;
            const prompt = promptInput.value.trim();
            const model = document.getElementById('modelSelect').value;
            const btn = document.getElementById('sendBtn');
            
            if (!apiKey) {
                alert("Please enter your OpenAI API Key in the sidebar.");
                return;
            }
            if (!prompt) return;

            // 1. Update UI
            appendMessage('user', prompt);
            promptInput.value = '';
            promptInput.style.height = 'auto';
            btn.disabled = true;
            btn.innerHTML = `<div class="loader ease-linear rounded-full border-2 border-t-2 border-white h-3 w-3"></div>`;
            document.getElementById('statusText').innerText = "Architecting solution...";

            // 2. Add to History
            conversationHistory.push({ role: "user", content: prompt });

            // 3. Prepare System Prompt (The "Brain")
            // We inject instructions for UI DESIGN here.
            const systemPrompt = `
                You are ChromeForge, an elite Senior Full-Stack Engineer and UI/UX Designer. 
                
                YOUR GOAL:
                Create fully functional Chrome Extensions (Manifest V3) based on the user's request.
                
                STRICT OUTPUT FORMAT:
                Return ONLY a JSON object. No markdown. No code blocks.
                {
                    "analysis": "Brief technical explanation of what you changed/created.",
                    "manifest": { ...valid V3 manifest... },
                    "files": {
                        "popup.html": "...",
                        "popup.js": "...",
                        "content.js": "...",
                        "background.js": "...",
                        "styles.css": "...",
                        "icon.svg": "..."
                    },
                    "readme": "Instructions"
                }

                CRITICAL DESIGN RULES (MIND-BLOWING UI):
                1. NEVER use default browser HTML styles.
                2. For 'popup.html', you MUST use a modern Dark Mode design.
                3. Use this CSS template for popup.html styling (inject it or put in styles.css):
                   - Font: Inter or system-ui.
                   - Background: #0f172a (Slate 900).
                   - Text: #e2e8f0 (Slate 200).
                   - Buttons: Gradient backgrounds (blue-600 to purple-600), rounded-lg, hover effects.
                   - Padding: Spacious (p-4).
                   - Shadows: soft box-shadows.
                4. If the user asks for a change (e.g., "Make the button red"), ONLY update the relevant files in the JSON but return the FULL extension structure so we can overwrite the folder.
                5. Ensure 'manifest.json' permissions match the JS logic exactly.
            `;

            // 4. Call OpenAI
            try {
                const messages = [
                    { role: "system", content: systemPrompt },
                    ...conversationHistory // Send full history for context!
                ];

                const response = await fetch("https://api.openai.com/v1/chat/completions", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${apiKey}`
                    },
                    body: JSON.stringify({
                        model: model,
                        messages: messages,
                        response_format: { type: "json_object" }
                    })
                });

                if (!response.ok) throw new Error("OpenAI API Error");
                
                const data = await response.json();
                const aiContent = data.choices[0].message.content;
                const aiResult = JSON.parse(aiContent);

                // 5. Add AI response to history
                conversationHistory.push({ role: "assistant", content: aiContent });

                // 6. Send to Python Backend to Write Files
                const saveResponse = await fetch("/save", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(aiResult)
                });
                
                const saveResult = await saveResponse.json();

                // 7. Success Message
                appendMessage('assistant', `✅ **Success!**\n${aiResult.analysis}\n\n📂 **Folder Updated:** ${saveResult.path}`);
                document.getElementById('statusText').innerText = "Extension ready to load.";
                document.getElementById('statusText').className = "text-sm text-green-400 font-mono";
                document.getElementById('pathDisplay').innerText = saveResult.path;
                document.getElementById('pathDisplay').classList.remove('hidden');

            } catch (error) {
                appendMessage('assistant', `❌ **Error:** ${error.message}`);
                document.getElementById('statusText').innerText = "Generation Failed.";
                document.getElementById('statusText').className = "text-sm text-red-500 font-mono";
            } finally {
                btn.disabled = false;
                btn.innerHTML = `<span>Forge</span> <i class="fa-solid fa-bolt"></i>`;
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
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/save', methods=['POST'])
def save_files():
    try:
        data = request.json
        
        # 1. Clean & Create Directory
        if os.path.exists(OUTPUT_DIR):
            import shutil
            shutil.rmtree(OUTPUT_DIR)
        os.makedirs(OUTPUT_DIR)

        # 2. Write Manifest
        manifest = data.get('manifest', {})
        # Ensure icons path
        if 'icons' not in manifest:
            manifest['icons'] = {"16": "icon.png", "48": "icon.png", "128": "icon.png"}
            
        with open(os.path.join(OUTPUT_DIR, "manifest.json"), "w") as f:
            json.dump(manifest, f, indent=2)

        # 3. Write Files
        files = data.get('files', {})
        for filename, content in files.items():
            path = os.path.join(OUTPUT_DIR, filename)
            
            # Special SVG Handling (Convert to dummy PNG for Chrome compatibility)
            if filename.endswith(".svg"):
                with open(path, "w") as f:
                    f.write(content)
                # Create dummy PNG if icon.png doesn't exist in files
                if "icon.png" not in files:
                    with open(os.path.join(OUTPUT_DIR, "icon.png"), "wb") as f:
                         # 1x1 Pixel Transparent PNG
                         f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)

        # 4. Write README
        if 'readme' in data:
            with open(os.path.join(OUTPUT_DIR, "README.md"), "w") as f:
                f.write(data['readme'])

        return jsonify({"status": "success", "path": os.path.abspath(OUTPUT_DIR), "folder": OUTPUT_DIR})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("---------------------------------------------------------")
    print("  CHROMEFORGE v3.0 (AI ARCHITECT) - ONLINE")
    print("  1. Open: http://127.0.0.1:5000")
    print("  2. Enter OpenAI Key in Sidebar.")
    print("  3. Chat with your architect!")
    print("---------------------------------------------------------")
    app.run(debug=True, port=5000)