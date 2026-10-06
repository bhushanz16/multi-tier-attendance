from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    roll_no = Column(String, unique=True, index=True)
    name = Column(String)
    password = Column(String)
    year = Column(String) # e.g., '1st', '2nd', '3rd', '4th'
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
    year = Column(String, index=True)
    dept = Column(String, index=True)
    div = Column(String, index=True)
    status = Column(String)
