import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from retail.core.database import (
    get_connection,
    registrar_historial_deuda,
    obtener_historial_deudas,
)
import datetime
import os
from PIL import Image, ImageTk


def abrir_historial_deudas(parent, nombre_cliente="Cliente", cliente_rapido=None, id_deuda=None):
    """
    Muestra el historial de deudas para un cliente (nombre completo o cliente_rapido) o para una deuda específica.
    Si se pasa id_deuda, solo muestra los productos de esa deuda.
    """

    # Obtener nombre a mostrar (igual que historial_ventas)
    nombre_mostrar = nombre_cliente
    cliente_rapido_mostrar = cliente_rapido if cliente_rapido is not None else nombre_cliente
    id_cliente = None
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Si es un id_cliente, úsalo
            if str(nombre_cliente).isdigit():
                id_cliente = int(nombre_cliente)
                cursor.execute("SELECT nombres, apellidos FROM clientes WHERE id_cliente = ?", (id_cliente,))
                res = cursor.fetchone()
                if res:
                    nombre_mostrar = f"{res[0]} {res[1]}"
            else:
                # Buscar el id_cliente por nombre completo exacto
                cursor.execute("SELECT id_cliente, nombres, apellidos FROM clientes WHERE (nombres || ' ' || apellidos) = ?", (nombre_cliente,))
                res = cursor.fetchone()
                if res:
                    id_cliente = res[0]
                    nombre_mostrar = f"{res[1]} {res[2]}"
    except Exception:
        pass

    # Si no se proporcionó id_deuda, pero queremos mostrar el historial de UN registro
    # específico (evitar mezclar abonos entre múltiples deudas del mismo cliente),
    # buscar deudas existentes para este cliente y pedir selección si hay más de una.
    if id_deuda is None:
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                if id_cliente is not None:
                    cursor.execute(
                        "SELECT id_deuda, fecha, hora, total FROM deudas WHERE cliente = ? ORDER BY id_deuda ASC",
                        (id_cliente,),
                    )
                else:
                    cursor.execute(
                        "SELECT id_deuda, fecha, hora, total FROM deudas WHERE cliente_rapido = ? ORDER BY id_deuda ASC",
                        (cliente_rapido_mostrar,),
                    )
                deudas_disponibles = cursor.fetchall()
            # Si hay más de una deuda, pedir al usuario que elija cuál abrir
            if len(deudas_disponibles) > 1:
                sel_win = tk.Toplevel(parent)
                sel_win.title("Seleccionar deuda")
                sel_win.geometry("520x300+250+180")
                sel_win.configure(bg="#F5F5F5")
                try:
                    sel_win.transient(parent)
                except Exception:
                    pass
                try:
                    sel_win.grab_set()
                except Exception:
                    pass
                try:
                    sel_win.attributes("-topmost", True)
                except Exception:
                    pass

                tv = ttk.Treeview(sel_win, columns=("id", "fecha", "hora", "total"), show="headings")
                tv.heading("id", text="ID")
                tv.heading("fecha", text="Fecha")
                tv.heading("hora", text="Hora")
                tv.heading("total", text="Total")
                tv.column("id", width=80, anchor="center")
                tv.column("fecha", width=120, anchor="center")
                tv.column("hora", width=100, anchor="center")
                tv.column("total", width=120, anchor="e")
                for d in deudas_disponibles:
                    tid = str(d[0])
                    total_fmt = f"${d[3]:,.0f}".replace(",", ".") if d[3] is not None else ""
                    tv.insert("", "end", iid=tid, values=(d[0], d[1], d[2], total_fmt))
                tv.pack(fill="both", expand=True, padx=8, pady=8)

                def _abrir_seleccion():
                    sel = tv.selection()
                    if not sel:
                        messagebox.showwarning("Seleccione", "Seleccione una deuda para ver su historial.", parent=sel_win)
                        return
                    nonlocal id_deuda
                    id_deuda = int(sel[0])
                    sel_win.destroy()

                btnf = tk.Frame(sel_win, bg="#F5F5F5")
                btnf.pack(pady=8)
                tk.Button(btnf, text="Abrir historial", command=_abrir_seleccion, bg="#1976D2", fg="white").pack(side="left", padx=8)
                tk.Button(btnf, text="Cancelar", command=sel_win.destroy).pack(side="left", padx=8)
                sel_win.wait_window()
            elif len(deudas_disponibles) == 1:
                id_deuda = deudas_disponibles[0][0]
        except Exception:
            # En caso de cualquier error, continuar y mostrar historial por cliente (existente comportamiento)
            pass

    ventana = tk.Toplevel(parent)
    ventana.title(f"Historial de Deuda Para: {nombre_mostrar}")
    ventana.geometry("1000x600+180+30")
    ventana.configure(bg="#E6D9E3")
    # Comportamiento modal y siempre encima (como el Carrito): no redimensionable, grab y topmost
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
    var_total_cantidad = tk.StringVar(value="0")

    label_titulo = tk.Label(
        ventana,
        text=f"Historial de Deuda Para: {nombre_mostrar}",
        font=("Helvetica", 17, "bold"),
        bg="#8e24aa",
        fg="white",
        pady=12
    )
    label_titulo.pack(fill="x")

    frame_tabla = tk.Frame(ventana, bg="#F5F5F5")
    frame_tabla.pack(padx=30, pady=(20, 5), fill="both", expand=True)

    columnas = ("ID", "N°", "Producto", "Día", "Fecha", "Hora", "Cantidad", "Subtotal", "Acción")
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
        bg="#B71C1C",
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

    # Botón Abono (pago parcial)
    btn_abono = tk.Button(
        frame_totales,
        text="  Abono",
        image=None,
        compound="left",
        font=("Helvetica", 13, "bold"),
        bg="#1976D2",
        fg="white",
        activebackground="#1976D2",
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=10,
        pady=4,
        anchor="center"
    )
    btn_abono.pack(side="left", padx=(0, 10), pady=0)


    frame_totales_derecha = tk.Frame(frame_totales, bg="#f3e5f5", bd=2, relief="groove")
    frame_totales_derecha.pack(side="right", padx=(0, 10), pady=2)

    tk.Label(
        frame_totales_derecha,
        text="Total Cantidad:",
        font=("Helvetica", 13, "bold"),
        bg="#f3e5f5",
        fg="#333"
    ).grid(row=0, column=0, sticky="e", padx=(10, 4), pady=6)
    tk.Label(
        frame_totales_derecha,
        textvariable=var_total_cantidad,
        font=("Helvetica", 13, "bold"),
        bg="#f3e5f5",
        fg="#008B8B",
        width=8
    ).grid(row=0, column=1, sticky="w", padx=(0, 16), pady=6)

    tk.Label(
        frame_totales_derecha,
        text="Total Deuda:",
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
            messagebox.showwarning(
                "Advertencia", "Seleccione un registro para eliminar.", parent=ventana
            )
            return
        item = seleccionado[0]
        valores = tree.item(item, "values")
        id_historial, _, producto, _, fecha, hora, cantidad, subtotal, accion = valores

        if not messagebox.askyesno(
            "Confirmar",
            f"¿Está seguro de eliminar el registro de '{producto}' del {fecha}?",
            parent=ventana,
        ):
            return

        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                # 1. Obtener los datos del historial para encontrar el detalle de deuda
                cursor.execute(
                    "SELECT id_deuda, id_producto, cantidad, subtotal FROM historial_deudas WHERE id_historial = ?",
                    (id_historial,)
                )
                res = cursor.fetchone()
                if not res:
                    messagebox.showerror("Error", "No se encontró el registro en el historial.", parent=ventana)
                    return

                id_deuda, id_producto, cantidad_db, subtotal_db = res

                # 2. Eliminar el registro de historial_deudas
                cursor.execute("DELETE FROM historial_deudas WHERE id_historial = ?", (id_historial,))

                # 3. Restaurar el stock en inventario si la acción fue "Deuda" o "Editado"
                if accion.lower() in ("deuda", "deuda directa", "editado"):
                    cursor.execute(
                        "UPDATE inventario SET stock = stock + ? WHERE id_producto = ?",
                        (cantidad_db, id_producto)
                    )

                # 4. Recalcular el total de la deuda y actualizar la tabla 'deudas'
                # Tener en cuenta los abonos: si accion = 'Abono' restar el subtotal
                cursor.execute(
                    "SELECT SUM(CASE WHEN accion = 'Abono' THEN -subtotal ELSE subtotal END) FROM historial_deudas WHERE id_deuda = ?",
                    (id_deuda,)
                )
                nuevo_total = cursor.fetchone()[0] or 0
                cursor.execute("UPDATE deudas SET total = ? WHERE id_deuda = ?", (nuevo_total, id_deuda))

                # 5. Si ya no quedan registros para esa deuda, eliminar la deuda principal
                cursor.execute("SELECT COUNT(*) FROM historial_deudas WHERE id_deuda = ?", (id_deuda,))
                count = cursor.fetchone()[0]
                if count == 0:
                    cursor.execute("DELETE FROM deudas WHERE id_deuda = ?", (id_deuda,))

                conn.commit()

            # 6. Actualizar la interfaz gráfica (fuera del with, sin conexión abierta)
            tree.delete(item)
            cargar_historial()
            # Actualizar la tabla principal de deudas y el total
            parent_ref = ventana.master
            while parent_ref:
                if hasattr(parent_ref, "frames"):
                    for frame in parent_ref.frames.values():
                        if hasattr(frame, "cargar_deudas"):
                            frame.cargar_deudas()
                        if hasattr(frame, "actualizar_total_deudas"):
                            frame.actualizar_total_deudas()
                if hasattr(parent_ref, "cargar_deudas"):
                    parent_ref.cargar_deudas()
                if hasattr(parent_ref, "actualizar_total_deudas"):
                    parent_ref.actualizar_total_deudas()
                parent_ref = getattr(parent_ref, "master", None)
            messagebox.showinfo("Éxito", "El registro ha sido eliminado correctamente.", parent=ventana)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el registro: {e}", parent=ventana)

    btn_eliminar.config(command=eliminar_registro)

    def abonar_registro():
        """
        Abona la deuda que se está visualizando (si `id_deuda` fue pasado a abrir_historial_deudas)
        o la deuda asociada al registro seleccionado. Crea un registro en `historial_deudas`
        con acción 'Abonado', actualiza la tabla `deudas` y, si la deuda queda en 0,
        mueve automáticamente a `ventas` creando `ventas`, `detalle_venta` y registros
        en `historial_ventas` (incluyendo los abonos) para que sean visibles en ambos historiales.
        """
        # Determinar id_deuda objetivo: preferir `id_deuda` pasado al abrir la ventana
        id_deuda_local = id_deuda if id_deuda is not None else None

        # Si no tenemos id_deuda por parámetro, intentar obtenerla de la selección
        if id_deuda_local is None:
            seleccionado = tree.selection()
            if not seleccionado:
                messagebox.showwarning(
                    "Advertencia", "Seleccione un registro o abra el historial de una deuda específica para abonar.", parent=ventana
                )
                return
            item = seleccionado[0]
            valores = tree.item(item, "values")
            id_historial = valores[0]
            try:
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id_deuda FROM historial_deudas WHERE id_historial = ?", (id_historial,))
                    res = cursor.fetchone()
                    if not res or res[0] is None:
                        messagebox.showerror("Error", "No se encontró la deuda asociada o no es posible abonar.", parent=ventana)
                        return
                    id_deuda_local = res[0]
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo obtener la deuda: {e}", parent=ventana)
                return

        # Obtener información de la deuda y del cliente
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT cliente, cliente_rapido, total FROM deudas WHERE id_deuda = ?", (id_deuda_local,))
                deuda_row = cursor.fetchone()
                if not deuda_row:
                    messagebox.showerror("Error", "Deuda no encontrada.", parent=ventana)
                    return
                cliente_fk, cliente_rap, total_actual = deuda_row[0], deuda_row[1], float(deuda_row[2] or 0)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer la deuda: {e}", parent=ventana)
            return

        # Mostrar Toplevel de abono con información del cliente y deuda
        abono_win = tk.Toplevel(ventana)
        abono_win.title(f"Abono - Deuda #{id_deuda_local}")
        abono_win.geometry("420x230+300+200")
        # Asociar modal al padre y evitar interacciones con otras ventanas
        try:
            abono_win.transient(ventana)
        except Exception:
            pass
        try:
            abono_win.grab_set()
        except Exception:
            pass
        try:
            abono_win.attributes("-topmost", True)
        except Exception:
            pass
        abono_win.configure(bg="#F5F5F5")

        cliente_text = ""
        if cliente_fk:
            try:
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT nombres, apellidos FROM clientes WHERE id_cliente = ?", (cliente_fk,))
                    r = cursor.fetchone()
                    cliente_text = f"{r[0]} {r[1]}" if r else "Cliente"
            except Exception:
                cliente_text = cliente_rap or "Cliente"
        else:
            cliente_text = cliente_rap or "Cliente"

        tk.Label(abono_win, text=f"Cliente: {cliente_text}", font=("Helvetica", 12, "bold"), bg="#F5F5F5").pack(fill="x", pady=(10, 4), padx=12)
        tk.Label(abono_win, text=f"Total deuda actual: ${total_actual:,.0f}".replace(",", "."), font=("Helvetica", 12), bg="#F5F5F5").pack(fill="x", padx=12)

        tk.Label(abono_win, text="Monto a abonar:", font=("Helvetica", 11), bg="#F5F5F5").pack(pady=(8, 0), anchor="w", padx=12)
        entry_var = tk.StringVar()
        def validate_numeric(P):
            if P == "":
                return True
            try:
                v = float(P)
                return v >= 0
            except Exception:
                return False
        vcmd = (abono_win.register(validate_numeric), "%P")
        entry_abono = tk.Entry(abono_win, textvariable=entry_var, validate="key", validatecommand=vcmd, font=("Helvetica", 12), justify="center")
        entry_abono.pack(padx=12, pady=(6, 4))
        entry_abono.focus_set()

        restante_var = tk.StringVar(value=f"${total_actual:,.0f}".replace(",", "."))
        tk.Label(abono_win, text="Deuda restante:", font=("Helvetica", 11), bg="#F5F5F5").pack(pady=(6, 0), anchor="w", padx=12)
        tk.Label(abono_win, textvariable=restante_var, font=("Helvetica", 13, "bold"), bg="#F5F5F5", fg="#4CAF50").pack(pady=(0, 8), padx=12, anchor="w")

        def _on_entry_change(*_):
            val = entry_var.get().strip()
            if val == "":
                restante = total_actual
            else:
                try:
                    monto_tmp = float(val)
                    restante = max(0, total_actual - monto_tmp)
                except Exception:
                    restante = total_actual
            restante_var.set(f"${restante:,.0f}".replace(",", "."))
        entry_var.trace_add("write", _on_entry_change)

        btn_frame = tk.Frame(abono_win, bg="#F5F5F5")
        btn_frame.pack(pady=(6, 10))

        def confirmar_abono():
            val = entry_var.get().strip()
            if val == "":
                messagebox.showwarning("Advertencia", "Ingrese un monto válido.", parent=abono_win)
                return
            try:
                monto = float(val)
            except Exception:
                messagebox.showwarning("Advertencia", "Monto inválido.", parent=abono_win)
                return
            if monto <= 0:
                messagebox.showwarning("Advertencia", "El monto debe ser mayor que 0.", parent=abono_win)
                return
            if monto > total_actual:
                if not messagebox.askyesno("Confirmar", f"El monto a abonar (${monto:,.0f}) es mayor que la deuda actual (${total_actual:,.0f}). ¿Desea continuar?", parent=abono_win):
                    return
            if not messagebox.askyesno("Confirmar", f"¿Confirmar abono de ${monto:,.0f} a la deuda #{id_deuda_local}?", parent=abono_win):
                return

            try:
                with get_connection() as conn:
                    cursor = conn.cursor()
                    fecha = datetime.datetime.now().strftime("%Y-%m-%d")
                    hora = datetime.datetime.now().strftime("%H:%M:%S")
                    usuario = os.getlogin() if hasattr(os, "getlogin") else "sistema"

                    # Insertar registro de abono (subtotal positivo) con acción 'Abono'
                    cursor.execute(
                        """
                        INSERT INTO historial_deudas (id_deuda, id_producto, cantidad, subtotal, accion, usuario, fecha, hora, detalle, abono)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (id_deuda_local, None, 0, float(monto), 'Abono', usuario, fecha, hora, f'Abono de ${monto:,.0f}'.replace(',', '.'), float(monto)),
                    )

                    # Recalcular total de la deuda: restar abonos (accion = 'Abono') y sumar los cargos
                    cursor.execute(
                        "SELECT SUM(CASE WHEN accion = 'Abono' THEN -subtotal ELSE subtotal END) FROM historial_deudas WHERE id_deuda = ?",
                        (id_deuda_local,)
                    )
                    nuevo_total = cursor.fetchone()[0] or 0
                    cursor.execute("UPDATE deudas SET total = ?, deuda = ? WHERE id_deuda = ?", (nuevo_total, nuevo_total, id_deuda_local))

                    # Si la deuda queda en 0, mover a ventas (facturar)
                    if round(nuevo_total, 2) == 0:
                        # Crear venta con los items originales de la deuda
                        # Obtener items de historial_deudas que representen productos (subtotal > 0 y id_producto not null)
                        cursor.execute(
                            "SELECT id_producto, cantidad, subtotal FROM historial_deudas WHERE id_deuda = ? AND accion IN ('Deuda', 'Deuda directa', 'Editado')",
                            (id_deuda_local,)
                        )
                        items = cursor.fetchall()

                        # Insert venta
                        cursor.execute(
                            "INSERT INTO ventas (cliente_venta, cliente_rapido, fecha, hora, total, ganancia, monto_recibido, vuelto) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (cliente_fk, cliente_rap, fecha, hora, abs(sum([it[2] for it in items])), 0, abs(sum([it[2] for it in items])), 0),
                        )
                        id_ventas = cursor.lastrowid

                        # Insert detalle_venta y historial_ventas por cada item
                        for id_producto, cantidad_p, subtotal_p in items:
                            cursor.execute(
                                "INSERT INTO detalle_venta (id_producto, cantidad, subtotal, pago, id_ventas, id_deuda, hora_producto, fecha_producto) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (id_producto, cantidad_p, subtotal_p, 1, id_ventas, None, hora, fecha),
                            )
                            # Registrar en historial_ventas
                            cursor.execute(
                                "INSERT INTO historial_ventas (id_ventas, id_producto, cantidad, subtotal, accion, usuario, fecha, hora, detalle) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (id_ventas, id_producto, cantidad_p, subtotal_p, 'Venta por abono', usuario, fecha, hora, f'Producto desde deuda #{id_deuda_local}'),
                            )

                        # Registrar cada abono también en historial_ventas para visibilidad
                        # Registrar cada abono también en historial_ventas para visibilidad
                        # Traer fecha, hora, monto, usuario y detalle para preservar información original
                        cursor.execute(
                            "SELECT fecha, hora, abono, usuario, detalle FROM historial_deudas WHERE id_deuda = ? AND accion = 'Abono' ORDER BY fecha ASC, hora ASC",
                            (id_deuda_local,)
                        )
                        abonos_rows = cursor.fetchall()
                        for f, h, a, usr, det in abonos_rows:
                            # Registrar en historial_ventas como subtotales negativos para reflejar pago
                            detalle_text = det if det else f'Abono de ${a:,.0f}'.replace(',', '.')
                            usuario_text = usr if usr else usuario
                            cursor.execute(
                                "INSERT INTO historial_ventas (id_ventas, id_producto, cantidad, subtotal, accion, usuario, fecha, hora, detalle) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (id_ventas, None, 0, -float(a), 'Abono', usuario_text, f, h, detalle_text),
                            )

                        # Finalmente eliminar la deuda principal
                        cursor.execute("DELETE FROM deudas WHERE id_deuda = ?", (id_deuda_local,))

                    conn.commit()

                # Cerrar ventana y refrescar
                abono_win.destroy()
                cargar_historial()
                parent_ref = ventana.master
                while parent_ref:
                    if hasattr(parent_ref, "frames"):
                        for frame in parent_ref.frames.values():
                            if hasattr(frame, "cargar_deudas"):
                                frame.cargar_deudas()
                            if hasattr(frame, "actualizar_total_deudas"):
                                frame.actualizar_total_deudas()
                    if hasattr(parent_ref, "cargar_deudas"):
                        parent_ref.cargar_deudas()
                    if hasattr(parent_ref, "actualizar_total_deudas"):
                        parent_ref.actualizar_total_deudas()
                    parent_ref = getattr(parent_ref, "master", None)

                messagebox.showinfo("Éxito", "Abono registrado correctamente.", parent=ventana)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo registrar el abono: {e}", parent=abono_win)

        tk.Button(btn_frame, text="Confirmar", command=confirmar_abono, bg="#1976D2", fg="white", font=("Helvetica", 11, "bold"), width=12).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Cancelar", command=abono_win.destroy, width=12).pack(side="left", padx=8)

        abono_win.wait_window()

    btn_abono.config(command=lambda: abonar_registro())

    def cargar_historial():
        tree.delete(*tree.get_children())
        # --- Usar la función que retorna también el id_historial ---

        with get_connection() as conn:
            cursor = conn.cursor()
            if id_deuda is not None:
                # Mostrar solo los productos de esa deuda específica
                cursor.execute(
                    """
                                        SELECT h.id_historial, i.producto, h.fecha, h.hora, h.cantidad, h.subtotal, h.accion
                                        FROM historial_deudas h
                                        LEFT JOIN inventario i ON h.id_producto = i.id_producto
                                        WHERE h.id_deuda = ?
                                            AND h.accion IN ('Deuda', 'Deuda directa', 'Editado', 'Abono')
                                        ORDER BY h.fecha DESC, h.hora DESC
                                        """,
                    (id_deuda,)
                )
            elif id_cliente is not None:
                # Buscar solo por id_cliente (cliente normal)
                cursor.execute(
                    """
                                        SELECT h.id_historial, i.producto, h.fecha, h.hora, h.cantidad, h.subtotal, h.accion
                                        FROM historial_deudas h
                                        LEFT JOIN inventario i ON h.id_producto = i.id_producto
                                        LEFT JOIN deudas d ON h.id_deuda = d.id_deuda
                                        WHERE d.cliente = ?
                                            AND h.accion IN ('Deuda', 'Deuda directa', 'Editado', 'Abono')
                                        ORDER BY h.fecha DESC, h.hora DESC
                                        """,
                    (id_cliente,),
                )
            else:
                # Buscar solo por cliente_rapido (cliente rápido)
                cursor.execute(
                    """
                                        SELECT h.id_historial, i.producto, h.fecha, h.hora, h.cantidad, h.subtotal, h.accion
                                        FROM historial_deudas h
                                        LEFT JOIN inventario i ON h.id_producto = i.id_producto
                                        LEFT JOIN deudas d ON h.id_deuda = d.id_deuda
                                        WHERE d.cliente_rapido = ?
                                            AND h.accion IN ('Deuda', 'Deuda directa', 'Editado', 'Abono')
                                        ORDER BY h.fecha DESC, h.hora DESC
                                        """,
                    (cliente_rapido_mostrar,),
                )
            rows = cursor.fetchall()
        total = 0
        total_cantidad = 0
        dias = [
            "Lunes",
            "Martes",
            "Miércoles",
            "Jueves",
            "Viernes",
            "Sábado",
            "Domingo",
        ]
        for idx, (id_historial, producto, fecha, hora, cantidad, subtotal, accion) in enumerate(rows, start=1):
            try:
                fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
                dia_semana = dias[fecha_dt.weekday()]
            except Exception:
                dia_semana = ""
            # Si la acción es 'Abono', el subtotal debe restarse del total de la deuda
            try:
                if accion == 'Abono':
                    total -= float(subtotal) if subtotal is not None else 0
                else:
                    total += float(subtotal) if subtotal is not None else 0
            except Exception:
                # Fallback seguro: sumar si ocurre cualquier error al interpretar
                total += float(subtotal) if subtotal is not None else 0
            total_cantidad += int(cantidad) if cantidad is not None else 0
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
                    f"${float(subtotal):,.0f}".replace(",", ".") if subtotal is not None else "",
                    accion,
                ),
            )
        var_total.set(f"${total:,.0f}".replace(",", "."))
        var_total_cantidad.set(str(total_cantidad))

    cargar_historial()
