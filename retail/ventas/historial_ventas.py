import tkinter as tk
from tkinter import ttk, messagebox
from retail.core.database import (
    get_connection,
    registrar_historial_venta,
)
import datetime
import os
from PIL import Image, ImageTk

def abrir_historial_ventas(parent, id_ventas=None, nombre_cliente="Cliente", facturas_window=None):
    """
    Muestra el historial de ventas para una venta específica.
    """
    # --- Obtener el nombre real del cliente si se pasa un id ---
    nombre_mostrar = nombre_cliente
    id_cliente = None
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            if str(nombre_cliente).isdigit():
                id_cliente = int(nombre_cliente)
                cursor.execute("SELECT nombres, apellidos FROM clientes WHERE id_cliente = ?", (id_cliente,))
                res = cursor.fetchone()
                if res:
                    nombre_mostrar = f"{res[0]} {res[1]}"
            else:
                cursor.execute("SELECT id_cliente, nombres, apellidos FROM clientes WHERE (nombres || ' ' || apellidos) = ?", (nombre_cliente,))
                res = cursor.fetchone()
                if res:
                    id_cliente = res[0]
                    nombre_mostrar = f"{res[1]} {res[2]}"
    except Exception:
        pass

    ventana = tk.Toplevel(parent)
    ventana.title(f"Historial de Venta Para: {nombre_mostrar}")
    ventana.geometry("1000x600+180+30")
    ventana.configure(bg="#E6D9E3")
    # Comportamiento modal y siempre encima (consistente con el Carrito)
    ventana.resizable(False, False)
    try:
        ventana.transient(parent)
    except Exception:
        pass
    try:
        ventana.grab_set()
    except Exception:
        pass
    try:
        ventana.attributes("-topmost", True)
    except Exception:
        pass

    var_total = tk.StringVar(value="$0")
    var_total_stock = tk.StringVar(value="0")

    label_titulo = tk.Label(
        ventana,
        text=f"Historial de Venta Para: {nombre_mostrar}",
        font=("Helvetica", 17, "bold"),
        bg="#8e24aa",
        fg="white",
        pady=12
    )
    label_titulo.pack(fill="x")

    frame_tabla = tk.Frame(ventana, bg="#F5F5F5")
    frame_tabla.pack(padx=30, pady=(20, 5), fill="both", expand=True)

    columnas = ("ID", "N°", "Producto", "Día", "Fecha", "Hora", "Stock", "Subtotal", "Acción")
    tree = ttk.Treeview(
        frame_tabla,
        columns=columnas,
        show="headings",
        height=10,
    )
    for col, ancho in zip(columnas, [0, 60, 220, 90, 120, 90, 90, 120, 140]):
        tree.heading(col, text=col)
        tree.column(col, width=ancho, anchor="center")
    tree.column("ID", width=0, stretch=tk.NO)

    scrollbar_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=tree.yview)
    scrollbar_x = ttk.Scrollbar(frame_tabla, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar_y.grid(row=0, column=1, sticky="ns")
    scrollbar_x.grid(row=1, column=0, sticky="ew")

    frame_tabla.grid_rowconfigure(0, weight=1)
    frame_tabla.grid_columnconfigure(0, weight=1)

    def _on_mousewheel(event):
        tree.yview_scroll(int(-1 * (event.delta / 120)), "units")
    tree.bind("<Enter>", lambda e: tree.bind_all("<MouseWheel>", _on_mousewheel))
    tree.bind("<Leave>", lambda e: tree.unbind_all("<MouseWheel>"))

    frame_totales = tk.Frame(ventana, bg="#E6D9E3")
    frame_totales.pack(fill="x", padx=30, pady=(0, 15))

    ruta_img = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "img"))
    try:
        img_delete = ImageTk.PhotoImage(Image.open(os.path.join(ruta_img, "eliminar.png")).resize((28, 28)))
    except Exception:
        img_delete = None

    btn_eliminar = tk.Button(
        frame_totales,
        text="  Eliminar",
        image=img_delete,
        compound="left",
        font=("Helvetica", 13, "bold"),
        bg="#F44336",
        fg="white",
        activebackground="#B71C1C",
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=10,
        pady=4,
        anchor="center"
    )
    btn_eliminar.image = img_delete
    btn_eliminar.pack(side="left", padx=(0, 20), pady=0)

    frame_totales_derecha = tk.Frame(frame_totales, bg="#f3e5f5", bd=2, relief="groove")
    frame_totales_derecha.pack(side="right", padx=(0, 10), pady=2)

    tk.Label(
        frame_totales_derecha,
        text="Total Stock:",
        font=("Helvetica", 13, "bold"),
        bg="#f3e5f5",
        fg="#333"
    ).grid(row=0, column=0, sticky="e", padx=(10, 4), pady=6)
    tk.Label(
        frame_totales_derecha,
        textvariable=var_total_stock,
        font=("Helvetica", 13, "bold"),
        bg="#f3e5f5",
        fg="#008B8B",
        width=8
    ).grid(row=0, column=1, sticky="w", padx=(0, 16), pady=6)

    tk.Label(
        frame_totales_derecha,
        text="Total Vendido:",
        font=("Helvetica", 14, "bold"),
        bg="#f3e5f5",
        fg="#333"
    ).grid(row=0, column=2, sticky="e", padx=(10, 4), pady=6)
    tk.Label(
        frame_totales_derecha,
        textvariable=var_total,
        font=("Helvetica", 15, "bold"),
        bg="#f3e5f5",
        fg="#4CAF50",
        width=14
    ).grid(row=0, column=3, sticky="w", padx=(0, 10), pady=6)

    def eliminar_registro():
        seleccionado = tree.selection()
        if not seleccionado:
            messagebox.showwarning("Advertencia", "Seleccione un registro para eliminar.", parent=ventana)
            return

        item = seleccionado[0]
        valores = tree.item(item, "values")
        id_historial, _, producto, _, fecha, hora, _, _, _ = valores

        if not messagebox.askyesno(
            "Confirmar",
            f"¿Está seguro de eliminar el registro de '{producto}' del {fecha}?",
            parent=ventana,
        ):
            return

        try:
            # 1. Obtener los datos del historial para encontrar el detalle de venta
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id_ventas, id_producto, cantidad, subtotal FROM historial_ventas WHERE id_historial = ?",
                    (id_historial,)
                )
                res = cursor.fetchone()
                if not res:
                    messagebox.showerror("Error", "No se encontró el registro en el historial.", parent=ventana)
                    return

                id_ventas, id_producto, cantidad, subtotal = res

                # 2. Encontrar el id_detalle para una eliminación precisa
                cursor.execute(
                    "SELECT id_detalle FROM detalle_venta WHERE id_ventas = ? AND id_producto = ? AND cantidad = ? AND subtotal = ? LIMIT 1",
                    (id_ventas, id_producto, cantidad, subtotal)
                )
                detalle_res = cursor.fetchone()
                if not detalle_res:
                    messagebox.showerror("Error", "No se pudo encontrar el detalle de venta correspondiente para eliminar.", parent=ventana)
                    return

                id_detalle = detalle_res[0]

                # 3. Eliminar el detalle de la venta usando su ID único
                cursor.execute("DELETE FROM detalle_venta WHERE id_detalle = ?", (id_detalle,))

                # 4. Restaurar el stock en el inventario
                cursor.execute(
                    "UPDATE inventario SET stock = stock + ? WHERE id_producto = ?",
                    (cantidad, id_producto)
                )

                # 5. Recalcular el total de la venta y actualizar la tabla 'ventas'
                cursor.execute("SELECT COUNT(*) FROM detalle_venta WHERE id_ventas = ?", (id_ventas,))
                detalles_restantes = cursor.fetchone()[0]
                if detalles_restantes == 0:
                    # Si no quedan productos, eliminar la venta y su historial
                    cursor.execute("DELETE FROM ventas WHERE id_ventas = ?", (id_ventas,))
                    cursor.execute("DELETE FROM historial_ventas WHERE id_ventas = ?", (id_ventas,))
                else:
                    # Si quedan productos, actualizar el total
                    cursor.execute("SELECT SUM(subtotal) FROM detalle_venta WHERE id_ventas = ?", (id_ventas,))
                    nuevo_total = cursor.fetchone()[0] or 0
                    cursor.execute("UPDATE ventas SET total = ? WHERE id_ventas = ?", (nuevo_total, id_ventas))
                # 7. Eliminar el registro del historial de ventas por completo
                cursor.execute("DELETE FROM historial_ventas WHERE id_historial = ?", (id_historial,))
                conn.commit()

            # 8. Actualizar la interfaz gráfica inmediatamente
            # Quitar la fila eliminada de inmediato
            valores_fila = tree.item(item, "values")
            subtotal_fila = valores_fila[7]
            cantidad_fila = valores_fila[6]
            try:
                subtotal_num = float(subtotal_fila.replace("$", "").replace(".", "").replace(",", ".")) if subtotal_fila else 0
            except Exception:
                subtotal_num = 0
            try:
                cantidad_num = int(cantidad_fila) if cantidad_fila else 0
            except Exception:
                cantidad_num = 0
            tree.delete(item)
            # Actualizar totales inmediatamente
            try:
                total_actual = float(var_total.get().replace("$", "").replace(".", "").replace(",", "."))
            except Exception:
                total_actual = 0
            try:
                total_stock_actual = int(var_total_stock.get())
            except Exception:
                total_stock_actual = 0
            nuevo_total = max(0, total_actual - subtotal_num)
            nuevo_total_stock = max(0, total_stock_actual - cantidad_num)
            var_total.set(f"${nuevo_total:,.0f}".replace(",", "."))
            var_total_stock.set(str(nuevo_total_stock))
            if facturas_window:
                facturas_window.cargar_facturas()
            messagebox.showinfo("Éxito", "El registro ha sido eliminado correctamente.", parent=ventana)

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al eliminar el registro: {e}", parent=ventana)

    btn_eliminar.config(command=eliminar_registro)

    def cargar_historial():
        tree.delete(*tree.get_children())
        from retail.core.database import obtener_historial_por_venta
        try:
            if id_cliente is not None:
                # Buscar ventas solo para ese id_cliente, asegurando no duplicar registros
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                            SELECT h.id_historial, i.producto, h.fecha, h.hora, h.cantidad, h.subtotal, h.accion
                            FROM historial_ventas h
                            LEFT JOIN inventario i ON h.id_producto = i.id_producto
                            LEFT JOIN ventas v ON h.id_ventas = v.id_ventas
                            WHERE v.cliente_venta = ?
                            ORDER BY h.fecha DESC, h.hora DESC
                            """,
                        (id_cliente,)
                    )
                    rows = cursor.fetchall()
            else:
                # Fallback: usar la función original (por id_ventas)
                rows = obtener_historial_por_venta(id_ventas)
        except Exception:
            rows = []
        total = 0
        total_stock = 0
        dias = [
            "Lunes",
            "Martes",
            "Miércoles",
            "Jueves",
            "Viernes",
            "Sábado",
            "Domingo",
        ]
        for idx, (id_historial, producto, fecha, hora, cantidad, subtotal, accion) in enumerate(
            rows, start=1
        ):
            try:
                fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
                dia_semana = dias[fecha_dt.weekday()]
            except Exception:
                dia_semana = ""
            # Para mostrar correctamente: los abonos no deben restar el Total Vendido
            # Mostrar el subtotal de abonos como positivo, pero no sumarlos en Total Vendido
            try:
                if accion == 'Abono':
                    display_subtotal = abs(float(subtotal)) if subtotal is not None else 0
                else:
                    display_subtotal = float(subtotal) if subtotal is not None else 0
            except Exception:
                # fallback seguro
                display_subtotal = float(subtotal) if subtotal is not None else 0

            # Sumar al total solo si no es un Abono
            try:
                if accion != 'Abono':
                    total += float(subtotal) if subtotal is not None else 0
            except Exception:
                pass

            total_stock += int(cantidad) if cantidad is not None else 0
            tree.insert(
                "",
                "end",
                values=(
                    id_historial,
                    idx,
                    producto if producto is not None else ("" if accion != 'Abono' else "Abono"),
                    dia_semana,
                    fecha,
                    hora,
                    cantidad if cantidad is not None else "",
                    f"${display_subtotal:,.0f}".replace(",", ".")
                    if subtotal is not None
                    else "",
                    accion,
                ),
            )
        var_total.set(f"${total:,.0f}".replace(",", "."))
        var_total_stock.set(str(total_stock))

    cargar_historial()
