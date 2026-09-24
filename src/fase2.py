import heapq
import math
import time

# 1. HEURÍSTICAS GEOGRÁFICAS

def h1_euclidiana(node, goal, G):
    """ $h_1$: Distancia Euclidiana en coordenadas planas proyectadas. """
    x1, y1 = G.nodes[node]['x'], G.nodes[node]['y']
    x2, y2 = G.nodes[goal]['x'], G.nodes[goal]['y']
    dx = (x1 - x2) * 111000 * math.cos(math.radians(y1))
    dy = (y1 - y2) * 111000
    return math.sqrt(dx**2 + dy**2)

def h2_haversine(node, goal, G):
    """ $h_2$: Distancia Haversine sobre superficie esférica (metros). """
    lat1, lon1 = G.nodes[node]['y'], G.nodes[node]['x']
    lat2, lon2 = G.nodes[goal]['y'], G.nodes[goal]['x']
    R = 6371000  # Radio de la Tierra en metros
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def h3_personalizada(node, goal, G):
    """ $h_3$: Haversine ponderada considerando intersecciones (grado del nodo). """
    base_h = h2_haversine(node, goal, G)
    return base_h + (G.degree[node] * 0.5)


# 2. ALGORITMOS DE BÚSQUEDA INFORMADA

def a_star(G, origin, goal, heuristic_func):
    """ Algoritmo A* con f(n) = g(n) + h(n). """
    start_time = time.time()
    frontier = []
    heapq.heappush(frontier, (0, origin))
    came_from = {origin: None}
    g_score = {origin: 0}
    nodes_expanded = 0
    max_frontier_size = 1

    while frontier:
        max_frontier_size = max(max_frontier_size, len(frontier))
        _, current = heapq.heappop(frontier)
        nodes_expanded += 1

        if current == goal:
            break

        for neighbor in G.neighbors(current):
            edge_data = G.get_edge_data(current, neighbor)
            weight = min(d.get('length', 1) for d in edge_data.values()) if isinstance(edge_data, dict) else 1
            tentative_g = g_score[current] + weight

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic_func(neighbor, goal, G)
                heapq.heappush(frontier, (f_score, neighbor))
                came_from[neighbor] = current

    path = []
    curr = goal
    if goal in came_from:
        while curr is not None:
            path.append(curr)
            curr = came_from.get(curr)
        path.reverse()

    exec_time = (time.time() - start_time) * 1000  # ms
    costo_total = g_score.get(goal, float('inf'))
    return {
        'camino': path,
        'costo': costo_total,
        'nodos_expandidos': nodes_expanded,
        'tiempo_ms': exec_time,
        'max_frontera': max_frontier_size
    }


def greedy_best_first(G, origin, goal, heuristic_func):
    """ Greedy Best-First Search guiado únicamente por h(n). """
    start_time = time.time()
    frontier = []
    heapq.heappush(frontier, (heuristic_func(origin, goal, G), origin))
    came_from = {origin: None}
    visited = {origin}
    nodes_expanded = 0
    max_frontier_size = 1

    while frontier:
        max_frontier_size = max(max_frontier_size, len(frontier))
        _, current = heapq.heappop(frontier)
        nodes_expanded += 1

        if current == goal:
            break

        for neighbor in G.neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                came_from[neighbor] = current
                priority = heuristic_func(neighbor, goal, G)
                heapq.heappush(frontier, (priority, neighbor))

    path = []
    curr = goal
    if goal in came_from:
        while curr is not None:
            path.append(curr)
            curr = came_from.get(curr)
        path.reverse()

    costo_total = 0
    for i in range(len(path) - 1):
        edge_data = G.get_edge_data(path[i], path[i+1])
        costo_total += min(d.get('length', 1) for d in edge_data.values()) if isinstance(edge_data, dict) else 1

    exec_time = (time.time() - start_time) * 1000  # ms
    return {
        'camino': path,
        'costo': costo_total,
        'nodos_expandidos': nodes_expanded,
        'tiempo_ms': exec_time,
        'max_frontera': max_frontier_size
    }