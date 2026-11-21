import os
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE = os.getenv("DATABASE_PATH", str(BASE_DIR / "clinic.db"))


def migrate_treatment_records_table():
    conn = sqlite3.connect(DATABASE, timeout=15.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Fetch existing columns in treatment_records
    cursor.execute("PRAGMA table_info(treatment_records)")
    existing_columns = {row["name"] for row in cursor.fetchall()}

    # 2. Columns to add if missing
    columns_to_add = [
        ("appointment_id", "INTEGER"),
        ("service", "TEXT"),
        ("doctor", "TEXT"),
        ("pain_score", "INTEGER"),
        ("created_at", "TEXT"),
    ]

    for col, col_type in columns_to_add:
        if col not in existing_columns:
            cursor.execute(f"ALTER TABLE treatment_records ADD COLUMN {col} {col_type}")
            print(f"Added '{col}' column to treatment_records table.")
        else:
            print(f"Column '{col}' already exists in treatment_records. Skipped.")

    # 3. Backfill created_at for existing treatment records if missing
    now_iso = datetime.now().isoformat(timespec="seconds")
    cursor.execute(
        """
        UPDATE treatment_records
        SET created_at = COALESCE(NULLIF(created_at, ''), date, ?)
        WHERE created_at IS NULL OR created_at = ''
        """,
        (now_iso,)
    )

    conn.commit()
    conn.close()
    print("Migration complete!")


if __name__ == "__main__":
    migrate_treatment_records_table()