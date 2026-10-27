# INTEGRADOR II - FINAL: Tienda de Ropa IT (Tkinter + SQLite)

## 1. Carátula

* **Universidad / Institución:** Centro Regional Universitario de Ituzaingó (CRUI)
* **Materia:** Programación en Python - Integrador II Final
* **Docente:** Profesora Inés del Castillo
* **Tema:** Opción 3 - Tienda de Ropa (Interfaz Gráfica con Tkinter y Base de Datos SQLite)
* **Integrantes del Grupo:**
  * Arispe Gabriel
  * López Cristian
  * Loza Valentina
  * Lucero Germán
  * Zarate Benito Elías

---

## 2. Enunciado del Tema o Problema

El objetivo del trabajo consiste en desarrollar una interfaz gráfica de usuario (GUI) utilizando la biblioteca estándar **Tkinter** para el sistema de gestión de ventas y control de turnos de una **Tienda de Ropa**, manteniendo la lógica del sistema originalmente implementado en consola y su persistencia en base de datos **SQLite** (`comercio.sql`), mejorando la experiencia del usuario.

El comercio registra ventas de cuatro productos: **Remera ($10)**, **Pantalón ($20)**, **Buzo ($25)** y **Gorra ($8)**. El sistema gráfico implementa las siguientes funcionalidades obligatorias y extras:

1. **Inicio y Gestión de Turnos (IN / OUT):** Permite ingresar el nombre de un nuevo encargado o seleccionar uno previamente guardado mediante botones de opción (`tk.Radiobutton`), así como eliminar encargados de la lista de acceso rápido sin perder su historial contable. Cada inicio y cierre de turno se registra en la tabla `registro` de SQLite.
2. **Menú Principal Gráfico:** Muestra en tiempo real el encargado activo, la recaudación del turno actual y el total histórico acumulado mediante variables de control (`tk.StringVar`), junto con los botones de acceso a **Nuevo Pedido**, **Historial de Ventas y Turnos**, **Cambio de Turno** y **Salir**.
3. **Carga de Nuevo Pedido:** Despliega una ventana secundaria (`tk.Toplevel`) con campos de texto (`tk.Entry`) para el nombre del cliente y las cantidades de cada prenda, una casilla de verificación (`tk.Checkbutton` con `tk.IntVar`) para aplicar el descuento opcional del 10%, botón de cálculo de subtotal/total, cálculo automático de vuelto y confirmación con guardado en la tabla `venta`.
4. **Dashboard de Historial y Validaciones Visuales (Extras):** Incluye una ventana con indicadores de resumen (KPIs), tabla estilizada de las últimas ventas ordenadas con `reversed()` y listado de movimientos de caja, además de alertas visuales por colores que impiden que el programa se rompa ante ingresos inválidos.

---

## 3. Prueba de Escritorio

*(Nota: Ejecutar el programa con estos casos de prueba y adjuntar las capturas de pantalla correspondientes debajo de cada punto antes de exportar a PDF)*.

| Caso de Prueba | Acción en la Interfaz Gráfica | Datos de Entrada | Resultado Obtenido (Pantalla y Base de Datos) |
| :--- | :--- | :--- | :--- |
| **1. Alta e Inicio de Turno (IN)** | Se escribe el nombre del encargado y se presiona **"Iniciar Turno (IN)"**. | Encargado: `Cristian` | Se inserta `IN - Entrada` en la tabla `registro` y se guarda el nombre en `encargado_guardado`. Se abre el Menú Principal con recaudación en `$0`. |
| **2. Validación de Datos No Numéricos** | En **"Nuevo Pedido"**, se ingresa texto en una cantidad y se presiona **"1. Calcular Total"**. | Remera: `dos` | El sistema evalúa `.isdecimal()`, evita el `ValueError` y muestra alerta roja: *"ERROR: Las cantidades deben ser números enteros positivos"*. |
| **3. Pedido con Descuento del 10%** | Se cargan prendas, se marca el `Checkbutton` de descuento y se presiona **"1. Calcular Total"**. | Cliente: `Valentina`<br>Remera: `2` ($20)<br>Buzo: `1` ($25)<br>Descuento: `Activado (1)` | Se calcula Subtotal `$45`. Al estar `var_descuento.get() == 1`, aplica `round(45 * 0.9)` y muestra: **TOTAL A PAGAR: `$40`**. |
| **4. Control de Pago Insuficiente** | Se ingresa un monto menor al total en *"Abona con $"* y se presiona **"2. Calcular Vuelto"**. | Abona con: `30` | Alerta roja: *"El monto no alcanza. Faltan $10"*. Bloquea la confirmación del pedido hasta ingresar un pago válido. |
| **5. Cobro, Vuelto y Confirmación** | Se ingresa un monto válido, se calcula el vuelto y se presiona **"3. Confirmar y Guardar Pedido"**. | Abona con: `50` | Muestra *"Vuelto a entregar: $10"*. Guarda el registro en la tabla `venta`, cierra la ventana y suma `$40` a la recaudación del turno. |
| **6. Cambio de Turno (OUT)** | En el Menú Principal se presiona **"2 - Cambio de Turno (OUT / IN)"**. | — | Registra `OUT - Salida` en la tabla `registro` con `caja = 40.0`. Vuelve al login mostrando a `Cristian` como `Radiobutton` guardado. |
| **7. Eliminación de Encargado Guardado** | En el login se selecciona el `Radiobutton` del encargado y se toca **"Eliminar Encargad@ Seleccionad@"**. | Selección: `Cristian` | Se ejecuta `DELETE FROM encargado_guardado`. El botón desaparece del inicio, pero sus ventas y turnos continúan intactos en el Historial. |

