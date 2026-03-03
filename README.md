<p align="center">
  <img src="SlicerClaw/Resources/Icons/SlicerClaw.png" width="200" alt="SlicerClaw Logo">
</p>

# SlicerClaw (Slicer Native AI Agent & MCP Server)

English | [简体中文](README_zh-CN.md)

A revolutionary, lightning-fast AI assistant natively integrated into 3D Slicer.
SlicerClaw provides a seamless, "Spotlight"-style floating command bar for native control, while simultaneously running a secure **Model Context Protocol (MCP)** server on port 2016 to allow external AI tools (like Cursor, Claude Desktop, OpenCode) to control your 3D Slicer environment.

## Features

- **Spotlight Floating Console:** Say goodbye to clunky, screen-hogging sidebar skins. Summon a stunning, translucent floating panel from anywhere in Slicer by clicking the toolbar button or just pressing `Ctrl+I` (Cmd+I on Mac).
- **Embedded MCP Server:** Safely exposes Slicer's mighty Python environment to external AI powerhouses via standard JSON-RPC HTTP requests (`http://127.0.0.1:2016/mcp`).
- **Native Tool Calling:** Click the 🦞 button in the chat box to enter Slicer Mode! In this mode, both built-in and external AIs have direct access to Slicer's Python runtime. They can list scene nodes, get properties, take screenshots, and execute raw code to orchestrate complex medical 3D scenes.
- **One-Click MCP Bridge Generator:** Easily generate a `slicer_mcp_bridge.py` script from the UI to seamlessly connect stdio-based AI clients (like Claude/Cursor).
- **Built-in Knowledge Base Downloader:** Directly download and extract Slicer AI Skills (e.g., `jumbojing/slicerSkill`, Slicer Source Code, Discourse Archives) from the UI to empower your models with 3D Slicer's specific coding context.
- **Auto Skill Discovery:** The internal MCP tools will automatically search your downloaded skills so external AIs don't have to manually mount the folders.
- **Evolution Memory (Long-term):** SlicerClaw now features a permanent memory bank! AI assistants can actively dump lessons learned, preferred workflows, and Slicer API corrections into global and project-level `.md` diaries. They will "read" this evolution memory in future sessions to avoid making the same mistakes twice!
- **Dr. Verboser Mode:** Enable the `Dr. Verboser` checkbox to force the AI into a cautious, hyper-analytical persona. Before any Slicer scene modification, the AI MUST output a detailed `🩺 Dr. Verboser Analysis`, explaining its reasoning, citing specific Slicer API docs from the Knowledge Base, and evaluating potential risks.

## Installation

1. Clone or download this repository to your local machine:
   ```bash
   git clone https://github.com/jumbojing/slicerClaw.git
   ```
2. Open 3D Slicer.
3. Go to **Edit -> Application Settings -> Modules**.
4. Add the `slicerClaw` directory to your Additional Module Paths.
5. Restart 3D Slicer.

## Usage

### 1. Native Spotlight Chat
Open the **SlicerClaw** module from Slicer's module selector. In the first panel, enter your `API Base URL` and `API Key` (e.g. from OpenAI, Anthropic, or Alibaba Cloud).

> **💡 [First Launch Note]**
> You can hit the `Spotlight Chat (Cmd/Ctrl+I)` button with the 🧠 icon on the toolbar to **summon** the input box for the first time. Afterwards, you can use the shortcut `Ctrl+I` (Mac: Cmd+I) to bring it up instantly from anywhere.

In the chat box:
- By default (Dim 🦞 button): The model acts as a **pure text chat**.
- **Lit 🦞 button**: Enters Slicer operation mode! The AI can securely call native Slicer APIs to analyze or modify the current scene.

Type your request in natural language and the AI will work its magic entirely in the background!

### 2. External AI Connection (MCP)
If you prefer using external AI tools like Cursor, OpenCode, or Claude Desktop to control Slicer, SlicerClaw now provides an **AI-Driven Auto-Setup**:

1. Open the SlicerClaw module in 3D Slicer and expand the **"2. External AI Connection (Cursor/Claude)"** panel.
2. Click the **"📋 Copy One-Click Setup Prompt"** button. This will copy a highly-structured prompt (including the bridge source code and your local paths) to your clipboard.
3. Go to your external AI software (Cursor, Claude, windsurf, etc.) and simply **paste (Ctrl+V) the prompt into your chat window**.
4. The external AI will automatically read the instructions, create the `slicer_mcp_bridge.py` script for you, and configure its own `mcp.json` workspace settings.

Once the AI says it's ready, you can type something like "List all the models in the current Slicer scene" in your external AI chat window and watch it orchestrate Slicer!

### 3. Downloading Slicer Skills (Knowledge Base)
To prevent your AI from hallucinating incorrect Slicer Python APIs:
1. Open the SlicerClaw module and expand **"3. AI Knowledge Base (Skills & Data)"**.
2. Select your desired skill source (e.g., `jumbojing/slicerSkill` or Local Data).
3. Click **Download & Extract** and point it to your working environment (e.g., `.opencode/skills`).
4. SlicerClaw's MCP server will now automatically search these files when the AI requests Slicer programming knowledge!

