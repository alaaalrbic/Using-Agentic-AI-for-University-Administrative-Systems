import sqlite3
from typing import List, Tuple, Optional
from core.semester_rules import (
    can_close_semester,
    calculate_semester_average,
)


class SemesterMixin:
    def create_semester(self, name: str) -> dict:
        name_clean = str(name).strip()
        if not name_clean:
            return {"success": False, "message": "Semester name cannot be empty.", "data": None}

        try:
            with self._connect() as conn:
                cur = conn.cursor()
                # Case-insensitive unique check
                cur.execute("SELECT 1 FROM semesters WHERE LOWER(name)=LOWER(?)", (name_clean,))
                if cur.fetchone():
                    return {"success": False, "message": f"Semester '{name_clean}' already exists.", "data": None}

                # Create semester (default state: OPEN)
                cur.execute(
                    "INSERT INTO semesters (name, state) VALUES (?, 'OPEN');",
                    (name_clean,),
                )
                sem_id = int(cur.lastrowid)

                # Set this semester as the active one (active_semester table)
                cur.execute(
                    """
                    INSERT INTO active_semester (id, semester_id)
                    VALUES (1, ?)
                    ON CONFLICT(id) DO UPDATE SET semester_id=excluded.semester_id;
                    """,
                    (sem_id,),
                )

                conn.commit()
            return {"success": True, "message": "Semester created and set as active.", "data": {"id": sem_id}}
        except sqlite3.IntegrityError:
            return {"success": False, "message": "A semester with this name already exists.", "data": None}
        except sqlite3.Error as e:
            return {"success": False, "message": f"Database error: {e}", "data": None}

    # --------------------------------------------------------------------------------------
    def list_semesters(self) -> List[Tuple[int, str, str]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name, state FROM semesters ORDER BY id;")
            return cur.fetchall()

    # --------------------------------------------------------------------------------------
    def get_semester_state(self, semester_id: int) -> Optional[str]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT state FROM semesters WHERE id=?;", (int(semester_id),))
            row = cur.fetchone()
            return str(row[0]) if row else None

    # --------------------------------------------------------------------------------------
    def set_active_semester(self, semester_id: Optional[int]) -> dict:
        with self._connect() as conn:
            cur = conn.cursor()

            if semester_id is None:
                cur.execute("DELETE FROM active_semester;")
                conn.commit()
                return {"success": True, "message": "Active semester cleared.", "data": None}

            # Verify semester exists
            cur.execute("SELECT 1 FROM semesters WHERE id=?;", (int(semester_id),))
            if not cur.fetchone():
                return {"success": False, "message": "Semester not found.", "data": None}

            # Store as active semester
            cur.execute(
                """
                INSERT INTO active_semester (id, semester_id)
                VALUES (1, ?)
                ON CONFLICT(id) DO UPDATE SET semester_id=excluded.semester_id;
                """,
                (int(semester_id),),
            )

            conn.commit()
        return {"success": True, "message": "Active semester updated.", "data": None}

    # --------------------------------------------------------------------------------------
    def get_active_semester_id(self) -> Optional[int]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT semester_id FROM active_semester WHERE id=1;")
            row = cur.fetchone()
            if not row or row[0] is None:
                return None
            try:
                return int(row[0])
            except ValueError:
                return None

    # --------------------------------------------------------------------------------------
    def close_semester(self, semester_id: int) -> dict:
        sem_id = int(semester_id)
        try:
            with self._connect() as conn:
                cur = conn.cursor()

                cur.execute("SELECT state FROM semesters WHERE id=?;", (sem_id,))
                row = cur.fetchone()
                if not row:
                    return {"success": False, "message": "Semester not found.", "data": None}

                state = str(row[0]).upper()
                if state == "CLOSED":
                    return {"success": False, "message": "Semester already CLOSED.", "data": None}

                # Fetch semester enrollments for validation
                cur.execute(
                    """
                    SELECT student_id, course_id, midterm, final, withdrawn, incomplete
                    FROM enrollments
                    WHERE semester_id=?;
                    """,
                    (sem_id,),
                )
                enrolls = [
                    {
                        "student_id": r[0],
                        "course_id": r[1],
                        "midterm": r[2],
                        "final": r[3],
                        "withdrawn": r[4],
                        "incomplete": r[5],
                    }
                    for r in cur.fetchall()
                ]

                ok, msg = can_close_semester(enrolls)
                if not ok:
                    return {"success": False, "message": msg, "data": None}

                # Calculate average grade for each student in this semester
                cur.execute(
                    "SELECT DISTINCT student_id FROM enrollments WHERE semester_id=?;",
                    (sem_id,),
                )
                student_ids = [int(r[0]) for r in cur.fetchall()]

                for sid in student_ids:
                    cur.execute(
                        """
                        SELECT total
                        FROM enrollments
                        WHERE semester_id=? AND student_id=?
                          AND withdrawn=0 AND incomplete=0
                          AND total IS NOT NULL;
                        """,
                        (sem_id, sid),
                    )
                    totals = [r[0] for r in cur.fetchall()]
                    avg = calculate_semester_average(totals)

                    cur.execute(
                        """
                        INSERT OR REPLACE INTO semester_averages (student_id, semester_id, average)
                        VALUES (?, ?, ?);
                        """,
                        (sid, sem_id, None if avg is None else float(avg)),
                    )

                # Close the semester
                cur.execute("UPDATE semesters SET state='CLOSED' WHERE id=?;", (sem_id,))

                # If this was the active semester, clear active_semester (no active semester)
                cur.execute("SELECT semester_id FROM active_semester WHERE id=1;")
                active = cur.fetchone()
                if active and active[0] == sem_id:
                    cur.execute("UPDATE active_semester SET semester_id=NULL WHERE id=1;")

                conn.commit()
            return {"success": True, "message": "Semester CLOSED. Averages calculated.", "data": None}
        except sqlite3.Error as e:
            return {"success": False, "message": f"Database error: {e}", "data": None}

    # --------------------------------------------------------------------------------------
    def get_semester_average(self, student_id: int, semester_id: int) -> Optional[float]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT average FROM semester_averages WHERE student_id=? AND semester_id=?;",
                (int(student_id), int(semester_id)),
            )
            row = cur.fetchone()
            return float(row[0]) if row and row[0] is not None else None

    # --------------------------------------------------------------------------------------
    def get_semester_summary_data(self, semester_id: int):
        if not semester_id:
            return []
        with self._connect() as conn:
            cur = conn.cursor()
            sql = """
            SELECT s.name, AVG(e.total) as avg_grade, COUNT(e.course_id) as course_count
            FROM enrollments e
            JOIN students s ON s.id = e.student_id
            WHERE e.semester_id = ?
              AND e.withdrawn = 0
              AND e.total IS NOT NULL
            GROUP BY s.id, s.name
            ORDER BY avg_grade DESC
            """
            cur.execute(sql, (semester_id,))
            rows = cur.fetchall()

            data = []
            for r in rows:
                data.append({
                    "student": r[0],
                    "average": round(r[1], 2) if r[1] is not None else None,
                    "course_count": r[2]
                })
            return data
