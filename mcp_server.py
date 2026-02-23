from fastmcp import FastMCP
from db_manager import DatabaseManager
from typing import Optional
import json
import os
DB_NAME = os.getenv("MCP_DB_NAME", "university.db")
db = DatabaseManager(db_name=DB_NAME)
mcp = FastMCP("university-system")


@mcp.tool()
def list_students() -> list[dict]:
    """
    Get a list of all registered students in the university system.
    
    Returns:
        List of dictionaries containing student ID and name fields.
    """
    rows = db.get_students()
    return [{"id": int(sid), "name": name} for (sid, name) in rows]


@mcp.tool()
def search_students(query: str) -> list[dict]:
    """
    Search for students by name or partial name match.
    
    Args:
        query: Search string to match against student names (case-insensitive).
        
    Returns:
        List of matching students with ID and name fields.
    """
    if not query or not query.strip():
        return []
    results = db.search_students_by_name(query.strip())
    return [{"id": int(sid), "name": name} for (sid, name) in results]

@mcp.tool()
def list_courses() -> list[dict]:
    """
    Get a list of all courses with availability information.
    
    Returns:
        List of dictionaries containing course code, title, instructor,
        available seats, and maximum seats.
    """
    rows = db.get_all_courses_with_availability()
    return [
        {"code": code, "title": title, "instructor": instructor, "available": int(avail), "max_seats": int(max_seats)}
        for (code, title, instructor, avail, max_seats) in rows
    ]

# ---------------------- Semester tools ----------------------
@mcp.tool()
def add_semester(name: str) -> dict:
    """
    Create a new academic semester.
    
    Args:
        name: Name of the semester (e.g., "Fall 2024", "Spring 2025").
        
    Returns:
        Dictionary with 'success' boolean and 'message' string.
    """
    if not name or not name.strip():
        return {"success": False, "message": "Semester name cannot be empty."}
    return db.create_semester(str(name).strip())


@mcp.tool()
def list_semesters() -> list[dict]:
    """
    Get a list of all semesters with their states and active status.
    
    Returns:
        List of dictionaries containing semester ID, name, state, and is_active flag.
    """
    rows = db.list_semesters()
    active_id = db.get_active_semester_id()
    return [
        {"id": int(sid), "name": str(name), "state": str(state), "is_active": (int(sid) == int(active_id or -1))}
        for (sid, name, state) in rows
    ]


@mcp.tool()
def get_active_semester() -> dict:
    """
    Get information about the currently active semester.
    
    Returns:
        Dictionary with semester ID, name, and state. Returns {"id": None} if no active semester.
    """
    sid = db.get_active_semester_id()
    if sid is None:
        return {"id": None}
    state = db.get_semester_state(int(sid))
    # Find name
    semesters = db.list_semesters()
    name = None
    for _id, _name, _state in semesters:
        if int(_id) == int(sid):
            name = _name
            break
    return {"id": int(sid), "name": name, "state": state}


@mcp.tool()
def set_active_semester(semester_id: Optional[int]) -> dict:
    """
    Set a specific semester as the active semester. Pass None or 0 to clear.
    
    Args:
        semester_id: The ID of the semester to make active.
        
    Returns:
        Dictionary with 'success' boolean and 'message' string.
    """
    if semester_id is None or int(semester_id) <= 0:
         return db.set_active_semester(None)
    return db.set_active_semester(int(semester_id))


@mcp.tool()
def close_semester(semester_id: int) -> dict:
    """
    Mark a semester as closed, preventing further enrollments.
    
    Args:
        semester_id: The ID of the semester to close.
        
    Returns:
        Dictionary with 'success' boolean and 'message' string.
    """
    if int(semester_id) <= 0:
         return {"success": False, "message": "Invalid semester ID."}
    return db.close_semester(int(semester_id))


