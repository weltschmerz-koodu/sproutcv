import cv2
import numpy as np
import networkx as nx
from skimage.morphology import skeletonize
from shapely.geometry import LineString

# ---------------- Graph Utilities ---------------- #

def build_graph_from_skeleton(skeleton):

    G = nx.Graph()
    points = np.column_stack(np.where(skeleton > 0))

    for y, x in points:
        G.add_node((y, x))

    for y, x in points:
        for dy, dx in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:

            ny, nx_ = y + dy, x + dx

            if (
                0 <= ny < skeleton.shape[0]
                and 0 <= nx_ < skeleton.shape[1]
                and skeleton[ny, nx_] > 0
            ):
                d = ((y - ny)**2 + (x - nx_)**2) ** 0.5
                G.add_edge((y, x), (ny, nx_), weight=d)

    return G


def simplify_path(path, tolerance=2.0):

    if len(path) < 3:
        return path

    return list(LineString(path).simplify(
        tolerance,  
        preserve_topology=False
    ).coords)


def reconnect_path(G, path):

    total = 0

    for i in range(len(path) - 1):

        p1 = tuple(map(int, path[i]))
        p2 = tuple(map(int, path[i + 1]))

        if p2 not in G[p1]:
            d = ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2) ** 0.5
            G.add_edge(p1, p2, weight=d)

        total += G[p1][p2]["weight"]

    return total


def find_farthest_nodes(G):

    start = list(G.nodes)[0]

    d = nx.single_source_dijkstra_path_length(G, start)
    n1 = max(d, key=d.get)

    d = nx.single_source_dijkstra_path_length(G, n1)
    n2 = max(d, key=d.get)

    return n1, n2