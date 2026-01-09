import tkinter as tk
from tkinter import ttk, messagebox, END
from retail.core import database
import os
from PIL import Image, ImageTk
import re


class Clientes(tk.Frame):
    def __init__(self, padre, controlador):
        super().__init__(padre)
        self.controlador = controlador
        self.pack(fill="both", expand=True)
        self.widgets()

    def widgets(self):
        # =========================
        # SECCIÓN CLIENTES
        # =========================
        # Título Principal
        label_titulo = tk.Label(
            self,
            text="Clientes",
            font=("Helvetica", 15, "bold"),
            bg="#FF9800",
            fg="#0A0A0A",
        )
        label_titulo.place(x=0, y=0, width=1100, height=30)

        # Frame principal para dividir la vista en dos secciones
        frame_principal = tk.Frame(self, bg="#E6D9E3")
        frame_principal.place(
            x=0, y=30, width=1100, height=580
        )  # 650 - 40(menu) - 30(titulo)

        # Frame 1: Opciones de búsqueda, entradas y botones (30% del ancho)
        frame1 = tk.Frame(frame_principal, bg="#E6D9E3", padx=10, pady=10)
        frame1.place(x=0, y=0, width=330, height=580)  # 30% del ancho de 1100

        # Label Frame para búsqueda (solo el combobox, sin texto extra)
        lf_buscar = tk.LabelFrame(
            frame1,
            text="Búsqueda",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
            fg="#0A0A0A",
        )
        lf_buscar.pack(fill="x", pady=(0, 10))

        self.combo_clientes = ttk.Combobox(
            lf_buscar,
            font=("Helvetica", 11),
            state="normal",  # Permite escribir
            width=25,
            values=database.combobox_clientes(),
        )
        self.combo_clientes.pack(fill="x", padx=5, pady=5)
        self.combo_clientes.bind("<KeyRelease>", self.filtrar_clientes)
        self.combo_clientes.bind("<<ComboboxSelected>>", self.filtrar_clientes)

        # Sub-frame para los campos de entrada
        frame_form = tk.Frame(frame1, bg="#E6D9E3")
        frame_form.pack(fill="x", pady=10)

        # Validadores para los campos
        def validar_string(valor):
            return re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ ]*", valor) is not None

        def validar_entero(valor):
            return valor == "" or (valor.isdigit() and int(valor) > 0)

        def validar_zona(valor):
            return re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9 ]*", valor) is not None

        vcmd_string = (self.register(validar_string), "%P")
        vcmd_entero = (self.register(validar_entero), "%P")
        vcmd_zona = (self.register(validar_zona), "%P")

        campos = [
            ("Nombres", "entry_nombres", vcmd_string),
            ("Apellidos", "entry_apellidos", vcmd_string),
            ("Cédula", "entry_cedula", vcmd_entero),
            ("Celular", "entry_celular", vcmd_entero),
            ("Zona", "entry_zona", vcmd_zona),
        ]

        self.entries = {}
        for text, key, vcmd in campos:
            frame_campo = tk.Frame(frame_form, bg="#E6D9E3")
            frame_campo.pack(fill="x", pady=5)
            tk.Label(
                frame_campo,
                text=text,
                bg="#E6D9E3",
                font=("Helvetica", 12, "bold"),
                width=10,
                anchor="w",
            ).pack(side="left")
            entry = ttk.Entry(
                frame_campo,
                font=("Helvetica", 12, "bold"),
                validate="key",
                validatecommand=vcmd,
            )
            entry.pack(side="left", fill="x", expand=True, padx=5)
            self.entries[key] = entry

        # --- LabelFrame Opciones (Botones con imágenes y estilo, uno debajo del otro, tamaño igual a inventario.py) ---
        lf_opciones = tk.LabelFrame(
            frame1,
            text="Opciones",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
        )
        lf_opciones.place(x=50, y=300, width=200, height=200)  # Más grande y alineado como inventario.py

        # Cargar imágenes para los botones desde la carpeta img
        ruta_img = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "img"))

        def cargar_img(nombre):
            try:
                return ImageTk.PhotoImage(Image.open(os.path.join(ruta_img, nombre)).resize((28, 28)))
            except Exception:
                return None

        img_add = cargar_img("add.png")
        img_delete = cargar_img("eliminar.png")
        img_clear = cargar_img("limpiar.png")

        # Mantener referencias para evitar garbage collection
        self._imgs_btns = [img_add, img_delete, img_clear]

        # Botón Agregar
        self.btn_agregar = tk.Button(
            lf_opciones,
            text="  Agregar",
            image=img_add,
            compound="left",
            font=("Helvetica", 13, "bold"),
            bg="#2196F3",
            fg="white",
            activebackground="#388E3C",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.agregar_cliente,
            padx=10,
            anchor="w"
        )
        self.btn_agregar.image = img_add
        self.btn_agregar.place(x=25, y=15, width=150, height=40)

        # Botón Desactivar
        self.btn_eliminar = tk.Button(
            lf_opciones,
            text="  Desactivar",
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
            command=self.eliminar_cliente,
            padx=10,
            anchor="w"
        )
        self.btn_eliminar.image = img_delete
        self.btn_eliminar.place(x=25, y=70, width=150, height=40)

        # Botón Limpiar
        self.btn_limpiar = tk.Button(
            lf_opciones,
            text="  Limpiar",
            image=img_clear,
            compound="left",
            font=("Helvetica", 13, "bold"),
            bg="#9E9E9E",
            fg="white",
            activebackground="#757575",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.limpiar_campos,
            padx=10,
            anchor="w"
        )
        self.btn_limpiar.image = img_clear
        self.btn_limpiar.place(x=25, y=125, width=150, height=40)

        # Frame 2: Tabla de clientes (70% del ancho)
        frame2 = tk.Frame(frame_principal, bg="#E6D9E3", padx=10, pady=10)
        frame2.place(x=330, y=0, width=770, height=580)  # 70% del ancho de 1100

        # --- ESTILO DE LA TABLA (Treeview) ---
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Calibri", 14, "bold"), background="#E6D9E3", foreground="#333")
        style.configure("Treeview", font=("Calibri", 13), rowheight=32, background="#fff", fieldbackground="#fff")
        style.map("Treeview", background=[("selected", "#222")], foreground=[("selected", "#fff")])

        # Configurar la tabla para que ocupe todo el espacio del frame
        self.tree = ttk.Treeview(
            frame2,
            columns=("id_cliente", "nombres", "apellidos", "cedula", "celular", "zona"),
            show="headings",
            selectmode="browse",
            style="Treeview"
        )

        # Definir las columnas con sus identificadores y anchos
        columnas = [
            ("id_cliente", "ID", 50),
            ("nombres", "Nombres", 150),
            ("apellidos", "Apellidos", 150),
            ("cedula", "Cédula", 120),
            ("celular", "Celular", 120),
            ("zona", "Zona", 120),
        ]

        for col_id, col_text, width in columnas:
            self.tree.heading(col_id, text=col_text)
            self.tree.column(col_id, width=width, anchor="center")

        # Asociar el evento de doble clic para editar celdas
        self.tree.bind("<Double-1>", self.editar_celda)

        # Asociar el evento de selección en la tabla para llenar los campos
        self.tree.bind("<<TreeviewSelect>>", self.cargar_formulario)

        # Scrollbar para la tabla
        scroll = ttk.Scrollbar(frame2, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Mostrar los datos de clientes al iniciar
        self.cargar_datos()

    # --------------------------
    # Funciones de base de datos (Clientes)
    # --------------------------
    def buscar_cliente_nombre(self, event=None):
        """
        Filtra la tabla de clientes por el nombre seleccionado en el combobox.
        """
        nombre = self.combo_clientes.get()
        self.tree.delete(*self.tree.get_children())
        try:
            clientes = database.buscar_clientes_por_nombre(nombre)
            for cliente in clientes:
                self.tree.insert("", tk.END, values=cliente)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo buscar el cliente: {e}")

    def filtrar_clientes(self, event=None):
        """
        Filtra la tabla de clientes por coincidencia parcial del texto ingresado en el combobox.
        Si no hay coincidencias, la tabla queda vacía.
        Si el campo está vacío, muestra todos los clientes.
        No muestra clientes cuya zona sea 'Negocio'.
        """
        texto = self.combo_clientes.get().strip().lower()
        self.tree.delete(*self.tree.get_children())
        try:
            clientes = database.obtener_clientes()
            # Filtrar clientes cuya zona no sea "Negocio" primero
            clientes = [c for c in clientes if str(c[5]).strip().lower() != "negocio"]
            if texto == "":
                for cliente in clientes:
                    self.tree.insert("", tk.END, values=cliente)
            else:
                coincidencias = [
                    cliente
                    for cliente in clientes
                    if texto in cliente[1].lower()  # cliente[1] es 'nombres'
                ]
                for cliente in coincidencias:
                    self.tree.insert("", tk.END, values=cliente)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo buscar el cliente: {e}")

    def cargar_datos(self):
        """
        Carga los datos de los clientes en la tabla, ordenados por id_cliente.
        Solo muestra clientes cuya zona NO sea 'Negocio'.
        """
        self.tree.delete(*self.tree.get_children())
        try:
            # Actualizar el combobox de búsqueda
            clientes = database.obtener_clientes()
            clientes = [c for c in clientes if str(c[5]).strip().lower() != "negocio"]
            self.combo_clientes["values"] = [f"{c[1]}" for c in clientes]
            self.combo_clientes.set("")  # Limpiar el campo de búsqueda
            for cliente in clientes:
                self.tree.insert("", tk.END, values=cliente)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los datos: {e}")

    # --------------------------
    # Funciones CRUD (Clientes)
    # --------------------------
    def agregar_cliente(self):
        """
        Agrega un nuevo cliente a la base de datos.
        """
        datos = [entry.get().strip() for entry in self.entries.values()]

        # Validaciones estrictas
        if not all(datos):
            messagebox.showwarning("Campos vacíos", "Todos los campos son obligatorios")
            return

        # Nombres y Apellidos solo letras y espacios
        if not all(re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ ]+", datos[i]) for i in [0, 1]):
            messagebox.showwarning("Datos inválidos", "Nombres y Apellidos solo deben contener letras y espacios")
            return

        # Zona solo letras, números y espacios
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9 ]+", datos[4]):
            messagebox.showwarning("Datos inválidos", "Zona solo debe contener letras, números y espacios")
            return

        # Cédula y Celular solo números enteros positivos
        if not (datos[2].isdigit() and int(datos[2]) > 0 and datos[3].isdigit() and int(datos[3]) > 0):
            messagebox.showwarning(
                "Datos inválidos", "Cédula y celular deben ser números enteros positivos"
            )
            return

        try:
            # Verificar si ya existe un cliente con la misma cédula
            resultado = database.buscar_cliente_por_cedula(datos[2])
            if resultado:
                messagebox.showerror(
                    "Duplicado", "Ya existe un cliente con esta cédula"
                )
                return

            # Verificar si ya existe un cliente con el mismo celular
            if self._celular_duplicado(datos[3]):
                messagebox.showerror(
                    "Duplicado", "Ya existe un cliente con este celular"
                )
                return

            # Insertar el cliente en la base de datos
            database.insertar_cliente(*datos)
            self.cargar_datos()
            self.limpiar_campos()

            messagebox.showinfo("Éxito", "Cliente agregado correctamente")
        except Exception as e:
            if "UNIQUE constraint failed: clientes.celular" in str(e):
                messagebox.showerror(
                    "Duplicado", "Ya existe un cliente con este celular"
                )
            else:
                messagebox.showerror("Error", f"No se pudo agregar el cliente: {e}")

    def _celular_duplicado(self, celular):
        """
        Verifica si ya existe un cliente con el mismo celular.
        """
        try:
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id_cliente FROM clientes WHERE celular = ?", (celular,)
            )
            resultado = cursor.fetchone()
            conn.close()
            return resultado is not None
        except Exception:
            return False

    def eliminar_cliente(self):
        """
        Desactiva el cliente seleccionado en la tabla.
        """
        seleccionado = self.tree.selection()
        if not seleccionado:
            messagebox.showwarning("Advertencia", "Seleccione un cliente para desactivar")
            return

        id_cliente = self.tree.item(seleccionado[0], "values")[0]

        if messagebox.askyesno(
            "Confirmar desactivación", "¿Está seguro de desactivar este cliente?"
        ):
            try:
                database.eliminar_cliente(id_cliente)
                self.cargar_datos()
                self.limpiar_campos()
                messagebox.showinfo("Éxito", "Cliente desactivado correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo desactivar el cliente: {e}")

    def editar_celda(self, event):
        """
        Permite editar una celda seleccionada en la tabla con un diseño mejorado.
        """
        columna = self.tree.identify_column(event.x)
        item = self.tree.selection()[0]
        columna_texto = self.tree.heading(columna)["text"]

        if columna_texto == "ID":  # No permitir editar el ID
            return

        columnas_db = {
            "Nombres": "nombres",
            "Apellidos": "apellidos",
            "Cédula": "cedula",
            "Celular": "celular",
            "Zona": "zona",
        }

        columna_db = columnas_db.get(columna_texto)
        if not columna_db:
            messagebox.showerror("Error", "No se puede editar esta columna")
            return

        # Obtener el valor actual
        valor_actual = self.tree.item(item, "values")[int(columna[1:]) - 1]

        # Crear la ventana emergente
        popup = tk.Toplevel(self)
        popup.title(f"Editar {columna_texto}")
        popup.geometry("400x250+450+200")
        popup.resizable(False, False)
        popup.transient(self)
        popup.protocol("WM_DELETE_WINDOW", lambda: popup.destroy())
        self.after(100, lambda: popup.grab_set())
        popup.focus_force()

        frame_popup = tk.Frame(popup, bg="#F5F5F5", padx=20, pady=20)
        frame_popup.pack(fill="both", expand=True)

        tk.Label(
            frame_popup,
            text=f"Editar {columna_texto}",
            font=("Helvetica", 14, "bold"),
            bg="#F5F5F5",
            fg="#333333",
        ).pack(pady=10)

        tk.Label(
            frame_popup,
            text="Nuevo valor:",
            font=("Helvetica", 12),
            bg="#F5F5F5",
            fg="#333333",
        ).pack(anchor="w", pady=5)

        # --- Validadores para el Entry de edición ---
        def validar_string_popup(valor):
            return re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ ]*", valor) is not None

        def validar_entero_popup(valor):
            return valor == "" or (valor.isdigit() and int(valor) > 0)

        def validar_zona_popup(valor):
            return re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9 ]*", valor) is not None

        if columna_texto in ["Nombres", "Apellidos"]:
            vcmd_popup = (self.register(validar_string_popup), "%P")
            validate_type = "key"
        elif columna_texto in ["Cédula", "Celular"]:
            vcmd_popup = (self.register(validar_entero_popup), "%P")
            validate_type = "key"
        elif columna_texto == "Zona":
            vcmd_popup = (self.register(validar_zona_popup), "%P")
            validate_type = "key"
        else:
            vcmd_popup = None
            validate_type = None

        if vcmd_popup:
            nuevo_valor = ttk.Entry(frame_popup, font=("Helvetica", 12), width=30, validate=validate_type, validatecommand=vcmd_popup)
        else:
            nuevo_valor = ttk.Entry(frame_popup, font=("Helvetica", 12), width=30)
        nuevo_valor.pack(pady=5)
        nuevo_valor.insert(0, valor_actual)

        frame_botones = tk.Frame(frame_popup, bg="#F5F5F5")
        frame_botones.pack(pady=20)

        def guardar_cambios(event=None):
            """
            Guarda los cambios realizados en la celda.
            """
            nuevo_valor_texto = nuevo_valor.get().strip()

            if not nuevo_valor_texto:
                messagebox.showwarning(
                    "Valor vacío", "El nuevo valor no puede estar vacío", parent=popup
                )
                return

            try:
                id_cliente = self.tree.item(item, "values")[0]

                # Validar que la cédula y el celular sean numéricos enteros positivos
                if columna_texto in ["Cédula", "Celular"]:
                    if not (nuevo_valor_texto.isdigit() and int(nuevo_valor_texto) > 0):
                        messagebox.showerror(
                            "Error",
                            f"{columna_texto} debe ser un número entero positivo",
                            parent=popup,
                        )
                        return

                # Validar que Nombres y Apellidos sean solo letras y espacios
                if columna_texto in ["Nombres", "Apellidos"]:
                    if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ ]+", nuevo_valor_texto):
                        messagebox.showerror(
                            "Error",
                            f"{columna_texto} solo debe contener letras y espacios",
                            parent=popup,
                        )
                        return

                # Validar que Zona sea solo letras, números y espacios
                if columna_texto == "Zona":
                    if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9 ]+", nuevo_valor_texto):
                        messagebox.showerror(
                            "Error",
                            f"{columna_texto} solo debe contener letras, números y espacios",
                            parent=popup,
                        )
                        return

                # Actualizar el cliente en la base de datos
                database.actualizar_cliente(
                    id_cliente, columna_db, nuevo_valor_texto
                )  # <-- SQLite

                # Actualizar en la tabla
                valores = list(self.tree.item(item, "values"))
                valores[int(columna[1:]) - 1] = nuevo_valor_texto
                self.tree.item(item, values=valores)

                popup.destroy()
                messagebox.showinfo(
                    "Éxito",
                    f"El valor de {columna_texto} se actualizó correctamente",
                    parent=self,
                )
            except Exception as e:
                messagebox.showerror(
                    "Error", f"No se pudo actualizar el valor: {e}", parent=popup
                )

        # Asociar Enter a guardar_cambios solo en la ventana popup
        popup.bind("<Return>", guardar_cambios)

        tk.Button(
            frame_botones,
            text="Guardar",
            command=guardar_cambios,
            font=("Helvetica", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            width=12,
        ).pack(side="left", padx=10)

        tk.Button(
            frame_botones,
            text="Cancelar",
            command=popup.destroy,
            font=("Helvetica", 12, "bold"),
            bg="#F44336",
            fg="white",
            width=12,
        ).pack(side="left", padx=10)

    def limpiar_campos(self):
        for entry in self.entries.values():
            entry.delete(0, END)
        # Limpiar también el combobox de búsqueda y mostrar todos los clientes
        self.combo_clientes.set("")
        self.cargar_datos()

    def cargar_formulario(self, event):
        """
        Llena los campos de entrada con los datos del registro seleccionado en la tabla.
        """
        seleccionado = self.tree.selection()
        if not seleccionado:
            return

        valores = self.tree.item(seleccionado[0], "values")
        for entry, valor in zip(self.entries.values(), valores[1:]):  # Excluir el ID
            entry.delete(0, tk.END)
            entry.insert(0, valor)
