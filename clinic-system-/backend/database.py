import sqlite3


DATABASE = "clinic.db"



def get_connection():

    conn = sqlite3.connect(DATABASE)

    return conn





def create_tables():

    conn = get_connection()

    cursor = conn.cursor()



    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL,

        phone TEXT,

        email TEXT

    )
    """)




    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        patient_id INTEGER,

        service TEXT,

        appointment_date TEXT,

        appointment_time TEXT,

        status TEXT DEFAULT 'Pending'

    )
    """)




    cursor.execute("""
    CREATE TABLE IF NOT EXISTS treatment_records (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    patient_id INTEGER,

    date TEXT,

    notes TEXT,

    image TEXT,

    FOREIGN KEY(patient_id)
    REFERENCES patients(id)

    )
    """)

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS followups (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    patient_id INTEGER,

    date TEXT,

    status TEXT,

    notes TEXT,

    FOREIGN KEY(patient_id)
    REFERENCES patients(id)

    )

    """)

    cursor.execute("""

CREATE TABLE IF NOT EXISTS packages (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT,

    service TEXT,

    total_sessions INTEGER,

    price REAL

)

""")


    cursor.execute("""

    CREATE TABLE IF NOT EXISTS patient_packages (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    patient_id INTEGER,

    package_id INTEGER,

    used_sessions INTEGER DEFAULT 0,

    purchase_date TEXT,

    status TEXT DEFAULT 'Active',

    FOREIGN KEY(patient_id)
    REFERENCES patients(id),

    FOREIGN KEY(package_id)
    REFERENCES packages(id)

)

""")






    conn.commit()

    conn.close()


    