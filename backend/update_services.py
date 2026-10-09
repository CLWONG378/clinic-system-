import sqlite3
import os

DATABASE = os.getenv("DATABASE_PATH", "clinic.db")

# Mapping of legacy text / Chinese strings to standardized backend keys
SERVICE_MAPPINGS = {
    "spinal_correction": ["Spinal Correction", "脊柱矯正", "脊椎矯正"],
    "pain_rehabilitation": ["Pain Rehabilitation", "疼痛康復"],
    "postpartum_recovery": ["Postpartum Recovery", "產後康復", "產后康復"],
    "posture_adjustment": ["Posture Adjustment", "體態調整"],
    "foot_treatment": ["Foot Treatment", "足科治療"],
    "chinese_orthopedics": ["Chinese Orthopedics", "中醫骨科"],
    "psychological_consultation": ["Psychological Consultation", "心理諮詢", "心理咨詢"],
    "nutrition": ["Nutrition", "營養食療"]
}

def normalize_service_names():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    total_updated = 0

    for standardized_key, variants in SERVICE_MAPPINGS.items():
        for variant in variants:
            cursor.execute(
                """
                UPDATE appointments
                SET service = ?
                WHERE service = ?
                """,
                (standardized_key, variant)
            )
            count = cursor.rowcount
            if count > 0:
                print(f"Updated {count} records: '{variant}' -> '{standardized_key}'")
                total_updated += count

    conn.commit()
    conn.close()
    print(f"\nService normalization complete! Total records updated: {total_updated}")

if __name__ == "__main__":
    normalize_service_names()
