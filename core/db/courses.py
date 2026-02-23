import sqlite3
from typing import List, Optional, Tuple

class CourseMixin:
    def add_course(self, code: str, title: str, instructor: str, max_seats: int) -> dict:
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO courses (code, title, instructor, max_seats) VALUES (?, ?, ?, ?);",
                    (str(code).upper(), str(title), str(instructor), int(max_seats)),
                )
                conn.commit()
            return {"success": True, "message": "Course added successfully.", "data": None}
        except sqlite3.IntegrityError as e:
            return {"success": False, "message": f"Error adding course: {e}", "data": None}
        except sqlite3.Error as e:
            return {"success": False, "message": f"Database error: {e}", "data": None}
#-----------------------------------------------------------------------------------------------------------------------------
    def find_course_id_by_code(self, code: str) -> Optional[int]:
        if not code:
            return None
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM courses WHERE code=?;", (str(code).upper(),))
            row = cur.fetchone()
            return int(row[0]) if row else None
#-----------------------------------------------------------------------------------------------------------------------------
    def get_all_courses_with_availability(self, semester_id: Optional[int] = None) -> List[Tuple]:
        sem_id = semester_id if semester_id is not None else self.get_active_semester_id()
        with self._connect() as conn:
            cur = conn.cursor()
            if sem_id is None:
                cur.execute(
                    """
                    SELECT code,
                        title,
                        instructor,
                        max_seats AS available,
                        max_seats
                    FROM courses
                    ORDER BY code;
                    """
                )
                return cur.fetchall()
            cur.execute(
                """
                SELECT c.code,
                    c.title,
                    c.instructor,
                    c.max_seats - COALESCE(e.count, 0) AS available,
                    c.max_seats
                FROM courses c
                LEFT JOIN (
                    SELECT course_id, COUNT(*) AS count
                    FROM enrollments
                    WHERE semester_id = ?
                    AND withdrawn = 0
                    GROUP BY course_id
                ) e ON c.id = e.course_id
                ORDER BY c.code;
                """,
                (int(sem_id),),
            )
            return cur.fetchall()
#-----------------------------------------------------------------------------------------------------------------------------

