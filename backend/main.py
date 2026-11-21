import os
import shutil
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import Body, FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from database import create_tables, get_connection, normalize_phone

app = FastAPI(title="LOHAS Medical Clinic System")

# --- Setup Directory Paths ---
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent if BASE_DIR.name == "backend" else BASE_DIR

ADMIN_DIR = ROOT_DIR / "admin"
PAGES_DIR = ROOT_DIR / "pages"
ASSETS_DIR = ROOT_DIR / "assets"
UPLOADS_DIR = BASE_DIR / "uploads"

os.makedirs(UPLOADS_DIR, exist_ok=True)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://lohas.synology.me",
        "https://lohasmedical.synology.me",
        "https://www.lohas.com.hk",
        "http://www.lohas.com.hk",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database tables and safe migrations on startup
create_tables()

# --- Pydantic Data Models ---

class Booking(BaseModel):
    name: str
    phone: str
    email: Optional[str] = ""
    service: str
    doctor: str
    appointment_date: str
    appointment_time: str
    source: Optional[str] = "web"
    notes: Optional[str] = ""
    # Optional online payment fields at booking time
    amount: Optional[float] = 0.0
    payment_method: Optional[str] = ""
    transaction_ref: Optional[str] = ""
    payment_status: Optional[str] = "Unpaid"  # "Unpaid" or "Paid"

class PaymentConfirm(BaseModel):
    appointment_id: int
    amount: float
    method: str = "Online"
    transaction_ref: str = ""

class PatientPackageCreate(BaseModel):
    patient_id: int
    package_id: int
    purchase_date: str
    expiry_date: Optional[str] = None

class PackageConsume(BaseModel):
    patient_id: int
    service: str

class FollowupCreate(BaseModel):
    patient_id: int
    date: str
    status: str
    notes: str
    next_followup_date: Optional[str] = None
    progress_rating: Optional[str] = None

class PatientUpdate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = ""
    birthday: Optional[str] = ""
    gender: Optional[str] = ""
    address: Optional[str] = ""
    medical_history: Optional[str] = ""
    notes: Optional[str] = ""

# --- Helper Functions ---

def _generate_member_code(patient_id: int) -> str:
    year = datetime.now().year
    return f"LM-{year}-{patient_id:04d}"

def _find_or_create_patient(cursor, name: str, phone: str, email: str) -> tuple[int, str, bool]:
    """
    Matches an existing patient by normalized phone (or email) so returning
    patients reuse one unified member profile. Creates a new profile if none exists.
    Returns: (patient_id, member_code, is_new_member)
    """
    phone_norm = normalize_phone(phone)
    clean_email = (email or "").strip().lower()

    existing = None
    if phone_norm:
        cursor.execute(
            "SELECT id, member_code FROM patients WHERE phone_normalized = ? LIMIT 1",
            (phone_norm,)
        )
        existing = cursor.fetchone()

    if not existing and clean_email:
        cursor.execute(
            "SELECT id, member_code FROM patients WHERE LOWER(email) = ? LIMIT 1",
            (clean_email,)
        )
        existing = cursor.fetchone()

    if existing:
        patient_id = existing["id"]
        member_code = existing["member_code"] or _generate_member_code(patient_id)
        if not existing["member_code"]:
            cursor.execute(
                "UPDATE patients SET member_code = ? WHERE id = ?",
                (member_code, patient_id)
            )
        if clean_email:
            cursor.execute(
                "UPDATE patients SET email = COALESCE(NULLIF(email, ''), ?) WHERE id = ?",
                (email.strip(), patient_id)
            )
        return patient_id, member_code, False

    cursor.execute(
        """
        INSERT INTO patients (name, phone, phone_normalized, email)
        VALUES (?, ?, ?, ?)
        """,
        (name.strip(), phone.strip(), phone_norm, (email or "").strip())
    )
    patient_id = cursor.lastrowid
    member_code = _generate_member_code(patient_id)

    cursor.execute(
        "UPDATE patients SET member_code = ? WHERE id = ?",
        (member_code, patient_id)
    )
    return patient_id, member_code, True

