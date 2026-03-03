import os
import qt
import slicer
from slicer.ScriptedLoadableModule import *
import urllib.request
import urllib.error
import urllib.parse
import json
import base64
import traceback
import sys
import ctk

# ==============================================================================
# SlicerClaw
#
class SlicerClaw(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "SlicerClaw"
        self.parent.categories = ["AI & Machine Learning"]
        self.parent.dependencies = []
        self.parent.contributors = ["Slicer Community"]
        self.parent.helpText = """
This module provides a native LLM Agent directly integrated into 3D Slicer.
Once configured with an API Key and Base URL, you can press Ctrl+I (or Cmd+I) from 
anywhere in Slicer to bring up the Spotlight Chat and instruct the AI.
"""
        self.parent.acknowledgementText = "Built with passion."
        
        # 延迟初始化全局快捷键，使 Slicer 启动后即可按 Cmd+I 唤醒
        if not slicer.app.commandOptions().noMainWindow:
            self._initRetryCount = 0
            qt.QTimer.singleShot(2000, self.initializeGlobalShortcut)

    def initializeGlobalShortcut(self):
        # 确保 mainWindow 已创建，否则重试
        if slicer.util.mainWindow() is None:
            self._initRetryCount = getattr(self, '_initRetryCount', 0) + 1
            if self._initRetryCount < 30:
                qt.QTimer.singleShot(1000, self.initializeGlobalShortcut)
            else:
                print("[SlicerClaw] Warning: mainWindow not available after 30 retries, giving up.")
            return
        if not hasattr(slicer, "slicerclaw_logic"):
            slicer.slicerclaw_logic = SlicerClawLogic()
        slicer.slicerclaw_logic.ensureUiHook()

# ==============================================================================
# SlicerClawWidget (The Settings UI)
# ==============================================================================
class SlicerClawWidget(ScriptedLoadableModuleWidget):
    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        if hasattr(slicer, "slicerclaw_logic"):
            self.logic = slicer.slicerclaw_logic
        else:
            self.logic = SlicerClawLogic()
            slicer.slicerclaw_logic = self.logic

        # --- Section A: Spotlight AI Settings ---
        settingsCollapsibleButton = ctk.ctkCollapsibleButton()
        settingsCollapsibleButton.text = "1. AI API Settings (Spotlight)"
        self.layout.addWidget(settingsCollapsibleButton)
        settingsFormLayout = qt.QFormLayout(settingsCollapsibleButton)
        
        self.apiUrlEdit = qt.QLineEdit()
        self.apiUrlEdit.setToolTip("e.g., https://coding.dashscope.aliyuncs.com/v1/chat/completions")
        settingsFormLayout.addRow("API Base URL:", self.apiUrlEdit)
        
        self.apiKeyEdit = qt.QLineEdit()
        self.apiKeyEdit.setEchoMode(qt.QLineEdit.Password)
        settingsFormLayout.addRow("API Key:", self.apiKeyEdit)
        
        self.modelEdit = qt.QLineEdit()
        self.modelEdit.setToolTip("e.g., glm-5 or glm-4-plus")
        settingsFormLayout.addRow("Model Name:", self.modelEdit)

        self.languageCombo = qt.QComboBox()
        self.languageCombo.addItems(["中文 (Chinese)", "English"])
        self.languageCombo.setToolTip("Select the language for AI responses and the Spotlight UI.")
        settingsFormLayout.addRow("Language:", self.languageCombo)

        self.drVerboserCheck = qt.QCheckBox("🩺 Dr. Verboser Mode")
        self.drVerboserCheck.setToolTip("Enable detailed chain-of-thought analysis and reliability checks before AI takes action.")
        settingsFormLayout.addRow("", self.drVerboserCheck)

        self.saveButton = qt.QPushButton("Save Settings & Apply")
        settingsFormLayout.addRow("", self.saveButton)
        self.saveButton.connect('clicked(bool)', self.onSaveSettings)

        # --- Section B: External AI Connection (MCP) ---
        mcpCollapsibleButton = ctk.ctkCollapsibleButton()
        mcpCollapsibleButton.text = "2. External AI Connection (Cursor/Claude)"
        mcpCollapsibleButton.collapsed = True
        self.layout.addWidget(mcpCollapsibleButton)
        mcpLayout = qt.QVBoxLayout(mcpCollapsibleButton)
        
        mcpInfo = qt.QLabel("The built-in MCP Server is running silently at <b>http://127.0.0.1:2016/mcp</b>.<br><br>"
                            "There's no need to configure paths manually. Just copy the AI Setup Prompt below, paste it into Cursor or Claude, and let the AI assistant configure itself!")
        mcpInfo.setWordWrap(True)
        mcpLayout.addWidget(mcpInfo)
        
        self.btnCopyPrompt = qt.QPushButton("📋 Copy One-Click Setup Prompt")
        font = qt.QFont()
        font.setBold(True)
        self.btnCopyPrompt.setFont(font)
        self.btnCopyPrompt.setStyleSheet("QPushButton { background-color: #2196F3; color: white; border-radius: 4px; padding: 6px; } QPushButton:hover { background-color: #1976D2; }")
        self.btnCopyPrompt.connect('clicked(bool)', self.onCopySetupPrompt)
        mcpLayout.addWidget(self.btnCopyPrompt)

        # --- Section C: AI Knowledge Base ---
        kbCollapsibleButton = ctk.ctkCollapsibleButton()
        kbCollapsibleButton.text = "3. AI Knowledge Base (Skills & Data)"
        kbCollapsibleButton.collapsed = True
        self.layout.addWidget(kbCollapsibleButton)
        kbLayout = qt.QVBoxLayout(kbCollapsibleButton)
        
        kbInfo = qt.QLabel("Install the core AI skill for cloud search, or download massive "
                           "local databases (Source, Discourse) for offline AI context.")
        kbInfo.setWordWrap(True)
        kbLayout.addWidget(kbInfo)
        
        self.kbCombo = qt.QComboBox()
        self.kbCombo.addItem("🌟 Default Core Skill: jumbojing/slicerSkill", "skill|https://github.com/jumbojing/slicerSkill")
        self.kbCombo.addItem("2. Local Data: Slicer Source Code", "data|https://github.com/Slicer/Slicer|slicer-source")
        self.kbCombo.addItem("3. Local Data: Slicer Extensions Index", "data|https://github.com/Slicer/ExtensionsIndex|slicer-extensions")
        self.kbCombo.addItem("4. Local Data: Slicer Discourse Archive", "data|https://github.com/pieper/slicer-discourse-archive|slicer-discourse")
        kbLayout.addWidget(self.kbCombo)
        
        self.btnDownloadKb = qt.QPushButton("Download & Extract")
        self.btnDownloadKb.connect('clicked(bool)', self.onDownloadKb)
        kbLayout.addWidget(self.btnDownloadKb)

        # --- Section D: Evolution Memory ---
        memCollapsibleButton = ctk.ctkCollapsibleButton()
        memCollapsibleButton.text = "4. AI Evolution Memory (Long-term)"
        memCollapsibleButton.collapsed = True
        self.layout.addWidget(memCollapsibleButton)
        memLayout = qt.QVBoxLayout(memCollapsibleButton)
        
        memInfo = qt.QLabel("SlicerClaw and external AIs can 'remember' your corrections, project context, and custom API usage patterns across sessions.")
        memInfo.setWordWrap(True)
        memLayout.addWidget(memInfo)
        
        self.chkGlobalMemory = qt.QCheckBox("Enable Global Memory (cross-project)")
        self.chkGlobalMemory.toolTip = "Allow AI to read/write global lessons shared across all projects."
        memLayout.addWidget(self.chkGlobalMemory)
        
        memBtnLayoutGlobal = qt.QHBoxLayout()
        self.btnViewMemory = qt.QPushButton("👁️ View Global Memory")
        self.btnViewMemory.connect('clicked(bool)', self.onViewMemory)
        memBtnLayoutGlobal.addWidget(self.btnViewMemory)
        
        self.btnClearMemory = qt.QPushButton("🧹 Clear Global Memory")
        self.btnClearMemory.connect('clicked(bool)', self.onClearMemory)
        memBtnLayoutGlobal.addWidget(self.btnClearMemory)
        memLayout.addLayout(memBtnLayoutGlobal)
        
        memBtnLayoutProject = qt.QHBoxLayout()
        self.btnViewProjectMemory = qt.QPushButton("👁️ View Project Memory")
        self.btnViewProjectMemory.connect('clicked(bool)', self.onViewProjectMemory)
        memBtnLayoutProject.addWidget(self.btnViewProjectMemory)
        
        self.btnClearProjectMemory = qt.QPushButton("🧹 Clear Project Memory")
        self.btnClearProjectMemory.connect('clicked(bool)', self.onClearProjectMemory)
        memBtnLayoutProject.addWidget(self.btnClearProjectMemory)
        memLayout.addLayout(memBtnLayoutProject)
        
        # --- Section E: Developer Workspace ---
        workspaceCollapsibleButton = ctk.ctkCollapsibleButton()
        workspaceCollapsibleButton.text = "5. Active Dev Workspace (Project Sync)"
        workspaceCollapsibleButton.collapsed = True
        self.layout.addWidget(workspaceCollapsibleButton)
        workspaceLayout = qt.QVBoxLayout(workspaceCollapsibleButton)
        
        wsInfo = qt.QLabel("Set this to your project repository root. Project-Specific Memory will sync here to share AI lessons with your team via git.")
        wsInfo.setWordWrap(True)
        workspaceLayout.addWidget(wsInfo)
        
        wsLayout = qt.QHBoxLayout()
        self.workspaceEdit = qt.QLineEdit()
        self.workspaceEdit.setPlaceholderText("e.g., /Users/name/projects/myExtension")
        wsLayout.addWidget(self.workspaceEdit)
        
        self.btnBrowseWorkspace = qt.QPushButton("Browse...")
        self.btnBrowseWorkspace.connect('clicked(bool)', self.onBrowseWorkspace)
        wsLayout.addWidget(self.btnBrowseWorkspace)
        workspaceLayout.addLayout(wsLayout)

        self.layout.addStretch(1)

        self.loadSettings()
        self.logic.ensureUiHook()

    def onBrowseWorkspace(self):
        dir_path = qt.QFileDialog.getExistingDirectory(slicer.util.mainWindow(), "Select Active Project Workspace")
        if dir_path:
            self.workspaceEdit.text = dir_path
            self.onSaveSettings()

    def loadSettings(self):
        settings = slicer.app.settings()
        self.apiUrlEdit.text = settings.value("SlicerClaw/ApiUrl", "https://coding.dashscope.aliyuncs.com/v1/chat/completions")
        self.apiKeyEdit.text = settings.value("SlicerClaw/ApiKey", "")
        self.modelEdit.text = settings.value("SlicerClaw/ModelName", "glm-5")
        
        saved_lang = settings.value("SlicerClaw/Language", "中文 (Chinese)")
        index = self.languageCombo.findText(saved_lang)
        if index >= 0:
            self.languageCombo.currentIndex = index
            
        self.chkGlobalMemory.checked = (settings.value("SlicerClaw/EnableGlobalMemory", "true").lower() == "true")
        self.workspaceEdit.text = settings.value("SlicerClaw/ActiveWorkspace", "")

    def onSaveSettings(self):
        settings = slicer.app.settings()
        settings.setValue("SlicerClaw/ApiUrl", self.apiUrlEdit.text.strip())
        settings.setValue("SlicerClaw/ApiKey", self.apiKeyEdit.text.strip())
        settings.setValue("SlicerClaw/ModelName", self.modelEdit.text.strip())
        settings.setValue("SlicerClaw/Language", self.languageCombo.currentText)
        settings.setValue("SlicerClaw/DrVerboser", "true" if self.drVerboserCheck.checked else "false")
        settings.setValue("SlicerClaw/EnableGlobalMemory", "true" if self.chkGlobalMemory.checked else "false")
        settings.setValue("SlicerClaw/ActiveWorkspace", self.workspaceEdit.text.strip())
        slicer.util.messageBox("Settings saved successfully!")
        self.logic.loadSettings()

    def onCopySetupPrompt(self):
        bridge_code = '''import sys\nimport json\nimport urllib.request\nimport urllib.error\n\nSLICER_MCP_URL = "http://127.0.0.1:2016/mcp"\n\ndef main():\n    while True:\n        try:\n            line = sys.stdin.readline()\n            if not line: break\n            line = line.strip()\n            if not line: continue\n            req = urllib.request.Request(SLICER_MCP_URL, data=line.encode('utf-8'))\n            req.add_header('Content-Type', 'application/json')\n            try:\n                response = urllib.request.urlopen(req, timeout=120)\n                sys.stdout.write(response.read().decode('utf-8') + "\\n")\n                sys.stdout.flush()\n            except urllib.error.URLError as e:\n                try:\n                    msg = json.loads(line)\n                    if msg.get("id") is not None:\n                        err = {"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32000, "message": str(e)}}\n                        sys.stdout.write(json.dumps(err) + "\\n")\n                        sys.stdout.flush()\n                except: pass\n        except KeyboardInterrupt: break\n        except Exception as e: sys.stderr.write(f"Bridge error: {e}\\n")\n\nif __name__ == '__main__':\n    main()'''
        
        resources_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Resources")
        prompt = f"""Hello AI, I want you to connect yourself to my 3D Slicer embedded Model Context Protocol (MCP) server. It is waiting for connections at http://127.0.0.1:2016/mcp.

Please configure yourself exactly as follows automatically:
1. Create a python script at: `{resources_path}/slicer_mcp_bridge.py`
2. Insert the following code into it exactly as provided:
```python
{bridge_code}
```
3. Detect your own identity/environment and configure the MCP connection named "slicer-agent" using your specific standard:
   - type: "command"
   - command: "{sys.executable}"
   - args: ["{resources_path}/slicer_mcp_bridge.py"]
   
   * Detection guide for you:
   - If you are Cursor: update `.cursor/mcp.json`
   - If you are Windsurf: update `.codeium/windsurf/mcp.json`
   - If you are OpenCode: update `.opencode/mcp.json`
   - If you are Claude Desktop/Claude Code: update your global/project config (e.g. `claude_desktop_config.json` or by using the `mcp add` command via CLI)

4. Once configured successfully, verify your active MCP connection by calling my `execute_python` tool. Explicitly manipulate my Slicer environment to show an alert or print a message.
   - For example: `print("Slicer你好, 我是伴随着 🦞 来的外部 AI助手...")`
   
5. I have also prepared a local Knowledge Base (Slicer Skills). Whenever you are asked to write Slicer-specific Python code but are unsure about the exact API, **ALWAYS use the `search_slicer_knowledge` MCP tool** first to find verified code snippets!
"""
        memory_scopes = "global and project scopes" if self.chkGlobalMemory.checked else "project scope only"
        prompt += f"""
6. You have access to an 'Evolution Memory' system ({memory_scopes}) via `read_long_term_memory` and `append_long_term_memory`. When tackling complex tasks, you should first read the memory to check for past lessons. If you learn something new or correct a mistake, you MUST append it to the memory so you won't forget it in future sessions!
"""
        if self.drVerboserCheck.checked:
            prompt += """
7. You are currently in 'Dr. Verboser' mode. Before giving your final answer or executing any Slicer python functions, you MUST output a section titled '🩺 Dr. Verboser Analysis:'.
In this section, explicitly state: 1) Your detailed reasoning process. 2) The exact Slicer APIs or knowledge base items you are relying on. 3) Any potential risks or side effects of your code. Only after thinking out loud should you proceed with the actual response or tool call.
"""
            
        prompt += "\\nPlease complete this silently, and let me know when you are fully ready to manipulate my 3D Slicer scene!"

        try:
            qt.QApplication.clipboard().setText(prompt)
            slicer.util.messageBox("✅ Setup Prompt Copied to Clipboard!\\n\\nNow simply go to Cursor, Claude, or your favorite external AI assistant and paste (Ctrl+V) this prompt!\\n\\nThe AI will automatically create the scripts and configure itself.")
        except Exception as e:
            slicer.util.errorDisplay(f"Failed to copy prompt: {e}")

    def onDownloadKb(self):
        item_data = self.kbCombo.currentData.split("|")
        item_type = item_data[0]
        repo_base = item_data[1]
        
        repo_url = repo_base.replace("github.com", "api.github.com/repos") + "/zipball/main"
        # Fallback to master if main fails
        repo_url_master = repo_base.replace("github.com", "api.github.com/repos") + "/zipball/master"
        
        target_dir = qt.QFileDialog.getExistingDirectory(slicer.util.mainWindow(), "Select the SKILL folder (e.g. .opencode/skills) to install to")
        if not target_dir:
            return
            
        slicer.util.delayDisplay(f"Downloading {repo_base}... this may take a while depending on the size.", autoClose=3000)
        slicer.app.processEvents()
        
        try:
            import zipfile, io
            req = urllib.request.Request(repo_url, headers={'User-Agent': 'SlicerClaw'})
            try:
                response = urllib.request.urlopen(req)
            except urllib.error.HTTPError as e:
                # If 404 on main, try master
                if e.code == 404:
                    req = urllib.request.Request(repo_url_master, headers={'User-Agent': 'SlicerClaw'})
                    response = urllib.request.urlopen(req)
                else:
                    raise e
                    
            zip_data = response.read()
            
            with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
                root_dir = z.namelist()[0].split('/')[0]
                
                if item_type == "skill":
                    installed_dir = os.path.join(target_dir, "slicer-skill")
                else:
                    sub_folder = item_data[2]
                    installed_dir = os.path.join(target_dir, "slicer-skill", sub_folder)
                    
                for file_info in z.infolist():
                    if file_info.is_dir(): continue
                    rel_path = file_info.filename[len(root_dir)+1:]
                    if not rel_path: continue
                    target_path = os.path.join(installed_dir, rel_path)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with open(target_path, "wb") as f:
                        f.write(z.read(file_info.filename))
                        
            slicer.util.messageBox(f"Successfully downloaded and extracted to:\\n{installed_dir}")
        except Exception as e:
            slicer.util.errorDisplay(f"Download failed: {e}")

    def onViewMemory(self):
        mem_dir = os.path.expanduser("~/.slicerClaw")
        os.makedirs(mem_dir, exist_ok=True)
        path = os.path.join(mem_dir, "global_memory.md")
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write("# SlicerClaw Global Evolution Memory\\n\\nThis file is managed by your AI assistance. It stores lessons learned and user preferences.\\n")
        qt.QDesktopServices.openUrl(qt.QUrl.fromLocalFile(path))

    def onClearMemory(self):
        if slicer.util.confirmOkCancelDisplay("Are you sure you want to completely erase the AI's Global Evolution Memory? AI will forget all past lessons."):
            path = os.path.join(os.path.expanduser("~/.slicerClaw"), "global_memory.md")
            if os.path.exists(path):
                os.remove(path)
                slicer.util.messageBox("Global memory erased successfully.")
            else:
                slicer.util.messageBox("No global memory found to erase.")
                
    def onViewProjectMemory(self):
        scene_file = slicer.mrmlScene.GetURL()
        if scene_file:
            path = os.path.join(os.path.dirname(scene_file), ".slicer_project_memory.md")
        else:
            path = os.path.join(slicer.app.temporaryPath, ".slicer_project_memory.md")
            
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                f.write("# SlicerClaw Project Evolution Memory\n\nThis file is managed by your AI assistance. It stores lessons and context exclusive to this specific Slicer Scene.\n")
        qt.QDesktopServices.openUrl(qt.QUrl.fromLocalFile(path))

    def onClearProjectMemory(self):
        if slicer.util.confirmOkCancelDisplay("Are you sure you want to completely erase the AI's Project Evolution Memory for the current scene?"):
            scene_file = slicer.mrmlScene.GetURL()
            if scene_file:
                path = os.path.join(os.path.dirname(scene_file), ".slicer_project_memory.md")
            else:
                path = os.path.join(slicer.app.temporaryPath, ".slicer_project_memory.md")
                
            if os.path.exists(path):
                os.remove(path)
                slicer.util.messageBox("Project memory erased successfully.")
            else:
                slicer.util.messageBox("No project memory found to erase.")

# ==============================================================================
# SlicerClawLogic (Agent Core & Spotlight UI)
# ==============================================================================
class SlicerClawLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        self.chatHistory = []
        self.loadSettings()
        
    def loadSettings(self):
        settings = slicer.app.settings()
        self.api_url = settings.value("SlicerClaw/ApiUrl", "https://coding.dashscope.aliyuncs.com/v1/chat/completions")
        self.api_key = settings.value("SlicerClaw/ApiKey", "")
        self.api_model = settings.value("SlicerClaw/ModelName", "glm-5")
        self.api_lang = settings.value("SlicerClaw/Language", "中文 (Chinese)")
        self.dr_verboser = (settings.value("SlicerClaw/DrVerboser", "false").lower() == "true")
        self.enable_global_memory = (settings.value("SlicerClaw/EnableGlobalMemory", "true").lower() == "true")
        
        lang_instruction = "Please communicate in English."
        sys_msg = f"You are a helpful AI assistant operating directly inside 3D Slicer. You can call tools to query the scene and execute python code natively. Be concise, precise, and polite. {lang_instruction}"
        
        # Inject Memory System Instructions
        memory_scopes = "global and project scopes" if self.enable_global_memory else "project scope only"
        sys_msg += (f"\\n\\nYou have access to an 'Evolution Memory' system ({memory_scopes}). "
                    "When tackling hard problems, you can call 'read_long_term_memory' to check for past lessons. "
                    "Critically, if the user corrects your code or you learn a new API, you MUST call 'append_long_term_memory' to permanently save this experience.")
        
        if self.dr_verboser:
            sys_msg += ("\\n\\nYou are currently in 'Dr. Verboser' mode. Before giving your final answer or executing any Slicer python functions, "
                        "you MUST output a section titled '🩺 Dr. Verboser Analysis:'.\\n"
                        "In this section, explicitly state: 1) Your detailed reasoning process. 2) The exact Slicer APIs or knowledge base items you are relying on. "
                        "3) Any potential risks or side effects of your code. Only after thinking out loud should you proceed with the actual response or tool call.")
        
        if not self.chatHistory or self.chatHistory[0]["role"] != "system":
            self.chatHistory.insert(0, {"role": "system", "content": sys_msg})
        else:
            self.chatHistory[0]["content"] = sys_msg
        
        if hasattr(slicer, "ai_spotlight_chat") and slicer.ai_spotlight_chat is not None:
            slicer.ai_spotlight_chat.update_language(self.api_lang)

    def ensureUiHook(self):
        mainWin = slicer.util.mainWindow()
        if mainWin is None:
            print("[SlicerClaw] mainWindow not ready, skipping UI hook.")
            return

        # Destroy existing instance if any (to support reloading)
        if hasattr(slicer, "ai_spotlight_chat") and slicer.ai_spotlight_chat is not None:
            try:
                slicer.ai_spotlight_chat.hide()
                slicer.ai_spotlight_chat.deleteLater()
            except Exception:
                pass
            slicer.ai_spotlight_chat = None

        if not hasattr(slicer, "ai_spotlight_chat") or slicer.ai_spotlight_chat is None:
            slicer.ai_spotlight_chat = SpotlightChat(self)

        toolbar = mainWin.findChild("QToolBar", "AICopilotToolBar")
        if toolbar:
            # Clear old toolbar actions to unbind previous destroyed chat instance
            toolbar.clear()
            mainWin.removeToolBar(toolbar)
            toolbar.deleteLater()
            
        toolbar = mainWin.addToolBar("AI Copilot")
        toolbar.setObjectName("AICopilotToolBar")
        ai_action = toolbar.addAction("🧠 Spotlight Chat (Cmd/Ctrl+I)")
        ai_action.setObjectName("AIChatAction")
        ai_action.connect("triggered()", slicer.ai_spotlight_chat.toggle_visibility)

    def doChatLoop(self, user_msg):
        if not self.api_key:
            print("\n[AI Copilot Error] Please configure the API Key in the SlicerClaw module settings first!")
            return
        
        # Check if the message is a direct Slicer command starting with /slicerClaw
        is_slicer_command = user_msg.strip().startswith("/slicerClaw")
        if is_slicer_command:
            # Strip the prefix for underlying query
            actual_msg = user_msg.strip()[len("/slicerClaw"):].strip()
            if not actual_msg:
                actual_msg = user_msg  # If only prefix, keep original message
            else:
                user_msg = actual_msg  # Update display message
        
        print(f"\n[You]: {user_msg}\n")
        
        if is_slicer_command:
            # Slicer Operation Mode: Add context hint for the API
            slicer_hint = "\n[Mode: Slicer Command - Tools enabled]"
            self.chatHistory.append({"role": "user", "content": user_msg + slicer_hint})
        else:
            # Pure Chat Mode: No extra tool hint
            self.chatHistory.append({"role": "user", "content": user_msg})
        
        for _ in range(5):
            # Include tools only if Slicer Mode is requested
            if is_slicer_command:
                payload = {
                    "model": self.api_model,
                    "messages": self.chatHistory,
                    "tools": OPENAI_TOOLS_SCHEMA,
                    "tool_choice": "auto"
                }
            else:
                # Chat mode restricts to standard dialogue without enabling tools schema
                payload = {
                    "model": self.api_model,
                    "messages": self.chatHistory
                }
            
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(self.api_url, data=data)
            req.add_header('Content-Type', 'application/json')
            req.add_header('Authorization', f'Bearer {self.api_key}')
            
            try:
                print("⏳ Thinking...")
                slicer.app.processEvents()
                response = urllib.request.urlopen(req, timeout=120)
                res_json = json.loads(response.read().decode('utf-8'))
                
                choice = res_json['choices'][0]
                msg = choice['message']
                
                self.chatHistory.append(msg)
                
                if msg.get('content'):
                    print(f"[AI]:\n{msg['content']}\n")
                    
                if 'tool_calls' in msg and msg['tool_calls']:
                    for tc in msg['tool_calls']:
                        f_name = tc['function']['name']
                        f_args = json.loads(tc['function']['arguments'])
                        print(f"🔧 [Tool Call]: {f_name}({f_args})")
                        
                        try:
                            if f_name == "list_nodes":
                                result = tool_list_nodes(f_args.get("className", "vtkMRMLNode"))
                            elif f_name == "get_node_properties":
                                result = tool_get_node_properties(f_args.get("id"))
                            elif f_name == "execute_python":
                                result = tool_execute_python(f_args.get("code"))
                            elif f_name == "screenshot":
                                result = tool_screenshot()
                            elif f_name == "search_slicer_knowledge":
                                result = _mcp_tool_search_slicer_knowledge(f_args)[0]["text"]
                            elif f_name == "read_long_term_memory":
                                result = tool_read_memory(f_args.get("scope", "global"))
                            elif f_name == "append_long_term_memory":
                                result = tool_append_memory(f_args.get("scope", "global"), f_args.get("content"))
                            else:
                                result = f"Unknown tool: {f_name}"
                        except Exception as e:
                            result = f"Tool execution error: {e}"
                            
                        tool_msg = {
                            "role": "tool",
                            "tool_call_id": tc['id'],
                            "name": f_name,
                            "content": str(result)
                        }
                        self.chatHistory.append(tool_msg)
                        print(f"✅ Tool results sent back. Waiting for the thoughts of LLM...\n")
                    continue
                else:
                    hint = "👉 (Press Ctrl+I to continue...)"
                    print(f"\n{hint}\n")
                    break
                    
            except urllib.error.HTTPError as e:
                err_body = ""
                try:
                    err_body = e.read().decode('utf-8')
                except:
                    pass
                print(f"\n❌ [Error] API Request Failed ({e.code}): {e.reason}\nDetails: {err_body}")
                self.chatHistory.pop()
                slicer.util.errorDisplay(f"API Request Failed: {e.code} {e.reason}\n{err_body}")
                break
            except Exception as e:
                print(f"\n❌ [Error] API Request Failed: {e}")
                self.chatHistory.pop()
                slicer.util.errorDisplay(f"API Request Failed:\n{str(e)}")
                break

# ==============================================================================
# Spotlight UI Class
# ==============================================================================
class SpotlightChat(qt.QWidget):
    def __init__(self, logic):
        super().__init__(None) 
        self.logic = logic
        self._first_show = True # Controls one-time welcome message
        self.setWindowFlags(qt.Qt.FramelessWindowHint | qt.Qt.WindowStaysOnTopHint | qt.Qt.Tool)
        self.setAttribute(qt.Qt.WA_TranslucentBackground)
        
        main_layout = qt.QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        self.container = qt.QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 30, 240);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 40);
            }
        """)
        container_layout = qt.QHBoxLayout(self.container)
        container_layout.setContentsMargins(15, 10, 15, 10)
        
        icon_label = qt.QLabel("✨")
        icon_label.setStyleSheet("font-size: 24px; background: transparent; border: none;")
        container_layout.addWidget(icon_label)
        
        self.input_edit = qt.QLineEdit()
        self.input_edit.setStyleSheet("""
            QLineEdit {
                background: transparent;
                color: white;
                font-size: 20px;
                border: none;
                qproperty-cursorPosition: 0;
            }
        """)
        self.input_edit.setMinimumWidth(450)
        self.input_edit.setMinimumHeight(40)
        container_layout.addWidget(self.input_edit)
        
        # Slicer Mode Switch Button
        self.slicer_mode_btn = qt.QPushButton("🦞")
        self.slicer_mode_btn.setCheckable(True)
        self.slicer_mode_btn.setChecked(False)  # Default disabled (pure chat mode)
        self.slicer_mode_btn.setFixedSize(40, 36)
        self.slicer_mode_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                font-size: 22px;
                border: 2px solid rgba(255, 255, 255, 60);
                border-radius: 8px;
                padding: 2px;
                opacity: 0.4;
            }
            QPushButton:hover {
                border: 2px solid rgba(255, 255, 255, 120);
                background: rgba(255, 255, 255, 20);
            }
            QPushButton:checked {
                border: 2px solid rgba(255, 140, 60, 220);
                background: rgba(255, 100, 30, 60);
            }
            QPushButton:checked:hover {
                border: 2px solid rgba(255, 160, 80, 255);
                background: rgba(255, 120, 40, 80);
            }
        """)
        self.slicer_mode_btn.connect("toggled(bool)", self.on_slicer_mode_toggled)
        container_layout.addWidget(self.slicer_mode_btn)
        
        self.update_language(self.logic.api_lang if hasattr(self.logic, 'api_lang') else "中文 (Chinese)")
        
        main_layout.addWidget(self.container)
        self.input_edit.connect("returnPressed()", self.on_enter)

        # Clear existing shortcuts if any
        if hasattr(slicer, "slicerclaw_shortcut") and slicer.slicerclaw_shortcut:
            try:
                slicer.slicerclaw_shortcut.disconnect("activated()")
                slicer.slicerclaw_shortcut.setParent(None)
                slicer.slicerclaw_shortcut.deleteLater()
            except Exception:
                pass
            
        self.shortcut = qt.QShortcut(qt.QKeySequence("Ctrl+I"), slicer.util.mainWindow())
        self.shortcut.setContext(qt.Qt.ApplicationShortcut)  # Important: Prevents Slicer panels from intercepting the trigger
        self.shortcut.connect("activated()", self.toggle_visibility)
        slicer.slicerclaw_shortcut = self.shortcut

        # Global hook to intercept module loads just in case
        self._obs = slicer.mrmlScene.AddObserver(slicer.mrmlScene.StartImportEvent, self._keepAlive)

    def update_language(self, lang):
        # Override with English consistently
        self.input_edit.setPlaceholderText("Chat with AI... | 🦞 Slicer Mode")
        self.slicer_mode_btn.setToolTip(
            "Dim: Chat mode only\n"
            "Lit: Slicer operation mode (tools enabled)"
        )

    def on_slicer_mode_toggled(self, checked):
        if checked and getattr(self, "_first_slicer_mode", True):
            self._first_slicer_mode = False
            msg = "⚠️ 🦞 Slicer Mode Enabled.\nThe AI can now execute Python code modifying your scene! Proceed with caution."
            slicer.util.warningDisplay(msg, windowTitle="SlicerClaw Security")
            print(f"\n{msg}\n")

    def _keepAlive(self, caller, event):
        pass # To satisfy python garbage collection

    def keyPressEvent(self, event):
        if event.key() == qt.Qt.Key_Escape:
            self.hide()
        # Accept all inputs since PythonQt intercepts super.keyPressEvent
        event.accept()

    def toggle_visibility(self):
        try:
            if self.isVisible():
                self.hide()
            else:
                self.show_center()
        except ValueError:
            # Handle "Trying to call 'isVisible' on a destroyed QWidget object"
            # which happens if old shortcuts linger after module reload.
            pass

    def show_center(self):
        self.input_edit.clear()
        main_window = slicer.util.mainWindow()
        if main_window:
            geom = main_window.geometry
            w = 680
            h = 100
            x = geom.x() + (geom.width() - w) // 2
            y = geom.y() + (geom.height() - h) // 3
            self.setGeometry(x, y, w, h)
        self.show()
        self.raise_()
        self.activateWindow() # Crucial: Force activation for frameless windows on macOS
        self.input_edit.setFocus()
        
        # Show welcome message only on first launch
        if getattr(self, "_first_show", False):
            self._first_show = False
            welcome_msg = ("\n👋 Welcome to SlicerClaw!\n"
                           "• Default: Pure text chat mode.\n"
                           "• Click the 🦞 button: Slicer Mode (grants AI power to modify scenes).\n"
                           "• Press Ctrl+I or Cmd+I to summon this window anytime.\n")
            print(welcome_msg)

    def on_enter(self):
        text = self.input_edit.text.strip()
        if not text:
            return
        self.hide()
        # Adjust command format based on Slicer Mode state
        if self.slicer_mode_btn.checked:
            # Slicer Operation Mode: Auto prepend the underlying command prefix
            if not text.startswith("/slicerClaw"):
                text = "/slicerClaw " + text
        qt.QTimer.singleShot(50, lambda: self.logic.doChatLoop(text))


