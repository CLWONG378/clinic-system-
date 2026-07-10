import sqlite3


conn = sqlite3.connect(
    "clinic.db"
)


cursor = conn.cursor()



columns = [

"birthday",

"gender",

"address",

"notes"

]



for column in columns:

    try:

        cursor.execute(
            f"""
            ALTER TABLE patients
            ADD COLUMN {column} TEXT
            """
        )

    except:

        pass



conn.commit()

conn.close()


print("updated")