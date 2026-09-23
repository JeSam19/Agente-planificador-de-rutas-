import csv
import os
from pathlib import Path
import platform
import subprocess
import sys
import webbrowser

# Asegurar que se reconozcan la raíz y src/
RAIZ = Path(__file__).resolve().parent
sys.path.append(str(RAIZ))

import matplotlib.pyplot as plt
from src.BFS import bfs
from src.DFS import dfs
from src.UCS import ucs
from src.fase1 import accesible
from src.utils import cargar_grafo, gen_nodo_entrega

# Conexión directa a tus scripts existentes
from ver_fronteras import _capturar_snapshots, _checkpoints, graficar_snapshots
from ver_rutas import ALGORITMOS, construir_mapa


def abrir_archivo_sistema(ruta):
    """Abre un archivo (PNG, HTML) en la aplicación predeterminada del sistema sin bloquear."""
    ruta_obj = Path(ruta).resolve()
    if not ruta_obj.exists():
        return

    sistema = platform.system()
    if sistema == "Windows":
        os.startfile(str(ruta_obj))
    elif sistema == "Darwin":  # macOS
        subprocess.Popen(["open", str(ruta_obj)])
    else:  # Linux
        subprocess.Popen(["xdg-open", str(ruta_obj)])


def generar_tabla_png(datos, nombre_archivo="tabla_busquedas_ciegas.png"):
    """Genera la imagen PNG con la tabla comparativa completa de los 3 algoritmos (15 filas)."""
    if not datos:
        print("  [!] No hay datos para generar la tabla.")
        return

    columnas = [
        "Caso",
        "Algoritmo",
        "Metros (m)",
        "Arcos",
        "Expandidos",
        "Max Frontera",
        "Tiempo (ms)",
    ]
    filas = []

    for d in datos:
        filas.append([
            str(d["Caso"]),
            d["Algoritmo"],
            f"{d['Metros (m)']:.2f}",
            str(d["Arcos (saltos)"]),
            str(d["Nodos Expandidos"]),
            str(d["Max Frontera"]),
            f"{d['Tiempo (ms)']:.2f}",
        ])

    # Altura ajustada para alojar las 15 filas con claridad
    fig, ax = plt.subplots(figsize=(11, 9), dpi=200)
    ax.axis("off")
    ax.axis("tight")

    tabla = ax.table(
        cellText=filas, colLabels=columnas, loc="center", cellLoc="center"
    )
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(8.5)
    tabla.scale(1.1, 1.3)

    # Colores suaves para distinguir fácilmente los 3 algoritmos
    colores_alg = {
        "BFS": "#E3F2FD",  # Celeste claro
        "DFS": "#FFF3E0",  # Naranja claro
        "UCS": "#E8F5E9",  # Verde claro
    }

    for (fila, col), celda in tabla.get_celld().items():
        if fila == 0:
            celda.set_text_props(weight="bold", color="white")
            celda.set_facecolor("#1B263B")  # Encabezado azul oscuro
        else:
            alg_actual = filas[fila - 1][1]
            celda.set_facecolor(colores_alg.get(alg_actual, "#FFFFFF"))

    plt.title(
        "Métricas de Búsqueda a Ciegas (BFS vs DFS vs UCS)",
        fontsize=13,
        fontweight="bold",
        pad=16,
    )
    plt.savefig(nombre_archivo, bbox_inches="tight", dpi=200)
    plt.close(fig)
    print(f"  [+] Tabla comparativa completa guardada como imagen: {nombre_archivo}")


