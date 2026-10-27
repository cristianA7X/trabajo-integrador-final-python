"""
INTEGRADOR II - FINAL: Tienda de Ropa IT (Interfaz Gráfica con Tkinter)
Opción 3 - Tienda de Ropa
Productos: Remera $10, Pantalón $20, Buzo $25, Gorra $8

DISTRIBUCIÓN DEL TRABAJO - 5 INTEGRANTES:
1. Arispe Gabriel: Configuración general, Base de Datos SQLite y Catálogo.
2. López Cristian: Validaciones, Registro de turnos (IN/OUT), Gestión (Alta/Baja) de encargados y Consultas.
3. Loza Valentina: Interfaz de Nuevo Pedido, cálculo de Subtotal y Descuento con IntVar/Checkbutton.
4. Lucero Germán: Cobro, cálculo de Vuelto, Confirmación y guardado de Venta en SQLite.
5. Zarate Benito Elías: Inicio con selección/eliminación de encargados (Radiobutton), Menú y Dashboard de Historial.
"""

import sqlite3
import time
import tkinter as tk

# =============================================================================
# BLOQUE 1 - CONFIGURACIÓN GENERAL, BASE DE DATOS Y CATÁLOGO DE PRODUCTOS
# INTEGRANTE RESPONSABLE: ARISPE GABRIEL
#
# En este bloque se importan los módulos necesarios, se establece la conexión
# con la base de datos SQLite ("comercio.sql") y se crean las tablas "venta",
# "registro" y "encargado_guardado" si no existen. Además, se definen el
# diccionario "menu" con los precios de las prendas y el diccionario "estado"
# para compartir los datos del turno actual entre las distintas funciones.
# =============================================================================

