from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QSpinBox,
    QPushButton, QHBoxLayout, QVBoxLayout, QMessageBox, QLabel, QAbstractSpinBox
)
from PyQt5.QtCore import Qt

class ModernDialog(QDialog):
    """Base class providing a modern 2026-style look."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                font-size: 14px;
                color: #334155;
                font-weight: 500;
            }
            QLineEdit, QSpinBox {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                background-color: #f8fafc;
                font-size: 14px;
                color: #1e293b;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 2px solid #3b82f6;
                background-color: #ffffff;
            }
            /* Primary Button (OK/Update) */
            QPushButton[role="primary"] {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton[role="primary"]:hover {
                background-color: #1d4ed8;
            }
            /* Secondary Button (Cancel) */
            QPushButton[role="secondary"] {
                background-color: #f1f5f9;
                color: #475569;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton[role="secondary"]:hover {
                background-color: #e2e8f0;
                color: #1e293b;
            }
        """)

class NewSemesterDialog(ModernDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Semester")
        self.setMinimumWidth(400)
        self._init_ui()

    def _init_ui(self):
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Fall 2026")

        form = QFormLayout()
        form.setSpacing(15)
        form.addRow("Semester Name:", self.name_edit)

        btn_ok = QPushButton("Add Semester")
        btn_ok.setProperty("role", "primary")
        btn_ok.setCursor(Qt.PointingHandCursor)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("role", "secondary")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_cancel)
        buttons_layout.addWidget(btn_ok)

        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        layout.addLayout(form)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def get_data(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Semester name cannot be empty.")
            return None
        return name


class EditGradesDialog(ModernDialog):
    """Edit Midterm/Final. Total is computed by the backend."""

    def __init__(self, parent=None, midterm=None, final=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Grades")
        self.setMinimumWidth(350)
        self._init_ui(midterm, final)

    def _init_ui(self, midterm, final):
        self.midterm_edit = QLineEdit()
        self.final_edit = QLineEdit()
        self.midterm_edit.setPlaceholderText("0 - 40")
        self.final_edit.setPlaceholderText("0 - 60")

        if midterm is not None:
            self.midterm_edit.setText(str(midterm))
        if final is not None:
            self.final_edit.setText(str(final))

        form = QFormLayout()
        form.setSpacing(15)
        form.addRow("Midterm (Max 40):", self.midterm_edit)
        form.addRow("Final Exam (Max 60):", self.final_edit)

        btn_ok = QPushButton("Save Grades")
        btn_ok.setProperty("role", "primary")
        btn_ok.setCursor(Qt.PointingHandCursor)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("role", "secondary")
        btn_cancel.setCursor(Qt.PointingHandCursor)

        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_cancel)
        buttons_layout.addWidget(btn_ok)

        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        layout.addLayout(form)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def get_data(self):
        def parse_optional_float(text: str):
            t = text.strip()
            if t == "":
                return None
            try:
                return float(t)
            except ValueError:
                return "__invalid__"

        m = parse_optional_float(self.midterm_edit.text())
        f = parse_optional_float(self.final_edit.text())
        
        if m == "__invalid__" or f == "__invalid__":
            QMessageBox.warning(self, "Input Error", "Midterm/Final must be numbers (or left empty).")
            return None
            
        # UI Validation for ranges
        if m is not None and (m < 0 or m > 40):
            QMessageBox.warning(self, "Input Error", "Midterm must be between 0 and 40.")
            return None
        if f is not None and (f < 0 or f > 60):
            QMessageBox.warning(self, "Input Error", "Final exam must be between 0 and 60.")
            return None
            
        return m, f


class NewCourseDialog(ModernDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Course")
        self.setMinimumWidth(450)
        self._init_ui()

    def _init_ui(self):
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("e.g. CS101")
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("e.g. Intro to CS")
        
        self.instructor_edit = QLineEdit()
        self.instructor_edit.setPlaceholderText("e.g. Dr. Ahmed")
        
        self.max_seats_edit = QSpinBox()
        self.max_seats_edit.setRange(1, 500)
        self.max_seats_edit.setValue(30)

        form = QFormLayout()
        form.setSpacing(15)
        form.addRow("Course Code:", self.code_edit)
        form.addRow("Course Title:", self.title_edit)
        form.addRow("Instructor:", self.instructor_edit)
        form.addRow("Max Seats:", self.max_seats_edit)

        btn_ok = QPushButton("Create Course")
        btn_ok.setProperty("role", "primary")
        btn_ok.setCursor(Qt.PointingHandCursor)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("role", "secondary")
        btn_cancel.setCursor(Qt.PointingHandCursor)

        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_cancel)
        buttons_layout.addWidget(btn_ok)

        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        layout.addLayout(form)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def get_data(self):
        code = self.code_edit.text().strip()
        title = self.title_edit.text().strip()
        instructor = self.instructor_edit.text().strip()
        max_seats = self.max_seats_edit.value()
        if not code or not title or not instructor:
            QMessageBox.critical(self, "Input Error", "Code, title, and instructor are required.")
            return None
        return code, title, instructor, max_seats


class NewStudentDialog(ModernDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register New Student")
        self.setMinimumWidth(400)
        self._init_ui()

    def _init_ui(self):
        self.id_edit = QSpinBox()
        self.id_edit.setRange(1, 999999)
        self.id_edit.setValue(1)  # Default to 1; enter any available unique ID
        self.id_edit.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.id_edit.setToolTip("Enter a unique numeric ID for this student (e.g. 1, 101, 2025001)")
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Full Name")

        form = QFormLayout()
        form.setSpacing(15)
        form.addRow("Student ID:", self.id_edit)
        form.addRow("Full Name:", self.name_edit)

        btn_ok = QPushButton("Register Student")
        btn_ok.setProperty("role", "primary")
        btn_ok.setCursor(Qt.PointingHandCursor)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("role", "secondary")
        btn_cancel.setCursor(Qt.PointingHandCursor)

        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_cancel)
        buttons_layout.addWidget(btn_ok)

        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        layout.addLayout(form)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def get_data(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Name cannot be empty.")
            return None
        return self.id_edit.value(), name







class ConfirmationDialog(ModernDialog):
    """Generic confirmation dialog with customizable message and action button."""
    def __init__(self, parent=None, title="Confirm Action", message="Are you sure?", confirm_text="Confirm", is_destructive=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self._init_ui(message, confirm_text, is_destructive)

    def _init_ui(self, message, confirm_text, is_destructive):
        # Message Label
        lbl_message = QLabel(message)
        lbl_message.setWordWrap(True)
        lbl_message.setStyleSheet("font-size: 15px; color: #1e293b; padding: 10px 0;")

        # Buttons
        btn_confirm = QPushButton(confirm_text)
        if is_destructive:
            btn_confirm.setStyleSheet("""
                QPushButton {
                    background-color: #dc2626;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: 600;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #b91c1c;
                }
            """)
        else:
            btn_confirm.setProperty("role", "primary")
        btn_confirm.setCursor(Qt.PointingHandCursor)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("role", "secondary")
        btn_cancel.setCursor(Qt.PointingHandCursor)

        btn_confirm.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_cancel)
        buttons_layout.addWidget(btn_confirm)

        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        layout.addWidget(lbl_message)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)