def ejecutar_busqueda_ciegas():
    print("\n" + "=" * 70)
    print("         MÓDULO: BÚSQUEDA A CIEGAS (BFS vs DFS vs UCS)")
    print("=" * 70)

    # 1. Cargar el grafo y seleccionar almacén + 5 destinos
    print("\n[1/5] Cargando grafo vial de la CDMX...")
    G = cargar_grafo("data/cdmx_norte_centro.graphml")

    print("[2/5] Generando almacén y validando 5 destinos alcanzables...")
    almacen, candidatos = gen_nodo_entrega(G, rango_entregas=(15, 25))
    alcanzables, _, _ = accesible(G, almacen, candidatos)

    if len(alcanzables) < 5:
        almacen, candidatos = gen_nodo_entrega(G, rango_entregas=(30, 45))
        alcanzables, _, _ = accesible(G, almacen, candidatos)

    destinos = alcanzables[:5]
    print(f"  -> Almacén Origen : {almacen}")
    print(f"  -> Destinos (5)   : {destinos}")

    # 2. Correr BFS, DFS y UCS sobre los 5 pares
    print("\n[3/5] Ejecutando algoritmos sobre los 5 pares origen-destino...")
    algoritmos_ordenados = [("BFS", bfs), ("DFS", dfs), ("UCS", ucs)]
    resultados_metricas = []
    destinos_info = {
        d: {} for d in destinos
    }  # Estructura requerida por ver_rutas.py

    for i, destino in enumerate(destinos, start=1):
        print(f"\n--- Caso {i}: Almacén {almacen} -> Destino {destino} ---")
        for nombre, funcion in algoritmos_ordenados:
            res = funcion(G, almacen, destino)
            destinos_info[destino][nombre] = res

            # CORRECCIÓN: Este bloque debe ir DENTRO del ciclo para registrar cada algoritmo
            if res.get("encontrado"):
                resultados_metricas.append({
                    "Caso": i,
                    "Origen": almacen,
                    "Destino": destino,
                    "Algoritmo": nombre,
                    "Metros (m)": round(res["metros"], 2),
                    "Arcos (saltos)": res["arcos"],
                    "Nodos Expandidos": res["expandidos"],
                    "Max Frontera": res["max_frontera"],
                    "Tiempo (ms)": round(res["tiempo_ms"], 2),
                })
                print(
                    f"  [{nombre:<3}] {res['metros']:>9.2f} m |"
                    f" {res['arcos']:>2} arcos |"
                    f" {res['expandidos']:>5} exp |"
                    f" {res['max_frontera']:>4} front |"
                    f" {res['tiempo_ms']:>6.2f} ms"
                )
            else:
                print(f"  [{nombre:<3}] Destino no alcanzable.")

    # Guardar CSV
    archivo_csv = "reporte_busquedas_ciegas.csv"
    if resultados_metricas:
        with open(archivo_csv, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=resultados_metricas[0].keys())
            writer.writeheader()
            writer.writerows(resultados_metricas)
        print(f"\n  [+] Reporte CSV exportado: {archivo_csv}")

    # 3. Generar tabla PNG
    print("\n[4/5] Generando mapa interactivo y tabla comparativa...")
    archivo_tabla_png = "tabla_busquedas_ciegas.png"
    generar_tabla_png(resultados_metricas, nombre_archivo=archivo_tabla_png)

    # 4. Generar visualizacion_rutas_ciegas.html mediante ver_rutas.py
    archivo_html = "visualizacion_rutas_ciegas.html"
    mapa = construir_mapa(G, almacen, destinos_info)
    mapa.save(archivo_html)
    print(f"  [+] Mapa interactivo guardado: {archivo_html}")

    # 5. Generar los 3 snapshots de fronteras mediante ver_fronteras.py
    print("\n[5/5] Generando snapshots de frontera (BFS, DFS, UCS)...")
    carpeta_fronteras = Path("fronteras")
    carpeta_fronteras.mkdir(exist_ok=True)

    # Usamos el primer destino evaluado como referencia para las capturas
    destino_ref = destinos[0]
    archivos_fronteras = []

    for nombre, func_alg in ALGORITMOS.items():
        res_base = func_alg(G, almacen, destino_ref)
        # CORRECCIÓN: Todo el guardado y graficado dentro de la condición de éxito
        if res_base.get("encontrado"):
            checkpoints = _checkpoints(res_base["expandidos"], n=3)
            snapshots = _capturar_snapshots(
                func_alg, G, almacen, destino_ref, checkpoints
            )
            ruta_img = carpeta_fronteras / f"frontera_{nombre.lower()}.png"
            graficar_snapshots(
                G,
                nombre,
                snapshots,
                almacen,
                destino_ref,
                res_base["expandidos"],
                ruta_img,
            )
            archivos_fronteras.append(ruta_img)

    # -------------------------------------------------------------
    # APERTURA AUTOMÁTICA DE LAS 5 VENTANAS
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print(">>> Abriendo las 5 ventanas de resultados automáticas...")
    print("=" * 70)

    # 1. Ventana de la Tabla de Métricas (15 filas comparadas)
    print(" -> Abriendo tabla_busquedas_ciegas.png...")
    abrir_archivo_sistema(archivo_tabla_png)

    # 2. Ventana del Navegador con las Rutas
    print(" -> Abriendo visualizacion_rutas_ciegas.html en el navegador...")
    webbrowser.open(Path(archivo_html).resolve().as_uri())

    # 3, 4 y 5. Ventanas de los Snapshots de Frontera
    for img_f in archivos_fronteras:
        print(f" -> Abriendo {img_f.name}...")
        abrir_archivo_sistema(img_f)

    input("\nPresiona [Enter] para volver al menú principal...")


def ejecutar_busqueda_informada():
    print("\n" + "=" * 60)
    print("              MÓDULO: BÚSQUEDA INFORMADA")
    print("=" * 60)
    print("\n[!] Módulo en desarrollo (Asignado al equipo).")
    input("\nPresiona [Enter] para volver al menú principal...")


def ejecutar_busqueda_local():
    print("\n" + "=" * 60)
    print("                MÓDULO: BÚSQUEDA LOCAL")
    print("=" * 60)
    print("\n[!] Módulo en desarrollo (Asignado al equipo).")
    input("\nPresiona [Enter] para volver al menú principal...")


def menu():
    while True:
        print("\n" + "=" * 55)
        print("      SISTEMA DE PLANIFICACIÓN DE RUTAS - CDMX")
        print("=" * 55)
        print("  1. Búsqueda a ciegas (BFS, DFS, UCS)")
        print("  2. Búsqueda informada (En desarrollo)")
        print("  3. Búsqueda local (En desarrollo)")
        print("  0. Salir")
        print("=" * 55)

        opcion = input("Selecciona un módulo [0-3]: ").strip()

        if opcion == "1":
            ejecutar_busqueda_ciegas()
        elif opcion == "2":
            ejecutar_busqueda_informada()
        elif opcion == "3":
            ejecutar_busqueda_local()
        elif opcion == "0":
            print("\nSaliendo del programa. ¡Hasta luego!\n")
            break
        else:
            print("\n[!] Opción no válida. Introduce un valor entre 0 y 3.")


if __name__ == "__main__":
    menu()