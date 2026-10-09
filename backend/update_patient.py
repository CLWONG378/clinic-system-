import sqlite3
import os

DATABASE = os.getenv("DATABASE_PATH", "clinic.db")


def migrate_patients_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # 1. Fetch current existing columns in 'patients' table
    cursor.execute("PRAGMA table_info(patients)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    # 2. Columns to add if missing
    columns_to_add = ["birthday", "gender", "address", "notes"]

    for col in columns_to_add:
        if col not in existing_columns:
            cursor.execute(f"ALTER TABLE patients ADD COLUMN {col} TEXT")
            print(f"Added column '{col}' to patients table.")
        else:
            print(f"Column '{col}' already exists. Skipped.")

    conn.commit()
    conn.close()
    print("Database migration complete!")


if __name__ == "__main__":
    migrate_patients_table()