---

## 4. Diagrama de Resolución y Diagrama de Ventanas

### 4.1. Diagrama de Ventanas (Navegación de la Interfaz)

```
+-----------------------------------------------------------------------+
|                    VENTANA PRINCIPAL (tk.Tk)                          |
|                                                                       |
|  [PANEL 1: LOGIN Y GESTIÓN DE ENCARGADOS]                             |
|   - Entry: Ingreso de nuevo encargado                                 |
|   - Radiobuttons (tk.StringVar): Selección de encargados guardados    |
|   - Botón: "Eliminar Encargad@ Seleccionad@" (Baja en acceso rápido)  |
|   - Botón: "Iniciar Turno (IN)" (Registra Entrada en SQLite)          |
+-----------------------------------+-----------------------------------+
                                    |
                                    v (Oculta Panel 1 / Muestra Panel 2)
+-----------------------------------------------------------------------+
|  [PANEL 2: MENÚ PRINCIPAL]                                            |
|   - Labels dinámicos (tk.StringVar):                                  |
|     Encargado activo, Recaudación del Turno y Total Histórico BD      |
|   - Botón "1 - Nuevo Pedido"          ---> Abre Toplevel Nuevo Pedido |
|   - Botón "★ Historial de Ventas"     ---> Abre Toplevel Dashboard    |
|   - Botón "2 - Cambio de Turno"       ---> Registra OUT y va a Panel 1|
|   - Botón "3 - Salir (Apagar)"        ---> Registra OUT y cierra BD   |
+-----------------------------------------------------------------------+
```

### 4.2. Diagrama de Flujo de Datos (DFD - Proceso de Venta)

```
[Abrir Ventana Nuevo Pedido]
             |
             v
[Ingresar Cliente, Cantidades (Entry) y Checkbutton 10% (IntVar)]
             |
             v
< ¿Cantidades válidas con .isdecimal() y Subtotal > 0? >
   |-- NO --> [Mostrar Alerta Roja en Label (StringVar)]
   |-- SÍ --> [Calcular Subtotal y aplicar 10% si IntVar == 1]
                           |
                           v
              [Ingresar monto en "Abona con $" (Entry)]
                           |
                           v
              < ¿Monto es numérico y Pago >= Total? >
                 |-- NO --> [Mostrar Alerta: "Faltan $X"]
                 |-- SÍ --> [Calcular Vuelto = Pago - Total]
                                         |
                                         v
                            [Presionar "Confirmar y Guardar"]
                                         |
                                         v
                            [INSERT INTO venta + Actualizar Turno]
                                         |
                                         v
                            [Destruir ventana Toplevel y refrescar Menú]
```

---

## 5. Dificultades Encontradas y Soluciones Implementadas

1. **Bloqueo de la interfaz gráfica al migrar los ciclos `while True` de consola:**
   * **Problema:** En el programa original de consola, la función `pedir_entero()` utilizaba un bucle `while True` con `input()` para exigir un número válido. Al trasladar esa lógica a Tkinter, el bucle retenía el hilo de ejecución y congelaba la ventana principal.
   * **Solución:** Se reemplazaron los ciclos por funciones disparadas mediante el atributo `command=` de los botones (`tk.Button`) y se implementó la función `convertir_entero(dato)` apoyada en el método `.isdecimal()` visto en la Clase 18, mostrando los mensajes de error en etiquetas visuales sin detener la aplicación.

