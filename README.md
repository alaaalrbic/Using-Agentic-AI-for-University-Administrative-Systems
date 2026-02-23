# 🎓 University AI Management System

A modern desktop application for managing university students, courses, enrollments, and semesters — powered by a conversational **AI Assistant** built on the **Mistral AI API** and the **Model Context Protocol (MCP)**.

The AI assistant supports **both English and Arabic** and can perform all management operations through natural language commands.

---

## ✨ Features

### 🤖 AI Chat Assistant
- Full natural language interface in **English and Arabic** (auto-detected per message)
- Agentic reasoning loop — the AI chains multiple database tools autonomously to complete complex requests
- Supports all CRUD operations: add students, enroll/drop courses, set grades, generate reports
- Context-aware: automatically uses the currently selected semester

### 👨‍🎓 Student Management
- Add, search, and list students
- View per-student enrollment history and grades
- Calculate semester averages and pass/fail status

### 📚 Course Management
- Add courses with instructor and seat capacity
- Track available seats in real time
- Enroll and drop students with validation

### 📅 Semester Management
- Create and manage academic semesters
- Open/close semester lifecycle control
- Full semester performance summaries and student rankings

### 🗄️ Database
- SQLite backend with mixin-based modular architecture
- Strict data integrity enforced at the database layer
- All data stored in English regardless of input language

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Desktop UI | Python / PyQt5 (QSS Styling) |
| AI / LLM | Mistral AI API (`mistral-large-latest`) |
| AI Middleware | FastMCP (Model Context Protocol) |
| Database | SQLite3 |
| Environment | python-dotenv |

---

## 📋 Prerequisites

