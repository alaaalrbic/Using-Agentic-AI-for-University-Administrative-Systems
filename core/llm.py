from __future__ import annotations
import json
import os
from typing import Any, List, Optional
from openai import OpenAI


PROVIDER_CONFIGS = {
    "mistral": {
        "base_url":  "https://api.mistral.ai/v1",
        "api_key_env": "MISTRAL_API_KEY",
        "default_model": "mistral-large-latest",
    },
    "groq": {
        "base_url":  "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "default_model": "llama-3.3-70b-versatile",
    },
    "gemini": {
        "base_url":  "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "default_model": "gemini-1.5-flash",
    },
    "openrouter": {
        "base_url":  "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "default_model": "mistralai/mistral-large",
    },
    "ollama": {
        "base_url":  "http://localhost:11434/v1",
        "api_key_env": "OLLAMA_API_KEY",
        "default_model": "qwen2.5:3b",
    },
}
DEFAULT_PROVIDER = "mistral"
DEFAULT_MODEL    = "mistral-large-latest"
TOOLS = [
    {"type": "function", "function": {
        "name": "list_students",
        "description": "Retrieve all registered students with their numeric IDs and full names. Use this when you need to find a student ID from a name, or when listing all students.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }},
    {"type": "function", "function": {
        "name": "search_students",
        "description": "Search students by name (full or partial). ALWAYS call this first when the user refers to a student by name and you need their numeric ID for enroll/drop/grades operations.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Student name or partial name"}
        }, "required": ["query"]}
    }},
    {"type": "function", "function": {
        "name": "list_courses",
        "description": "Get all courses with their codes, titles, instructors, and available seats.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }},
    {"type": "function", "function": {
        "name": "list_semesters",
        "description": "Get all semesters with their IDs, names, states (OPEN/CLOSED), and which is active.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }},
    {"type": "function", "function": {
        "name": "get_active_semester",
        "description": "Get the currently active semester details.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }},
    {"type": "function", "function": {
        "name": "get_student_enrollments",
        "description": "Get all courses a specific student is enrolled in, with their midterm, final, and total grades. Requires numeric student_id — use search_students first if you have a name.",
        "parameters": {"type": "object", "properties": {
            "student_id": {"type": "integer", "description": "Numeric student ID"},
            "semester_id": {"type": "integer", "description": "Semester ID (optional, defaults to active)"}
        }, "required": ["student_id"]}
    }},
    {"type": "function", "function": {
        "name": "enroll",
        "description": "Enroll a student in a course. Requires numeric student_id. If you only have a student name, call search_students first to get the ID.",
        "parameters": {"type": "object", "properties": {
            "student_id": {"type": "integer", "description": "Numeric student ID — never a name string"},
            "course_code": {"type": "string", "description": "Course code e.g. CS101"},
            "semester_id": {"type": "integer", "description": "Optional semester ID"}
        }, "required": ["student_id", "course_code"]}
    }},
    {"type": "function", "function": {
        "name": "drop",
        "description": "Remove a student from a course. Requires numeric student_id. If you only have a name, call search_students first.",
        "parameters": {"type": "object", "properties": {
            "student_id": {"type": "integer", "description": "Numeric student ID — never a name string"},
            "course_code": {"type": "string", "description": "Course code e.g. CS101"},
            "semester_id": {"type": "integer", "description": "Optional semester ID"}
        }, "required": ["student_id", "course_code"]}
    }},
    {"type": "function", "function": {
        "name": "add_student",
        "description": "Register a new student in the university system.",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "description": "Full name of the student"}
        }, "required": ["name"]}
    }},
    {"type": "function", "function": {
        "name": "add_course",
        "description": "Create a new course. Requires code, title, instructor name, and max seats.",
        "parameters": {"type": "object", "properties": {
            "code": {"type": "string", "description": "Course code e.g. CS301"},
            "title": {"type": "string", "description": "Full course title"},
            "instructor": {"type": "string", "description": "Instructor full name"},
            "max_seats": {"type": "integer", "description": "Maximum number of students allowed"}
        }, "required": ["code", "title", "instructor", "max_seats"]}
    }},
    {"type": "function", "function": {
        "name": "set_course_grade",
        "description": "Set or update a student's midterm (0-40) and/or final (0-60) grade in a course. Requires numeric student_id — search_students first if needed.",
        "parameters": {"type": "object", "properties": {
            "student_id": {"type": "integer", "description": "Numeric student ID"},
            "course_code": {"type": "string", "description": "Course code"},
            "midterm": {"type": "number", "description": "Midterm grade 0-40 (optional)"},
            "final": {"type": "number", "description": "Final grade 0-60 (optional)"},
            "semester_id": {"type": "integer", "description": "Optional semester ID"}
        }, "required": ["student_id", "course_code"]}
    }},
    {"type": "function", "function": {
        "name": "get_semester_average",
        "description": "Calculate a student's average grade across all courses in a semester.",
        "parameters": {"type": "object", "properties": {
            "student_id": {"type": "integer", "description": "Numeric student ID"},
            "semester_id": {"type": "integer", "description": "Optional semester ID"}
        }, "required": ["student_id"]}
    }},
    {"type": "function", "function": {
        "name": "get_semester_summary_data",
        "description": "Get a full performance report for ALL students in a semester. Use this for ranking, comparing, or analyzing all students.",
        "parameters": {"type": "object", "properties": {
            "semester_id": {"type": "integer", "description": "The semester ID"}
        }, "required": ["semester_id"]}
    }},
    {"type": "function", "function": {
        "name": "add_semester",
        "description": "Create a new academic semester.",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "description": "Semester name e.g. Fall 2025"}
        }, "required": ["name"]}
    }},
    {"type": "function", "function": {
        "name": "set_active_semester",
        "description": "Set a semester as the currently active one.",
        "parameters": {"type": "object", "properties": {
            "semester_id": {"type": "integer", "description": "ID of the semester to activate"}
        }, "required": ["semester_id"]}
    }},
    {"type": "function", "function": {
        "name": "close_semester",
        "description": "Close a semester to prevent further enrollments.",
        "parameters": {"type": "object", "properties": {
            "semester_id": {"type": "integer", "description": "ID of the semester to close"}
        }, "required": ["semester_id"]}
    }},
]

