from sqlalchemy import Column, Integer, String, Date
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
    password = Column(String)  # New field for student auth
    face_encoding = Column(String, nullable=True) # Can be null if registered but not enrolled yet

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    roll_no = Column(String, index=True)
    date = Column(Date, index=True)
    status = Column(String)
