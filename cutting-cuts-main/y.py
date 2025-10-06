
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import  CORSMiddleware
import json
from fastapi.responses import  JSONResponse
from pydantic import  BaseModel
app=FastAPI()
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Autoriser ton front-end
    allow_credentials=True,
    allow_methods=["*"],         # GET, POST, PUT, DELETE…
    allow_headers=["*"],
)
@app.get("/")
def root():
    return {"message":"API de découpe pannaux opérationnelle"}
@app.get("/optimize")
def optimize():

    from core.Piece import Piece
    from core.Pannel import Panel
    from Algorithms.MultiPannaux import MultiPanelCuttingOptimizer
    from databases.GestionWoodStore import WoodStoreManager
    from fastapi import HTTPException
    from Algorithms.LogsErreur import check_piece_fit



    FICHIER_EXCEL = ("N:/ProgramData/Cutrite/Import/240417_24_CL_Part_Prod_250918_16-25-53.xls")
    #FICHIER_EXCEL = ("N:/ProgramData/Cutrite/Import/TEST_AEB_CUTRITE_2709.xls")
    COLONNE_MATERIEL = "MATID"
    try:
        manager = WoodStoreManager(use_chute=True)
        optimizer = MultiPanelCuttingOptimizer(
            rotation_allowed=False,
            cut_marge=4.5,
            trimLeft=20,
            trimRight=20,
            trimTop=10,
            trimBottom=20,
            min_width=50,
            min_height=50
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

                pieces_valide, pices_rejetes = check_piece_fit(
                    pieces_liste,
                    optimizer.panel_templates,
                    rotation_allowed=optimizer.rotation_allowed,
                    cut_marge=optimizer.cut_marge,
                    trimTop=optimizer.trimTop,
                    trimLeft=optimizer.trimLeft,
                    trimRight=optimizer.trimRight,
                    trimBottom=optimizer.trimBottom

                )

                optimizer.load_pieces(pieces_liste)
                optimizer.optimize_multi_panel_greedy()
                all_results.extend(optimizer.export_result())

                optimizer.reset()
            #     print( {
            #     "results"       :all_results ,
            #     "pieces_valides":pieces_valide,
            #     "pices_rejetes" :pices_rejetes
            # })
            return {
                "results"       :all_results ,
                "pieces_valides":pieces_valide,
                "pices_rejetes" :pices_rejetes
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors de l’optimisation : {str(e)}")

        finally:
            manager.close_connection()
    except Exception as e :
        print(e)

































# pieces_list =[Piece(33,   1389, "Tablette A", "MDF", 4),
# Piece(33,   814, "Tablette A", "MDF", 4),
# Piece(33,   235, "Tablette A", "MDF", 2),
# Piece(94,   780, "Tablette A", "MDF", 4),
# Piece(94,   2574, "Tablette A", "MDF", 4),
# Piece(94,   235, "Tablette A", "MDF", 2),
#    ]
# print(pieces_list)
# #afficher_dimensions_materiels()
# # Créer l'optimiseur multi-panneaux
# # optimizer = MultiPanelCuttingOptimizer(rotation_allowed=False,cut_marge=4.5,trimLeft=12,trimRight=12,trimTop=12,trimBottom=12)
#
# # Ajouter différents types de panneaux disponibles
# # optimizer.add_panel_template(Panel(1300, 3050, "Standard", "MDF"), max_quantity=55)
#
# # optimizer.add_panel_template(Panel(1220, 3050, "Standard", "MDF"), max_quantity=55)
#
#
# # Charger les pièces
# optimizer.load_pieces(pieces_list)
#
# # Optimiser avec algorithme glouton
# result = optimizer.optimize_multi_panel_greedy()
# optimizer.print_multi_panel_summary()
# # 1. Visualiser un panneau spécifique
# optimizer.visualize_panel(0) # Premier panneau
# optimizer.visualize_panel(1) # Premier panneau
