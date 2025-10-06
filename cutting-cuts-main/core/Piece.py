from typing import List, Tuple, Optional
import uuid

class Piece:
    def __init__(self, width: float, height: float, name: str = None, material: str = None, quantity: int = 1,label:str=None):
        self.id = str(uuid.uuid4())[:8]  # ID unique court
        self.width = width
        self.height = height
        self.name = name if name else f"Piece_{self.id}"
        self.material = material
        self.quantity = quantity
        self.area = width * height
        self.label=label

        # Position après découpe (sera rempli par l'optimiseur)
        self.x = None
        self.y = None
        self.panel_id = None
        self.is_rotated = False

    def __repr__(self):
        return f"Piece(id={self.id}, name='{self.name}', {self.width}x{self.height}, qty={self.quantity})"

    def get_dimensions(self) -> Tuple[float, float]:
        """Retourne les dimensions (largeur, hauteur)"""
        return (self.width, self.height)

    def rotate(self):
        """Effectue une rotation de 90°"""
        self.width, self.height = self.height, self.width
        self.is_rotated = not self.is_rotated

    def copy(self):
        """Crée une copie de la pièce"""
        new_piece = Piece(self.width, self.height, self.name, self.material, 1)
        new_piece.is_rotated = self.is_rotated
        return new_piece