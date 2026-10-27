import json
import csv
import io
from fpdf import FPDF
from fastapi import FastAPI, Depends, Request, Response, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, desc, text
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from pydantic import BaseModel
from typing import List
from sqlalchemy.sql import func

from models import Base, Student, Attendance, Teacher, Subject, AuditLog

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

import os

# Dynamic Cloud DB (Supabase / Neon / PostgreSQL) with Local SQLite fallback
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./attendance_v5.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def get_engine(url):
    if "sqlite" in url:
        return create_engine(url, connect_args={"check_same_thread": False})
    else:
        return create_engine(url, pool_pre_ping=True, pool_recycle=300)

engine = get_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    global engine, SessionLocal
    try:
        Base.metadata.create_all(bind=engine)
        print("Connected to primary database successfully.")
    except Exception as e:
        print(f"Warning: Primary database connection failed ({e}).")
        if "sqlite" not in DATABASE_URL:
            print("Auto-falling back to local SQLite database to prevent downtime...")
            engine = get_engine("sqlite:///./attendance_v5.db")
            SessionLocal.configure(bind=engine)
            Base.metadata.create_all(bind=engine)

    try:
        # Check and add columns to existing tables if missing
        try:
            with engine.connect() as conn:
                for col in ["dept", "div"]:
                    try:
                        conn.execute(text(f"ALTER TABLE subjects ADD COLUMN {col} VARCHAR"))
                        conn.commit()
                    except Exception:
                        pass
                try:
                    conn.execute(text("ALTER TABLE students ADD COLUMN student_id VARCHAR"))
                    conn.commit()
                except Exception:
                    pass
                for col in ["student_id", "method"]:
                    try:
                        conn.execute(text(f"ALTER TABLE attendance ADD COLUMN {col} VARCHAR"))
                        conn.commit()
                    except Exception:
                        pass
        except Exception:
            pass

        db = SessionLocal()
        # Seed default faculty accounts if not existing
        if not db.query(Teacher).filter(Teacher.username=="admin").first():
            db.add(Teacher(
                username="admin", name="Prof. Rajesh Sharma", password="password", 
                designation="Head of Department (HOD)", dept="Computer", 
                assigned_semester="Semester 3", assigned_div="A"
            ))
        if not db.query(Teacher).filter(Teacher.username=="professor2").first():
            db.add(Teacher(
                username="professor2", name="Prof. Anjali Gupta", password="password", 
                designation="Assistant Professor", dept="Computer", 
                assigned_semester="Semester 3", assigned_div="B"
            ))
        
        # Seed 5 demo students with distinct student_id (Primary ID) & roll_no
        demo_students = [
            ("101", "STU202401", "Aarav Sharma", "password", "Semester 3", "Computer", "A"),
            ("102", "STU202402", "Priya Patel", "password", "Semester 3", "Computer", "A"),
            ("103", "STU202403", "Rohan Verma", "password", "Semester 3", "Computer", "A"),
            ("104", "STU202404", "Ananya Iyer", "password", "Semester 3", "Computer", "A"),
            ("105", "STU202405", "Karan Mehta", "password", "Semester 3", "Computer", "A"),
        ]
        for roll, sid, sname, spwd, sem, sdept, sdiv in demo_students:
            s_exist = db.query(Student).filter(Student.roll_no == roll).first()
            if not s_exist:
                db.add(Student(roll_no=roll, student_id=sid, name=sname, password=spwd, semester=sem, dept=sdept, div=sdiv))
            elif not s_exist.student_id:
                s_exist.student_id = sid

        # Backfill any existing students missing student_id
        all_s = db.query(Student).filter(Student.student_id == None).all()
        for s in all_s:
            s.student_id = f"STU{s.roll_no}"

        # Seed default subjects for admin so scanner is ready immediately
        if not db.query(Subject).filter(Subject.teacher_username == "admin").first():
            db.add(Subject(name="Data Structures & Algorithms", code="CS-301", semester="Semester 3", dept="Computer", div="A", teacher_username="admin"))
            db.add(Subject(name="Database Management Systems", code="CS-302", semester="Semester 3", dept="Computer", div="A", teacher_username="admin"))
            db.add(Subject(name="Computer Networks", code="CS-303", semester="Semester 3", dept="Computer", div="A", teacher_username="admin"))

        db.commit()
        db.close()
        print("Database schema verified and sample data ready.")
    except Exception as e:
        print(f"Notice during seeding: {e}")

# Run DB verification immediately on import and on startup
init_db()

@app.on_event("startup")
async def startup_event():
    init_db()

def get_teacher_user(request: Request):
    return request.cookies.get("teacher_session")

def get_student_user(request: Request):
    return request.cookies.get("student_session")

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

# ==================== TEACHER ROUTES ====================

