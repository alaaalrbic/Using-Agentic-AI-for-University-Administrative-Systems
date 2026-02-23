
import json
import unittest
import asyncio
import sys
from mcp_server import mcp

class TestMCPServer(unittest.TestCase):
    """
    Tests for the MCP server tools and resources.
    Uses asyncio.run() to call async FastMCP methods.
    """

    @classmethod
    def setUpClass(cls):
        print("\nSetting up TestMCPServer...")
        try:
            # Fetch tools/resources
            t_coro = mcp.get_tools()
            cls.all_tools = asyncio.run(t_coro) if asyncio.iscoroutine(t_coro) else t_coro
            
            r_coro = mcp.get_resources()
            cls.all_resources = asyncio.run(r_coro) if asyncio.iscoroutine(r_coro) else r_coro
            
            # Map tools correctly
            cls.tools = {}
            if isinstance(cls.all_tools, dict):
                cls.tools = cls.all_tools
            elif isinstance(cls.all_tools, list):
                for t in cls.all_tools:
                    if hasattr(t, 'name'):
                        cls.tools[t.name] = t
                    elif isinstance(t, str):
                        cls.tools[t] = t
            
            # Map resources correctly
            cls.resources = {}
            if isinstance(cls.all_resources, dict):
                cls.resources = {str(k): v for k, v in cls.all_resources.items()}
            elif isinstance(cls.all_resources, list):
                for r in cls.all_resources:
                    if hasattr(r, 'uri_template'):
                        cls.resources[str(r.uri_template)] = r
                    elif isinstance(r, str):
                        cls.resources[r] = r

            print(f"Mapped Tools: {list(cls.tools.keys())}")
            print(f"Mapped Resources: {list(cls.resources.keys())}")

        except Exception as e:
            print(f"FATAL Setup Error: {e}")
            sys.exit(1)

    def call_tool(self, tool_name, **kwargs):
        """Renamed first arg to tool_name to avoid collision with tool params like 'name'"""
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool {tool_name} not found.")
        
        fn = getattr(tool, 'fn', tool)
        
        if asyncio.iscoroutinefunction(fn):
            return asyncio.run(fn(**kwargs))
        else:
            return fn(**kwargs)

    def call_resource(self, uri):
        res = self.resources.get(uri)
        if not res:
            raise ValueError(f"Resource {uri} not found.")
        
        fn = getattr(res, 'fn', res)
        
        if asyncio.iscoroutinefunction(fn):
            return asyncio.run(fn())
        else:
            return fn()

    def test_01_list_students(self):
        print("\nTesting list_students...")
        result = self.call_tool("list_students")
        self.assertIsInstance(result, list)

    def test_02_search_students(self):
        print("\nTesting search_students...")
        result = self.call_tool("search_students", query="NonExistentStudent123")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_03_list_courses(self):
        print("\nTesting list_courses...")
        result = self.call_tool("list_courses")
        self.assertIsInstance(result, list)

    def test_04_semester_tools(self):
        print("\nTesting semester tools...")
        name = "Test Semester 2026"
        res = self.call_tool("add_semester", name=name)
        self.assertIn("success", res)
        
        semesters = self.call_tool("list_semesters")
        self.assertIsInstance(semesters, list)
        
        active = self.call_tool("get_active_semester")
        self.assertIn("id", active)

    def test_05_student_and_course_addition(self):
        print("\nTesting add_student and add_course...")
        # Add student
        res_student = self.call_tool("add_student", name="Test User", student_id=9999)
        self.assertIn("success", res_student)
        
        # Add course
        res_course = self.call_tool("add_course", code="TEST101", title="Test Course", instructor="Test Instructor", max_seats=10)
        self.assertIn("success", res_course)

    def test_06_resources(self):
        print("\nTesting resources...")
        res_students = self.call_resource("university://students")
        students_data = json.loads(res_students)
        self.assertIsInstance(students_data, list)
        
        res_courses = self.call_resource("university://courses")
        courses_data = json.loads(res_courses)
        self.assertIsInstance(courses_data, list)

    def test_07_enrollment_flow(self):
        print("\nTesting enrollment flow...")
        # Ensure student 9999 and course TEST101 exist (added in test_05)
        active = self.call_tool("get_active_semester")
        sem_id = active.get("id")
        
        if sem_id:
            # Try to enroll
            res_enroll = self.call_tool("enroll", student_id=9999, course_code="TEST101", semester_id=sem_id)
            print(f"Enrollment result: {res_enroll.get('message')}")
            self.assertTrue(res_enroll.get("success"), f"Enrollment failed: {res_enroll.get('message')}")
            
            # Check enrollments
            enrollments = self.call_tool("get_student_enrollments", student_id=9999, semester_id=sem_id)
            self.assertIsInstance(enrollments, list)
            
            # Try to drop
            res_drop = self.call_tool("drop", student_id=9999, course_code="TEST101", semester_id=sem_id)
            self.assertIsInstance(res_drop, dict)
            self.assertTrue(res_drop.get("success"), f"Drop failed: {res_drop.get('message')}")

if __name__ == "__main__":
    unittest.main()
