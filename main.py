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
from src.fase2 import a_star, greedy_best_first, h1_euclidiana, h2_haversine, h3_personalizada
from src.fase3 import (
    calcular_matriz_distancias,
    evaluar_costo_ruta,
    simulated_annealing,
    algoritmo_genetico,
    graficar_convergencia,
    graficar_ruta_optimizada
)
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
    print("\n" + "=" * 70)
    print("         MÓDULO: BÚSQUEDA INFORMADA (A* vs Greedy)")
    print("=" * 70)

    print("\n[1/4] Cargando grafo vial de la CDMX...")
    G = cargar_grafo("data/cdmx_norte_centro.graphml")

    print("[2/4] Generando almacén y validando 5 destinos...")
    almacen, candidatos = gen_nodo_entrega(G, rango_entregas=(15, 25))
    alcanzables, _, _ = accesible(G, almacen, candidatos)
    destinos = alcanzables[:5]

    print(f"  -> Almacén Origen : {almacen}")
    print(f"  -> Destinos (5)   : {destinos}")

    print("\n[3/4] Ejecutando algoritmos informados...\n")
    
    # Diccionario para guardar las rutas y mandarlas al mapa
    destinos_info = {d: {} for d in destinos}

    # Función interna para adaptar los nombres de las variables para ver_rutas.py
    def adaptar_res(res):
        return {
            "encontrado": True if res.get("camino") else False,
            "camino": res.get("camino", []),
            "metros": res.get("costo", 0),
            "arcos": len(res.get("camino", [])) - 1 if res.get("camino") else 0,
            "expandidos": res.get("nodos_expandidos", 0),
            "tiempo_ms": res.get("tiempo_ms", 0)
        }

    for i, destino in enumerate(destinos, start=1):
        print(f"--- Caso {i}: Almacén {almacen} -> Destino {destino} ---")
        
        res_a1 = a_star(G, almacen, destino, h1_euclidiana)
        destinos_info[destino]["A* (Euclidiana)"] = adaptar_res(res_a1)
        print(f"  [A*_h1_Euclidiana]   {res_a1['costo']:>9.2f} m | {res_a1['nodos_expandidos']:>5} exp | {res_a1['tiempo_ms']:>6.2f} ms")
        
        res_a2 = a_star(G, almacen, destino, h2_haversine)
        destinos_info[destino]["A* (Haversine)"] = adaptar_res(res_a2)
        print(f"  [A*_h2_Haversine]    {res_a2['costo']:>9.2f} m | {res_a2['nodos_expandidos']:>5} exp | {res_a2['tiempo_ms']:>6.2f} ms")
        
        res_a3 = a_star(G, almacen, destino, h3_personalizada)
        destinos_info[destino]["A* (Personalizada)"] = adaptar_res(res_a3)
        print(f"  [A*_h3_Personalizada] {res_a3['costo']:>8.2f} m | {res_a3['nodos_expandidos']:>5} exp | {res_a3['tiempo_ms']:>6.2f} ms")
        
        res_g = greedy_best_first(G, almacen, destino, h2_haversine)
        destinos_info[destino]["Greedy Best-First"] = adaptar_res(res_g)
        print(f"  [Greedy_h2]          {res_g['costo']:>9.2f} m | {res_g['nodos_expandidos']:>5} exp | {res_g['tiempo_ms']:>6.2f} ms\n")
        
    print("[4/4] Generando mapa interactivo...")
    archivo_html = "visualizacion_rutas_informadas.html"
    
    mapa = construir_mapa(G, almacen, destinos_info)
    mapa.save(archivo_html)
    print(f"  [+] Mapa interactivo guardado: {archivo_html}")
    
    print(" -> Abriendo mapa en el navegador...")
    webbrowser.open(Path(archivo_html).resolve().as_uri())

    input("\nPresiona [Enter] para volver al menú principal...")