@app.get("/teacher/login", response_class=HTMLResponse)
async def teacher_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="teacher_login.html")

@app.post("/teacher/login")
async def teacher_login_post(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.username == username, Teacher.password == password).first()
    if teacher:
        res = RedirectResponse(url="/teacher/dashboard", status_code=302)
        res.set_cookie(key="teacher_session", value=username, path="/", samesite="lax")
        return res
    return HTMLResponse("Invalid credentials", status_code=401)

@app.get("/teacher/register", response_class=HTMLResponse)
async def teacher_register_page(request: Request):
    return templates.TemplateResponse(request=request, name="teacher_register.html")

@app.post("/teacher/register")
async def teacher_register_post(
    username: str = Form(...), name: str = Form(...), password: str = Form(...),
    email: str = Form(""), dept: str = Form(...), designation: str = Form(...),
    assigned_semester: str = Form(...), assigned_div: str = Form(...),
    db: Session = Depends(get_db)
):
    existing = db.query(Teacher).filter(Teacher.username == username).first()
    if existing:
        return HTMLResponse("Username already taken. Please choose another username.", status_code=400)
    
    new_teacher = Teacher(
        username=username, name=name, password=password, email=email,
        dept=dept, designation=designation, assigned_semester=assigned_semester, assigned_div=assigned_div
    )
    db.add(new_teacher)
    db.commit()
    return RedirectResponse(url="/teacher/login", status_code=302)

@app.get("/teacher/logout")
async def teacher_logout():
    res = RedirectResponse(url="/teacher/login", status_code=302)
    res.delete_cookie(key="teacher_session", path="/")
    res.set_cookie(key="teacher_session", value="", max_age=0, expires=0, path="/")
    return res

def get_academic_structure(db: Session):
    """
    Returns standard institutional academic structure (Semesters 1 through 6,
    standard engineering departments, and divisions A-D) independent of student enrollment,
    merged with any custom entries found in the database.
    Ensures teachers can always create subjects and manage classes without bottlenecks.
    """
    base_sems = ["Semester 1", "Semester 2", "Semester 3", "Semester 4", "Semester 5", "Semester 6"]
    db_sems = [s[0] for s in db.query(Student.semester).distinct().all() if s[0]]
    all_sems = list(base_sems)
    for s in db_sems:
        if s and s not in all_sems:
            all_sems.append(s)

    base_depts = ["Computer", "Information Technology", "AI & Data Science", "Mechanical", "Civil", "Electrical"]
    db_depts = [d[0] for d in db.query(Student.dept).distinct().all() if d[0]]
    all_depts = list(base_depts)
    for d in db_depts:
        if d and d not in all_depts:
            all_depts.append(d)

    base_divs = ["A", "B", "C", "D"]
    db_divs = [v[0] for v in db.query(Student.div).distinct().all() if v[0]]
    all_divs = list(base_divs)
    for v in db_divs:
        if v and v not in all_divs:
            all_divs.append(v)

    return all_sems, all_depts, all_divs

@app.get("/teacher/dashboard", response_class=HTMLResponse)
async def teacher_dashboard(request: Request, semester: str = None, dept: str = None, div: str = None, db: Session = Depends(get_db)):
    t_user = get_teacher_user(request)
    if not t_user:
        return RedirectResponse(url="/teacher/login")
    
    teacher_obj = db.query(Teacher).filter(Teacher.username == t_user).first()
    if not teacher_obj:
        teacher_obj = Teacher(username=t_user, name=t_user.title(), designation="Faculty", dept="Computer", assigned_semester="Semester 3", assigned_div="A")
    
    # ISOLATE DATA: Filter Records based on Hierarchy AND Teacher Username
    query = db.query(Attendance).filter(Attendance.teacher_username == t_user)
    if semester: query = query.filter(Attendance.semester == semester)
    if dept: query = query.filter(Attendance.dept == dept)
    if div: query = query.filter(Attendance.div == div)
    
    records = query.order_by(desc(Attendance.timestamp)).all()
    
    # Calculate Teacher's personal stats
    total_records = query.count()
    today = datetime.now().date()
    classes_today = db.query(Attendance.subject, Attendance.semester).filter(
        Attendance.teacher_username == t_user, Attendance.date == today
    ).distinct().count()

    # Subject breakdown for this specific teacher
    subject_stats = db.query(Attendance.subject, func.count(Attendance.id)).filter(
        Attendance.teacher_username == t_user
    ).group_by(Attendance.subject).all()

    subjects = [s[0] for s in subject_stats if s[0]]
    counts = [s[1] for s in subject_stats if s[0]]

    # Standard academic hierarchy (guaranteed 6 semesters, standard depts and divs)
    semesters, depts, divs = get_academic_structure(db)

    teacher_subjects = db.query(Subject).filter(Subject.teacher_username == t_user).all()

    return templates.TemplateResponse(
        request=request, 
        name="teacher_dashboard.html", 
        context={
            "t_user": t_user,
            "teacher": teacher_obj,
            "records": records, 
            "total_records": total_records,
            "classes_today": classes_today,
            "semesters": semesters,
            "depts": depts,
            "divs": divs,
            "teacher_subjects": teacher_subjects,
            "selected_semester": semester,
            "selected_dept": dept,
            "selected_div": div,
            "chart_labels": json.dumps(subjects),
            "chart_data": json.dumps(counts)
        }
    )

