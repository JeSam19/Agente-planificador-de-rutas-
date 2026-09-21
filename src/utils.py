import random
import osmnx as ox

# Coordenadas del almacén
coord_almacen = {"lat": 19.3606, "lon": -99.1645}


def cargar_grafo(ruta="data/cdmx_norte_centro.graphml"):
    #Carga el grafo desde el archivo GraphML.
    return ox.load_graphml(ruta)


def gen_nodo_almacen(G):
    #Retorna el nodo del grafo más cercano a la coordenada del almacén.
    return ox.distance.nearest_nodes(
        G, X=coord_almacen["lon"], Y=coord_almacen["lat"]
    )


def gen_nodo_entrega(G, n_entregas=None, rango_entregas=(5, 15), seed=None):
    #Genera entregas dinámicas seleccionando esquinas aleatorias del grafo.
    if seed is not None:
        random.seed(seed)

    nodo_almacen = gen_nodo_almacen(G)

    if n_entregas is None:
        n_entregas = random.randint(rango_entregas[0], rango_entregas[1])

    # Candidatos: todos los nodos excepto el almacén
    candidatos = [nodo for nodo in G.nodes if nodo != nodo_almacen]

    entregas_seleccionadas = random.sample(
        candidatos, min(n_entregas, len(candidatos))
    )

    return nodo_almacen, entregas_seleccionadas


if __name__ == "__main__":
    print("Probando funciones de utils.py...")
    ruta_grafo = "data/cdmx_norte_centro.graphml"

    try:
        print(f"Cargando grafo desde '{ruta_grafo}'...")
        G = cargar_grafo(ruta_grafo)

        deposito, entregas = gen_nodo_entrega(G, rango_entregas=(5, 8))
        print(f"\nNodo del almacén: {deposito}")
        print(f"Cantidad de entregas generadas: {len(entregas)}")
        print(f"Nodos de entrega: {entregas}")
        print("\n¡Ejecución exitosa!")

    except FileNotFoundError as e:
        print(f"Error de archivo no encontrado: {e}")