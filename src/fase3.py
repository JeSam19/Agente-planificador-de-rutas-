import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.append(str(RAIZ))

import copy
import math
import random
import time
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd

# Ahora sí reconocerá src.UCS perfectamente
from src.UCS import ucs

# Importamos las funciones de la Fase 1 / UCS sin modificar ningún código
from src.UCS import ucs


# =============================================================================
# 1. MATRIZ DE DISTANCIAS
# =============================================================================
def calcular_matriz_distancias(G, puntos):
    """Calcula la matriz de distancias (en metros) entre todos los puntos usando UCS o A*.

    puntos: Lista que inicia con el Almacén [depósito, entrega1, entrega2,
    ...]
    """
    n = len(puntos)
    matriz = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            if i == j:
                matriz[i][j] = 0.0
            else:
                # Se utiliza el algoritmo de menor costo de la fase previa
                res = ucs(G, puntos[i], puntos[j])
                if res.get("encontrado"):
                    matriz[i][j] = res["metros"]
                else:
                    matriz[i][j] = float("inf")
    return matriz


def evaluar_costo_ruta(matriz_distancias, permutacion):
    """Calcula el costo total f(pi) recorriendo los puntos y regresando al almacén."""
    distancia_total = 0.0
    num_puntos = len(permutacion)

    for i in range(num_puntos - 1):
        origen = permutacion[i]
        destino = permutacion[i + 1]
        distancia_total += matriz_distancias[origen][destino]

    # Regreso al almacén (punto 0)
    distancia_total += matriz_distancias[permutacion[-1]][permutacion[0]]
    return distancia_total


# =============================================================================
# 2. OPERADOR DE VECINDAD 2-OPT
# =============================================================================
def aplicar_2opt(permutacion):
    """Aplica el operador 2-opt invirtiendo un subsegmento entre los índices i y j

    (manteniendo fijo el Almacén en el índice 0).
    """
    n = len(permutacion)
    if n <= 3:
        return permutacion.copy()

    nueva_perm = permutacion.copy()
    # El almacén es el índice 0, intercambiamos a partir del índice 1
    i, j = sorted(random.sample(range(1, n), 2))
    nueva_perm[i : j + 1] = reversed(nueva_perm[i : j + 1])
    return nueva_perm


# =============================================================================
# 3. SIMULATED ANNEALING (ENFRIAMIENTO GEOMÉTRICO)
# =============================================================================
def simulated_annealing(
    matriz_distancias, T0=1000.0, alpha=0.95, T_min=0.01, max_iter_temp=100
):
    """Implementa Simulated Annealing con esquema de enfriamiento geométrico T = T * alpha."""
    num_puntos = len(matriz_distancias)
    solucion_actual = list(range(num_puntos))
    costo_actual = evaluar_costo_ruta(matriz_distancias, solucion_actual)

    mejor_solucion = solucion_actual.copy()
    mejor_costo = costo_actual

    historial_costos = []
    temperatura = T0

    t_inicio = time.time()

    while temperatura > T_min:
        for _ in range(max_iter_temp):
            vecino = aplicar_2opt(solucion_actual)
            costo_vecino = evaluar_costo_ruta(matriz_distancias, vecino)
            delta_e = costo_vecino - costo_actual

            # Criterio de aceptación de Metropolis
            if delta_e < 0 or random.random() < math.exp(-delta_e / temperatura):
                solucion_actual = vecino
                costo_actual = costo_vecino

                if costo_actual < mejor_costo:
                    mejor_solucion = solucion_actual.copy()
                    mejor_costo = costo_actual

            historial_costos.append(mejor_costo)

        temperatura *= alpha  # Enfriamiento geométrico

    t_ejecucion = (time.time() - t_inicio) * 1000  # ms

    return {
        "algoritmo": "Simulated Annealing",
        "mejor_ruta": mejor_solucion,
        "mejor_costo": mejor_costo,
        "historial": historial_costos,
        "tiempo_ms": t_ejecucion,
    }


# =============================================================================
# 4. ALGORITMO GENÉTICO (OPERADOR OX + MUTACIÓN INTERCAMBIO)
# =============================================================================
def cruza_ox(paterno1, paterno2):
    """Order Crossover (OX) preservando la permutación de los clientes."""
    size = len(paterno1)
    hijo = [-1] * size

    # Mantener el almacén fijo en la posición 0
    hijo[0] = 0

    a, b = sorted(random.sample(range(1, size), 2))
    hijo[a : b + 1] = paterno1[a : b + 1]

    idx_hijo = (b + 1) % size
    if idx_hijo == 0:
        idx_hijo = 1

    for elem in paterno2[b + 1 :] + paterno2[: b + 1]:
        if elem not in hijo:
            if idx_hijo == 0:
                idx_hijo = 1
            hijo[idx_hijo] = elem
            idx_hijo = (idx_hijo + 1) % size
            if idx_hijo == 0:
                idx_hijo = 1

    return hijo


def mutacion_intercambio(permutacion, pm=0.2):
    """Mutación por intercambio de posiciones."""
    if random.random() < pm and len(permutacion) > 2:
        i, j = random.sample(range(1, len(permutacion)), 2)
        permutacion[i], permutacion[j] = permutacion[j], permutacion[i]
    return permutacion


