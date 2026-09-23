import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
import osmnx as ox

from src.fase1 import accesible
from src.utils import cargar_grafo, gen_nodo_entrega
from src.BFS import bfs
from src.DFS import dfs
from src.UCS import ucs

RUTA_GRAFO = "data/cdmx_norte_centro.graphml"
CARPETA_SALIDA = Path("fronteras")
N_SNAPSHOTS = 3

COLOR_VISITADOS = "#3388FF"
COLOR_FRONTERA = "#FF3333"
COLOR_ALMACEN = "#FFFFFF"
COLOR_DESTINO = "#FFD700"

ALGORITMOS = {
    "BFS": bfs,
    "DFS": dfs,
    "UCS": ucs,
}


def _checkpoints(total, n):
    if total <= 1:
        return [1] * n
    crudos = (round(total * (i + 1) / (n + 1)) for i in range(n))
    return sorted({min(max(1, c), total - 1) for c in crudos})


def _capturar_snapshots(func_algoritmo, G, almacen, destino, checkpoints):
    
    checkpoints = list(checkpoints)
    snapshots = []
    idx = {"i": 0}  # mutable para poder modificarlo dentro del closure

    def on_expand(n_expandidos, visitados_o_cerrados, frontera_ids):
        if idx["i"] < len(checkpoints) and n_expandidos == checkpoints[idx["i"]]:
            snapshots.append((n_expandidos, set(visitados_o_cerrados), list(frontera_ids)))
            idx["i"] += 1

    func_algoritmo(G, almacen, destino, on_expand=on_expand)
    return snapshots


def graficar_snapshots(G, algoritmo, snapshots, almacen, destino, total_expandidos, archivo_salida):
    if not snapshots:
        print(f"  {algoritmo}: no se generaron snapshots (búsqueda muy corta), se omite imagen.")
        return

    fig, axes = plt.subplots(1, len(snapshots), figsize=(6 * len(snapshots), 8))
    if len(snapshots) == 1:
        axes = [axes]

    for ax, (paso, visitados, frontera) in zip(axes, snapshots):
        ox.plot_graph(
            G, ax=ax, node_size=0, edge_linewidth=0.3, edge_color="#333333",
            bgcolor="#111111", show=False, close=False,
        )
        if visitados:
            ax.scatter(
                [G.nodes[n]["x"] for n in visitados],
                [G.nodes[n]["y"] for n in visitados],
                c=COLOR_VISITADOS, s=8, zorder=5, label=f"Visitados ({len(visitados)})",
            )
        if frontera:
            ax.scatter(
                [G.nodes[n]["x"] for n in frontera],
                [G.nodes[n]["y"] for n in frontera],
                c=COLOR_FRONTERA, s=14, zorder=6, label=f"Frontera ({len(frontera)})",
            )
        ax.scatter(
            G.nodes[almacen]["x"], G.nodes[almacen]["y"],
            c=COLOR_ALMACEN, s=120, marker="*", zorder=10,
            edgecolors="black", linewidths=0.6, label="Almacén",
        )
        ax.scatter(
            G.nodes[destino]["x"], G.nodes[destino]["y"],
            c=COLOR_DESTINO, s=90, marker="X", zorder=10,
            edgecolors="black", linewidths=0.6, label="Destino",
        )
        pct = round(100 * paso / total_expandidos)
        ax.set_title(f"{algoritmo} — {pct}% ({paso}/{total_expandidos} nodos expandidos)",color="white", fontsize=11)
        ax.legend(loc="upper left", facecolor="#222222", edgecolor="#555555", labelcolor="white", fontsize=7)

    fig.patch.set_facecolor("#111111")
    fig.tight_layout()
    fig.savefig(archivo_salida, dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  Guardado: {archivo_salida}")


def main():
    print("Cargando grafo...")
    G = cargar_grafo(RUTA_GRAFO)

    print("Seleccionando almacén y un destino de referencia...")
    almacen, candidatos = gen_nodo_entrega(G, rango_entregas=(10, 15))
    alcanzables, _, _ = accesible(G, almacen, candidatos)

    if not alcanzables:
        print("No se encontraron destinos alcanzables, aborta.")
        return

    destino = alcanzables[0]
    print(f"Almacén: {almacen} | Destino de referencia: {destino}\n")

    CARPETA_SALIDA.mkdir(exist_ok=True)

    for nombre, func_algoritmo in ALGORITMOS.items():
        print(f"Ejecutando {nombre}...")
        # Pasada 1: la función original, sin callback, solo para saber el total.
        res = func_algoritmo(G, almacen, destino)

        if not res["encontrado"]:
            print(f"  {nombre}: destino inalcanzable, se omite.\n")
            continue

        checkpoints = _checkpoints(res["expandidos"], N_SNAPSHOTS)

        # Pasada 2: la misma función original, ahora con callback,
        # para capturar el estado interno en los checkpoints.
        snapshots = _capturar_snapshots(func_algoritmo, G, almacen, destino, checkpoints)

        archivo = CARPETA_SALIDA / f"frontera_{nombre.lower()}.png"
        graficar_snapshots(G, nombre, snapshots, almacen, destino, res["expandidos"], archivo)
        print()

    print(f"Listo. Revisa la carpeta '{CARPETA_SALIDA}/' con frontera_bfs.png, frontera_dfs.png y frontera_ucs.png")


if __name__ == "__main__":
    main()