@app.get("/teacher/edge", response_class=HTMLResponse)
async def teacher_edge_page(request: Request, db: Session = Depends(get_db)):
    t_user = get_teacher_user(request)
    if not t_user:
        return RedirectResponse(url="/teacher/login")
    
    semesters, depts, divs = get_academic_structure(db)

    teacher_subjects = db.query(Subject).filter(Subject.teacher_username == t_user).all()
    if not teacher_subjects:
        for s_name, s_code in [("Data Structures & Algorithms", "CS-301"), ("Database Management Systems", "CS-302"), ("Computer Networks", "CS-303")]:
            db.add(Subject(name=s_name, code=s_code, semester="Semester 3", dept="Computer", div="A", teacher_username=t_user))
        db.commit()
        teacher_subjects = db.query(Subject).filter(Subject.teacher_username == t_user).all()

    return templates.TemplateResponse(request=request, name="teacher_edge.html", context={
        "semesters": semesters, "depts": depts, "divs": divs, "subjects": teacher_subjects
    })

@app.post("/teacher/subject")
async def create_subject(
    request: Request, 
    name: str = Form(...), 
    code: str = Form(...), 
    semester: str = Form(...),
    dept: str = Form("Computer"),
    div: str = Form("All"),
    db: Session = Depends(get_db)
):
    t_user = get_teacher_user(request)
    if not t_user: return RedirectResponse(url="/teacher/login", status_code=302)
    db.add(Subject(name=name, code=code, semester=semester, dept=dept, div=div, teacher_username=t_user))
    db.commit()
    referer = request.headers.get("referer")
    if referer and ("/teacher/subjects" in referer or "/teacher/dashboard" in referer):
        return RedirectResponse(url=referer, status_code=302)
    return RedirectResponse(url="/teacher/subjects", status_code=302)

@app.delete("/api/subject/{id}")
async def delete_subject(id: int, request: Request, db: Session = Depends(get_db)):
    t_user = get_teacher_user(request)
    if not t_user: return JSONResponse({"status": "error"}, status_code=401)
    record = db.query(Subject).filter(Subject.id == id, Subject.teacher_username == t_user).first()
    if record:
        db.delete(record)
        db.commit()
        return {"status": "success"}
    return {"status": "error"}

# ==================== STUDENT ROUTES ====================

@app.get("/student/login", response_class=HTMLResponse)
async def student_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="student_login.html")

