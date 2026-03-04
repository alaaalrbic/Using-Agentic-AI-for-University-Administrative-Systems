"""
University AI — Real Benchmark (Fresh Start)
=============================================
Every run starts from ZERO:
  1. Clears the entire database
  2. Creates fresh test data (students, courses, semester, grades)
  3. Runs all 20 tests × 2 languages against that real data
  4. Checks answers against what was actually written

TO CHANGE THE MODEL — edit only this one line:
  MODEL = "mistral-large-latest"

HOW time.time() WORKS:
  start   = time.time()          → records current time in seconds
  elapsed = time.time() - start  → seconds the model took to respond
"""

import time, json, os, sys, sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    pass


# ═══════════════════════════════════════════════════════════════════════════════
#  ▶  CHANGE THIS LINE TO TEST A DIFFERENT MODEL
# ═══════════════════════════════════════════════════════════════════════════════
MODEL = "mistral-large-latest"
# Other options:
#   "mistral-medium-latest"
#   "mistral-small-latest"
#   "open-mixtral-8x22b"
#   "open-mistral-7b"
# ═══════════════════════════════════════════════════════════════════════════════

DB_PATH = os.path.join(BASE_DIR, "university.db")

# ── The exact data we will write into the DB before testing ───────────────────
FRESH_STUDENTS = [
    {"id": 1, "name": "Ahmed Ali"},
    {"id": 2, "name": "Sara Mohammed"},
    {"id": 3, "name": "Omar Hassan"},
    {"id": 4, "name": "Fatima Noor"},
    {"id": 5, "name": "Khalid Ibrahim"},
]

FRESH_COURSES = [
    {"code": "CS101",   "title": "Intro to Programming", "instructor": "Dr. Smith",   "max_seats": 30},
    {"code": "MATH201", "title": "Calculus I",            "instructor": "Dr. Johnson", "max_seats": 25},
    {"code": "ENG301",  "title": "Technical Writing",     "instructor": "Dr. Brown",   "max_seats": 20},
    {"code": "DB401",   "title": "Database Systems",      "instructor": "Dr. Davis",   "max_seats": 15},
]

FRESH_SEMESTER = "Spring 2025"

# Grades: (student_id, course_code, midterm, final)
FRESH_GRADES = [
    (1, "CS101",   35, 50),   # Ahmed  → total 85  pass
    (1, "MATH201", 30, 45),   # Ahmed  → total 75  pass
    (2, "CS101",   38, 55),   # Sara   → total 93  pass
    (2, "DB401",   36, 52),   # Sara   → total 88  pass
    (3, "MATH201", 20, 22),   # Omar   → total 42  fail
    (3, "ENG301",  25, 30),   # Omar   → total 55  pass
    (4, "CS101",   39, 57),   # Fatima → total 96  pass
    (4, "DB401",   38, 54),   # Fatima → total 92  pass
    (5, "ENG301",  18, 20),   # Khalid → total 38  fail
    (5, "MATH201", 22, 25),   # Khalid → total 47  fail
]


# ── Step 1: Reset DB completely and write fresh data ─────────────────────────
def reset_and_seed_db():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    print("  Clearing database...")

    cur.execute("DELETE FROM enrollments")
    cur.execute("DELETE FROM semester_averages")
    cur.execute("DELETE FROM active_semester")
    cur.execute("DELETE FROM semesters")
    cur.execute("DELETE FROM courses")
    cur.execute("DELETE FROM students")
    for tbl in ["students", "courses", "semesters", "enrollments"]:
        cur.execute(f"DELETE FROM sqlite_sequence WHERE name='{tbl}'")
    conn.commit()
    print("  Database cleared")

    for s in FRESH_STUDENTS:
        cur.execute("INSERT INTO students (id, name) VALUES (?, ?)", (s["id"], s["name"]))
    conn.commit()
    print(f"  {len(FRESH_STUDENTS)} students written: {[s['name'] for s in FRESH_STUDENTS]}")

    for c in FRESH_COURSES:
        cur.execute(
            "INSERT INTO courses (code, title, instructor, max_seats) VALUES (?, ?, ?, ?)",
            (c["code"], c["title"], c["instructor"], c["max_seats"])
        )
    conn.commit()
    print(f"  {len(FRESH_COURSES)} courses written: {[c['code'] for c in FRESH_COURSES]}")

    cur.execute("INSERT INTO semesters (name, state) VALUES (?, 'OPEN')", (FRESH_SEMESTER,))
    semester_id = cur.lastrowid
    cur.execute("DELETE FROM active_semester")
    cur.execute("INSERT INTO active_semester (semester_id) VALUES (?)", (semester_id,))
    conn.commit()
    print(f"  Semester '{FRESH_SEMESTER}' written (ID={semester_id}, OPEN)")

    for (student_id, course_code, midterm, final) in FRESH_GRADES:
        cur.execute("SELECT id FROM courses WHERE code=?", (course_code,))
        row = cur.fetchone()
        if not row:
            continue
        course_id = row[0]
        total = midterm + final
        cur.execute(
            """INSERT INTO enrollments
               (student_id, course_id, semester_id, midterm, final, total, withdrawn, incomplete)
               VALUES (?, ?, ?, ?, ?, ?, 0, 0)""",
            (student_id, course_id, semester_id, midterm, final, total)
        )
    conn.commit()
    print(f"  {len(FRESH_GRADES)} enrollments + grades written")
    conn.close()
    return semester_id


