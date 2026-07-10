import sqlite3


conn = sqlite3.connect(
"clinic.db"
)


cursor = conn.cursor()


try:

    cursor.execute(
    """
    ALTER TABLE treatment_records
    ADD COLUMN service TEXT
    """
    )

except:

    pass



conn.commit()

conn.close()


print("updated")