def compute_mer(panel, pieces):
    W, H = panel["width"], panel["height"]
    print(W, H)

    # 1. Collecter les coordonnées critiques
    xs = {0, W}
    ys = {0, H}
    for p in pieces:
        xs.add(p["x"])
        xs.add(p["x"] + p["width"])
        ys.add(p["y"])
        ys.add(p["y"] + p["height"])

    xs = sorted(xs)
    ys = sorted(ys)

    # 2. Générer les rectangles candidats
    candidates = []
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            x1, x2 = xs[i], xs[i + 1]
            y1, y2 = ys[j], ys[j + 1]
            rect = (x1, y1, x2 - x1, y2 - y1)

            # Vérifier si ce rect chevauche une pièce
            overlap = False
            for p in pieces:
                if not (x2 <= p["x"] or x1 >= p["x"] + p["width"] or
                        y2 <= p["y"] or y1 >= p["y"] + p["height"]):
                    overlap = True
                    break

            if not overlap:
                candidates.append(rect)

    # 3. Filtrer pour garder les maximaux
    mers = []
    for r in candidates:
        x, y, w, h = r
        contained = False
        for r2 in candidates:
            if r != r2:
                x2, y2, w2, h2 = r2
                if x >= x2 and y >= y2 and x + w <= x2 + w2 and y + h <= y2 + h2:
                    contained = True
                    break
        if not contained:
            mers.append(r)

    return mers


def compute_mer_ignore_cutmargin(panel, pieces, cut_margin=0):
    """
    Calcule les MERs en ignorant les espaces de coupe entre pièces adjacentes
    """
    W, H = panel["width"], panel["height"]

    # 1. Créer des "super-pièces" en fusionnant les pièces adjacentes
    super_pieces = merge_adjacent_pieces(pieces, cut_margin)

    # 2. Calculer les MERs normalement sur les super-pièces
    return compute_mer(panel, super_pieces)


def merge_adjacent_pieces(pieces, cut_margin):
    """
    Fusionne les pièces qui sont séparées par moins de cut_margin
    """
    if not pieces:
        return []

    # Convertir en format (x1, y1, x2, y2)
    rects = []
    for p in pieces:
        rects.append({
            'x1': p['x'],
            'y1': p['y'],
            'x2': p['x'] + p['width'],
            'y2': p['y'] + p['height'],
            'original': p
        })

    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(rects):
            j = i + 1
            while j < len(rects):
                r1, r2 = rects[i], rects[j]

                # Vérifier l'adjacence horizontale
                horizontal_gap = min(abs(r1['x2'] - r2['x1']), abs(r2['x2'] - r1['x1']))
                same_height_band = not (r1['y2'] <= r2['y1'] or r2['y2'] <= r1['y1'])

                # Vérifier l'adjacence verticale
                vertical_gap = min(abs(r1['y2'] - r2['y1']), abs(r2['y2'] - r1['y1']))
                same_width_band = not (r1['x2'] <= r2['x1'] or r2['x2'] <= r1['x1'])

                # Fusionner si gap <= cut_margin
                if ((horizontal_gap <= cut_margin and same_height_band) or
                        (vertical_gap <= cut_margin and same_width_band)):
                    # Fusionner les deux rectangles
                    new_x1 = min(r1['x1'], r2['x1'])
                    new_y1 = min(r1['y1'], r2['y1'])
                    new_x2 = max(r1['x2'], r2['x2'])
                    new_y2 = max(r1['y2'], r2['y2'])

                    rects[i] = {
                        'x1': new_x1, 'y1': new_y1,
                        'x2': new_x2, 'y2': new_y2,
                        'original': [r1['original'], r2['original']]  # Garder trace
                    }
                    rects.pop(j)
                    changed = True
                    continue

                j += 1
            i += 1

    # Convertir en format pièce normal
    result = []
    for r in rects:
        result.append({
            'x': r['x1'],
            'y': r['y1'],
            'width': r['x2'] - r['x1'],
            'height': r['y2'] - r['y1'],
            'merged_from': r.get('original', [])
        })

    return result
def analyze_chute_merging(panel, chutes, cut_margin):
    """
    Analyse quelles chutes peuvent être fusionnées
    """
    # 1. MERs normaux (sans fusion)
    normal_mers = compute_mer(panel, chutes)

    # 2. MERs en ignorant les cut_margins (avec fusion potentielle)
    merged_mers = compute_mer_ignore_cutmargin(panel, chutes, cut_margin)

    # 3. Analyser les différences
    analysis = {
        'normal_mers': normal_mers,
        'merged_mers': merged_mers,
        'fusion_opportunities': []
    }

    # Trouver les MERs qui sont apparus grâce à la fusion
    for mer in merged_mers:
        # Vérifier si ce MER n'existait pas avant fusion
        is_new = True
        for normal_mer in normal_mers:
            if (abs(mer[0] - normal_mer[0]) < 1e-6 and
                    abs(mer[1] - normal_mer[1]) < 1e-6 and
                    abs(mer[2] - normal_mer[2]) < 1e-6 and
                    abs(mer[3] - normal_mer[3]) < 1e-6):
                is_new = False
                break

        if is_new:
            # Ce MER représente une opportunité de fusion
            analysis['fusion_opportunities'].append(mer)

    return analysis


# Exemple d'utilisation
panel = {"width": 100, "height": 100}
chutes = [
    {"x": 10, "y": 10, "width": 20, "height": 20},
    {"x": 32, "y": 10, "width": 20, "height": 20},  # Séparé par 2 unités
    {"x": 60, "y": 10, "width": 20, "height": 20}
]
cut_margin = 5  # Marge de coupe

analysis = analyze_chute_merging(panel, chutes, cut_margin)

print(f"MERs normaux: {len(analysis['normal_mers'])}")
print(f"MERs avec fusion: {len(analysis['merged_mers'])}")
print(f"Opportunités de fusion: {len(analysis['fusion_opportunities'])}")

for opportunity in analysis['fusion_opportunities']:
    x, y, w, h = opportunity
    print(f"Fusion possible: rectangle {w}x{h} à ({x}, {y})")