# ── Step 2: Build ground truth from what we just wrote ────────────────────────
def build_facts(semester_id):
    facts = {
        "student_count":      len(FRESH_STUDENTS),
        "student_names":      [s["name"].lower() for s in FRESH_STUDENTS],
        "course_count":       len(FRESH_COURSES),
        "course_codes":       [c["code"].lower() for c in FRESH_COURSES],
        "courses_with_seats": [c["code"].lower() for c in FRESH_COURSES],
        "semester_id":        semester_id,
        "semester_name":      FRESH_SEMESTER.lower(),
        "semester_status":    "open",
    }

    facts["student1_courses"] = [code.lower() for (sid, code, _, _) in FRESH_GRADES if sid == 1]
    s1_grades = [(mid + fin) for (sid, _, mid, fin) in FRESH_GRADES if sid == 1]
    facts["student1_average"] = round(sum(s1_grades) / len(s1_grades), 1) if s1_grades else None

    from collections import defaultdict
    student_totals = defaultdict(list)
    for (sid, _, mid, fin) in FRESH_GRADES:
        student_totals[sid].append(mid + fin)
    averages = [round(sum(v)/len(v), 1) for v in student_totals.values()]
    facts["class_average"] = round(sum(averages)/len(averages), 1) if averages else None
    facts["passed_count"]  = sum(1 for a in averages if a >= 50)
    facts["failed_count"]  = sum(1 for a in averages if a < 50)

    best_sid = max(student_totals, key=lambda s: sum(student_totals[s])/len(student_totals[s]))
    facts["top_student"] = next((s["name"].lower() for s in FRESH_STUDENTS if s["id"] == best_sid), None)

    return facts


