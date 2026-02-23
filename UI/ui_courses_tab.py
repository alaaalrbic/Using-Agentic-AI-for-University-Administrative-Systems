from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush, QFont
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QComboBox,
    QMessageBox,
    QDialog,
    QHeaderView,
    QScrollArea,
    QFrame,
    QLineEdit,
    QSizePolicy

)

from utils.utils import mcp_to_python
from UI.dialogs import NewCourseDialog, NewStudentDialog, NewSemesterDialog, EditGradesDialog, ConfirmationDialog


class CourseCard(QFrame):
    """
    A modern card widget representing a course.
    Style depends on status (Full, Open, Enrolled).
    """
    action_clicked = pyqtSignal(str) # Emits course_code

    def __init__(self, code, title, instructor, seats_info, status, action_label, action_color, parent=None):
        super().__init__(parent)
        self.code = code
        self.setFrameShape(QFrame.StyledPanel)
        self.setLineWidth(1)
        
        # Color coding based on status
        bg_color = "#ffffff"
        border_color = "#e0e0e0"
        status_color = "#28a745" # Green default
        
        if status == "Full":
            bg_color = "#fff3f3" # Red tint
            border_color = "#ffcdd2"
            status_color = "#d32f2f"
        elif status == "Enrolled":
            bg_color = "#e8f5e9" # Green tint
            border_color = "#c8e6c9"
            status_color = "#2e7d32"
        elif status == "Waitlist":
            bg_color = "#fffde7" # Yellow tint
            border_color = "#fff9c4"
            status_color = "#fbc02d"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
            QLabel {{ border: none; background: transparent; }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Left Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        info_layout.addWidget(lbl_title)
        
        lbl_meta = QLabel(f"{code} • {instructor}")
        lbl_meta.setStyleSheet("font-size: 12px; color: #666;")
        info_layout.addWidget(lbl_meta)
        
        lbl_seats = QLabel(seats_info)
        lbl_seats.setStyleSheet("font-size: 12px; color: #888;")
        info_layout.addWidget(lbl_seats)
        
        layout.addLayout(info_layout, 1) # Stretch

        # Right Actions
        action_layout = QVBoxLayout()
        action_layout.setSpacing(5)
        
        lbl_status = QLabel(status)
        lbl_status.setAlignment(Qt.AlignRight)
        lbl_status.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {status_color}; text-transform: uppercase;")
        action_layout.addWidget(lbl_status)
        
        btn_action = QPushButton(action_label)
        btn_action.setCursor(Qt.PointingHandCursor)
        btn_action.setStyleSheet(f"""
            QPushButton {{
                background-color: {action_color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
        """)
        btn_action.clicked.connect(lambda: self.action_clicked.emit(self.code))
        action_layout.addWidget(btn_action)
        
        layout.addLayout(action_layout)


class StudentsPage(QWidget):
    """
    Matches the screenshot precisely:
    - Header: "Course Management - [Student Name]"
    - Select Student Bar: Wide white box.
    - Dual Columns: Available vs Enrolled, each with a Search Bar.
    - Cards: Status badges, action buttons.
    - Footer: Cancel/Save Changes (dummy for now).
    """

    def __init__(self, mcp_bridge, parent=None):
        super().__init__(parent)
        self.mcp = mcp_bridge
        self._semesters_cache = []
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 20, 30, 20)
        self.setLayout(main_layout)

        # 1. Page Header
        self.lbl_header = QLabel("Course Management")
        self.lbl_header.setStyleSheet("font-size: 28px; font-weight: 800; color: #1a237e;")
        main_layout.addWidget(self.lbl_header)

        # 2. Select Student Section (White Card)
        student_bar = QFrame()
        student_bar.setStyleSheet("background-color: white; border-radius: 12px; border: 1px solid #e0e6ed; padding: 15px;")
        sb_layout = QHBoxLayout(student_bar)
        
        lbl_sel = QLabel("Select Student:")
        lbl_sel.setStyleSheet("font-weight: 600; color: #555; border: none;")
        sb_layout.addWidget(lbl_sel)

        self.student_combo = QComboBox()
        # Modern 2026 CSS for ComboBox
        combo_style = """
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 10px;
                padding: 5px 15px;
                font-size: 13px;
                color: #333;
                min-height: 30px;
            }
            QComboBox:hover {
                border: 1px solid #a0a0a0;
                background-color: #fcfcfc;
            }
            QComboBox:focus {
                border: 2px solid #007bff;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left-width: 0px; 
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
            }
            QComboBox::down-arrow {
                width: 10px; 
                height: 10px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #ced4da;
                selection-background-color: #e6f7ff;
                selection-color: #007bff;
                background-color: white;
                outline: none;
                border-radius: 5px;
                padding: 4px;
            }
        """
        
        self.student_combo.setMinimumWidth(150)
        self.student_combo.setFixedHeight(40) # Consistent Height
        self.student_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.student_combo.setStyleSheet(combo_style)
        sb_layout.addWidget(self.student_combo, 1) # Add stretch factor
        
        # Tools near combo (Small buttons)
        self.btn_new_student = QPushButton("+ Add")
        self.btn_new_student.setStyleSheet("background-color: #28a745; color: white; padding: 4px 8px; font-size: 12px; font-weight: bold; border-radius: 4px;")
        self.btn_new_student.setToolTip("Add Student")
        sb_layout.addWidget(self.btn_new_student)
        
        # Semester
        lbl_sem = QLabel("Semester:")
        lbl_sem.setStyleSheet("font-weight: 600; color: #555; border: none;")
        sb_layout.addWidget(lbl_sem)
        
        self.semester_combo = QComboBox()
        self.semester_combo.setMinimumWidth(150)
        self.semester_combo.setFixedHeight(40) # Consistent Height
        self.semester_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.semester_combo.setStyleSheet(combo_style)
        sb_layout.addWidget(self.semester_combo, 1) # Add stretch factor
        
        self.btn_new_semester = QPushButton("+ Add")
        self.btn_new_semester.setStyleSheet("background-color: #28a745; color: white; padding: 4px 8px; font-size: 12px; font-weight: bold; border-radius: 4px;")
        self.btn_new_semester.setToolTip("Add New Semester")
        sb_layout.addWidget(self.btn_new_semester)
        
        self.btn_close_semester = QPushButton("Close")
        self.btn_close_semester.setStyleSheet("background-color: #dc3545; color: white; padding: 4px 8px; font-size: 12px; font-weight: bold; border-radius: 4px;")
        self.btn_close_semester.setToolTip("Close Semester")
        sb_layout.addWidget(self.btn_close_semester)
        
        self.semester_state_label = QLabel("")
        sb_layout.addWidget(self.semester_state_label)

        sb_layout.addStretch()
        main_layout.addWidget(student_bar)

        # 3. Two Columns Area
        cols_layout = QHBoxLayout()
        cols_layout.setSpacing(25)

        # --- LEFT: Available ---
        left_col = QVBoxLayout()
        # Header with Tools
        av_header_layout = QHBoxLayout()
        left_header = QLabel("Available Courses")
        left_header.setStyleSheet("font-size: 18px; font-weight: 700; color: #333;")
        av_header_layout.addWidget(left_header)
        av_header_layout.addStretch()
        
        self.btn_add_course = QPushButton("+ Course")
        self.btn_add_course.setStyleSheet("background-color: #007bff; color: white; padding: 4px 8px; font-size: 11px; font-weight: bold; border-radius: 4px;")
        av_header_layout.addWidget(self.btn_add_course)
        
        left_col.addLayout(av_header_layout)

        self.scroll_avail = QScrollArea()
        self.scroll_avail.setWidgetResizable(True)
        self.scroll_avail.setStyleSheet("background: transparent; border: none;")
        self.container_avail = QWidget()
        self.layout_avail = QVBoxLayout(self.container_avail)
        self.layout_avail.setSpacing(12)
        self.layout_avail.addStretch()
        self.scroll_avail.setWidget(self.container_avail)
        left_col.addWidget(self.scroll_avail)
        cols_layout.addLayout(left_col, 1)

        # --- RIGHT: Enrolled ---
        right_col = QVBoxLayout()
        right_header = QLabel("Enrolled Courses")
        right_header.setStyleSheet("font-size: 18px; font-weight: 700; color: #333;")
        right_col.addWidget(right_header)

        self.scroll_enrolled = QScrollArea()
        self.scroll_enrolled.setWidgetResizable(True)
        self.scroll_enrolled.setStyleSheet("background: transparent; border: none;")
        self.container_enrolled = QWidget()
        self.layout_enrolled = QVBoxLayout(self.container_enrolled)
        self.layout_enrolled.setSpacing(12)
        self.layout_enrolled.addStretch()
        self.scroll_enrolled.setWidget(self.container_enrolled)
        right_col.addWidget(self.scroll_enrolled)
        
        # GPA Label
        self.avg_label = QLabel("")
        self.avg_label.setAlignment(Qt.AlignRight)
        self.avg_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #007bff;")
        right_col.addWidget(self.avg_label)

        cols_layout.addLayout(right_col, 1)
        main_layout.addLayout(cols_layout)

    def _connect_signals(self):
        self.btn_new_student.clicked.connect(self.handle_add_student)
        self.btn_new_semester.clicked.connect(self.handle_add_semester)
        self.btn_close_semester.clicked.connect(self.handle_close_semester)

        self.btn_add_course.clicked.connect(self.handle_add_course)

        self.student_combo.currentIndexChanged.connect(self.refresh_after_selection_change)
        self.semester_combo.currentIndexChanged.connect(self.on_semester_changed)

    # --- Helpers ---
    def show_message(self, title, text, icon=QMessageBox.Information):
        mb = QMessageBox(self)
        mb.setWindowTitle(title)
        mb.setText(text)
        mb.setIcon(icon)
        mb.exec_()

    def get_current_student_id(self):
        return self.student_combo.currentData()

    def get_current_semester_id(self):
        return self.semester_combo.currentData()

    # --- Loading Data (Redesigned for Cards) ---
    def refresh_all(self):
        self.load_students()
        self.load_semesters()
        self.load_avail_courses()
        self.load_enrolled_courses()
    
    def _clear_layout(self, layout):
        # Remove all widgets except the spacer at the end
        while layout.count() > 1:
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def load_students(self):
        current = self.get_current_student_id()
        raw = self.mcp.call_tool("list_students")
        students = mcp_to_python(raw) or []
        if not isinstance(students, list): students = [students]

        self.student_combo.blockSignals(True)
        self.student_combo.clear()
        for s in students:
            if isinstance(s, dict) and s.get("id"):
                self.student_combo.addItem(f"{s['name']} (ID: {s['id']})", int(s['id']))
        
        if current is not None:
            idx = self.student_combo.findData(current)
            if idx >= 0: self.student_combo.setCurrentIndex(idx)
        self.student_combo.blockSignals(False)
        self._update_header()

    def _update_header(self):
         name = self.student_combo.currentText().rsplit(" (ID:", 1)[0]
         if name and "--" not in name:
             self.lbl_header.setText(f"Course Management - {name}")
         else:
             self.lbl_header.setText("Course Management")

    def load_semesters(self):
        # Same as before
        current = self.get_current_semester_id()
        raw = self.mcp.call_tool("list_semesters")
        semesters = mcp_to_python(raw) or []
        if not isinstance(semesters, list): semesters = [semesters]
        self._semesters_cache = [s for s in semesters if isinstance(s, dict)]

        self.semester_combo.blockSignals(True)
        self.semester_combo.clear()
        self.semester_combo.addItem("-- Select Semester --", None)

        for s in self._semesters_cache:
             if s.get("id"):
                self.semester_combo.addItem(f"{s['name']} ({s['state']})", int(s['id']))
        
        if current is not None:
             idx = self.semester_combo.findData(current)
             if idx >= 0: self.semester_combo.setCurrentIndex(idx)
        else:
             self.semester_combo.setCurrentIndex(0)
             
        self.semester_combo.blockSignals(False)
        self._update_semester_state_ui()

    def load_avail_courses(self):
        self._clear_layout(self.layout_avail)
        
        raw = self.mcp.call_tool("list_courses")
        courses = mcp_to_python(raw) or []
        if not isinstance(courses, list): courses = [courses]

        for c in courses:
            if not isinstance(c, dict): continue
            
            code = str(c.get("code", ""))
            title = str(c.get("title", ""))
            inst = str(c.get("instructor", ""))
            
            avail = c.get('available', 0)
            maxx = c.get('max_seats', 0)
            seats_info = f"{avail}/{maxx} seats"
            
            # Determine status
            try:
                is_full = int(avail) <= 0
            except: is_full = False
            
            status = "Full" if is_full else "Open"
            
            # Create CARD
            card = CourseCard(
                code, title, inst, seats_info, 
                status=status, 
                action_label="Enroll",
                action_color="#007bff",
                parent=self
            )
            # If full, maybe disable? But user might want to try waitlist logic (if existed)
            # For now, allow clicking but backend might reject
            if is_full:
                 card.setStyleSheet(card.styleSheet().replace("#ffffff", "#fff5f5")) # Light red bg
            
            card.action_clicked.connect(self.handle_enroll_by_code)
            
            # Valid insert at position 0 (top) or append before stretch? 
            # Layout has stretch at end, so insert at count()-1 matches append behavior
            self.layout_avail.insertWidget(self.layout_avail.count()-1, card)

    def load_enrolled_courses(self):
        self._clear_layout(self.layout_enrolled)
        
        sid = self.get_current_student_id()
        sem_id = self.get_current_semester_id()
        
        if not (sid and sem_id):
            self.avg_label.setText("")
            return

        raw = self.mcp.call_tool("get_student_enrollments", {"student_id": int(sid), "semester_id": int(sem_id)})
        courses = mcp_to_python(raw) or []
        if not isinstance(courses, list): courses = [courses]

        for c in courses:
            if not isinstance(c, dict): continue
            
            code = str(c.get("code", ""))
            title = str(c.get("title", ""))
            # Reuse instructor if available, else blank
            inst = str(c.get("instructor", "")) 
            
            mid = c.get("midterm")
            fin = c.get("final")
            grade_str = f"Mid: {mid} | Fin: {fin}" if (mid or fin) else "No Grades"
            
            card = CourseCard(
                code, title, inst, grade_str, 
                status="Enrolled",
                action_label="Drop",
                action_color="#dc3545", # Red
                parent=self
            )
            # Add 'Edit Grade' button to the card content manually or modifying CourseCard?
            # Easier to add a second button to the card layout for now. 
            # I will inject a "Grades" button into the card's action layout.
            btn_grades = QPushButton("Grades")
            btn_grades.setCursor(Qt.PointingHandCursor)
            btn_grades.setStyleSheet("background-color: #17a2b8; color: white; border: none; border-radius: 4px; padding: 4px 8px; font-weight: bold; font-size: 11px;")
            btn_grades.clicked.connect(lambda _, c=code: self.handle_edit_grades(c))
            
            # Insert before Drop button (which is the last item in action_layout)
            # CourseCard layout structure: HBox -> [VBox(Info), VBox(Action)]
            # Action VBox has: Label(Status), Button(Action)
            card.layout().itemAt(1).layout().insertWidget(1, btn_grades)

            card.action_clicked.connect(self.handle_drop_by_code)
            self.layout_enrolled.insertWidget(self.layout_enrolled.count()-1, card)

        # GPA
        avg_raw = self.mcp.call_tool("get_semester_average", {"student_id": int(sid), "semester_id": int(sem_id)})
        avg_Obj = mcp_to_python(avg_raw) or {}
        val = avg_Obj.get("average")
        if val is not None:
            self.avg_label.setText(f"Semester GPA: {val:.2f}")
        else:
            self.avg_label.setText("")

    def refresh_after_selection_change(self):
        self._update_header()
        self.load_enrolled_courses()
        self.load_avail_courses()

    def on_semester_changed(self):
        sem_id = self.get_current_semester_id()
        # Call set_active_semester with None if selection is "-- Select Semester --"
        self.mcp.call_tool("set_active_semester", {"semester_id": int(sem_id) if sem_id else None})
        self._update_semester_state_ui()
        self.load_semesters()
        self.load_avail_courses()
        self.load_enrolled_courses()

    def _update_semester_state_ui(self):
        sem_id = self.get_current_semester_id()
        if not sem_id:
            self.semester_state_label.setText("")
            self.btn_close_semester.setEnabled(False)
            return
            
        state = "UNKNOWN"
        for s in self._semesters_cache:
            if s.get("id") == sem_id:
                state = str(s.get("state")).upper()
                break
        
        self.semester_state_label.setText(state)
        isOpen = (state == "OPEN")
        self.btn_close_semester.setEnabled(isOpen)
        
        if isOpen:
            self.semester_state_label.setStyleSheet("color: #28a745; font-weight: bold;")
        else:
            self.semester_state_label.setStyleSheet("color: #dc3545; font-weight: bold;")

    # --- Actions ---
    def handle_add_student(self):
        d = NewStudentDialog(self)
        if d.exec_() == QDialog.Accepted:
            data = d.get_data()
            if data:
                res = self.mcp.call_tool("add_student", {"student_id": int(data[0]), "name": str(data[1])})
                self.show_message("Result", str(mcp_to_python(res).get("message")))
                self.load_students()

    def handle_add_semester(self):
        d = NewSemesterDialog(self)
        if d.exec_() == QDialog.Accepted:
            name = d.get_data()
            if name:
                 res = self.mcp.call_tool("add_semester", {"name": str(name)})
                 self.show_message("Result", str(mcp_to_python(res).get("message")))
                 self.load_semesters()

    def handle_close_semester(self):
        sid = self.get_current_semester_id()
        if not sid: 
            return
            
        # Get semester name for better message
        sem_name = self.semester_combo.currentText()
        
        # Show modern confirmation dialog
        d = ConfirmationDialog(
            self,
            title="Confirm Close Semester",
            message=f"Are you sure you want to close semester '{sem_name}'?\n\nThis action cannot be undone.",
            confirm_text="Close Semester",
            is_destructive=True
        )
        if d.exec_() == QDialog.Accepted:
            res = self.mcp.call_tool("close_semester", {"semester_id": int(sid)})
            self.show_message("Result", str(mcp_to_python(res).get("message")))
            self.load_semesters()

    def handle_enroll_by_code(self, code):
        sid = self.get_current_student_id()
        sem = self.get_current_semester_id()
        if not sid or not sem:
            self.show_message("Error", "Please select a student and semester first.", QMessageBox.Warning)
            return
            
        # Show modern confirmation dialog
        student_name = self.student_combo.currentText().rsplit(" (ID:", 1)[0]
        d = ConfirmationDialog(
            self,
            title="Confirm Enrollment",
            message=f"Enroll {student_name} in course {code}?",
            confirm_text="Enroll",
            is_destructive=False
        )
        if d.exec_() == QDialog.Accepted:
            res = self.mcp.call_tool("enroll", {"student_id": int(sid), "semester_id": int(sem), "course_code": code})
            self.show_message("Result", str(mcp_to_python(res).get("message")))
            self.refresh_all()

    def handle_drop_by_code(self, code):
        sid = self.get_current_student_id()
        sem = self.get_current_semester_id()
        if not sid or not sem:
            return
            
        # Show modern confirmation dialog
        student_name = self.student_combo.currentText().rsplit(" (ID:", 1)[0]
        d = ConfirmationDialog(
            self,
            title="Confirm Drop",
            message=f"Drop {student_name} from course {code}?",
            confirm_text="Drop Course",
            is_destructive=True
        )
        if d.exec_() == QDialog.Accepted:
            res = self.mcp.call_tool("drop", {"student_id": int(sid), "semester_id": int(sem), "course_code": code})
            self.show_message("Result", str(mcp_to_python(res).get("message")))
            self.refresh_all()
    
    # Missing: Edit Grades for a card. 
    # Logic: Maybe Click the card to edit? Or add a small "Edit" button?
    # For now, I'll rely on a click or a long-press, OR user can add a "Edit" button to Enrolled cards.
    # Updated Enrolled Card: Added 'Drop' button. 
    # I will add a click handler to the EnrolledCard itself to open Edit Grades dialog.


    def handle_add_course(self):
        d = NewCourseDialog(self)
        if d.exec_() == QDialog.Accepted:
            data = d.get_data()
            if data:
                payload = {"code": data[0], "title": data[1], "instructor": data[2], "max_seats": int(data[3])}
                res = self.mcp.call_tool("add_course", payload)
                self.show_message("Result", str(mcp_to_python(res).get("message")))
                self.refresh_all()

    def handle_edit_grades(self, course_code):
        sid = self.get_current_student_id()
        sem = self.get_current_semester_id()
        

        
        # Quick lookup in current enrollments UI or data?
        # Accessing tool again is safer.
        raw = self.mcp.call_tool("get_student_enrollments", {"student_id": int(sid), "semester_id": int(sem)})
        courses = mcp_to_python(raw) or []
        if not isinstance(courses, list): courses = [courses]
        
        target = None
        for c in courses:
            if c.get("code") == course_code:
                target = c
                break
        
        if target:
            mid = target.get("midterm", 0)
            fin = target.get("final", 0)
            d = EditGradesDialog(self, midterm=mid, final=fin)
            if d.exec_() == QDialog.Accepted:
                data = d.get_data()
                if data is None:
                    return
                new_mid, new_fin = data
                payload = {
                    "student_id": int(sid), 
                    "semester_id": int(sem), 
                    "course_code": course_code,
                }
                if new_mid is not None:
                    payload["midterm"] = int(new_mid)
                if new_fin is not None:
                    payload["final"] = int(new_fin)

                res = self.mcp.call_tool("set_course_grade", payload)
                self.show_message("Result", str(mcp_to_python(res).get("message")))
                self.load_enrolled_courses() # Refresh to show new grades