conn = sqlite3.connect("comercio.sql")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS venta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT,
    fecha TEXT,
    cant_remera INTEGER,
    cant_pantalon INTEGER,
    cant_gorra INTEGER,
    cant_buzo INTEGER,
    total REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS registro (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    encargado TEXT,
    fecha TEXT,
    evento TEXT,
    caja REAL
)
""")

# Tabla para almacenar la lista de encargados frecuentes (permite eliminarlos
# de la pantalla de inicio sin borrar su historial contable en "registro").
cursor.execute("""
CREATE TABLE IF NOT EXISTS encargado_guardado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE
)
""")

conn.commit()

menu = {
    "1": {"nombre": "Remera", "precio": 10},
    "2": {"nombre": "Pantalón", "precio": 20},
    "3": {"nombre": "Buzo", "precio": 25},
    "4": {"nombre": "Gorra", "precio": 8},
}

# Variables globales de estado para el manejo de turnos en la interfaz
estado = {
    "encargado": "",
    "total_turno": 0,
    "subtotal_actual": 0,
    "total_actual": 0,
    "vuelto_actual": 0,
    "pedido_calculado": False,
    "pago_valido": False
}


# =============================================================================
# BLOQUE 2 - VALIDACIÓN DE DATOS, GESTIÓN DE ENCARGADOS, TURNOS Y CONSULTAS
# INTEGRANTE RESPONSABLE: LÓPEZ CRISTIAN
#
# Este bloque adapta las validaciones al entorno gráfico utilizando el método
# .isdecimal() visto en la Clase 18 para evitar errores (ValueError). Administra
# el registro de entrada (IN) y salida (OUT) de los encargados en la base de
# datos, permite guardar y eliminar encargados frecuentes de la pantalla de
# inicio, y ejecuta las consultas SQL para nutrir el historial de ventas.
# =============================================================================

def convertir_entero(dato):
    dato = dato.strip()
    if dato == "":
        return 0
    # Validamos con isdecimal() como se vio en la Clase 18
    if dato.isdecimal():
        return int(dato)
    else:
        return "error"


def guardar_encargado_frecuente(encargado):
    # Guarda el nombre en la lista de acceso rápido si todavía no existe
    cursor.execute(
        "INSERT OR IGNORE INTO encargado_guardado(nombre) VALUES (?)",
        (encargado,)
    )
    conn.commit()


def eliminar_encargado_guardado(encargado):
    # Elimina al encargado de la lista de acceso rápido sin borrar su historial
    cursor.execute(
        "DELETE FROM encargado_guardado WHERE nombre = ?",
        (encargado,)
    )
    conn.commit()


def obtener_encargados_guardados():
    cursor.execute("SELECT nombre FROM encargado_guardado")
    filas = cursor.fetchall()
    nombres = []
    # Usamos reversed() (Clase 18) para mostrar primero los últimos agregados
    for fila in reversed(filas):
        nombres.append(fila[0])
    return nombres[:6]


def registroEntrada(encargado):
    fecha = time.asctime()
    # Aseguramos que quede agendado en la lista de encargados guardados
    guardar_encargado_frecuente(encargado)

    cursor.execute(
        "INSERT INTO registro(encargado, fecha, evento, caja) VALUES (?, ?, ?, ?)",
        (encargado, fecha, "IN - Entrada", 0)
    )
    conn.commit()


def registroSalida(encargado, total):
    fecha = time.asctime()
    cursor.execute(
        "INSERT INTO registro(encargado, fecha, evento, caja) VALUES (?, ?, ?, ?)",
        (encargado, fecha, "OUT - Salida", total)
    )
    conn.commit()


def obtener_total_historico():
    cursor.execute("SELECT SUM(total) FROM venta")
    resultado = cursor.fetchone()[0]
    if resultado is None:
        return 0
    return resultado


def obtener_cantidad_ventas():
    cursor.execute("SELECT COUNT(id) FROM venta")
    resultado = cursor.fetchone()[0]
    if resultado is None:
        return 0
    return resultado


def obtener_ultimas_ventas():
    cursor.execute(
        "SELECT id, cliente, fecha, cant_remera, cant_pantalon, cant_buzo, cant_gorra, total "
        "FROM venta"
    )
    filas = cursor.fetchall()
    # Aplicamos reversed() visto en Clase 18 para mostrar las más recientes primero
    return list(reversed(filas))[:7]


def obtener_ultimos_registros():
    cursor.execute("SELECT id, encargado, fecha, evento, caja FROM registro")
    filas = cursor.fetchall()
    return list(reversed(filas))[:4]


# =============================================================================
# BLOQUE 3 - VENTANA DE NUEVO PEDIDO, SELECCIÓN DE PRODUCTOS, TOTAL Y DESCUENTO
# INTEGRANTE RESPONSABLE: LOZA VALENTINA
#
# Este bloque construye la ventana de "Nuevo Pedido" y gestiona la primera
# etapa de la compra: ingreso del nombre del cliente, cajas de texto (Entry)
# para las cantidades de cada prenda, y un Checkbutton asociado a un tk.IntVar
# (visto en Clase 18) para aplicar el descuento opcional del 10%. Al presionar
# "Calcular Total", valida las cantidades y actualiza las etiquetas dinámicas.
# =============================================================================

def abrir_ventana_pedido():
    estado["subtotal_actual"] = 0
    estado["total_actual"] = 0
    estado["vuelto_actual"] = 0
    estado["pedido_calculado"] = False
    estado["pago_valido"] = False

    v_pedido = tk.Toplevel(ventana_principal)
    v_pedido.title("Nuevo Pedido - Tienda de Ropa IT")
    v_pedido.config(width=520, height=560, bg="#F4F6F7")

    lbl_titulo = tk.Label(
        v_pedido, text="CARGA DE NUEVO PEDIDO",
        bg="#1F3A52", fg="white", font=("Arial", 12, "bold")
    )
    lbl_titulo.place(x=20, y=15, width=480, height=35)

    lbl_cliente = tk.Label(v_pedido, text="Nombre del Cliente:", bg="#F4F6F7", font=("Arial", 10, "bold"))
    lbl_cliente.place(x=30, y=65)
    caja_cliente = tk.Entry(v_pedido, font=("Arial", 10))
    caja_cliente.place(x=200, y=65, width=250, height=25)

    lbl_prod = tk.Label(v_pedido, text="Cantidades por producto (dejar vacío o 0 si no lleva):", bg="#F4F6F7")
    lbl_prod.place(x=30, y=105)

    # Producto 1: Remera ($10)
    lbl_rem = tk.Label(v_pedido, text="1 - Remera ($10):", bg="#F4F6F7", font=("Arial", 10))
    lbl_rem.place(x=40, y=135)
    caja_remera = tk.Entry(v_pedido, font=("Arial", 10))
    caja_remera.insert(0, "0")
    caja_remera.place(x=200, y=135, width=80, height=25)

    # Producto 2: Pantalón ($20)
    lbl_pan = tk.Label(v_pedido, text="2 - Pantalón ($20):", bg="#F4F6F7", font=("Arial", 10))
    lbl_pan.place(x=40, y=170)
    caja_pantalon = tk.Entry(v_pedido, font=("Arial", 10))
    caja_pantalon.insert(0, "0")
    caja_pantalon.place(x=200, y=170, width=80, height=25)

    # Producto 3: Buzo ($25)
    lbl_buz = tk.Label(v_pedido, text="3 - Buzo ($25):", bg="#F4F6F7", font=("Arial", 10))
    lbl_buz.place(x=40, y=205)
    caja_buzo = tk.Entry(v_pedido, font=("Arial", 10))
    caja_buzo.insert(0, "0")
    caja_buzo.place(x=200, y=205, width=80, height=25)

    # Producto 4: Gorra ($8)
    lbl_gor = tk.Label(v_pedido, text="4 - Gorra ($8):", bg="#F4F6F7", font=("Arial", 10))
    lbl_gor.place(x=40, y=240)
    caja_gorra = tk.Entry(v_pedido, font=("Arial", 10))
    caja_gorra.insert(0, "0")
    caja_gorra.place(x=200, y=240, width=80, height=25)

    # Checkbutton con tk.IntVar() para el descuento del 10% (Clase 18)
    var_descuento = tk.IntVar()
    var_descuento.set(0)
    check_desc = tk.Checkbutton(
        v_pedido, text="Aplicar descuento del 10%",
        variable=var_descuento, bg="#F4F6F7", font=("Arial", 10, "bold")
    )
    check_desc.place(x=35, y=275)

    # Variables de control StringVar (Clase 18)
    var_resultado_total = tk.StringVar()
    var_resultado_total.set("Subtotal: $0  |  Total a pagar: $0")

    var_mensaje_estado = tk.StringVar()
    var_mensaje_estado.set("Complete las cantidades y presione '1. Calcular Total'.")

    lbl_mostrar_total = tk.Label(
        v_pedido, textvariable=var_resultado_total,
        bg="#D6EAF8", fg="#1B4F72", font=("Arial", 10, "bold")
    )
    lbl_mostrar_total.place(x=30, y=345, width=460, height=30)

    lbl_estado = tk.Label(
        v_pedido, textvariable=var_mensaje_estado,
        bg="#FCF3CF", fg="#7D6608", font=("Arial", 9, "bold")
    )
    lbl_estado.place(x=30, y=505, width=460, height=35)

    def calcular_total_pedido():
        c_rem = convertir_entero(caja_remera.get())
        c_pan = convertir_entero(caja_pantalon.get())
        c_buz = convertir_entero(caja_buzo.get())
        c_gor = convertir_entero(caja_gorra.get())

        if "error" in (c_rem, c_pan, c_buz, c_gor):
            var_mensaje_estado.set("ERROR: Las cantidades deben ser números enteros positivos.")
            lbl_estado.config(bg="#FADBD8", fg="#78281F")
            estado["pedido_calculado"] = False
            return

        subtotal = (
            c_rem * menu["1"]["precio"] +
            c_pan * menu["2"]["precio"] +
            c_buz * menu["3"]["precio"] +
            c_gor * menu["4"]["precio"]
        )

        if subtotal == 0:
            var_mensaje_estado.set("ATENCIÓN: Debe seleccionar al menos 1 producto.")
            lbl_estado.config(bg="#FADBD8", fg="#78281F")
            estado["pedido_calculado"] = False
            return

        if var_descuento.get() == 1:
            total = round(subtotal * 0.9)
            texto_desc = " (10% Desc. aplicado)"
        else:
            total = subtotal
            texto_desc = " (Sin descuento)"

        estado["subtotal_actual"] = subtotal
        estado["total_actual"] = total
        estado["pedido_calculado"] = True
        estado["pago_valido"] = False

        var_resultado_total.set(f"Subtotal: ${subtotal}{texto_desc}  |  TOTAL A PAGAR: ${total}")
        var_mensaje_estado.set("Total calculado. Ingrese con cuánto abona y calcule el vuelto.")
        lbl_estado.config(bg="#D4EFDF", fg="#145A32")

    btn_calcular = tk.Button(
        v_pedido, text="1. Calcular Total",
        bg="#2980B9", fg="white", font=("Arial", 10, "bold"),
        command=calcular_total_pedido
    )
    btn_calcular.place(x=30, y=310, width=200, height=28)


    # =========================================================================
    # BLOQUE 4 - PAGO, CÁLCULO DE VUELTO, CONFIRMACIÓN Y GUARDADO EN SQLITE
    # INTEGRANTE RESPONSABLE: LUCERO GERMÁN
    #
    # Este bloque continúa dentro de la ventana de pedido para gestionar el
    # cobro. Permite ingresar el monto con el que abona el cliente, calcula
    # automáticamente el vuelto validando que el dinero alcance, y finalmente
    # confirma el pedido guardando todos los datos en la tabla "venta" de
    # SQLite y actualizando la recaudación del turno.
    # =========================================================================

    lbl_pago = tk.Label(v_pedido, text="Abona con $:", bg="#F4F6F7", font=("Arial", 10, "bold"))
    lbl_pago.place(x=30, y=390)

    caja_pago = tk.Entry(v_pedido, font=("Arial", 10))
    caja_pago.place(x=140, y=390, width=100, height=25)

    var_vuelto = tk.StringVar()
    var_vuelto.set("Vuelto: $0")

    lbl_vuelto = tk.Label(
        v_pedido, textvariable=var_vuelto,
        bg="#E8F8F5", fg="#117864", font=("Arial", 10, "bold")
    )
    lbl_vuelto.place(x=250, y=425, width=240, height=30)

    def calcular_vuelto():
        if not estado["pedido_calculado"]:
            var_mensaje_estado.set("ERROR: Primero debe presionar '1. Calcular Total'.")
            lbl_estado.config(bg="#FADBD8", fg="#78281F")
            return

        pago = convertir_entero(caja_pago.get())

        if pago == "error" or caja_pago.get().strip() == "":
            var_mensaje_estado.set("ERROR: Ingrese un monto de pago numérico válido.")
            lbl_estado.config(bg="#FADBD8", fg="#78281F")
            estado["pago_valido"] = False
            return

        total = estado["total_actual"]

        if pago < total:
            faltante = total - pago
            var_vuelto.set("Monto insuficiente")
            var_mensaje_estado.set(f"El monto no alcanza. Faltan ${faltante}.")
            lbl_estado.config(bg="#FADBD8", fg="#78281F")
            estado["pago_valido"] = False
        else:
            vuelto = pago - total
            estado["vuelto_actual"] = vuelto
            estado["pago_valido"] = True
            var_vuelto.set(f"Vuelto a entregar: ${vuelto}")
            var_mensaje_estado.set("Pago válido. Ya puede presionar '3. Confirmar Pedido'.")
            lbl_estado.config(bg="#D4EFDF", fg="#145A32")

    def confirmar_pedido():
        calcular_total_pedido()
        if not estado["pedido_calculado"]:
            return

        calcular_vuelto()
        if not estado["pago_valido"]:
            return

        cliente = caja_cliente.get().strip()
        if cliente == "":
            var_mensaje_estado.set("ERROR: Debe ingresar el nombre del cliente.")
            lbl_estado.config(bg="#FADBD8", fg="#78281F")
            return

        cant_remera = convertir_entero(caja_remera.get())
        cant_pantalon = convertir_entero(caja_pantalon.get())
        cant_buzo = convertir_entero(caja_buzo.get())
        cant_gorra = convertir_entero(caja_gorra.get())
        total = estado["total_actual"]
        fecha = time.asctime()

        cursor.execute("""
            INSERT INTO venta
            (cliente, fecha, cant_remera, cant_pantalon, cant_buzo, cant_gorra, total)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            cliente,
            fecha,
            cant_remera,
            cant_pantalon,
            cant_buzo,
            cant_gorra,
            total
        ))
        conn.commit()

        estado["total_turno"] += total
        actualizar_datos_menu()
        v_pedido.destroy()

    btn_vuelto = tk.Button(
        v_pedido, text="2. Calcular Vuelto",
        bg="#16A085", fg="white", font=("Arial", 10, "bold"),
        command=calcular_vuelto
    )
    btn_vuelto.place(x=30, y=425, width=200, height=30)

    btn_confirmar = tk.Button(
        v_pedido, text="3. Confirmar y Guardar Pedido",
        bg="#27AE60", fg="white", font=("Arial", 10, "bold"),
        command=confirmar_pedido
    )
    btn_confirmar.place(x=30, y=465, width=310, height=32)

    btn_cancelar = tk.Button(
        v_pedido, text="Cancelar",
        bg="#C0392B", fg="white", font=("Arial", 10, "bold"),
        command=v_pedido.destroy
    )
    btn_cancelar.place(x=355, y=465, width=135, height=32)


