import copy
from typing import List, Tuple, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from rectpack import newPacker

from core.Piece import Piece
from core.Pannel import Panel
import rectpack
import packaging
class CuttingOptimizer:

    def __init__(self, rotation_allowed: bool = False):

        self.rotation_allowed = rotation_allowed
        self.pieces: List[Piece] = []
        self.panels: List[Panel] = []
        self.used_panels: List[Panel] = []

    def add_piece(self, piece: Piece):
        """Ajoute une pièce à optimiser"""
        # Si quantité > 1, créer plusieurs copies
        for i in range(piece.quantity):
            if i == 0:
                self.pieces.append(piece)
            else:
                copy_piece = piece.copy()
                copy_piece.name = f"{piece.name}_copy_{i}"
                self.pieces.append(copy_piece)

    def add_pieces(self, pieces: List[Piece]):
        """Ajoute plusieurs pièces"""
        for piece in pieces:
            self.add_piece(piece)

    def set_panel_template(self, panel: Panel):
        self.panel_template = panel

    def optimize(self, algorithm=rectpack.SkylineMwf) -> List[Panel]:

        if not hasattr(self, 'panel_template'):
            raise ValueError("Aucun modèle de panneau défini. Utilisez set_panel_template()")

        # Création du packer
        packer = newPacker(
            rotation=self.rotation_allowed, pack_algo=algorithm
        )

        # Ajout d'un grand nombre de panneaux identiques (le packer n'utilisera que ceux nécessaires)
        max_panels = len(self.pieces)  # Marge de sécurité
        for i in range(max_panels):
            packer.add_bin(self.panel_template.width, self.panel_template.height)

        # Ajout des pièces
        for i, piece in enumerate(self.pieces):
            packer.add_rect(piece.width, piece.height, i)

        # Lancement de l'optimisation
        packer.pack()

        # Traitement des résultats
        self.used_panels = []

        for bin_index, abin in enumerate(packer):
            if len(abin) == 0:  # Panneau vide, on s'arrête
                break

            # Création d'un nouveau panneau
            panel = Panel(
                self.panel_template.width,
                self.panel_template.height,
                f"{self.panel_template.name}_used_{bin_index + 1}",
                self.panel_template.material,
            )

            # Ajout des pièces au panneau
            for rect in abin:
                piece = self.pieces[rect.rid]

                # Vérifier si la pièce a été tournée
                if (rect.width != piece.width or rect.height != piece.height):
                    piece.rotate()

                panel.add_piece(piece, rect.x, rect.y)

            self.used_panels.append(panel)

        return self.used_panels



    def get_global_efficiency(self) -> float:
        """Calcule l'efficacité globale"""
        if not self.used_panels:
            return 0.0

        total_piece_area = sum(piece.area for piece in self.pieces)
        total_panel_area = sum(panel.area for panel in self.used_panels)

        return (total_piece_area / total_panel_area) * 100 if total_panel_area > 0 else 0.0



    def _reset_pieces(self):
        """Prépare une copie propre des pièces (non placées, non modifiées)"""
        self.pieces = [copy.deepcopy(p) for p in self.original_pieces]

    def load_pieces(self, pieces: List[Piece]):
        """Charge les pièces et conserve une copie originale pour réinitialiser plus tard"""
        self.original_pieces = []
        self.pieces = []
        for piece in pieces:
            for i in range(piece.quantity):
                new_piece = piece.copy()
                if i > 0:
                    new_piece.name += f"_copy_{i}"
                self.original_pieces.append(new_piece)
        self._reset_pieces()

    def find_best_panel_template(self, panel_templates: List[Panel], algorithm=rectpack.SkylineMwf):
        best_efficiency = 0
        best_template = None
        best_result = []
        best_total_area = None

        for template in panel_templates:
            self._reset_pieces()
            self.set_panel_template(template)
            result = self.optimize(algorithm)
            efficiency = self.get_global_efficiency()
            total_area = sum(p.area for p in self.used_panels)

            # print(f"Essai avec panneau '{template.name}': efficacité = {efficiency:.2f}%, chutes = {100 - efficiency:.2f}%")

            if (efficiency > best_efficiency) or \
                    (efficiency == best_efficiency and (best_total_area is None or total_area < best_total_area)):
                best_efficiency = efficiency
                best_template = template
                best_result = copy.deepcopy(self.used_panels)
                best_total_area = total_area

        # Charger le meilleur résultat
        self.set_panel_template(best_template)
        self.used_panels = best_result
        # print(f"\n✅ Meilleur panneau sélectionné: {best_template.name} ({best_efficiency:.2f}% efficacité)\n")

    def export_result(self):
        results=[]
        for panel in self.used_panels:
            panel_data={
                "Panel":panel.name,
                "Parts":[]
            }
            for piece in panel.pieces:
                piece_data={
                    "label": piece.name,
                    "x": piece.x,
                    "y": piece.y,
                    "width": piece.width,
                    "height": piece.height,
                    "Name" : piece.label
                }
                panel_data["Pieces"].append(piece_data)

                results.append(panel_data)

        return results
