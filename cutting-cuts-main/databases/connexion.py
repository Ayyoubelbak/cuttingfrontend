import pyodbc
import pandas as pd

def connect_db_woodStore(server, database,user,password):
    connection_string = f"""
    DRIVER={{SQL Server}};
    SERVER={server};
    DATABASE={database};
    UID={user};
    PWD={password}
    """

    try:
        conn = pyodbc.connect(connection_string)
        print("Connexion réussie à SQL Server avec Windows Authentication")
        return conn
    except pyodbc.Error as e:
        print(f"Erreur de connexion : {e}")
        return None


if __name__ == "__main__":
    server = '192.2.50.1\sqlexpress'
    database = 'lagerdb'

    connection = connect_db_woodStore(server, database)