# =============================================================================
# BLOQUE 5 - INICIO CON GESTIÓN DE ENCARGADOS, MENÚ Y DASHBOARD DE HISTORIAL
# INTEGRANTE RESPONSABLE: ZARATE BENITO ELÍAS
#
# Este bloque coordina la ventana principal: permite seleccionar un encargado
# guardado mediante Radiobuttons (Clase 18), eliminarlo de la lista rápida con
# un botón dedicado o ingresar uno nuevo; presenta el Menú Principal y despliega
# el Dashboard visual para el Historial de Ventas y Turnos.
# =============================================================================

def abrir_ventana_historial():
    v_hist = tk.Toplevel(ventana_principal)
    v_hist.title("Historial y Estadísticas - Tienda de Ropa IT")
    v_hist.config(width=680, height=540, bg="#EAECEE")

    # Encabezado superior del Historial
    lbl_tit = tk.Label(
        v_hist, text="PANEL DE HISTORIAL DE VENTAS Y REGISTRO DE CAJA",
        bg="#1F3A52", fg="white", font=("Arial", 12, "bold")
    )
    lbl_tit.place(x=20, y=15, width=640, height=35)

    # --- TARJETAS DE RESUMEN (KPIs) ---
    cant_ventas = obtener_cantidad_ventas()
    total_hist = obtener_total_historico()

    lbl_card1 = tk.Label(
        v_hist, text=f"VENTAS REGISTRADAS: {cant_ventas}",
        bg="#2980B9", fg="white", font=("Arial", 10, "bold")
    )
    lbl_card1.place(x=20, y=60, width=200, height=35)

    lbl_card2 = tk.Label(
        v_hist, text=f"TURNO ACTUAL: ${estado['total_turno']}",
        bg="#16A085", fg="white", font=("Arial", 10, "bold")
    )
    lbl_card2.place(x=230, y=60, width=200, height=35)

    lbl_card3 = tk.Label(
        v_hist, text=f"CAJA HISTÓRICA: ${total_hist}",
        bg="#8E44AD", fg="white", font=("Arial", 10, "bold")
    )
    lbl_card3.place(x=440, y=60, width=220, height=35)

    # --- TABLA VISUAL DE ÚLTIMAS VENTAS ---
    lbl_sub_ventas = tk.Label(
        v_hist, text="Últimas Ventas Confirmadas (Más recientes primero):",
        bg="#EAECEE", fg="#2C3E50", font=("Arial", 10, "bold")
    )
    lbl_sub_ventas.place(x=20, y=105)

    # Encabezados de columna de la tabla de ventas
    y_tabla = 130
    tk.Label(v_hist, text="ID", bg="#34495E", fg="white", font=("Arial", 9, "bold")).place(x=20, y=y_tabla, width=45, height=26)
    tk.Label(v_hist, text="CLIENTE", bg="#34495E", fg="white", font=("Arial", 9, "bold")).place(x=67, y=y_tabla, width=155, height=26)
    tk.Label(v_hist, text="FECHA / HORA", bg="#34495E", fg="white", font=("Arial", 9, "bold")).place(x=224, y=y_tabla, width=135, height=26)
    tk.Label(v_hist, text="REM", bg="#34495E", fg="white", font=("Arial", 9, "bold")).place(x=361, y=y_tabla, width=48, height=26)
    tk.Label(v_hist, text="PAN", bg="#34495E", fg="white", font=("Arial", 9, "bold")).place(x=411, y=y_tabla, width=48, height=26)
    tk.Label(v_hist, text="BUZ", bg="#34495E", fg="white", font=("Arial", 9, "bold")).place(x=461, y=y_tabla, width=48, height=26)
    tk.Label(v_hist, text="GOR", bg="#34495E", fg="white", font=("Arial", 9, "bold")).place(x=511, y=y_tabla, width=48, height=26)
    tk.Label(v_hist, text="TOTAL", bg="#34495E", fg="white", font=("Arial", 9, "bold")).place(x=561, y=y_tabla, width=99, height=26)

    ventas = obtener_ultimas_ventas()

    if len(ventas) == 0:
        tk.Label(
            v_hist, text="Aún no se registraron ventas en la base de datos.",
            bg="white", fg="#7F8C8D", font=("Arial", 10, "italic")
        ).place(x=20, y=158, width=640, height=180)
    else:
        y_fila = 158
        for i in range(len(ventas)):
            v = ventas[i]
            color_fondo = "#FFFFFF" if i % 2 == 0 else "#EBF5FB"
            fecha_corta = v[2][4:16] if len(v[2]) >= 16 else v[2]

            tk.Label(v_hist, text=f"#{v[0]}", bg=color_fondo, fg="#2C3E50", font=("Arial", 9, "bold")).place(x=20, y=y_fila, width=45, height=25)
            tk.Label(v_hist, text=v[1], bg=color_fondo, fg="#2C3E50", font=("Arial", 9)).place(x=67, y=y_fila, width=155, height=25)
            tk.Label(v_hist, text=fecha_corta, bg=color_fondo, fg="#566573", font=("Arial", 8)).place(x=224, y=y_fila, width=135, height=25)
            tk.Label(v_hist, text=str(v[3]), bg=color_fondo, fg="#2C3E50", font=("Arial", 9)).place(x=361, y=y_fila, width=48, height=25)
            tk.Label(v_hist, text=str(v[4]), bg=color_fondo, fg="#2C3E50", font=("Arial", 9)).place(x=411, y=y_fila, width=48, height=25)
            tk.Label(v_hist, text=str(v[5]), bg=color_fondo, fg="#2C3E50", font=("Arial", 9)).place(x=461, y=y_fila, width=48, height=25)
            tk.Label(v_hist, text=str(v[6]), bg=color_fondo, fg="#2C3E50", font=("Arial", 9)).place(x=511, y=y_fila, width=48, height=25)
            tk.Label(v_hist, text=f"${v[7]}", bg="#D4EFDF", fg="#145A32", font=("Arial", 9, "bold")).place(x=561, y=y_fila, width=99, height=25)
            y_fila += 27

    # --- TABLA INFERIOR: ÚLTIMOS MOVIMIENTOS DE ENCARGADOS (IN / OUT) ---
    lbl_sub_turnos = tk.Label(
        v_hist, text="Últimos Movimientos de Turno (Tabla Registro):",
        bg="#EAECEE", fg="#2C3E50", font=("Arial", 10, "bold")
    )
    lbl_sub_turnos.place(x=20, y=355)

    registros = obtener_ultimos_registros()
    y_reg = 380

    for r in registros:
        es_entrada = "IN" in str(r[3]) or "Entrada" in str(r[3])
        bg_evento = "#D6EAF8" if es_entrada else "#FADBD8"
        fg_evento = "#1B4F72" if es_entrada else "#78281F"
        fecha_r = r[2][4:16] if len(r[2]) >= 16 else r[2]
        caja_texto = "-" if r[4] is None else f"Caja: ${r[4]}"

        tk.Label(v_hist, text=f"Encargado: {r[1]}", bg="white", fg="#2C3E50", font=("Arial", 9, "bold")).place(x=20, y=y_reg, width=210, height=22)
        tk.Label(v_hist, text=fecha_r, bg="white", fg="#566573", font=("Arial", 8)).place(x=232, y=y_reg, width=150, height=22)
        tk.Label(v_hist, text=r[3], bg=bg_evento, fg=fg_evento, font=("Arial", 9, "bold")).place(x=384, y=y_reg, width=140, height=22)
        tk.Label(v_hist, text=caja_texto, bg="white", fg="#145A32", font=("Arial", 9, "bold")).place(x=526, y=y_reg, width=134, height=22)
        y_reg += 24

    btn_cerrar = tk.Button(
        v_hist, text="Cerrar Panel de Historial",
        bg="#2C3E50", fg="white", font=("Arial", 10, "bold"),
        command=v_hist.destroy
    )
    btn_cerrar.place(x=230, y=490, width=220, height=34)


