def merge_vertical_chutes(chutes, tolerance=1e-6):
    """
    Fusionne les chutes alignées verticalement
    """
    if len(chutes) < 2:
        return chutes

    # Trier par position X puis Y
    sorted_chutes = sorted(chutes, key=lambda c: (c['x'], c['y']))

    merged = []
    used = set()

    for i in range(len(sorted_chutes)):
        if i in used:
            continue

        current = sorted_chutes[i]
        best_merge = None
        best_index = None

        # Chercher une chute alignée verticalement
        for j in range(i + 1, len(sorted_chutes)):
            if j in used:
                continue

            candidate = sorted_chutes[j]

            # Vérifier l'alignement vertical
            if (abs(current['x'] - candidate['x']) <= tolerance and
                    abs(current['width'] - candidate['width']) <= tolerance and
                    abs(current['y'] + current['height'] - candidate['y']) <= tolerance):

                # Fusion possible !
                if best_merge is None or candidate['y'] < best_merge['y']:
                    best_merge = candidate
                    best_index = j

        if best_merge is not None:
            # Fusionner les deux chutes
            new_chute = {
                'x': current['x'],
                'y': current['y'],
                'width': current['width'],
                'height': current['height'] + best_merge['height']
            }
            merged.append(new_chute)
            used.add(i)
            used.add(best_index)
        else:
            # Aucune fusion trouvée, garder la chute originale
            merged.append(current)
            used.add(i)

    return merged


def merge_horizontal_chutes(chutes, tolerance=1e-6):
    """
    Fusionne les chutes alignées horizontalement
    """
    if len(chutes) < 2:
        return chutes

    # Trier par position Y puis X
    sorted_chutes = sorted(chutes, key=lambda c: (c['y'], c['x']))

    merged = []
    used = set()

    for i in range(len(sorted_chutes)):
        if i in used:
            continue

        current = sorted_chutes[i]
        best_merge = None
        best_index = None

        # Chercher une chute alignée horizontalement
        for j in range(i + 1, len(sorted_chutes)):
            if j in used:
                continue

            candidate = sorted_chutes[j]

            # Vérifier l'alignement horizontal
            if (abs(current['y'] - candidate['y']) <= tolerance and
                    abs(current['height'] - candidate['height']) <= tolerance and
                    abs(current['x'] + current['width'] - candidate['x']) <= tolerance):

                # Fusion possible !
                if best_merge is None or candidate['x'] < best_merge['x']:
                    best_merge = candidate
                    best_index = j

        if best_merge is not None:
            # Fusionner les deux chutes
            new_chute = {
                'x': current['x'],
                'y': current['y'],
                'width': current['width'] + best_merge['width'],
                'height': current['height']
            }
            merged.append(new_chute)
            used.add(i)
            used.add(best_index)
        else:
            # Aucune fusion trouvée, garder la chute originale
            merged.append(current)
            used.add(i)

    return merged


def merge_all_chutes(chutes, tolerance=1e-6):
    """
    Fusionne toutes les chutes possibles (verticalement et horizontalement)
    """
    # Fusion verticale d'abord
    vertical_merged = merge_vertical_chutes(chutes, tolerance)

    # Puis fusion horizontale
    fully_merged = merge_horizontal_chutes(vertical_merged, tolerance)

    return fully_merged


def compute_mer(panel, pieces, merge_chutes=False):
    W, H = panel["width"], panel["height"]
    print(W, H)

    # NOUVEAU : Fusionner les chutes si demandé
    if merge_chutes:
        pieces = merge_all_chutes(pieces)

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