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

# ==============================================================================
# SlicerClawWidget (The Settings UI)
# ==============================================================================
class SlicerClawWidget(ScriptedLoadableModuleWidget):
    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        self.logic = SlicerClawLogic()

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

        self.saveButton = qt.QPushButton("Save Settings & Apply")
        settingsFormLayout.addRow("", self.saveButton)
        self.saveButton.connect('clicked(bool)', self.onSaveSettings)

        # --- Section B: External AI Connection (MCP) ---
        mcpCollapsibleButton = ctk.ctkCollapsibleButton()
        mcpCollapsibleButton.text = "2. External AI Connection (Cursor/Claude)"
        mcpCollapsibleButton.collapsed = True
        self.layout.addWidget(mcpCollapsibleButton)
        mcpLayout = qt.QVBoxLayout(mcpCollapsibleButton)
        
        mcpInfo = qt.QLabel("The built-in MCP Server is running at <b>http://127.0.0.1:2016/mcp</b>.<br><br>"
                            "To control Slicer from external AI like Cursor or OpenCode, "
                            "first generate the CLI bridge script, then configure your AI to run it.")
        mcpInfo.setWordWrap(True)
        mcpLayout.addWidget(mcpInfo)
        
        self.btnGenerateBridge = qt.QPushButton("Generate Local slicer_mcp_bridge.py")
        self.btnGenerateBridge.connect('clicked(bool)', self.onGenerateBridge)
        mcpLayout.addWidget(self.btnGenerateBridge)

        configInfo = qt.QTextEdit()
        configInfo.setReadOnly(True)
        configInfo.setPlainText('{\n  "mcpServers": {\n    "slicer-agent": {\n      "command": "python",\n      "args": ["/path/to/slicer_mcp_bridge.py"]\n    }\n  }\n}')
        configInfo.setMaximumHeight(120)
        mcpLayout.addWidget(configInfo)

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

        self.layout.addStretch(1)

        self.loadSettings()
        self.logic.ensureUiHook()

    def loadSettings(self):
        settings = slicer.app.settings()
        self.apiUrlEdit.text = settings.value("SlicerClaw/ApiUrl", "https://coding.dashscope.aliyuncs.com/v1/chat/completions")
        self.apiKeyEdit.text = settings.value("SlicerClaw/ApiKey", "")
        self.modelEdit.text = settings.value("SlicerClaw/ModelName", "glm-5")
        
        saved_lang = settings.value("SlicerClaw/Language", "中文 (Chinese)")
        index = self.languageCombo.findText(saved_lang)
        if index >= 0:
            self.languageCombo.currentIndex = index

    def onSaveSettings(self):
        settings = slicer.app.settings()
        settings.setValue("SlicerClaw/ApiUrl", self.apiUrlEdit.text.strip())
        settings.setValue("SlicerClaw/ApiKey", self.apiKeyEdit.text.strip())
        settings.setValue("SlicerClaw/ModelName", self.modelEdit.text.strip())
        settings.setValue("SlicerClaw/Language", self.languageCombo.currentText)
        slicer.util.messageBox("Settings saved successfully!")
        self.logic.loadSettings()

    def onGenerateBridge(self):
        out_path = qt.QFileDialog.getSaveFileName(slicer.util.mainWindow(), "Save Bridge Script", "slicer_mcp_bridge.py", "Python Files (*.py)")
        if not out_path:
            return
        
        code = '''import sys\nimport json\nimport urllib.request\nimport urllib.error\n\nSLICER_MCP_URL = "http://127.0.0.1:2016/mcp"\n\ndef main():\n    while True:\n        try:\n            line = sys.stdin.readline()\n            if not line: break\n            line = line.strip()\n            if not line: continue\n            req = urllib.request.Request(SLICER_MCP_URL, data=line.encode('utf-8'))\n            req.add_header('Content-Type', 'application/json')\n            try:\n                response = urllib.request.urlopen(req, timeout=120)\n                sys.stdout.write(response.read().decode('utf-8') + "\\n")\n                sys.stdout.flush()\n            except urllib.error.URLError as e:\n                try:\n                    msg = json.loads(line)\n                    if msg.get("id") is not None:\n                        err = {"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32000, "message": str(e)}}\n                        sys.stdout.write(json.dumps(err) + "\\n")\n                        sys.stdout.flush()\n                except: pass\n        except KeyboardInterrupt: break\n        except Exception as e: sys.stderr.write(f"Bridge error: {e}\\n")\n\nif __name__ == '__main__':\n    main()'''
        
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(code)
            slicer.util.messageBox(f"Bridge created at:\\n{out_path}\\n\\nPoint your Cursor/Claude MCP config to this file.")
        except Exception as e:
            slicer.util.errorDisplay(f"Failed to create bridge: {e}")

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
        
        lang_instruction = "Please communicate in Chinese." if "中文" in self.api_lang else "Please communicate in English."
        sys_msg = f"You are a helpful AI assistant operating directly inside 3D Slicer. You can call tools to query the scene and execute python code natively. Be concise, precise, and polite. {lang_instruction}"
        
        if not self.chatHistory or self.chatHistory[0]["role"] != "system":
            self.chatHistory.insert(0, {"role": "system", "content": sys_msg})
        else:
            self.chatHistory[0]["content"] = sys_msg
        
        if hasattr(slicer, "ai_spotlight_chat") and slicer.ai_spotlight_chat is not None:
            slicer.ai_spotlight_chat.update_language(self.api_lang)

    def ensureUiHook(self):
        if not hasattr(slicer, "ai_spotlight_chat") or slicer.ai_spotlight_chat is None:
            slicer.ai_spotlight_chat = SpotlightChat(self)

        toolbar = slicer.util.mainWindow().findChild("QToolBar", "AICopilotToolBar")
        if not toolbar:
            toolbar = slicer.util.mainWindow().addToolBar("AI Copilot")
            toolbar.setObjectName("AICopilotToolBar")
            ai_action = toolbar.addAction("🧠 唤起 AI 大脑 (Ctrl+I)")
            ai_action.setObjectName("AIChatAction")
            ai_action.connect("triggered()", slicer.ai_spotlight_chat.toggle_visibility)

    def doChatLoop(self, user_msg):
        if not self.api_key:
            print("\n[AI Copilot Error] Please configure the API Key in the SlicerClaw module settings first!")
            return
            
        print(f"\n[You]: {user_msg}\n")
        self.chatHistory.append({"role": "user", "content": user_msg})
        
        for _ in range(5):
            payload = {
                "model": self.api_model,
                "messages": self.chatHistory,
                "tools": OPENAI_TOOLS_SCHEMA,
                "tool_choice": "auto"
            }
            
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(self.api_url, data=data)
            req.add_header('Content-Type', 'application/json')
            req.add_header('Authorization', f'Bearer {self.api_key}')
            
            try:
                print("⏳ 正在思考...")
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
                        print(f"🔧 [执行工具]: {f_name}({f_args})")
                        
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
                        print(f"✅ 工具返回结果已发往大模型，等待下一步指示...\n")
                    continue
                else:
                    hint = "👉 (按 Ctrl+I 继续对话...)" if "中文" in getattr(self, "api_lang", "中文") else "👉 (Press Ctrl+I to continue...)"
                    print(f"\n{hint}\n")
                    break
                    
            except urllib.error.HTTPError as e:
                err_body = ""
                try:
                    err_body = e.read().decode('utf-8')
                except:
                    pass
                print(f"\n❌ [Error] 请求大模型失败 ({e.code}): {e.reason}\n详细信息: {err_body}")
                self.chatHistory.pop()
                slicer.util.errorDisplay(f"API Request Failed: {e.code} {e.reason}\n{err_body}")
                break
            except Exception as e:
                print(f"\n❌ [Error] 请求大模型失败: {e}")
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
        self.update_language(self.logic.api_lang if hasattr(self.logic, 'api_lang') else "中文 (Chinese)")
        self.input_edit.setStyleSheet("""
            QLineEdit {
                background: transparent;
                color: white;
                font-size: 20px;
                border: none;
                qproperty-cursorPosition: 0;
            }
        """)
        self.input_edit.setMinimumWidth(500)
        self.input_edit.setMinimumHeight(40)
        container_layout.addWidget(self.input_edit)
        main_layout.addWidget(self.container)
        
        self.input_edit.connect("returnPressed()", self.on_enter)

    def update_language(self, lang):
        if "中文" in lang:
            self.input_edit.setPlaceholderText("告诉 AI 你想做什么... (按回车发送, 按 Esc 关闭)")
        else:
            self.input_edit.setPlaceholderText("Tell AI what to do... (Press Enter to send, Esc to close)")
        
        self.shortcut = qt.QShortcut(qt.QKeySequence("Ctrl+I"), slicer.util.mainWindow())
        self.shortcut.connect("activated()", self.toggle_visibility)

        # Global hook to intercept module loads just in case
        self._obs = slicer.mrmlScene.AddObserver(slicer.mrmlScene.StartImportEvent, self._keepAlive)

    def _keepAlive(self, caller, event):
        pass # To satisfy python garbage collection

    def keyPressEvent(self, event):
        if event.key() == qt.Qt.Key_Escape:
            self.hide()
        super().keyPressEvent(event)

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show_center()

    def show_center(self):
        self.input_edit.clear()
        main_window = slicer.util.mainWindow()
        if main_window:
            geom = main_window.geometry
            w = 600
            h = 100
            x = geom.x() + (geom.width() - w) // 2
            y = geom.y() + (geom.height() - h) // 3
            self.setGeometry(x, y, w, h)
        self.show()
        self.raise_()
        self.input_edit.setFocus()

    def on_enter(self):
        text = self.input_edit.text.strip()
        if not text:
            return
        self.hide()
        qt.QTimer.singleShot(50, lambda: self.logic.doChatLoop(text))


# ==============================================================================
# Helper Tools Methods
# ==============================================================================
def tool_list_nodes(className="vtkMRMLNode"):
    nodes = slicer.util.getNodesByClass(className)
    result = [{"name": n.GetName(), "id": n.GetID(), "class": n.GetClassName()} for n in nodes]
    return json.dumps(result, indent=2)

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
    }
]

# Provide automatic initialization upon Slicer startup if the module is loaded but UI isn't displayed
def __init_copilot__():
    try:
        if not hasattr(slicer, "ai_spotlight_chat"):
            logic = SlicerClawLogic()
            logic.ensureUiHook()
    except Exception as e:
        print(f"Failed to auto-init SlicerClaw: {e}")

qt.QTimer.singleShot(100, __init_copilot__)

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
