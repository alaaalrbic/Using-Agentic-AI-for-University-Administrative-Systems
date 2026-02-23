"""
AI Assistant Tab UI
"""

import concurrent.futures
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTextEdit, QFrame, QScrollArea, QSizePolicy
)


class ChatWorker(QThread):
    finished = pyqtSignal(str)
    
    def __init__(self, client, msg: str, context: dict = None, timeout_sec: int = 30):
        super().__init__()
        self.client = client
        self.msg = msg
        self.context = context or {}
        self.timeout_sec = timeout_sec

    def run(self):
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(self.client.handle_chat, self.msg, self.context)
                # Remove timeout to allow infinite wait for AI response
                reply = fut.result()
        except Exception as e:
            reply = f"(Error: {e})"
        self.finished.emit(reply)


class ChatTab(QWidget):
    
    data_refreshed = pyqtSignal()
    
    def __init__(self, client, parent=None, get_context_callback=None):
        super().__init__(parent)
        self.client = client
        self.get_context_callback = get_context_callback
        self._init_ui()

    def _init_ui(self):
        """Initialize the UI components."""
        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(20)
        self.setLayout(main_layout)
        
        # 1. Header Section
        header_container = QWidget()
        hc_layout = QVBoxLayout(header_container)
        hc_layout.setContentsMargins(0, 0, 0, 0)
        hc_layout.setSpacing(5)
        
        lbl_title = QLabel("AI Assistant")
        lbl_title.setStyleSheet("font-size: 32px; font-weight: 800; color: #0f172a;")
        hc_layout.addWidget(lbl_title)
        
        lbl_subtitle = QLabel("Ask questions about student management, courses, and analytics")
        lbl_subtitle.setStyleSheet("font-size: 16px; color: #64748b;")
        hc_layout.addWidget(lbl_subtitle)
        
        main_layout.addWidget(header_container)
        
        # 2. Content Area (Two Columns)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(25)
        
        # --- LEFT: Chat Card ---
        self.chat_card = QFrame()
        self.chat_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
        """)
        cc_layout = QVBoxLayout(self.chat_card)
        cc_layout.setContentsMargins(20, 20, 20, 20)
        
        # Chat Header inside card
        lbl_chat_head = QLabel("Chat with AI Assistant")
        lbl_chat_head.setStyleSheet("border: none; font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 10px;")
        cc_layout.addWidget(lbl_chat_head)
        
        # Chat Display (TextEdit)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: white;
                font-size: 14px;
                color: #334155;
                line-height: 1.6;
            }
        """)
        cc_layout.addWidget(self.chat_display)
        
        # Input Area (Rounded box)
        input_container = QFrame()
        input_container.setStyleSheet("""
            QFrame {
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                background-color: white;
            }
        """)
        ic_layout = QHBoxLayout(input_container)
        ic_layout.setContentsMargins(10, 5, 10, 5)
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your message...")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                border: none;
                font-size: 14px;
                color: #333;
            }
        """)
        
        self.btn_clear = QPushButton("🗑 Clean")
        self.btn_clear.setFixedSize(90, 40)
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.setToolTip("Clear Chat")
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #64748b;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #fee2e2;
                color: #dc2626;
                border: 1px solid #fca5a5;
            }
        """)
        self.btn_clear.clicked.connect(self.clear_chat)

        self.chat_send_btn = QPushButton("Send ➤") 
        self.chat_send_btn.setFixedSize(100, 40)
        self.chat_send_btn.setCursor(Qt.PointingHandCursor)
        self.chat_send_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a237e;
                color: white;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
                border: none;
                padding-left: 5px;
            }
            QPushButton:hover { background-color: #283593; }
        """)
        
        ic_layout.addWidget(self.chat_input)
        ic_layout.addWidget(self.btn_clear)
        ic_layout.addWidget(self.chat_send_btn)
        
        cc_layout.addWidget(input_container)
        
        # Add Left Card to Content
        content_layout.addWidget(self.chat_card, 3) # Stretch factor 3 (wider)



        main_layout.addLayout(content_layout)
        
        # Signal Connections
        self.chat_send_btn.clicked.connect(self.on_chat_send)
        self.chat_input.returnPressed.connect(self.on_chat_send)
        
        # Initial System Message
        self._append_chat("system", "AI Assistant ready. You can ask me to manage courses and students, generate reports, or analyze data.")

    def on_prompt_clicked(self, text):
        self.chat_input.setText(text)
        self.chat_input.setFocus()
        self.on_chat_send()

    def clear_chat(self):
        self.chat_display.clear()
        self._append_chat("system", "Chat cleared. AI Assistant ready.")

    def _append_chat(self, role: str, text: str):
        prefix_map = {"user": "You:", "assistant": "Assistant:", "system": "System:"}
        prefix = prefix_map.get(role, "System:")
        
        # Simple HTML styling for chat messages
        color = "#1e293b" # Default dark
        if role == "system": color = "#64748b" # Gray
        if role == "user": color = "#2563eb" # Blue
        
        # Ensure block spacing and clear line starts
        # Wrapping in a <div> with margin and adding a <br>
        formatted = f"<div style='margin-top: 10px; margin-bottom: 5px; clear: both;'>"\
                    f"<b style='color: {color};'>{prefix}</b><br>"\
                    f"<span>{text}</span></div>"
        
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.End)
        self.chat_display.setTextCursor(cursor)
        
        # Insert a newline before if not empty to ensure isolation
        if not self.chat_display.document().isEmpty():
            self.chat_display.insertHtml("<br>")

        self.chat_display.insertHtml(formatted)
        self.chat_display.ensureCursorVisible()

    def on_chat_send(self):
        msg = self.chat_input.text().strip()
        if not msg:
            return
        
        # Check if API key is configured
        if hasattr(self.client, 'check_health') and not self.client.check_health():
            self._append_chat("system", "⚠️ <b>Mistral API key not configured. Please check your settings.")
            return

        self.chat_input.clear()
        self._append_chat("user", msg)
        self.chat_send_btn.setEnabled(False)
        self.chat_input.setEnabled(False)
        self._append_chat("loading", "⏳ Processing...") # Loading state - visually distinct
        
        # Build context from GUI state
        context = {}
        if self.get_context_callback:
            try:
                sem_id = self.get_context_callback()
                if sem_id:
                    context["semester_id"] = sem_id
            except Exception:
                pass
        
        self.worker = ChatWorker(self.client, msg, context)
        self.worker.finished.connect(self._on_chat_reply)
        self.worker.start()

    def _on_chat_reply(self, reply: str):
        # Remove "Processing..." if possible? Or just append.
        # Ideally we'd remove styling but simple append is fine.
        self._append_chat("assistant", reply)
        self.chat_send_btn.setEnabled(True)
        self.chat_input.setEnabled(True)
        self.data_refreshed.emit()