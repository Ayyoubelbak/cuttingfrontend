from typing import List, Tuple, Optional
import uuid

from core.Piece import Piece
class Panel:
    """Classe représentant un panneau (conteneur) sur lequel découper"""

    def __init__(self, width: float, height: float, name: str = None, material: str = None, cost: float = 0.0):

        self.id = str(uuid.uuid4())[:8]  # ID unique court
        self.width = width
        self.height = height
        self.name = name if name else f"Panel_{self.id}"
        self.material = material
        self.area = width * height

        # Pièces placées sur ce panneau
        self.pieces: List[Piece] = []
        self.used_area = 0.0

        self.efficiency = 0.0

    def __repr__(self):
        return f"Panel(id={self.id}, name='{self.name}', {self.width}x{self.height}, pieces={len(self.pieces)})"

    def add_piece(self, piece: Piece, x: float, y: float):
        """Ajoute une pièce positionnée sur le panneau"""
        piece.x = x
        piece.y = y
        piece.panel_id = self.id
        self.pieces.append(piece)
        self.used_area += piece.area
        self.efficiency = (self.used_area / self.area) * 100

    def get_remaining_area(self) -> float:
        """Retourne l'aire restante disponible"""
        return self.area - self.used_area

    def get_waste_percentage(self) -> float:
        """Retourne le pourcentage de chute"""
        return 100 - self.efficiency

    def clear(self):
        """Vide le panneau de toutes ses pièces"""
        for piece in self.pieces:
            piece.x = None
            piece.y = None
            piece.panel_id = None
        self.pieces.clear()
        self.used_area = 0.0
        self.efficiency = 0.0