def ejecutar_busqueda_local():
    print("\n" + "=" * 60)
    print("                MÓDULO: BÚSQUEDA LOCAL (TSP)")
    print("=" * 60)

    # 1. Cargar grafo y seleccionar de 10 a 15 puntos de entrega
    print("\n[1/4] Cargando grafo vial de la CDMX...")
    G = cargar_grafo("data/cdmx_norte_centro.graphml")

    print("[2/4] Seleccionando conjunto de entregas alcanzables (10-15 puntos)...")
    almacen, candidatos = gen_nodo_entrega(G, rango_entregas=(15, 20))
    alcanzables, _, _ = accesible(G, almacen, candidatos)

    puntos_entrega = alcanzables[:12]
    todos_los_puntos = [almacen] + puntos_entrega

    print(f"  -> Total de paradas a optimizar: {len(todos_los_puntos)} (1 Almacén + {len(puntos_entrega)} Entregas)")

    # 2. Calcular matriz de distancias punto a punto
    print("\n[3/4] Calculando matriz de distancias A*/UCS entre todos los pares...")
    matriz_dist = calcular_matriz_distancias(G, todos_los_puntos)

    # Solución Trivial Aleatoria de referencia
    solucion_inicial = list(range(len(todos_los_puntos)))
    costo_inicial = evaluar_costo_ruta(matriz_dist, solucion_inicial)

    # 3. Ejecutar Simulated Annealing y Algoritmo Genético
    print("\n[4/4] Ejecutando algoritmos de Búsqueda Local...")
    res_sa = simulated_annealing(matriz_dist, T0=1000.0, alpha=0.95, T_min=0.01)
    res_ga = algoritmo_genetico(matriz_dist, num_generaciones=250, tam_poblacion=50)

    # Calcular mejoras en porcentaje
    mejora_sa = ((costo_inicial - res_sa["mejor_costo"]) / costo_inicial) * 100
    mejora_ga = ((costo_inicial - res_ga["mejor_costo"]) / costo_inicial) * 100

    print("\n" + "-" * 55)
    print("               RESULTADOS DE LA OPTIMIZACIÓN")
    print("-" * 55)
    print(f"Ruta Aleatoria Inicial : {costo_inicial:,.2f} m")
    print(f"Simulated Annealing    : {res_sa['mejor_costo']:,.2f} m | Mejora: {mejora_sa:.2f}% | Tiempo: {res_sa['tiempo_ms']:.2f} ms")
    print(f"Algoritmo Genético     : {res_ga['mejor_costo']:,.2f} m | Mejora: {mejora_ga:.2f}% | Tiempo: {res_ga['tiempo_ms']:.2f} ms")
    print("-" * 55)
    
    # Exportación del CSV y de su PNG
    archivo_csv = "reporte_busqueda_local.csv"
    img_tabla = "tabla_reporte_busqueda_local.png"

    datos_tabla = [
        {
            "Estrategia": "Solución Trivial Aleatoria",
            "N° Paradas": len(todos_los_puntos),
            "Costo Total (m)": f"{costo_inicial:,.2f} m",
            "Mejora (%)": "0.00%",
            "Tiempo (ms)": "0.00 ms"
        },
        {
            "Estrategia": "Simulated Annealing (SA)",
            "N° Paradas": len(todos_los_puntos),
            "Costo Total (m)": f"{res_sa['mejor_costo']:,.2f} m",
            "Mejora (%)": f"{mejora_sa:.2f}%",
            "Tiempo (ms)": f"{res_sa['tiempo_ms']:.2f} ms"
        },
        {
            "Estrategia": "Algoritmo Genético (AG)",
            "N° Paradas": len(todos_los_puntos),
            "Costo Total (m)": f"{res_ga['mejor_costo']:,.2f} m",
            "Mejora (%)": f"{mejora_ga:.2f}%",
            "Tiempo (ms)": f"{res_ga['tiempo_ms']:.2f} ms"
        }
    ]

    # 1. Escritura del archivo CSV
    filas_csv = [
        {
            "Estrategia": d["Estrategia"],
            "N_Paradas": d["N° Paradas"],
            "Costo_Total_Metros": float(d["Costo Total (m)"].replace(" m", "").replace(",", "")),
            "Mejora_Porcentaje": float(d["Mejora (%)"].replace("%", "")),
            "Tiempo_ms": float(d["Tiempo (ms)"].replace(" ms", ""))
        }
        for d in datos_tabla
    ]

    with open(archivo_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=filas_csv[0].keys())
        writer.writeheader()
        writer.writerows(filas_csv)
    print(f"  [+] Reporte CSV exportado automáticamente: {archivo_csv}")

    # 2. Renderizado de la tabla con el esquema Dark/Neón idéntico
    import pandas as pd
    import matplotlib.pyplot as plt

    df_tabla = pd.DataFrame(datos_tabla)

    fig, ax = plt.subplots(figsize=(9, 2.5), dpi=300)
    fig.patch.set_facecolor('#111111')  # Fondo exterior negro
    ax.set_facecolor('#111111')
    ax.axis('tight')
    ax.axis('off')

    tabla = ax.table(
        cellText=df_tabla.values,
        colLabels=df_tabla.columns,
        cellLoc='center',
        loc='center'
    )

    tabla.auto_set_font_size(False)
    tabla.set_fontsize(9)
    tabla.scale(1.2, 1.6)

    # Aplicar estilos 
    for (row, col), cell in tabla.get_celld().items():
        cell.set_edgecolor('#333333')  # Bordes gris oscuro
        cell.set_linewidth(0.8)
        
        if row == 0:
            # Encabezado: fondo gris oscuro, texto blanco en negritas
            cell.set_facecolor('#222222')
            cell.set_text_props(weight='bold', color='white')
        else:
            # Filas de datos: fondo gris muy oscuro (#181818)
            cell.set_facecolor('#181818')
            
            # Resaltado verde neón para las columnas de 'Estrategia' o 'Mejora (%)'
            if col in [0, 3]:
                cell.set_text_props(color='#00FF66', weight='bold')
            else:
                cell.set_text_props(color='#E0E0E0')

    plt.savefig(img_tabla, bbox_inches='tight', dpi=300, facecolor=fig.get_facecolor())
    plt.close()
    print(f"  [+] Imagen de la tabla guardada: {img_tabla}")

    # 4. Generar imágenes 
    img_convergencia = "convergencia_busqueda_local.png"
    img_mapa_opt = "mapa_ruta_optimizada_fase3.png"

    graficar_convergencia(res_sa, res_ga, costo_inicial, nombre_archivo=img_convergencia)

    mejor_res = res_sa if res_sa["mejor_costo"] < res_ga["mejor_costo"] else res_ga
    graficar_ruta_optimizada(
        G,
        todos_los_puntos,
        mejor_res["mejor_ruta"],
        f"Ruta Óptima ({mejor_res['algoritmo']}) - {mejor_res['mejor_costo']:.1f} m",
        nombre_archivo=img_mapa_opt,
    )

    # Abrir imágenes automáticamente
    print("\n -> Abriendo imágenes generadas...")
    abrir_archivo_sistema(img_convergencia)
    abrir_archivo_sistema(img_mapa_opt)
    abrir_archivo_sistema(img_tabla)

    input("\nPresiona [Enter] para volver al menú principal...")

def menu():
    while True:
        print("\n" + "=" * 55)
        print("      SISTEMA DE PLANIFICACIÓN DE RUTAS - CDMX")
        print("=" * 55)
        print("  1. Búsqueda a ciegas (BFS, DFS, UCS)")
        print("  2. Búsqueda informada ")
        print("  3. Búsqueda local (AG, SA, CC)")
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
