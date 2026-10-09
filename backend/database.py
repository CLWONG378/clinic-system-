import sqlite3
import os

DATABASE = os.getenv("DATABASE_PATH", "clinic.db")


def get_connection():
    conn = sqlite3.connect(DATABASE)
    # Return query rows as dictionaries/Row objects for cleaner FastAPI JSON serializing
    conn.row_factory = sqlite3.Row
    # Enable SQLite Foreign Key constraints
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Patients Table (extended with profile fields used in member-profile)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        birthday TEXT,
        gender TEXT,
        address TEXT,
        notes TEXT
    )
    """)

    # 2. Appointments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        service TEXT,
        appointment_date TEXT,
        appointment_time TEXT,
        status TEXT DEFAULT 'Pending',
        FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
    )
    """)

    # 3. Treatment Records Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS treatment_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        service TEXT,
        date TEXT,
        notes TEXT,
        image TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
    )
    """)

    # 4. Customer Followups Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS followups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        date TEXT,
        status TEXT,
        notes TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
    )
    """)

    # 5. Packages Table (Standardized 'sessions' column)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        service TEXT,
        sessions INTEGER NOT NULL,
        price REAL
    )
    """)

    # 6. Patient Purchased Packages Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patient_packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        package_id INTEGER,
        used_sessions INTEGER DEFAULT 0,
        purchase_date TEXT,
        status TEXT DEFAULT 'Active',
        FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE,
        FOREIGN KEY(package_id) REFERENCES packages(id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully!")