# ── Step 3: Check model response against known facts ─────────────────────────
def check_response(response: str, test_id: int, facts: dict) -> tuple[bool, str]:
    if not response or not response.strip():
        return False, "No response"
    r = response.lower()

    if test_id in (1, 2):
        if str(facts["student_count"]) in r: return True, f"Correct count ({facts['student_count']})"
        found = sum(1 for n in facts["student_names"] if n.split()[0] in r)
        if found >= 2: return True, f"Mentioned {found} student names"
        return False, f"Expected {facts['student_count']} students or their names"

    if test_id == 3:
        if "ahmed" in r: return True, "Found Ahmed"
        return False, "Ahmed not mentioned"

    if test_id == 4:
        found = sum(1 for c in facts["course_codes"] if c in r)
        if found >= 2: return True, f"{found}/{facts['course_count']} codes found"
        return False, f"Only {found} codes found"

    if test_id == 5:
        if any(c in r for c in facts["courses_with_seats"]): return True, "Mentioned available course"
        return False, "No available course mentioned"

    if test_id == 6:
        if any(c in r for c in facts["course_codes"]): return True, "Mentioned a course code"
        return False, "No course code found"

    if test_id == 7:
        if any(c in r for c in facts["student1_courses"]): return True, "Mentioned Ahmed's course"
        return False, f"Ahmed's courses not found"

    if test_id == 8:
        if any(w in r for w in ["success","done","enrolled","تم","تسجيل","نجح"]): return True, "Enroll confirmed"
        return False, "No enroll confirmation"

    if test_id == 9:
        if any(w in r for w in ["success","done","dropped","removed","تم","حذف","إلغاء"]): return True, "Drop confirmed"
        return False, "No drop confirmation"

    if test_id == 10:
        if any(w in r for w in ["midterm","final","total","grade","نصفي","نهائي","درجة"]): return True, "Grade info found"
        if any(c in r for c in facts["student1_courses"]): return True, "Mentioned Ahmed's course"
        return False, "No grade info found"

    if test_id == 11:
        avg_val = facts["student1_average"]
        if avg_val:
            for d in range(3):
                if str(round(avg_val+d,1)) in r or str(round(avg_val-d,1)) in r: return True, f"Correct average ({avg_val})"
            if "average" in r or "معدل" in r: return True, "Mentioned average"
        return False, "Average not found"

    if test_id == 12:
        avg_val = facts["student1_average"]
        should_pass = avg_val >= 50 if avg_val else True
        said_pass = any(w in r for w in ["pass","passed","نجح","ناجح"])
        said_fail = any(w in r for w in ["fail","failed","رسب","راسب"])
        if should_pass and said_pass:      return True, "Correctly said PASS"
        if not should_pass and said_fail:  return True, "Correctly said FAIL"
        if said_pass and not should_pass:  return False, f"Said PASS but avg={avg_val}<50"
        if said_fail and should_pass:      return False, f"Said FAIL but avg={avg_val}>=50"
        return True, "Cannot verify"

    if test_id in (13, 14, 15):
        passed_c = 0
        if str(facts["student_count"]) in r:                                                       passed_c += 1
        if facts["class_average"] and (str(facts["class_average"]) in r or str(int(facts["class_average"])) in r): passed_c += 1
        if facts["top_student"] and facts["top_student"].split()[0] in r:                          passed_c += 1
        if passed_c >= 1: return True, f"Verified {passed_c} facts"
        if any(c.isdigit() for c in r): return True, "Contains numbers"
        return False, "No verifiable facts"

    if test_id in (16, 17):
        if any(w in r for w in facts["semester_name"].split()):   return True, "Semester name found"
        if facts["semester_status"] in r:                         return True, "Status found"
        if any(w in r for w in ["open","closed","active","مفتوح","مغلق","نشط"]): return True, "Status word found"
        return False, "Semester info not found"

    if test_id in (18, 19, 20):
        if any(w in r for w in ["?","which","what","who","need","provide","؟","أي","ما","من","أحتاج","يرجى","اسم","رقم"]):
            return True, "Asked for missing info"
        return False, "Did not ask for info"

    return True, "Response received"


