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

# ==============================================================================
# slicerClaw
# ==============================================================================
class slicerClaw(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "slicerClaw"
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
# slicerClawWidget (The Settings UI)
# ==============================================================================
class slicerClawWidget(ScriptedLoadableModuleWidget):
    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        settingsCollapsibleButton = ctk.ctkCollapsibleButton()
        settingsCollapsibleButton.text = "AI API Settings"
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
        self.saveButton.toolTip = "Save the configuration to Slicer settings."
        settingsFormLayout.addRow("", self.saveButton)
        self.saveButton.connect('clicked(bool)', self.onSaveSettings)

        self.layout.addStretch(1)

        self.logic = slicerClawLogic()
        self.loadSettings()
        
        # Ensures the logic installs the hook once the UI is loaded (for cases where user hasn't opened it before)
        self.logic.ensureUiHook()

    def loadSettings(self):
        settings = slicer.app.settings()
        self.apiUrlEdit.text = settings.value("slicerClaw/ApiUrl", "https://coding.dashscope.aliyuncs.com/v1/chat/completions")
        self.apiKeyEdit.text = settings.value("slicerClaw/ApiKey", "")
        self.modelEdit.text = settings.value("slicerClaw/ModelName", "glm-5")
        
        saved_lang = settings.value("slicerClaw/Language", "中文 (Chinese)")
        index = self.languageCombo.findText(saved_lang)
        if index >= 0:
            self.languageCombo.currentIndex = index

    def onSaveSettings(self):
        settings = slicer.app.settings()
        settings.setValue("slicerClaw/ApiUrl", self.apiUrlEdit.text.strip())
        settings.setValue("slicerClaw/ApiKey", self.apiKeyEdit.text.strip())
        settings.setValue("slicerClaw/ModelName", self.modelEdit.text.strip())
        settings.setValue("slicerClaw/Language", self.languageCombo.currentText)
        slicer.util.messageBox("Settings saved successfully!")
        self.logic.loadSettings()

# ==============================================================================
# slicerClawLogic (Agent Core & Spotlight UI)
# ==============================================================================
class slicerClawLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        self.chatHistory = []
        self.loadSettings()
        
    def loadSettings(self):
        settings = slicer.app.settings()
        self.api_url = settings.value("slicerClaw/ApiUrl", "https://coding.dashscope.aliyuncs.com/v1/chat/completions")
        self.api_key = settings.value("slicerClaw/ApiKey", "")
        self.api_model = settings.value("slicerClaw/ModelName", "glm-5")
        self.api_lang = settings.value("slicerClaw/Language", "中文 (Chinese)")
        
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
            print("\n[AI Copilot Error] Please configure the API Key in the slicerClaw module settings first!")
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
    }
]

# Provide automatic initialization upon Slicer startup if the module is loaded but UI isn't displayed
def __init_copilot__():
    try:
        if not hasattr(slicer, "ai_spotlight_chat"):
            logic = slicerClawLogic()
            logic.ensureUiHook()
    except Exception as e:
        print(f"Failed to auto-init slicerClaw: {e}")

qt.QTimer.singleShot(100, __init_copilot__)