# ==============================================================================
# ==============================================================================
# Helper Tools Methods (Nodes & Python Execution)
# ==============================================================================
def tool_list_nodes(className="vtkMRMLNode"):
    nodes = slicer.util.getNodesByClass(className)
    result = [{"name": n.GetName(), "id": n.GetID(), "class": n.GetClassName()} for n in nodes]
    return json.dumps(result, indent=2)

def _get_global_memory_path():
    mem_dir = os.path.expanduser("~/.slicerClaw")
    os.makedirs(mem_dir, exist_ok=True)
    return os.path.join(mem_dir, "global_memory.md")

def _get_project_memory_path():
    ws_path = slicer.app.settings().value("SlicerClaw/ActiveWorkspace", "").strip()
    if ws_path and os.path.exists(ws_path):
        return os.path.join(ws_path, ".slicer_project_memory.md")
        
    scene_file = slicer.mrmlScene.GetURL()
    if scene_file:
        return os.path.join(os.path.dirname(scene_file), ".slicer_project_memory.md")
    # Tmp fallback if scene is not saved and no workspace set
    return os.path.join(slicer.app.temporaryPath, ".slicer_project_memory.md")

def tool_read_memory(scope="global"):
    if scope == "global" and slicer.app.settings().value("SlicerClaw/EnableGlobalMemory", "true").lower() != "true":
        return "Global memory is disabled in settings. You may only read from 'project' scope."
    path = _get_global_memory_path() if scope == "global" else _get_project_memory_path()
    if not os.path.exists(path): return f"No {scope} memory found yet. You can append new lessons."
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Failed to read {scope} memory: {e}"

