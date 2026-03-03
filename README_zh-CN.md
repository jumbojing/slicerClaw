<p align="center">
  <img src="SlicerClaw/Resources/Icons/SlicerClaw.png" width="200" alt="SlicerClaw Logo">
</p>

# SlicerClaw (3D Slicer 原生 AI 智能体与 MCP 服务器)

[English](README.md) | 简体中文

一款拥有革命性体验、响应极速的 3D Slicer 原生 AI 助手。
SlicerClaw 为您提供了一个无缝的、“Spotlight”风格的悬浮命令控制台进行强大的原生控制，同时它还会在 2016 端口静默运行一个安全的 **模型上下文协议 (MCP)** 服务器，允许外部 AI 工具（如 Cursor、Claude Desktop、OpenCode 等）直接“看见”并控制您的 3D Slicer 环境。

## ✨ 核心特性

- **Spotlight 悬浮控制台:** 告别笨重、占据屏幕空间的侧边栏皮肤。在 Slicer 界面通过点击工具栏按钮，或者在成功启动插件后按下 `Ctrl+I` (Mac 下为 Cmd+I) 即可召唤出绝美的半透明悬浮框。
- **内嵌的 MCP 服务器:** 通过标准的 JSON-RPC HTTP 请求 (`http://127.0.0.1:2016/mcp`)，将 Slicer 强大的 Python 环境安全地暴露给外部强力 AI 客户端。
- **原生函数调用 (Tool Calling):** 请务必在聊天框中点亮 🦞 按钮进入 Slicer 操作模式！在此模式下内置与外接的 AI 均拥有直接访问 Slicer Python 运行库的权限，执行任何 Python 代码构建复杂的医疗三维场景。
- **一键生成 MCP 桥接器:** 通过自带的可视化 UI 面板，您可以一键生成 `slicer_mcp_bridge.py` 脚本，用来无缝对接基于标准输入输出 (stdio) 的热门外部 AI 客户端。
- **内置的知识库下载器:** 从 UI 中直接下载并解压 Slicer 的各路 AI 技能库 (Skills)（例如：`jumbojing/slicerSkill`、Slicer 源代码库、官方论坛高阶问答归档），以此赋予缺乏领域知识基座的通用大模型针对 3D Slicer 的“专业字典”。
- **全自动的知识发现机制:** 内部的 MCP Server 会自动扫描和读取您下载的本地技能知识库。外部请求代码协助的 AI 不再需要手动挂载成百上千篇文档，即可在生成代码前自动搜索并利用。
- **进化化长期记忆 (Evolution Memory):** 全新的双轨长程记忆机制！AI 助理现在可以把血泪教训、纠正过的 Slicer 代码范式以及当前项目的解剖学语境主动沉淀写进本地 Markdown，重开软件也不会失忆！它甚至会在回答难题前自动翻看这本过去的日记本。
- **话唠安全博导模式 (Dr. Verboser Mode):** 勾选此项，瞬间强制给轻量化 AI 注入类似顶级思考模型（R1）的“反身性查房系统”！AI 在调用真正的代码改造场景前，必须先输出一段叫作 `🩺 Dr. Verboser Analysis:` 的长篇大论，仔细论述它的动机、参考文献来源以及代码后遗症评估，让人类放心。

## 📥 安装指南

1. 使用 Git 克隆或直接下载本仓库到本地计算机：
   ```bash
   git clone https://github.com/jumbojing/slicerClaw.git
   ```
2. 打开 3D Slicer。
3. 导航至左上角菜单栏: **Edit -> Application Settings -> Modules**。
4. 将克隆下来的 `slicerClaw` 目录路径添加到框内的 **Additional Module Paths** 中。
5. 重启 3D Slicer。

## 💡 使用指南

### 1. 原生 Spotlight 对话配置
从 3D Slicer 模块选择下拉菜单中打开 **SlicerClaw** 模块。在首个面板中，填入您的 `API Base URL`（API 地址）和 `API Key`（例如使用 OpenAI 或 阿里云百炼的模型密钥）。

> **💡 [首次唤醒注意]**
> 您可以点击工具栏里带有 🧠 图标的 `Spotlight Chat (Cmd/Ctrl+I)` 按钮来**首次唤醒**悬浮输入框。后续均可在任意位置通过快捷键 `Ctrl+I` (Mac: Cmd+I) 实现秒级呼出。

在对话框中：

- 默认状态下 (🦞 按钮灰暗)：模型处于**纯文本聊天模式**。
- **点亮 🦞 按钮**：进入 Slicer 接管操作模式！此时允许 AI 自主调用 Slicer 内置 API 分析并修改当前场景。

在自然语言中输入您的请求，AI 便会在后台开始奇妙的魔法！

### 2. 连接外部 AI 客户端 (MCP)
如果您更习惯在 Cursor、OpenCode 或 Claude Desktop 等外部 AI 工具中向 Slicer 下达指令，SlicerClaw 提出了领先的 **AI自动配网（AI-Driven Auto-Setup）** 机制：

