from __future__ import annotations
from typing import Iterable, Optional, Tuple, Dict


PASS_MARK_DEFAULT = 50.0


def is_semester_open(state: str) -> bool:
    return str(state).upper() == "OPEN"
#-------------------------------------------------------------------------------------
def ensure_semester_open(state: str) -> Tuple[bool, str]:
    if not is_semester_open(state):
        return False, "Semester is CLOSED. This action is not allowed."
    return True, ""
#-------------------------------------------------------------------------------------
def compute_total(midterm: Optional[float], final: Optional[float]) -> Optional[float]:
    if midterm is None and final is None:
        return None
    m = float(midterm or 0)
    f = float(final or 0)
    return m + f
#-------------------------------------------------------------------------------------
def enrollment_is_finished(e: Dict) -> bool:
    if int(e.get("withdrawn", 0) or 0) == 1:
        return True
    if int(e.get("incomplete", 0) or 0) == 1:
        return True
    return e.get("midterm") is not None and e.get("final") is not None
#-------------------------------------------------------------------------------------
def can_close_semester(enrollments: Iterable[Dict]) -> Tuple[bool, str]:
    for e in enrollments:
        if not enrollment_is_finished(e):
            return False, "Cannot close semester: some courses still have missing grades."
    return True, ""
#-------------------------------------------------------------------------------------
def calculate_semester_average(totals: Iterable[Optional[float]]) -> Optional[float]:
    values = [float(t) for t in totals if t is not None]
    if not values:
        return None
    return sum(values) / len(values)
#-------------------------------------------------------------------------------------
def check_max_courses(count_current: int, max_allowed: int = 4) -> Tuple[bool, str]:
    if count_current >= max_allowed:
        return False, f"Maximum {max_allowed} courses per student in a semester."
    return True, ""
#-------------------------------------------------------------------------------------
def check_not_passed_before(passed_before: bool) -> Tuple[bool, str]:
    if passed_before:
        return False, "Cannot enroll: student already passed this course in a previous semester."
    return True, ""
#-------------------------------------------------------------------------------------
def check_not_taken_this_semester(already_taken_this_semester: bool) -> Tuple[bool, str]:
    if already_taken_this_semester:
        return False, "Cannot retake the same course within the same semester."
    return True, ""