def tool_append_memory(scope, content):
    if scope == "global" and slicer.app.settings().value("SlicerClaw/EnableGlobalMemory", "true").lower() != "true":
        return "Global memory is disabled in settings. You may only append to 'project' scope."
    path = _get_global_memory_path() if scope == "global" else _get_project_memory_path()
    try:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"\\n\\n### Note [{timestamp}]\\n{content}\\n")
        return f"Successfully appended to {scope} memory at {path}"
    except Exception as e:
        return f"Failed to append {scope} memory: {e}"

def tool_get_node_properties(node_id):
    node = slicer.mrmlScene.GetNodeByID(node_id)
    if not node: return f"Node '{node_id}' not found"
    return str(node)

def tool_execute_python(code):
    exec_globals = {"__builtins__": __builtins__, "__result": None}
    for name in ("slicer", "vtk", "qt", "ctk"):
        if name in sys.modules: 
            exec_globals[name] = sys.modules[name]
    try:
        exec(code, exec_globals)
    except Exception:
        return f"Error:\n{traceback.format_exc()}"
    result = exec_globals.get("__result")
    if result is not None: return str(result)
    return "OK (no __result set)"

def tool_screenshot():
    slicer.app.processEvents()
    slicer.util.forceRenderAllViews()
    pixmap = slicer.util.mainWindow().grab()
    byteArray = qt.QByteArray()
    buf = qt.QBuffer(byteArray)
    buf.open(qt.QIODevice.WriteOnly)
    pixmap.save(buf, "PNG")
    b64 = base64.b64encode(bytes(byteArray.data())).decode("ascii")
    return f"Screenshot captured. Size: {len(b64)} bytes (omitted from text context to save space)."

