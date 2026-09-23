import heapq    #Ccolas de prioridad
from pathlib import Path
import sys
import time

# Agrega la raíz para resolver importaciones
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Funciones para cargar datos y generar paradas
from src.utils import cargar_grafo, gen_nodo_entrega


def ucs(G, origen, destino, on_expand=None):
    t_inicio = time.perf_counter()
    contador = 0    # Contador para evitar comparaciones directas entre nodos en el heap
    frontera = [(0.0, contador, origen)]    # Frontera estructurada como heap: tupla (costo_acumulado_metros, id_unico, nodo
    padres = {origen: None}         # Mapeo de predecesores óptimos
    costos = {origen: 0.0}          # Registro del menor costo en metros acumulado para llegar a cada nodo
    cerrados = set()                # Conjunto de nodos evaluados de forma definitiva (cerrados)


    nodos_expandidos = 0
    max_frontera = 1         # Registro del pico máximo de nodos en el heap (requisito de la rúbrica)
    encontrado = False       # Bandera booleana de éxito

    
    while frontera:             # Bucle que extrae elementos del heap mientras haya opciones
        max_frontera = max(max_frontera, len(frontera))
        
        costo_actual, _, actual = heapq.heappop(frontera)   # Extrae el nodo con el menor costo g(n) acumulado

        if actual in cerrados:      # Si el nodo ya fue cerrado por una vía anterior más corta, se descarta
            continue

        cerrados.add(actual)        # Se agrega al conjunto de cerrados
        nodos_expandidos += 1

        if actual == destino:       # Prueba de meta: al extraerse del heap, se garantiza que es la distancia mínima global
            encontrado = True
            break

        for vecino in G.successors(actual):     # Prueba de meta: al extraerse del heap, se garantiza que es la distancia mínima global
            datos_arista = G.get_edge_data(actual, vecino)      # Obtiene el diccionario con los atributos de la calle conectora
            peso = min(attrs.get("length", 0.0) for attrs in datos_arista.values()) if datos_arista else 0.0
            nuevo_costo = costo_actual + peso

            if vecino not in costos or nuevo_costo < costos[vecino]:        # Si no se conocía costo hacia el vecino o se descubrió un atajo más corto
                costos[vecino] = nuevo_costo        # Actualiza el costo mínimo
                padres[vecino] = actual
                contador += 1
                heapq.heappush(frontera, (nuevo_costo, contador, vecino))       # Inserta en el montículo con su nuevo costo acumulado

        if on_expand is not None:
            on_expand(nodos_expandidos, cerrados, [n for _, _, n in frontera])

    # Calcula la duración total en milisegundos
    t_total_ms = (time.perf_counter() - t_inicio) * 1000

    # Reconstrucción del camino óptimo en metros
    camino = []
    if encontrado:
        curr = destino
        while curr is not None:
            camino.append(curr)
            curr = padres.get(curr)
        # Se invierte la ruta para que empiece en el origen
        camino.reverse()

    # Retorna las métricas registradas
    return {
        "algoritmo": "UCS",
        "encontrado": encontrado,
        "camino": camino,
        "arcos": max(0, len(camino) - 1),
        "metros": costos.get(destino, 0.0) if encontrado else 0.0,
        "expandidos": nodos_expandidos,
        "max_frontera": max_frontera,
        "tiempo_ms": t_total_ms
    }


"""""
if __name__ == "__main__":
    G = cargar_grafo("data/cdmx_norte_centro.graphml")
    
    origen, entregas = gen_nodo_entrega(G, rango_entregas=(5, 5))

    print(f"\n--- EXPERIMENTO UCS (Búsqueda de Costo Uniforme) ---")
    print(f"Almacén origen: {origen}\n")
    print(f"Destinos evaluados: {entregas}\n")

    for i, destino in enumerate(entregas, start=1):
        res = ucs(G, origen, destino)
        print(f"Punto {i} (Destino: {destino}):")
        if res["encontrado"]:
            print(f"  - Longitud en metros: {res['metros']:.2f} m")
            print(f"  - Número de arcos (saltos): {res['arcos']}")
            print(f"  - Nodos expandidos: {res['expandidos']}")
            print(f"  - Tamaño máx. de frontera: {res['max_frontera']}")
            print(f"  - Tiempo de ejecución: {res['tiempo_ms']:.2f} ms")
        else:
            print("  - Destino inalcanzable.")
        print()
        
"""