<p align="center">
  <img src="banner.png" alt="Digital Dave Banner" width="100%"/>
</p>

<h1 align="center">🤖 Digital Dave — AMD Edge AI Copilot</h1>

<p align="center">
  <b>A fully hybrid, voice-activated AI assistant with offline-first intelligence, real-time system monitoring, and cloud-powered autonomous code agents.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white" />
  <img src="https://img.shields.io/badge/Ollama-Local_AI-4B32C3?logo=meta&logoColor=white" />
  <img src="https://img.shields.io/badge/Groq-Cloud_Agent-FF6B35?logo=lightning&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-REST_API-000000?logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green" />
</p>

---

## ⚡ What is Digital Dave?

**Digital Dave** is a desktop AI copilot built for **Windows** that combines voice control, local AI inference, real-time hardware telemetry, and cloud-powered autonomous agents into a single unified interface. It operates in three distinct intelligence tiers:

| Tier | Mode | Engine | Speed |
|------|------|--------|-------|
| 🟢 **Offline** | Default | Local commands + Ollama `phi` | Instant |
| 🔵 **Deep Research** | On-demand | Wolfram Alpha + Wikipedia → Ollama | ~10s |
| 🟣 **Developer Mode** | On-demand | Groq `llama3-70b` via smolagents | ~5s |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────┐
│                  React Dashboard                  │
│         (Voice + Text + System Monitor)           │
└────────────────────┬─────────────────────────────┘
                     │ HTTP (axios)
┌────────────────────▼─────────────────────────────┐
│               Flask API Server                    │
│       /chat  /listen  /metrics  /diagnose         │
└────────────────────┬─────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────┐
│           Digital_Assistant.py                     │
│                                                    │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │  Offline     │  │ Deep Research│  │Developer │ │
│  │  Commands    │  │ Wolfram+Wiki │  │  Mode    │ │
│  │  (if/elif)   │  │  + Ollama    │  │ (Groq)  │ │
│  └─────────────┘  └──────────────┘  └──────────┘ │
└──────────────────────────────────────────────────┘
```

---

## 🚀 Key Features

### 🎙️ Voice & Text Hybrid Input
- **Voice-activated** — Just speak naturally, Dave listens and responds.
- **Text input** — Type commands directly in the React chat interface.
- **Seamless switching** — Say *"activate text"* or *"deactivate text"* to toggle modes.

### 🧠 Local AI Inference (Offline-First)
- Powered by **Ollama** running Microsoft's `phi` model locally.
- **Zero internet dependency** for standard operations.
- Sentiment analysis, screen summarization, and Q&A all run on-device.
- Unrecognized commands automatically routed to the local AI for intelligent responses.

### 🔬 Deep Research Mode
- Say **"start deep research"** to activate.
- Cross-references **Wolfram Alpha** (computational) + **Wikipedia** (factual) data.
- Feeds combined context into the local Ollama model for the best synthesized answer.
- Say **"stop deep research"** to return to fast, direct answers.

### 🤖 Developer Mode (Cloud Agent)
- Say **"activate developer mode"** to switch.
- Spins up an autonomous **smolagents CodeAgent** powered by **Groq's llama3-70b-8192**.
- Capable of writing, analyzing, and executing complex code tasks.
- Say **"deactivate developer mode"** to return to offline operations.

### 📊 Real-Time System Monitoring
- **AMD Edge AI Dashboard** — Say **"view system analytics"** to open.
- Live metrics: CPU load, RAM usage, GPU utilization.
- **Emergency Compute State** triggered when CPU > 85% or RAM > 80%.
- AI-powered optimization advice during system stress events.
- Say **"close system analytics"** to dismiss.

### 🖥️ Screen Intelligence
- **OCR-powered screen reading** — Say *"summarize screen"* or *"what's on screen"*.
- Captures your display, extracts text via Tesseract OCR.
- Summarizes content using the local Phi model (fully offline).

### 😊 Emotional Intelligence
- Say *"I feel tired"* or *"I'm feeling anxious"* — Dave detects your mood.
- Responds with empathetic, mood-appropriate reactions.
- Sentiment analysis powered entirely by local AI.

### 🌐 Web & App Control
- Open websites: *"open YouTube"*, *"open GitHub"*, *"open StackOverflow"*
- Search Google: *"search for machine learning"*
- Play YouTube content: *"play something on YouTube"*
- Control YouTube playback: *"pause"*, *"play"*, *"skip"*, *"mute"*
- Smart web button clicking via OCR

### 🛠️ Productivity Tools
- **Alarm system** — *"set alarm"* with natural language time input
- **Schedule manager** — *"set my schedule"* / *"show my schedule"*
- **Internet speed test** — *"run speed test"*
- **System controls** — *"shutdown"*, *"lock"*, open Task Manager, Device Manager
- **App launcher** — Open Notepad, Camera, Calculator, File Explorer, VS Code, and more

### 🎮 Built-in Entertainment
- **Flappy Bird** — *"play flappy bird"*
- **Car Game** — *"open car game"*
- **Dino Game** — *"open dino game"*
- **Drawing App** — *"open drawing app"*
- **Notes App** — *"open notes app"*
- **Password Generator** — *"open password generator"*
- **GitHub Profiler** — *"open github profiler"*

### 📰 Information Services
- **News** — *"give me news"* fetches top headlines
- **Weather** — *"weather today"*
- **Time** — *"what's the time"*
- **IP Address** — *"what is my IP"*
- **Wikipedia** — *"tell me about [topic]"*

---

## 🛡️ Safety Guardrails

Emergency exit commands are **always evaluated first**, regardless of active mode:

```
"stop" | "abort" | "shut down" | "bye" | "exit dave"
```

These will immediately terminate Digital Dave from any state — normal, deep research, or developer mode.

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, Vite, Framer Motion, Lucide Icons |
| **Backend** | Python 3.13, Flask, Flask-CORS |
| **Local AI** | Ollama (Microsoft Phi), Tesseract OCR |
| **Cloud AI** | Groq API (Llama3-70b), smolagents (HuggingFace) |
| **Monitoring** | psutil, custom SystemDashboard component |
| **Voice** | SpeechRecognition, pyttsx3 |
| **Knowledge** | Wolfram Alpha API, Wikipedia API |
| **Automation** | pyautogui, pynput, desktop_use |

---

## ⚙️ Installation

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **Ollama** installed and running ([ollama.com](https://ollama.com))
- **Tesseract OCR** installed at `C:\Program Files\Tesseract-OCR\`

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/Kine-main.git
cd Kine-main
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
pip install smolagents litellm flask flask-cors psutil
```