# ---------------------- Enrollment tools ----------------------
@mcp.tool()
def get_student_enrollments(student_id: int, semester_id: Optional[int] = None) -> list[dict]:
    """
    Get all courses a student is enrolled in for a specific semester.
    
    Args:
        student_id: The unique identifier of the student.
        semester_id: Optional semester ID (defaults to active semester if not specified).
        
    Returns:
        List of enrolled courses with code, title, midterm, final, and total grades.
    """
    if int(student_id) <= 0:
        return []
    if semester_id is not None and int(semester_id) <= 0:
        return []
        
    rows = db.get_enrolled_courses_for_student(int(student_id), semester_id=semester_id)
    # rows: code, title, midterm, final, total
    result = []
    for (code, title, midterm, final, total) in rows:
        result.append(
            {
                "code": code,
                "title": title,
                "midterm": midterm,
                "final": final,
                "total": total,
            }
        )
    return result


@mcp.tool()
def enroll(student_id: int, course_code: str, semester_id: Optional[int] = None) -> dict:
    """
    Enroll a student in a course for the specified semester.
    
    Args:
        student_id: The unique identifier of the student.
        course_code: The course code (e.g., 'CS101').
        semester_id: Optional semester ID (defaults to active semester if not specified).
        
    Returns:
        Dictionary with 'success' boolean and 'message' string.
    """
    if int(student_id) <= 0:
        return {"success": False, "message": "Invalid student ID."}
    
    code = str(course_code).strip().upper()
    if not code:
        return {"success": False, "message": "Course code cannot be empty."}
        
    if semester_id is not None and int(semester_id) <= 0:
        return {"success": False, "message": "Invalid semester ID."}

    course_id = db.find_course_id_by_code(code)
    if course_id is None:
        return {"success": False, "message": f"Course '{code}' not found."}
    return db.enroll_student_in_course(int(student_id), int(course_id), semester_id=semester_id)


@mcp.tool()
def drop(student_id: int, course_code: str, semester_id: Optional[int] = None) -> dict:
    """
    Remove a student from a course in the specified semester.
    
    Args:
        student_id: The unique identifier of the student.
        course_code: The course code to drop from (e.g., 'CS101').
        semester_id: Optional semester ID (defaults to active semester if not specified).
        
    Returns:
        Dictionary with 'success' boolean and 'message' string.
    """
    if int(student_id) <= 0:
        return {"success": False, "message": "Invalid student ID."}

    code = str(course_code).strip().upper()
    if not code:
        return {"success": False, "message": "Course code cannot be empty."}

    course_id = db.find_course_id_by_code(code)
    if course_id is None:
        return {"success": False, "message": f"Course '{code}' not found."}
    return db.drop_student_from_course(int(student_id), int(course_id), semester_id=semester_id)


@mcp.tool()
def set_course_grade(
    student_id: int,
    course_code: str,
    midterm: Optional[float] = None,
    final: Optional[float] = None,
    semester_id: Optional[int] = None,
) -> dict:
    """
    Set or update grades for a student in a specific course.
    
    Args:
        student_id: The unique identifier of the student.
        course_code: The course code (e.g., 'CS101').
        midterm: Optional midterm grade (0-40).
        final: Optional final exam grade (0-60).
        semester_id: Optional semester ID (defaults to active semester if not specified).
        
    Returns:
        Dictionary with 'success' boolean and 'message' string.
    """
    if int(student_id) <= 0:
        return {"success": False, "message": "Invalid student ID."}

    code = str(course_code).strip().upper()
    if not code:
        return {"success": False, "message": "Course code cannot be empty."}
        
    # Validation: Grade ranges
    if midterm is not None:
        if not (0 <= midterm <= 40):
            return {"success": False, "message": "Midterm grade must be between 0 and 40."}
    
    if final is not None:
        if not (0 <= final <= 60):
            return {"success": False, "message": "Final grade must be between 0 and 60."}

    course_id = db.find_course_id_by_code(code)
    if course_id is None:
        return {"success": False, "message": f"Course '{code}' not found."}
    return db.update_course_grade(
        int(student_id),
        int(course_id),
        semester_id=semester_id,
        midterm=midterm,
        final=final,
    )


