import sqlite3


conn = sqlite3.connect("clinic.db")

cursor = conn.cursor()



cursor.execute(
"""
UPDATE appointments
SET service='pain_rehabilitation'
WHERE service='疼痛康復'
"""
)



cursor.execute(
"""
UPDATE appointments
SET service='spinal_correction'
WHERE service='Spinal Correction'
"""
)



cursor.execute(
"""
UPDATE appointments
SET service='spinal_correction'
WHERE service='脊柱矯正'
"""
)



conn.commit()

conn.close()


print("Service names updated")