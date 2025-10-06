# from fastapi import FastAPI, HTTPException, File, UploadFile, Form
# from fastapi.middleware.cors import CORSMiddleware
# import json
# import shutil
# import os
# from pathlib import Path
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel
# from typing import Optional
#
# app = FastAPI()
#
# origins = [
#     "http://localhost:3000",
#     "http://127.0.0.1:3000"
# ]
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
# # Dossier pour stocker temporairement les fichiers uploadés
# UPLOAD_DIR = Path("temp_uploads")
# UPLOAD_DIR.mkdir(exist_ok=True)
#
#
# # Modèle Pydantic pour recevoir la configuration (optionnel maintenant)
# class OptimizationConfig(BaseModel):
#     # Nouveaux paramètres du frontend
#     saw_kerf: float = 3.2
#     trim_left: int = 20
#     trim_right: int = 20
#     trim_top: int = 10
#     trim_bottom: int = 20
#     min_width: int = 50
#     min_height: int = 50
#     min_area : float =0.4
#     allow_rotation: bool = False
#     use_waste: bool = True
#
#     # Paramètres avancés (optionnels)
#     optimization_method: Optional[str] = "best_fit_decreasing"
#     max_iterations: Optional[int] = 1000
#     timeout_seconds: Optional[int] = 300
#     minimize_waste: Optional[bool] = True
#     maximize_utilization: Optional[bool] = True
#
#
# @app.get("/")
# def root():
#     return {"message": "API de découpe panneaux opérationnelle"}
#
#
# @app.get("/optimize")
# def optimize_default():
#     """Endpoint GET avec fichier et paramètres par défaut"""
#     FICHIER_EXCEL = ("N:/ProgramData/Cutrite/Import/240417_24_CL_Part_Prod_250918_16-25-53.xls")
#     config = OptimizationConfig()
#     return run_optimization_from_file(FICHIER_EXCEL, config)
#
#
# @app.post("/optimize")
# async def optimize_with_uploaded_file(
#         file: UploadFile = File(...),
#         saw_kerf: float = Form(3.2),
#         trim_left: int = Form(20),
#         trim_right: int = Form(20),
#         trim_top: int = Form(10),
#         trim_bottom: int = Form(20),
#         min_width: int = Form(50),
#         min_height: int = Form(50),
#         min_area : float =Form(0.4),
#         allow_rotation: bool = Form(False),
#         use_waste: bool = Form(True),
#         optimization_method: str = Form("best_fit_decreasing"),
#         max_iterations: int = Form(1000),
#         timeout_seconds: int = Form(300)
# ):
#     """Endpoint POST avec fichier uploadé et configuration personnalisée"""
#
#     # Vérifier le type de fichier
#     if not (file.filename.endswith('.xls') or file.filename.endswith('.xlsx')):
#         raise HTTPException(status_code=400, detail="Le fichier doit être au format .xls ou .xlsx")
#
#     # Sauvegarder le fichier temporairement
#     temp_file_path = UPLOAD_DIR / file.filename
#     try:
#         with open(temp_file_path, "wb") as buffer:
#             shutil.copyfileobj(file.file, buffer)
#
#         print(f"Fichier reçu et sauvegardé : {temp_file_path}")
#
#         # Créer l'objet de configuration
#         config = OptimizationConfig(
#             saw_kerf=saw_kerf,
#             trim_left=trim_left,
#             trim_right=trim_right,
#             trim_top=trim_top,
#             trim_bottom=trim_bottom,
#             min_width=min_width,
#             min_height=min_height,
#             min_area=min_area,
#             allow_rotation=allow_rotation,
#             use_waste=use_waste,
#             optimization_method=optimization_method,
#             max_iterations=max_iterations,
#             timeout_seconds=timeout_seconds
#         )
#
#         # Lancer l'optimisation avec le fichier uploadé
#         result = run_optimization_from_file(str(temp_file_path), config)
#
#         return result
#
#     except Exception as e:
#         print(f"Erreur lors du traitement : {e}")
#         raise HTTPException(status_code=500, detail=f"Erreur lors du traitement : {str(e)}")
#
#     finally:
#         # Nettoyer le fichier temporaire
#         if temp_file_path.exists():
#             try:
#                 os.remove(temp_file_path)
#                 print(f"Fichier temporaire supprimé : {temp_file_path}")
#             except Exception as e:
#                 print(f"Erreur lors de la suppression du fichier : {e}")
#
#
# def run_optimization_from_file(excel_file_path: str, config: OptimizationConfig):
#     """Fonction principale d'optimisation avec fichier et configuration"""
#
#     from core.Piece import Piece
#     from core.Pannel import Panel
#     from Algorithms.MultiPannaux import MultiPanelCuttingOptimizer
#     from databases.GestionWoodStore import WoodStoreManager
#     from Algorithms.LogsErreur import check_piece_fit
#
#     FICHIER_EXCEL = excel_file_path
#     COLONNE_MATERIEL = "MATID"
#
#     try:
#         # Utiliser les paramètres de configuration reçus
#         print(f"Configuration reçue:")
#         print(f"- Fichier Excel: {FICHIER_EXCEL}")
#         print(f"- Saw kerf (cut_marge): {config.saw_kerf}mm")
#         print(f"- Trims: L:{config.trim_left}, R:{config.trim_right}, T:{config.trim_top}, B:{config.trim_bottom}")
#         print(f"- Min dimensions: {config.min_width}x{config.min_height}mm")
#         print(f"- Rotation autorisée: {config.allow_rotation}")
#         print(f"- Utiliser chutes: {config.use_waste}")
#
#         manager = WoodStoreManager(use_chute=config.use_waste)
#
#         # Créer l'optimiseur avec les paramètres reçus
#         optimizer = MultiPanelCuttingOptimizer(
#             rotation_allowed=config.allow_rotation,
#             cut_marge=config.saw_kerf,
#             trimLeft=config.trim_left,
#             trimRight=config.trim_right,
#             trimTop=config.trim_top,
#             trimBottom=config.trim_bottom,
#             min_width=config.min_width,
#             min_height=config.min_height,
#             min_area=config.min_area
#         )
#
#         all_results = []
#
#         try:
#             resultats = manager.afficher_dimensions_materiels(FICHIER_EXCEL, COLONNE_MATERIEL)
#
#             for cle, panneaux in resultats.items():
#                 # Ajouter les panneaux
#                 for height, width, code, mat_type in panneaux:
#                     optimizer.add_panel_template(
#                         Panel(float(width), float(height), code, mat_type),
#                         max_quantity=9999
#                     )
#
#                 # Charger les pièces
#                 pieces_data = manager.afficher_liste_piéce_découper(FICHIER_EXCEL, cle)
#                 pieces_liste = [Piece(p[0], p[1], p[2], p[3], int(p[4]), p[5]) for p in pieces_data]
#
#                 # Vérifier les pièces avec les nouveaux paramètres
#                 pieces_valide, pices_rejetes = check_piece_fit(
#                     pieces_liste,
#                     optimizer.panel_templates,
#                     rotation_allowed=config.allow_rotation,
#                     cut_marge=config.saw_kerf,
#                     trimTop=config.trim_top,
#                     trimLeft=config.trim_left,
#                     trimRight=config.trim_right,
#                     trimBottom=config.trim_bottom
#                 )
#
#                 optimizer.load_pieces(pieces_liste)
#                 optimizer.optimize_multi_panel_greedy()
#                 all_results.extend(optimizer.export_result())
#
#                 optimizer.reset()
#
#             return {
#                 "results": all_results,
#                 "pieces_valides": pieces_valide,
#                 "pices_rejetes": pices_rejetes,
#                 "configuration_used": {
#                     "fichier": FICHIER_EXCEL,
#                     "saw_kerf": config.saw_kerf,
#                     "trim_left": config.trim_left,
#                     "trim_right": config.trim_right,
#                     "trim_top": config.trim_top,
#                     "trim_bottom": config.trim_bottom,
#                     "min_width": config.min_width,
#                     "min_height": config.min_height,
#                     "min_area":config.min_area,
#                     "allow_rotation": config.allow_rotation,
#                     "use_waste": config.use_waste
#                 }
#             }
#
#         except Exception as e:
#             raise HTTPException(status_code=500, detail=f"Erreur lors de l'optimisation : {str(e)}")
#
#         finally:
#             manager.close_connection()
#
#     except Exception as e:
#         print(f"Erreur générale: {e}")
#         raise HTTPException(status_code=500, detail=f"Erreur générale : {str(e)}")
#
#
# # Endpoint pour tester la réception des paramètres
# @app.post("/test-upload")
# async def test_upload(file: UploadFile = File(...)):
#     """Endpoint pour tester l'upload de fichier"""
#     return {
#         "message": "Fichier reçu avec succès",
#         "filename": file.filename,
#         "content_type": file.content_type,
#         "size": file.size if hasattr(file, 'size') else "unknown"
#     }
#
#
# # Endpoint pour obtenir la configuration par défaut
# @app.get("/default-config")
# def get_default_config():
#     """Retourne la configuration par défaut"""
#     config = OptimizationConfig()
#     return {
#         "default_config": {
#             "saw_kerf": config.saw_kerf,
#             "trim_left": config.trim_left,
#             "trim_right": config.trim_right,
#             "trim_top": config.trim_top,
#             "trim_bottom": config.trim_bottom,
#             "min_width": config.min_width,
#             "min_height": config.min_height,
#             "min_area":config.min_area,
#             "allow_rotation": config.allow_rotation,
#             "use_waste": config.use_waste
#         }
#     }
#     """Fonction principale d'optimisation avec configuration"""
#
#     from core.Piece import Piece
#     from core.Pannel import Panel
#     from Algorithms.MultiPannaux import MultiPanelCuttingOptimizer
#     from databases.GestionWoodStore import WoodStoreManager
#     from Algorithms.LogsErreur import check_piece_fit
#
#     FICHIER_EXCEL = ("N:/ProgramData/Cutrite/Import/240417_24_CL_Part_Prod_250918_16-25-53.xls")
#     COLONNE_MATERIEL = "MATID"
#
#     try:
#         # Utiliser les paramètres de configuration reçus
#         print(f"Configuration reçue:")
#         print(f"- Saw kerf (cut_marge): {config.saw_kerf}mm")
#         print(f"- Trims: L:{config.trim_left}, R:{config.trim_right}, T:{config.trim_top}, B:{config.trim_bottom}")
#         print(f"- Min dimensions: {config.min_width}x{config.min_height}mm")
#         print(f"- Rotation autorisée: {config.allow_rotation}")
#         print(f"- Utiliser chutes: {config.use_waste}")
#
#         manager = WoodStoreManager(use_chute=config.use_waste)
#
#         # Créer l'optimiseur avec les paramètres reçus
#         optimizer = MultiPanelCuttingOptimizer(
#             rotation_allowed=config.allow_rotation,
#             cut_marge=config.saw_kerf,  # saw_kerf correspond à cut_marge
#             trimLeft=config.trim_left,
#             trimRight=config.trim_right,
#             trimTop=config.trim_top,
#             trimBottom=config.trim_bottom,
#             min_width=config.min_width,
#             min_height=config.min_height,
#             min_area=config.min_area
#         )
#
#         all_results = []
#
#         try:
#             resultats = manager.afficher_dimensions_materiels(FICHIER_EXCEL, COLONNE_MATERIEL)
#
#             for cle, panneaux in resultats.items():
#                 # Ajouter les panneaux
#                 for height, width, code, mat_type in panneaux:
#                     optimizer.add_panel_template(
#                         Panel(float(width), float(height), code, mat_type),
#                         max_quantity=9999
#                     )
#
#                 # Charger les pièces
#                 pieces_data = manager.afficher_liste_piéce_découper(FICHIER_EXCEL, cle)
#                 pieces_liste = [Piece(p[0], p[1], p[2], p[3], int(p[4]), p[5]) for p in pieces_data]
#
#                 # Vérifier les pièces avec les nouveaux paramètres
#                 pieces_valide, pices_rejetes = check_piece_fit(
#                     pieces_liste,
#                     optimizer.panel_templates,
#                     rotation_allowed=config.allow_rotation,  # Utiliser config
#                     cut_marge=config.saw_kerf,  # Utiliser config
#                     trimTop=config.trim_top,  # Utiliser config
#                     trimLeft=config.trim_left,  # Utiliser config
#                     trimRight=config.trim_right,  # Utiliser config
#                     trimBottom=config.trim_bottom  # Utiliser config
#                 )
#
#                 optimizer.load_pieces(pieces_liste)
#                 optimizer.optimize_multi_panel_greedy()
#                 all_results.extend(optimizer.export_result())
#
#                 optimizer.reset()
#
#             return {
#                 "results": all_results,
#                 "pieces_valides": pieces_valide,
#                 "pices_rejetes": pices_rejetes,
#                 "configuration_used": {  # Ajouter la config utilisée pour debug
#                     "saw_kerf": config.saw_kerf,
#                     "trim_left": config.trim_left,
#                     "trim_right": config.trim_right,
#                     "trim_top": config.trim_top,
#                     "trim_bottom": config.trim_bottom,
#                     "min_width": config.min_width,
#                     "min_height": config.min_height,
#                     "min_area": config.min_area,
#                     "allow_rotation": config.allow_rotation,
#                     "use_waste": config.use_waste
#                 }
#             }
#
#         except Exception as e:
#             raise HTTPException(status_code=500, detail=f"Erreur lors de l'optimisation : {str(e)}")
#
#         finally:
#             manager.close_connection()
#
#     except Exception as e:
#         print(f"Erreur générale: {e}")
#         raise HTTPException(status_code=500, detail=f"Erreur générale : {str(e)}")
#
#
# # Endpoint pour tester la réception des paramètres
# @app.post("/test-config")
# def test_config(config: OptimizationConfig):
#     """Endpoint pour tester la réception des paramètres sans faire l'optimisation"""
#     return {
#         "message": "Configuration reçue avec succès",
#         "config_received": {
#             "saw_kerf": config.saw_kerf,
#             "trim_left": config.trim_left,
#             "trim_right": config.trim_right,
#             "trim_top": config.trim_top,
#             "trim_bottom": config.trim_bottom,
#             "min_width": config.min_width,
#             "min_height": config.min_height,
#             "min_area" : config.min_area,
#             "allow_rotation": config.allow_rotation,
#             "use_waste": config.use_waste,
#             "optimization_method": config.optimization_method
#         }
#     }
#
#
# # Endpoint pour obtenir la configuration par défaut
# @app.get("/default-config")
# def get_default_config():
#     """Retourne la configuration par défaut"""
#     config = OptimizationConfig()
#     return {
#         "default_config": {
#             "saw_kerf": config.saw_kerf,
#             "trim_left": config.trim_left,
#             "trim_right": config.trim_right,
#             "trim_top": config.trim_top,
#             "trim_bottom": config.trim_bottom,
#             "min_width": config.min_width,
#             "min_height": config.min_height,
#             "min_area": config.min_area,
#             "allow_rotation": config.allow_rotation,
#             "use_waste": config.use_waste
#         }
#     }

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import json
import shutil
import os
from pathlib import Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dossier pour stocker temporairement les fichiers uploadés
UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# Modèle Pydantic pour recevoir la configuration (optionnel maintenant)
class OptimizationConfig(BaseModel):
    # Nouveaux paramètres du frontend
    saw_kerf: float = 3.2
    trim_left: int = 20
    trim_right: int = 20
    trim_top: int = 10
    trim_bottom: int = 20
    min_width: int = 50
    min_height: int = 50
    min_area: float = 0.4
    allow_rotation: bool = False
    use_waste: bool = True

    # Paramètres avancés (optionnels)
    optimization_method: Optional[str] = "best_fit_decreasing"
    max_iterations: Optional[int] = 1000
    timeout_seconds: Optional[int] = 300
    minimize_waste: Optional[bool] = True
    maximize_utilization: Optional[bool] = True


