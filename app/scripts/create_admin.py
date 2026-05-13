"""Admin kullanici olusturucu CLI.

Kullanim:
    python -m app.scripts.create_admin --email admin@example.com --name "Admin" --password gizli123

Ortam degiskeni ile (interaktif olmadan):
    ADMIN_PASSWORD=gizli123 python -m app.scripts.create_admin --email admin@example.com --name "Admin"

Eger email zaten varsa parolayi gunceller (idempotent).
"""

import argparse
import asyncio
import getpass
import os
import sys

from app.db.crud import admin_users as admin_crud
from app.db.session import SessionLocal


async def run(email: str, name: str, password: str) -> None:
    email = email.lower().strip()
    async with SessionLocal() as db:
        existing = await admin_crud.get_by_email(db, email)
        if existing:
            await admin_crud.set_password(db, existing, password)
            existing.name = name
            existing.is_active = True
            await db.commit()
            print(f"UPDATED admin user: id={existing.id} email={email}")
        else:
            user = await admin_crud.create(
                db, email=email, password=password, name=name
            )
            await db.commit()
            print(f"CREATED admin user: id={user.id} email={email}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Admin kullanici olustur veya parolasini guncelle."
    )
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default="Admin")
    parser.add_argument(
        "--password",
        default=None,
        help="CLI'dan password. Yoksa ADMIN_PASSWORD env veya prompt.",
    )
    args = parser.parse_args()

    password = args.password or os.environ.get("ADMIN_PASSWORD")
    if not password:
        password = getpass.getpass("Password: ")
    if not password:
        print("ERROR: password gerekli", file=sys.stderr)
        sys.exit(1)
    if len(password) < 8:
        print("ERROR: password en az 8 karakter olmali", file=sys.stderr)
        sys.exit(1)

    asyncio.run(run(args.email, args.name, password))


if __name__ == "__main__":
    main()
