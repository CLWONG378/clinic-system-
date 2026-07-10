import sqlite3


conn = sqlite3.connect(
"clinic.db"
)


cursor = conn.cursor()


cursor.execute(

"""

INSERT INTO packages

(
name,
service,
total_sessions,
price
)

VALUES

(
?,
?,
?,
?
)

""",

(
"脊柱矯正10次套餐",
"spinal_correction",
10,
5000
)

)


conn.commit()

conn.close()


print("package added")