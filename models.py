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
    class_name = Column(String)  # New field: e.g., 'CS-A', 'Grade 10'
    face_encoding = Column(String, nullable=True)

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    roll_no = Column(String, index=True)
    date = Column(Date, index=True)
    timestamp = Column(DateTime) # Precise time of scan
    subject = Column(String, index=True) # e.g., 'Mathematics'
    class_name = Column(String, index=True) # e.g., 'CS-A'
    status = Column(String)
