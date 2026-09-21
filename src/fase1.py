import sys
from pathlib import Path

# Añade la raíz del proyecto a la ruta de búsqueda de módulos de Python
sys.path.append(str(Path(__file__).resolve().parent.parent))

from collections import deque       # Estructura cola de doble extremo
import time                         # Tiempo de cómputo al encontrar la ruta
import networkx as nx
import osmnx as ox           
from src.utils import cargar_grafo, gen_nodo_entrega


# Se calcula la distancia en metros de una ruta
def costo_camino(G, camino):
    # camino es la lista con IDs de los nodos
    if not camino or len(camino) < 2:
        return 0.0
    
    # Variable para sumar la longitud de cada calle que compone la ruta
    distancia_total = 0.0
    # Recorremos la ruta en tuplas "u, v"
    for u, v in zip(camino[:-1], camino[1:]):
        # Pedimos los datos de las aristas que van del nodo u al v
        datos_arista = G.get_edge_data(u, v)
        if datos_arista:
            min_longitud = min(
                # Tomamos la arista con menor longitud si un nodo tiene varias aristas
                attrs.get("length", 0.0) for attrs in datos_arista.values()
            )
            # Sumamos la longitud obtenida del tramo actual 
            distancia_total += min_longitud
            
    return distancia_total


# Verificación de accesibilidad y cálculo de distancias por BFS
def accesible(G, origen, destinos):
    visitados = set()
    cola = deque([origen])
    visitados.add(origen)
    padres = {origen: None}

    while cola:
        actual = cola.popleft()
        for vecino in G.successors(actual):
            if vecino not in visitados:
                visitados.add(vecino)
                padres[vecino] = actual
                cola.append(vecino)

    alcanzables = [d for d in destinos if d in visitados]
    no_alcanzables = [d for d in destinos if d not in visitados]

    costos_entregas = {}
    for d in alcanzables:
        camino = []
        actual = d
        
        # Reconstruir camino hacia atrás hasta llegar a la raíz (None)
        while actual is not None:
            camino.append(actual)
            actual = padres.get(actual)
            
        camino.reverse()

        # Validación de ruta conectada desde el origen
        if camino and camino[0] == origen:
            costos_entregas[d] = {
                "distancia_metros": costo_camino(G, camino),
                "num_arcos": max(0, len(camino) - 1),
                "camino": camino,
            }

    return alcanzables, no_alcanzables, costos_entregas


if __name__ == "__main__":
    print("Cargando grafo para ver accesibilidad...")
    G = cargar_grafo()
    
    origen, destinos = gen_nodo_entrega(G, rango_entregas=(5, 8))
    alcanzables, no_alcanzables, costos = accesible(G, origen, destinos)
    
    print(f"\nID Almacen: {origen}")
    print(f"Total de pedidos: {len(destinos)}")
    print(f"Pedidos alcanzables ({len(alcanzables)}): {alcanzables}")
    print(f"Pedidos no alcanzables ({len(no_alcanzables)}): {no_alcanzables}\n")
    
    print("--- Costo hacia cada pedido alcanzable ---")
    for d in alcanzables:
        if d in costos:
            metros = costos[d]["distancia_metros"]
            arcos = costos[d]["num_arcos"]
            km = metros / 1000.0
            print(f"Entrega {d}: {metros:.2f} m ({km:.2f} km) en {arcos} intersecciones")
        else:
            print(f"Entrega {d}: alcanzable, pero no se pudo reconstruir la ruta.")