@app.get("/")
def root():
    return {"message": "API de découpe panneaux opérationnelle"}


@app.get("/optimize")
def optimize_default():
    """Endpoint GET avec fichier et paramètres par défaut"""
    FICHIER_EXCEL = ("N:/ProgramData/Cutrite/Import/240417_24_CL_Part_Prod_250918_16-25-53.xls")
    config = OptimizationConfig()
    return run_optimization_from_file(FICHIER_EXCEL, config)


@app.post("/optimize")
async def optimize_with_uploaded_file(
        file: UploadFile = File(...),
        saw_kerf: float = Form(3.2),
        trim_left: int = Form(20),
        trim_right: int = Form(20),
        trim_top: int = Form(10),
        trim_bottom: int = Form(20),
        min_width: int = Form(50),
        min_height: int = Form(50),
        min_area: float = Form(0.4),
        allow_rotation: bool = Form(False),
        use_waste: bool = Form(True),
        optimization_method: str = Form("best_fit_decreasing"),
        max_iterations: int = Form(1000),
        timeout_seconds: int = Form(300)
):
    """Endpoint POST avec fichier uploadé et configuration personnalisée"""

    # Vérifier le type de fichier
    if not (file.filename.endswith('.xls') or file.filename.endswith('.xlsx')):
        raise HTTPException(status_code=400, detail="Le fichier doit être au format .xls ou .xlsx")

    # Sauvegarder le fichier temporairement
    temp_file_path = UPLOAD_DIR / file.filename
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"Fichier reçu et sauvegardé : {temp_file_path}")

        # Créer l'objet de configuration
        config = OptimizationConfig(
            saw_kerf=saw_kerf,
            trim_left=trim_left,
            trim_right=trim_right,
            trim_top=trim_top,
            trim_bottom=trim_bottom,
            min_width=min_width,
            min_height=min_height,
            min_area=min_area,
            allow_rotation=allow_rotation,
            use_waste=use_waste,
            optimization_method=optimization_method,
            max_iterations=max_iterations,
            timeout_seconds=timeout_seconds
        )

        # Lancer l'optimisation avec le fichier uploadé
        result = run_optimization_from_file(str(temp_file_path), config)

        return result

    except Exception as e:
        print(f"Erreur lors du traitement : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement : {str(e)}")

    finally:
        # Nettoyer le fichier temporaire
        if temp_file_path.exists():
            try:
                os.remove(temp_file_path)
                print(f"Fichier temporaire supprimé : {temp_file_path}")
            except Exception as e:
                print(f"Erreur lors de la suppression du fichier : {e}")


