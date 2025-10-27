import mysql.connector

def ket_noi_csdl():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="tuyendung"
    )
