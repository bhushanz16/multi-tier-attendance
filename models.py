from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    name = Column(String, nullable=True) # Full Name, e.g., Dr. Rajesh Sharma
    email = Column(String, nullable=True)
    password = Column(String)
    dept = Column(String, nullable=True) # e.g. Computer, AI/DS, Mechanical
    designation = Column(String, nullable=True) # e.g. Professor, Assistant Professor, HOD
    assigned_semester = Column(String, nullable=True) # e.g. Semester 3
    assigned_div = Column(String, nullable=True) # e.g. A, B

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    roll_no = Column(String, unique=True, index=True)
    name = Column(String)
    password = Column(String)
    semester = Column(String) # e.g., 'Semester 1', 'Semester 2', etc.
    dept = Column(String) # e.g., 'Computer', 'Mechanical'
    div = Column(String)  # e.g., 'A', 'B'
    face_encoding = Column(String, nullable=True)

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    roll_no = Column(String, index=True)
    date = Column(Date, index=True)
    timestamp = Column(DateTime)
    subject = Column(String, index=True)
    semester = Column(String, index=True)
    dept = Column(String, index=True)
    div = Column(String, index=True)
    status = Column(String)
    teacher_username = Column(String, index=True) # Links attendance to the specific teacher

class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String, index=True)
    semester = Column(String, index=True)
    dept = Column(String, index=True, nullable=True) # e.g. Computer, AI/DS, IT, Mechanical, All
    div = Column(String, index=True, nullable=True)   # e.g. All, A, B, C, D
    teacher_username = Column(String, index=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    actor = Column(String, index=True)
    action_type = Column(String, index=True)
    target_student = Column(String, index=True)
    details = Column(String)
