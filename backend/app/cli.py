import sys

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.crud.stock_items import create_stock_item
from app.crud.users import any_admin_exists, any_superuser_exists, create_user
from app.models.stock_item import StockItem

STOCK_ITEMS_SEED = [
    # name, unit, price (peso), category
    ("Pork belly (liempo)", "kg", 320.0, "Meats"),
    ("Pork jowl (pigue/kasim)", "kg", 300.0, "Meats"),
    ("Pork skirt/secreto", "kg", 380.0, "Meats"),
    ("Beef bulgogi cut", "kg", 450.0, "Meats"),
    ("Chicken thigh (boneless)", "kg", 260.0, "Meats"),
    ("Squid", "kg", 300.0, "Meats"),
    ("Shrimp (medium)", "kg", 400.0, "Meats"),
    ("Kimchi (bulk pack)", "kg", 220.0, "Side Dishes / Banchan"),
    ("Fish cake (odeng)", "kg", 180.0, "Side Dishes / Banchan"),
    ("Egg roll (gyeranmari)", "pcs", 260.0, "Side Dishes / Banchan"),
    ("Japchae noodles", "kg", 150.0, "Side Dishes / Banchan"),
    ("Rice", "sack", 1500.0, "Rice & Staples"),
    ("Cooking Oil", "box", 1200.0, "Rice & Staples"),
    ("Garlic", "kg", 120.0, "Rice & Staples"),
    ("Union", "kg", 80.0, "Rice & Staples"),
    ("Lettuce", "kg", 150.0, "Rice & Staples"),
    ("Perilla leaves", "kg", 250.0, "Rice & Staples"),
    ("Ssamjang", "kg", 680.0, "Sauces & Condiments"),
    ("Gochujang", "kg", 750.0, "Sauces & Condiments"),
    ("Sesame oil", "L", 350.0, "Sauces & Condiments"),
    ("Soy sauce", "L", 350.0, "Sauces & Condiments"),
    ("Vinegar", "L", 150.0, "Sauces & Condiments"),
    ("Soft Drinks", "bottle", 450.0, "Drinks"),
    ("Bottled water", "bottle", 200.0, "Drinks"),
    ("Soju (Korean import)", "bottle", 2400.0, "Drinks"),
    ("Charcoal", "sack", 350.0, "Consumables/Supplies"),
    ("Aluminum foil", "roll", 200.0, "Consumables/Supplies"),
    ("Grill mesh/net", "pack", 150.0, "Consumables/Supplies"),
    ("Disposable gloves", "box", 180.0, "Consumables/Supplies"),
]


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


def seed_superuser() -> None:
    db = SessionLocal()
    try:
        if any_superuser_exists(db):
            print("A superuser already exists — skipping seed.")
            return
        create_user(
            db,
            name="Superuser",
            email=settings.superuser_email,
            password=settings.superuser_password,
            role="superuser",
            branch_id=None,
        )
        print(f"Created default superuser: {settings.superuser_email}")
    finally:
        db.close()


def seed_stock_items() -> None:
    db = SessionLocal()
    try:
        existing_names = set(db.scalars(select(StockItem.name)))
        created = 0
        for name, unit, price, category in STOCK_ITEMS_SEED:
            if name in existing_names:
                continue
            create_stock_item(db, name=name, unit=unit, price=price, category=category)
            created += 1
        print(f"Created {created} stock item(s), skipped {len(STOCK_ITEMS_SEED) - created} existing.")
    finally:
        db.close()


def main() -> None:
    commands = ("seed-admin", "seed-superuser", "seed-stock-items")
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print(f"Usage: python -m app.cli {'|'.join(commands)}")
        sys.exit(1)
    if sys.argv[1] == "seed-admin":
        seed_admin()
    elif sys.argv[1] == "seed-superuser":
        seed_superuser()
    else:
        seed_stock_items()


if __name__ == "__main__":
    main()
