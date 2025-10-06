
import  json
def subtract(rect, part):
    """Soustrait part de rect et retourne les zones vides restantes"""
    rx, ry, rw, rh = rect
    px, py, pw, ph = part

    # Vérifier chevauchement
    if px >= rx+rw or py >= ry+rh or px+pw <= rx or py+ph <= ry:
        return [rect]  # pas de chevauchement → rect reste entier

    chutes = []
    # zone à gauche
    if px > rx:
        chutes.append((rx, ry, px-rx, rh))
    # zone à droite
    if px+pw < rx+rw:
        chutes.append((px+pw, ry, (rx+rw)-(px+pw), rh))
    # zone au-dessus
    if py > ry:
        chutes.append((rx, ry, rw, py-ry))
    # zone en dessous
    if py+ph < ry+rh:
        chutes.append((rx, py+ph, rw, (ry+rh)-(py+ph)))

    return chutes


def detect_chutes(json_panels):
    """Enrichit le JSON avec les chutes calculées"""
    for panel in json_panels:
        free_spaces = [(0, 0, panel["width"], panel["height"])]

        # Soustraire chaque pièce
        for part in panel["Parts"]:
            new_spaces = []
            for space in free_spaces:
                new_spaces.extend(subtract(space, (part["x"], part["y"], part["width"], part["height"])))
            free_spaces = new_spaces

        # Enrichir le JSON avec les chutes
        panel["Chutes"] = [
            {"label": f"chute{i+1}", "x": x, "y": y, "width": w, "height": h}
            for i, (x, y, w, h) in enumerate(free_spaces)
        ]

    return json_panels



json_data = [
    {"Panel": "MAT_PO_PA_HGS_PBO_C182_ESS_19_2800_2070_used_1", "height": 2800.0, "width": 2070.0, "Parts": [
        {"label": "MAT_PO_PA_HGS_PBO_C182_ESS_19", "x": 0, "y": 0, "width": 1190.0, "height": 2599.0},
        {"label": "MAT_PO_PA_HGS_PBO_C182_ESS_19", "x": 1206.75, "y": 0, "width": 600.0, "height": 2600.0
        }]}
     ]


result = detect_chutes(json_data)


print(json.dumps(result, indent=4))
