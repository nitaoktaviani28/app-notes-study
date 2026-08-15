from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.ai_service import safe_generate_quiz, safe_summarize
from app.config import settings
from app.database import Base, engine, get_db
from app.file_service import ensure_folder, extract_text_from_material
from app.models import AiResult, Course, Grade, Material, PomodoroSession, Routine, ScheduleItem
from app.s3_service import s3_is_enabled, s3_storage, safe_create_presigned_url, safe_download_to_temp
from app.schemas import CourseCreate, GradeCreate, PomodoroCreate, RoutineCreate, ScheduleCreate
from app.telegram_service import send_telegram_message

ensure_folder(settings.storage_dir)
ensure_folder("./data")
Base.metadata.create_all(bind=engine)


def ensure_schema_updates() -> None:
    # Keep simple SQLite deployments working even when new columns are introduced.
    inspector = inspect(engine)
    if "schedule_items" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("schedule_items")}
    if "schedule_date" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE schedule_items ADD COLUMN schedule_date VARCHAR(10)"))


ensure_schema_updates()

app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
try:
    APP_TZ = ZoneInfo(settings.app_timezone)
except ZoneInfoNotFoundError:
    # Fallback to WIB fixed offset so reminders still align with Indonesia time.
    APP_TZ = timezone(timedelta(hours=7), name="WIB")

scheduler = AsyncIOScheduler(timezone=APP_TZ)


def validate_storage_configuration() -> None:
    if settings.storage_backend.lower() != "s3":
        raise RuntimeError("STORAGE_BACKEND harus bernilai 's3' untuk mode ini")
    if not settings.s3_bucket:
        raise RuntimeError("S3_BUCKET belum diisi")


async def schedule_alert_job() -> None:
    now = datetime.now(APP_TZ)
    current_day = now.strftime("%a").lower()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    def to_hhmm(base: datetime, offset_minutes: int) -> str:
        return (base + timedelta(minutes=offset_minutes)).strftime("%H:%M")

    reminder_targets = {
        -10: to_hhmm(now, 10),
        -5: to_hhmm(now, 5),
        0: current_time,
    }

    from app.database import SessionLocal

    db = SessionLocal()
    try:
        classes = db.query(ScheduleItem).join(Course).all()
        for item in classes:
            is_today_by_date = bool(item.schedule_date and item.schedule_date == current_date)
            is_today_by_day = item.day_of_week.lower() == current_day

            if not is_today_by_date and not is_today_by_day:
                continue

            if item.start_time == reminder_targets[-10]:
                msg = f"[Kuliah Alert] 10 menit lagi: {item.course.name} mulai {item.start_time} di {item.location or '-'}"
                await send_telegram_message(msg)
            if item.start_time == reminder_targets[-5]:
                msg = f"[Kuliah Alert] 5 menit lagi: {item.course.name} mulai {item.start_time} di {item.location or '-'}"
                await send_telegram_message(msg)
            if item.start_time == reminder_targets[0]:
                msg = f"[Kuliah Alert] Sekarang mulai: {item.course.name} ({item.start_time}-{item.end_time or '-'}) di {item.location or '-'}"
                await send_telegram_message(msg)

        routines = db.query(Routine).all()
        for routine in routines:
            if routine.day_of_week.lower() == current_day and routine.reminder_time == current_time:
                msg = f"[Routine Alert] {routine.title} jam {routine.reminder_time}\nCatatan: {routine.note or '-'}"
                await send_telegram_message(msg)
    finally:
        db.close()


@app.on_event("startup")
async def on_startup() -> None:
    validate_storage_configuration()
    if not scheduler.running:
        scheduler.add_job(schedule_alert_job, "cron", minute="*", timezone=APP_TZ)
        scheduler.start()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown()


@app.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    courses = db.query(Course).order_by(Course.name).all()
    schedules = db.query(ScheduleItem).join(Course).all()
    materials = db.query(Material).join(Course).order_by(Material.uploaded_at.desc()).all()
    grades = db.query(Grade).join(Course).order_by(Grade.semester.asc()).all()
    routines = db.query(Routine).all()
    pomodoros = db.query(PomodoroSession).order_by(PomodoroSession.created_at.desc()).limit(10).all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "courses": courses,
            "schedules": schedules,
            "materials": materials,
            "grades": grades,
            "routines": routines,
            "pomodoros": pomodoros,
        },
    )


@app.post("/courses")
def create_course(name: str = Form(...), code: str = Form(default=""), db: Session = Depends(get_db)):
    payload = CourseCreate(name=name.strip(), code=code.strip() or None)
    exists = db.query(Course).filter(Course.name == payload.name).first()
    if exists:
        return RedirectResponse(url="/", status_code=303)

    course = Course(name=payload.name, code=payload.code)
    db.add(course)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/courses/{course_id}/delete")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        return RedirectResponse(url="/", status_code=303)

    db.delete(course)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/schedules")
def create_schedule(
    course_id: int = Form(...),
    schedule_date: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(default=""),
    location: str = Form(default=""),
    note: str = Form(default=""),
    db: Session = Depends(get_db),
):
    try:
        parsed_date = datetime.strptime(schedule_date.strip(), "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Format tanggal harus YYYY-MM-DD") from exc
    day_of_week = parsed_date.strftime("%a").lower()

    payload = ScheduleCreate(
        course_id=course_id,
        day_of_week=day_of_week,
        schedule_date=schedule_date.strip(),
        start_time=start_time.strip(),
        end_time=end_time.strip() or None,
        location=location.strip() or None,
        note=note.strip() or None,
    )
    item = ScheduleItem(**payload.model_dump())
    db.add(item)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/grades")
