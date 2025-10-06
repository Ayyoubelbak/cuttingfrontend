import pandas as pd
from connexion import  connect_db_woodStore
from sqlalchemy import create_engine,text

def connect_db_woodStore_sqlalchemy(server, database,password,user):
    connection_string = f"mssql+pyodbc://{user}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
    return create_engine(connection_string)
server = '192.2.50.1\sqlexpress'
database = 'lagerdb'
user="sa"
password="Homag"
connexion=connect_db_woodStore_sqlalchemy(server,database,password,user)
def afficher_materiels_categories(fichier_excel,coloneName):
    try:
        df=pd.read_excel(fichier_excel)
        if coloneName not in df.columns:
            print(f"la colone {coloneName} n'existe pas dans le fichier")
            return


        return df[coloneName].dropna().unique()
        # print("liste des materiels distincts")
        # for mat in materiels_distinct:
        #     print(f'-{mat}')
    except Exception as e :
        print(f"Erreur lors de la lecture du fichier : {e}")
def chercher_materiels_bd_woodstore(MATID,connexion):
    query = text("""
              SELECT Identnummer,Laenge,Breite ,Materialcode
              FROM Ident
              WHERE Materialcode LIKE :matid
              """)
    df = pd.read_sql(query, connexion, params={"matid": f"{MATID}"})
    df = df[["Laenge", "Breite", "Identnummer", "Materialcode"]]
    return  [tuple(row) for row in df.to_numpy()]


def afficher_par_code_materiel(resultats):
     if not resultats:
         return
     groupe={}
     for tuple_maateriel in resultats:
         width,height,identifiant,code=tuple_maateriel
         if code not in groupe:
             groupe[code]=[]
         groupe[code].append(tuple_maateriel)
     return  groupe
def afficher_dimensions_materiels(fichier_excel,colonneMat):
    materiels=afficher_materiels_categories(fichier_excel,colonneMat)
    # for mat in materiels:
    #     df=chercher_materiels_bd_woodstore(mat, connexion)
    #     print(df)
    if materiels is None:
        return []

    resultats_complets=[]
    for mat in materiels:
        df=chercher_materiels_bd_woodstore(mat, connexion)
        resultats_complets.extend(df)
    resultats_complets2=afficher_par_code_materiel(resultats_complets)
    return resultats_complets2
# liste=afficher_dimensions_materiels(fichier_excel,'MATID')
# print(liste)