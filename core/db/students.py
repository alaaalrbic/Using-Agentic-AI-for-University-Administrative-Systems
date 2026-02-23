import sqlite3
from typing import List, Tuple

class StudentMixin:
    def get_students(self) -> List[Tuple[int, str]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM students ORDER BY id;")
            return cur.fetchall()
#-----------------------------------------------------------------------------------------------------------------------------
    def add_student_with_id(self, sid: int | None, name: str) -> dict:
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                if sid is not None:
                    cur.execute("INSERT INTO students (id, name) VALUES (?, ?);", (int(sid), str(name)))
                else:
                    cur.execute("INSERT INTO students (name) VALUES (?);", (str(name),))
                conn.commit()
            return {"success": True, "message": "Student added successfully.", "data": None}
        except sqlite3.IntegrityError as e:
            return {"success": False, "message": f"Error adding student: {e}", "data": None}
        except sqlite3.Error as e:
            return {"success": False, "message": f"Database error: {e}", "data": None}
#-----------------------------------------------------------------------------------------------------------------------------
    def search_students_by_name(self, query: str) -> List[Tuple[int, str]]:
        if not query:
            return []
        q = f"%{query}%"
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM students WHERE name LIKE ? ORDER BY name LIMIT 10;", (q,))
            return cur.fetchall()
#-----------------------------------------------------------------------------------------------------------------------------