2. **Actualización en tiempo real de importes, vueltos y alertas:**
   * **Problema:** Al modificar las cantidades o registrar nuevas ventas, los widgets `tk.Label` mantenían el texto estático inicial y no reflejaban los nuevos cálculos.
   * **Solución:** Se incorporaron las variables de control `tk.StringVar()` vinculadas con `textvariable=` para actualizar dinámicamente los subtotales, vueltos y alertas de estado, y una variable `tk.IntVar()` vinculada al `tk.Checkbutton` para detectar si correspondía aplicar el 10% de descuento.

3. **Eliminación de encargados frecuentes sin alterar el historial contable:**
   * **Problema:** Si se eliminaban los nombres de los encargados ejecutando un `DELETE` sobre la tabla `registro`, se borraban también las auditorías de turnos anteriores y los cierres de caja históricos.
   * **Solución:** Se creó una tercera tabla independiente en SQLite llamada `encargado_guardado`. De esta forma, al seleccionar un `tk.Radiobutton` y presionar *"Eliminar Encargad@ Seleccionad@"*, únicamente se da de baja del listado de inicio rápido, preservando intactos todos los registros de entrada/salida en la tabla `registro`.

4. **Pérdida del cierre de turno al cerrar la ventana desde la "X" del sistema operativo:**
   * **Problema:** Si el usuario cerraba la ventana directamente desde el botón `"X"` de Windows en lugar de usar el botón *"3 - Salir"*, el programa finalizaba sin guardar la salida (`OUT`) ni la recaudación del encargado en turno.
   * **Solución:** Se capturó el evento de cierre mediante `ventana_principal.protocol("WM_DELETE_WINDOW", salir_sistema)`, garantizando que siempre se registre el movimiento `OUT - Salida` y se ejecute `conn.close()` antes de destruir la ventana.


## 6. Estructura para la Presentación (Diapositivas - Exposición de 2 minutos)

### Diapositiva 1: Portada
* **Título:** Sistema de Gestión Gráfica - Tienda de Ropa IT
* **Subtítulo:** Trabajo Práctico Integrador II - Final (Python + Tkinter + SQLite)
* **Institución:** Centro Regional Universitario de Ituzaingó (CRUI) - Prof. Inés del Castillo
* **Integrantes:** Arispe Gabriel, López Cristian, Loza Valentina, Lucero Germán y Zarate Benito Elías.

### Diapositiva 2: Objetivo y Arquitectura de Datos
* **Migración de Consola a GUI:** Reemplazo de `input()` y `print()` por controles interactivos de Tkinter posicionados con `.place()`.
* **Persistencia en SQLite (`comercio.sql`):**
  * Tabla `venta`: Registra cliente, fecha, cantidades por prenda y total cobrado.
  * Tabla `registro`: Audita entradas (`IN`) y salidas (`OUT`) con el cierre de caja de cada turno.
  * Tabla `encargado_guardado`: Almacena los encargados frecuentes para reingreso rápido o baja sin alterar la auditoría histórica.

### Diapositiva 3: Flujo de Pantallas y Controles Aplicados (Clase 18)
* **Pantalla de Inicio:** Selección rápida de encargados con `tk.Radiobutton` y `tk.StringVar`, alta automática y botón de baja.
* **Menú Principal:** Indicadores en vivo de turno actual y acumulado histórico.
* **Ventana de Nuevo Pedido:** Cajas `tk.Entry`, descuento del 10% con `tk.Checkbutton` y `tk.IntVar`, cálculo automático de vuelto y confirmación.

### Diapositiva 4: Funcionalidades Extras y Validaciones
* **Validación sin bloqueos:** Uso de `.isdecimal()` para impedir cierres abruptos (`ValueError`) y alertas visuales dinámicas por colores.
* **Dashboard de Historial:** Visualización de tarjetas de resumen (KPIs), tabla de últimas ventas y movimientos de turno ordenados mediante `reversed()`.
* **Cierre Seguro:** Captura del evento de cierre de ventana (`WM_DELETE_WINDOW`) para asegurar el guardado del turno activo antes de desconectar SQLite.