OPENAI_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "list_nodes",
            "description": "List MRML nodes in the Slicer scene.",
            "parameters": {
                "type": "object",
                "properties": {
                    "className": {"type": "string", "description": "MRML node class filter e.g., 'vtkMRMLScalarVolumeNode'"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_node_properties",
            "description": "Get properties of an MRML node by its ID.",
            "parameters": {
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": "Execute Python code natively in 3D Slicer.",
            "parameters": {
                "type": "object",
                "properties": {"code": {"type": "string", "description": "Python code. Use slicer.util for common operations."}},
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "screenshot",
            "description": "Capture a screenshot of Slicer UI",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_slicer_knowledge",
            "description": "Search the downloaded local Slicer Knowledge Base for code snippets or API usage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Keyword to search for (e.g. 'markups', 'volume render')"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_long_term_memory",
            "description": "Read long-term memory to retrieve past lessons, common API usages, or project contexts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scope": {"type": "string", "enum": ["global", "project"], "description": "Global memory for general python APIs, or Project memory for current scene context."}
                },
                "required": ["scope"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "append_long_term_memory",
            "description": "Save an important lesson, error correction, or verified python pattern to your permanent memory so you know it for all future chats.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scope": {"type": "string", "enum": ["global", "project"]},
                    "content": {"type": "string", "description": "The detailed lesson, code snippet, or context to permanently remember."}
                },
                "required": ["scope", "content"]
            }
        }
    }
]