@app.post("/student/login")
async def student_login_post(roll_no: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    student = db.query(Student).filter(
        ((Student.roll_no == roll_no) | (Student.student_id == roll_no)),
        Student.password == password
    ).first()
    if student:
        res = RedirectResponse(url="/student/dashboard", status_code=302)
        res.set_cookie(key="student_session", value=student.roll_no, path="/", samesite="lax")
        return res
    return HTMLResponse("Invalid roll number, student ID, or password", status_code=401)

@app.get("/student/register", response_class=HTMLResponse)
async def student_register_page(request: Request):
    return templates.TemplateResponse(request=request, name="student_register.html")

@app.post("/student/register")
async def student_register_post(
    roll_no: str = Form(...), name: str = Form(...), password: str = Form(...), 
    semester: str = Form(...), dept: str = Form(...), div: str = Form(...), 
    student_id: str = Form(None),
    db: Session = Depends(get_db)
):
    existing = db.query(Student).filter(
        (Student.roll_no == roll_no) | (Student.student_id == (student_id or roll_no))
    ).first()
    if existing:
        return HTMLResponse("Student roll number or ID already registered", status_code=400)
    
    sid = student_id if (student_id and student_id.strip()) else f"STU{roll_no}"
    new_student = Student(roll_no=roll_no, student_id=sid, name=name, password=password, semester=semester, dept=dept, div=div)
    db.add(new_student)
    db.commit()
    return RedirectResponse(url="/student/login", status_code=302)

@app.post("/student/update_id")
async def student_update_id(request: Request, student_id: str = Form(...), db: Session = Depends(get_db)):
    roll_no = get_student_user(request)
    if not roll_no: return RedirectResponse(url="/student/login")
    student = db.query(Student).filter(Student.roll_no == roll_no).first()
    if student and student_id and student_id.strip():
        sid = student_id.strip()
        taken = db.query(Student).filter(Student.student_id == sid, Student.roll_no != roll_no).first()
        if not taken:
            old_sid = student.student_id
            student.student_id = sid
            db.add(AuditLog(actor=roll_no, action_type="STUDENT_ID_SELF_UPDATE", target_student=roll_no, details=f"Student updated ID from [{old_sid}] to [{sid}]"))
            db.commit()
    return RedirectResponse(url="/student/dashboard", status_code=302)

@app.get("/student/logout")
async def student_logout():
    res = RedirectResponse(url="/student/login", status_code=302)
    res.delete_cookie(key="student_session", path="/")
    res.set_cookie(key="student_session", value="", max_age=0, expires=0, path="/")
    return res

@app.get("/student/dashboard", response_class=HTMLResponse)
async def student_dashboard(request: Request, db: Session = Depends(get_db)):
    roll_no = get_student_user(request)
    if not roll_no:
        return RedirectResponse(url="/student/login")
    
    student = db.query(Student).filter(Student.roll_no == roll_no).first()
    if not student:
        res = RedirectResponse(url="/student/login")
        res.delete_cookie(key="student_session", path="/")
        return res
    records = db.query(Attendance).filter(Attendance.roll_no == roll_no).all()
    
    # Format for FullCalendar
    calendar_events = []
    for r in records:
        color = "#10b981" if r.status == "Present" else "#ef4444"
        calendar_events.append({
            "title": f"{r.subject} ({r.status})",
            "start": r.timestamp.isoformat() if r.timestamp else str(r.date),
            "color": color
        })

    # Calculate Attendance % per subject
    subjects = db.query(Attendance.subject).filter(
        Attendance.semester == student.semester, Attendance.dept == student.dept, Attendance.div == student.div
    ).distinct().all()
    
    analytics = []
    chart_labels = []
    chart_data = []

    for s in subjects:
        subj = s[0]
        # Count distinct timestamps for this subject (Total Lectures)
        total_lectures = db.query(Attendance.timestamp).filter(
            Attendance.subject == subj, Attendance.semester == student.semester, 
            Attendance.dept == student.dept, Attendance.div == student.div
        ).distinct().count()
        
        if total_lectures == 0: total_lectures = 1
        
        # Count student's presence
        attended = db.query(Attendance).filter(
            Attendance.roll_no == roll_no, Attendance.subject == subj, Attendance.status == 'Present'
        ).count()
        
        percentage = min(100, round((attended / total_lectures) * 100))
        
        analytics.append({"subject": subj, "attended": attended, "total": total_lectures, "percentage": percentage})
        chart_labels.append(subj)
        chart_data.append(percentage)

    has_face = student.face_encoding is not None
    
    return templates.TemplateResponse(
        request=request, 
        name="student_dashboard.html", 
        context={
            "student": student, 
            "has_face": has_face,
            "calendar_events": json.dumps(calendar_events),
            "analytics": analytics,
            "chart_labels": json.dumps(chart_labels),
            "chart_data": json.dumps(chart_data)
        }
    )

# ==================== API ROUTES ====================

class EnrollData(BaseModel):
    encoding: list

@app.post("/api/enroll_face")
async def enroll_face_api(data: EnrollData, request: Request, db: Session = Depends(get_db)):
    roll_no = get_student_user(request)
    if not roll_no:
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)
    
    student = db.query(Student).filter(Student.roll_no == roll_no).first()
    student.face_encoding = json.dumps(data.encoding)
    db.add(AuditLog(actor=roll_no, action_type="FACE_UPDATE", target_student=roll_no, details="Uploaded new biometric vector"))
    db.commit()
    return JSONResponse({"status": "success"})

class TeacherEnrollData(BaseModel):
    roll_no: str
    encoding: list

@app.post("/api/teacher/enroll_face")
async def teacher_enroll_face_api(data: TeacherEnrollData, request: Request, db: Session = Depends(get_db)):
    t_user = get_teacher_user(request)
    if not t_user:
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)
    
    student = db.query(Student).filter(Student.roll_no == data.roll_no).first()
    if not student:
        return JSONResponse({"status": "error", "message": "Student not found"}, status_code=404)
        
    student.face_encoding = json.dumps(data.encoding)
    db.add(AuditLog(actor=t_user, action_type="MANUAL_FACE_UPLOAD", target_student=data.roll_no, details=f"Teacher uploaded photo biometric encoding for {student.name} ({student.roll_no})"))
    db.commit()
    return JSONResponse({"status": "success", "message": f"Biometrics successfully saved for {student.name}"})