@mcp.tool()
def get_semester_average(student_id: int, semester_id: Optional[int] = None) -> dict:
    """
    Calculate a student's average grade for a specific semester.
    
    Args:
        student_id: The unique identifier of the student.
        semester_id: Optional semester ID (defaults to active semester if not specified).
        
    Returns:
        Dictionary with student_id, semester_id, and average grade.
    """
    if int(student_id) <= 0:
         return {"student_id": int(student_id), "semester_id": None, "average": None}
         
    if semester_id is not None:
        sem_id = int(semester_id)
    else:
        sem_id = db.get_active_semester_id()
        if sem_id is None:
            return {"student_id": int(student_id), "semester_id": None, "average": None}

    avg = db.get_semester_average(int(student_id), int(sem_id))
    return {"student_id": int(student_id), "semester_id": int(sem_id), "average": avg}


@mcp.tool()
def get_semester_summary_data(semester_id: int) -> list[dict]:
    """
    Get a comprehensive summary of all students' performance in a semester.
    
    Args:
        semester_id: The ID of the semester to summarize.
        
    Returns:
        List of dictionaries with student information and their average grades.
    """
    if int(semester_id) <= 0:
        return []
    return db.get_semester_summary_data(int(semester_id))


# ---------------------- Admin data tools ----------------------
@mcp.tool()
def add_course(code: str, title: str, instructor: str, max_seats: int) -> dict:
    """
    Create a new course in the system.
    
    Args:
        code: Course code (e.g., 'CS101'). Will be automatically uppercased.
        title: Full title of the course.
        instructor: Name of the course instructor.
        max_seats: Maximum number of students that can enroll.
        
    Returns:
        Dictionary with 'success' boolean and 'message' string.
    """
    clean_code = str(code).strip().upper()
    if not clean_code:
        return {"success": False, "message": "Course code cannot be empty."}
        
    if int(max_seats) <= 0:
        return {"success": False, "message": "Max seats must be greater than 0."}
        
    return db.add_course(clean_code, str(title).strip(), str(instructor).strip(), int(max_seats))


@mcp.tool()
def add_student(name: str, student_id: int = None) -> dict:
    """
    Register a brand new student in the university system.
    
    Args:
        name: Full name of the student.
        student_id: Optional student ID. If not provided, one will be auto-assigned.
        
    Returns:
        Dictionary with 'success' boolean and 'message' string.
    """
    if not name or not name.strip():
        return {"success": False, "message": "Student name cannot be empty."}
        
    if student_id is not None and int(student_id) <= 0:
        return {"success": False, "message": "Invalid student ID."}
        
    return db.add_student_with_id(student_id, str(name).strip())

# ---------------------- MCP Resources ----------------------
@mcp.resource("university://students")
def get_student_list() -> str:
    """
    Provides a complete list of all registered students in the system.
    
    Returns JSON array with student ID and name fields.
    Updated in real-time with database changes.
    
    Intended audience: LLM assistant
    Priority: High (0.9) - Critical for context awareness
    """
    students = db.get_students()
    return json.dumps([{"id": sid, "name": name} for (sid, name) in students])


@mcp.resource("university://courses")
def get_course_list() -> str:
    """
    Provides the complete course catalog with instructor information.
    
    Returns JSON array with course code, title, and instructor fields.
    Updated in real-time with database changes.
    
    Intended audience: LLM assistant
    Priority: High (0.9) - Critical for course-related queries
    """
    courses = db.get_all_courses_with_availability()
    return json.dumps([
        {"code": code, "title": title, "instructor": instructor} 
        for (code, title, instructor, _, _) in courses
    ])

 

if __name__ == "__main__":
    mcp.run()