# --- API Endpoints ---

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    favicon_path = ASSETS_DIR / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    return {"message": "No favicon set"}

@app.get("/booked-slots")
def get_booked_slots(doctor: str, appointment_date: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT appointment_time
        FROM appointments
        WHERE doctor = ?
          AND appointment_date = ?
          AND COALESCE(status, 'Pending') NOT IN ('Cancelled', 'cancelled')
        """,
        (doctor, appointment_date)
    )
    rows = cursor.fetchall()
    conn.close()

    return {"booked_times": [row["appointment_time"] for row in rows]}

@app.post("/booking")
def create_booking(booking: Booking):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Check if this doctor + date + time is already booked
        cursor.execute(
            """
            SELECT id FROM appointments
            WHERE doctor = ?
              AND appointment_date = ?
              AND appointment_time = ?
              AND COALESCE(status, 'Pending') NOT IN ('Cancelled', 'cancelled')
            """,
            (booking.doctor, booking.appointment_date, booking.appointment_time)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=409,
                detail="此時段已被預約 (This time slot is already booked)"
            )

        # 2. Auto-match existing member or generate new member profile
        patient_id, member_code, is_new_member = _find_or_create_patient(
            cursor, booking.name, booking.phone, booking.email or ""
        )

        # 3. Determine initial booking & payment status
        is_paid = (booking.payment_status or "").lower() == "paid"
        appt_status = "Confirmed" if is_paid else "Pending"
        pay_status = "Paid" if is_paid else "Unpaid"

        cursor.execute(
            """
            INSERT INTO appointments (
                patient_id, service, doctor, appointment_date, appointment_time,
                status, payment_status, source, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                booking.service,
                booking.doctor,
                booking.appointment_date,
                booking.appointment_time,
                appt_status,
                pay_status,
                booking.source or "web",
                booking.notes or ""
            )
        )
        appointment_id = cursor.lastrowid

        # 4. Record payment entry if payment info was included
        if is_paid or (booking.amount and booking.amount > 0):
            cursor.execute(
                """
                INSERT INTO payments (
                    appointment_id, patient_id, amount, method, transaction_ref, status, paid_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    appointment_id,
                    patient_id,
                    booking.amount or 0.0,
                    booking.payment_method or "Online",
                    booking.transaction_ref or "",
                    pay_status,
                    datetime.now().isoformat(timespec="seconds") if is_paid else None
                )
            )

        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise HTTPException(
            status_code=409,
            detail="此時段剛剛已被預約 (This time slot was just booked)"
        )
    finally:
        conn.close()

    return {
        "message": "預約成功！ (Booking created successfully)",
        "appointment_id": appointment_id,
        "patient_id": patient_id,
        "member_code": member_code,
        "is_new_member": is_new_member,
        "status": appt_status,
        "payment_status": pay_status
    }

@app.post("/payment/confirm")
def confirm_payment(data: PaymentConfirm):
    """Marks an appointment as Paid & Confirmed and logs the transaction."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, patient_id FROM appointments WHERE id = ?", (data.appointment_id,))
    appt = cursor.fetchone()
    if not appt:
        conn.close()
        raise HTTPException(status_code=404, detail="Appointment not found")

    now_iso = datetime.now().isoformat(timespec="seconds")

    cursor.execute(
        """
        UPDATE appointments
        SET payment_status = 'Paid',
            status = CASE WHEN status = 'Pending' THEN 'Confirmed' ELSE status END
        WHERE id = ?
        """,
        (data.appointment_id,)
    )

    cursor.execute(
        """
        INSERT INTO payments (appointment_id, patient_id, amount, method, transaction_ref, status, paid_at)
        VALUES (?, ?, ?, ?, ?, 'Paid', ?)
        """,
        (data.appointment_id, appt["patient_id"], data.amount, data.method, data.transaction_ref, now_iso)
    )

    conn.commit()
    conn.close()
    return {"message": "Payment confirmed", "appointment_id": data.appointment_id}