def create_grade(
    course_id: int = Form(...),
    semester: int = Form(...),
    score: float = Form(...),
    weight: float = Form(default=0),
    note: str = Form(default=""),
    db: Session = Depends(get_db),
):
    payload = GradeCreate(
        course_id=course_id,
        semester=semester,
        score=score,
        weight=weight if weight > 0 else None,
        note=note.strip() or None,
    )
    grade = Grade(**payload.model_dump())
    db.add(grade)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/routines")
def create_routine(
    title: str = Form(...),
    day_of_week: str = Form(...),
    reminder_time: str = Form(...),
    note: str = Form(default=""),
    db: Session = Depends(get_db),
):
    payload = RoutineCreate(
        title=title.strip(),
        day_of_week=day_of_week.strip().lower(),
        reminder_time=reminder_time.strip(),
        note=note.strip() or None,
    )
    routine = Routine(**payload.model_dump())
    db.add(routine)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/pomodoro")
def create_pomodoro(
    task: str = Form(...),
    focus_minutes: int = Form(...),
    break_minutes: int = Form(...),
    cycles: int = Form(...),
    db: Session = Depends(get_db),
):
    payload = PomodoroCreate(
        task=task,
        focus_minutes=focus_minutes,
        break_minutes=break_minutes,
        cycles=cycles,
    )
    session = PomodoroSession(**payload.model_dump())
    db.add(session)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/materials")
async def upload_material(
    course_id: int = Form(...),
    title: str = Form(...),
    folder_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in {".pdf", ".pptx"}:
        raise HTTPException(status_code=400, detail="Only PDF and PPTX are supported")

    safe_folder = "".join(ch for ch in folder_name if ch.isalnum() or ch in {"-", "_"})
    if not safe_folder:
        safe_folder = "general"

    new_name = f"{uuid.uuid4().hex}{ext}"
    content = await file.read()
    content_type = "application/pdf" if ext == ".pdf" else "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    if not s3_is_enabled():
        raise HTTPException(status_code=500, detail="S3 belum aktif atau konfigurasi belum lengkap")

    s3_key = f"{settings.s3_prefix.strip('/')}/{safe_folder}/{new_name}"
    s3_storage.upload_bytes(content=content, key=s3_key, content_type=content_type)
    file_path = f"s3://{settings.s3_bucket}/{s3_key}"
    web_path = s3_key

    material = Material(
        course_id=course_id,
        title=title,
        folder_name=safe_folder,
        file_name=file.filename or new_name,
        file_path=file_path,
        web_path=web_path,
    )
    db.add(material)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.get("/materials/{material_id}/open")
def open_material(material_id: int, db: Session = Depends(get_db)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    signed_url = safe_create_presigned_url(material.web_path, expires_seconds=3600)
    if not signed_url:
        raise HTTPException(status_code=500, detail="Failed to create S3 access URL")
    return RedirectResponse(url=signed_url, status_code=302)


@app.post("/materials/{material_id}/summarize")
def summarize_material(material_id: int, db: Session = Depends(get_db)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    ext = Path(material.file_name).suffix.lower()
    read_path = material.file_path
    temp_path = None

    if not s3_is_enabled():
        raise HTTPException(status_code=500, detail="S3 belum aktif atau konfigurasi belum lengkap")

    temp_path = safe_download_to_temp(material.web_path, suffix=ext)
    if not temp_path:
        raise HTTPException(status_code=500, detail="Failed to download S3 file")
    read_path = temp_path

    text = extract_text_from_material(read_path)
    if temp_path and os.path.exists(temp_path):
        os.remove(temp_path)

    summary = safe_summarize(text or "Materi kosong")
    result = AiResult(material_id=material.id, result_type="summary", content=summary)
    db.add(result)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/materials/{material_id}/quiz")
def quiz_material(material_id: int, db: Session = Depends(get_db)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    ext = Path(material.file_name).suffix.lower()
    read_path = material.file_path
    temp_path = None

    if not s3_is_enabled():
        raise HTTPException(status_code=500, detail="S3 belum aktif atau konfigurasi belum lengkap")

    temp_path = safe_download_to_temp(material.web_path, suffix=ext)
    if not temp_path:
        raise HTTPException(status_code=500, detail="Failed to download S3 file")
    read_path = temp_path

    text = extract_text_from_material(read_path)
    if temp_path and os.path.exists(temp_path):
        os.remove(temp_path)

    quiz = safe_generate_quiz(text or "Materi kosong")
    result = AiResult(material_id=material.id, result_type="quiz", content=quiz)
    db.add(result)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.get("/ai-results/{material_id}")
def material_results(request: Request, material_id: int, db: Session = Depends(get_db)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    results = db.query(AiResult).filter(AiResult.material_id == material_id).order_by(AiResult.created_at.desc()).all()
    return templates.TemplateResponse(
        "ai_results.html",
        {"request": request, "material": material, "results": results},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/debug/time")
def debug_time():
    now_local = datetime.now(APP_TZ)
    return {
        "app_timezone": str(APP_TZ),
        "now_local": now_local.isoformat(),
        "date": now_local.strftime("%Y-%m-%d"),
        "time": now_local.strftime("%H:%M"),
    }


@app.post("/debug/send-telegram")
async def debug_send_telegram():
    now_local = datetime.now(APP_TZ).strftime("%Y-%m-%d %H:%M:%S")
    sent = await send_telegram_message(f"[Debug] Test telegram dari complite-study jam {now_local} ({APP_TZ})")
    return {"sent": sent}
