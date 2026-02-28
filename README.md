# slicerClaw (Slicer Native Agent)

A revolutionary,  lightning-fast AI assistant natively integrated into 3D Slicer.
Experience a seamless, "Spotlight"-style floating command bar that allows you to control 3D Slicer and query your scene using natural language without writing a single line of code!

## Features

- **Spotlight Interface:** No more clunky, docked panels. Just press `Ctrl+I` (Cmd+I) from anywhere in Slicer to summon a beautiful, translucent floating bar.
- **Direct LLM Integration:** Connects directly to OpenAI-compatible APIs (e.g. Aliyun Bailian, Zhipu GLM, Antigravity, DeepSeek) without heavy local middle layers.
- **Function Calling (Tools):** The AI has direct access to Slicer's Python environment. It can list nodes, get properties, take screenshots, and execute arbitrary python code natively.
- **Persistent Settings:** Safely stores your API keys and model configurations in Slicer's native application settings.

## Installation

1. Clone or download this repository to your local machine:
   ```bash
   git clone https://github.com/YourUsername/slicerClaw.git
   ```
2. Open 3D Slicer.
3. Go to **Edit -> Application Settings -> Modules**.
4. Add the `slicerClaw` directory to your Additional Module Paths.
5. Restart 3D Slicer.

## Usage

1. **First-time setup:** 
   - Open the **slicerClaw** module from the modules menu.
   - Enter your `API Base URL` (e.g., `https://coding.dashscope.aliyuncs.com/v1/chat/completions`)
   - Enter your `API Key` (e.g., `sk-sp-...`)
   - Enter your preferred `Model` (e.g., `glm-5` or `glm-4-plus`)
   - Click **Save Settings**.

2. **Summoning the Copilot:**
   - Press **`Ctrl+I`** anywhere in Slicer, or click the 🧠 button on your top toolbar.
   - Type your request in natural language: *"Please list all volume nodes in the scene"* or *"Take a screenshot."*
   - Press **Enter**. The UI will vanish, and the AI will execute your request in the background, printing the results in the Python Console.

Enjoy the extreme power of LLM Agents integrated right into your 3D medical imaging workflow!
