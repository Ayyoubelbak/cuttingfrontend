import copy
import json
from typing import List, Dict, Any
from typing import List, Tuple, Optional, Dict
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from rectpack import newPacker
import rectpack
from scipy.stats import alpha
from .ManagementChute import compute_mer,merge_adjacent_mers,merge_adjacent_mers_improved
from core.Pannel import Panel
from core.Piece import Piece

class MultiPanelCuttingOptimizer:
    """Extension pour gérer plusieurs types de panneaux simultanément"""

    def __init__(self, rotation_allowed: bool = False, cut_marge: float = 0.0, trimLeft=0.0, trimRight=0.0, trimTop=0.0,trimBottom=0.0,min_width: float=0.0,min_height: float=0.0, min_area :float=0.0):
        self.rotation_allowed = rotation_allowed
        self.cut_marge = cut_marge
        self.pieces: List[Piece] = []
        self.panel_templates: List[Panel] = []
        self.used_panels: List[Panel] = []
        self.original_pieces: List[Piece] = []
        self.trimLeft = trimLeft
        self.trimRight = trimRight
        self.trimTop = trimTop
        self.trimBottom = trimBottom
        self.min_width=min_width
        self.min_height=min_height
        self.min_area=min_area

    def add_panel_template(self, panel: Panel, max_quantity: int = None):
        """Ajoute un type de panneau disponible"""
        panel.max_quantity = max_quantity  # None = illimité
        self.panel_templates.append(panel)


    def load_pieces(self, pieces: List[Piece]):
        """Charge les pièces"""
        self.original_pieces = []
        self.pieces = []
        for piece in pieces:
            for i in range(piece.quantity):
                new_piece = piece.copy()
                if i > 0:
                    new_piece.name += f"_copy_{i}"
                self.original_pieces.append(new_piece)
        self._reset_pieces()

    def _reset_pieces(self):
        """Remet les pièces dans leur état initial"""
        self.pieces = [copy.deepcopy(p) for p in self.original_pieces]

    def optimize_multi_panel_greedy(self) -> List[Panel]:
        """
        Algorithme glouton pour optimiser avec plusieurs types de panneaux
        Stratégie: Pour chaque groupe de pièces, choisir le panneau le plus efficace
        """

        if not self.panel_templates:
            raise ValueError("Aucun modèle de panneau défini")

        self._reset_pieces()
        remaining_pieces = self.pieces.copy()

        self.used_panels = []
        panel_usage_count = {template.name: 0 for template in self.panel_templates}

        while remaining_pieces:
            best_option = None
            best_efficiency = 0
            best_pieces_placed = []

            # Tester chaque type de panneau
            for template in self.panel_templates:
                # Vérifier la limite de quantité
                if template.max_quantity and panel_usage_count[template.name] >= template.max_quantity:
                    continue

                # Tester ce panneau avec les pièces restantes
                efficiency, pieces_placed = self._test_panel_with_pieces(template, remaining_pieces)

                # print(efficiency)


                if efficiency > best_efficiency and pieces_placed:
                    best_efficiency = efficiency
                    best_option = template
                    best_pieces_placed = pieces_placed

            if not best_option or not best_pieces_placed:
                # print(f"Impossible de placer les pièces restantes: {len(remaining_pieces)}")
                break

            # Créer le panneau avec les meilleures pièces

            panel = self._create_panel_with_pieces(best_option, best_pieces_placed)


            # print(self.used_panels)
            self.used_panels.append(panel)
            panel_usage_count[best_option.name] += 1

            # Retirer les pièces placées

            for piece in best_pieces_placed:
                remaining_pieces.remove(piece)


            # print(f"✅ Panneau {len(self.used_panels)}: {best_option.name} "
            #       f"({best_efficiency:.1f}% efficacité, {len(best_pieces_placed)} pièces)")


        return self.used_panels



    def sort_pieces(self, pieces):
        pieces_sorted = []
        # 1. Grouper par dimensions identiques
        pieces.sort(key=lambda p: p.area, reverse=True)

        # 2. Si même largeur, placer avant
        # 3. Sinon si même hauteur
        # 4. Enfin, par aire décroissante (grandes d'abord)
        pieces.sort(key=lambda p: p.width, reverse=True)

        return pieces

    def _test_panel_with_pieces(self, template: Panel, pieces: List[Piece]) -> Tuple[float, List[Piece]]:
        """Teste un panneau avec un ensemble de pièces et retourne l'efficacité"""
        # packer = newPacker(rotation=self.rotation_allowed, pack_algo=rectpack.GuillotineBssfMinas  )
        packer = newPacker(rotation=self.rotation_allowed, pack_algo=rectpack.SkylineBlWm)
        usable_height = template.height - self.trimBottom - self.trimTop
        usable_width = template.width - self.trimRight - self.trimLeft
        packer.add_bin(usable_width, usable_height)
        # Trier les pièces par aire décroissante (stratégie First Fit Decreasing)
        sorted_pieces = sorted(pieces, key=lambda p: (-max(p.width, p.height), -min(p.width, p.height)))



        for i, piece in enumerate(sorted_pieces):
            if piece.height == usable_height and piece.width == usable_width:
                packer.add_rect(piece.width,
                                piece.height,
                                i
                                )
            elif piece.height == usable_height and piece.width <= usable_width:
                packer.add_rect(piece.width + self.cut_marge,
                                piece.height,
                                i)
            elif piece.height <= usable_height and piece.width == usable_width:
                packer.add_rect(piece.width,
                                piece.height + self.cut_marge,
                                i)
            else:
                packer.add_rect(piece.width + self.cut_marge,
                                piece.height + self.cut_marge,
                                i
                                )

        packer.pack()

        placed_pieces = []
        total_placed_area = 0

        for bin_index, abin in enumerate(packer):
            for rect in abin:
                piece = sorted_pieces[rect.rid]
                placed_pieces.append(piece)
                total_placed_area += piece.area


        efficiency = (total_placed_area / template.area) * 100 if template.area > 0 else 0
        return efficiency, placed_pieces

    def _create_panel_with_pieces(self, template: Panel, pieces: List[Piece]) -> Panel:


        """Crée un panneau optimisé avec les pièces données"""
        # print("""Crée un panneau optimisé avec les pièces données""")
        # print(template)
        packer = newPacker(rotation=self.rotation_allowed, pack_algo=rectpack.SkylineBlWm)
        # if self.cut_marge < self.trimLeft  and self.cut_marge < self.trimRight:
        #
        # elif self.cut_marge >= self.trimLeft and self.cut_marge >= self.trimRight:
        #     usable_height= template.height -

        usable_height = template.height - (self.trimTop + self.trimBottom)
        usable_width = template.width - (self.trimRight + self.trimLeft)
        packer.add_bin(usable_width, usable_height)

        for i, piece in enumerate(pieces):
            if piece.height == usable_height and piece.width == usable_width:
                packer.add_rect(piece.width,
                                piece.height,
                                i
                                )
            elif piece.height == usable_height and piece.width < usable_width:
                packer.add_rect(piece.width + self.cut_marge,
                                piece.height,
                                i)
            elif piece.height < usable_height and piece.width == usable_width:
                packer.add_rect(piece.width,
                                piece.height + self.cut_marge,
                                i)
            else:
                packer.add_rect(piece.width + self.cut_marge,
                                piece.height + self.cut_marge,
                                i
                                )

        packer.pack()

        # Création du panneau résultat
        panel = Panel(
            template.width,
            template.height,
            f"{template.name}_used_{len(self.used_panels) + 1}",
            template.material
        )

        # Placement des pièces
        for bin_index, abin in enumerate(packer):
            for rect in abin:
                piece = pieces[rect.rid]

                # Gestion de la rotation
                if ((rect.width == piece.height + self.cut_marge and rect.height == piece.width + self.cut_marge) or
                        (rect.width == piece.height and rect.height == piece.width)):
                    piece.rotate()

                if rect.x == 0:
                    x = rect.x + self.trimLeft
                elif rect.x + rect.width >= usable_width:
                    x = rect.x + self.trimLeft
                else:
                    x = rect.x  + self.trimLeft
                if rect.y == 0:
                    y = rect.y + self.trimBottom
                elif rect.y + rect.height >= usable_height:
                    y = rect.y + self.trimBottom
                else:
                    y = rect.y  + self.trimBottom

                piece.x = x
                piece.y = y
                panel.add_piece(piece, x, y)

        return panel


    def _group_pieces_by_size(self) -> List[List[Piece]]:
        """Groupe les pièces par taille similaire pour optimiser l'allocation"""
        # Algorithme de clustering simple basé sur l'aire
        groups = []
        remaining = self.pieces.copy()

        while remaining:
            # Prendre la plus grande pièce restante comme référence
            reference = max(remaining, key=lambda p: p.area)
            group = [reference]
            remaining.remove(reference)

            # Ajouter les pièces de taille similaire (±20% d'aire)
            tolerance = 0.2
            to_remove = []

            for piece in remaining:
                ratio = min(piece.area, reference.area) / max(piece.area, reference.area)
                if ratio >= (1 - tolerance):
                    group.append(piece)
                    to_remove.append(piece)

            for piece in to_remove:
                remaining.remove(piece)

            groups.append(group)

        return groups

    def print_multi_panel_summary(self):
        """Affiche un résumé détaillé pour multi-panneaux"""
        print("=" * 70)
        print("RÉSUMÉ OPTIMISATION MULTI-PANNEAUX")
        print("=" * 70)
        print(f"Nombre de pièces: {len(self.original_pieces)}")
        print(f"Nombre de panneaux utilisés: {len(self.used_panels)}")
        print()

        # Détail par type de panneau
        print("Répartition par type de panneau:")

        # Détail de chaque panneau

        for i, panel in enumerate(self.used_panels):
            print(f"Panneau {i + 1}: {panel.name}")
            print(f"  - Dimensions: {panel.width}×{panel.height}")
            print(f"  - Pièces: {len(panel.pieces)}")
            print(f"  - Efficacité: {panel.efficiency:.2f}%")

    def visualize_panel(self, panel_index: int = 0):
        """Visualise un panneau spécifique"""
        if panel_index >= len(self.used_panels):
            print(f"Panneau {panel_index} n'existe pas")
            return

        panel = self.used_panels[panel_index]

        fig, ax = plt.subplots(1, 1, figsize=(12, 10))

        # Dessiner le panneau avec couleur selon le type
        panel_color = self._get_panel_type_color(panel.name)

        panel_rect = patches.Rectangle(
            (0, 0), panel.width, panel.height,
            linewidth=3, edgecolor='black', facecolor=panel_color, alpha=0.2
        )
        ax.add_patch(panel_rect)

        # Couleurs pour les pièces
        colors = ['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'pink', 'brown', 'cyan', 'magenta']

        # Dessiner chaque pièce
        for i, piece in enumerate(panel.pieces):
            color = colors[i % len(colors)]
            trim_rect = patches.Rectangle(
                (self.trimLeft, self.trimBottom),
                panel.width - self.trimLeft - self.trimRight,
                panel.height - self.trimTop - self.trimBottom,
                linewidth=1, edgecolor='red', linestyle='--', facecolor='none', alpha=0.3
            )
            ax.add_patch(trim_rect)

            if self.cut_marge > 0:
                cut_rect = patches.Rectangle(
                    (piece.x - self.cut_marge + self.trimLeft, piece.y - self.cut_marge + self.trimBottom),
                    piece.width + self.cut_marge,
                    piece.height + self.cut_marge,
                    linewidth=0.5,
                    edgecolor='black',
                    facecolor='black',
                    linestyle='--',
                    alpha=0.5
                )
                ax.add_patch(cut_rect)
            piece_rect = patches.Rectangle(
                (piece.x + self.trimLeft, piece.y + self.trimBottom), piece.width, piece.height,
                linewidth=1, edgecolor='black', facecolor=color, alpha=0.7
            )
            ax.add_patch(piece_rect)

            # Texte avec info de la pièce
            text = f"{piece.name}\n{piece.width}x{piece.height}"
            if piece.is_rotated:
                text += "\n(R)"

            # Afficher le texte centré dans la pièce
            ax.text(
                piece.x + piece.width / 2, piece.y + piece.height / 2,
                text, ha='center', va='center', fontsize=8, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8)
            )

        ax.set_xlim(0, panel.width)
        ax.set_ylim(0, panel.height)
        ax.set_aspect('equal')

        # Titre avec informations détaillées
        panel_type = panel.name.split('_used_')[0]
        title = f'Panneau {panel_index + 1}: {panel_type} ({panel.width}×{panel.height}mm)\n'
        title += f'Efficacité: {panel.efficiency:.1f}% - Chute: {panel.get_waste_percentage():.1f}% - {len(panel.pieces)} pièces'
        ax.set_title(title, fontsize=12, fontweight='bold')

        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Largeur (mm)', fontsize=10)
        ax.set_ylabel('Hauteur (mm)', fontsize=10)

        plt.tight_layout()
        plt.show()

    def _get_panel_type_color(self, panel_name: str) -> str:
        """Retourne une couleur unique pour chaque type de panneau"""
        panel_type = panel_name.split('_used_')[0]
        color_map = {
            'Standard': 'lightblue',
            'Petit': 'lightcoral',
            'Grand': 'lightgreen',
            'Medium': 'lightyellow',
            'XL': 'lightpink'
        }
        return color_map.get(panel_type, 'lightgray')

    # def detecter_chutes_pour_un_panneau(self, panel_data: Dict) -> Dict:
    #     """
    #     Détecte les chutes pour un seul panneau et les ajoute au dictionnaire
    #     Retourne le panel_data avec une nouvelle clé 'chutes'
    #     """
    #     panel_name = panel_data["Panel"]
    #     panel_width = panel_data["width"]
    #     panel_height = panel_data["height"]
    #     parts = panel_data["Parts"]
    #
    #     # Dimensions utilisables (après trim)
    #     width_utilisable = panel_width - (self.trimLeft + self.trimRight)
    #     height_utilisable = panel_height - (self.trimTop + self.trimBottom)
    #
    #     panel_info = {"width": width_utilisable, "height": height_utilisable}
    #     pieces_info = []
    #
    #     # Préparer les pièces en ajustant les coordonnées
    #     for part in parts:
    #         pieces_info.append({
    #             "x": part["x"] - self.trimLeft,
    #             "y": part["y"] - self.trimBottom,
    #             "width": part["width"],
    #             "height": part["height"]
    #         })
    #
    #     # Calculer les MER
    #     mers = compute_mer(panel_info, pieces_info)
    #     mers_fusionnes = merge_adjacent_mers_improved(mers, eps=self.cut_marge + 0.5)
    #
    #     # Filtrer les chutes trop petites
    #     mers_fusionnes = [
    #         (x, y, w, h) for (x, y, w, h) in mers_fusionnes
    #         if w >= self.min_width and h >= self.min_height and w * h >= self.min_area * 1000000
    #     ]
    #
    #     # Formater les chutes avec ajustement des marges
    #     chutes_formatees = []
    #     for x, y, w, h in mers_fusionnes:
    #         # Ajustements basés sur la position dans le panneau
    #         if y == 0:  # Chute en bas
    #             chute_x = x + self.cut_marge
    #             chute_y = y + self.trimBottom
    #             chute_width = w - 2 * self.cut_marge  # Marges des deux côtés
    #             chute_height = h - self.cut_marge  # Marge seulement en haut
    #
    #         elif y + h == height_utilisable:  # Chute en haut
    #             chute_x = x + self.cut_marge
    #             chute_y = y + self.trimBottom
    #             chute_width = w - 2 * self.cut_marge
    #             chute_height = h - self.cut_marge
    #
    #         elif x == 0:  # Chute à gauche
    #             chute_x = x + self.trimLeft
    #             chute_y = y + self.trimBottom + self.cut_marge
    #             chute_width = w - self.cut_marge
    #             chute_height = h - 2 * self.cut_marge
    #
    #         elif x + w == width_utilisable:  # Chute à droite
    #             chute_x = x + self.trimLeft
    #             chute_y = y + self.trimBottom + self.cut_marge
    #             chute_width = w - self.cut_marge
    #             chute_height = h - 2 * self.cut_marge
    #
    #         else:  # Chute interne
    #             chute_x = x + self.trimLeft + self.cut_marge
    #             chute_y = y + self.trimBottom + self.cut_marge
    #             chute_width = w - 2 * self.cut_marge
    #             chute_height = h - 2 * self.cut_marge
    #
    #         # S'assurer que les dimensions restent positives
    #         chute_width = max(0, chute_width)
    #         chute_height = max(0, chute_height)
    #
    #         if chute_width >= self.min_width and chute_height >= self.min_height:
    #             chutes_formatees.append({
    #                 "x": chute_x,
    #                 "y": chute_y,
    #                 "width": chute_width,
    #                 "height": chute_height,
    #                 "surface": chute_width * chute_height
    #             })
    #
    #     # Ajouter les chutes au dictionnaire du panneau
    #     panel_data_avec_chutes = panel_data.copy()
    #     panel_data_avec_chutes["chutes"] = chutes_formatees
    #
    #     return panel_data_avec_chutes


    def detecter_chutes_pour_un_panneau(self, panel_data: Dict) -> Dict:
        """
        Détecte les chutes pour un seul panneau et les ajoute au dictionnaire
        Retourne le panel_data avec une nouvelle clé 'chutes'
        """
        panel_name = panel_data["Panel"]
        panel_width = panel_data["width"]
        panel_height = panel_data["height"]
        parts = panel_data["Parts"]

        # Préparer les données pour compute_mer
        width_utilisable=panel_width-(self.trimLeft+self.trimRight)
        height_utilisable=panel_height-(self.trimTop+self.trimBottom)
        panel_info = {"width": width_utilisable, "height": height_utilisable}
        pieces_info = []

        for part in parts:
            print(part)
            print("---------------------------")
            pieces_info.append({
                "x": part["x"]-self.trimLeft,
                "y": part["y"]-self.trimBottom,
                "width": part["width"],
                "height": part["height"]
            })
            print(pieces_info)
            print("11111111111111111111111111111111")



        # Calculer les MER
        mers = compute_mer(panel_info, pieces_info)

        mers_fusionnes=merge_adjacent_mers_improved(mers,eps=self.cut_marge+0.5)



        mers_fusionnes = [(x, y, w, h) for (x, y, w, h) in mers_fusionnes if w >= self.min_width and h >= self.min_height and w*h>=self.min_area*1000000]


        # Formater les chutes
        chutes_formatees = []
        for x, y, w, h in mers_fusionnes:
            # if y==0 :
            #     chutes_formatees.append({
            #         "x": x+self.cut_marge,
            #         "y": y + self.trimBottom,
            #         "width": w + self.trimRight + self.trimLeft,
            #         "height": h -200 ,
            #         "surface": w * h
            #     })
            # else :
            #     chutes_formatees.append({
            #         "x": x,
            #         "y": y + self.trimBottom,
            #         "width": w + self.trimRight + self.trimLeft,
            #         "height": h + self.trimTop + self.trimBottom,
            #         "surface": w * h
            #     })
            # print("============================")
            # print(chutes_formatees)


            width_reelle=w-self.cut_marge
            height_reelle=h+self.cut_marge
            if x == 0 and y != 0 :
                if w < width_utilisable :
                    chutes_formatees.append({
                        "x": x,
                        "y": y +self.trimBottom+self.cut_marge,
                        "width": w +self.trimLeft ,
                        "height": h+self.trimTop-self.cut_marge ,
                        "surface": w * h
                    })

                if w == width_utilisable :
                    chutes_formatees.append({
                        "x": x,
                        "y": y + self.trimBottom+self.cut_marge,
                        "width": w + self.trimRight + self.trimLeft,
                        "height": h+self.trimTop -self.cut_marge,
                        "surface": w * h
                    })
                    print("x == 0 and y != 0")

            elif y ==0  :
                if h == height_utilisable :
                    chutes_formatees.append({
                        "x": x+self.cut_marge+self.trimLeft,
                        "y": y+self.trimBottom,
                        "width": w + self.trimRight + self.cut_marge,
                        "height": h + self.trimTop,
                        "surface": w * h
                    })
                print("if y==0")

                if h < height_utilisable:
                    chutes_formatees.append({
                        "x": x+self.trimLeft+self.cut_marge,
                        "y": y+self.trimBottom,
                        "width": w + self.trimRight-self.cut_marge,
                        "height": h ,
                        "surface": w * h
                    })


            elif x + w == width_utilisable and y != 0 and x !=0:

                chutes_formatees.append({
                    "x": x + self.trimLeft,
                    "y": y + self.trimBottom+self.cut_marge,
                    "width": w+self.trimRight,
                    "height": h - self.cut_marge,
                    "surface": w * h
                })
                print("x + w == panel_width and y != 0 and x !=0")

            elif x != 0 and y != self.cut_marge and x+w != width_utilisable:
                chutes_formatees.append({
                    "x": x + self.trimLeft,
                    "y": y+self.trimBottom,
                    "width": w-2*self.cut_marge,
                    "height": h-self.cut_marge,
                    "surface": w * h
                })




            else :
                chutes_formatees.append({
                    "x": x + self.trimLeft,
                    "y": y + self.trimBottom,
                    "width": w + self.trimRight,
                    "height": h,
                    "surface": w * h
                })
                print("x + w == panel_widthwidth_utilisablepanel_width and y != 0 and x !=0")
                print(x + w, width_reelle)
                print(x + w, width_utilisable)
                print(x + w, panel_width)







            # if width_reelle>=self.min_width and height_reelle>=self.min_height:
            #     if y==self.cut_marge:
            #         chutes_formatees.append({
            #             "x": x + self.trimLeft,
            #             "y": y + self.trimBottom-self.cut_marge,
            #             "width": w,
            #             "height": h,
            #             "surface": w * h
            #         })
            #     elif x==0:
            #         chutes_formatees.append({
            #             "x": x + self.trimLeft,
            #             "y": y + self.trimBottom,
            #             "width": w,
            #             "height": h,
            #             "surface": w * h
            #         })
            #     elif x+w==panel_width-self.trimRight:
            #         chutes_formatees.append({
            #             "x": x + self.trimLeft,
            #             "y": y + self.trimBottom,
            #             "width": w,
            #             "height": h-self.cut_marge,
            #             "surface": w * h
            #         })
            #
            #
            #     else:
            #         chutes_formatees.append({
            #             "x": x + self.trimLeft,
            #             "y": y + self.trimBottom,
            #             "width": w,
            #             "height": h-self.cut_marge,
            #             "surface": w * h
            #         })
            #
            #







        # Ajouter les chutes au dictionnaire du panneau (sans modifier l'original)
        panel_data_avec_chutes = panel_data.copy()
        panel_data_avec_chutes["chutes"] = chutes_formatees

        return panel_data_avec_chutes

    def export_result(self):
        results = {}


        for panel in self.used_panels:
            mat = panel.material

            panel_data = {
                "Panel": panel.name,
                "height":panel.height,
                "width":panel.width,
                "Parts": [
                    {
                        "label": piece.name,
                        "x": piece.x,
                        "y": piece.y,
                        "width": piece.width,
                        "height": piece.height,
                        "name": piece.label
                    }
                    for piece in panel.pieces
                ]
            }
            chutes= self.detecter_chutes_pour_un_panneau(panel_data)

            if mat not in results:
                results[mat] = []

            results[mat].append(chutes)


        final_results = [{mat: panels} for mat, panels in results.items()]
        return final_results

    def reset(self):
        self.panel_templates=[]
        self.used_panels=[]
        self.pieces=[]
        self.original_pieces=[]