def seleccionar_encargado_guardado():
    # Cuando el usuario elige un Radiobutton, copia ese nombre en la caja Entry
    elegido = var_encargado_radio.get()
    caja_encargado.delete(0, tk.END)
    caja_encargado.insert(0, elegido)
    var_alerta_inicio.set(f"Encargad@ '{elegido}' seleccionad@.")
    lbl_alerta_login.config(fg="#1B4F72")


def accion_eliminar_encargado():
    # Obtiene el encargado seleccionado en el Radiobutton o escrito en la caja
    elegido = var_encargado_radio.get().strip()
    if elegido == "":
        elegido = caja_encargado.get().strip()

    if elegido == "":
        var_alerta_inicio.set("ERROR: Seleccione primero un encargad@ de la lista para eliminarlo.")
        lbl_alerta_login.config(fg="#C0392B")
        return

    guardados = obtener_encargados_guardados()
    if elegido not in guardados:
        var_alerta_inicio.set(f"ERROR: '{elegido}' no se encuentra en la lista de guardados.")
        lbl_alerta_login.config(fg="#C0392B")
        return

    # Llamamos a la función del Bloque 2 para borrarlo de SQLite
    eliminar_encargado_guardado(elegido)

    # Limpiamos la caja y recargamos los Radiobuttons en pantalla
    caja_encargado.delete(0, tk.END)
    var_encargado_radio.set("")
    cargar_botones_encargados()

    var_alerta_inicio.set(f"Encargad@ '{elegido}' eliminado de la lista de inicio.")
    lbl_alerta_login.config(fg="#C0392B")


