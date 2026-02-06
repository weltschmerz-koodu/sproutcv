"""
Graph utility functions for skeleton analysis
"""

import numpy as np
import networkx as nx
import logging
from shapely.geometry import LineString
from typing import List, Tuple

from sproutcv.config import GraphConfig
from sproutcv.exceptions import ProcessingError

logger = logging.getLogger('sproutcv.graph_utils')


def build_graph_from_skeleton(skeleton: np.ndarray) -> nx.Graph:
    """
    Build a NetworkX graph from skeleton image
    
    Args:
        skeleton: Binary skeleton image (255 = skeleton, 0 = background)
    
    Returns:
        nx.Graph: NetworkX Graph with nodes as (y, x) tuples and edge weights as distances
    
    Raises:
        ProcessingError: If skeleton is empty or invalid
    """
    if skeleton.size == 0:
        logger.error("Skeleton image is empty")
        raise ProcessingError("Skeleton image is empty")
    
    # Find skeleton points
    points = np.column_stack(np.where(skeleton > 0))
    
    if len(points) == 0:
        logger.error("No skeleton points found")
        raise ProcessingError("No skeleton points found")
    
    # Create graph
    G = nx.Graph()
    
    # Add nodes
    for y, x in points:
        G.add_node((y, x))
    
    # Add edges to neighbors
    for y, x in points:
        for dy, dx in GraphConfig.NEIGHBORS:
            ny, nx_ = y + dy, x + dx
            
            # Check bounds
            if (0 <= ny < skeleton.shape[0] and 
                0 <= nx_ < skeleton.shape[1] and
                skeleton[ny, nx_] > 0):
                
                # Calculate Euclidean distance
                distance = np.sqrt((y - ny)**2 + (x - nx_)**2)
                G.add_edge((y, x), (ny, nx_), weight=distance)
    
    logger.debug(f"Built graph with {len(G.nodes)} nodes and {len(G.edges)} edges")
    return G


def simplify_path(path: List[Tuple[int, int]], 
                 tolerance: float = None) -> List[Tuple[float, float]]:
    """
    Simplify a path using Douglas-Peucker algorithm
    
    Args:
        path: List of (y, x) coordinate tuples
        tolerance: Simplification tolerance (default from config)
    
    Returns:
        list: Simplified path as list of (y, x) tuples
    """
    if tolerance is None:
        tolerance = GraphConfig.PATH_SIMPLIFICATION_TOLERANCE
    
    if len(path) < 3:
        return path
    
    try:
        line = LineString(path)
        simplified = line.simplify(tolerance, preserve_topology=False)
        result = list(simplified.coords)
        logger.debug(f"Simplified path from {len(path)} to {len(result)} points")
        return result
    except Exception as e:
        logger.warning(f"Path simplification failed: {e}, returning original path")
        return path


def reconnect_path(G: nx.Graph, 
                  path: List[Tuple[float, float]]) -> float:
    """
    Reconnect simplified path and calculate total length
    
    Args:
        G: NetworkX graph
        path: List of (y, x) coordinate tuples
    
    Returns:
        float: Total path length in pixels
    
    Raises:
        ProcessingError: If path is empty or has only one point
    """
    if len(path) < 2:
        logger.error("Path must have at least 2 points")
        raise ProcessingError("Path must have at least 2 points")
    
    total_length = 0.0
    
    for i in range(len(path) - 1):
        # Convert to integer coordinates
        p1 = tuple(map(int, path[i]))
        p2 = tuple(map(int, path[i + 1]))
        
        # Check if edge exists
        if p2 not in G[p1]:
            # Add missing edge with Euclidean distance
            distance = np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
            G.add_edge(p1, p2, weight=distance)
        
        # Add edge weight to total
        total_length += G[p1][p2]['weight']
    
    logger.debug(f"Path length: {total_length:.2f} pixels")
    return total_length


def find_farthest_nodes(G: nx.Graph) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Find the two farthest nodes in the graph (approximate endpoints)
    
    Uses two-pass algorithm:
    1. Find farthest node from arbitrary start
    2. Find farthest node from that node
    
    Args:
        G: NetworkX graph
    
    Returns:
        tuple: (node1, node2) representing endpoints as (y, x) tuples
    
    Raises:
        ProcessingError: If graph is empty or has no nodes
    """
    if len(G.nodes) == 0:
        logger.error("Graph has no nodes")
        raise ProcessingError("Graph has no nodes")
    
    if len(G.nodes) == 1:
        # Single node - return same node twice
        node = list(G.nodes)[0]
        logger.debug("Graph has only one node")
        return node, node
    
    # First pass: find farthest from arbitrary start
    start_node = list(G.nodes)[0]
    
    try:
        distances = nx.single_source_dijkstra_path_length(G, start_node)
        node1 = max(distances, key=distances.get)
        
        # Second pass: find farthest from node1
        distances = nx.single_source_dijkstra_path_length(G, node1)
        node2 = max(distances, key=distances.get)
        
        logger.debug(f"Found endpoints: {node1} and {node2}")
        return node1, node2
    
    except nx.NetworkXError as e:
        logger.error(f"Graph analysis failed: {str(e)}")
        raise ProcessingError(f"Graph analysis failed: {str(e)}")