import tkinter as tk
from tkinter import ttk, messagebox
from retail.core.database import obtener_productos, get_connection


def peso_colombiano(value):
    return f"${value:,.0f}".replace(",", ".")


def ver_carrito(ventas_view):
    if not ventas_view.carrito:
        messagebox.showinfo(
            "Carrito vacío", "No hay productos en el carrito.", parent=ventas_view
        )
        return

    top = tk.Toplevel(ventas_view)
    top.title("Carrito de Ventas")
    # Tamaño por defecto fijado (no redimensionable)
    top.geometry("820x510+200+50")
    top.configure(bg="#F4F6F8")
    top.resizable(False, False)
    top.grab_set()

    carrito = ventas_view.carrito
    # Agrupar productos por cliente
    clientes = {}
    for item in carrito:
        cliente = item["cliente"]
        if cliente not in clientes:
            clientes[cliente] = []
        clientes[cliente].append(item)

    # Frame principal para mejor padding y fondo
    frame_main = tk.Frame(top, bg="#F4F6F8")
    frame_main.pack(fill="both", expand=True, padx=18, pady=12)

    for cliente, productos in clientes.items():
        lf_cliente = tk.LabelFrame(
            frame_main,
            text=f"Cliente: {cliente}",
            font=("Helvetica", 13, "bold"),
            bg="#FFFFFF",
            fg="#333333",
            relief="groove",
            labelanchor="n",
            bd=2,
            padx=6,
            pady=6,
        )
        lf_cliente.pack(fill="x", padx=0, pady=(0, 12))

        frame_tabla = tk.Frame(lf_cliente, bg="#FFFFFF")
        frame_tabla.pack(fill="both", padx=8, pady=(8, 8), expand=True)

        columns = ("producto", "cantidad", "subtotal")
        style = ttk.Style(top)
        style.theme_use("clam")
        style.configure(
            "Carrito.Treeview.Heading",
            font=("Helvetica", 12, "bold"),
            background="#2196F3",
            foreground="#fff",
            borderwidth=0,
        )
        style.configure(
            "Carrito.Treeview",
            font=("Helvetica", 12),
            rowheight=32,
            background="#F8FAFB",
            fieldbackground="#F8FAFB",
            borderwidth=0,
        )
        style.map("Carrito.Treeview", background=[("selected", "#105A65")])  # <-- Selección color

        tree = ttk.Treeview(
            frame_tabla,
            columns=columns,
            show="headings",
            style="Carrito.Treeview",
        )
        tree.heading("producto", text="Producto")
        tree.heading("cantidad", text="Cantidad")
        tree.heading("subtotal", text="Subtotal")

        # Ajustar anchos de columna para que el texto se vea correctamente
        tree.column("producto", width=300, anchor="w")
        tree.column("cantidad", width=100, anchor="center")
        tree.column("subtotal", width=140, anchor="e")

        # Altura del treeview en filas: depende de cuántos productos hay (mín 5, máx 12)
        filas = max(5, min(12, len(productos) + 1))
        tree.config(height=filas)

        # Scrollbar vertical
        scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Insertar productos en la tabla
        for idx, prod in enumerate(productos):
            tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    prod["producto"],
                    prod["cantidad"],
                    peso_colombiano(prod["subtotal"]),
                ),
            )

        # --- Edición de cantidad en la tabla ---
        def editar_cantidad(event):
            seleccion = tree.selection()
            if not seleccion:
                return
            idx = int(seleccion[0])
            prod_a_editar = productos[idx]

            # Obtener stock actualizado en tiempo real
            productos_actualizados = obtener_productos()
            stock_actual = None
            id_producto = prod_a_editar["id_producto"]
            for p in productos_actualizados:
                if p[0] == id_producto:
                    stock_actual = p[4]
                    break

            popup = tk.Toplevel(top)
            popup.title("Editar cantidad")
            popup.geometry("340x210+500+250")
            popup.configure(bg="#F4F6F8")
            popup.resizable(False, False)
            popup.transient(top)

            # Validación solo números enteros positivos
            def validar_entero(valor):
                return valor == "" or (valor.isdigit() and int(valor) > 0)

            vcmd_entero = (popup.register(validar_entero), "%P")

            def hacer_grab():
                try:
                    popup.grab_set()
                except Exception:
                    pass

            popup.wait_visibility()
            popup.after_idle(hacer_grab)
            popup.focus_force()

            tk.Label(
                popup,
                text=f"Producto: {prod_a_editar['producto']}",
                font=("Helvetica", 13, "bold"),
                bg="#F4F6F8",
                fg="#333333",
            ).pack(pady=(12, 2), padx=10)
            tk.Label(
                popup,
                text=f"Stock disponible en inventario: {stock_actual if stock_actual is not None else 'N/D'}",
                font=("Helvetica", 12, "bold"),
                bg="#F4F6F8",
                fg="#008B8B" if stock_actual and stock_actual > 0 else "#F44336",
            ).pack(pady=(2, 2), padx=10)
            tk.Label(
                popup,
                text="Nueva cantidad:",
                font=("Helvetica", 12),
                bg="#F4F6F8",
                fg="#333333",
            ).pack(pady=(5, 5), padx=10)
            entry_cantidad = tk.Entry(
                popup,
                font=("Helvetica", 12),
                width=10,
                validate="key",
                validatecommand=vcmd_entero,
                justify="center",
                bg="#FFFFFF",
                relief="solid",
                bd=1,
            )
            entry_cantidad.pack(pady=(0, 10))
            entry_cantidad.insert(0, str(prod_a_editar["cantidad"]))

            frame_btns = tk.Frame(popup, bg="#F4F6F8")
            frame_btns.pack(pady=(5, 0))

            def guardar_cantidad():
                try:
                    nueva_cantidad = int(entry_cantidad.get())
                    if nueva_cantidad <= 0:
                        messagebox.showwarning(
                            "Cantidad inválida",
                            "Ingrese una cantidad mayor a cero.",
                            parent=popup,
                        )
                        return
                    # Validar stock actualizado en tiempo real
                    productos_actualizados2 = obtener_productos()
                    stock_actual2 = None
                    for p in productos_actualizados2:
                        if p[0] == id_producto:
                            stock_actual2 = p[4]
                            break
                    if stock_actual2 is None:
                        messagebox.showerror(
                            "Error",
                            "No se pudo obtener el stock actual del producto.",
                            parent=popup,
                        )
                        return
                    if nueva_cantidad > stock_actual2:
                        messagebox.showwarning(
                            "Stock insuficiente",
                            f"Solo hay {stock_actual2} unidades disponibles.",
                            parent=popup,
                        )
                        return
                    # Actualizar en la lista del carrito
                    prod_a_editar["cantidad"] = nueva_cantidad
                    prod_a_editar["subtotal"] = nueva_cantidad * prod_a_editar["precio"]
                    # Actualizar en la tabla visual
                    tree.set(seleccion[0], "cantidad", nueva_cantidad)
                    tree.set(
                        seleccion[0],
                        "subtotal",
                        peso_colombiano(prod_a_editar["subtotal"]),
                    )
                    actualizar_total()
                    # Si el stock se agota tras editar, actualizar estado y notificar
                    if nueva_cantidad == stock_actual2:
                        with get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "UPDATE inventario SET estado = 0 WHERE id_producto = ?",
                                (id_producto,),
                            )
                            conn.commit()
                        messagebox.showwarning(
                            "Producto agotado",
                            f"El producto '{prod_a_editar['producto']}' se encuentra AGOTADO tras esta edición.\n"
                            "Debe solicitar un pedido y actualizar el stock desde la sección de Inventario.",
                            parent=top,
                        )
                    popup.destroy()
                except ValueError:
                    messagebox.showwarning(
                        "Cantidad inválida", "Ingrese un número válido.", parent=popup
                    )

            btn_guardar = tk.Button(
                frame_btns,
                text="Guardar",
                font=("Helvetica", 12, "bold"),
                bg="#4CAF50",
                fg="white",
                activebackground="#388E3C",
                activeforeground="white",
                relief="flat",
                bd=0,
                cursor="hand2",
                command=guardar_cantidad,
                width=10,
                height=1,
            )
            btn_guardar.pack(side="left", padx=10)
            btn_cancelar = tk.Button(
                frame_btns,
                text="Cancelar",
                font=("Helvetica", 12, "bold"),
                bg="#F44336",
                fg="white",
                activebackground="#B71C1C",
                activeforeground="white",
                relief="flat",
                bd=0,
                cursor="hand2",
                command=popup.destroy,
                width=10,
                height=1,
            )
            btn_cancelar.pack(side="left", padx=10)

        tree.bind("<Double-1>", editar_cantidad)

        # Botón Eliminar debajo de la tabla
        def eliminar_producto():
            seleccion = tree.selection()
            if not seleccion:
                messagebox.showwarning(
                    "Advertencia",
                    "Seleccione un producto para eliminar.",
                    parent=top,
                )
                return
            idx = int(seleccion[0])
            # Elimina el producto del carrito de la vista principal
            # Buscar el producto correcto en ventas_view.carrito (por cliente y producto)
            prod_a_eliminar = productos[idx]
            for i, item in enumerate(ventas_view.carrito):
                if (
                    item["cliente"] == cliente
                    and item["producto"] == prod_a_eliminar["producto"]
                    and item["cantidad"] == prod_a_eliminar["cantidad"]
                    and item["subtotal"] == prod_a_eliminar["subtotal"]
                ):
                    del ventas_view.carrito[i]
                    break
            tree.delete(seleccion[0])
            # Si ya no quedan productos en la tabla, cerrar ventana y mostrar mensaje
            if not tree.get_children():
                top.destroy()
                messagebox.showinfo(
                    "Carrito vacío",
                    "No hay productos en el carrito.",
                    parent=ventas_view,
                )
                return
            # Si el cliente ya no tiene productos, cerrar ventana y mostrar mensaje
            if all(item["cliente"] != cliente for item in ventas_view.carrito):
                top.destroy()
                messagebox.showinfo(
                    "Carrito vacío",
                    "No hay productos en el carrito.",
                    parent=ventas_view,
                )
                return
            # Actualizar el total mostrado
            actualizar_total()

        btns_frame = tk.Frame(lf_cliente, bg="#FFFFFF")
        btns_frame.pack(fill="x", padx=8, pady=(0, 8))

        # Colocar el botón Eliminar a la derecha (UX request)
        btn_eliminar = tk.Button(
            btns_frame,
            text="Eliminar producto",
            font=("Helvetica", 12, "bold"),
            bg="#F44336",
            fg="white",
            activebackground="#B71C1C",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=eliminar_producto,
            width=16,
            height=1,
        )
        btn_eliminar.pack(side="right", padx=(0, 10), pady=2)

        # LabelFrame "Menudo" (campo monto recibido + vuelto) - estilo parecido a Total
        lf_menudo = tk.LabelFrame(
            lf_cliente,
            text="Menudo",
            font=("Helvetica", 11, "bold"),
            bg="#FFFFFF",
            fg="#333333",
            relief="groove",
            labelanchor="n",
            bd=1,
            padx=6,
            pady=6,
        )
        lf_menudo.pack(fill="x", padx=0, pady=(0, 6))

        # Contenido interno: izquierda -> monto recibido, derecha -> vuelto
        frame_menudo = tk.Frame(lf_menudo, bg="#FFFFFF")
        frame_menudo.pack(fill="x", padx=10, pady=6)

        tk.Label(
            frame_menudo,
            text="Monto recibido:",
            font=("Helvetica", 11),
            bg="#FFFFFF",
            fg="#333333",
        ).pack(side="left")

        # Dejar el campo en blanco esperando entrada del usuario
        monto_var = tk.StringVar(value="")
        # Inicializar en la vista principal para que Confirmar pueda leerlo
        try:
            ventas_view.monto_recibido = ""
        except Exception:
            pass

        def _validar_numero_simple(val):
            if val == "":
                return True
            try:
                float(val)
                return True
            except Exception:
                return False

        vcmd_num = (lf_menudo.register(_validar_numero_simple), "%P")

        entry_monto = tk.Entry(
            frame_menudo,
            textvariable=monto_var,
            validate="key",
            validatecommand=vcmd_num,
            font=("Helvetica", 12, "bold"),
            width=18,
            justify="center",
            bg="#FFFFFF",
            relief="solid",
            bd=1,
        )
        entry_monto.pack(side="left", padx=(8, 6), pady=4)

        # Espaciador flexible
        tk.Frame(frame_menudo, bg="#FFFFFF").pack(side="left", expand=True, fill="x")

        tk.Label(
            frame_menudo,
            text="Vuelto:",
            font=("Helvetica", 11),
            bg="#FFFFFF",
            fg="#333333",
        ).pack(side="left")

        vuelto_var = tk.StringVar(value=peso_colombiano(0))
        lbl_vuelto = tk.Label(
            frame_menudo,
            textvariable=vuelto_var,
            font=("Helvetica", 12, "bold"),
            bg="#FFFFFF",
            fg="#0B6623",
            width=14,
            relief="solid",
            bd=1,
            anchor="e",
            justify="right",
        )
        lbl_vuelto.pack(side="left", padx=(8, 0), pady=4)

        # Actualizar el vuelto cuando cambie el monto ingresado
        def actualizar_vuelto(*_):
            # Sincronizar el monto con la vista principal para validaciones en Confirmar
            try:
                ventas_view.monto_recibido = monto_var.get().strip()
            except Exception:
                pass
            # Si no se ingresó monto (vacío o <= 0) el menudo permanece en 0
            try:
                monto_val = float(monto_var.get() or 0)
            except Exception:
                monto_val = 0
            total_actual = getattr(lbl_total, "_total_value", 0)
            if monto_val <= 0:
                vuelto_var.set(peso_colombiano(0))
                return
            vuelto_calc = monto_val - total_actual
            vuelto_var.set(peso_colombiano(max(0, round(vuelto_calc))))

        # LabelFrame para el total (sigue abajo)
        lf_total = tk.LabelFrame(
            lf_cliente,
            text="Total",
            font=("Helvetica", 11, "bold"),
            bg="#FFFFFF",
            fg="#333333",
            relief="groove",
            labelanchor="n",
            bd=1,
            padx=6,
            pady=6,
        )
        lf_total.pack(fill="x", padx=0, pady=(0, 5))
        lbl_total = tk.Label(
            lf_total,
            font=("Helvetica", 18, "bold"),
            bg="#FFFFFF",
            fg="#0B6623",
            anchor="e",
        )
        # Total destacado, alineado a la derecha y con suficiente padding
        lbl_total.pack(fill="x", anchor="e", padx=12, pady=8)

        def actualizar_total():
            total_cliente = 0
            for iid in tree.get_children():
                subtotal_str = (
                    tree.set(iid, "subtotal").replace("$", "").replace(".", "")
                )
                subtotal = int(subtotal_str)
                total_cliente += subtotal
            lbl_total.config(text=peso_colombiano(total_cliente))
            # Guardar valor numérico para uso por el Menudo
            lbl_total._total_value = total_cliente

            # Actualizar vuelto inmediatamente cuando cambie el total
            try:
                monto_val = float(monto_var.get() or 0)
            except Exception:
                monto_val = 0
            if monto_val <= 0:
                vuelto_var.set(peso_colombiano(0))
            else:
                vuelto_var.set(peso_colombiano(max(0, round(monto_val - total_cliente))))

        # Registrar la traza UNA sola vez (después de definir lbl_total y actualizar_total)
        monto_var.trace_add("write", actualizar_vuelto)

        # Calcular el total inicial
        actualizar_total()