# ==============================================================================
# Embedded Slicer MCP Server (Port 2016)
# ==============================================================================

import WebServer
import WebServerLib

_mcpLogFile = os.path.join(slicer.app.temporaryPath, f"slicer-mcp-{os.getpid()}.log")

def mcpFileLog(*args):
    line = " ".join(str(a) for a in args)
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    with open(_mcpLogFile, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {line}\\n")

def mcpStatusMessage(msg):
    slicer.util.mainWindow().statusBar().showMessage(str(msg), 5000)

PROTOCOL_VERSION = "2025-03-26"
SERVER_INFO = {"name": "slicer-mcp", "version": "0.1.0"}
SERVER_CAPABILITIES = {"tools": {}}

MCP_TOOLS = []
TOOL_HANDLERS = {}

def mcp_tool(name, description, inputSchema):
    def decorator(func):
        MCP_TOOLS.append({
            "name": name,
            "description": description,
            "inputSchema": inputSchema,
        })
        TOOL_HANDLERS[name] = func
        return func
    return decorator

@mcp_tool(
    name="list_nodes",
    description="List MRML nodes in the Slicer scene. Returns name, id, and class.",
    inputSchema={
        "type": "object",
        "properties": {
            "className": {
                "type": "string",
                "description": "MRML node class filter (e.g. 'vtkMRMLScalarVolumeNode'). Default: all nodes."
            }
        }
    }
)
def _mcp_tool_list_nodes(args):
    return [{"type": "text", "text": tool_list_nodes(args.get("className", "vtkMRMLNode"))}]

@mcp_tool(
    name="get_node_properties",
    description="Get the full property dump of an MRML node by its ID.",
    inputSchema={
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "MRML node ID"}
        },
        "required": ["id"],
    }
)
def _mcp_tool_get_node_properties(args):
    return [{"type": "text", "text": tool_get_node_properties(args["id"])}]