SYSTEM_PROMPT = """You are an intelligent autonomous AI agent managing a university administration system.
You have full access to the university database through tools, and you reason step by step before acting.

━━━ LANGUAGE RULES — HIGHEST PRIORITY ━━━

RESPONDING — PER MESSAGE RULE:
- Evaluate the language of the CURRENT message ONLY — ignore previous messages language.
- Look at the user's LATEST message right now:
  * If it contains Arabic letters (ا ب ت ث ...) → respond ENTIRELY in Arabic.
  * If it is written in English letters only → respond ENTIRELY in English.
- This rule applies to EVERY single message independently — the conversation history does NOT affect language choice.
- Even if the last 10 messages were in Arabic, if the current message is in English → respond in English.
- Even if the last 10 messages were in English, if the current message is in Arabic → respond in Arabic.
- Never mix Arabic and English in the same response.

DATA STORAGE — CRITICAL:
- ALL data saved to the database must ALWAYS be in English, regardless of what language the user typed.
- If the user gives a student name in Arabic (e.g. "محمد علي") → translate it to English (e.g. "Mohammed Ali") before calling add_student.
- If the user gives a course title in Arabic → translate it to English before calling add_course.
- If the user gives an instructor name in Arabic → translate it to English before calling add_course.
- If the user gives a semester name in Arabic (e.g. "الخريف 2026") → translate it to English (e.g. "Fall 2026") before calling add_semester.
- Course codes (like CS101) stay as-is — never translate codes.
- After saving, confirm to the user in their language what was saved.

SEARCHING:
- If the user searches for a student by Arabic name → translate the name to English first, then call search_students with the English version.
- Example: "ابحث عن محمد" → search_students("Mohammed")

━━━ REASONING RULES ━━━

1. THINK BEFORE ACTING:
   Reason about what data you need and in what order before calling any tool.

2. ALWAYS RESOLVE NAMES TO IDs:
   If the user gives a student name (not a number), ALWAYS call search_students first to get the numeric ID.
   NEVER pass a name string as student_id — it must be an integer.

3. HANDLE MISSING INFO IN THE USER'S LANGUAGE:
   If the request is incomplete, tell them warmly in Arabic (or English) exactly what is missing.
   Arabic examples:
   - "يسعدني إضافة المقرر، لكن أحتاج اسم المحاضر وعدد المقاعد."
   - "وجدت 3 طلاب باسم أحمد — أيهم تقصد؟ أحمد سالم (رقم 101)، أحمد علي (رقم 205)."

4. CHAIN TOOLS INTELLIGENTLY:
   Call multiple tools in sequence without asking permission.

5. ANALYZE DATA YOURSELF:
   For ranking, filtering, averages — fetch data then reason through it to give a meaningful answer.

6. UNDERSTAND INTENT IN ANY LANGUAGE:
   "ما درجة سارة في النصفي؟" → search Sara (translate if needed) → get enrollments → answer in Arabic
   "رتب الطلاب حسب الدرجة" → get summary → sort → present in Arabic
   "هل نجح أحمد؟" → search Ahmed → get average → reason if ≥ 50 → answer in Arabic

━━━ RESPONSE STYLE ━━━
- Warm, conversational sentences in the user's language
- No bullet points, no markdown, no bold, no headers
- Be specific with real numbers and names from the database
- If something failed, explain why in the user's language

━━━ GRADING SCALE ━━━
- Midterm: 0–40  |  Final: 0–60  |  Total: 0–100  |  Pass: ≥ 50
- النصفي: 0–40  |  النهائي: 0–60  |  المجموع: 0–100  |  النجاح: 50 فأكثر"""