1. 打开 3D Slicer 中的 SlicerClaw 模块面板，展开 **"2. External AI Connection (Cursor/Claude)"** 选项卡。
2. 点击 **"📋 Copy One-Click Setup Prompt"** 按钮。这会将一段带有极其明确结构指令的 Prompt （不仅包含了必要的 Python 桥接源码、也包含了您的本地各种系统绝对路径）直接复制到您的剪贴板中。
3. 去您的外部 AI 软件（如 Cursor, Claude Desktop）的新会话聊天框中，**直接粘贴发送 (Ctrl+V) 这段暗号**。
4. 您的 AI 助手由于看懂了这段提示词，它会自动建立 `slicer_mcp_bridge.py` 文件填入代码，并且去修改自身的 MCP json 配置文件。您毫无任何配置心智负担。

当 AI 回复它已经成功连上之后，尝试对它说：“帮我列出 Slicer 当前场景的所有模型”，见证它跨软件接管 Slicer 的奇迹吧！

### 3. 下载 Slicer 专属技能训练库 (Knowledge Base)
为了尽可能防止通用大型模型在调用 Slicer Python APIs 时胡编乱造产生幻觉：
1. 打开 SlicerClaw 模块，展开 **"3. AI Knowledge Base (Skills & Data)"** 选项卡。
2. 在下拉框中选择您需要的技能知识库数据源（如强烈推荐默认的 `jumbojing/slicerSkill` 或本地基础源码）。
3. 点击 **Download & Extract** ，将知识包解压保存在您的常规工作目录中（例如 `.opencode/skills`）。
4. SlicerClaw 的 MCP 中枢服务器会自动探测这些文件；当 AI 对未知 Slicer 编程领域感到疑惑时会自动检索它！