@mcp_tool(
    name="execute_python",
    description="Execute Python code in the running Slicer environment. Set the variable __result to return a value.",
    inputSchema={
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Python code to execute"}
        },
        "required": ["code"],
    }
)
def _mcp_tool_execute_python(args):
    return [{"type": "text", "text": tool_execute_python(args["code"])}]

@mcp_tool(
    name="screenshot",
    description="Capture the Slicer application window as a PNG image.",
    inputSchema={"type": "object", "properties": {}}
)
def _mcp_tool_screenshot(_args):
    slicer.app.processEvents()
    slicer.util.forceRenderAllViews()
    pixmap = slicer.util.mainWindow().grab()
    byteArray = qt.QByteArray()
    buf = qt.QBuffer(byteArray)
    buf.open(qt.QIODevice.WriteOnly)
    pixmap.save(buf, "PNG")
    b64 = base64.b64encode(bytes(byteArray.data())).decode("ascii")
    return [{"type": "image", "data": b64, "mimeType": "image/png"}]

@mcp_tool(
    name="search_slicer_knowledge",
    description="Search the downloaded Slicer Knowledge Base (Skills) for code snippets, API usage, or documentation. Returns matches.",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Keyword to search for (e.g. 'markups', 'volume rendering')"}
        },
        "required": ["query"],
    }
)
def _mcp_tool_search_slicer_knowledge(args):
    query = args["query"].lower()
    # Attempt to locate the downloaded skills folder in likely places.
    possible_paths = [
        "/Users/liguimei/Documents/ppPrj/SlicerTotalSegmentator-main/TotalSegmentator/.opencode/skills/slicer-skill",
        os.path.expanduser("~/.opencode/skills/slicer-skill"),
        os.path.expanduser("~/Documents/slicer-skill"),
        os.path.join(slicer.app.temporaryPath, "slicer-skill"),
    ]
     
    # Ask Slicer for parent directory of modules and look there too
    moduleDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    possible_paths.insert(1, os.path.join(moduleDir, ".opencode", "skills", "slicer-skill"))
    possible_paths.insert(1, os.path.join(moduleDir, "slicer-skill"))

    kb_path = None
    for p in possible_paths:
        if os.path.exists(p):
            kb_path = p
            break
            
    if not kb_path:
        return [{"type": "text", "text": "Knowledge base not found. Please tell the user to download it from SlicerClaw UI under 'AI Knowledge Base (Skills & Data)'."}]

    results = []
    import glob
    for root, _, files in os.walk(kb_path):
        for file in files:
            if file.endswith((".py", ".md", ".txt", ".h", ".cxx")):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        
                        match_blocks = []
                        for i, line in enumerate(lines):
                            if query in line.lower():
                                start = max(0, i - 2)
                                end = min(len(lines), i + 7)
                                match_blocks.append("".join(lines[start:end]))
                                
                        if match_blocks:
                            rel_path = os.path.relpath(path, kb_path)
                            results.append(f"--- File: {rel_path} ---\\n" + "\\n...\\n".join(match_blocks[:3]))
                except Exception:
                    pass
                    
            if len(results) >= 5:
                break
        if len(results) >= 5:
            break
            
    if not results:
         return [{"type": "text", "text": f"No matches found for '{query}' in knowledge base at {kb_path}."}]
         
    return [{"type": "text", "text": f"Knowledge base search results from {kb_path}:\\n\\n" + "\\n\\n".join(results)}]

