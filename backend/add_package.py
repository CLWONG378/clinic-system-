import sqlite3

def seed_packages():
    conn = sqlite3.connect("clinic.db")
    cursor = conn.cursor()

    # Ensure the table exists with standardized column names
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            service TEXT NOT NULL,
            sessions INTEGER NOT NULL,
            price REAL NOT NULL
        )
    """)

    # Default packages seed data
    default_packages = [
        ("脊柱矯正10次套餐", "spinal_correction", 10, 5000),
        ("疼痛康復5次套餐", "pain_rehabilitation", 5, 2800),
        ("體態調整8次套餐", "posture_adjustment", 8, 4200),
        ("足科治療6次套餐", "foot_treatment", 6, 3200)
    ]

    for name, service, sessions, price in default_packages:
        # Prevent duplicate inserts on repeated runs
        cursor.execute("SELECT id FROM packages WHERE name = ?", (name,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO packages (name, service, sessions, price)
                VALUES (?, ?, ?, ?)
            """, (name, service, sessions, price))
            print(f"Added package: {name}")
        else:
            print(f"Package already exists: {name}")

    conn.commit()
    conn.close()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_packages()
