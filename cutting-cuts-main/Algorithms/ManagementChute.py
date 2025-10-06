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




def merge_adjacent_mers(mers, eps=1e-6, max_passes=10):
    # utilitaires
    def to_xyxy(r):
        if isinstance(r, dict):
            x, y, w, h = r['x'], r['y'], r['width'], r['height']
        else:
            x, y, w, h = r
        return {'x1': float(x), 'y1': float(y), 'x2': float(x + w), 'y2': float(y + h)}

    def to_xywh(r):
        return (r['x1'], r['y1'], r['x2'] - r['x1'], r['y2'] - r['y1'])

    def group_by_key(rects, key_fn):
        groups = []
        # groups : list of tuples (rep_key_values, list_of_rects)
        for r in rects:
            assigned = False
            ky = key_fn(r)
            for rep, lst in groups:
                # compare key components with eps
                if all(abs(ky[i] - rep[i]) <= eps for i in range(len(ky))):
                    lst.append(r)
                    assigned = True
                    break
            if not assigned:
                groups.append((ky, [r]))
        return [lst for rep, lst in groups]

    def merge_intervals_sorted_by_start(sorted_rects, axis='x'):
        """ axis='x' or 'y' : fusionne en suivant x (horiz) ou y (vert).
            sorted_rects sont rects avec mêmes span orthogonale (même y/h ou x/w)
        """
        merged = []
        cur = sorted_rects[0].copy()
        for nxt in sorted_rects[1:]:
            if axis == 'x':
                if cur['x2'] + eps >= nxt['x1']:  # touche ou chevauche
                    cur['x2'] = max(cur['x2'], nxt['x2'])
                else:
                    merged.append(cur)
                    cur = nxt.copy()
            else:  # axis == 'y'
                if cur['y2'] + eps >= nxt['y1']:
                    cur['y2'] = max(cur['y2'], nxt['y2'])
                else:
                    merged.append(cur)
                    cur = nxt.copy()
        merged.append(cur)
        return merged

    # normalize input
    rects = [to_xyxy(r) for r in mers]

    for _pass in range(max_passes):
        changed = False

        # --------- Horizontal pass: group by (y1, height) ----------
        groups = group_by_key(rects, lambda r: (r['y1'], r['y2'] - r['y1']))
        new_rects = []
        for group in groups:
            # trier par x1
            group_sorted = sorted(group, key=lambda r: r['x1'])
            merged = merge_intervals_sorted_by_start(group_sorted, axis='x')
            new_rects.extend(merged)
            if len(merged) != len(group):
                changed = True

        rects = new_rects

        # --------- Vertical pass: group by (x1, width) ----------
        groups = group_by_key(rects, lambda r: (r['x1'], r['x2'] - r['x1']))
        new_rects = []
        for group in groups:
            group_sorted = sorted(group, key=lambda r: r['y1'])
            merged = merge_intervals_sorted_by_start(group_sorted, axis='y')
            new_rects.extend(merged)
            if len(merged) != len(group):
                changed = True

        rects = new_rects

        if not changed:
            break

    # convertir en (x,y,w,h) et arrondir légèrement si eps > 0
    result = []
    for r in rects:
        x = r['x1']
        y = r['y1']
        w = r['x2'] - r['x1']
        h = r['y2'] - r['y1']
        # arrondir à 6 décimales pour éviter long float
        result.append((round(x, 6), round(y, 6), round(w, 6), round(h, 6)))
    return result




def merge_adjacent_mers_improved(mers, eps=1e-6):
    """
    Fusionne les MERs adjacents de manière récursive jusqu'à ce qu'aucune fusion ne soit possible.
    """
    if not mers:
        return []

    # Convertir en format uniforme
    rects = []
    for r in mers:
        if isinstance(r, dict):
            rects.append({
                'x1': float(r['x']),
                'y1': float(r['y']),
                'x2': float(r['x'] + r['width']),
                'y2': float(r['y'] + r['height'])
            })
        else:
            x, y, w, h = r
            rects.append({
                'x1': float(x),
                'y1': float(y),
                'x2': float(x + w),
                'y2': float(y + h)
            })

    # Boucle de fusion
    changed = True
    iteration = 0
    max_iterations = 50

    while changed and iteration < max_iterations:
        changed = False
        iteration += 1
        i = 0

        while i < len(rects):
            j = i + 1
            merged_in_this_pass = False

            while j < len(rects):
                merged_rect = try_merge_two_rects(rects[i], rects[j], eps)

                if merged_rect is not None:
                    # Remplacer rects[i] par le rectangle fusionné
                    rects[i] = merged_rect
                    # Supprimer rects[j]
                    rects.pop(j)
                    changed = True
                    merged_in_this_pass = True
                    # Ne pas incrémenter j, car on vient de supprimer un élément
                else:
                    j += 1

            # Si on a fusionné quelque chose avec rects[i], on le réexamine
            if not merged_in_this_pass:
                i += 1

    # Convertir en (x, y, w, h)
    result = []
    for r in rects:
        x = round(r['x1'], 6)
        y = round(r['y1'], 6)
        w = round(r['x2'] - r['x1'], 6)
        h = round(r['y2'] - r['y1'], 6)
        result.append((x, y, w, h))

    return result


def try_merge_two_rects(rect1, rect2, eps=1e-6):
    """
    Tente de fusionner deux rectangles adjacents.
    Retourne le rectangle fusionné ou None.
    """
    # Cas 1: Adjacents HORIZONTALEMENT (côte à côte)
    # Même y1, même y2, et x2 de l'un touche x1 de l'autre
    if (abs(rect1['y1'] - rect2['y1']) <= eps and
            abs(rect1['y2'] - rect2['y2']) <= eps):

        # rect1 à gauche de rect2
        if abs(rect1['x2'] - rect2['x1']) <= eps:
            return {
                'x1': rect1['x1'],
                'y1': rect1['y1'],
                'x2': rect2['x2'],
                'y2': rect1['y2']
            }

        # rect2 à gauche de rect1
        if abs(rect2['x2'] - rect1['x1']) <= eps:
            return {
                'x1': rect2['x1'],
                'y1': rect1['y1'],
                'x2': rect1['x2'],
                'y2': rect1['y2']
            }

    # Cas 2: Adjacents VERTICALEMENT (l'un au-dessus de l'autre)
    # Même x1, même x2, et y2 de l'un touche y1 de l'autre
    if (abs(rect1['x1'] - rect2['x1']) <= eps and
            abs(rect1['x2'] - rect2['x2']) <= eps):

        # rect1 en bas, rect2 en haut
        if abs(rect1['y2'] - rect2['y1']) <= eps:
            return {
                'x1': rect1['x1'],
                'y1': rect1['y1'],
                'x2': rect1['x2'],
                'y2': rect2['y2']
            }

        # rect2 en bas, rect1 en haut
        if abs(rect2['y2'] - rect1['y1']) <= eps:
            return {
                'x1': rect1['x1'],
                'y1': rect2['y1'],
                'x2': rect1['x2'],
                'y2': rect1['y2']
            }

    return None