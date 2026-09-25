import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

import folium

from src.utils import cargar_grafo, gen_nodo_entrega
from src.fase1 import accesible
from src.BFS import bfs
from src.DFS import dfs
from src.UCS import ucs

# ---------------------- Configuración ----------------------
RUTA_GRAFO = "data/cdmx_norte_centro.graphml"
RANGO_DESTINOS_A_MOSTRAR = (5, 15)  # mínimo y máximo de pedidos a comparar (aleatorio)
SALIDA_HTML = "visualizacion_rutas_ciegas.html"

COLORES_ALGORITMO = {
    "BFS": "#00BFFF",   # celeste
    "DFS": "#FF8C00",   # naranja
    "UCS": "#39FF14",   # verde neón
    "A* (Euclidiana)": "#FF33F6",      # rosa neón
    "A* (Haversine)": "#F3FF33",       # amarillo neón
    "A* (Personalizada)": "#B833FF",   # morado
    "Greedy Best-First": "#FF3333",    # rojo
    
}

# Diccionario nombre -> función; así el script no depende de cómo
# cada módulo llama internamente a la clave "algoritmo"/"Algoritmo"
# (BFS.py usa "Algoritmo" con mayúscula, DFS.py y UCS.py usan minúscula;
# aquí no importa porque identificamos el algoritmo por esta clave, no
# por el contenido del resultado).
ALGORITMOS = {
    "BFS": bfs,
    "DFS": dfs,
    "UCS": ucs,
    
}


def nodo_a_latlon(G, nodo):
    """osmnx guarda x=longitud, y=latitud; folium espera [lat, lon]."""
    return (G.nodes[nodo]["y"], G.nodes[nodo]["x"])


def construir_mapa(G, almacen, destinos_info):
    lat_c, lon_c = nodo_a_latlon(G, almacen)
    # Basemap claro de Esri/ArcGIS (fondo blanco, calles en gris oscuro),
    # gratuito y sin API key. Es el equivalente claro del "Dark Gray Canvas".
    mapa = folium.Map(
        location=[lat_c, lon_c],
        zoom_start=13,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
              "Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ",
    )

    # Grupo aparte solo para los marcadores (almacén + pedidos), siempre
    # visible, para que no desaparezcan al ocultar una búsqueda puntual.
    grupo_marcadores = folium.FeatureGroup(name="Marcadores", show=True)
    folium.Marker(
        location=[lat_c, lon_c],
        tooltip="Almacén Central",
        icon=folium.Icon(color="red", icon="warehouse", prefix="fa"),
    ).add_to(grupo_marcadores)

    for destino in destinos_info:
        lat_d, lon_d = nodo_a_latlon(G, destino)
        folium.Marker(
            location=[lat_d, lon_d],
            tooltip=f"Pedido {destino}",
            icon=folium.Icon(color="gray", icon="flag", prefix="fa"),
        ).add_to(grupo_marcadores)
    grupo_marcadores.add_to(mapa)

    # Una capa por ALGORITMO (no por destino): agrupa ahí las rutas de
    # todos los destinos, así una sola casilla prende/apaga, por ejemplo,
    # todas las rutas de BFS de un tirón.# Extraer dinámicamente los algoritmos que vengan en el diccionario
    nombres_usados = set()
    for resultados in destinos_info.values():
        nombres_usados.update(resultados.keys())
        
    grupos_algoritmo = {
        nombre: folium.FeatureGroup(name=nombre, show=True)
        for nombre in nombres_usados
    }
    

    for destino, resultados in destinos_info.items():
        for nombre_algo, res in resultados.items():
            if not res["encontrado"]:
                continue

            coords = [nodo_a_latlon(G, n) for n in res["camino"]]

            popup_html = (
                f"<b>{nombre_algo}</b><br>"
                f"Destino: {destino}<br>"
                f"Distancia: {res['metros']:.1f} m<br>"
                f"Arcos: {res['arcos']}<br>"
                f"Nodos expandidos: {res['expandidos']}<br>"
                f"Tiempo: {res['tiempo_ms']:.2f} ms"
            )

            folium.PolyLine(
                locations=coords,
                color=COLORES_ALGORITMO.get(nombre_algo, "#FFFFFF"),
                weight=4,
                opacity=0.85,
                tooltip=f"{nombre_algo} → {destino} ({res['metros']:.0f} m)",
                popup=folium.Popup(popup_html, max_width=250),
            ).add_to(grupos_algoritmo[nombre_algo])

    for grupo in grupos_algoritmo.values():
        grupo.add_to(mapa)

    folium.LayerControl(collapsed=False).add_to(mapa)
    return mapa


def main():
    print("Cargando grafo...")
    G = cargar_grafo(RUTA_GRAFO)

    print("Generando almacén y pedidos...")
    almacen, candidatos = gen_nodo_entrega(G, rango_entregas=(10, 15))

    print("Filtrando destinos alcanzables...")
    alcanzables, _, _ = accesible(G, almacen, candidatos)

    # Cantidad aleatoria dentro del rango configurado, sin pasarnos
    # de los que realmente son alcanzables.
    n_a_mostrar = random.randint(*RANGO_DESTINOS_A_MOSTRAR)
    n_a_mostrar = min(n_a_mostrar, len(alcanzables))
    destinos = random.sample(alcanzables, n_a_mostrar)

    if not destinos:
        print("No se encontraron destinos alcanzables, aborta.")
        return

    print(f"Almacén: {almacen}")
    print(f"Destinos a comparar: {destinos}\n")

    destinos_info = {}
    for destino in destinos:
        print(f"Calculando rutas hacia {destino}...")
        resultados = {}
        for nombre_algo, funcion_algo in ALGORITMOS.items():
            res = funcion_algo(G, almacen, destino)
            resultados[nombre_algo] = res
            if res["encontrado"]:
                print(f"  {nombre_algo}: {res['metros']:.1f} m, "f"{res['arcos']} arcos, {res['expandidos']} expandidos, "f"{res['tiempo_ms']:.2f} ms")
            else:
                print(f"  {nombre_algo}: sin ruta")
        destinos_info[destino] = resultados

    print("\nGenerando mapa interactivo...")
    mapa = construir_mapa(G, almacen, destinos_info)
    mapa.save(SALIDA_HTML)
    print(f"Mapa guardado como '{SALIDA_HTML}'. Ábrelo en tu navegador.")


if __name__ == "__main__":
    main()