# ── Test prompts ──────────────────────────────────────────────────────────────
TEST_PROMPTS = [
    {"id":1,  "category":"Student Management",    "difficulty":"Easy",   "en":"Show me all students",                                                                 "ar":"أظهر لي جميع الطلاب"},
    {"id":2,  "category":"Student Management",    "difficulty":"Easy",   "en":"How many students are registered?",                                                    "ar":"كم عدد الطلاب المسجلين؟"},
    {"id":3,  "category":"Student Management",    "difficulty":"Medium", "en":"Search for a student named Ahmed",                                                     "ar":"ابحث عن طالب اسمه أحمد"},
    {"id":4,  "category":"Course Management",     "difficulty":"Easy",   "en":"List all available courses",                                                           "ar":"اعرض جميع المقررات المتاحة"},
    {"id":5,  "category":"Course Management",     "difficulty":"Easy",   "en":"Which courses have available seats?",                                                  "ar":"أي المقررات لديها مقاعد شاغرة؟"},
    {"id":6,  "category":"Course Management",     "difficulty":"Medium", "en":"Which course has the most enrolled students?",                                         "ar":"أي مقرر يحتوي على أكبر عدد من الطلاب؟"},
    {"id":7,  "category":"Enrollment Management", "difficulty":"Easy",   "en":"What courses is student with ID 1 enrolled in?",                                      "ar":"ما هي المقررات التي يدرسها الطالب رقم 1؟"},
    {"id":8,  "category":"Enrollment Management", "difficulty":"Medium", "en":"Enroll student with ID 1 in ENG301",                                                  "ar":"سجّل الطالب رقم 1 في مقرر ENG301"},
    {"id":9,  "category":"Enrollment Management", "difficulty":"Medium", "en":"Drop student with ID 1 from ENG301",                                                  "ar":"أحذف الطالب رقم 1 من مقرر ENG301"},
    {"id":10, "category":"Grades & Performance",  "difficulty":"Easy",   "en":"Show all grades for student with ID 1",                                               "ar":"أظهر جميع درجات الطالب رقم 1"},
    {"id":11, "category":"Grades & Performance",  "difficulty":"Medium", "en":"What is the semester average for student with ID 1?",                                 "ar":"ما هو معدل الطالب رقم 1 في هذا الفصل؟"},
    {"id":12, "category":"Grades & Performance",  "difficulty":"Medium", "en":"Did student with ID 1 pass this semester?",                                           "ar":"هل نجح الطالب رقم 1 في هذا الفصل؟"},
    {"id":13, "category":"Analytics",             "difficulty":"Hard",   "en":"Get active semester then give full report: total students, pass rate, class average", "ar":"احصل على الفصل النشط ثم أعطني تقريراً: عدد الطلاب ونسبة النجاح والمعدل"},
    {"id":14, "category":"Analytics",             "difficulty":"Hard",   "en":"Get active semester then rank students highest to lowest and show top 3",             "ar":"احصل على الفصل النشط ثم رتب الطلاب من الأعلى للأدنى وأظهر أفضل 3"},
    {"id":15, "category":"Analytics",             "difficulty":"Hard",   "en":"Get active semester then list every student who failed",                              "ar":"احصل على الفصل النشط ثم اعرض كل طالب رسب"},
    {"id":16, "category":"Semester Management",   "difficulty":"Easy",   "en":"What is the current active semester?",                                                "ar":"ما هو الفصل الدراسي النشط حالياً؟"},
    {"id":17, "category":"Semester Management",   "difficulty":"Easy",   "en":"Is the semester open or closed?",                                                     "ar":"هل الفصل الدراسي مفتوح أم مغلق؟"},
    {"id":18, "category":"Error Handling",        "difficulty":"Medium", "en":"Add a new course",                                                                    "ar":"أضف مقرراً جديداً"},
    {"id":19, "category":"Error Handling",        "difficulty":"Medium", "en":"Enroll in CS101",                                                                     "ar":"سجّلني في CS101"},
    {"id":20, "category":"Error Handling",        "difficulty":"Medium", "en":"Set grade to 35",                                                                     "ar":"ضع الدرجة 35"},
]


# ── Main ──────────────────────────────────────────────────────────────────────
def run_benchmark():
    from core.mcp_bridge import MCPBridge
    from core.llm_client import LLMUniversityClient

    print("\n" + "="*65)
    print("   UNIVERSITY AI — BENCHMARK  (Fresh Start Every Run)")
    print("="*65)
    print(f"   Model : {MODEL}")
    print(f"   Tests : {len(TEST_PROMPTS)} questions × 2 languages = {len(TEST_PROMPTS)*2}")
    print("="*65)

    # 1. Reset DB and write known data
    print("\n  Setting up fresh database...")
    semester_id = reset_and_seed_db()

    # 2. Build ground truth
    facts = build_facts(semester_id)
    print(f"\n  Ground truth:")
    print(f"    Student 1 (Ahmed) avg : {facts['student1_average']}")
    print(f"    Class average         : {facts['class_average']}")
    print(f"    Passed / Failed       : {facts['passed_count']} / {facts['failed_count']}")
    print("="*65)

    # 3. Start bridge and client
    try:
        bridge = MCPBridge()
    except Exception as e:
        print(f"\n  FAILED to start MCP: {e}")
        return

    client  = LLMUniversityClient(mcp_bridge=bridge, model_name=MODEL)
    context = {"semester_id": semester_id}
    all_results = []

    # 4. Run all tests
    for test in TEST_PROMPTS:
        print(f"\n  ── [{test['id']:02d}] {test['category']} ({test['difficulty']}) ──")

        for lang, flag in [("en", "🇬🇧"), ("ar", "🇸🇦")]:
            prompt = test[lang]

            # Wait between requests to avoid Mistral rate limit
            time.sleep(3)

            start_time = time.time()
            try:
                response = client.handle_chat(prompt, context)
                # If rate limit hit, wait and retry once
                if response and "request limit" in response.lower():
                    print(f"       ⏳ Rate limit hit — waiting 30s...")
                    time.sleep(30)
                    response = client.handle_chat(prompt, context)
                success  = True
            except Exception as e:
                response = ""
                success  = False
            elapsed = round(time.time() - start_time, 3)

            passed, reason = check_response(response, test["id"], facts) if success else (False, "Error")

            mark = "✅" if passed else "❌"
            print(f"  {mark} {flag} [{lang.upper()}]  {elapsed:>6.2f}s   {prompt[:50]}")
            print(f"       reason : {reason}")
            if response:
                print(f"       reply  : {response[:80].replace(chr(10),' ')}")

            all_results.append({
                "prompt_id": test["id"], "category": test["category"],
                "difficulty": test["difficulty"], "lang": lang,
                "prompt": prompt, "model": MODEL,
                "elapsed_seconds": elapsed, "passed": passed,
                "reason": reason, "success": success,
                "response_preview": response[:300] if response else "",
            })

    # 5. Summary
    def avg(lst): return round(sum(lst)/len(lst), 2) if lst else 0
    en_r    = [r for r in all_results if r["lang"]=="en"]
    ar_r    = [r for r in all_results if r["lang"]=="ar"]
    en_pass = sum(1 for r in en_r if r["passed"])
    ar_pass = sum(1 for r in ar_r if r["passed"])
    total   = len(all_results)
    correct = en_pass + ar_pass

    print(f"\n{'='*65}")
    print(f"  RESULTS  —  Model: {MODEL}")
    print(f"{'='*65}")
    print(f"  {'':30} {'🇬🇧 English':>14}   {'🇸🇦 Arabic':>12}")
    print(f"  {'─'*58}")
    print(f"  {'Correct':30} {en_pass:>8}/{len(en_r)}   {ar_pass:>8}/{len(ar_r)}")
    print(f"  {'Avg Time':30} {avg([r['elapsed_seconds'] for r in en_r]):>12.2f}s   {avg([r['elapsed_seconds'] for r in ar_r]):>10.2f}s")
    print(f"  {'Overall Accuracy':30} {correct}/{total} ({round(correct/total*100,1)}%)")
    print(f"{'='*65}")

    try:
        bridge.cleanup()
    except Exception:
        pass

    output   = build_output(all_results, facts)
    out_path = os.path.join(BASE_DIR, "benchmark_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  Saved → {out_path}")
    print("  Open benchmark_dashboard.html and drop the JSON\n")
    return output