def cargar_botones_encargados():
    # Limpiamos los controles previos dentro del contenedor de encargados
    for widget in frame_guardados.winfo_children():
        widget.destroy()

    guardados = obtener_encargados_guardados()
    var_encargado_radio.set("")

    if len(guardados) == 0:
        tk.Label(
            frame_guardados,
            text="No hay encargados guardados actualmente.\nEscriba un nombre arriba e inicie turno para guardarlo.",
            bg="#D6EAF8", fg="#1B4F72", font=("Arial", 9, "italic")
        ).place(x=15, y=40, width=420, height=45)
    else:
        tk.Label(
            frame_guardados,
            text="Encargados guardados (seleccione para ingresar o eliminar):",
            bg="#D6EAF8", fg="#1B4F72", font=("Arial", 9, "bold")
        ).place(x=15, y=6)

        # Ubicamos hasta 6 encargados en 2 columnas usando Radiobutton (Clase 18)
        for i in range(len(guardados)):
            nombre_enc = guardados[i]
            columna = i % 2
            fila = i // 2
            pos_x = 20 + (columna * 210)
            pos_y = 32 + (fila * 27)

            rb = tk.Radiobutton(
                frame_guardados,
                text=nombre_enc,
                variable=var_encargado_radio,
                value=nombre_enc,
                bg="#FFFFFF",
                fg="#2C3E50",
                font=("Arial", 9, "bold"),
                command=seleccionar_encargado_guardado
            )
            rb.place(x=pos_x, y=pos_y, width=195, height=23)

        # Botón para eliminar el encargado seleccionado
        btn_eliminar_enc = tk.Button(
            frame_guardados,
            text="Eliminar Encargad@ Seleccionad@",
            bg="#E74C3C", fg="white", font=("Arial", 9, "bold"),
            command=accion_eliminar_encargado
        )
        btn_eliminar_enc.place(x=115, y=118, width=220, height=26)