def algoritmo_genetico(
    matriz_distancias, num_generaciones=200, tam_poblacion=50, pm=0.2
):
    """Implementa Algoritmo Genético para permutaciones."""
    num_puntos = len(matriz_distancias)
    t_inicio = time.time()

    # Población inicial
    poblacion = []
    for _ in range(tam_poblacion):
        ind = list(range(1, num_puntos))
        random.shuffle(ind)
        poblacion.append([0] + ind)

    mejor_solucion = None
    mejor_costo = float("inf")
    historial_costos = []

    for gen in range(num_generaciones):
        # Evaluar
        costos = [evaluar_costo_ruta(matriz_distancias, ind) for ind in poblacion]

        for i, c in enumerate(costos):
            if c < mejor_costo:
                mejor_costo = c
                mejor_solucion = poblacion[i].copy()

        historial_costos.append(mejor_costo)

        # Selección por Torneo
        nueva_poblacion = []
        for _ in range(tam_poblacion):
            p1, p2 = random.sample(poblacion, 2)
            padre1 = p1 if evaluar_costo_ruta(matriz_distancias, p1) < evaluar_costo_ruta(matriz_distancias, p2) else p2

            p3, p4 = random.sample(poblacion, 2)
            padre2 = p3 if evaluar_costo_ruta(matriz_distancias, p3) < evaluar_costo_ruta(matriz_distancias, p4) else p4

            # Cruza OX
            hijo = cruza_ox(padre1, padre2)

            # Mutación
            hijo = mutacion_intercambio(hijo, pm=pm)
            nueva_poblacion.append(hijo)

        poblacion = nueva_poblacion

    t_ejecucion = (time.time() - t_inicio) * 1000

    return {
        "algoritmo": "Algoritmo Genético",
        "mejor_ruta": mejor_solucion,
        "mejor_costo": mejor_costo,
        "historial": historial_costos,
        "tiempo_ms": t_ejecucion,
    }


# =============================================================================
# 5. GENERACIÓN DE VISUALIZACIONES E IMÁGENES
# =============================================================================
def graficar_convergencia(
    res_sa, res_ga, costo_inicial, nombre_archivo="convergencia_fase3.png"
):
    """Genera la gráfica de curva de convergencia comparativa (Costo vs Iteraciones)."""
    plt.figure(figsize=(10, 5), dpi=300)
    plt.style.use("dark_background")

    plt.plot(res_sa["historial"], label=f"Simulated Annealing ({res_sa['mejor_costo']:.1f} m)", color="#00FFFF", linewidth=2)
    plt.plot(res_ga["historial"], label=f"Algoritmo Genético ({res_ga['mejor_costo']:.1f} m)", color="#FF00FF", linewidth=2)
    plt.axhline(y=costo_inicial, color="#FF4444", linestyle="--", label=f"Solución Aleatoria ({costo_inicial:.1f} m)")

    plt.title("Curva de Convergencia: Búsqueda Local (TSP)", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Iteraciones / Generaciones", fontsize=10)
    plt.ylabel("Distancia Total Recorrida (m)", fontsize=10)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(facecolor="#222222", edgecolor="#555555", fontsize=9)

    plt.tight_layout()
    plt.savefig(nombre_archivo, dpi=300)
    plt.close()
    print(f"  [+] Gráfica de convergencia guardada: {nombre_archivo}")


def graficar_ruta_optimizada(
    G, puntos, ruta_indices, titulo, nombre_archivo="mapa_ruta_optima.png"
):
    """Dibuja en el mapa real del grafo de OSMnx el recorrido óptimo resuelto."""
    fig_mapa, ax_mapa = ox.plot_graph(
        G,
        node_size=0,
        edge_linewidth=0.3,
        edge_color="#333333",
        bgcolor="#111111",
        show=False,
        close=False,
        figsize=(8, 10),
    )

    # Convertir índices a nodos reales
    nodos_ordenados = [puntos[i] for i in ruta_indices] + [puntos[ruta_indices[0]]]

    # Trazar rutas entre par de nodos seguidos usando la ruta en la red vial
    colores_tramo = plt.cm.spring(np.linspace(0, 1, len(nodos_ordenados) - 1))

    for idx in range(len(nodos_ordenados) - 1):
        u = nodos_ordenados[idx]
        v = nodos_ordenados[idx + 1]
        res = ucs(G, u, v)
        if res.get("encontrado"):
            camino = res["camino"]
            ox.plot_graph_route(
                G,
                camino,
                route_color=colores_tramo[idx],
                route_linewidth=2.5,
                ax=ax_mapa,
                show=False,
                close=False,
            )

    # Dibujar marcadores de las entregas
    xs = [G.nodes[n]["x"] for n in puntos]
    ys = [G.nodes[n]["y"] for n in puntos]

    # Almacén (índice 0)
    ax_mapa.scatter(xs[0], ys[0], c="#FF2222", s=200, marker="*", edgecolors="white", zorder=10, label="Almacén")

    # Clientes
    ax_mapa.scatter(xs[1:], ys[1:], c="#00FF66", s=60, marker="o", edgecolors="black", zorder=9, label="Puntos de Entrega")

    # Etiquetas numéricas con el orden de visita
    for pos_orden, idx_nodo in enumerate(ruta_indices):
        nodo = puntos[idx_nodo]
        ax_mapa.text(
            G.nodes[nodo]["x"],
            G.nodes[nodo]["y"],
            f" {pos_orden}",
            color="white",
            fontsize=9,
            weight="bold",
            zorder=11,
        )

    ax_mapa.legend(loc="upper left", facecolor="#222222", edgecolor="#555555", labelcolor="white")
    ax_mapa.set_title(titulo, color="white", fontsize=11, pad=10)

    fig_mapa.savefig(nombre_archivo, dpi=300, bbox_inches="tight", facecolor=fig_mapa.get_facecolor())
    plt.close(fig_mapa)
    print(f"  [+] Mapa de la ruta optimizada guardado: {nombre_archivo}")

