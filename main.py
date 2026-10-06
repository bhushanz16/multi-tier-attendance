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

from models import Base, Student, Attendance, Teacher

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Use v3 for new advanced schema
SQLALCHEMY_DATABASE_URL = "sqlite:///./attendance_v3.db"
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
    if not db.query(Teacher).first():
        db.add(Teacher(username="admin", password="password"))
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
async def teacher_dashboard(request: Request, db: Session = Depends(get_db)):
    if not get_teacher_user(request):
        return RedirectResponse(url="/teacher/login")
    
    total_students = db.query(Student).count()
    total_records = db.query(Attendance).count()
    
    # Calculate classes taken today
    today = datetime.now().date()
    classes_today = db.query(Attendance.subject, Attendance.class_name).filter(Attendance.date == today).distinct().count()

    records = db.query(Attendance).order_by(desc(Attendance.timestamp)).limit(50).all()
    
    # Subject breakdown for chart
    subject_stats = db.query(Attendance.subject, func.count(Attendance.id)).group_by(Attendance.subject).all()
    subjects = [s[0] for s in subject_stats if s[0]]
    counts = [s[1] for s in subject_stats if s[0]]

    return templates.TemplateResponse(
        request=request, 
        name="teacher_dashboard.html", 
        context={
            "records": records, 
            "total_students": total_students, 
            "total_records": total_records,
            "classes_today": classes_today,
            "chart_labels": json.dumps(subjects),
            "chart_data": json.dumps(counts)
        }
    )

@app.get("/teacher/edge", response_class=HTMLResponse)
async def teacher_edge_page(request: Request, db: Session = Depends(get_db)):
    if not get_teacher_user(request):
        return RedirectResponse(url="/teacher/login")
    
    # Get unique classes for dropdown
    classes = db.query(Student.class_name).distinct().all()
    class_list = [c[0] for c in classes if c[0]]

    return templates.TemplateResponse(request=request, name="teacher_edge.html", context={"classes": class_list})

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
async def student_register_post(roll_no: str = Form(...), name: str = Form(...), password: str = Form(...), class_name: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(Student).filter(Student.roll_no == roll_no).first()
    if existing:
        return HTMLResponse("Student already registered", status_code=400)
    
    new_student = Student(roll_no=roll_no, name=name, password=password, class_name=class_name)
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
    records = db.query(Attendance).filter(Attendance.roll_no == roll_no).order_by(desc(Attendance.timestamp)).all()
    
    # Calculate Attendance % per subject
    total_lectures = db.query(Attendance.subject, func.count(Attendance.id)).filter(Attendance.class_name == student.class_name).group_by(Attendance.subject).all()
    my_presence = db.query(Attendance.subject, func.count(Attendance.id)).filter(Attendance.roll_no == roll_no, Attendance.status == 'Present').group_by(Attendance.subject).all()
    
    presence_dict = {p[0]: p[1] for p in my_presence}
    analytics = []
    chart_labels = []
    chart_data = []

    for t in total_lectures:
        subj = t[0]
        total = t[1]
        # Divide by number of unique students in class to get actual lecture count
        student_count = db.query(Student).filter(Student.class_name == student.class_name).count()
        if student_count > 0:
            actual_lectures = total // student_count
        else:
            actual_lectures = total

        if actual_lectures == 0: actual_lectures = 1
        attended = presence_dict.get(subj, 0)
        percentage = min(100, round((attended / actual_lectures) * 100))
        
        analytics.append({"subject": subj, "attended": attended, "total": actual_lectures, "percentage": percentage})
        chart_labels.append(subj)
        chart_data.append(percentage)

    has_face = student.face_encoding is not None
    
    return templates.TemplateResponse(
        request=request, 
        name="student_dashboard.html", 
        context={
            "student": student, 
            "records": records, 
            "has_face": has_face,
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
    if not student:
        return JSONResponse({"status": "error", "message": "Student not found"})
        
    student.face_encoding = json.dumps(data.encoding)
    db.commit()
    return JSONResponse({"status": "success", "message": "Face data updated successfully."})

@app.get("/api/students/{class_name}")
async def get_students_by_class(class_name: str, db: Session = Depends(get_db)):
    students = db.query(Student).filter(Student.face_encoding != None, Student.class_name == class_name).all()
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
    class_name: str
    status: str

@app.post("/api/sync_attendance")
async def sync_attendance_api(records: List[AttendanceRecord], request: Request, db: Session = Depends(get_db)):
    if not get_teacher_user(request):
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)
        
    for row in records:
        try:
            r_date = datetime.strptime(str(row.date), "%Y-%m-%d").date()
            r_time = datetime.strptime(str(row.date) + " " + str(row.time), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        
        # Don't overwrite if same subject/date/rollno exists, unless status changes? 
        # Actually just record it as a new timestamped event or overwrite. Let's overwrite for same day/subject.
        existing = db.query(Attendance).filter(
            Attendance.roll_no == row.roll_no,
            Attendance.date == r_date,
            Attendance.subject == row.subject
        ).first()

        if existing:
            existing.status = row.status
            existing.timestamp = r_time
        else:
            new_record = Attendance(
                roll_no=row.roll_no, 
                date=r_date, 
                timestamp=r_time,
                subject=row.subject,
                class_name=row.class_name,
                status=row.status
            )
            db.add(new_record)
    
    db.commit()
    return {"status": "success", "message": "Synced to advanced database."}