def iniciar_turno():
    nombre = caja_encargado.get().strip()
    if nombre == "":
        var_alerta_inicio.set("ERROR: Ingrese un nombre o seleccione un encargad@ guardado.")
        lbl_alerta_login.config(fg="#C0392B")
        return

    estado["encargado"] = nombre
    estado["total_turno"] = 0

    registroEntrada(nombre)

    caja_encargado.delete(0, tk.END)
    var_alerta_inicio.set("")
    actualizar_datos_menu()

    frame_login.place_forget()
    frame_menu.place(x=0, y=0, width=520, height=480)


def cambiar_turno():
    registroSalida(estado["encargado"], estado["total_turno"])

    var_alerta_inicio.set(
        f"Turno de {estado['encargado']} cerrado (Caja: ${estado['total_turno']}). "
        "Seleccione o ingrese nuevo encargad@."
    )
    lbl_alerta_login.config(fg="#145A32")

    estado["encargado"] = ""
    estado["total_turno"] = 0

    cargar_botones_encargados()

    frame_menu.place_forget()
    frame_login.place(x=0, y=0, width=520, height=480)


def salir_sistema():
    if estado["encargado"] != "":
        registroSalida(estado["encargado"], estado["total_turno"])
    conn.close()
    ventana_principal.destroy()


