from typing import List, Tuple
from core.Pannel import Panel
from core.Piece import Piece
def check_piece_fit(pieces: List[Piece], panels: List[Panel], rotation_allowed=True, cut_marge=0,
                    trimLeft=0, trimRight=0, trimTop=0, trimBottom=0):

    valid_pieces = []
    rejected_pieces = []

    for piece in pieces:
        fits = False
        for panel in panels:
            usable_width = panel.width - (trimLeft + trimRight)
            usable_height = panel.height - (trimTop + trimBottom)

            # dimensions pièce avec marge
            pw = piece.width + cut_marge
            ph = piece.height + cut_marge

            # cas 1: sans rotation
            if pw <= usable_width and ph <= usable_height:
                fits = True
                break

            # cas 2: rotation autorisée
            if rotation_allowed and ph <= usable_width and pw <= usable_height:
                fits = True
                break

        if fits:
            valid_pieces.append(piece)
        else:
            rejected_pieces.append(piece)

    return valid_pieces, rejected_pieces