*注：此版本的本地知识技能挂载机制以及 MCP 连接的原始思路深度致敬了 [pieper/slicer-skill](https://github.com/pieper/slicer-skill) 中的开创性工作。*

### 4. AI 进化记忆库 (Evolution Memory)
AI 在不断的纠错和解决疑难杂症的过程中会通过 MCP 调用特制的记忆工具包写入日记，你可以随时核查它到底学到了什么：
1. 展开 **"4. AI Evolution Memory Bank"** 面板。
2. 勾选 / 取消勾选 **"Enable Global Memory"**：用于控制 AI 是否能跨项目读写全局经验（如果你只想让它专注当前病案，即可关掉此项）。
3. 点击 **"👁️ View Global Memory"**：修改全局记忆本（通常位于 `~/.slicerClaw/global_memory.md`），或者点击右侧的 **"🧹 Clear Global Memory"** 清空忘却所有教训。
4. **项目专属记忆:** 只要当前 Slicer 场景存在哪怕是一个临时的未存盘路径，AI 会在同级目录生成 `.slicer_project_memory.md`。使用面板第二排专供项目的 **"👁️ View Project Memory"** 或 **"🧹 Clear Project Memory"** 按钮即可轻松审查或重置当前这例特定影像病案的操作关联经验！

## ⚠️ 极其重要的安全警告

**请在运转 MCP 服务器并将其暴露给外部 AI 控制时保持极高的警惕。**

SlicerClaw MCP 服务器赋予了任何连入系统的 MCP 客户端在您的 Slicer 进程内**执行任意 Python 代码**的至高权限。这是一项威力极其巨大的功能，但同样伴随巨大的风险：

* **代码执行风险:** 一个遭到入侵，或者是正在产生“灾难性幻觉”的 AI 发出的客户端指令，能够利用 Slicer 进程持有的同等完整宿主机文件权限运行任何危险命令（例如意外调用了 `os.remove()`），这可能造成严重的数据损毁。
* **个人医疗健康信息 (PHI) 保护:** 如果您正在处理真实的患者医学影像数据或其它必须保密的记录，请警惕 MCP 客户端（以及连接在这个客户端背后的广域网云端大模型服务）在执行截图工具或向原生场景拿取元数据时将敏感包含 PHI 特征的数据发送出局。请确保您的使用方式必须合规于您所在医疗机构的 HIPAA（或同等级别）个人医疗保密协议和数据规章制度。
* **第三方商业闭源模型拦截:** 注意您的提示词对话、截图工具返回的回执、以及复杂的场景元数据绝大部分情况下都必须通过互联网传递到云端 AI 商业厂商的服务期里（如 OpenAI、Claude 等）。除非您有把握将本地化的完整体模型（如 Llama3 本地部署）对接为后端，否则不要以为仅仅基于本地的 MCP 连接能让您的所有隐私数据也全部呆在本地。
* **不要暴露您的内网端口:** 切勿将默认的 `2016` 端口穿透进公共互联网络，或是在没有严格防火墙保护的不受信任办公网络内放开它的绑定。SlicerClaw 的系统安全性严格立足于只接听来自本机调试回环地 (`127.0.0.1`) 的直接命令。

**作者强烈建议:** 如果您正在测试一款并不完全信任或是能力未知极不稳定的 Agent 模型，请务必将包含 MCP 服务器和 3D Slicer 本体的主程序放入沙盒容器环境（例如 Docker 诸如 SlicerDockers 等工具或虚拟机等）中运行，严格限定测试的爆炸影响半径。

## 🚀 未来的开发路线图 (TODOs)

SlicerClaw 正在极速进化中！以下列出了我们的优先攻坚难题：
- [ ] **执行环境沙盒化 (Sandboxed Execution):** 给这把巨大的“手术刀”( `execute_python` 工具)套上一层限制读取宿主机敏感目录或屏蔽调用危险文件系统 `os` 功能包的沙盒执行外壳。
- [ ] **原生大模型图形视联 (Multi-Modal AI Support):** 使外部强力的视觉语义大模型不仅能靠通过 MCP 回传的编码看图；也期待不久后能将这些前瞻的多模态能力注入其 SlicerClaw 的内建原生悬浮窗中，直接截图发送给对话框。
- [ ] **上下文检索引擎 (Context Window Optimization):** 内建自带的 `search_slicer_knowledge` 目前往往粗暴地灌入超大段 markdown 文本。团队计划使用本地完全隔离化部署的文本推理向量嵌入工具 (Local Vector Embeddings Engine) 给查询构建 RAG (Retrieval-Augmented Generation) 数据链，降低 Token 无谓损耗。
- [ ] **零代码自动化宏生成 (Task Automation Macros):** 录制下您的自然语义所促使 AI 在 SlicerClaw 里做出的每一步反馈和所有跑通过的代码；将这些交互转换为只需普通一击点击即可在日后随意一劳永逸复用的 Python 自动化宏命令。
- [ ] **报错智能自愈死循环 (Auto-Correct Loops):** 若 AI 狂妄无知地发出的一条命令却让 Slicer 全局触发底层或者 UI 级别的异常报错，将这个 Traceback 调用栈主动抓取并且沉默地再甩回到 LLM 给其一个反省机会，使之自我调试自我修复直到写出正确的代码为止。
- [x] **跨版本时空的长效记忆机制 (Long-Term Memory):** 赋予您桌面上这颗智脑以跨越这单次启动界面的持久记忆力，能够记得之前对工作流您的各种奇葩偏爱或者是它之前对它反复叮咛不要犯的重构教训，构建出一个完全拟人与专属于当前工作病案的高端语境。
- [x] **自动学习强化与物种进化 (Self-Learning & Evolution):** 让这个 Agent 模型不仅可以被动的读字典，甚至能在完成各种刁钻的用户需求尝试之后主动的凝练成功要素，化身为一名“开源讲师”总结属于自己的“小笔记技巧脚本”，将成果逆向反哺保存到知识库里，做到越来越强、真正无止境进化的工具精灵！

## 🔗 相关核心链接与致敬

SlicerClaw 建立在其背后整个蓬勃向上的 3D Slicer 的 AI 革新生态。作者高度建议您亲自访问如下这些璀璨夺目的启明星开源探索：

* **[pieper/slicer-skill](https://github.com/pieper/slicer-skill)** — 最先将 Claude 以及基于此建立起来针对 3D Slicer MCP 接入规范理念落地的基础开源代码。*这也是直接赋予启发了 SlicerClaw 有关这部分系统全套架构以及技能资料包解发逻辑机制诞生的伟大学习宝库。*
* **[jumbojing/slicerSkill](https://github.com/jumbojing/slicerSkill)** — 基于这套规范演进而诞生，内容收纳丰富详实，囊括云检索、现作为 SlicerClaw 强力推荐且内置搭载的核心 AI 本地技能辞典大全！
* **[mcp-slicer](https://github.com/zhaoyouj/mcp-slicer)** — 由开发者 @zhaoyouj 实现，目前完全可以通过 `pip` 直接静默部署脱离宿主程序环境外部驻留呼叫原生 3D Slicer 内置网络服务器接口的跨端 MCP 服务器版本。
* **[SlicerDeveloperAgent](https://github.com/muratmaga/SlicerDeveloperAgent)** — Murat Maga 大牛将类似机制思路接入 Gemini 推理模块让用户不必跳出画面也能对脚本指手画脚的 Slicer 环境内嵌式 AI 操作助手。
* **[SlicerChat: Building a Local Chatbot for 3D Slicer](https://arxiv.org/abs/2407.11987)** (Barr, 2024) — 在不使用在线庞大计算量为代价，基于本地方案搭建运行 LLM 助手对入门者指导 Slicer 上手的高水平前沿科研探讨文献。

## 🙏 鸣谢 `AI`

特别感谢以下为本项目体验与代码重构全流程提供不可思议支持的技术力量：

* **Antigravity (Google DeepMind)** — 自动理解需求、独立重写了全套全新架构面板并亲手构建了内置极速 MCP 大杀器服务器底层逻辑的超级 AI 编码引擎！
* **OpenCode** — 搭建了极其优秀的 AI IDE 集成桥接环境，使得外部对话中枢能够丝滑、毫无阻力地接管并控制 3D Slicer 的虚拟世界。
* **GLM-5 (智谱 AI)** — 赋予这一切原生交互以毫无妥协的中文逻辑推理与原生复杂 Tool Calling 执行能力的顶级基座大模型。


