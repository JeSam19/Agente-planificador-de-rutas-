from collections import deque   # Colas de doble extremo FIFO
from pathlib import Path        # Rutas relativas y absolutas
import sys
import time

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.fase1 import costo_camino
from src.utils import cargar_grafo, gen_nodo_entrega

def bfs(G, origen, destino, on_expand=None):
    t_inicio = time.perf_counter()       # Registrar marca de tiempo inicial
    
    # Caso base trivial: si el origen es el mismo destino
    if origen == destino:
        return {
            "Algoritmo": "BFS",
            "encontrado": True,
            "camino": [origen],
            "arcos": 0,
            "metros": 0.0,
            "expandidos": 1,
            "max_frontera": 1,
            "tiempo_ms": (time.perf_counter() - t_inicio) * 1000
        }

    visitados = set()           # Nodos visitados para evitar ciclos
    cola = deque([origen])      # Cola inicializada con el nodo del almacén
    visitados.add(origen)       
    padres = {origen: None}     # Mapeo hijo -> padre predecesor
    
    n_expandidos = 0            # Contador de nodos extraídos y procesados
    max_frontera = 1            # Registro del pico máximo de memoria en la cola
    encontrado = False          # Bandera de éxito
    
    while cola:
        # Monitorear el tamaño máximo alcanzado por la cola
        max_frontera = max(max_frontera, len(cola))
        
        actual = cola.popleft()     # Extrae el nodo más antiguo (disciplina FIFO)
        n_expandidos += 1
        
        if actual == destino:       # Comprobación de meta al extraer
            encontrado = True
            break
        
        for vecino in G.successors(actual):
            if vecino not in visitados:
                visitados.add(vecino)
                padres[vecino] = actual     # Se registra su predecesor
                cola.append(vecino)         # Se encola para explorar después

        if on_expand is not None:
            on_expand(n_expandidos, visitados, list(cola))
                
    t_total_ms = (time.perf_counter() - t_inicio) * 1000
    
    camino = []     # Lista para reconstruir la ruta
    
    if encontrado:
        curr = destino
        # Bucle corregido: ahora sí avanza hacia el padre
        while curr is not None:
            camino.append(curr)
            curr = padres.get(curr)   # avanzar al padre
        
        camino.reverse()             # Invierte la lista
        
    return {
        "Algoritmo": "BFS",
        "encontrado": encontrado,
        "camino": camino,
        "arcos": max(0, len(camino) - 1),
        "metros": costo_camino(G, camino) if encontrado else 0.0,
        "expandidos": n_expandidos,
        "max_frontera": max_frontera,
        "tiempo_ms": t_total_ms
    }

"""""
# Ejecución de prueba sobre 5 destinos garantizados
if __name__ == "__main__":
    from src.fase1 import accesible

    print("Cargando grafo...")
    G = cargar_grafo("data/cdmx_norte_centro.graphml")

    print("Seleccionando nodos...")
    origen, candidatos = gen_nodo_entrega(G, rango_entregas=(15, 20))

    # Filtramos para usar únicamente destinos que sí tengan camino
    alcanzables, _, _ = accesible(G, origen, candidatos)
    entregas = alcanzables[:5]

    print("\n--- EXPERIMENTO BFS (Búsqueda en Amplitud) ---")
    print(f"Almacén origen: {origen}")
    print(f"Destinos evaluados: {entregas}\n")

    # Itera sobre cada entrega evaluando el algoritmo con aviso en consola
    for i, destino in enumerate(entregas, start=1):
        print(f"Calculando ruta hacia Punto {i} (Destino: {destino})...", flush=True)
        res = bfs(G, origen, destino)
        if res["encontrado"]:
            print(f"  - Longitud en metros: {res['metros']:.2f} m")
            print(f"  - Número de arcos (saltos): {res['arcos']}")
            print(f"  - Nodos expandidos: {res['expandidos']}")
            print(f"  - Máx. en frontera: {res['max_frontera']}")
            print(f"  - Tiempo de ejecución: {res['tiempo_ms']:.2f} ms\n")
        else:
            print("  - Destino inalcanzable.\n")
"""