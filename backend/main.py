import os
import shutil
import uuid
from pathlib import Path
from fastapi import Body, FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from database import create_tables, get_connection

app = FastAPI()

# --- Setup Directory Paths ---
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent if (BASE_DIR / "main.py").exists() and BASE_DIR.name == "backend" else BASE_DIR

ADMIN_DIR = ROOT_DIR / "admin"
PAGES_DIR = ROOT_DIR / "pages"
ASSETS_DIR = ROOT_DIR / "assets"
UPLOADS_DIR = ROOT_DIR / "uploads"

# Ensure uploads folder exists
os.makedirs(UPLOADS_DIR, exist_ok=True)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://lohasmedical.synology.me",
        "https://www.lohas.com.hk",
        "http://www.lohas.com.hk",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database tables on startup
create_tables()


# --- Pydantic Data Models ---

class Booking(BaseModel):
    name: str
    phone: str
    email: str
    service: str
    appointment_date: str
    appointment_time: str


class PatientPackageCreate(BaseModel):
    patient_id: int
    package_id: int
    purchase_date: str


class TreatmentCreate(BaseModel):
    patient_id: int
    date: str
    notes: str


class FollowupCreate(BaseModel):
    patient_id: int
    date: str
    status: str
    notes: str


class PatientUpdate(BaseModel):
    name: str
    phone: str
    email: str
    birthday: str
    gender: str
    address: str
    notes: str


# --- API Endpoints ---

@app.post("/booking")
def create_booking(booking: Booking):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO patients (name, phone, email)
        VALUES (?, ?, ?)
        """,
        (booking.name, booking.phone, booking.email)
    )
    patient_id = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO appointments (patient_id, service, appointment_date, appointment_time)
        VALUES (?, ?, ?, ?)
        """,
        (patient_id, booking.service, booking.appointment_date, booking.appointment_time)
    )

    conn.commit()
    conn.close()

    return {"message": "Booking created successfully"}


@app.get("/appointments")
def get_appointments():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM appointments")
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "patient_id": row[1],
            "service": row[2],
            "appointment_date": row[3],
            "appointment_time": row[4],
            "status": row[5]
        }
        for row in rows
    ]


@app.get("/appointment/{appointment_id}")
def get_appointment(appointment_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            appointments.id,
            patients.name,
            patients.phone,
            patients.email,
            appointments.service,
            appointments.appointment_date,
            appointments.appointment_time,
            appointments.status
        FROM appointments
        JOIN patients ON appointments.patient_id = patients.id
        WHERE appointments.id = ?
        """,
        (appointment_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return {"error": "Appointment not found"}

    return {
        "id": row[0],
        "name": row[1],
        "phone": row[2],
        "email": row[3],
        "service": row[4],
        "date": row[5],
        "time": row[6],
        "status": row[7]
    }


@app.put("/appointment/{appointment_id}")
def update_appointment(appointment_id: int, status: str = Body(...)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE appointments
        SET status = ?
        WHERE id = ?
        """,
        (status, appointment_id)
    )

    conn.commit()
    conn.close()

    return {"message": "Status updated"}


@app.get("/patients")
def get_patients():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM patients")
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "phone": row[2],
            "email": row[3]
        }
        for row in rows
    ]


@app.get("/patient/{patient_id}")
def get_patient(patient_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM patients WHERE id=?", (patient_id,))
    patient = cursor.fetchone()

    cursor.execute(
        """
        SELECT service, appointment_date, status
        FROM appointments
        WHERE patient_id=?
        """,
        (patient_id,)
    )
    appointments = cursor.fetchall()

    conn.close()

    if patient is None:
        return {"error": "Patient not found"}

    return {
        "id": patient[0],
        "name": patient[1],
        "phone": patient[2],
        "email": patient[3],
        "birthday": patient[4],
        "gender": patient[5],
        "address": patient[6],
        "notes": patient[7],
        "appointments": [
            {
                "service": a[0],
                "date": a[1],
                "status": a[2]
            }
            for a in appointments
        ]
    }


@app.post("/treatment")
def add_treatment(data: TreatmentCreate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO treatment_records (patient_id, date, notes)
        VALUES (?, ?, ?)
        """,
        (data.patient_id, data.date, data.notes)
    )

    conn.commit()
    conn.close()

    return {"message": "Treatment record added"}


@app.get("/treatment/{patient_id}")
def get_treatments(patient_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT date, notes, image
        FROM treatment_records
        WHERE patient_id=?
        """,
        (patient_id,)
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "date": r[0],
            "notes": r[1],
            "image": r[2]
        }
        for r in rows
    ]


