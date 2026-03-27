import os
from datetime import datetime
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont, QColor
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QStackedWidget, QFrame, QSizePolicy
)

from core.mcp_client import MCPClient
from core.llm import LLMUniversity
from UI.ui_courses_tab import StudentsPage

from UI.ui_chat_tab import ChatTab


class NavigationButton(QPushButton):
    """Custom button for the sidebar."""
    def __init__(self, text, icon_char, parent=None):
        super().__init__(parent)
        self.label_text = text
        self.icon_char = icon_char
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setFixedHeight(50)
        self.setCursor(Qt.PointingHandCursor)
        self.set_collapsed(False) # Start expanded

    def set_collapsed(self, collapsed):
        if collapsed:
            self.setText(self.icon_char)
            self.setToolTip(self.label_text)
            self.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #ecf0f1;
                    border: none;
                    outline: none;
                    font-size: 20px;
                    border-left: 3px solid transparent;
                }
                QPushButton:hover { background-color: #34495e; color: white; }
                QPushButton:checked {
                    background-color: #34495e;
                    color: #3498db;
                    border-left: 3px solid #3498db;
                }
            """)
        else:
            self.setText(f"  {self.icon_char}    {self.label_text}")
            self.setToolTip("")
            self.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #ecf0f1;
                    text-align: left;
                    padding-left: 20px;
                    border: none;
                    outline: none;
                    font-size: 15px;
                    font-weight: 500;
                    border-left: 5px solid transparent;
                }
                QPushButton:hover { background-color: #34495e; color: white; }
                QPushButton:checked {
                    background-color: #34495e;
                    color: #3498db;
                    font-weight: bold;
                    border-left: 5px solid #3498db;
                }
            """)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("University System")
        self.resize(1280, 800) # Suitable default size for laptops

        self._setup_styles()
        self._init_mcp()
        self._data_dirty = True  # Tracks whether data needs refresh on tab switch
        
        # Main Layout container
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        
        self.layout = QHBoxLayout(self.main_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # 1. Sidebar
        self._setup_sidebar()

        # 2. Content Area Container
        self.content_container = QWidget()
        self.cc_layout = QVBoxLayout(self.content_container)
        self.cc_layout.setContentsMargins(0, 0, 0, 0)
        self.cc_layout.setSpacing(0)
        
        # Admin Header (Matches "University Administration" in screenshot)
        admin_header = QFrame()
        admin_header.setFixedHeight(80)
        admin_header.setStyleSheet("background-color: white; border-bottom: 1px solid #e0e6ed; padding-left: 30px;")
        ah_layout = QHBoxLayout(admin_header)
        ah_lbl = QLabel("University Administration")
        ah_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #1a237e;")
        ah_layout.addWidget(ah_lbl)
        ah_layout.addStretch()
        
        self.cc_layout.addWidget(admin_header)

        # 3. Pages (StackedWidget)
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet("background-color: #f4f7f6;") # Light Gray Content
        self.cc_layout.addWidget(self.content_area)
        
        self.layout.addWidget(self.content_container)

        # 4. Pages Initialization
        self._setup_pages()
        
        # Select first tab
        self.nav_btns[0].click()
        self.showMaximized()

    def closeEvent(self, event):
        """Cleanup resources before closing."""
        if hasattr(self, 'mcp'):
            self.mcp.cleanup()
        super().closeEvent(event)

    def _setup_styles(self):
        """Setup a MODERN application stylesheet."""
        self.setStyleSheet("""
            /* Global Reset */
            QWidget {
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                font-size: 14px;
                color: #333333;
            }
            QMainWindow { background-color: #f4f7f6; } /* Very light soothing gray/green tint */
            
            /* Buttons (Modern Flat) */
            QPushButton {
                background-color: #007bff; /* Vibrant Blue */
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #0069d9; }
            QPushButton:pressed { background-color: #0056b3; }
            
            QPushButton#danger {
                background-color: #dc3545; /* Modern Red */
            }
            QPushButton#danger:hover { background-color: #c82333; }
            
            /* Tables (Clean, No Grid) */
            QTableWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                gridline-color: transparent; /* No ugly grid lines */
                selection-background-color: #e3f2fd;
                selection-color: #1976d2;
                outline: 0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: white;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #007bff;
                font-weight: bold;
                color: #555;
                text-transform: uppercase;
                font-size: 12px;
            }
            
            /* Inputs (Modern) */
            QLineEdit, QComboBox, QSpinBox {
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #80bdff;
            }
            
            /* Scrollbars (Subtle) */
            QScrollBar:vertical {
                border: none;
                background: #f1f1f1;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover { background: #a8a8a8; }

            /* ScrollArea (Transparent for Cards) */
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

    def _init_mcp(self):
        server_path = os.path.join(os.path.dirname(__file__), "..", "mcp_server.py")
        self.mcp = MCPClient(server_path)
        self.client = LLMUniversity(self.mcp)

    def _setup_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar_width_expanded = 260
        self.sidebar_width_collapsed = 70
        self.sidebar.setFixedWidth(self.sidebar_width_expanded)
        self.is_sidebar_collapsed = False

        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #1a237e;
                border-right: 1px solid #1a237e;
            }
            QLabel { color: white; }
        """)
        
        sb_layout = QVBoxLayout(self.sidebar)
        sb_layout.setContentsMargins(0, 20, 0, 20)
        sb_layout.setSpacing(10)

        # Brand / Toggle Header
        self.brand_label = QLabel("University")
        self.brand_label.setAlignment(Qt.AlignCenter)
        self.brand_label.setStyleSheet("font-size: 20px; font-weight: 800; letter-spacing: 1px; color: #ffffff;")
        sb_layout.addWidget(self.brand_label)
        
        sb_layout.addSpacing(20)

        # Navigation Buttons
        self.nav_btns = []
        # icon, label
        items = [
            ("⊞", "Welcome"),
            ("👤", "Students"),
            ("💬", "AI Assistant")
        ]
        
        for i, (icon, label) in enumerate(items):
            btn = NavigationButton(label, icon)
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))
            sb_layout.addWidget(btn)
            self.nav_btns.append(btn)
            
        sb_layout.addStretch()
        
        # Collapse Toggle Button
        self.toggle_btn = QPushButton("☰") # Initial text
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setFixedHeight(40)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.1);
                color: #ecf0f1;
                border: none;
                border-radius: 4px;
                margin: 0 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.2); }
        """)
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        sb_layout.addWidget(self.toggle_btn)

        self.layout.addWidget(self.sidebar)

    def toggle_sidebar(self):
        self.is_sidebar_collapsed = not self.is_sidebar_collapsed
        collapse = self.is_sidebar_collapsed
        
        # Animate (simple property set for now)
        target_w = self.sidebar_width_collapsed if collapse else self.sidebar_width_expanded
        self.sidebar.setFixedWidth(target_w)
        
        # Update visibility of text elements
        self.brand_label.setVisible(not collapse)
        # self.toggle_btn.setText("☰") # Text remains same
        
        # Update buttons
        for btn in self.nav_btns:
            btn.set_collapsed(collapse)
            
        # Adjust margins for collapsed state if needed
        sb_layout = self.sidebar.layout()
        if collapse:
             sb_layout.setContentsMargins(5, 20, 5, 20)
             self.toggle_btn.setStyleSheet(self.toggle_btn.styleSheet().replace("margin: 0 10px;", "margin: 0;"))
        else:
             sb_layout.setContentsMargins(0, 20, 0, 20)
             self.toggle_btn.setStyleSheet(self.toggle_btn.styleSheet().replace("margin: 0;", "margin: 0 10px;"))

    def _get_greeting(self):
        """Returns a greeting string based on the current time of day."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Good Morning!"
        elif 12 <= hour < 17:
            return "Good Afternoon!"
        else:
            return "Good Evening!"

    def _setup_pages(self):
        # 0. Welcome Page - Structured Layout (Matches Screenshot)
        self.dashboard = QWidget()
        welcome_layout = QVBoxLayout(self.dashboard)
        welcome_layout.setContentsMargins(50, 50, 50, 50)
        welcome_layout.setSpacing(15)
        
        # Greeting
        greeting_text = self._get_greeting()
        greeting_label = QLabel(greeting_text)
        greeting_label.setStyleSheet("font-size: 42px; font-weight: 800; color: #2c3e50; margin-top: 20px;")
        welcome_layout.addWidget(greeting_label)
        
        # Subtitle
        subtitle_label = QLabel("Welcome to the University Management System")
        subtitle_label.setStyleSheet("font-size: 20px; color: #7f8c8d; font-weight: 400;")
        welcome_layout.addWidget(subtitle_label)
        
        welcome_layout.addSpacing(20)
        
        # Description
        desc_text = "This comprehensive system helps you manage student enrollments, course schedules, and academic records efficiently."
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 16px; color: #34495e; line-height: 1.5;")
        welcome_layout.addWidget(desc_label)
        
        welcome_layout.addSpacing(30)
        
        # AI Assistant Help Box
        ai_help_frame = QFrame()
        ai_help_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        ai_help_layout = QHBoxLayout(ai_help_frame)
        ai_help_layout.setContentsMargins(0, 0, 0, 0)
        ai_help_layout.setSpacing(10)
        
        ai_icon = QLabel("💬")
        ai_icon.setStyleSheet("font-size: 24px; color: #7f8c8d;")
        ai_icon.setAlignment(Qt.AlignTop)
        
        ai_text_label = QLabel(
            "<b>Need help? Our AI Assistant is here for you!</b> Ask questions about "
            "student enrollments, course management, or get analytics insights. "
            "Navigate to the AI Assistant tab to get started."
        )
        ai_text_label.setWordWrap(True)
        ai_text_label.setStyleSheet("font-size: 15px; color: #1a237e; line-height: 1.4;")
        
        ai_help_layout.addWidget(ai_icon)
        ai_help_layout.addWidget(ai_text_label, 1)
        
        welcome_layout.addWidget(ai_help_frame)
        welcome_layout.addStretch()
        
        self.content_area.addWidget(self.dashboard)

        # 1. Students Page (Refactored)
        self.students_page = StudentsPage(self.mcp, self)
        self.content_area.addWidget(self.students_page)



        # 3. AI Assistant
        self.chat_page = ChatTab(self.client, self, get_context_callback=self.get_selected_semester_id)
        self.content_area.addWidget(self.chat_page)
        
        # Signal Connections
        # When AI adds data, refresh other pages
        self.chat_page.data_refreshed.connect(self.refresh_data)

    def switch_page(self, index):
        self.content_area.setCurrentIndex(index)
        # Only refresh when data has actually changed since last refresh (dirty flag)
        if self._data_dirty:
            self.students_page.refresh_all()
            self._data_dirty = False

    def refresh_data(self):
        """Called by AI tab to refresh all views."""
        self._data_dirty = True
        self.students_page.refresh_all()

    def get_selected_semester_id(self):
        """Return the currently selected semester ID from the Students page."""
        return self.students_page.get_current_semester_id()