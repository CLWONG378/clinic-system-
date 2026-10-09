import sqlite3
import os

DATABASE = os.getenv("DATABASE_PATH", "clinic.db")

def migrate_treatment_records_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Fetch existing columns in treatment_records
    cursor.execute("PRAGMA table_info(treatment_records)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    if "service" not in existing_columns:
        cursor.execute("ALTER TABLE treatment_records ADD COLUMN service TEXT")
        print("Added 'service' column to treatment_records table.")
    else:
        print("Column 'service' already exists in treatment_records. Skipped.")

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate_treatment_records_table()
