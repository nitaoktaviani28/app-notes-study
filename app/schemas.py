from pydantic import BaseModel


class CourseCreate(BaseModel):
    name: str
    code: str | None = None


class ScheduleCreate(BaseModel):
    course_id: int
    day_of_week: str
    schedule_date: str | None = None
    start_time: str
    end_time: str | None = None
    location: str | None = None
    note: str | None = None


class GradeCreate(BaseModel):
    course_id: int
    semester: int
    score: float
    weight: float | None = None
    note: str | None = None


class RoutineCreate(BaseModel):
    title: str
    day_of_week: str
    routine_date: str | None = None
    reminder_time: str
    note: str | None = None


class PomodoroCreate(BaseModel):
    task: str
    focus_minutes: int
    break_minutes: int
    cycles: int
