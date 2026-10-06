import json
from fastapi import FastAPI, Depends, Request, Response, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from pydantic import BaseModel
from typing import List
from sqlalchemy.sql import func
from sqlalchemy import desc

from models import Base, Student, Attendance, Teacher, Subject

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Use v5 for Semester & Teacher Data Isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///./attendance_v5.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    db = SessionLocal()
    # Let's add two teachers so the user can test data isolation
    if not db.query(Teacher).filter(Teacher.username=="admin").first():
        db.add(Teacher(username="admin", password="password"))
    if not db.query(Teacher).filter(Teacher.username=="professor2").first():
        db.add(Teacher(username="professor2", password="password"))
    db.commit()
    db.close()
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
async def teacher_login_post(response: Response, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.username == username, Teacher.password == password).first()
    if teacher:
        res = RedirectResponse(url="/teacher/dashboard", status_code=302)
        res.set_cookie(key="teacher_session", value=username)
        return res
    return HTMLResponse("Invalid credentials", status_code=401)

@app.get("/teacher/logout")
async def teacher_logout(response: Response):
    res = RedirectResponse(url="/teacher/login", status_code=302)
    res.delete_cookie("teacher_session")
    return res

@app.get("/teacher/dashboard", response_class=HTMLResponse)
async def teacher_dashboard(request: Request, semester: str = None, dept: str = None, div: str = None, db: Session = Depends(get_db)):
    t_user = get_teacher_user(request)
    if not t_user:
        return RedirectResponse(url="/teacher/login")
    
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

    # Unique lists for dropdowns (shows all available students' hierarchy)
    semesters = [y[0] for y in db.query(Student.semester).distinct().all() if y[0]]
    depts = [d[0] for d in db.query(Student.dept).distinct().all() if d[0]]
    divs = [d[0] for d in db.query(Student.div).distinct().all() if d[0]]

    teacher_subjects = db.query(Subject).filter(Subject.teacher_username == t_user).all()

    return templates.TemplateResponse(
        request=request, 
        name="teacher_dashboard.html", 
        context={
            "t_user": t_user,
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
    if not get_teacher_user(request):
        return RedirectResponse(url="/teacher/login")
    
    semesters = [y[0] for y in db.query(Student.semester).distinct().all() if y[0]]
    depts = [d[0] for d in db.query(Student.dept).distinct().all() if d[0]]
    divs = [d[0] for d in db.query(Student.div).distinct().all() if d[0]]

    teacher_subjects = db.query(Subject).filter(Subject.teacher_username == t_user).all()

    return templates.TemplateResponse(request=request, name="teacher_edge.html", context={
        "semesters": semesters, "depts": depts, "divs": divs, "subjects": teacher_subjects
    })

@app.post("/teacher/subject")
async def create_subject(request: Request, name: str = Form(...), code: str = Form(...), semester: str = Form(...), db: Session = Depends(get_db)):
    t_user = get_teacher_user(request)
    if not t_user: return RedirectResponse(url="/teacher/login", status_code=302)
    db.add(Subject(name=name, code=code, semester=semester, teacher_username=t_user))
    db.commit()
    return RedirectResponse(url="/teacher/dashboard", status_code=302)

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
    student = db.query(Student).filter(Student.roll_no == roll_no, Student.password == password).first()
    if student:
        res = RedirectResponse(url="/student/dashboard", status_code=302)
        res.set_cookie(key="student_session", value=roll_no)
        return res
    return HTMLResponse("Invalid roll number or password", status_code=401)

@app.get("/student/register", response_class=HTMLResponse)
async def student_register_page(request: Request):
    return templates.TemplateResponse(request=request, name="student_register.html")

@app.post("/student/register")
async def student_register_post(
    roll_no: str = Form(...), name: str = Form(...), password: str = Form(...), 
    semester: str = Form(...), dept: str = Form(...), div: str = Form(...), 
    db: Session = Depends(get_db)
):
    existing = db.query(Student).filter(Student.roll_no == roll_no).first()
    if existing:
        return HTMLResponse("Student already registered", status_code=400)
    
    new_student = Student(roll_no=roll_no, name=name, password=password, semester=semester, dept=dept, div=div)
    db.add(new_student)
    db.commit()
    return RedirectResponse(url="/student/login", status_code=302)

@app.get("/student/logout")
async def student_logout(response: Response):
    res = RedirectResponse(url="/student/login", status_code=302)
    res.delete_cookie("student_session")
    return res

@app.get("/student/dashboard", response_class=HTMLResponse)
async def student_dashboard(request: Request, db: Session = Depends(get_db)):
    roll_no = get_student_user(request)
    if not roll_no:
        return RedirectResponse(url="/student/login")
    
    student = db.query(Student).filter(Student.roll_no == roll_no).first()
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
    db.commit()
    return JSONResponse({"status": "success"})

@app.get("/api/students/{semester}/{dept}/{div}")
async def get_students_by_hierarchy(semester: str, dept: str, div: str, db: Session = Depends(get_db)):
    students = db.query(Student).filter(
        Student.face_encoding != None, 
        Student.semester == semester, Student.dept == dept, Student.div == div
    ).all()
    res = []
    for s in students:
        res.append({
            "roll_no": s.roll_no,
            "name": s.name,
            "face_encoding": json.loads(s.face_encoding)
        })
    return res

class AttendanceRecord(BaseModel):
    roll_no: str
    date: str
    time: str
    subject: str
    semester: str
    dept: str
    div: str
    status: str

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
            roll_no=row.roll_no, date=r_date, timestamp=r_time,
            subject=row.subject, semester=row.semester, dept=row.dept, div=row.div, status=row.status,
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
