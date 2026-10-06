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

from models import Base, Student, Attendance, Teacher

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Changed DB name to avoid lock issues with previous schema
SQLALCHEMY_DATABASE_URL = "sqlite:///./attendance_v2.db"
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
    records = db.query(Attendance).order_by(Attendance.date.desc()).limit(50).all()
    
    return templates.TemplateResponse(
        request=request, 
        name="teacher_dashboard.html", 
        context={"records": records, "total_students": total_students, "total_records": total_records}
    )

@app.get("/teacher/edge", response_class=HTMLResponse)
async def teacher_edge_page(request: Request):
    if not get_teacher_user(request):
        return RedirectResponse(url="/teacher/login")
    return templates.TemplateResponse(request=request, name="teacher_edge.html")

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
async def student_register_post(roll_no: str = Form(...), name: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(Student).filter(Student.roll_no == roll_no).first()
    if existing:
        return HTMLResponse("Student already registered", status_code=400)
    
    new_student = Student(roll_no=roll_no, name=name, password=password)
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
    records = db.query(Attendance).filter(Attendance.roll_no == roll_no).order_by(Attendance.date.desc()).all()
    
    has_face = student.face_encoding is not None
    
    return templates.TemplateResponse(
        request=request, 
        name="student_dashboard.html", 
        context={"student": student, "records": records, "has_face": has_face}
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

@app.get("/api/students")
async def get_students_api(db: Session = Depends(get_db)):
    # Only fetch students that have enrolled their face
    students = db.query(Student).filter(Student.face_encoding != None).all()
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
    status: str

@app.post("/api/sync_attendance")
async def sync_attendance_api(records: List[AttendanceRecord], request: Request, db: Session = Depends(get_db)):
    if not get_teacher_user(request):
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=401)
        
    for row in records:
        try:
            r_date = datetime.strptime(str(row.date), "%Y-%m-%d").date()
        except ValueError:
            continue
        
        existing = db.query(Attendance).filter(
            Attendance.roll_no == row.roll_no,
            Attendance.date == r_date
        ).first()

        if existing:
            existing.status = row.status
        else:
            new_record = Attendance(roll_no=row.roll_no, date=r_date, status=row.status)
            db.add(new_record)
    
    db.commit()
    return {"status": "success", "message": "Synced to database."}
