import cv2
import numpy as np
import networkx as nx
import os
import pandas as pd
from skimage.morphology import skeletonize
from shapely.geometry import LineString

from sproutcv.utils.graph_utils import (
    build_graph_from_skeleton,
    simplify_path,
    reconnect_path,
    find_farthest_nodes
)

# ---------------- Preprocessing ---------------- #

def preprocess_image(image_path):

    image = cv2.imread(image_path)

    shifted = cv2.pyrMeanShiftFiltering(image, sp=20, sr=40)
    gray = cv2.cvtColor(shifted, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    _, binary = cv2.threshold(
        blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)

    return image, cleaned, gray


# ---------------- Core Measurement ---------------- #

def analyze_sprouts(image, cleaned, gray, mm_to_pixel_ratio):

    h, w = image.shape[:2]

    font_scale = max(0.45, min(h, w) / 1500)
    thickness = max(1, int(font_scale * 3))

    used_boxes = []

    contours, _ = cv2.findContours(
        cleaned,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    # ---------- Row grouping ---------- #
    items = []

    for c in contours:

        if cv2.contourArea(c) < 300:
            continue

        M = cv2.moments(c)
        if M["m00"] == 0:
            continue

        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        items.append((c, cx, cy))

    row_tol = int(h * 0.08)

    items.sort(key=lambda x: x[2])
    rows = []

    for c, cx, cy in items:

        for r in rows:
            if abs(r[0][2] - cy) < row_tol:
                r.append((c, cx, cy))
                break
        else:
            rows.append([(c, cx, cy)])

    # ---------- Visualization ---------- #

    out = image.copy()
    skeleton_image = np.zeros_like(gray)
    sprout_data = []

    idx = 1

    def overlaps(b):
        for u in used_boxes:
            if not (b[2] < u[0] or b[0] > u[2] or b[3] < u[1] or b[1] > u[3]):
                return True
        return False

    def keep_inside(x, y, tw, th):
        x = max(8, min(x, w - tw - 8))
        y = max(th + 8, min(y, h - 8))
        return x, y

    # ---------- Process each sprout ---------- #

    for row in rows:

        row.sort(key=lambda x: x[1])

        for ci, (contour, cx, cy) in enumerate(row):

            cv2.drawContours(out, [contour], -1, (255, 0, 0), 2)

            mask = np.zeros_like(gray)
            cv2.drawContours(mask, [contour], -1, 255, -1)

            sk = skeletonize(mask > 0).astype(np.uint8) * 255
            skeleton_image = cv2.bitwise_or(skeleton_image, sk)

            G = build_graph_from_skeleton(sk)

            if len(G.nodes) < 2:
                continue

            n1, n2 = find_farthest_nodes(G)

            path = simplify_path(nx.shortest_path(G, n1, n2))
            px_len = reconnect_path(G, path)
            mm_len = px_len * mm_to_pixel_ratio

            sprout_data.append([idx, px_len, mm_len])

            # ----- Draw skeleton path -----
            for i in range(len(path) - 1):

                p1 = (int(path[i][1]), int(path[i][0]))
                p2 = (int(path[i+1][1]), int(path[i+1][0]))

                cv2.line(out, p1, p2, (0, 0, 255), 2)

            # ----- Label placement -----
            label = f"{idx}: {mm_len:.2f} mm"

            (tw, th), _ = cv2.getTextSize(
                label,
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                thickness
            )

            x = cx - tw // 2
            y = cy - 30 if ci % 2 == 0 else cy + 30

            for _ in range(12):

                x, y = keep_inside(x, y, tw, th)
                box = (x, y - th, x + tw, y)

                if not overlaps(box):
                    break

                y += 22 if ci % 2 == 0 else -22

            used_boxes.append((x, y - th, x + tw, y))

            cv2.putText(out, label, (x, y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        font_scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)

            cv2.putText(out, label, (x, y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

            idx += 1

    return out, skeleton_image, sprout_data