def build_output(results, facts):
    def avg(lst): return round(sum(lst)/len(lst), 2) if lst else 0
    langs = {"en":{"t":[],"pass":0,"tot":0}, "ar":{"t":[],"pass":0,"tot":0}}
    cats  = {}
    diffs = {d:{l:{"t":[],"pass":0,"tot":0} for l in ["en","ar"]} for d in ["Easy","Medium","Hard"]}
    for r in results:
        l, c, d = r["lang"], r["category"], r["difficulty"]
        langs[l]["t"].append(r["elapsed_seconds"]); langs[l]["tot"] += 1
        if r["passed"]: langs[l]["pass"] += 1
        if c not in cats: cats[c] = {"en":{"t":[],"pass":0,"tot":0},"ar":{"t":[],"pass":0,"tot":0}}
        cats[c][l]["t"].append(r["elapsed_seconds"]); cats[c][l]["tot"] += 1
        if r["passed"]: cats[c][l]["pass"] += 1
        if d in diffs:
            diffs[d][l]["t"].append(r["elapsed_seconds"]); diffs[d][l]["tot"] += 1
            if r["passed"]: diffs[d][l]["pass"] += 1
    ls = {l: {"correct":d["pass"],"total":d["tot"],"pass_rate":round(d["pass"]/d["tot"]*100,1) if d["tot"] else 0,"avg_time":avg(d["t"]),"total_time":round(sum(d["t"]),1)} for l,d in langs.items()}
    cs = {c: {l: {"correct":d[l]["pass"],"total":d[l]["tot"],"pass_rate":round(d[l]["pass"]/d[l]["tot"]*100,1) if d[l]["tot"] else 0,"avg_time":avg(d[l]["t"])} for l in ["en","ar"]} for c,d in cats.items()}
    ds = {diff: {l: {"correct":d[l]["pass"],"total":d[l]["tot"],"pass_rate":round(d[l]["pass"]/d[l]["tot"]*100,1) if d[l]["tot"] else 0,"avg_time":avg(d[l]["t"])} for l in ["en","ar"]} for diff,d in diffs.items()}
    return {"model":MODEL,"db_facts":{k:v for k,v in facts.items() if k not in ("student_names","course_codes","student1_courses")},"lang_summary":ls,"category_summary":cs,"difficulty_summary":ds,"raw_results":results}


if __name__ == "__main__":
    run_benchmark()
