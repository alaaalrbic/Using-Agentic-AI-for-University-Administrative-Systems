import sqlite3
from typing import Optional, Tuple, List

from core.semester_rules import (
    ensure_semester_open,
    compute_total,
    check_max_courses,
    check_not_passed_before,
    check_not_taken_this_semester,
    PASS_MARK_DEFAULT,
)

class EnrollmentMixin:
    def _resolve_semester_id(self, semester_id: Optional[int]) -> Tuple[Optional[int], Optional[str]]:
        if semester_id is not None:
            return int(semester_id), None
        sem_id = self.get_active_semester_id()
        if sem_id is None:
            return None, "No active semester. Please create/set an active semester first."
        return int(sem_id), None
#-----------------------------------------------------------------------------------------------------------------------------
    def get_enrolled_courses_for_student(self, student_id: int, semester_id: Optional[int] = None):
        sem_id, err = self._resolve_semester_id(semester_id)
        if err:
            return []

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT c.code, c.title,
                       e.midterm, e.final, e.total
                FROM enrollments e
                JOIN courses c ON e.course_id = c.id
                WHERE e.student_id = ?
                  AND e.semester_id = ?
                  AND e.withdrawn = 0
                ORDER BY c.code;
                """,
                (int(student_id), int(sem_id)),
            )
            return cur.fetchall()
#-----------------------------------------------------------------------------------------------------------------------------
    def _semester_guard(self, cur: sqlite3.Cursor, semester_id: int) -> Tuple[bool, str]:
        cur.execute("SELECT state FROM semesters WHERE id=?;", (int(semester_id),))
        row = cur.fetchone()
        if not row:
            return False, "Semester not found."
        return ensure_semester_open(row[0])
#-----------------------------------------------------------------------------------------------------------------------------
    def _count_current_courses(self, cur: sqlite3.Cursor, student_id: int, semester_id: int) -> int:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM enrollments
            WHERE student_id=? AND semester_id=? AND withdrawn=0;
            """,
            (int(student_id), int(semester_id)),
        )
        return int(cur.fetchone()[0])
#-----------------------------------------------------------------------------------------------------------------------------
    def _student_passed_course_before(self, cur: sqlite3.Cursor, student_id: int, course_id: int) -> bool:
        cur.execute(
            """
            SELECT 1
            FROM enrollments
            WHERE student_id=?
              AND course_id=?
              AND withdrawn=0
              AND incomplete=0
              AND total IS NOT NULL
              AND total >= ?;
            """,
            (int(student_id), int(course_id), float(PASS_MARK_DEFAULT)),
        )
        return cur.fetchone() is not None
#-----------------------------------------------------------------------------------------------------------------------------
    def _already_taken_course_this_semester(self, cur: sqlite3.Cursor, student_id: int, course_id: int, semester_id: int) -> bool:
        cur.execute(
            """
            SELECT 1
            FROM enrollments
            WHERE student_id=? AND course_id=? AND semester_id=?;
            """,
            (int(student_id), int(course_id), int(semester_id)),
        )
        return cur.fetchone() is not None