@app.get("/calendar")
def get_calendar_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    doctor: Optional[str] = None
):
    """Returns enriched appointments for the clinic calendar view."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            a.id,
            a.patient_id,
            p.member_code,
            p.name AS patient_name,
            p.phone AS patient_phone,
            a.service,
            a.doctor,
            a.appointment_date,
            a.appointment_time,
            a.duration_mins,
            a.status,
            a.payment_status,
            a.source
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        WHERE 1 = 1
    """
    params = []

    if start_date:
        query += " AND a.appointment_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND a.appointment_date <= ?"
        params.append(end_date)
    if doctor:
        query += " AND a.doctor = ?"
        params.append(doctor)

    query += " ORDER BY a.appointment_date ASC, a.appointment_time ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

@app.get("/appointments")
def get_appointments():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            a.id, a.patient_id, p.member_code, p.name AS patient_name, p.phone AS patient_phone,
            a.service, a.doctor, a.appointment_date, a.appointment_time, a.status, a.payment_status
        FROM appointments a
        LEFT JOIN patients p ON a.patient_id = p.id
        ORDER BY a.appointment_date DESC, a.appointment_time ASC
        """
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row["id"],
            "patient_id": row["patient_id"],
            "member_code": row["member_code"],
            "patient_name": row["patient_name"],
            "patient_phone": row["patient_phone"],
            "service": row["service"],
            "doctor": row["doctor"],
            "appointment_date": row["appointment_date"],
            "appointment_time": row["appointment_time"],
            "status": row["status"],
            "payment_status": row["payment_status"]
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
            patients.id AS patient_id,
            patients.member_code,
            patients.name,
            patients.phone,
            patients.email,
            appointments.service,
            appointments.doctor,
            appointments.appointment_date,
            appointments.appointment_time,
            appointments.status,
            appointments.payment_status,
            appointments.notes
        FROM appointments
        JOIN patients ON appointments.patient_id = patients.id
        WHERE appointments.id = ?
        """,
        (appointment_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return {
        "id": row["id"],
        "patient_id": row["patient_id"],
        "member_code": row["member_code"],
        "name": row["name"],
        "phone": row["phone"],
        "email": row["email"],
        "service": row["service"],
        "doctor": row["doctor"],
        "date": row["appointment_date"],
        "time": row["appointment_time"],
        "status": row["status"],
        "payment_status": row["payment_status"],
        "notes": row["notes"]
    }

@app.put("/appointment/{appointment_id}")
def update_appointment(appointment_id: int, status: str = Body(...)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE appointments SET status = ? WHERE id = ?",
        (status, appointment_id)
    )

    conn.commit()
    conn.close()
    return {"message": "Status updated"}

@app.get("/patients")
def get_patients(q: Optional[str] = None):
    """Lists all members, with optional search by name, phone, or member_code."""
    conn = get_connection()
    cursor = conn.cursor()

    if q and q.strip():
        like_q = f"%{q.strip()}%"
        cursor.execute(
            """
            SELECT id, member_code, name, phone, email, created_at
            FROM patients
            WHERE name LIKE ? OR phone LIKE ? OR member_code LIKE ?
            ORDER BY id DESC
            """,
            (like_q, like_q, like_q)
        )
    else:
        cursor.execute("SELECT id, member_code, name, phone, email, created_at FROM patients ORDER BY id DESC")

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

@app.get("/patient/{patient_id}")
def get_patient(patient_id: int):
    """Full digital member profile including appointments, treatments, follow-ups, packages, and payments."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, member_code, name, phone, email, birthday, gender, address, medical_history, notes, created_at
        FROM patients
        WHERE id = ?
        """,
        (patient_id,)
    )
    patient = cursor.fetchone()

    if patient is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Patient not found")

    cursor.execute(
        """
        SELECT id, service, doctor, appointment_date, appointment_time, status, payment_status
        FROM appointments
        WHERE patient_id = ?
        ORDER BY appointment_date DESC, appointment_time DESC
        """,
        (patient_id,)
    )
    appointments = cursor.fetchall()

    cursor.execute(
        """
        SELECT id, appointment_id, service, doctor, date, pain_score, notes, image
        FROM treatment_records
        WHERE patient_id = ?
        ORDER BY date DESC, id DESC
        """,
        (patient_id,)
    )
    treatments = cursor.fetchall()

    cursor.execute(
        """
        SELECT id, date, next_followup_date, status, progress_rating, notes
        FROM followups
        WHERE patient_id = ?
        ORDER BY date DESC, id DESC
        """,
        (patient_id,)
    )
    followups = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            pp.id,
            pkg.name,
            pkg.service,
            pkg.sessions,
            pp.used_sessions,
            pp.purchase_date,
            pp.expiry_date,
            pp.status
        FROM patient_packages pp
        JOIN packages pkg ON pkg.id = pp.package_id
        WHERE pp.patient_id = ?
        ORDER BY pp.id DESC
        """,
        (patient_id,)
    )
    packages = cursor.fetchall()

    cursor.execute(
        """
        SELECT id, appointment_id, amount, currency, method, transaction_ref, status, paid_at
        FROM payments
        WHERE patient_id = ?
        ORDER BY id DESC
        """,
        (patient_id,)
    )
    payments = cursor.fetchall()

    conn.close()

    return {
        "id": patient["id"],
        "member_code": patient["member_code"],
        "name": patient["name"],
        "phone": patient["phone"],
        "email": patient["email"],
        "birthday": patient["birthday"],
        "gender": patient["gender"],
        "address": patient["address"],
        "medical_history": patient["medical_history"],
        "notes": patient["notes"],
        "created_at": patient["created_at"],
        "appointments": [
            {
                "id": a["id"],
                "service": a["service"],
                "doctor": a["doctor"],
                "date": a["appointment_date"],
                "time": a["appointment_time"],
                "status": a["status"],
                "payment_status": a["payment_status"]
            }
            for a in appointments
        ],
        "treatments": [dict(t) for t in treatments],
        "followups": [dict(f) for f in followups],
        "packages": [
            {
                "id": p["id"],
                "name": p["name"],
                "service": p["service"],
                "total": p["sessions"],
                "used": p["used_sessions"],
                "remaining": p["sessions"] - p["used_sessions"],
                "purchase_date": p["purchase_date"],
                "expiry_date": p["expiry_date"],
                "status": p["status"]
            }
            for p in packages
        ],
        "payments": [dict(pay) for pay in payments]
    }

@app.put("/patient/{patient_id}")
def update_patient(patient_id: int, data: PatientUpdate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE patients
        SET name = ?,
            phone = ?,
            phone_normalized = ?,
            email = ?,
            birthday = ?,
            gender = ?,
            address = ?,
            medical_history = ?,
            notes = ?
        WHERE id = ?
        """,
        (
            data.name,
            data.phone,
            normalize_phone(data.phone),
            data.email,
            data.birthday,
            data.gender,
            data.address,
            data.medical_history,
            data.notes,
            patient_id
        )
    )

    conn.commit()
    conn.close()
    return {"message": "Patient updated"}

