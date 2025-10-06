import pandas as pd
import logging
from typing import List, Dict, Tuple, Optional, Union

from fastapi import HTTPException
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.exc import SQLAlchemyError
from collections import  defaultdict
# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WoodStoreManager:
    def __init__(self, server: str = '192.2.50.1\sqlexpress', database: str = 'lagerdb',password='Homag',user='sa',use_chute: bool=True):

        self.server = server
        self.database = database
        self.password=password
        self.user=user
        self.connexion = self._connect_db_woodstore_sqlalchemy()
        self.use_chute=use_chute

    def _connect_db_woodstore_sqlalchemy(self) -> Optional[Engine]:
        try:
            # connection_string = (f"mssql+pyodbc://{self.server}/{self.database}"
            #                      f"?driver=ODBC+Driver+17+for+SQL+Server")
            connection_string = f"mssql+pyodbc://{self.user}:{self.password}@{self.server}/{self.database}?driver=ODBC+Driver+17+for+SQL+Server"

            engine = create_engine(connection_string)
            # Test de la connexion
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return engine
        except Exception as e:
            return None

    def afficher_materiels_categories(self, fichier_excel: str, colonne_name: str) -> Optional[List[str]]:
        try:
            df = pd.read_excel(fichier_excel)

        except Exception as e :
            print("erreur :", e)



        materiels_uniques = df[colonne_name].dropna().unique().tolist()

        return materiels_uniques

        # try:
        #     df = pd.read_excel(fichier_excel)
        #     if colonne_name not in df.columns:
        #         return None
        #     materiels_uniques = df[colonne_name].dropna().unique().tolist()
        #     return materiels_uniques
        # except FileNotFoundError:
        #     return None
        # except Exception as e:
        #     print("Erreur:", e)
        #     raise HTTPException(status_code=500, detail=str(e))

    def chercher_materiels_bd_woodstore(self, mat_id: str) -> List[Tuple]:

        if not self.connexion:
            return []

        try:
            if self.use_chute == False :
                query = text("""
                                SELECT Laenge, Breite, Identnummer, Materialcode
                                FROM Ident
                                WHERE Materialcode LIKE :matid and Identnummer not like 'X%'
                                ORDER BY Materialcode, Laenge DESC, Breite DESC
                            """)
            else :
                query = text("""
                                SELECT Laenge, Breite, Identnummer, Materialcode
                                FROM Ident
                                WHERE Materialcode LIKE :matid
                                ORDER BY Materialcode, Laenge DESC, Breite DESC
                            """)



            df = pd.read_sql(query, self.connexion, params={"matid": f"{mat_id}%"})

            if df.empty:
                return []

            # Conversion en liste de tuples
            resultats = [tuple(row) for row in df.to_numpy()]

            return resultats

        except SQLAlchemyError as e:
            return []
        except Exception as e:
            return []

    def grouper_par_code_materiel(self, resultats: List[Tuple]) -> Dict[str, List[Tuple]]:

        if not resultats:
            return {}

        groupe = {}
        for tuple_materiel in resultats:
            longueur, largeur, identifiant, code = tuple_materiel
            code_upper=code.upper()

            if code_upper not in groupe:
                groupe[code_upper] = []

            groupe[code_upper].append(tuple_materiel)




        return groupe

    def afficher_dimensions_materiels(self, fichier_excel: str, colonne_mat: str) -> Dict[str, List[Tuple]]:
        # Extraction des codes matériaux du fichier Excel
        materiels = self.afficher_materiels_categories(fichier_excel, colonne_mat)
        if not materiels:
            return {}

        # Recherche dans la base de données pour chaque matériau
        resultats_complets = []
        for mat in materiels:
            resultats_mat = self.chercher_materiels_bd_woodstore(mat)

            resultats_complets.extend(resultats_mat)


        # Groupement par code matériau
        resultats_groupes = self.grouper_par_code_materiel(resultats_complets)

        return resultats_groupes


    def afficher_liste_piéce_découper(self,fichier_excel:str,Materiel:str)->List[Tuple]:
        try :
            df=pd.read_excel(fichier_excel)

            df=df[['CWIDTH','CLENG','MATID','MATNAME','CNT','NAME1']]

            if Materiel:
                df = df[df['MATID'].str.upper() == Materiel.upper()]

            #Créer une dictionnaire
            result = [
                (row['CWIDTH'], row['CLENG'],row['MATID'] ,row['MATNAME'], row['CNT'],row['NAME1'])
                for _, row in df.iterrows()
            ]

            return result
        except Exception as e :
           print("errur",e)


    def close_connection(self) -> None:
        """Ferme proprement la connexion à la base de données."""
        if self.connexion:
            self.connexion.dispose()


