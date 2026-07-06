import sys

from app.core.config import settings
from app.core.database import SessionLocal
from app.crud.users import any_admin_exists, create_user


def seed_admin() -> None:
    db = SessionLocal()
    try:
        if any_admin_exists(db):
            print("An admin user already exists — skipping seed.")
            return
        create_user(
            db,
            name="Admin",
            email=settings.admin_email,
            password=settings.admin_password,
            role="admin",
            branch_id=None,
        )
        print(f"Created default admin: {settings.admin_email}")
    finally:
        db.close()


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] != "seed-admin":
        print("Usage: python -m app.cli seed-admin")
        sys.exit(1)
    seed_admin()


if __name__ == "__main__":
    main()
