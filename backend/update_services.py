import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE = os.getenv("DATABASE_PATH", str(BASE_DIR / "clinic.db"))

# Mapping of standardized backend keys to English, Traditional Chinese, and Simplified Chinese variants
SERVICE_MAPPINGS = {
    "spinal_correction": [
        "Spinal Correction",
        "脊柱矯正",
        "脊柱矫正",
        "脊椎矯正",
        "脊椎矫正",
    ],
    "pain_rehabilitation": [
        "Pain Rehabilitation",
        "疼痛康復",
        "疼痛康复",
    ],
    "postpartum_recovery": [
        "Postpartum Recovery",
        "產後康復",
        "產后康復",
        "产后康复",
    ],
    "posture_adjustment": [
        "Posture Adjustment",
        "體態調整",
        "体态调整",
    ],
    "foot_treatment": [
        "Foot Treatment",
        "足科治療",
        "足科治疗",
    ],
    "chinese_orthopedics": [
        "Chinese Orthopedics",
        "中醫骨科",
        "中医骨科",
    ],
    "psychological_consultation": [
        "Psychological Consultation",
        "心理諮詢",
        "心理咨詢",
        "心理咨询",
    ],
    "nutrition": [
        "Nutrition",
        "Nutrition Therapy",
        "營養食療",
        "营养食疗",
    ],
    "online_consultation": [
        "Online Consultation",
        "網上診症",
        "网上诊症",
    ],
}

TABLES_WITH_SERVICE = ["appointments", "treatment_records", "packages"]


def normalize_service_names():
    conn = sqlite3.connect(DATABASE, timeout=15.0)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    total_updated = 0

    for table in TABLES_WITH_SERVICE:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = {row["name"] for row in cursor.fetchall()}
        if "service" not in columns:
            continue

        for standardized_key, variants in SERVICE_MAPPINGS.items():
            # Include the standardized key itself in case it has trailing spaces or casing differences
            candidates = list(dict.fromkeys([standardized_key, *variants]))

            for variant in candidates:
                clean_variant = variant.strip().lower()
                cursor.execute(
                    f"""
                    UPDATE {table}
                    SET service = ?
                    WHERE service IS NOT NULL
                      AND service != ?
                      AND LOWER(TRIM(service)) = ?
                    """,
                    (standardized_key, standardized_key, clean_variant)
                )
                count = cursor.rowcount
                if count > 0:
                    print(f"[{table}] Updated {count} record(s): '{variant}' -> '{standardized_key}'")
                    total_updated += count

    conn.commit()
    conn.close()
    print(f"\nService normalization complete! Total records updated: {total_updated}")


if __name__ == "__main__":
    normalize_service_names()