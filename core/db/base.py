import sqlite3
from pathlib import Path
class BaseDB:
    def __init__(self, db_name: str = "university.db"):
        if Path(db_name).name != db_name:
             raise ValueError(f"Database name must be a simple filename, not a path: {db_name}")
            
        safe_db_name = db_name
        if not safe_db_name or safe_db_name.startswith('.'):
            raise ValueError(f"Invalid database name: {db_name}")
        
        base_dir = Path(__file__).resolve().parents[2]
        self.db_path = str((base_dir / safe_db_name).resolve())
        
        if not self.db_path.startswith(str(base_dir)):
            raise ValueError(f"Database path {self.db_path} is outside project directory")
        
        self.create_tables()
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------
    def create_tables(self) -> None:
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS students (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL COLLATE NOCASE UNIQUE
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS courses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code TEXT NOT NULL UNIQUE,
                        title TEXT NOT NULL,
                        instructor TEXT NOT NULL,
                        max_seats INTEGER NOT NULL CHECK (max_seats > 0)
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS semesters (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                        state TEXT NOT NULL CHECK(state IN ('OPEN','CLOSED'))
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS active_semester (
                        id INTEGER PRIMARY KEY CHECK(id = 1),
                        semester_id INTEGER NULL,
                        FOREIGN KEY (semester_id) REFERENCES semesters(id)
                    );
                    """
                )
                cur.execute("INSERT OR IGNORE INTO active_semester (id, semester_id) VALUES (1, NULL);")
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS semester_averages (
                        student_id INTEGER NOT NULL,
                        semester_id INTEGER NOT NULL,
                        average REAL CHECK (average IS NULL OR (average BETWEEN 0 AND 100)),
                        PRIMARY KEY (student_id, semester_id),
                        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                        FOREIGN KEY (semester_id) REFERENCES semesters(id) ON DELETE CASCADE
                    );
                    """
                )
                self._create_enrollments_table(cur)
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_enrollments_semester
                    ON enrollments(semester_id);
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_enrollments_course_semester
                    ON enrollments(course_id, semester_id);
                    """
                )

                conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(
                f"Failed to initialize the database. The disk may be full or the file may be corrupted.\n"
                f"Details: {e}"
            ) from e
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------
    def _create_enrollments_table(self, cur: sqlite3.Cursor) -> None:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS enrollments (
                student_id INTEGER NOT NULL,
                course_id  INTEGER NOT NULL,
                semester_id INTEGER NOT NULL,

                midterm REAL CHECK (midterm IS NULL OR (midterm BETWEEN 0 AND 40)),
                final REAL CHECK (final IS NULL OR (final BETWEEN 0 AND 60)),
                total REAL CHECK (total IS NULL OR (total BETWEEN 0 AND 100)),

                withdrawn INTEGER NOT NULL DEFAULT 0 CHECK (withdrawn IN (0,1)),
                incomplete INTEGER NOT NULL DEFAULT 0 CHECK (incomplete IN (0,1)),

                PRIMARY KEY (student_id, course_id, semester_id),
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id)  REFERENCES courses(id) ON DELETE CASCADE,
                FOREIGN KEY (semester_id) REFERENCES semesters(id) ON DELETE CASCADE
            );
            """
        )
