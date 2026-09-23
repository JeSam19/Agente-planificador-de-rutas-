import sys
from pathlib import Path

# Añade la raíz del proyecto para importar módulos de src
sys.path.append(str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
import osmnx as ox
import pandas as pd
from src.fase1 import accesible
from src.utils import cargar_grafo, gen_nodo_entrega

# 1. Cargar grafo y generar pedidos aleatorios
print("Cargando grafo...")
G = cargar_grafo("data/cdmx_norte_centro.graphml")
almacen, entregas = gen_nodo_entrega(G, rango_entregas=(5, 8))

# 2. Conexión con fase1.py para accesibilidad y costos en metros
print("Calculando accesibilidad y distancias con fase1.py...")
alcanzables, no_alcanzables, costos = accesible(G, almacen, entregas)

print(f"Almacén: {almacen}")
print(f"Alcanzables ({len(alcanzables)}): {alcanzables}")
print(f"No alcanzables ({len(no_alcanzables)}): {no_alcanzables}")

# 3. Descargar límites de las alcaldías
print("Obteniendo límites de alcaldías...")
alcaldias = [
    {"county": "Cuauhtémoc", "state": "Ciudad de México", "country": "Mexico"},
    {"county": "Benito Juárez", "state": "Ciudad de México", "country": "Mexico"},
    {"county": "Coyoacán", "state": "Ciudad de México", "country": "Mexico"},
]
gdf_limites = ox.geocode_to_gdf(alcaldias)

# MAPA en png
print("\nGenerando imagen del grafo...")
fig_mapa, ax_mapa = ox.plot_graph(
    G,
    node_size=0,
    edge_linewidth=0.3,
    edge_color="#333333",
    bgcolor="#111111",
    show=False,
    close=False,
    figsize=(8, 12),
)

# Trazar fronteras de alcaldías
colores_fronteras = ["#00FFFF", "#FF00FF", "#FFFF00"]
for i in range(len(gdf_limites)):
    alcaldia = gdf_limites.iloc[[i]].copy()
    if i == 0:
        geometria = alcaldia.geometry.iloc[0]
        if geometria.geom_type == "MultiPolygon":
            partes = list(geometria.geoms)
            parte_principal = max(partes, key=lambda p: p.area)
            alcaldia.geometry = [parte_principal]

    alcaldia.boundary.plot(
        ax=ax_mapa,
        color=colores_fronteras[i],
        linewidth=1.8,
        linestyle="--",
        zorder=3,
    )

# Coordenadas del almacén
x_alm = G.nodes[almacen]["x"]
y_alm = G.nodes[almacen]["y"]

# Marcador Almacén
ax_mapa.scatter(
    x_alm,
    y_alm,
    c="#FF2222",
    s=180,
    marker="*",
    edgecolors="white",
    linewidths=1.2,
    zorder=10,
    label="Almacén Central",
)

# Marcadores Entregas Alcanzables
if alcanzables:
    ax_mapa.scatter(
        [G.nodes[d]["x"] for d in alcanzables],
        [G.nodes[d]["y"] for d in alcanzables],
        c="#00FF66",
        s=60,
        marker="o",
        edgecolors="black",
        linewidths=0.8,
        zorder=9,
        label=f"Alcanzables ({len(alcanzables)})",
    )

# Marcadores Entregas No Alcanzables
if no_alcanzables:
    ax_mapa.scatter(
        [G.nodes[d]["x"] for d in no_alcanzables],
        [G.nodes[d]["y"] for d in no_alcanzables],
        c="#FFAA00",
        s=60,
        marker="X",
        edgecolors="black",
        linewidths=0.8,
        zorder=9,
        label=f"No alcanzables ({len(no_alcanzables)})",
    )

ax_mapa.legend(
    loc="upper left",
    facecolor="#222222",
    edgecolor="#555555",
    labelcolor="white",
    fontsize=9,
)

salida_mapa = "mapa.png"
fig_mapa.savefig(
    salida_mapa,
    dpi=300,
    bbox_inches="tight",
    facecolor=fig_mapa.get_facecolor(),
)
plt.close(fig_mapa)
print(f"Mapa guardado como: '{salida_mapa}'")

# Tabla de datos
print("Generando imagen de la tabla de costos...")

filas_tabla = []
for destino in entregas:
    es_alcanzable = destino in alcanzables
    if es_alcanzable and destino in costos:
        m = costos[destino]["distancia_metros"]
        km = m / 1000.0
        tramos = costos[destino]["num_arcos"]
        filas_tabla.append(
            [str(destino), "Alcanzable", f"{m:,.1f} m", f"{km:.2f} km", str(tramos)]
        )
    else:
        filas_tabla.append([str(destino), "No accesible", "N/A", "N/A", "N/A"])

columnas = ["ID Pedido", "Estado", "Metros", "Kilómetros", "Arcos"]

# Figura para la tabla
fig_tabla, ax_tabla = plt.subplots(figsize=(8, 4), facecolor="#111111")
ax_tabla.axis("off")
ax_tabla.set_title(
    "Reporte de Costos por Entrega (Fase 1)",
    color="white",
    fontsize=12,
    pad=15,
    fontweight="bold",
)

tabla = ax_tabla.table(
    cellText=filas_tabla,
    colLabels=columnas,
    cellLoc="center",
    loc="center",
)

tabla.auto_set_font_size(False)
tabla.set_fontsize(10)
tabla.scale(1.1, 2.0)

# Estilo visual de las celdas
for (fila, col), celda in tabla.get_celld().items():
    celda.set_edgecolor("#444444")
    if fila == 0:
        celda.set_text_props(weight="bold", color="white")
        celda.set_facecolor("#2b2b2b")
    else:
        celda.set_facecolor("#1a1a1a")
        texto_estado = filas_tabla[fila - 1][1]
        if col == 1:
            celda.set_text_props(
            color="#00FF66" if texto_estado == "Alcanzable" else "#FFAA00"
        )
        else:
            celda.set_text_props(color="#E0E0E0")

salida_tabla = "tabla_costos_entregas.png"
fig_tabla.savefig(
    salida_tabla,
    dpi=300,
    bbox_inches="tight",
    facecolor=fig_tabla.get_facecolor(),
)
plt.close(fig_tabla)
print(f"Tabla guardada como: '{salida_tabla}'")

# Guardar CSV complementario
df_costos = pd.DataFrame(filas_tabla, columns=columnas)
df_costos.to_csv("reporte_costos_entregas.csv", index=False)
print("Archivo 'reporte_costos_entregas.csv' actualizado.")