@app.get("/api/students/{semester}/{dept}/{div}")
async def get_students_by_hierarchy(semester: str, dept: str, div: str, db: Session = Depends(get_db)):
    all_students = db.query(Student).all()

    def norm_sem(s):
        if not s: return ""
        return "".join(c for c in str(s).lower() if c.isalnum()).replace("semester", "").replace("sem", "").strip()

    def norm_dept(d):
        if not d: return ""
        d_str = str(d).lower()
        if "comp" in d_str or "cs" in d_str: return "computer"
        if "info" in d_str or "it" in d_str: return "it"
        if "ai" in d_str or "ds" in d_str: return "aids"
        if "mech" in d_str: return "mechanical"
        if "civil" in d_str: return "civil"
        if "elect" in d_str: return "electrical"
        return "".join(c for c in d_str if c.isalnum())

    def norm_div(v):
        if not v: return ""
        return str(v).strip().upper()

    target_sem = norm_sem(semester)
    target_dept = norm_dept(dept)
    target_div = norm_div(div)

    matched = []
    for s in all_students:
        s_sem = norm_sem(s.semester)
        s_dept = norm_dept(s.dept)
        s_div = norm_div(s.div)

        sem_ok = (not target_sem) or (s_sem == target_sem) or (semester.lower() in str(s.semester).lower()) or (str(s.semester).lower() in semester.lower())
        dept_ok = (dept == "All") or (not target_dept) or (s_dept == target_dept) or (dept.lower() in str(s.dept).lower()) or (str(s.dept).lower() in dept.lower())
        div_ok = (div == "All") or (not target_div) or (s_div == target_div)

        if sem_ok and dept_ok and div_ok:
            matched.append(s)

    def roll_sort_key(st):
        digits = "".join(c for c in (st.roll_no or "") if c.isdigit())
        return int(digits) if digits else 999999

    matched.sort(key=roll_sort_key)

    res = []
    for s in matched:
        res.append({
            "roll_no": s.roll_no,
            "student_id": s.student_id or s.roll_no,
            "name": s.name,
            "has_face": s.face_encoding is not None,
            "face_encoding": json.loads(s.face_encoding) if s.face_encoding else None
        })
    return res

class AttendanceRecord(BaseModel):
    roll_no: str
    student_id: str = None
    date: str
    time: str
    subject: str
    semester: str
    dept: str
    div: str
    status: str
    method: str = "Face"

