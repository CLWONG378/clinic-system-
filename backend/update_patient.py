import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE = os.getenv("DATABASE_PATH", str(BASE_DIR / "clinic.db"))


def normalize_phone(phone: str | None) -> str:
    """Strips spaces, dashes, and '+' so returning members match reliably."""
    if not phone:
        return ""
    return re.sub(r"[^\d]", "", phone)


def migrate_patients_table():
    conn = sqlite3.connect(DATABASE, timeout=15.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Fetch current existing columns in 'patients' table
    cursor.execute("PRAGMA table_info(patients)")
    existing_columns = {row["name"] for row in cursor.fetchall()}

    # 2. Columns to add if missing (profile + paperless member fields)
    columns_to_add = [
        ("member_code", "TEXT"),
        ("phone_normalized", "TEXT"),
        ("birthday", "TEXT"),
        ("gender", "TEXT"),
        ("address", "TEXT"),
        ("medical_history", "TEXT"),
        ("notes", "TEXT"),
        ("created_at", "TEXT"),
    ]

    for col, col_type in columns_to_add:
        if col not in existing_columns:
            cursor.execute(f"ALTER TABLE patients ADD COLUMN {col} {col_type}")
            print(f"Added column '{col}' to patients table.")
        else:
            print(f"Column '{col}' already exists. Skipped.")

    # 3. Backfill phone_normalized, member_code, and created_at for existing rows
    current_year = datetime.now().year
    cursor.execute("SELECT id, phone, member_code, created_at FROM patients")
    rows = cursor.fetchall()

    for row in rows:
        patient_id = row["id"]
        norm_phone = normalize_phone(row["phone"])
        member_code = row["member_code"] or f"LM-{current_year}-{patient_id:04d}"
        created_at = row["created_at"] or datetime.now().isoformat(timespec="seconds")

        cursor.execute(
            """
            UPDATE patients
            SET phone_normalized = ?,
                member_code = ?,
                created_at = ?
            WHERE id = ?
            """,
            (norm_phone, member_code, created_at, patient_id)
        )

    # 4. Ensure index for fast member lookup
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_patients_phone_norm ON patients(phone_normalized)"
    )

    conn.commit()
    conn.close()
    print(f"Database migration complete! Processed {len(rows)} patient record(s).")


if __name__ == "__main__":
    migrate_patients_table()