def actualizar_datos_menu():
    var_info_encargado.set(f"Encargad@ en Turno (IN): {estado['encargado']}")
    var_info_turno.set(f"Recaudación del Turno Actual: ${estado['total_turno']}")
    total_historico = obtener_total_historico()
    var_info_historico.set(f"Total General Vendido (Histórico BD): ${total_historico}")


# --- Construcción de la Ventana Principal ---
ventana_principal = tk.Tk()
ventana_principal.title("Sistema de Gestión - Tienda de Ropa IT")
ventana_principal.config(width=520, height=480, bg="#ECF0F1")

# Variables dinámicas StringVar para actualizar etiquetas y Radiobuttons (Clase 18)
var_alerta_inicio = tk.StringVar()
var_encargado_radio = tk.StringVar()
var_info_encargado = tk.StringVar()
var_info_turno = tk.StringVar()
var_info_historico = tk.StringVar()

# --- PANEL 1: INICIO DE TURNO (CON SELECCIÓN Y ELIMINACIÓN DE ENCARGADOS) ---
frame_login = tk.Frame(ventana_principal, bg="#ECF0F1")
frame_login.place(x=0, y=0, width=520, height=480)

lbl_bienvenida = tk.Label(
    frame_login, text="TIENDA DE ROPA IT - CONTROL DE TURNOS",
    bg="#1F3A52", fg="white", font=("Arial", 13, "bold")
)
lbl_bienvenida.place(x=25, y=18, width=470, height=42)