@app.post("/treatment/upload")
def upload_treatment(
    patient_id: int = Form(...),
    date: str = Form(...),
    notes: str = Form(...),
    service: str = Form(...),
    image: UploadFile = File(None)
):
    filename = None

    if image:
        filename = f"{uuid.uuid4()}_{image.filename}"
        path = UPLOADS_DIR / filename

        with open(path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO treatment_records (patient_id, date, notes, image, service)
        VALUES (?, ?, ?, ?, ?)
        """,
        (patient_id, date, notes, filename, service)
    )

    conn.commit()
    conn.close()

    return {"message": "Treatment uploaded"}


@app.post("/followup")
def add_followup(data: FollowupCreate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO followups (patient_id, date, status, notes)
        VALUES (?, ?, ?, ?)
        """,
        (data.patient_id, data.date, data.status, data.notes)
    )

    conn.commit()
    conn.close()

    return {"message": "Follow-up added"}


@app.get("/followup/{patient_id}")
def get_followups(patient_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT date, status, notes
        FROM followups
        WHERE patient_id=?
        """,
        (patient_id,)
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "date": r[0],
            "status": r[1],
            "notes": r[2]
        }
        for r in rows
    ]


@app.get("/dashboard-data")
def dashboard_data():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM patients")
    patients = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM appointments")
    bookings = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM treatment_records")
    treatments = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT service, COUNT(*)
        FROM appointments
        GROUP BY service
        ORDER BY COUNT(*) DESC
        """
    )
    services = cursor.fetchall()

    conn.close()

    return {
        "patients": patients,
        "bookings": bookings,
        "treatments": treatments,
        "services": [
            {"name": s[0], "count": s[1]}
            for s in services
        ]
    }


@app.put("/patient/{patient_id}")
def update_patient(patient_id: int, data: PatientUpdate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE patients
        SET name=?, phone=?, email=?, birthday=?, gender=?, address=?, notes=?
        WHERE id=?
        """,
        (
            data.name,
            data.phone,
            data.email,
            data.birthday,
            data.gender,
            data.address,
            data.notes,
            patient_id
        )
    )

    conn.commit()
    conn.close()

    return {"message": "Patient updated"}


@app.get("/packages")
def get_packages():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM packages")
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "name": r[1],
            "service": r[2],
            "sessions": r[3],
            "price": r[4]
        }
        for r in rows
    ]


@app.post("/patient-package")
def add_patient_package(data: PatientPackageCreate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO patient_packages (patient_id, package_id, purchase_date)
        VALUES (?, ?, ?)
        """,
        (data.patient_id, data.package_id, data.purchase_date)
    )

    conn.commit()
    conn.close()

    return {"message": "Package assigned"}


@app.get("/patient-packages/{patient_id}")
def get_patient_packages(patient_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            packages.name,
            packages.total_sessions,
            patient_packages.used_sessions,
            patient_packages.status
        FROM patient_packages
        JOIN packages ON packages.id = patient_packages.package_id
        WHERE patient_packages.patient_id=?
        """,
        (patient_id,)
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "name": r[0],
            "total": r[1],
            "used": r[2],
            "remaining": r[1] - r[2],
            "status": r[3]
        }
        for r in rows
    ]


@app.post("/consume-package")
def consume_package(patient_id: int, service: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            patient_packages.id,
            packages.total_sessions,
            patient_packages.used_sessions
        FROM patient_packages
        JOIN packages ON packages.id = patient_packages.package_id
        WHERE patient_packages.patient_id=?
          AND packages.service=?
          AND patient_packages.status='Active'
        LIMIT 1
        """,
        (patient_id, service)
    )

    package = cursor.fetchone()

    if package:
        cursor.execute(
            """
            UPDATE patient_packages
            SET used_sessions = used_sessions + 1
            WHERE id=?
            """,
            (package[0],)
        )
        conn.commit()

    conn.close()

    return {"message": "consumed"}


# --- Static Files & Frontend HTML Mounts ---

# 1. Uploaded treatment images
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# 2. Assets (CSS, JS, images used across the site)
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

# 3. Admin Panel (Accessible at https://lohas.synology.me/admin/)
if ADMIN_DIR.exists():
    app.mount("/admin", StaticFiles(directory=str(ADMIN_DIR), html=True), name="admin")

# 4. Pages Folder (Accessible at https://lohas.synology.me/pages/...)
if PAGES_DIR.exists():
    app.mount("/pages", StaticFiles(directory=str(PAGES_DIR), html=True), name="pages")

# 5. Root Directory Index/Public Files (Accessible at https://lohas.synology.me/)
if ROOT_DIR.exists():
    app.mount("/", StaticFiles(directory=str(ROOT_DIR), html=True), name="root")


# --- Entrypoint ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