- **Python 3.9 or higher**
- **pip** (Python package manager)
- A valid **Mistral AI API key** — get one at [console.mistral.ai](https://console.mistral.ai/)

---

## 📦 Installation

### 1. Clone or Download the Project

```bash
git clone <your-repo-url>
cd "MCPverEnglish and arabicV1"
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Your API Key

Create a `.env` file in the project root by copying the example:

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder with your real Mistral API key:

```env
MISTRAL_API_KEY=your_actual_mistral_api_key_here
```

> ⚠️ **Important:** Never commit your `.env` file to version control. Add it to `.gitignore`.

---

## 🚀 Running the Application

```bash
python main.py
```

The application will:
1. Launch the PyQt5 desktop window
2. Automatically start the MCP server in a background thread
3. Connect to the Mistral AI API using your key from `.env`
4. Load or create the `university.db` SQLite database

---

## 🗂 Project Structure

```
MCPverEnglish and arabicV1/
│
├── main.py                   # Application entry point
├── mcp_server.py             # MCP Server — exposes DB tools to the AI
├── db_manager.py             # DatabaseManager combining all mixins
├── university.db             # SQLite database (auto-created)
│
├── .env                      # Your local API key config (not in version control)
├── .env.example              # Template for environment variables
├── requirements.txt          # Python dependencies
│
├── core/
│   ├── llm_client.py         # Mistral AI client — agentic loop & tool execution
│   ├── mcp_bridge.py         # MCP Client — async bridge between GUI and MCP Server
│   ├── semester_rules.py     # Business rules for semester operations
│   └── db/
│       ├── base.py           # Base SQLite connection and utilities
│       ├── students.py       # Student CRUD mixin
│       ├── courses.py        # Course CRUD mixin
│       ├── semesters.py      # Semester lifecycle mixin
│       └── enrollments.py    # Enrollment & grading mixin
│
├── UI/
│   ├── university_gui.py     # Main window with sidebar navigation
│   ├── ui_chat_tab.py        # AI Chat tab — input, display, worker thread
│   ├── ui_courses_tab.py     # Students & Courses management tab
│   └── dialogs.py            # Reusable dialog windows
│
└── utils/
    └── utils.py              # Shared helper functions
```

---

## 🔗 MCP Architecture

This project implements the [Model Context Protocol (MCP)](https://modelcontextprotocol.io) — an open standard for connecting AI models to external tools and data sources.

```
┌─────────────────────────────────────────────────────────┐
│                     PyQt5 Desktop UI                    │
│                                                         │
│   ┌──────────────┐         ┌────────────────────────┐   │
│   │  Chat Tab    │────────▶│   LLMUniversityClient  │   │
│   │ (ui_chat_tab)│         │    (Mistral AI API)    │   │
│   └──────────────┘         └───────────┬────────────┘   │
│                                        │                │
│   ┌──────────────────────────────────┐ │                │
│   │         MCPBridge                │◀┘                │
│   │  (Async stdio client thread)     │                  │
│   └─────────────────┬────────────────┘                  │
└─────────────────────│───────────────────────────────────┘
                      │ stdio (JSON-RPC 2.0)
        ┌─────────────▼──────────────┐
        │       mcp_server.py        │
        │   (FastMCP Tool Server)    │
        └─────────────┬──────────────┘
                      │
        ┌─────────────▼──────────────┐
        │      DatabaseManager       │
        │   (SQLite via mixins)      │
        └────────────────────────────┘
```

### How It Works

- **MCP Server** (`mcp_server.py`) registers all database operations as callable tools (e.g. `list_students`, `enroll`, `set_course_grade`)
- **MCPBridge** (`core/mcp_bridge.py`) runs a persistent async event loop in a background thread, communicating with the server over stdio transport
- **LLMUniversityClient** (`core/llm_client.py`) sends user messages to Mistral, receives tool-call requests, executes them via the bridge, and loops until the AI produces a final answer

---

## 💬 AI Assistant Usage

### English Examples

```
"Show me all students"
"Enroll Ahmed in CS101"
"What is Sara's grade in the midterm?"
"Add a new course: Data Structures, instructor John Smith, 30 seats"
"Rank all students by total grade this semester"
"Did Mohammed pass this semester?"
```

### Arabic Examples

```
"اعرض جميع الطلاب"
"سجّل أحمد في مادة CS101"
"ما درجة سارة في النصفي؟"
"أضف مقرراً جديداً: هياكل البيانات، المحاضر: جون سميث، 30 مقعداً"
"رتب الطلاب حسب المجموع"
"هل نجح محمد هذا الفصل؟"
```

> The AI auto-detects language per message. Arabic inputs are automatically translated to English before being saved to the database, and responses are returned in the user's language.

---

## 📊 Grading System

| Component | Range | Notes |
|---|---|---|
| Midterm | 0 – 40 | النصفي |
| Final | 0 – 60 | النهائي |
| Total | 0 – 100 | المجموع |
| Pass Threshold | ≥ 50 | النجاح |

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MISTRAL_API_KEY` | *(required)* | Your Mistral AI API key |
| `MCP_DB_NAME` | `university.db` | Custom SQLite database filename |

---

## 🧪 Running Tests

```bash
python test_mcp_server.py
```

---

## 🔒 Security Notes

- API keys are loaded exclusively from the `.env` file or system environment — never hardcoded in source
- The `.env` file should always be listed in `.gitignore`
- If a key is accidentally exposed in version control, regenerate it immediately at [console.mistral.ai](https://console.mistral.ai/)

---

## 🐛 Troubleshooting

**"Mistral API key not configured"**
You haven't created a `.env` file, or the `MISTRAL_API_KEY` variable is missing. See the [Installation](#-installation) section.

**"The Mistral API key appears to be invalid"**
Your key may be expired or incorrect. Verify it at [console.mistral.ai](https://console.mistral.ai/).

**"I can't reach the Mistral servers"**
Check your internet connection. Mistral API requires outbound HTTPS access.

**Database errors on startup**
Delete `university.db` to let the app recreate it from scratch (this will erase all data).

---

## 📄 License

This project was created as part of the University Management Modernization initiative.

---

*Built with ❤️ using Python, PyQt5, Mistral AI, and the Model Context Protocol.*
