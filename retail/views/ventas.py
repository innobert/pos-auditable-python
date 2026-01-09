import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
from datetime import datetime

from retail.core.config import rutas
from retail.core.database import (
    obtener_productos,
    obtener_clientes,
    get_connection,
    actualizar_cuentas,
    buscar_productos_por_nombre,
    actualizar_producto,
    registrar_historial_venta,
    registrar_historial_deuda,
    create_sale,
)
from retail.ventas.facturas import ver_facturas
from retail.ventas.ganancias import ver_ganancias
from retail.ventas.carrito import ver_carrito


class Ventas(tk.Frame):
    def __init__(self, padre, controlador):
        super().__init__(padre, bg="#E6D9E3")
        self.controlador = controlador
        self.pack(fill="both", expand=True)
        self.producto_seleccionado_frame = None
        self.carrito = []
        self.productos_cache = []
        self.widgets()
        self.actualizar_combobox_clientes()
        self.actualizar_combobox_productos()
        self.entry_stock.bind("<KeyRelease>", self.filtrar_productos_combobox)
        self.entry_stock.bind("<Return>", self.seleccionar_producto_entry)
        self.entry_cliente.bind("<KeyRelease>", self.filtrar_clientes_combobox)

    def widgets(self):
        # Título Principal
        label_titulo = tk.Label(
            self,
            text="Ventas",
            font=("Helvetica", 15, "bold"),
            bg="#2196F3",
            fg="#0A0A0A",
        )
        label_titulo.place(x=0, y=0, width=1100, height=30)

        # Canvas para productos
        frame_canvas = tk.LabelFrame(
            self,
            text="Productos",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
        )
        frame_canvas.place(x=10, y=40, width=850, height=560)

        self.canvas = tk.Canvas(
            frame_canvas,
            bg="#E6D9E3",
            highlightthickness=0
        )
        self.scrollbar = tk.Scrollbar(
            frame_canvas, orient="vertical", command=self.canvas.yview
        )
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.frame_contenedor = tk.Frame(self.canvas, bg="#E6D9E3")
        self.canvas.create_window((0, 0), window=self.frame_contenedor, anchor="nw")

        self.frame_contenedor.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind("<Enter>", lambda event: self._activar_scroll_canvas())
        self.canvas.bind("<Leave>", lambda event: self._desactivar_scroll_canvas())

        self.mostrar_productos_inventario()

        # Label Frame Detalles de Venta
        frame_detalles = tk.LabelFrame(
            self,
            text="Detalles de Venta",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
        )
        frame_detalles.place(x=870, y=40, width=220, height=400)

        # Cliente
        label_cliente = tk.Label(
            frame_detalles,
            text="Cliente",
            font=("Calibri", 14, "bold"),
            bg="#E6D9E3",
            fg="#333333",
            anchor="w",
        )
        label_cliente.pack(fill="x", padx=10)

        self.entry_cliente = ttk.Combobox(
            frame_detalles,
            font=("Calibri", 14),
            foreground="#333333",
        )
        self.entry_cliente.pack(fill="x", padx=10, pady=(0, 20), ipady=4)

        # Producto
        label_stock = tk.Label(
            frame_detalles,
            text="Producto",
            font=("Calibri", 14, "bold"),
            bg="#E6D9E3",
            fg="#333333",
            anchor="w",
        )
        label_stock.pack(fill="x", padx=10)
        self.entry_stock = ttk.Combobox(
            frame_detalles,
            font=("Calibri", 14),
            foreground="#333333",
        )
        self.entry_stock.pack(fill="x", padx=10, pady=(0, 20), ipady=4)

        # ¿Pagó?
        label_pago = tk.Label(
            frame_detalles,
            text="¿Pagó?",
            font=("Calibri", 14, "bold"),
            bg="#E6D9E3",
            fg="#333333",
            anchor="w",
        )
        label_pago.pack(fill="x", padx=10)
        self.entry_pago = ttk.Combobox(
            frame_detalles,
            font=("Calibri", 14),
            foreground="#333333",
            values=["Sí", "No"],
            state="readonly",
        )
        self.entry_pago.pack(fill="x", padx=10, pady=(0, 20), ipady=4)
        self.entry_pago.set("Sí")

        # Cargar imágenes para los botones usando rutas absolutas
        def cargar_img(nombre, size=(30, 30)):
            ruta = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "img", nombre))
            try:
                return ImageTk.PhotoImage(Image.open(ruta).resize(size))
            except Exception:
                return None

        self.img_carrito = cargar_img("carrito.png")
        self.img_confirm = cargar_img("confirm.png")
        self.img_facturas = cargar_img("facturas.png")
        self.img_ganancias = cargar_img("ganancias.png")

        # Botón Carrito
        self.btn_carrito = tk.Button(
            frame_detalles,
            text="Carrito",
            image=self.img_carrito,
            compound="left" if self.img_carrito else None,
            font=("Helvetica", 13, "bold"),
            bg="#9E9E9E",
            fg="#FFFFFF",
            command=lambda: ver_carrito(self),
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=10,
            anchor="w",
            height=30,
            width=150
        )
        self.btn_carrito.pack(fill="x", padx=10, pady=(0, 20), ipady=4, ipadx=4)

        # Botón Confirmar
        self.btn_confirmar = tk.Button(
            frame_detalles,
            text="Confirmar",
            image=self.img_confirm,
            compound="left" if self.img_confirm else None,
            font=("Helvetica", 13, "bold"),
            bg="#4CAF50",
            fg="#FFFFFF",
            command=self.confirmar_venta,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=10,
            anchor="w",
            height=30,
            width=150
        )
        self.btn_confirmar.pack(fill="x", padx=10, pady=(0, 20), ipady=4, ipadx=4)

        # Opciones
        frame_opciones = tk.LabelFrame(
            self,
            text="Opciones",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
        )
        frame_opciones.place(x=870, y=450, width=220, height=150)

        self.btn_facturas = tk.Button(
            frame_opciones,
            text="Facturas",
            image=self.img_facturas,
            compound="left" if self.img_facturas else None,
            font=("Helvetica", 13, "bold"),
            bg="#008B8B",
            fg="#FFFFFF",
            command=lambda: ver_facturas(self),
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=10,
            anchor="w",
            height=30,
            width=150
        )
        self.btn_facturas.pack(fill="x", padx=10, pady=10, ipady=2, ipadx=4)

        self.btn_ganancias = tk.Button(
            frame_opciones,
            text="Ganancias",
            image=self.img_ganancias,
            compound="left" if self.img_ganancias else None,
            font=("Helvetica", 13, "bold"),
            bg="#FF9800",
            fg="#FFFFFF",
            command=lambda: ver_ganancias(self),
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=10,
            anchor="w",
            height=30,
            width=150
        )
        self.btn_ganancias.pack(fill="x", padx=10, pady=10, ipady=2, ipadx=4)

    def confirmar_venta(self):
        if not self.carrito:
            tk.messagebox.showwarning(
                "Carrito vacío",
                "No hay productos en el carrito para confirmar la venta.",
                parent=self
            )
            return

        cliente_nombre = self.entry_cliente.get().strip()
        pago = self.entry_pago.get().strip()
        if pago not in ("Sí", "No"):
            tk.messagebox.showwarning(
                "¿Pagó? requerido",
                "Debe seleccionar si la venta fue pagada o es una deuda.",
                parent=self
            )
            return
        pago_valor = 1 if pago == "Sí" else 0

        # Cliente obligatorio solo para crédito
        if pago_valor == 0 and not cliente_nombre:
            tk.messagebox.showwarning(
                "Cliente requerido",
                "Debe seleccionar un cliente para registrar una deuda.",
                parent=self
            )
            return

        # Buscar el id_cliente por el string seleccionado
        id_cliente = None
        if cliente_nombre and "ID:" in cliente_nombre:
            try:
                id_cliente = int(cliente_nombre.split("ID:")[1].strip())
            except ValueError:
                pass

        # Preparar items
        items = []
        for item in self.carrito:
            items.append({
                "id_producto": item["id_producto"],
                "cantidad": item["cantidad"],
                "precio": item["precio"]
            })

        # Monto recibido solo para contado
        monto_recibido = 0
        if pago_valor == 1:
            monto_str = getattr(self, "monto_recibido", "").strip()
            if monto_str == "":
                tk.messagebox.showwarning(
                    "Monto requerido en el carrito",
                    "Debe ingresar el monto recibido en el Menudo del Carrito antes de confirmar la venta.",
                    parent=self,
                )
                return
            try:
                monto_recibido = float(monto_str)
            except Exception:
                tk.messagebox.showwarning(
                    "Monto inválido",
                    "El monto ingresado en el carrito no es un número válido.",
                    parent=self,
                )
                return

        try:
            # Llamar a create_sale
            result = create_sale(
                cliente_id=id_cliente,
                items=items,
                monto_recibido=monto_recibido,
                pago=pago_valor,
                usuario=self.controlador.usuario_actual
            )

            # Validar monto si contado
            if pago_valor == 1 and monto_recibido < result["total"]:
                total_fmt = f"${result['total']:,.0f}".replace(",", ".")
                monto_fmt = f"${monto_recibido:,.0f}".replace(",", ".")
                tk.messagebox.showerror(
                    "Monto insuficiente",
                    f"El monto recibido ({monto_fmt}) es menor al total de la venta ({total_fmt}).\nNo se puede registrar la venta.\nIngrese un monto mayor o igual al total en el Menudo del Carrito.",
                    parent=self,
                )
                return

            actualizar_cuentas()

            # Mostrar mensaje de éxito
            if pago_valor == 1:
                vuelto_fmt = f"${result['vuelto']:,.0f}".replace(",", ".")
                tk.messagebox.showinfo(
                    "Venta registrada",
                    f"La venta se ha registrado correctamente.\n\nVuelto a entregar: {vuelto_fmt}",
                    parent=self,
                )
            else:
                tk.messagebox.showinfo(
                    "Éxito",
                    "La deuda se ha registrado correctamente.",
                    parent=self,
                )
            self.carrito.clear()
            # Limpiar monto recibido sincronizado desde el carrito
            try:
                self.monto_recibido = ""
            except Exception:
                pass
            self.actualizar_canvas_productos()
            self.entry_cliente.set("")
            self.entry_cliente.config(state="normal")
            self.entry_stock.delete(0, tk.END)
            self.entry_pago.set("Sí")
            parent = self.master
            while parent:
                if hasattr(parent, "frames"):
                    for frame in parent.frames.values():
                        if frame.__class__.__name__.lower() == "inventario":
                            if hasattr(frame, "cargar_productos"):
                                frame.cargar_productos()
                        if frame.__class__.__name__.lower() == "facturas":
                            if hasattr(frame, "cargar_facturas"):
                                frame.cargar_facturas()
                        if frame.__class__.__name__.lower() == "deudas":
                            if hasattr(frame, "cargar_deudas"):
                                frame.cargar_deudas()
                    break
                parent = getattr(parent, "master", None)
        except Exception as e:
            tk.messagebox.showerror("Error", f"No se pudo registrar la venta o deuda: {e}", parent=self)

    # --- SOLO UNA DEFINICIÓN DE CADA MÉTODO ABAJO ---
    def mostrar_productos_inventario(self):
        """
        Carga los productos desde la base de datos y los muestra en el canvas de ventas,
        usando el mismo diseño y efecto de selección que en inventario.py.
        """
        for widget in self.frame_contenedor.winfo_children():
            widget.destroy()
        productos = obtener_productos()
        columnas = 0
        row = 0
        ancho_producto = 450
        alto_producto = 420
        separacion_x = 70
        separacion_y = 36
        for producto in productos:
            frame_producto = tk.Frame(
                self.frame_contenedor,
                bg="white",
                width=ancho_producto,
                height=alto_producto,
                bd=1,
                relief="solid",
                highlightthickness=0  # Elimina el borde blanco por defecto
            )
            frame_producto.grid(row=row, column=columnas, padx=separacion_x//2, pady=separacion_y//2, sticky="nsew")
            frame_producto.grid_propagate(False)
            frame_producto.producto_data = {
                "id_producto": producto[0],
                "producto": producto[1],
                "precio": producto[2],
                "costo": producto[3],
                "stock": producto[4],
                "estado": "Disponible" if producto[5] == 1 else "Agotado",
                "imagen": producto[6],
            }
            # Imagen
            try:
                imagen = Image.open(producto[6])
                imagen = imagen.resize((180, 180), Image.LANCZOS)
                imagen_tk = ImageTk.PhotoImage(imagen)
                img_label = tk.Label(frame_producto, image=imagen_tk, bg="white")
                img_label.image = imagen_tk
                img_label.pack(pady=(30, 10))
            except Exception:
                img_label = tk.Label(frame_producto, text="Sin imagen", bg="white")
                img_label.pack(pady=(30, 10))
            # Bind click y doble click en la imagen
            img_label.bind(
                "<Button-1>",
                lambda e, frame=frame_producto: self._seleccionar_producto_canvas(frame),
            )
            img_label.bind(
                "<Double-Button-1>",
                lambda e, data=frame_producto.producto_data, frame=frame_producto: self._solicitar_cantidad_producto(data, frame),
            )
            # Bind click y doble click en todo el frame del producto
            frame_producto.bind(
                "<Button-1>",
                lambda e, frame=frame_producto: self._seleccionar_producto_canvas(frame),
            )
            frame_producto.bind(
                "<Double-Button-1>",
                lambda e, data=frame_producto.producto_data, frame=frame_producto: self._solicitar_cantidad_producto(data, frame),
            )
            # Nombre del producto (negrita)
            tk.Label(
                frame_producto, text=producto[1], font=("Helvetica", 16, "bold"), bg="white", anchor="w"
            ).pack(fill="x", padx=10, pady=(0, 0))
            # Precio
            tk.Label(
                frame_producto, text=f"${producto[2]:,.0f}".replace(",", "."), font=("Helvetica", 15), bg="white", anchor="w"
            ).pack(fill="x", padx=10, pady=(0, 10))

            columnas += 1
            if columnas >= 3:
                columnas = 0
                row += 1

    def mostrar_productos_en_canvas(self, productos):
        for widget in self.frame_contenedor.winfo_children():
            widget.destroy()
        columnas = 0
        row = 0
        ancho_producto = 450
        alto_producto = 420
        separacion_x = 70
        separacion_y = 36
        for producto in productos:
            frame_producto = tk.Frame(
                self.frame_contenedor,
                bg="white",
                width=ancho_producto,
                height=alto_producto,
                bd=1,
                relief="solid",
                highlightthickness=0  # Elimina el borde blanco por defecto
            )
            frame_producto.grid(row=row, column=columnas, padx=separacion_x//2, pady=separacion_y//2, sticky="nsew")
            frame_producto.grid_propagate(False)
            frame_producto.producto_data = {
                "id_producto": producto[0],
                "producto": producto[1],
                "precio": producto[2],
                "costo": producto[3],
                "stock": producto[4],
                "estado": producto[5],
                "imagen": producto[6],
            }
            try:
                imagen = Image.open(producto[6])
                imagen = imagen.resize((180, 180), Image.LANCZOS)
                imagen_tk = ImageTk.PhotoImage(imagen)
                img_label = tk.Label(frame_producto, image=imagen_tk, bg="white")
                img_label.image = imagen_tk
                img_label.pack(pady=(30, 10))
            except Exception:
                img_label = tk.Label(frame_producto, text="Sin imagen", bg="white")
                img_label.pack(pady=(30, 10))
            img_label.bind(
                "<Button-1>",
                lambda e, frame=frame_producto: self._seleccionar_producto_canvas(
                    frame
                ),
            )
            img_label.bind(
                "<Double-Button-1>",
                lambda e, data=frame_producto.producto_data, frame=frame_producto: self._solicitar_cantidad_producto(
                    data, frame
                ),
            )
            frame_producto.bind(
                "<Button-1>",
                lambda e, frame=frame_producto: self._seleccionar_producto_canvas(
                    frame
                ),
            )
            frame_producto.bind(
                "<Double-Button-1>",
                lambda e, data=frame_producto.producto_data, frame=frame_producto: self._solicitar_cantidad_producto(
                    data, frame
                ),
            )
            tk.Label(
                frame_producto, text=producto[1], font=("Helvetica", 16, "bold"), bg="white", anchor="w"
            ).pack(fill="x", padx=10, pady=(0, 0))
            tk.Label(
                frame_producto, text=f"${producto[2]:,.0f}".replace(",", "."), font=("Helvetica", 15), bg="white", anchor="w"
            ).pack(fill="x", padx=10, pady=(0, 10))

            columnas += 1
            if columnas >= 3:
                columnas = 0
                row += 1

    # --- Métodos internos para selección y cantidad ---
    def _seleccionar_producto_canvas(self, frame):
        # Limpia el efecto de selección anterior sin modificar el diseño
        if (
            hasattr(self, "producto_seleccionado_frame")
            and self.producto_seleccionado_frame
            and self.producto_seleccionado_frame.winfo_exists()
        ):
            self.producto_seleccionado_frame.config(
                highlightbackground="#BDBDBD",  # Gris claro o "#000000"
                highlightcolor="#BDBDBD",
                highlightthickness=1,
                bd=1,
                relief="solid"
            )
        self.producto_seleccionado_frame = None

        # Aplica un borde azul al frame seleccionado
        if frame:
            frame.config(
                highlightbackground="#2196F3",
                highlightcolor="#2196F3",
                highlightthickness=3,
                bd=1,
                relief="solid"
            )
            self.producto_seleccionado_frame = frame

    def _solicitar_cantidad_producto(self, data, frame):
        self._seleccionar_producto_canvas(frame)
        cliente = self.entry_cliente.get().strip()
        # Obtener el stock actualizado en tiempo real desde la base de datos
        productos_actualizados = obtener_productos()
        stock_actual = None
        id_producto = data["id_producto"]
        for p in productos_actualizados:
            if p[0] == id_producto:
                stock_actual = p[4]
                break
        if stock_actual is None:
            tk.messagebox.showerror(
                "Error",
                "No se pudo obtener el stock actual del producto.",
                parent=self,
            )
            return
        # Verificar si el producto ya está en el carrito para este cliente
        producto_en_carrito = any(
            item["producto"] == data["producto"] and item["cliente"] == cliente
            for item in self.carrito
        )
        if producto_en_carrito:
            tk.messagebox.showinfo(
                "Producto ya agregado",
                f"El producto '{data['producto']}' ya ha sido agregado al carrito.\n"
                "Si desea modificar la cantidad, hágalo desde el carrito.\n"
                "Si lo elimina del carrito, podrá volver a agregarlo.",
                parent=self,
            )
            return
        if stock_actual == 0:
            tk.messagebox.showwarning(
                "Producto agotado",
                f"El producto '{data['producto']}' se encuentra AGOTADO.\n"
                "Debe solicitar un pedido y actualizar el stock desde la sección de Inventario.",
                parent=self,
            )
            self.actualizar_canvas_productos()
            return
        top = tk.Toplevel(self)
        top.title(f"Agregar {data['producto']}")
        top.geometry("350x200+400+200")
        top.configure(bg="#E6D9E3")
        # Comportamiento modal y siempre encima (como el Carrito): no redimensionable, grab y topmost
        top.resizable(False, False)
        try:
            top.transient(self)
        except Exception:
            pass
        # grab_set lo aplicamos con after (como antes) para evitar errores de foco
        try:
            top.attributes("-topmost", True)
        except Exception:
            pass

        def set_grab():
            try:
                top.grab_set()
            except tk.TclError:
                pass

        top.after(1, set_grab)
        tk.Label(
            top,
            text=f"Cliente: {cliente if cliente else '(Seleccione un cliente)'}",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
            fg="#333333",
        ).pack(pady=(10, 2))
        tk.Label(
            top,
            text=f"Producto: {data['producto']}",
            font=("Helvetica", 13, "bold"),
            bg="#E6D9E3",
        ).pack(pady=(5, 5))
        tk.Label(
            top,
            text=f"Stock disponible: {stock_actual}",
            font=("Helvetica", 12),
            bg="#E6D9E3",
            fg="green" if stock_actual > 0 else "red",
        ).pack(pady=(0, 10))
        frame_cantidad = tk.Frame(top, bg="#E6D9E3")
        frame_cantidad.pack(pady=(0, 10))
        tk.Label(
            frame_cantidad,
            text="Cantidad:",
            font=("Helvetica", 12),
            bg="#E6D9E3",
        ).pack(side="left")
        # --- Validación solo números enteros positivos ---
        def validar_entero(valor):
            return valor == "" or (valor.isdigit() and int(valor) > 0)
        vcmd_entero = (self.register(validar_entero), "%P")
        entry_cantidad = tk.Entry(frame_cantidad, font=("Helvetica", 12), width=8, validate="key", validatecommand=vcmd_entero)
        entry_cantidad.pack(side="left", padx=(10, 0))
        frame_botones = tk.Frame(top, bg="#E6D9E3")
        frame_botones.pack(pady=(5, 0))

        def agregar():
            cliente_actual = self.entry_cliente.get().strip()
            pago = self.entry_pago.get()
            if pago == "No" and not cliente_actual:
                tk.messagebox.showwarning(
                    "Cliente requerido",
                    "Debe seleccionar un cliente para ventas a crédito.",
                    parent=top,
                )
                return
            try:
                cantidad = int(entry_cantidad.get())
                if cantidad <= 0:
                    tk.messagebox.showwarning(
                        "Cantidad inválida",
                        "Ingrese una cantidad mayor a cero.",
                        parent=top,
                    )
                    return
                # Validar stock actualizado en tiempo real
                productos_actualizados = obtener_productos()
                stock_actual = None
                for p in productos_actualizados:
                    if p[0] == id_producto:
                        stock_actual = p[4]
                        break
                if stock_actual is None:
                    tk.messagebox.showerror(
                        "Error",
                        "No se pudo obtener el stock actual del producto.",
                        parent=top,
                    )
                    return
                if cantidad > stock_actual:
                    tk.messagebox.showwarning(
                        "Stock insuficiente",
                        f"Solo hay {stock_actual} unidades disponibles.",
                        parent=top,
                    )
                    return
                self.carrito.append(
                    {
                        "cliente": cliente_actual,
                        "producto": data["producto"],
                        "id_producto": data["id_producto"],
                        "cantidad": cantidad,
                        "precio": data["precio"],
                        "subtotal": cantidad * data["precio"],
                    }
                )
                # Bloquear el combobox de cliente al añadir el primer producto
                if len(self.carrito) == 1:
                    self.entry_cliente.config(state="disabled")
                tk.messagebox.showinfo(
                    "Agregado",
                    f"Se agregaron {cantidad} unidades de {data['producto']} al carrito.",
                    parent=top,
                )
                # Si el stock se agota tras agregar, actualizar estado y notificar
                if cantidad == stock_actual:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE inventario SET estado = 0 WHERE id_producto = ?",
                        (id_producto,),
                    )
                    conn.commit()
                    conn.close()
                    tk.messagebox.showwarning(
                        "Producto agotado",
                        f"El producto '{data['producto']}' se encuentra AGOTADO tras esta venta.\n"
                        "Debe solicitar un pedido y actualizar el stock desde la sección de Inventario.",
                        parent=self,
                    )
                    self.actualizar_canvas_productos()
                top.destroy()
            except ValueError:
                tk.messagebox.showwarning(
                    "Cantidad inválida", "Ingrese un número válido.", parent=top
                )

        btn_agregar = tk.Button(
            frame_botones,
            text="Agregar",
            font=("Helvetica", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            command=agregar,
            width=10,
        )
        btn_agregar.pack(side="left", padx=10)
        btn_cancelar = tk.Button(
            frame_botones,
            text="Cancelar",
            font=("Helvetica", 12, "bold"),
            bg="#F44336",
            fg="white",
            command=top.destroy,
            width=10,
        )
        btn_cancelar.pack(side="left", padx=10)

    def actualizar_combobox_clientes(self):
        """
        Llenar el combobox de clientes con nombres, apellidos e ID.
        """
        try:
            clientes = obtener_clientes()
            self.lista_clientes = [f"{c[1]} {c[2]} | ID: {c[0]}" for c in clientes]
            self.entry_cliente["values"] = self.lista_clientes
        except Exception:
            self.entry_cliente["values"] = []

    def filtrar_clientes_combobox(self, event=None):
        """
        Filtra el combobox de clientes por coincidencia parcial en nombre o apellido.
        """
        texto = self.entry_cliente.get().strip().lower()
        try:
            clientes = obtener_clientes()
            if not texto:
                filtrados = [f"{c[1]} {c[2]} | ID: {c[0]}" for c in clientes]
            else:
                filtrados = [
                    f"{c[1]} {c[2]} | ID: {c[0]}"
                    for c in clientes
                    if texto in c[1].lower() or texto in c[2].lower()
                ]
            self.entry_cliente["values"] = filtrados
        except Exception:
            self.entry_cliente["values"] = []

    def actualizar_combobox_productos(self):
        """
        Actualiza el cache de productos y el combobox de productos.
        """
        productos = obtener_productos()
        self.productos_cache = productos
        self.entry_stock["values"] = [p[1] for p in productos]

    def filtrar_productos_combobox(self, event=None):
        """
        Filtra el combobox y el canvas de productos por coincidencia parcial en el nombre.
        """
        texto = self.entry_stock.get().strip().lower()
        if not texto:
            productos = obtener_productos()
        else:
            productos = buscar_productos_por_nombre(texto)
        self.productos_cache = productos
        self.entry_stock["values"] = [p[1] for p in productos]
        self.mostrar_productos_en_canvas(productos)

    def seleccionar_producto_entry(self, event=None):
        """
        Si el usuario presiona Enter, muestra solo el producto exacto si existe,
        si no, muestra coincidencias parciales.
        """
        nombre = self.entry_stock.get().strip()
        productos = self.productos_cache
        if nombre == "":
            self.mostrar_productos_en_canvas(productos)
            return
        seleccionados = [p for p in productos if p[1].lower() == nombre.lower()]
        if seleccionados:
            self.mostrar_productos_en_canvas(seleccionados)
            for frame in self.frame_contenedor.winfo_children():
                data = getattr(frame, "producto_data", None)
                if data and data["producto"].lower() == nombre.lower():
                    self._seleccionar_producto_canvas(frame)
                    break
        else:
            productos_filtrados = [
                p for p in productos if nombre.lower() in p[1].lower()
            ]
            self.mostrar_productos_en_canvas(productos_filtrados)

    # Método para actualizar productos desde fuera (por ejemplo, desde Inventario)
    def actualizar_canvas_productos(self):
        self.mostrar_productos_inventario()

    def _activar_scroll_canvas(self):
        # Asocia el scroll solo a este canvas
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _desactivar_scroll_canvas(self):
        # Desasocia el scroll de este canvas
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