@mcp_tool(
    name="read_long_term_memory",
    description="Read long-term memory to retrieve past lessons, common API usages, or project contexts.",
    inputSchema={
        "type": "object",
        "properties": {
            "scope": {"type": "string", "enum": ["global", "project"], "description": "Global memory for general python APIs, or Project memory for current scene context."}
        },
        "required": ["scope"]
    }
)
def _mcp_tool_read_long_term_memory(args):
    return [{"type": "text", "text": tool_read_memory(args.get("scope", "global"))}]

@mcp_tool(
    name="append_long_term_memory",
    description="Save an important lesson, error correction, or verified python pattern to your permanent memory so you know it for all future chats.",
    inputSchema={
        "type": "object",
        "properties": {
            "scope": {"type": "string", "enum": ["global", "project"]},
            "content": {"type": "string", "description": "The detailed lesson, code snippet, or context to permanently remember."}
        },
        "required": ["scope", "content"]
    }
)
def _mcp_tool_append_long_term_memory(args):
    return [{"type": "text", "text": tool_append_memory(args.get("scope", "global"), args.get("content"))}]

def _ok(id, result):
    return {"jsonrpc": "2.0", "id": id, "result": result}

def _err(id, code, message):
    return {"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}}

def _dispatch(msg):
    method = msg.get("method")
    msg_id = msg.get("id")
    params = msg.get("params", {})
    if method == "initialize":
        return _ok(msg_id, {"protocolVersion": PROTOCOL_VERSION,"capabilities": SERVER_CAPABILITIES,"serverInfo": SERVER_INFO})
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "ping":
        return _ok(msg_id, {})
    if method == "tools/list":
        return _ok(msg_id, {"tools": MCP_TOOLS})
    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        handler = TOOL_HANDLERS.get(tool_name)
        if not handler:
            return _err(msg_id, -32602, f"Unknown tool: {tool_name}")
        try:
            content = handler(arguments)
            return _ok(msg_id, {"content": content, "isError": False})
        except Exception:
            return _ok(msg_id, {"content": [{"type": "text", "text": traceback.format_exc()}], "isError": True})
    if msg_id is not None:
        return _err(msg_id, -32601, f"Method not found: {method}")
    return None

class MCPRequestHandler(WebServerLib.BaseRequestHandler):
    _access_allowed = None

    def __init__(self, logMessage=None):
        self.logMessage = logMessage or mcpFileLog

    def _check_access(self) -> bool:
        if MCPRequestHandler._access_allowed is not None:
            return MCPRequestHandler._access_allowed
        MCPRequestHandler._access_allowed = True
        return MCPRequestHandler._access_allowed

    def canHandleRequest(self, uri: bytes, **_kwargs) -> float:
        parsedURL = urllib.parse.urlparse(uri)
        return 0.5 if parsedURL.path == b"/mcp" else 0.0

    def handleRequest(self, method: str, uri: bytes, requestBody: bytes, **_kwargs) -> tuple[bytes, bytes]:
        if not self._check_access(): return b"application/json", json.dumps(_err(None, -32600, "Access denied")).encode()
        if method == "GET": return b"application/json", json.dumps(_err(None, -32600, "SSE not implemented")).encode()
        if method == "DELETE": return b"application/json", b'{"ok":true}'
        if method != "POST": return b"application/json", json.dumps(_err(None, -32600, "Unsupported HTTP method")).encode()
        try:
            msg = json.loads(requestBody)
        except Exception as e:
            return b"application/json", json.dumps(_err(None, -32700, str(e))).encode()
        if isinstance(msg, list):
            responses = [resp for resp in (_dispatch(item) for item in msg) if resp is not None]
            if not responses: return b"application/json", b"{}"
            body = responses if len(responses) > 1 else responses[0]
            return b"application/json", json.dumps(body).encode()
        
        response = _dispatch(msg)
        if response is None: return b"application/json", b"{}"
        return b"application/json", json.dumps(response).encode()

def start_embedded_mcp_server():
    global mcpLogic
    try:
        if "mcpLogic" in globals():
            mcpLogic.stop()
    except:
        pass
    try:
        mcpLogic = WebServer.WebServerLogic(
            port=2016,
            logMessage=mcpFileLog,
            enableSlicer=False,
            enableExec=False,
            enableStaticPages=False,
            enableDICOM=False,
            enableCORS=True,
            requestHandlers=[MCPRequestHandler(logMessage=mcpFileLog)],
        )
        mcpLogic.start()
        print(f"\\n  [SlicerClaw] External AI MCP Server online: http://localhost:{mcpLogic.port}/mcp")
    except Exception as e:
        print(f"\\n  [SlicerClaw] Failed to start MCP API: {e}")

_startup_retries = 0
def delayed_start_embedded_mcp_server():
    global _startup_retries
    if not hasattr(slicer.modules, 'webserver'):
        if _startup_retries < 20: 
            _startup_retries += 1
            qt.QTimer.singleShot(500, delayed_start_embedded_mcp_server)
        else:
            print("\\n  [SlicerClaw] Failed to start: Slicer WebServer module was not found after 10s.")
        return
    start_embedded_mcp_server()

qt.QTimer.singleShot(100, delayed_start_embedded_mcp_server)