@app.post("/treatment/upload")
def upload_treatment(
    patient_id: int = Form(...),
    date: str = Form(...),
    notes: str = Form(...),
    service: str = Form(...),
    doctor: Optional[str] = Form(""),
    appointment_id: Optional[int] = Form(None),
    pain_score: Optional[int] = Form(None),
    image: UploadFile = File(None)
):
    filename = None

    if image and image.filename:
        filename = f"{uuid.uuid4()}_{image.filename}"
        path = UPLOADS_DIR / filename

        with open(path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO treatment_records (patient_id, appointment_id, date, notes, image, service, doctor, pain_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (patient_id, appointment_id, date, notes, filename, service, doctor, pain_score)
    )

    if appointment_id:
        cursor.execute(
            "UPDATE appointments SET status = 'Completed' WHERE id = ?",
            (appointment_id,)
        )

    conn.commit()
    conn.close()
    return {"message": "Treatment uploaded"}

@app.get("/treatment/{patient_id}")
def get_treatments(patient_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, appointment_id, service, doctor, date, pain_score, notes, image
        FROM treatment_records
        WHERE patient_id = ?
        ORDER BY date DESC, id DESC
        """,
        (patient_id,)
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]

@app.post("/followup")
def add_followup(data: FollowupCreate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO followups (patient_id, date, next_followup_date, status, progress_rating, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (data.patient_id, data.date, data.next_followup_date, data.status, data.progress_rating, data.notes)
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
        SELECT id, date, next_followup_date, status, progress_rating, notes
        FROM followups
        WHERE patient_id = ?
        ORDER BY date DESC, id DESC
        """,
        (patient_id,)
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]

@app.get("/dashboard")
@app.get("/dashboard-data")
def dashboard_data():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM patients")
    patients = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*) FROM appointments
        WHERE COALESCE(status, 'Pending') NOT IN ('Cancelled', 'cancelled')
        """
    )
    bookings = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM treatment_records")
    treatments = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM followups")
    followups = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0) FROM payments
        WHERE LOWER(COALESCE(status, '')) = 'paid'
        """
    )
    paid_amount_hkd = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT service, COUNT(*) AS cnt
        FROM appointments
        WHERE COALESCE(status, 'Pending') NOT IN ('Cancelled', 'cancelled')
        GROUP BY service
        ORDER BY cnt DESC
        """
    )
    services = cursor.fetchall()

    conn.close()

    return {
        "patients": patients,
        "bookings": bookings,
        "treatments": treatments,
        "followups": followups,
        "paid_amount_hkd": paid_amount_hkd,
        "services": [
            {"name": s["service"], "count": s["cnt"]}
            for s in services
        ]
    }

@app.get("/packages")
def get_packages():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, service, sessions, price FROM packages")
    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]

@app.post("/patient-package")
def add_patient_package(data: PatientPackageCreate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO patient_packages (patient_id, package_id, purchase_date, expiry_date)
        VALUES (?, ?, ?, ?)
        """,
        (data.patient_id, data.package_id, data.purchase_date, data.expiry_date)
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
            pp.id,
            pkg.name,
            pkg.service,
            pkg.sessions,
            pp.used_sessions,
            pp.purchase_date,
            pp.expiry_date,
            pp.status
        FROM patient_packages pp
        JOIN packages pkg ON pkg.id = pp.package_id
        WHERE pp.patient_id = ?
        ORDER BY pp.id DESC
        """,
        (patient_id,)
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r["id"],
            "name": r["name"],
            "service": r["service"],
            "total": r["sessions"],
            "used": r["used_sessions"],
            "remaining": r["sessions"] - r["used_sessions"],
            "purchase_date": r["purchase_date"],
            "expiry_date": r["expiry_date"],
            "status": r["status"]
        }
        for r in rows
    ]

@app.post("/consume-package")
def consume_package(data: PackageConsume):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            pp.id,
            pkg.sessions,
            pp.used_sessions
        FROM patient_packages pp
        JOIN packages pkg ON pkg.id = pp.package_id
        WHERE pp.patient_id = ?
          AND pkg.service = ?
          AND pp.status = 'Active'
          AND pp.used_sessions < pkg.sessions
        ORDER BY pp.id ASC
        LIMIT 1
        """,
        (data.patient_id, data.service)
    )

    package = cursor.fetchone()

    if not package:
        conn.close()
        raise HTTPException(status_code=404, detail="No active package with remaining sessions found")

    new_used = package["used_sessions"] + 1
    new_status = "Completed" if new_used >= package["sessions"] else "Active"

    cursor.execute(
        "UPDATE patient_packages SET used_sessions = ?, status = ? WHERE id = ?",
        (new_used, new_status, package["id"])
    )
    conn.commit()
    conn.close()

    return {
        "message": "Session consumed",
        "used_sessions": new_used,
        "remaining_sessions": package["sessions"] - new_used,
        "status": new_status
    }

# --- Static Files & Frontend HTML Mounts ---

if UPLOADS_DIR.exists():
    app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

if ADMIN_DIR.exists():
    app.mount("/admin", StaticFiles(directory=str(ADMIN_DIR), html=True), name="admin")

if PAGES_DIR.exists():
    app.mount("/pages", StaticFiles(directory=str(PAGES_DIR), html=True), name="pages")

if ROOT_DIR.exists():
    app.mount("/", StaticFiles(directory=str(ROOT_DIR), html=True), name="root")

# --- Entrypoint ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)