lbl_ingrese = tk.Label(
    frame_login, text="Nombre del Encargad@ (escriba uno nuevo o elija abajo):",
    bg="#ECF0F1", fg="#2C3E50", font=("Arial", 10, "bold")
)
lbl_ingrese.place(x=35, y=72)

caja_encargado = tk.Entry(frame_login, font=("Arial", 11))
caja_encargado.place(x=35, y=98, width=280, height=32)

btn_ingresar = tk.Button(
    frame_login, text="Iniciar Turno (IN)",
    bg="#27AE60", fg="white", font=("Arial", 10, "bold"),
    command=iniciar_turno
)
btn_ingresar.place(x=325, y=98, width=160, height=32)

# Panel de encargados guardados en Base de Datos (usa Radiobuttons + Botón Eliminar)
frame_guardados = tk.Frame(frame_login, bg="#D6EAF8")
frame_guardados.place(x=35, y=145, width=450, height=152)

cargar_botones_encargados()

lbl_alerta_login = tk.Label(
    frame_login, textvariable=var_alerta_inicio,
    bg="#ECF0F1", fg="#C0392B", font=("Arial", 9, "bold")
)
lbl_alerta_login.place(x=25, y=310, width=470, height=28)

btn_historial_login = tk.Button(
    frame_login, text="Ver Historial de Ventas y Turnos",
    bg="#8E44AD", fg="white", font=("Arial", 10, "bold"),
    command=abrir_ventana_historial
)
btn_historial_login.place(x=55, y=355, width=230, height=36)

btn_salir_login = tk.Button(
    frame_login, text="Apagar Sistema",
    bg="#7F8C8D", fg="white", font=("Arial", 10, "bold"),
    command=salir_sistema
)
btn_salir_login.place(x=300, y=355, width=165, height=36)


# --- PANEL 2: PANTALLA PRINCIPAL (MENÚ) ---
frame_menu = tk.Frame(ventana_principal, bg="#ECF0F1")

lbl_menu_titulo = tk.Label(
    frame_menu, text="PANEL PRINCIPAL - TIENDA DE ROPA IT",
    bg="#1F3A52", fg="white", font=("Arial", 12, "bold")
)
lbl_menu_titulo.place(x=35, y=20, width=450, height=40)

lbl_encargado_activo = tk.Label(
    frame_menu, textvariable=var_info_encargado,
    bg="#D6EAF8", fg="#1B4F72", font=("Arial", 11, "bold")
)
lbl_encargado_activo.place(x=35, y=70, width=450, height=30)

lbl_recaudacion_turno = tk.Label(
    frame_menu, textvariable=var_info_turno,
    bg="#D4EFDF", fg="#145A32", font=("Arial", 10, "bold")
)
lbl_recaudacion_turno.place(x=35, y=105, width=450, height=28)

lbl_recaudacion_total = tk.Label(
    frame_menu, textvariable=var_info_historico,
    bg="#FCF3CF", fg="#7D6608", font=("Arial", 10, "bold")
)
lbl_recaudacion_total.place(x=35, y=138, width=450, height=28)

btn_nuevo_pedido = tk.Button(
    frame_menu, text="1 - Nuevo Pedido",
    bg="#2980B9", fg="white", font=("Arial", 11, "bold"),
    command=abrir_ventana_pedido
)
btn_nuevo_pedido.place(x=135, y=185, width=250, height=42)

btn_historial = tk.Button(
    frame_menu, text="★ Historial de Ventas y Turnos",
    bg="#8E44AD", fg="white", font=("Arial", 10, "bold"),
    command=abrir_ventana_historial
)
btn_historial.place(x=135, y=240, width=250, height=38)

btn_cambio_turno = tk.Button(
    frame_menu, text="2 - Cambio de Turno (OUT / IN)",
    bg="#D35400", fg="white", font=("Arial", 11, "bold"),
    command=cambiar_turno
)
btn_cambio_turno.place(x=135, y=290, width=250, height=42)

btn_salir_menu = tk.Button(
    frame_menu, text="3 - Salir (Apagar Sistema)",
    bg="#C0392B", fg="white", font=("Arial", 11, "bold"),
    command=salir_sistema
)
btn_salir_menu.place(x=135, y=345, width=250, height=42)

ventana_principal.protocol("WM_DELETE_WINDOW", salir_sistema)
ventana_principal.mainloop()