### 3. Pull the Local AI Model
```bash
ollama pull phi
```

### 4. Install Frontend Dependencies
```bash
cd assistant-ui
npm install
```

### 5. Set Environment Variables
```bash
# Windows PowerShell
$env:GROQ_API_KEY = "your_groq_api_key_here"
```

---

## ▶️ Running Digital Dave

Open **three terminals**:

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start the Flask backend
python server.py

# Terminal 3: Start the React frontend
cd assistant-ui
npm run dev
```

Then open **http://localhost:5174** in your browser.

---

## 🗣️ Quick Command Reference

| Command | Action |
|---------|--------|
| *"activate developer mode"* | Switch to cloud-powered CodeAgent |
| *"deactivate developer mode"* | Return to offline mode |
| *"start deep research"* | Enable Wolfram + Wikipedia + AI synthesis |
| *"stop deep research"* | Return to fast direct answers |
| *"view system analytics"* | Open real-time hardware dashboard |
| *"close system analytics"* | Hide the dashboard |
| *"summarize screen"* | OCR + AI summary of your display |
| *"activate ask me anything"* | Direct chat with local AI |
| *"set alarm"* | Set a voice-activated alarm |
| *"run speed test"* | Test your internet speed |
| *"play flappy bird"* | Launch the built-in game |

---

## 📁 Project Structure

```
Kine-main/
├── Digital_Assistant.py    # Core assistant logic (1100+ lines)
├── server.py               # Flask REST API server
├── system_monitor.py       # Real-time CPU/RAM/GPU monitoring
├── gui.py / gui1.py / gui2.py  # Legacy GUI interfaces
├── requirements.txt        # Python dependencies
├── banner.png              # Project banner
├── notification.wav        # Alert sound
├── assistant-ui/           # React frontend (Vite)
│   ├── src/
│   │   ├── App.jsx         # Main chat interface
│   │   ├── SystemDashboard.jsx  # Hardware metrics panel
│   │   ├── index.css       # Global styles
│   │   └── SystemDashboard.css  # Dashboard styles
│   └── package.json
├── desktop_use/            # Desktop automation library
├── Websites/               # Built-in web apps (games, tools)
└── flappy_Bird/            # Flappy Bird game
```

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

---

## 📄 License

This project is licensed under the **MIT License**.

---

<p align="center">
  Built with ❤️ by <b>Rishabh Sahni</b>
</p>
