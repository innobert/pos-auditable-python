import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import os
from retail.core.config import rutas  # <--- Importa la función rutas
from datetime import datetime

# Importa las funciones del backend
from retail.core.database import (
    add_producto,
    obtener_productos,
    combobox_productos,
    actualizar_producto,
    dlt_producto,
)


def peso_colombiano(value):
    return f"${value:,.0f}".replace(",", ".")


class Inventario(tk.Frame):
    def __init__(self, padre, controlador):
        super().__init__(padre, bg="#E6D9E3")
        self.controlador = controlador
        self.pack(fill="both", expand=True)

        # Usar rutas absolutas para la carpeta de imágenes
        self.img_folder = rutas("fotos")
        if not os.path.exists(self.img_folder):
            os.makedirs(self.img_folder)

        self.ultimo_directorio = os.path.expanduser("~")
        self.columnas = 0  # Contador de columnas
        self.row = 0  # Contador de filas
        self.producto_seleccionado_frame = None
        self.producto_seleccionado_data = None
        self.widgets()
        # Elimina cualquier binding de teclas globales
        self.unbind_all("<Delete>")

    def widgets(self):
        # Título Principal
        label_titulo = tk.Label(
            self,
            text="Inventario",
            font=("Helvetica", 15, "bold"),
            bg="#4CAF50",
            fg="#0A0A0A",
        )
        label_titulo.place(x=0, y=0, width=1100, height=30)

        # Frame lateral izquierdo para datos y botones
        frame_datos = tk.Frame(self, bg="#E6D9E3")
        frame_datos.place(x=0, y=30, width=270, height=620)  # Altura ajustada a la ventana

        # --- LabelFrame Buscar ---
        lf_buscar = tk.LabelFrame(
            frame_datos, text="Buscar", font=("Helvetica", 12, "bold"), bg="#E6D9E3"
        )
        lf_buscar.place(x=10, y=10, width=230, height=70)
        self.entry_buscar = ttk.Combobox(lf_buscar, font=("Helvetica", 11))
        self.entry_buscar.place(x=10, y=10, width=200, height=30)
        self.entry_buscar["values"] = []
        self.productos_cache = []  # Cache de productos para búsquedas

        # --- LabelFrame Selección ---
        lf_seleccion = tk.LabelFrame(
            frame_datos,
            text="Selección",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
        )
        lf_seleccion.place(x=10, y=90, width=250, height=190)
        labels = ["Producto:", "Precio:", "Costo:", "Stock:", "Estado:"]
        self.seleccion_vars = {}
        self.estado_label = None  # Para guardar referencia al label de estado
        for i, text in enumerate(labels):
            tk.Label(
                lf_seleccion,
                text=text,
                font=("Helvetica", 11, "bold"),
                bg="#E6D9E3",
                anchor="w",
            ).place(x=10, y=10 + i * 32)
            var = tk.StringVar(value="")
            self.seleccion_vars[text[:-1].lower()] = var
            # Para el campo Estado, guarda el label para cambiar el color dinámicamente
            if text == "Estado:":
                self.estado_label = tk.Label(
                    lf_seleccion,
                    textvariable=var,
                    font=("Helvetica", 11),
                    bg="#E6D9E3",
                    anchor="w",
                )
                self.estado_label.place(x=90, y=10 + i * 32)
            else:
                tk.Label(
                    lf_seleccion,
                    textvariable=var,
                    font=("Helvetica", 11),
                    bg="#E6D9E3",
                    anchor="w",
                ).place(x=90, y=10 + i * 32)

        # --- LabelFrame Opciones ---
        lf_opciones = tk.LabelFrame(
            frame_datos,
            text="Opciones",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
        )
        lf_opciones.place(x=30, y=300, width=200, height=260)  # Altura extendida

        # Cargar imágenes para los botones desde la carpeta img
        ruta_img = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "img"))
        def cargar_img(nombre):
            try:
                return ImageTk.PhotoImage(Image.open(os.path.join(ruta_img, nombre)).resize((28, 28)))
            except Exception:
                return None

        img_add = cargar_img("add.png")
        img_delete = cargar_img("eliminar.png")
        img_historial = cargar_img("historial.png")
        img_total = cargar_img("total.png")

        # Botón Agregar
        self.btn_agregar = tk.Button(
            lf_opciones,
            text="  Agregar",  # Espacio para separar la imagen del texto
            image=img_add,
            compound="left",
            font=("Helvetica", 13, "bold"),
            bg="#2196F3",
            fg="white",
            activebackground="#1976D2",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.agregar_producto,
            padx=10,  # Espacio horizontal interno
            anchor="w"
        )
        self.btn_agregar.image = img_add
        self.btn_agregar.place(x=25, y=15, width=150, height=40)

        # Botón Eliminar
        self.btn_eliminar = tk.Button(
            lf_opciones,
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
            command=self.eliminar_producto_seleccionado,
            padx=10,
            anchor="w"
        )
        self.btn_eliminar.image = img_delete
        self.btn_eliminar.place(x=25, y=70, width=150, height=40)

        # Botón Historial dentro del LabelFrame Opciones
        self.btn_historial = tk.Button(
            lf_opciones,
            text="  Historial",
            image=img_historial,
            compound="left",
            font=("Helvetica", 13, "bold"),
            bg="#8e24aa",
            fg="white",
            activebackground="#6d1b7b",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.abrir_historial_inventario,
            padx=10,
            anchor="w"
        )
        self.btn_historial.image = img_historial
        self.btn_historial.place(x=25, y=130, width=150, height=40)

        # Botón Totales dentro del LabelFrame Opciones
        self.btn_totales = tk.Button(
            lf_opciones,
            text="  Totales",
            image=img_total,
            compound="left",
            font=("Helvetica", 13, "bold"),
            bg="#4CAF50",
            fg="white",
            activebackground="#388E3C",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.abrir_totales_inventario,
            padx=10,
            anchor="w"
        )
        self.btn_totales.image = img_total
        self.btn_totales.place(x=25, y=185, width=150, height=40)

        # --- LabelFrame Productos ---
        lf_productos = tk.LabelFrame(
            self,
            text="Productos",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
        )
        lf_productos.place(x=280, y=35, width=800, height=570)

        # Canvas y Scrollbar correctamente integrados
        self.canvas = tk.Canvas(
            lf_productos,
            bg="#E6D9E3",
            highlightthickness=0
        )
        self.scrollbar = tk.Scrollbar(lf_productos, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.frame_contenedor = tk.Frame(self.canvas, bg="#E6D9E3")
        self.canvas.create_window((0, 0), window=self.frame_contenedor, anchor="nw")

        # Configura el scrollregion automáticamente
        self.frame_contenedor.bind("<Configure>", self._on_frame_configure)

        # Scroll con la rueda del mouse en cualquier parte del canvas
        self.canvas.bind("<Enter>", self._activar_scroll_canvas)
        self.canvas.bind("<Leave>", self._desactivar_scroll_canvas)
        self.frame_contenedor.bind("<Enter>", self._activar_scroll_canvas)
        self.frame_contenedor.bind("<Leave>", self._desactivar_scroll_canvas)

        # Llenar el combobox de búsqueda con productos de la base de datos
        self.actualizar_combobox_productos()
        self.actualizar_cache_productos()

        # Cargar los productos existentes después de configurar todo
        self.cargar_productos()

        # --- Bindings para el combobox de búsqueda ---
        self.entry_buscar.bind("<KeyRelease>", self.filtrar_productos_combobox)
        self.entry_buscar.bind("<Return>", self.seleccionar_producto_entry)

    def agregar_producto(self):
        """
        Método para agregar un nuevo producto al inventario.
        Abre un cuadro de diálogo para seleccionar una imagen y luego guarda la imagen en la carpeta 'fotos'.
        """
        top = tk.Toplevel(self)
        top.title("Agregar Producto")
        top.geometry("700x400+300+100")
        top.configure(bg="#E6D9E3")
        top.resizable(False, False)
        top.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)

        # Frame principal
        frame_principal = tk.Frame(top, bg="#E6D9E3")
        frame_principal.pack(fill="both", expand=True, padx=20, pady=20)

        # Guardar referencia a la ventana
        self.top = top

        # --- Validadores para los campos numéricos ---
        def validar_entero(valor):
            return valor == "" or (valor.isdigit() and int(valor) > 0)
        vcmd_entero = (self.register(validar_entero), "%P")

        # Frame para los campos de entrada
        frame_campos = tk.Frame(
            frame_principal,
            bg="#E6D9E3",
        )
        frame_campos.place(x=0, y=10, width=280, height=300)

        # Botones
        lf_botones = tk.LabelFrame(
            frame_principal,
            text="Opciones",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
        )
        lf_botones.place(x=0, y=290, width=270, height=60)

        # Botón Guardar
        btn_guardar = tk.Button(
            lf_botones,
            text="Guardar",
            font=("Helvetica", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            command=self.guardar_producto,
        )
        btn_guardar.place(x=10, y=0)

        # Botón Cancelar
        btn_cancelar = tk.Button(
            lf_botones,
            text="Cancelar",
            font=("Helvetica", 12, "bold"),
            bg="#f44336",
            fg="white",
            command=self.cerrar_ventana,
        )
        btn_cancelar.place(x=140, y=0)

        # Frame para la imagen
        self.frame_img = tk.Frame(frame_principal, bg="white", width=300, height=300)
        self.frame_img.place(x=300, y=10)

        # Cargar imagen por defecto
        try:
            default_image_path = rutas(os.path.join("fotos", "default.png"))
            default_image = Image.open(default_image_path)
            default_image = default_image.resize((300, 300), Image.LANCZOS)
            self.image_tk = ImageTk.PhotoImage(default_image)
            img_label = tk.Label(self.frame_img, image=self.image_tk, bg="white")
            img_label.pack(fill="both", expand=True)
            self.image_path = default_image_path
        except Exception as e:
            print(f"Error al cargar la imagen por defecto: {str(e)}")

        # Botón Cargar Imágen
        btn_cargar_imagen = tk.Button(
            frame_principal,
            text="Cargar Imágen",
            font=("Helvetica", 11, "bold"),
            bg="#2196F3",
            fg="white",
            command=self.cargar_imagen,
        )
        btn_cargar_imagen.place(x=370, y=320)

        # Campos de entrada
        tk.Label(
            frame_campos,
            text="Producto",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
        ).pack(anchor="w")
        self.entry_producto = tk.Entry(frame_campos, font=("Helvetica", 12))
        self.entry_producto.pack(fill="x", pady=(0, 10))

        tk.Label(
            frame_campos,
            text="Precio",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
        ).pack(anchor="w")
        self.entry_precio = tk.Entry(
            frame_campos,
            font=("Helvetica", 12),
            validate="key",
            validatecommand=vcmd_entero,
        )
        self.entry_precio.pack(fill="x", pady=(0, 10))

        tk.Label(
            frame_campos, text="Costo", font=("Helvetica", 12, "bold"), bg="#E6D9E3"
        ).pack(anchor="w")
        self.entry_costo = tk.Entry(
            frame_campos,
            font=("Helvetica", 12),
            validate="key",
            validatecommand=vcmd_entero,
        )
        self.entry_costo.pack(fill="x", pady=(0, 10))

        tk.Label(
            frame_campos, text="Stock", font=("Helvetica", 12, "bold"), bg="#E6D9E3"
        ).pack(anchor="w")
        self.entry_stock = tk.Entry(
            frame_campos,
            font=("Helvetica", 12),
            validate="key",
            validatecommand=vcmd_entero,
        )
        self.entry_stock.pack(fill="x", pady=(0, 10))

        tk.Label(
            frame_campos, text="Estado", font=("Helvetica", 12, "bold"), bg="#E6D9E3"
        ).pack(anchor="w")
        self.entry_estado = ttk.Combobox(
            frame_campos,
            font=("Helvetica", 12),
            values=["Disponible", "Agotado"],
            state="readonly",  # <-- Solo permite seleccionar, no escribir
        )
        self.entry_estado.pack(fill="x", pady=(0, 10))
        self.entry_estado.set("Disponible")
        self.entry_estado.config(state="disabled")

    def cargar_imagen(self):
        """Método para cargar una imagen para el producto"""
        try:
            # Crear una ventana de diálogo modal para seleccionar imagen
            dialog = tk.Toplevel(self)
            dialog.withdraw()  # Ocultar la ventana principal

            # Abrir el diálogo de selección de archivo
            file_path = filedialog.askopenfilename(
                parent=dialog,
                initialdir=self.ultimo_directorio,
                title="Seleccionar imagen",
                filetypes=[("Todos los archivos", "*.*")],  # Permitir cualquier archivo
            )

            # Destruir la ventana de diálogo
            dialog.destroy()

            if file_path:
                try:
                    self.ultimo_directorio = os.path.dirname(file_path)
                    image = Image.open(file_path)
                    image = image.resize((300, 300), Image.LANCZOS)

                    image_name = os.path.basename(file_path)
                    image_save_path = os.path.join(self.img_folder, image_name)
                    image.save(image_save_path)

                    # Actualizar la imagen en el frame
                    self.image_tk = ImageTk.PhotoImage(image)
                    for widget in self.frame_img.winfo_children():
                        widget.destroy()
                    img_label = tk.Label(self.frame_img, image=self.image_tk, bg="white")
                    img_label.pack(fill="both", expand=True)

                    self.image_path = image_save_path

                    # --- NUEVO: Si estamos editando, actualizar la variable en el Entry ---
                    if hasattr(self, "top") and self.top:
                        pass
                except Exception as e:
                    messagebox.showerror(
                        "Error", f"Error al cargar la imagen: {str(e)}", parent=self.top
                    )
        except Exception as e:
            messagebox.showerror(
                "Error", f"Error inesperado: {str(e)}", parent=self.top
            )

    def mostrar_producto(
        self, producto, precio, imagen_path, costo=None, stock=None, estado=None, row=0, col=0, columnas_max=3
    ):
        # Ajusta la separación entre productos
        ancho_producto = 450
        alto_producto = 420
        separacion_x = 70  # Separación horizontal mayor
        separacion_y = 36  # Separación vertical mayor

        img_canvas = tk.Frame(
            self.frame_contenedor,
            bg="white",
            width=ancho_producto,
            height=alto_producto,
            bd=1,
            relief="solid",
            highlightthickness=0  # Sin borde por defecto
        )
        img_canvas.grid(
            row=row, column=col, padx=separacion_x//2, pady=separacion_y//2, sticky="nsew"
        )
        img_canvas.grid_propagate(False)  # Mantiene el tamaño fijo

        img_canvas.producto_data = {
            "producto": producto,
            "precio": precio,
            "costo": costo,
            "stock": stock,
            "estado": estado,
            "imagen": imagen_path,
        }

        # Cargar y mostrar la imagen (centrada y cuadrada)
        try:
            imagen = Image.open(
                rutas(imagen_path) if not os.path.isabs(imagen_path) else imagen_path
            )
            imagen = imagen.resize((180, 180), Image.LANCZOS)
            imagen_tk = ImageTk.PhotoImage(imagen)
            img_label = tk.Label(img_canvas, image=imagen_tk, bg="white")
            img_label.image = imagen_tk
            img_label.pack(pady=(30, 10))
            # Bind click y doble click en la imagen
            img_label.bind(
                "<Button-1>",
                lambda e, data=img_canvas.producto_data, frame=img_canvas: self.mostrar_seleccion(
                    data, frame
                ),
            )
            img_label.bind(
                "<Double-Button-1>",
                lambda e, data=img_canvas.producto_data, frame=img_canvas: self.tl_editar(
                    data, frame
                ),
            )
        except Exception as e:
            print(f"Error al cargar la imagen: {str(e)}")

        # Bind click y doble click en todo el frame del producto
        img_canvas.bind(
            "<Button-1>",
            lambda e, data=img_canvas.producto_data, frame=img_canvas: self.mostrar_seleccion(
                data, frame
            ),
        )
        img_canvas.bind(
            "<Double-Button-1>",
            lambda e, data=img_canvas.producto_data, frame=img_canvas: self.tl_editar(
                data, frame
            ),
        )

        # Nombre del producto (negrita)
        tk.Label(
            img_canvas, text=producto, font=("Helvetica", 16, "bold"), bg="white", anchor="w"
        ).pack(fill="x", padx=10, pady=(0, 0))

        # Precio
        tk.Label(
            img_canvas, text=peso_colombiano(precio), font=("Helvetica", 15), bg="white", anchor="w"
        ).pack(fill="x", padx=10, pady=(0, 10))

        self.columnas += 1
        if self.columnas >= 3:
            self.columnas = 0
            self.row += 1

    def mostrar_seleccion(self, data, frame=None):
        # Limpia el efecto de selección anterior sin modificar el diseño
        if (
            self.producto_seleccionado_frame
            and self.producto_seleccionado_frame.winfo_exists()
        ):
            # Elimina el borde de selección anterior
            self.producto_seleccionado_frame.config(
                highlightbackground="white",
                highlightcolor="white",
                highlightthickness=0,
                bd=1,
                relief="solid"
            )
        self.producto_seleccionado_frame = None

        # Aplica un borde sutil al frame seleccionado
        if frame:
            frame.config(
                highlightbackground="#2196F3",
                highlightcolor="#2196F3",
                highlightthickness=3,
                bd=1,
                relief="solid"
            )
            self.producto_seleccionado_frame = frame

        # Carga la información en el LabelFrame de Selección
        self.seleccion_vars["producto"].set(data["producto"])
        self.seleccion_vars["precio"].set(peso_colombiano(data["precio"]))
        self.seleccion_vars["costo"].set(peso_colombiano(data["costo"]))
        self.seleccion_vars["stock"].set(str(data["stock"]))
        self.seleccion_vars["estado"].set(data["estado"])
        # Cambia el color del estado según el valor
        if self.estado_label:
            if data["estado"] == "Disponible":
                self.estado_label.config(fg="green")
            elif data["estado"] == "Agotado":
                self.estado_label.config(fg="red")
            else:
                self.estado_label.config(fg="black")

    def actualizar_combobox_productos(self):
        productos = combobox_productos()
        self.entry_buscar["values"] = []

    def actualizar_cache_productos(self):
        self.productos_cache = obtener_productos()

    def filtrar_productos_combobox(self, event=None):
        """
        Filtra el combobox y el canvas de productos por coincidencia parcial en el nombre.
        """
        texto = self.entry_buscar.get().strip().lower()
        if not texto:
            productos = obtener_productos()
        else:
            productos = [p for p in obtener_productos() if texto in p[1].lower()]
        self.productos_cache = productos
        self.entry_buscar["values"] = [p[1] for p in productos]
        self.mostrar_productos_en_canvas(productos)

    def mostrar_productos_en_canvas(self, productos):
        for widget in self.frame_contenedor.winfo_children():
            widget.destroy()
        self.columnas = 0
        self.row = 0
        columnas_max = 3
        filas_max = 3
        total_productos = len(productos)
        for idx, producto in enumerate(productos):
            bloque = idx // (columnas_max * filas_max)
            idx_en_bloque = idx % (columnas_max * filas_max)
            row = (idx_en_bloque // columnas_max) + (bloque * filas_max)
            col = idx_en_bloque % columnas_max
            if (idx_en_bloque // columnas_max) == filas_max - 1:
                productos_restantes = total_productos - idx
                productos_en_esta_fila = min(productos_restantes, columnas_max)
                centrar = (columnas_max - productos_en_esta_fila) // 2
                col_centrada = col + centrar
            else:
                col_centrada = col
            self.mostrar_producto(
                producto=producto[1],
                precio=producto[2],
                imagen_path=producto[6],
                costo=producto[3],
                stock=producto[4],
                estado="Disponible" if producto[5] == 1 else "Agotado",
                row=row,
                col=col_centrada,
                columnas_max=columnas_max
            )

    def seleccionar_producto_entry(self, event=None):
        """
        Si el usuario presiona Enter, muestra solo el producto exacto si existe,
        si no, muestra coincidencias parciales.
        """
        nombre = self.entry_buscar.get().strip()
        productos = self.productos_cache if self.productos_cache else obtener_productos()
        if nombre == "":
            self.mostrar_productos_en_canvas(productos)
            return
        seleccionados = [p for p in productos if p[1].lower() == nombre.lower()]
        if seleccionados:
            self.mostrar_productos_en_canvas(seleccionados)
            for frame in self.frame_contenedor.winfo_children():
                data = getattr(frame, "producto_data", None)
                if data and data["producto"].lower() == nombre.lower():
                    self.mostrar_seleccion(data, frame)
                    self.canvas.update_idletasks()
                    y = frame.winfo_y()
                    total_height = max(1, self.frame_contenedor.winfo_height())
                    self.canvas.yview_moveto(y / total_height)
                    break
        else:
            productos_filtrados = [p for p in productos if nombre.lower() in p[1].lower()]
            self.mostrar_productos_en_canvas(productos_filtrados)

    def cargar_productos(self):
        """Carga los productos desde la base de datos y los muestra en la interfaz"""
        productos = obtener_productos()
        self.productos_cache = productos
        self.mostrar_productos_en_canvas(productos)

    def guardar_producto(self):
        """Guarda el producto en la base de datos"""
        try:
            producto = self.entry_producto.get().strip()
            precio_str = self.entry_precio.get().strip()
            costo_str = self.entry_costo.get().strip()
            stock_str = self.entry_stock.get().strip()

            # Validación de campos vacíos
            if not all([producto, precio_str, costo_str, stock_str]):
                messagebox.showerror("Error de validación", "Todos los campos son obligatorios", parent=self.top)
                return

            # Validación de números enteros positivos para precio, costo y stock
            if not (precio_str.isdigit() and int(precio_str) > 0):
                messagebox.showerror("Error de validación", "El precio debe ser un número entero positivo mayor a 0.", parent=self.top)
                return
            if not (costo_str.isdigit() and int(costo_str) > 0):
                messagebox.showerror("Error de validación", "El costo debe ser un número entero positivo mayor a 0.", parent=self.top)
                return
            if not (stock_str.isdigit() and int(stock_str) > 0):
                messagebox.showerror("Error de validación", "El stock debe ser un número entero positivo mayor a 0.", parent=self.top)
                return

            precio = int(precio_str)
            costo = int(costo_str)
            stock = int(stock_str)
            estado = 1 if stock > 0 else 0
            imagen = self.image_path if hasattr(self, "image_path") else None

            # --- Validación de precio y costo ---
            if costo > precio:
                perdida = (costo - precio) * stock
                if not messagebox.askyesno(
                    "Advertencia",
                    f"El costo ({peso_colombiano(costo)}) es mayor que el precio ({peso_colombiano(precio)}).\n"
                    f"Esto generará una pérdida de {peso_colombiano(perdida)}.\n¿Desea continuar?",
                    parent=self.top
                ):
                    return
            elif precio == costo:
                if not messagebox.askyesno(
                    "Advertencia",
                    "El precio y el costo son iguales.\nNo se generará ninguna ganancia.\n¿Desea continuar?",
                    parent=self.top
                ):
                    return

            add_producto(producto, precio, costo, stock, estado, imagen)
            self.cargar_productos()
            self.actualizar_combobox_productos()
            self._actualizar_ventas_canvas()

            # --- REGISTRO EN HISTORIAL ---
            from retail.core.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id_producto FROM inventario WHERE producto = ?", (producto,))
            id_producto = cursor.fetchone()[0]
            now = datetime.now()
            dia = now.strftime("%A")
            fecha = now.strftime("%Y-%m-%d")
            hora = now.strftime("%H:%M:%S")
            accion = "Agregar"
            pedido = stock  # Al agregar, el pedido es igual al stock inicial
            ganancia = (precio - costo) * stock
            total = precio * stock
            cursor.execute(
                """
                INSERT INTO historial_inventario
                (id_producto, dia, fecha, hora, accion, pedido, stock, precio, costo, ganancia, total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (id_producto, dia, fecha, hora, accion, pedido, stock, precio, costo, ganancia, total)
            )
            conn.commit()
            conn.close()

            messagebox.showinfo(
                "Éxito", "Producto agregado correctamente", parent=self.top
            )
            if hasattr(self, "top") and self.top:
                self.top.destroy()
                self.top = None

        except Exception as e:
            messagebox.showerror(
                "Error", f"Error al guardar el producto: {str(e)}", parent=self.top
            )
            # No cerrar la ventana en caso de error

    def tl_editar(self, data, frame):
        top = tk.Toplevel(self)
        top.title("Editar Producto")
        top.geometry("700x400+300+100")
        top.configure(bg="#E6D9E3")
        top.resizable(False, False)
        top.lift()
        top.protocol("WM_DELETE_WINDOW", self.cerrar_ventana)
        self.top = top

        frame_principal = tk.Frame(top, bg="#E6D9E3")
        frame_principal.pack(fill="both", expand=True, padx=20, pady=20)

        # --- Validadores para los campos numéricos ---
        def validar_entero(valor):
            return valor == "" or (valor.isdigit() and int(valor) > 0)
        vcmd_entero = (self.register(validar_entero), "%P")

        frame_campos = tk.Frame(frame_principal, bg="#E6D9E3")
        frame_campos.place(x=0, y=10, width=280, height=300)

        lf_botones = tk.LabelFrame(
            frame_principal,
            text="Opciones",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
        )
        lf_botones.place(x=0, y=290, width=270, height=60)

        btn_guardar = tk.Button(
            lf_botones,
            text="Guardar",
            font=("Helvetica", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            command=lambda: self.guardar_edicion_producto(data),
        )
        btn_guardar.place(x=10, y=0)

        btn_cancelar = tk.Button(
            lf_botones,
            text="Cancelar",
            font=("Helvetica", 12, "bold"),
            bg="#f44336",
            fg="white",
            command=self.cerrar_ventana,
        )
        btn_cancelar.place(x=140, y=0)

        self.frame_img = tk.Frame(frame_principal, bg="white", width=300, height=300)
        self.frame_img.place(x=300, y=10)

        # Imagen
        try:
            imagen_path = data.get(
                "imagen", rutas(os.path.join("fotos", "default.png"))
            )
            default_image = Image.open(
                rutas(imagen_path) if not os.path.isabs(imagen_path) else imagen_path
            )
            default_image = default_image.resize((300, 300), Image.LANCZOS)
            self.image_tk = ImageTk.PhotoImage(default_image)
            img_label = tk.Label(self.frame_img, image=self.image_tk, bg="white")
            img_label.pack(fill="both", expand=True)
            self.image_path = imagen_path
        except Exception as e:
            print(f"Error al cargar la imagen por defecto: {str(e)}")

        btn_cargar_imagen = tk.Button(
            frame_principal,
            text="Cargar Imágen",
            font=("Helvetica", 11, "bold"),
            bg="#2196F3",
            fg="white",
            command=self.cargar_imagen,
        )
        btn_cargar_imagen.place(x=370, y=320)

        # Campos de entrada
        tk.Label(
            frame_campos,
            text="Producto",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
        ).pack(anchor="w")
        self.entry_producto = tk.Entry(frame_campos, font=("Helvetica", 12))
        self.entry_producto.pack(fill="x", pady=(0, 10))
        self.entry_producto.insert(0, data["producto"])

        tk.Label(
            frame_campos,
            text="Precio",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
        ).pack(anchor="w")
        self.entry_precio = tk.Entry(
            frame_campos,
            font=("Helvetica", 12),
            validate="key",
            validatecommand=vcmd_entero,
        )
        self.entry_precio.pack(fill="x", pady=(0, 10))
        self.entry_precio.insert(0, str(int(data["precio"])))

        tk.Label(
            frame_campos, text="Costo", font=("Helvetica", 12, "bold"), bg="#E6D9E3"
        ).pack(anchor="w")
        self.entry_costo = tk.Entry(
            frame_campos,
            font=("Helvetica", 12),
            validate="key",
            validatecommand=vcmd_entero,
        )
        self.entry_costo.pack(fill="x", pady=(0, 10))
        self.entry_costo.insert(0, str(int(data["costo"])))

        tk.Label(
            frame_campos, text="Stock", font=("Helvetica", 12, "bold"), bg="#E6D9E3"
        ).pack(anchor="w")
        self.entry_stock = tk.Entry(
            frame_campos,
            font=("Helvetica", 12),
            validate="key",
            validatecommand=vcmd_entero,
        )
        self.entry_stock.pack(fill="x", pady=(0, 10))
        self.entry_stock.insert(0, data["stock"])

        tk.Label(
            frame_campos, text="Estado", font=("Helvetica", 12, "bold"), bg="#E6D9E3"
        ).pack(anchor="w")
        self.entry_estado = ttk.Combobox(
            frame_campos,
            font=("Helvetica", 12),
            values=["Disponible", "Agotado"],
            state="readonly",
        )
        self.entry_estado.pack(fill="x", pady=(0, 10))
        self.entry_estado.set(data["estado"])
        self.entry_estado.config(state="disabled")

        top.after_idle(top.grab_set)  # <-- Esto reemplaza top.grab_set()

    def guardar_edicion_producto(self, data):
        """Guarda los cambios de un producto editado en la base de datos"""
        try:
            producto = self.entry_producto.get().strip()
            precio_str = self.entry_precio.get().strip()
            costo_str = self.entry_costo.get().strip()
            stock_str = self.entry_stock.get().strip()

            # Validación de campos vacíos
            if not all([producto, precio_str, costo_str, stock_str]):
                messagebox.showerror("Error de validación", "Todos los campos son obligatorios", parent=self.top)
                return

            # Validación de números enteros positivos para precio, costo y stock
            if not (precio_str.isdigit() and int(precio_str) > 0):
                messagebox.showerror("Error de validación", "El precio debe ser un número entero positivo mayor a 0.", parent=self.top)
                return
            if not (costo_str.isdigit() and int(costo_str) > 0):
                messagebox.showerror("Error de validación", "El costo debe ser un número entero positivo mayor a 0.", parent=self.top)
                return
            if not (stock_str.isdigit() and int(stock_str) > 0):
                messagebox.showerror("Error de validación", "El stock debe ser un número entero positivo mayor a 0.", parent=self.top)
                return

            precio = int(precio_str)
            costo = int(costo_str)
            stock = int(stock_str)
            estado = 1 if stock > 0 else 0

            # --- Validación de precio y costo ---
            if costo > precio:
                perdida = (costo - precio) * stock
                if not messagebox.askyesno(
                    "Advertencia",
                    f"El costo ({peso_colombiano(costo)}) es mayor que el precio ({peso_colombiano(precio)}).\n"
                    f"Esto generará una pérdida de {peso_colombiano(perdida)}.\n¿Desea continuar?",
                    parent=self.top
                ):
                    return
            elif precio == costo:
                if not messagebox.askyesno(
                    "Advertencia",
                    "El precio y el costo son iguales.\nNo se generará ninguna ganancia.\n¿Desea continuar?",
                    parent=self.top
                ):
                    return

            # Busca el id_producto en la base de datos
            productos = obtener_productos()
            id_producto = None
            stock_anterior = None
            for p in productos:
                if (
                    p[1] == data["producto"]
                    and p[2] == data["precio"]
                    and p[3] == data["costo"]
                    and p[4] == data["stock"]
                ):
                    id_producto = p[0]
                    stock_anterior = p[4]
                    break

            if id_producto is None:
                raise ValueError("No se pudo identificar el producto a editar.")

            imagen = self.image_path if hasattr(self, "image_path") else data["imagen"]

            actualizar_producto(
                id_producto, producto, precio, costo, stock, estado, imagen
            )
            self.cargar_productos()
            self.actualizar_combobox_productos()
            self._actualizar_ventas_canvas()

            # --- REGISTRO EN HISTORIAL ---
            from retail.core.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            now = datetime.now()
            dia = now.strftime("%A")
            fecha = now.strftime("%Y-%m-%d")
            hora = now.strftime("%H:%M:%S")
            accion = "Editar"
            # Lógica de pedido:
            if stock_anterior is not None and stock > stock_anterior:
                pedido = stock - stock_anterior
            else:
                pedido = 0
            ganancia = (precio - costo) * stock
            total = precio * stock
            cursor.execute(
                """
                INSERT INTO historial_inventario
                (id_producto, dia, fecha, hora, accion, pedido, stock, precio, costo, ganancia, total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (id_producto, dia, fecha, hora, accion, pedido, stock, precio, costo, ganancia, total)
            )
            conn.commit()
            conn.close()

            messagebox.showinfo(
                "Éxito", "Producto actualizado correctamente", parent=self.top
            )
            if hasattr(self, "top") and self.top:
                self.top.destroy()
                self.top = None

        except Exception as e:
            messagebox.showerror(
                "Error", f"Error al actualizar el producto: {str(e)}", parent=self.top
            )
            # No cerrar la ventana en caso de error

    def eliminar_producto_seleccionado(self):
        # Busca el producto seleccionado
        producto = self.seleccion_vars["producto"].get()
        if not producto:
            messagebox.showwarning(
                "Advertencia", "Seleccione un producto para eliminar."
            )
            return

        # Busca el id_producto en la base de datos
        productos = obtener_productos()
        id_producto = None
        for p in productos:
            if p[1] == producto:
                id_producto = p[0]
                break

        if id_producto is None:
            messagebox.showerror(
                "Error", "No se pudo identificar el producto a eliminar."
            )
            return

        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este producto?"):
            dlt_producto(id_producto)
            self.cargar_productos()
            self.actualizar_combobox_productos()
            self._actualizar_ventas_canvas()
            for var in self.seleccion_vars.values():
                var.set("")

    def cerrar_ventana(self):
        self.top.destroy()
        self.top = None

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _activar_scroll_canvas(self, event=None):
        # Asocia el scroll solo cuando el mouse está dentro del canvas/frame_contenedor
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel_windows)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _desactivar_scroll_canvas(self, event=None):
        # Desasocia el scroll cuando el mouse sale del canvas/frame_contenedor
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel_windows(self, event):
        # Scroll siempre que el mouse esté dentro del canvas o frame_contenedor
        widget = self.winfo_containing(event.x_root, event.y_root)
        if widget and (widget == self.canvas or widget.winfo_toplevel() == self.canvas.winfo_toplevel()):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux(self, event):
        widget = self.winfo_containing(event.x_root, event.y_root)
        if widget and (widget == self.canvas or widget.winfo_toplevel() == self.canvas.winfo_toplevel()):
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    def filtrar_productos(self, event=None):
        texto = self.entry_buscar.get().lower()
        productos = obtener_productos()
        if texto == "":
            # Si el texto está vacío, muestra todos los productos y todos los nombres en el combobox
            productos_filtrados = productos
            self.entry_buscar["values"] = [p[1] for p in productos]
        else:
            # Filtra productos por coincidencia parcial en el nombre
            productos_filtrados = [p for p in productos if texto in p[1].lower()]
            self.entry_buscar["values"] = [p[1] for p in productos_filtrados]
        # Limpia y muestra solo los productos filtrados en el Canvas
        for widget in self.frame_contenedor.winfo_children():
            widget.destroy()
        self.columnas = 0
        self.row = 0
        for producto in productos_filtrados:
            self.mostrar_producto(
                producto=producto[1],
                precio=producto[2],
                imagen_path=producto[6],
                costo=producto[3],
                stock=producto[4],
                estado="Disponible" if producto[5] == 1 else "Agotado",
            )

    def seleccionar_producto_busqueda(self, event=None):
        nombre = self.entry_buscar.get().strip()
        productos = obtener_productos()
        for widget in self.frame_contenedor.winfo_children():
            widget.destroy()
        self.columnas = 0
        self.row = 0
        seleccionado = None
        for producto in productos:
            if producto[1].lower() == nombre.lower():
                seleccionado = producto
                self.mostrar_producto(
                    producto=producto[1],
                    precio=producto[2],
                    imagen_path=producto[6],
                    costo=producto[3],
                    stock=producto[4],
                    estado="Disponible" if producto[5] == 1 else "Agotado",
                )
                break
        # Si se encontró, selecciona visualmente el producto
        if seleccionado:
            for frame in self.frame_contenedor.winfo_children():
                data = getattr(frame, "producto_data", None)
                if data and data["producto"].lower() == nombre.lower():
                    self.mostrar_seleccion(data, frame)
                    # Hacer scroll hasta el producto seleccionado usando winfo_y()
                    self.canvas.update_idletasks()
                    y = frame.winfo_y()
                    total_height = max(1, self.frame_contenedor.winfo_height())
                    self.canvas.yview_moveto(y / total_height)
                    break

    def actualizar_estado_por_stock(self, event=None):
        try:
            stock = int(self.entry_stock.get())
        except ValueError:
            stock = 0
        if stock > 0:
            self.entry_estado.set("Disponible")
        else:
            self.entry_estado.set("Agotado")

    def _actualizar_ventas_canvas(self):
        """
        Llama a la función de actualización de productos en la vista de ventas si existe.
        """
        parent = self.master
        while parent:
            if hasattr(parent, "ventas_view"):
                parent.ventas_view.actualizar_canvas_productos()
                break
            parent = getattr(parent, "master", None)

    def abrir_historial_inventario(self):
        from retail.inventario.historial_inventario import mostrar_historial_inventario
        mostrar_historial_inventario(self)

    def abrir_totales_inventario(self):
        from retail.inventario.totales import mostrar_totales_inventario
        mostrar_totales_inventario(self)
