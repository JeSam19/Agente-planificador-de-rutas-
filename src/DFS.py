from pathlib import Path 
import sys
import time

sys.path.append(str(Path(__file__).resolve().parent.parent))    #importamos librerias y scripts desde la raíz

from src.fase1 import accesible, costo_camino
from src.utils import cargar_grafo, gen_nodo_entrega

def dfs(G, origen, destino, on_expand=None):
    t_inicio = time.perf_counter()
    
    if origen == destino:
        return {
            "algoritmo": "DFS",
            "encontrado": True,
            "camino": [origen],
            "arcos": 0,
            "metros": 0.0,
            "expandidos": 1,
            "max_frontera": 1,
            "tiempo_ms": (time.perf_counter() - t_inicio) * 1000
        }

    # Pila LIFO almacena tuplas: (nodo_actual, nodo_padre)
    pila = [(origen, None)]
    visitados = set()
    padres = {}

    n_expandidos = 0
    max_frontera = 1
    encontrado = False

    while pila:
        # Registrar el tamaño máximo que alcanzó la pila durante la búsqueda
        max_frontera = max(max_frontera, len(pila))
        actual, padre = pila.pop()

        if actual in visitados:
            continue

        visitados.add(actual)
        padres[actual] = padre
        n_expandidos += 1

        if actual == destino:
            encontrado = True
            break

        # Explorar sucesores
        for vecino in G.successors(actual):
            if vecino not in visitados:
                pila.append((vecino, actual))

        if on_expand is not None:
            on_expand(n_expandidos, visitados, [n for n, _ in pila])

    # El cálculo de tiempo, reconstrucción y return deben ir FUERA del bucle while
    t_total_ms = (time.perf_counter() - t_inicio) * 1000

    camino = []
    if encontrado:
        curr = destino
        while curr is not None:
            camino.append(curr)
            curr = padres.get(curr)
        camino.reverse()

    return {
        "algoritmo": "DFS",
        "encontrado": encontrado,
        "camino": camino,
        "arcos": max(0, len(camino) - 1),
        "metros": costo_camino(G, camino) if encontrado else 0.0,
        "expandidos": n_expandidos,
        "max_frontera": max_frontera,
        "tiempo_ms": t_total_ms
    }

"""""
if __name__ == "__main__":
    print("Cargando grafo...")
    G = cargar_grafo("data/cdmx_norte_centro.graphml")

    print("Seleccionando nodos...")
    origen, candidatos = gen_nodo_entrega(G, rango_entregas=(15, 20))

    # Asegurar que se prueben destinos con camino existente
    alcanzables, _, _ = accesible(G, origen, candidatos)
    entregas = alcanzables[:5]

    print(f"\n--- EXPERIMENTO DFS (Búsqueda en Profundidad Iterativa) ---")
    print(f"Almacén origen: {origen}\n")
    print(f"Destinos evaluados: {entregas}\n")

    for i, destino in enumerate(entregas, start=1):
        print(f"Calculando ruta hacia Punto {i} (Destino: {destino})...", flush=True)
        res = dfs(G, origen, destino)
        if res["encontrado"]:
            print(f"  - Longitud en metros: {res['metros']:.2f} m")
            print(f"  - Número de arcos (saltos): {res['arcos']}")
            print(f"  - Nodos expandidos: {res['expandidos']}")
            print(f"  - Tamaño máx. de frontera: {res['max_frontera']}")
            print(f"  - Tiempo de ejecución: {res['tiempo_ms']:.2f} ms\n")
        else:
            print("  - Destino inalcanzable.\n")

"""