#-----------------------------------------------------------------------------------------------------------------------------
    def enroll_student_in_course(self, student_id: int, course_id: int, semester_id: Optional[int] = None) -> dict:
        sem_id, err = self._resolve_semester_id(semester_id)
        if err:
            return {"success": False, "message": err, "data": None}

        try:
            with self._connect() as conn:
                cur = conn.cursor()

                ok, msg = self._semester_guard(cur, sem_id)
                if not ok:
                    return {"success": False, "message": msg, "data": None}

                cur.execute("SELECT max_seats FROM courses WHERE id=?;", (int(course_id),))
                row = cur.fetchone()
                if row is None:
                    return {"success": False, "message": "Course not found.", "data": None}
                max_seats = int(row[0])

                current_count = self._count_current_courses(cur, student_id, sem_id)
                ok, msg = check_max_courses(current_count, 4)
                if not ok:
                    return {"success": False, "message": msg, "data": None}

                passed_before = self._student_passed_course_before(cur, student_id, course_id)
                ok, msg = check_not_passed_before(passed_before)
                if not ok:
                    return {"success": False, "message": msg, "data": None}
                cur.execute(
                    "SELECT withdrawn, incomplete FROM enrollments WHERE student_id=? AND course_id=? AND semester_id=?;",
                    (int(student_id), int(course_id), int(sem_id)),
                )
                existing = cur.fetchone()

                if existing:
                    is_withdrawn = (existing[0] == 1)
                    if not is_withdrawn:
                        return {"success": False, "message": "Cannot retake the same course within the same semester.", "data": None}
                    cur.execute(
                        "SELECT COUNT(*) FROM enrollments WHERE course_id=? AND semester_id=? AND withdrawn=0;",
                        (int(course_id), int(sem_id)),
                    )
                    current_seat_count = int(cur.fetchone()[0])
                    if current_seat_count >= max_seats:
                        return {"success": False, "message": "Course is full.", "data": None}

                    cur.execute(
                        """
                        UPDATE enrollments
                        SET withdrawn=0, midterm=NULL, final=NULL, total=NULL, incomplete=0
                        WHERE student_id=? AND course_id=? AND semester_id=?;
                        """,
                        (int(student_id), int(course_id), int(sem_id)),
                    )
                    conn.commit()
                    return {"success": True, "message": "Student re-enrolled successfully.", "data": None}

                else:
                    cur.execute(
                        "SELECT COUNT(*) FROM enrollments WHERE course_id=? AND semester_id=? AND withdrawn=0;",
                        (int(course_id), int(sem_id)),
                    )
                    current = int(cur.fetchone()[0])
                    if current >= max_seats:
                        return {"success": False, "message": "Course is full.", "data": None}

                    cur.execute(
                        """
                        INSERT INTO enrollments (student_id, course_id, semester_id, midterm, final, total, withdrawn, incomplete)
                        VALUES (?, ?, ?, NULL, NULL, NULL, 0, 0);
                        """,
                        (int(student_id), int(course_id), int(sem_id)),
                    )
                    conn.commit()

            return {"success": True, "message": "Student enrolled successfully.", "data": None}
        except sqlite3.IntegrityError:
            return {"success": False, "message": "Student is already enrolled in this course for this semester.", "data": None}
        except sqlite3.Error as e:
            return {"success": False, "message": f"Database error: {e}", "data": None}
#-----------------------------------------------------------------------------------------------------------------------------
    def drop_student_from_course(self, student_id: int, course_id: int, semester_id: Optional[int] = None) -> dict:
        sem_id, err = self._resolve_semester_id(semester_id)
        if err:
            return {"success": False, "message": err, "data": None}
        try:
            with self._connect() as conn:
                cur = conn.cursor()

                ok, msg = self._semester_guard(cur, sem_id)
                if not ok:
                    return {"success": False, "message": msg, "data": None}

                cur.execute(
                    """
                    UPDATE enrollments
                    SET withdrawn=1
                    WHERE student_id=? AND course_id=? AND semester_id=?;
                    """,
                    (int(student_id), int(course_id), int(sem_id)),
                )
                if cur.rowcount == 0:
                    return {"success": False, "message": "Student is not enrolled in this course.", "data": None}
                conn.commit()
            return {"success": True, "message": "Student withdrawn from course (W).", "data": None}
        except sqlite3.Error as e:
            return {"success": False, "message": f"Database error: {e}", "data": None}
#-----------------------------------------------------------------------------------------------------------------------------
    def update_course_grade(
        self,
        student_id: int,
        course_id: int,
        semester_id: Optional[int],
        midterm: Optional[float] = None,
        final: Optional[float] = None,
    ) -> dict:
        sem_id, err = self._resolve_semester_id(semester_id)
        if err:
            return {"success": False, "message": err, "data": None}

        try:
            with self._connect() as conn:
                cur = conn.cursor()

                ok, msg = self._semester_guard(cur, sem_id)
                if not ok:
                    return {"success": False, "message": msg, "data": None}

                # 1. Fetch existing grades
                cur.execute(
                    "SELECT midterm, final FROM enrollments WHERE student_id=? AND course_id=? AND semester_id=?;",
                    (int(student_id), int(course_id), int(sem_id)),
                )
                row = cur.fetchone()
                if not row:
                    return {"success": False, "message": "Enrollment not found.", "data": None}
                
                existing_mid, existing_final = row

                # 2. Merge new values with existing (new takes precedence unless it's None)
                new_mid = midterm if midterm is not None else existing_mid
                new_final = final if final is not None else existing_final

                # 3. Compute total
                # Treat None as 0 for total calculation if needed, or keep as None if both are None
                # Assuming compute_total handles None correctly (usually treats as 0)
                total = compute_total(new_mid, new_final)

                # 4. Update
                cur.execute(
                    """
                    UPDATE enrollments
                    SET midterm=?, final=?, total=?, incomplete=0
                    WHERE student_id=? AND course_id=? AND semester_id=? AND withdrawn=0;
                    """,
                    (
                        new_mid,
                        new_final,
                        total,
                        int(student_id),
                        int(course_id),
                        int(sem_id),
                    ),
                )
                conn.commit()
            return {"success": True, "message": "Grades updated.", "data": None}
        except sqlite3.Error as e:
            return {"success": False, "message": f"Database error: {e}", "data": None}
