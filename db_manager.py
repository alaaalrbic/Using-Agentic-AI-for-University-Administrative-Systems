from core.db.base import BaseDB
from core.db.students import StudentMixin
from core.db.courses import CourseMixin
from core.db.semesters import SemesterMixin
from core.db.enrollments import EnrollmentMixin

class DatabaseManager(BaseDB, StudentMixin, CourseMixin, SemesterMixin, EnrollmentMixin):
    pass