@app.post("/api/sync_attendance")
async def sync_attendance_api(records: List[AttendanceRecord], request: Request, db: Session = Depends(get_db)):
    t_user = get_teacher_user(request)
    if not t_user:
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)
        
    for row in records:
        try:
            r_date = datetime.strptime(str(row.date), "%Y-%m-%d").date()
            r_time = datetime.strptime(str(row.date) + " " + str(row.time), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        
        new_record = Attendance(
            roll_no=row.roll_no,
            student_id=row.student_id or row.roll_no,
            date=r_date, timestamp=r_time,
            subject=row.subject, semester=row.semester, dept=row.dept, div=row.div, 
            status=row.status,
            method=row.method or "Face",
            teacher_username=t_user # Link record to teacher
        )
        db.add(new_record)
    
    db.commit()
    return {"status": "success"}

# CRUD ROUTES FOR TEACHER
class UpdateStatus(BaseModel):
    status: str

@app.put("/api/attendance/{id}")
async def update_attendance(id: int, data: UpdateStatus, request: Request, db: Session = Depends(get_db)):
    t_user = get_teacher_user(request)
    if not t_user: return JSONResponse({"status": "error"}, status_code=401)
    record = db.query(Attendance).filter(Attendance.id == id, Attendance.teacher_username == t_user).first()
    if record:
        record.status = data.status
        db.commit()
        return {"status": "success"}
    return {"status": "error"}

@app.delete("/api/attendance/{id}")
async def delete_attendance(id: int, request: Request, db: Session = Depends(get_db)):
    t_user = get_teacher_user(request)
    if not t_user: return JSONResponse({"status": "error"}, status_code=401)
    record = db.query(Attendance).filter(Attendance.id == id, Attendance.teacher_username == t_user).first()
    if record:
        db.delete(record)
        db.commit()
        return {"status": "success"}
    return {"status": "error"}

# ==================== ADVANCED REPORTS & AUDITING ====================

@app.get("/teacher/database", response_class=HTMLResponse)
async def teacher_database(request: Request, db: Session = Depends(get_db)):
    t_user = get_teacher_user(request)
    if not t_user: return RedirectResponse(url="/teacher/login")
    students = db.query(Student).all()
    return templates.TemplateResponse(request=request, name="teacher_database.html", context={"t_user": t_user, "students": students})

@app.post("/teacher/database/update")
async def teacher_database_update(
    request: Request, id: int = Form(...), roll_no: str = Form(...), name: str = Form(...), 
    semester: str = Form(...), dept: str = Form(...), div: str = Form(...), 
    student_id: str = Form(None), db: Session = Depends(get_db)
):
    t_user = get_teacher_user(request)
    if not t_user: return RedirectResponse(url="/teacher/login")
    
    student = db.query(Student).filter(Student.id == id).first()
    if student:
        old_data = f"{student.roll_no}, {student.student_id}, {student.name}, {student.semester}, {student.dept}, {student.div}"
        student.roll_no = roll_no
        student.student_id = student_id if (student_id and student_id.strip()) else (student.student_id or f"STU{roll_no}")
        student.name = name
        student.semester = semester
        student.dept = dept
        student.div = div
        new_data = f"{roll_no}, {student.student_id}, {name}, {semester}, {dept}, {div}"
        db.add(AuditLog(actor=t_user, action_type="MANUAL_DB_EDIT", target_student=roll_no, details=f"Changed from [{old_data}] to [{new_data}]"))
        db.commit()
    return RedirectResponse(url="/teacher/database", status_code=302)

@app.post("/teacher/student/create")
async def teacher_create_student(
    request: Request,
    student_id: str = Form(...),
    roll_no: str = Form(...),
    name: str = Form(...),
    semester: str = Form(...),
    dept: str = Form(...),
    div: str = Form(...),
    password: str = Form("password"),
    db: Session = Depends(get_db)
):
    t_user = get_teacher_user(request)
    if not t_user: return RedirectResponse(url="/teacher/login")

    sid = student_id.strip() if student_id else f"STU{roll_no.strip()}"
    roll = roll_no.strip()

    existing = db.query(Student).filter((Student.roll_no == roll) | (Student.student_id == sid)).first()
    if existing:
        return HTMLResponse(f"Student with Roll No {roll} or Student ID {sid} already exists.", status_code=400)

    new_s = Student(
        student_id=sid,
        roll_no=roll,
        name=name.strip(),
        semester=semester,
        dept=dept,
        div=div,
        password=password.strip() if password else "password"
    )
    db.add(new_s)
    db.add(AuditLog(actor=t_user, action_type="STUDENT_MANUAL_CREATE", target_student=roll, details=f"Teacher created student: {name.strip()} (ID: {sid}, Roll: {roll})"))
    db.commit()
    return RedirectResponse(url="/teacher/database", status_code=302)

@app.post("/teacher/students/upload_csv")
async def teacher_upload_students_csv(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    t_user = get_teacher_user(request)
    if not t_user: return RedirectResponse(url="/teacher/login")

    contents = await file.read()
    decoded = contents.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    created = 0
    updated = 0

    for row in reader:
        clean = {k.strip().lower(): v.strip() for k, v in row.items() if k and v}
        sid = clean.get("student_id") or clean.get("prn") or clean.get("uid") or clean.get("id")
        roll = clean.get("roll_no") or clean.get("roll") or clean.get("rollno")
        name = clean.get("name") or clean.get("student_name")
        sem = clean.get("semester") or clean.get("sem") or "Semester 3"
        dept = clean.get("dept") or clean.get("department") or "Computer"
        div = clean.get("div") or clean.get("division") or "A"
        pwd = clean.get("password") or "password"

        if not roll and not sid:
            continue
        if not roll: roll = sid
        if not sid: sid = f"STU{roll}"
        if not name: name = f"Student {roll}"

        existing = db.query(Student).filter((Student.roll_no == roll) | (Student.student_id == sid)).first()
        if existing:
            existing.student_id = sid
            existing.roll_no = roll
            existing.name = name
            existing.semester = sem
            existing.dept = dept
            existing.div = div
            updated += 1
        else:
            db.add(Student(
                student_id=sid,
                roll_no=roll,
                name=name,
                semester=sem,
                dept=dept,
                div=div,
                password=pwd
            ))
            created += 1

    db.add(AuditLog(actor=t_user, action_type="CSV_STUDENT_UPLOAD", target_student="BULK", details=f"Teacher uploaded CSV: {created} students created, {updated} updated."))
    db.commit()
    return RedirectResponse(url="/teacher/database", status_code=302)

@app.get("/api/sample_students_csv")
async def download_sample_students_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["student_id", "roll_no", "name", "semester", "dept", "div", "password"])
    writer.writerow(["STU202410", "110", "Sneha Rao", "Semester 3", "Computer", "A", "password"])
    writer.writerow(["STU202411", "111", "Aditya Kulkarni", "Semester 3", "Computer", "A", "password"])
    writer.writerow(["STU202412", "112", "Kavya Nair", "Semester 3", "Computer", "B", "password"])
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_students_roster.csv"}
    )

