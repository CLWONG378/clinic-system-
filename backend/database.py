import os
import re
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE = os.getenv("DATABASE_PATH", str(BASE_DIR / "clinic.db"))


def normalize_phone(phone: str | None) -> str:
    """Strips spaces, dashes, and '+' so returning members match reliably."""
    if not phone:
        return ""
    return re.sub(r"[^\d]", "", phone)


def get_connection():
    conn = sqlite3.connect(DATABASE, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def _ensure_column(cursor, table: str, column: str, definition: str):
    """Adds a column to an existing table only if it does not already exist."""
    cursor.execute(f"PRAGMA table_info({table})")
    existing = {row["name"] for row in cursor.fetchall()}
    if column not in existing:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Patients / Member Profiles
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_code TEXT UNIQUE,
        name TEXT NOT NULL,
        phone TEXT,
        phone_normalized TEXT,
        email TEXT,
        birthday TEXT,
        gender TEXT,
        address TEXT,
        medical_history TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Appointments & Calendar
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        service TEXT NOT NULL,
        doctor TEXT DEFAULT '',
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        duration_mins INTEGER DEFAULT 30,
        status TEXT DEFAULT 'Pending',
        payment_status TEXT DEFAULT 'Unpaid',
        source TEXT DEFAULT 'web',
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
    )
    """)

    # 3. Online Payments Audit Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER,
        patient_id INTEGER NOT NULL,
        amount REAL NOT NULL DEFAULT 0,
        currency TEXT DEFAULT 'HKD',
        method TEXT DEFAULT 'Online',
        transaction_ref TEXT,
        status TEXT DEFAULT 'Pending',
        paid_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(appointment_id) REFERENCES appointments(id) ON DELETE SET NULL,
        FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
    )
    """)

    # 4. Treatment Records & Clinical Progress
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS treatment_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        appointment_id INTEGER,
        service TEXT,
        doctor TEXT,
        date TEXT NOT NULL,
        pain_score INTEGER,
        notes TEXT,
        image TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE,
        FOREIGN KEY(appointment_id) REFERENCES appointments(id) ON DELETE SET NULL
    )
    """)

    # 5. Follow-Ups & Recovery Tracking
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS followups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        next_followup_date TEXT,
        status TEXT,
        progress_rating TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
    )
    """)

    # 6. Service Packages Catalog
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        service TEXT,
        sessions INTEGER NOT NULL,
        price REAL
    )
    """)

    # 7. Patient Purchased Packages
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patient_packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        package_id INTEGER NOT NULL,
        used_sessions INTEGER DEFAULT 0,
        purchase_date TEXT,
        expiry_date TEXT,
        status TEXT DEFAULT 'Active',
        FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE,
        FOREIGN KEY(package_id) REFERENCES packages(id) ON DELETE CASCADE
    )
    """)

    # Safe migrations for existing clinic.db files
    _ensure_column(cursor, "patients", "member_code", "TEXT")
    _ensure_column(cursor, "patients", "phone_normalized", "TEXT")
    _ensure_column(cursor, "patients", "medical_history", "TEXT")
    _ensure_column(cursor, "patients", "created_at", "TEXT DEFAULT CURRENT_TIMESTAMP")

    _ensure_column(cursor, "appointments", "doctor", "TEXT DEFAULT ''")
    _ensure_column(cursor, "appointments", "duration_mins", "INTEGER DEFAULT 30")
    _ensure_column(cursor, "appointments", "payment_status", "TEXT DEFAULT 'Unpaid'")
    _ensure_column(cursor, "appointments", "source", "TEXT DEFAULT 'web'")
    _ensure_column(cursor, "appointments", "notes", "TEXT")
    _ensure_column(cursor, "appointments", "created_at", "TEXT DEFAULT CURRENT_TIMESTAMP")

    _ensure_column(cursor, "treatment_records", "appointment_id", "INTEGER")
    _ensure_column(cursor, "treatment_records", "doctor", "TEXT")
    _ensure_column(cursor, "treatment_records", "pain_score", "INTEGER")
    _ensure_column(cursor, "treatment_records", "created_at", "TEXT DEFAULT CURRENT_TIMESTAMP")

    _ensure_column(cursor, "followups", "next_followup_date", "TEXT")
    _ensure_column(cursor, "followups", "progress_rating", "TEXT")
    _ensure_column(cursor, "followups", "created_at", "TEXT DEFAULT CURRENT_TIMESTAMP")

    _ensure_column(cursor, "patient_packages", "expiry_date", "TEXT")

    # Backfill normalized phones for existing patients
    cursor.execute("SELECT id, phone FROM patients WHERE phone IS NOT NULL AND (phone_normalized IS NULL OR phone_normalized = '')")
    for row in cursor.fetchall():
        cursor.execute(
            "UPDATE patients SET phone_normalized = ? WHERE id = ?",
            (normalize_phone(row["phone"]), row["id"])
        )

    # Helpful indexes for calendar, profile lookups, and duplicate slot prevention
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_patients_phone_norm ON patients(phone_normalized)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_date_doctor ON appointments(appointment_date, doctor)")
    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS uq_active_appointment_slot
    ON appointments (doctor, appointment_date, appointment_time)
    WHERE COALESCE(status, 'Pending') NOT IN ('Cancelled', 'cancelled')
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()
    print("Database tables and migrations ready!")