# ---------------------------------------------------------------------------
# LLM CLIENT
# ---------------------------------------------------------------------------
class LLMUniversity:
    def __init__(self, mcp_bridge, model_name: Optional[str] = None,
                 api_key: Optional[str] = None, provider: Optional[str] = None, **kwargs):
        self.mcp = mcp_bridge
        self._history: List[dict] = []
        self._current_context: dict = {}

        # Load .env
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        # ── CHANGED: resolve provider and base_url ────────────────────────
        self.provider = provider or DEFAULT_PROVIDER
        cfg = PROVIDER_CONFIGS.get(self.provider, PROVIDER_CONFIGS["mistral"])

        self.model_name = model_name or DEFAULT_MODEL or cfg["default_model"]
        self.api_key    = api_key or os.getenv(cfg["api_key_env"], "ollama")
        self.base_url   = cfg["base_url"]

        # ── CHANGED: one OpenAI client instead of Mistral client ──────────
        self._client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        # CHANGED: OpenAI(base_url=...) instead of Mistral(api_key=...)
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client

    def check_health(self) -> bool:
        if self.provider == "ollama":
            return True
        return bool(self.api_key)

    def handle_chat(self, msg: str, context: dict = None) -> str:
        self._current_context = context or {}
        if not msg or not msg.strip():
            return "Please enter a message."
        if not self.check_health():
            return f"No API key found. Please set your {PROVIDER_CONFIGS.get(self.provider, {}).get('api_key_env','API_KEY')} in .env"

        def is_arabic(text):
            return any('\u0600' <= c <= '\u06FF' for c in text)

        use_arabic = is_arabic(msg)

        try:
            return self._run_agent(msg)
        except Exception as e:
            error = str(e)
            if "401" in error or "unauthorized" in error.lower():
                return "لا أستطيع الاتصال — مفتاح API يبدو غير صالح." if use_arabic else "Unable to connect — the API key appears invalid."
            if "429" in error or "rate_limit" in error.lower() or "too many" in error.lower():
                return "وصلت إلى الحد الأقصى للطلبات. يرجى الانتظار قليلاً." if use_arabic else "Rate limit reached. Please wait a moment and try again."
            if "503" in error or "connection" in error.lower():
                return "لا أستطيع الوصول إلى الخادم الآن." if use_arabic else "Cannot reach the server right now. Check your internet connection."
            return f"حدث خطأ: {e}" if use_arabic else f"Something went wrong: {e}"


    # ------------------------------------------------------------------
    # AGENTIC LOOP
    # ------------------------------------------------------------------
    def _run_agent(self, user_message: str, max_steps: int = 20) -> str:
        client = self._get_client()

        def is_arabic(text):
            return any('\u0600' <= c <= '\u06FF' for c in text)

        lang_hint = "[CURRENT MESSAGE LANGUAGE: ARABIC — You MUST respond in Arabic]" \
                    if is_arabic(user_message) else \
                    "[CURRENT MESSAGE LANGUAGE: ENGLISH — You MUST respond in English]"

        context_note = ""
        if self._current_context.get("semester_id"):
            context_note = f"\n[System context: Active semester ID = {self._current_context['semester_id']}]"

        history_window = self._history[-10:] if self._history else []
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history_window,
            {"role": "user", "content": f"{lang_hint}\n{user_message}{context_note}"},
        ]
        self._history.append({"role": "user", "content": f"{lang_hint}\n{user_message}{context_note}"})

        for step in range(max_steps):

            # ── CHANGED: client.chat.completions.create() ─────────────────
            # Old Mistral:  client.chat.complete(model=..., messages=..., tools=...)
            # New OpenAI:   client.chat.completions.create(model=..., messages=..., tools=...)
            # Everything else (tools format, tool_choice, temperature) is identical.
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0,
                max_tokens=2048,
            )

            choice    = response.choices[0]
            msg_obj   = choice.message
            # ── CHANGED: tool_calls access is the same ────────────────────
            tool_calls = msg_obj.tool_calls or []
            content    = msg_obj.content or ""

            assistant_msg = {"role": "assistant", "content": content}
            if tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            # ── CHANGED: arguments is already a string in openai ──
                            "arguments": tc.function.arguments
                        }
                    } for tc in tool_calls
                ]
            messages.append(assistant_msg)

            if not tool_calls:
                final_reply = content.strip() or "I've completed the task."
                self._history.append({"role": "assistant", "content": final_reply})
                if len(self._history) > 20:
                    self._history = self._history[-20:]
                return final_reply

            for tc in tool_calls:
                tool_name = tc.function.name
                try:
                    args_raw  = tc.function.arguments
                    tool_args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                except Exception:
                    tool_args = {}

                result = self._execute_tool(tool_name, tool_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

        return "I wasn't able to complete this request within the reasoning limit. Please try rephrasing your question."

    # ------------------------------------------------------------------
    # Tool execution  (unchanged)
    # ------------------------------------------------------------------
    def _execute_tool(self, tool_name: str, args: dict) -> str:
        try:
            args   = self._auto_resolve_semester(tool_name, args)
            raw    = self.mcp.call_tool(tool_name, args)
            result = self._mcp_to_python(raw)
            if result is None:
                return json.dumps({"status": "empty", "message": "No data returned."})
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def _auto_resolve_semester(self, tool_name: str, args: dict) -> dict:
        needs_sem = {"enroll", "drop", "get_student_enrollments",
                     "set_course_grade", "get_semester_average",
                     "get_semester_summary_data", "close_semester"}
        if tool_name not in needs_sem or args.get("semester_id"):
            return args
        gui_sem = self._current_context.get("semester_id")
        if gui_sem:
            args = dict(args)
            args["semester_id"] = int(gui_sem)
        return args

    # ------------------------------------------------------------------
    # MCP result parser  (unchanged)
    # ------------------------------------------------------------------
    def _mcp_to_python(self, result: Any) -> Any:
        if isinstance(result, (dict, list, str)):
            return result
        content = getattr(result, "content", None)
        if not content:
            return None
        parsed = []
        for item in content:
            txt = getattr(item, "text", None)
            if not isinstance(txt, str) or not txt.strip():
                continue
            try:
                parsed.append(json.loads(txt.strip()))
            except Exception:
                parsed.append(txt.strip())
        if not parsed:
            return None
        return parsed[0] if len(parsed) == 1 else parsed