@app.get("/teacher/audit", response_class=HTMLResponse)
async def teacher_audit_logs(request: Request, db: Session = Depends(get_db)):
    t_user = get_teacher_user(request)
    if not t_user: return RedirectResponse(url="/teacher/login")
    logs = db.query(AuditLog).order_by(desc(AuditLog.timestamp)).all()
    return templates.TemplateResponse(request=request, name="teacher_audit.html", context={"t_user": t_user, "logs": logs})

@app.get("/teacher/subjects", response_class=HTMLResponse)
async def teacher_subjects_page(request: Request, db: Session = Depends(get_db)):
    t_user = get_teacher_user(request)
    if not t_user: return RedirectResponse(url="/teacher/login")
    subjects = db.query(Subject).filter(Subject.teacher_username == t_user).all()
    semesters, depts, divs = get_academic_structure(db)
    return templates.TemplateResponse(request=request, name="teacher_subjects.html", context={
        "t_user": t_user, 
        "subjects": subjects, 
        "semesters": semesters,
        "depts": depts,
        "divs": divs
    })

@app.get("/teacher/reports", response_class=HTMLResponse)
async def teacher_reports_page(request: Request, db: Session = Depends(get_db)):
    t_user = get_teacher_user(request)
    if not t_user: return RedirectResponse(url="/teacher/login")
    students = db.query(Student).all()
    return templates.TemplateResponse(request=request, name="teacher_reports.html", context={"t_user": t_user, "students": students})

@app.get("/api/reports/overall")
async def generate_overall_csv(request: Request, db: Session = Depends(get_db)):
    t_user = get_teacher_user(request)
    if not t_user: return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Roll No", "Name", "Semester", "Dept", "Div", "Total Lectures", "Attended", "Percentage"])
    
    students = db.query(Student).all()
    for s in students:
        total = db.query(Attendance.timestamp).filter(
            Attendance.teacher_username == t_user, Attendance.semester == s.semester, Attendance.dept == s.dept, Attendance.div == s.div
        ).distinct().count()
        attended = db.query(Attendance).filter(
            Attendance.teacher_username == t_user, Attendance.roll_no == s.roll_no, Attendance.status == 'Present'
        ).count()
        if total == 0: total = 1
        pct = round((attended/total)*100)
        writer.writerow([s.roll_no, s.name, s.semester, s.dept, s.div, total, attended, f"{pct}%"])
    
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=overall_report.csv"})

@app.get("/api/reports/blacklist")
async def generate_blacklist_csv(request: Request, db: Session = Depends(get_db)):
    t_user = get_teacher_user(request)
    if not t_user: return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Roll No", "Name", "Semester", "Dept", "Div", "Total Lectures", "Attended", "Percentage", "Status"])
    
    students = db.query(Student).all()
    for s in students:
        total = db.query(Attendance.timestamp).filter(
            Attendance.teacher_username == t_user, Attendance.semester == s.semester, Attendance.dept == s.dept, Attendance.div == s.div
        ).distinct().count()
        attended = db.query(Attendance).filter(
            Attendance.teacher_username == t_user, Attendance.roll_no == s.roll_no, Attendance.status == 'Present'
        ).count()
        if total == 0: total = 1
        pct = round((attended/total)*100)
        if pct < 75:
            writer.writerow([s.roll_no, s.name, s.semester, s.dept, s.div, total, attended, f"{pct}%", "DEFAULTER"])
    
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=blacklist.csv"})

@app.get("/api/reports/student/{roll_no}")
async def generate_student_csv(roll_no: str, request: Request, db: Session = Depends(get_db)):
    t_user = get_teacher_user(request)
    if not t_user: return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    student = db.query(Student).filter(Student.roll_no == roll_no).first()
    if not student: return JSONResponse({"error": "Not Found"}, status_code=404)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Roll No", "Name", "Subject", "Date", "Time", "Status"])
    
    records = db.query(Attendance).filter(Attendance.teacher_username == t_user, Attendance.roll_no == roll_no).all()
    for r in records:
        writer.writerow([r.roll_no, student.name, r.subject, r.date, r.timestamp.strftime("%H:%M:%S") if r.timestamp else "", r.status])
    
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=student_{roll_no}_report.csv"})

@app.get("/student/report")
async def student_self_report(request: Request, db: Session = Depends(get_db)):
    roll_no = get_student_user(request)
    if not roll_no: return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    student = db.query(Student).filter(Student.roll_no == roll_no).first()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Roll No", "Name", "Subject", "Date", "Time", "Status", "Teacher"])
    
    records = db.query(Attendance).filter(Attendance.roll_no == roll_no).all()
    for r in records:
        writer.writerow([r.roll_no, student.name, r.subject, r.date, r.timestamp.strftime("%H:%M:%S") if r.timestamp else "", r.status, r.teacher_username])
    
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=my_attendance_report.csv"})

