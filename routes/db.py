import mysql.connector
# -----------------------------
# DATABASE
# -----------------------------
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="mca"
    )