def run_optimization_from_file(excel_file_path: str, config: OptimizationConfig):
    """Fonction principale d'optimisation avec fichier et configuration"""

    from core.Piece import Piece
    from core.Pannel import Panel
    from Algorithms.MultiPannaux import MultiPanelCuttingOptimizer
    from databases.GestionWoodStore import WoodStoreManager
    from Algorithms.LogsErreur import check_piece_fit

    FICHIER_EXCEL = excel_file_path
    COLONNE_MATERIEL = "MATID"

    try:
        # Utiliser les paramètres de configuration reçus
        print(f"Configuration reçue:")
        print(f"- Fichier Excel: {FICHIER_EXCEL}")
        print(f"- Saw kerf (cut_marge): {config.saw_kerf}mm")
        print(f"- Trims: L:{config.trim_left}, R:{config.trim_right}, T:{config.trim_top}, B:{config.trim_bottom}")
        print(f"- Min dimensions: {config.min_width}x{config.min_height}mm")
        print(f"- Rotation autorisée: {config.allow_rotation}")
        print(f"- Utiliser chutes: {config.use_waste}")

        manager = WoodStoreManager(use_chute=config.use_waste)

        # Créer l'optimiseur avec les paramètres reçus
        optimizer = MultiPanelCuttingOptimizer(
            rotation_allowed=config.allow_rotation,
            cut_marge=config.saw_kerf,
            trimLeft=config.trim_left,
            trimRight=config.trim_right,
            trimTop=config.trim_top,
            trimBottom=config.trim_bottom,
            min_width=config.min_width,
            min_height=config.min_height,
            min_area=config.min_area
        )

        all_results = []

        try:
            resultats = manager.afficher_dimensions_materiels(FICHIER_EXCEL, COLONNE_MATERIEL)

            for cle, panneaux in resultats.items():
                # Ajouter les panneaux
                for height, width, code, mat_type in panneaux:
                    optimizer.add_panel_template(
                        Panel(float(width), float(height), code, mat_type),
                        max_quantity=9999
                    )

                # Charger les pièces
                pieces_data = manager.afficher_liste_piéce_découper(FICHIER_EXCEL, cle)
                pieces_liste = [Piece(p[0], p[1], p[2], p[3], int(p[4]), p[5]) for p in pieces_data]

                # Vérifier les pièces avec les nouveaux paramètres
                pieces_valide, pices_rejetes = check_piece_fit(
                    pieces_liste,
                    optimizer.panel_templates,
                    rotation_allowed=config.allow_rotation,
                    cut_marge=config.saw_kerf,
                    trimTop=config.trim_top,
                    trimLeft=config.trim_left,
                    trimRight=config.trim_right,
                    trimBottom=config.trim_bottom
                )

                optimizer.load_pieces(pieces_liste)
                optimizer.optimize_multi_panel_greedy()
                all_results.extend(optimizer.export_result())

                optimizer.reset()

            return {
                "results": all_results,
                "pieces_valides": pieces_valide,
                "pices_rejetes": pices_rejetes,
                "configuration_used": {
                    "fichier": FICHIER_EXCEL,
                    "saw_kerf": config.saw_kerf,
                    "trim_left": config.trim_left,
                    "trim_right": config.trim_right,
                    "trim_top": config.trim_top,
                    "trim_bottom": config.trim_bottom,
                    "min_width": config.min_width,
                    "min_height": config.min_height,
                    "min_area": config.min_area,
                    "allow_rotation": config.allow_rotation,
                    "use_waste": config.use_waste
                }
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors de l'optimisation : {str(e)}")

        finally:
            manager.close_connection()

    except Exception as e:
        print(f"Erreur générale: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur générale : {str(e)}")


# Endpoint pour tester la réception des paramètres
@app.post("/test-upload")
async def test_upload(file: UploadFile = File(...)):
    """Endpoint pour tester l'upload de fichier"""
    return {
        "message": "Fichier reçu avec succès",
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file.size if hasattr(file, 'size') else "unknown"
    }


# Endpoint pour tester la réception des paramètres
@app.post("/test-config")
def test_config(config: OptimizationConfig):
    """Endpoint pour tester la réception des paramètres sans faire l'optimisation"""
    return {
        "message": "Configuration reçue avec succès",
        "config_received": {
            "saw_kerf": config.saw_kerf,
            "trim_left": config.trim_left,
            "trim_right": config.trim_right,
            "trim_top": config.trim_top,
            "trim_bottom": config.trim_bottom,
            "min_width": config.min_width,
            "min_height": config.min_height,
            "min_area": config.min_area,
            "allow_rotation": config.allow_rotation,
            "use_waste": config.use_waste,
            "optimization_method": config.optimization_method
        }
    }


# Endpoint pour obtenir la configuration par défaut
@app.get("/default-config")
def get_default_config():
    """Retourne la configuration par défaut"""
    config = OptimizationConfig()
    return {
        "default_config": {
            "saw_kerf": config.saw_kerf,
            "trim_left": config.trim_left,
            "trim_right": config.trim_right,
            "trim_top": config.trim_top,
            "trim_bottom": config.trim_bottom,
            "min_width": config.min_width,
            "min_height": config.min_height,
            "min_area": config.min_area,
            "allow_rotation": config.allow_rotation,
            "use_waste": config.use_waste
        }
    }