# ==================== PDF REPORTS ====================

def generate_pdf_table(title: str, headers: list, rows: list):
    pdf = FPDF(orientation='L' if len(headers) > 6 else 'P')
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, title, align="C")
    pdf.ln(15)
    
    epw = pdf.epw
    col_width = epw / len(headers)
    
    pdf.set_font("helvetica", "B", 10)
    for header in headers:
        pdf.cell(col_width, 10, str(header), border=1, align="C")
    pdf.ln()
    
    pdf.set_font("helvetica", "", 10)
    for row in rows:
        for item in row:
            pdf.cell(col_width, 10, str(item), border=1, align="C")
        pdf.ln()
        
    return pdf.output()

@app.get("/api/reports/overall/pdf")
async def generate_overall_pdf(request: Request, db: Session = Depends(get_db)):
    t_user = get_teacher_user(request)
    if not t_user: return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    headers = ["Roll No", "Name", "Semester", "Dept", "Div", "Total Lectures", "Attended", "Percentage"]
    rows = []
    students = db.query(Student).all()
    for s in students:
        total = db.query(Attendance.timestamp).filter(
            Attendance.teacher_username == t_user, Attendance.semester == s.semester, Attendance.dept == s.dept, Attendance.div == s.div
        ).distinct().count()
        attended = db.query(Attendance).filter(
            Attendance.teacher_username == t_user, Attendance.roll_no == s.roll_no, Attendance.status == 'Present'
        ).count()
        if total == 0: total = 1
        pct = round((attended/total)*100)
        rows.append([s.roll_no, s.name, s.semester, s.dept, s.div, total, attended, f"{pct}%"])
    
    pdf_bytes = bytes(generate_pdf_table("Overall Student Report", headers, rows))
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=overall_report.pdf"})

@app.get("/api/reports/blacklist/pdf")
async def generate_blacklist_pdf(request: Request, db: Session = Depends(get_db)):
    t_user = get_teacher_user(request)
    if not t_user: return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    headers = ["Roll No", "Name", "Semester", "Dept", "Div", "Percentage", "Status"]
    rows = []
    students = db.query(Student).all()
    for s in students:
        total = db.query(Attendance.timestamp).filter(
            Attendance.teacher_username == t_user, Attendance.semester == s.semester, Attendance.dept == s.dept, Attendance.div == s.div
        ).distinct().count()
        attended = db.query(Attendance).filter(
            Attendance.teacher_username == t_user, Attendance.roll_no == s.roll_no, Attendance.status == 'Present'
        ).count()
        if total == 0: total = 1
        pct = round((attended/total)*100)
        if pct < 75:
            rows.append([s.roll_no, s.name, s.semester, s.dept, s.div, f"{pct}%", "DEFAULTER"])
            
    pdf_bytes = bytes(generate_pdf_table("Defaulters Blacklist (< 75%)", headers, rows))
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=blacklist.pdf"})

@app.get("/api/reports/student/{roll_no}/pdf")
async def generate_student_pdf(roll_no: str, request: Request, db: Session = Depends(get_db)):
    t_user = get_teacher_user(request)
    if not t_user: return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    student = db.query(Student).filter(Student.roll_no == roll_no).first()
    if not student: return JSONResponse({"error": "Not Found"}, status_code=404)
    
    headers = ["Roll No", "Name", "Subject", "Date", "Time", "Status"]
    rows = []
    records = db.query(Attendance).filter(Attendance.teacher_username == t_user, Attendance.roll_no == roll_no).all()
    for r in records:
        rows.append([r.roll_no, student.name, r.subject, r.date, r.timestamp.strftime("%H:%M:%S") if r.timestamp else "", r.status])
        
    pdf_bytes = bytes(generate_pdf_table(f"Student Report: {roll_no}", headers, rows))
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=student_{roll_no}_report.pdf"})

@app.get("/student/report/pdf")
async def student_self_report_pdf(request: Request, db: Session = Depends(get_db)):
    roll_no = get_student_user(request)
    if not roll_no: return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    student = db.query(Student).filter(Student.roll_no == roll_no).first()
    headers = ["Subject", "Date", "Time", "Status", "Teacher"]
    rows = []
    records = db.query(Attendance).filter(Attendance.roll_no == roll_no).all()
    for r in records:
        rows.append([r.subject, r.date, r.timestamp.strftime("%H:%M:%S") if r.timestamp else "", r.status, r.teacher_username])
        
    pdf_bytes = bytes(generate_pdf_table(f"My Attendance Report ({roll_no})", headers, rows))
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=my_attendance_report.pdf"})
