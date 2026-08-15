from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    code = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    schedule_items = relationship("ScheduleItem", back_populates="course", cascade="all, delete-orphan")
    materials = relationship("Material", back_populates="course", cascade="all, delete-orphan")
    grades = relationship("Grade", back_populates="course", cascade="all, delete-orphan")


class ScheduleItem(Base):
    __tablename__ = "schedule_items"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    day_of_week = Column(String(20), nullable=False)
    schedule_date = Column(String(10), nullable=True)
    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=True)
    location = Column(String(200), nullable=True)
    note = Column(Text, nullable=True)

    course = relationship("Course", back_populates="schedule_items")


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(255), nullable=False)
    folder_name = Column(String(120), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    web_path = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course", back_populates="materials")


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    semester = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)
    weight = Column(Float, nullable=True)
    note = Column(Text, nullable=True)

    course = relationship("Course", back_populates="grades")


class Routine(Base):
    __tablename__ = "routines"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    day_of_week = Column(String(20), nullable=False)
    reminder_time = Column(String(10), nullable=False)
    note = Column(Text, nullable=True)


class PomodoroSession(Base):
    __tablename__ = "pomodoro_sessions"

    id = Column(Integer, primary_key=True, index=True)
    task = Column(String(255), nullable=False)
    focus_minutes = Column(Integer, nullable=False)
    break_minutes = Column(Integer, nullable=False)
    cycles = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AiResult(Base):
    __tablename__ = "ai_results"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    result_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