*Note: The local skill capability and MCP connection concepts take deep inspiration from the pioneering work at [pieper/slicer-skill](https://github.com/pieper/slicer-skill).*

### 4. AI Evolution Memory Bank
As the AI encounters errors and solves hard specific problems, it will automatically use specialized MCP tools to write its "lessons learned" into markdown logs. You can audit what it's thinking directly from the UI:
1. Open the SlicerClaw module and expand **"4. AI Evolution Memory Bank"**.
2. Toggle **"Enable Global Memory"**: Decide whether the AI is allowed to share and learn lessons globally across all your projects. Disable this if you want the logic strictly confined.
3. Click **"👁️ View Global Memory"** to open the global memory journal (`~/.slicerClaw/global_memory.md`), or hit **"🧹 Clear Global Memory"** to completely wipe its long-term baseline logic.
4. **Project-Specific Memory:** The AI also manages a localized `.slicer_project_memory.md` bound specifically to your current scene's directory. Easily audit or wipe it using the **"👁️ View Project Memory"** and **"🧹 Clear Project Memory"** buttons, directly tailoring the AI's persona to the unique anatomy structure of the current loaded case.

## ⚠️ Important Security Warning

**Use extreme caution when running the MCP Server and exposing it to external AI tools.**

The SlicerClaw MCP server grants any connected MCP client the ability to **execute arbitrary Python code** inside your Slicer process. This is powerful but carries significant risk:

* **Code execution:** A compromised or hallucinating AI client can run any code with the full privileges of the Slicer process, including reading and writing files (e.g., `os.remove()`), accessing the network, and modifying your system.
* **Protected Health Information (PHI):** If you are working with patient data or other confidential medical imaging information, be aware that an MCP client (and the remote AI model behind it) may send and receive data that includes PHI. Ensure you comply with your institution's data-handling policies, HIPAA, and any other applicable regulations.
* **Third-party models:** Prompts, screenshot tool responses, and scene data may be transmitted to cloud-hosted AI services (e.g., OpenAI, Claude, DeepSeek). Do not assume that data shared through the MCP connection stays local unless you use a local model.
* **Network Exposure:** Never expose port `2016` to the public internet or untrusted networks. SlicerClaw is designed strictly for local development environments (`127.0.0.1`).

**Recommendation:** We strongly recommend running Slicer and the MCP server inside a contained environment (like Docker or Virtual Machines) when testing untrusted agents, limiting the blast radius of any unintended actions and reducing the chance of exposing sensitive data.

## 🚀 Future Roadmap & TODOs

SlicerClaw is evolving fast! Here is what we plan to tackle next:
- [ ] **Sandboxed Execution:** Improve the security of the `execute_python` tool by restricting filesystem access and dangerous imports.
- [ ] **Multi-Modal AI Support:** Allow external Vision Language Models (like Claude 3.5 Sonnet or GPT-4o) to directly "see" the `screenshot` tool output inside the native Spotlight chat, not just via external MCP.
- [ ] **Context Window Optimization:** The built-in `search_slicer_knowledge` currently dumps potentially large chunks of markdown. We want to implement local vector embeddings (RAG) within Slicer to provide surgically precise AI context.
- [ ] **Task Automation Macros:** Record a series of AI actions and convert them into reusable Python macros that the user can execute later with a single click.
- [ ] **Auto-Correct Loops:** If the AI executes a python script that throws a Slicer Exception, feed the traceback automatically back into the LLM to self-heal its code.
- [x] **Long-Term Memory:** Equip the AI with persistent memory across Slicer sessions so it remembers your workflow preferences, past mistakes, and project-specific contexts.
- [x] **Self-Learning & Evolution:** Enable the AI to autonomously write new skills, generate documentation from its own successes, and save them back into the local Knowledge Base to continuously evolve its proficiency.

## 🔗 Related Projects

SlicerClaw builds upon and is inspired by a thriving ecosystem of AI integration within 3D Slicer. We highly recommend checking out these related projects:

* **[pieper/slicer-skill](https://github.com/pieper/slicer-skill)** — The foundational Claude skill for 3D Slicer that pioneered the MCP integration and local documentation indexing workflow. *SlicerClaw's MCP architecture and Skill download mechanics are directly inspired by this repository.*
* **[jumbojing/slicerSkill](https://github.com/jumbojing/slicerSkill)** — The comprehensive, cloud-searchable core AI skill fork used as the default knowledge base in SlicerClaw.
* **[mcp-slicer](https://github.com/zhaoyouj/mcp-slicer)** — A standalone MCP server for 3D Slicer by @zhaoyouj, installable via `pip`. It uses Slicer's built-in WebServer API as a bridge.
* **[SlicerDeveloperAgent](https://github.com/muratmaga/SlicerDeveloperAgent)** — A Slicer extension by Murat Maga that embeds an AI coding agent directly inside 3D Slicer using Gemini.
* **[SlicerChat: Building a Local Chatbot for 3D Slicer](https://arxiv.org/abs/2407.11987)** (Barr, 2024) — Explores integrating a locally-run LLM (Code-Llama Instruct) into 3D Slicer to assist users, investigating the effects of domain knowledge on answer quality.

## 🙏 Acknowledgements `AI`

A special thanks to the tools and agents that made this iteration of the project possible:

* **Antigravity (Google DeepMind)** — The powerful AI agent who autonomously reasoned, planned, and rewrote the SlicerClaw architecture, UI, and MCP server backend you see today.
* **OpenCode** — The brilliant IDE extension bridging the gap between developers and LLMs, making this external MCP workflow so accessible and powerful.
* **GLM-5 (Zhipu AI)** — The underlying state-of-the-art reasoning model powering the seamless natural language generation and tool execution API.
