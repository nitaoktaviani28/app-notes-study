from app.database import Base, engine, SessionLocal
from app.models import Course


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        defaults = [
            ("Algoritma", "IF101"),
            ("Basis Data", "IF202"),
            ("Sistem Operasi", "IF303"),
        ]
        for name, code in defaults:
            exists = db.query(Course).filter(Course.name == name).first()
            if not exists:
                db.add(Course(name=name, code=code))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    run()
