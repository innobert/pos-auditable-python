import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import webbrowser
from datetime import datetime
from PIL import Image, ImageTk
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm

from retail.core.config import rutas, obtener_ruta_logo
from retail.core.database import (
    get_connection,
    obtener_productos,
    registrar_historial_venta,
    registrar_historial_deuda,
)

from retail.utils.logo import cambiar_logo
from retail.deudas.historial_deudas import abrir_historial_deudas
from retail.utils.fileops import open_file_silently


class Deudas(tk.Frame):
    def __init__(self, padre, controlador):
        super().__init__(padre, bg="#E6D9E3")
        self.controlador = controlador
        self.ultimo_directorio = os.path.expanduser("~")
        self.widgets()

    def widgets(self):
        # Título Principal
        self.label_titulo = tk.Label(
            self,
            text="Deudas",
            font=("Helvetica", 15, "bold"),
            bg="#F44336",
            fg="#0A0A0A",
        )
        self.label_titulo.place(x=0, y=0, width=1100, height=30)

        # Frame principal para la tabla
        self.frame_tabla = tk.Frame(self, bg="#F5F5F5", padx=10, pady=10)
        self.frame_tabla.place(x=10, y=40, width=870, height=570)

        columnas = (
            "ID", "N°", "Cliente", "Productos", "Hora", "Fecha", "Total", "Zona", "¿Pagó?",
        )
        self.tree = ttk.Treeview(
            self.frame_tabla,
            columns=columnas,
            show="headings",
            selectmode="browse",
        )
        config_columnas = [
            ("ID", 0), ("N°", 50), ("Cliente", 130), ("Productos", 250), ("Hora", 90),
            ("Fecha", 110), ("Total", 100), ("Zona", 120), ("¿Pagó?", 80),
        ]
        for col, width in config_columnas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="center")
        self.tree.column("ID", width=0, stretch=tk.NO)

        self.scroll_y = ttk.Scrollbar(self.frame_tabla, orient="vertical")
        self.scroll_x = ttk.Scrollbar(self.frame_tabla, orient="horizontal")
        self.tree.configure(
            yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set
        )
        self.scroll_y.config(command=self.tree.yview)
        self.scroll_x.config(command=self.tree.xview)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scroll_y.grid(row=0, column=1, sticky="ns")
        self.scroll_x.grid(row=1, column=0, sticky="ew")
        self.frame_tabla.grid_rowconfigure(0, weight=1)
        self.frame_tabla.grid_columnconfigure(0, weight=1)

        # Label Frame Buscar (ajustado para no interferir con el título)
        frame_buscar = tk.LabelFrame(
            self,
            text="Búsqueda de Deudas",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
        )
        frame_buscar.place(x=900, y=40, width=190, height=70)  # y=30 igual que en Facturas

        self.combo_buscar = ttk.Combobox(
            frame_buscar,
            font=("Calibri", 12),
            state="normal",
        )
        self.combo_buscar.pack(pady=5, padx=10, fill="x")
        self.combo_buscar.bind("<KeyRelease>", self.filtrar_deudas)
        self.combo_buscar.bind("<<ComboboxSelected>>", self.filtrar_deudas)

        # Label Frame Opciones (ajustado igual que en Facturas)
        self.lf_opciones = tk.LabelFrame(
            self,
            text="Opciones",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
        )
        self.lf_opciones.place(x=900, y=110, width=190, height=270)  # y=90, height=270 igual que Facturas

        # Cargar imágenes
        ruta_img = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "img"))
        def cargar_img(nombre):
            try:
                return ImageTk.PhotoImage(Image.open(os.path.join(ruta_img, nombre)).resize((28, 28)))
            except Exception:
                return None
        img_pdf = cargar_img("imprimir.png")
        img_eliminar = cargar_img("eliminar.png")
        img_pagada = cargar_img("pagada.png")
        img_historial = cargar_img("historial.png")
        img_cambiar = cargar_img("cambiar.png")

        # Botón Generar PDF
        btn_generar_pdf = tk.Button(
            self.lf_opciones,
            text="  Deuda PDF",
            image=img_pdf,
            compound="left",
            font=("Helvetica", 13, "bold"),
            bg="#1976D2",
            fg="white",
            activebackground="#115293",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.generar_pdf_deuda,
            padx=10,
            anchor="w",
        )
        btn_generar_pdf.image = img_pdf
        btn_generar_pdf.pack(pady=7, padx=10, fill="x")

        # Botón Anular Deuda
        btn_eliminar = tk.Button(
            self.lf_opciones,
            text="  Anular",
            image=img_eliminar,
            compound="left",
            font=("Helvetica", 13, "bold"),
            bg="#F44336",
            fg="white",
            activebackground="#B71C1C",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.anular_deuda,
            padx=10,
            anchor="w",
        )
        btn_eliminar.image = img_eliminar
        btn_eliminar.pack(pady=7, padx=10, fill="x")

        # Botón Pagada
        btn_pagada = tk.Button(
            self.lf_opciones,
            text="  Pagada",
            image=img_pagada,
            compound="left",
            font=("Helvetica", 13, "bold"),
            bg="#008B8B",
            fg="white",
            activebackground="#006666",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.marcar_pagada,
            padx=10,
            anchor="w",
        )
        btn_pagada.image = img_pagada
        btn_pagada.pack(pady=7, padx=10, fill="x")

        # Botón Historial (ahora funcional)
        btn_historial = tk.Button(
            self.lf_opciones,
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
            command=self.abrir_historial_cliente_seleccionado,  # <--- Cambia aquí
            padx=10,
            anchor="w",
        )
        btn_historial.image = img_historial
        btn_historial.pack(pady=7, padx=10, fill="x")

        # Botón Cambiar Logo
        btn_logo = tk.Button(
            self.lf_opciones,
            text="  Cambiar logo",
            image=img_cambiar,
            compound="left",
            font=("Helvetica", 13, "bold"),
            bg="#1976D2",
            fg="white",
            activebackground="#115293",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=lambda: cambiar_logo(self),
            padx=10,
            anchor="w",
        )
        btn_logo.image = img_cambiar
        btn_logo.pack(pady=7, padx=10, fill="x")

        # Label Frame Total Deudas
        self.lf_total_deudas = tk.LabelFrame(
            self,
            text="Total Deudas",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
        )
        self.lf_total_deudas.place(x=900, y=400, width=190, height=70)

        self.var_total_deudas = tk.StringVar(value="$0")
        lbl_total_deudas = tk.Label(
            self.lf_total_deudas,
            textvariable=self.var_total_deudas,
            font=("Helvetica", 16, "bold"),
            bg="#E6D9E3",
            fg="#008B8B",
        )
        lbl_total_deudas.pack(expand=True, fill="both", pady=10)

        self.cargar_deudas()
        self.tree.bind("<Double-1>", self.abrir_agregar_productos_deuda)

    def cargar_deudas(self):
        self.tree.delete(*self.tree.get_children())
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    d.id_deuda,
                    c.nombres || ' ' || c.apellidos AS cliente,
                    GROUP_CONCAT(i.producto || ' x' || hd.cantidad, ', ') AS productos,
                    v.hora,
                    v.fecha,
                    COALESCE(SUM(CASE WHEN hd.accion = 'Abono' THEN -hd.subtotal ELSE hd.subtotal END), d.total) AS total_deuda,
                    COALESCE(c.zona, 'Negocio') AS zona
                FROM deudas d
                LEFT JOIN ventas v ON d.id_ventas = v.id_ventas
                LEFT JOIN clientes c ON d.cliente_id = c.id_cliente
                LEFT JOIN historial_deudas hd ON d.id_deuda = hd.id_deuda
                LEFT JOIN inventario i ON hd.id_producto = i.id_producto
                GROUP BY d.id_deuda
                ORDER BY d.id_deuda ASC;
                """
            )
            deudas = cursor.fetchall()
        clientes_unicos = list({deuda[1] for deuda in deudas})
        self.combo_buscar["values"] = clientes_unicos
        self.combo_buscar.set("")
        total_deudas = 0
        for idx, (
            id_deuda,
            cliente,
            productos,
            hora,
            fecha,
            total_deuda,
            zona,
        ) in enumerate(deudas, 1):
            self.tree.insert(
                "",
                "end",
                values=(
                    id_deuda,
                    idx,
                    cliente,
                    productos,
                    hora,
                    fecha,
                    f"${total_deuda:,.0f}".replace(",", "."),
                    zona,
                    "No",
                ),
            )
            try:
                total_deudas += float(total_deuda)
            except (ValueError, TypeError):
                pass
        self.var_total_deudas.set(f"${total_deudas:,.0f}".replace(",", "."))

    def filtrar_deudas(self, event=None):
        texto = self.combo_buscar.get().strip().lower()
        self.tree.delete(*self.tree.get_children())
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    d.id_deuda,
                    c.nombres || ' ' || c.apellidos AS cliente,
                    GROUP_CONCAT(i.producto || ' x' || hd.cantidad, ', ') AS productos,
                    v.hora,
                    v.fecha,
                    COALESCE(SUM(CASE WHEN hd.accion = 'Abono' THEN -hd.subtotal ELSE hd.subtotal END), d.total) AS total_deuda,
                    COALESCE(c.zona, 'Negocio') AS zona
                FROM deudas d
                LEFT JOIN ventas v ON d.id_ventas = v.id_ventas
                LEFT JOIN clientes c ON d.cliente_id = c.id_cliente
                LEFT JOIN historial_deudas hd ON d.id_deuda = hd.id_deuda
                LEFT JOIN inventario i ON hd.id_producto = i.id_producto
                GROUP BY d.id_deuda
                ORDER BY d.id_deuda ASC;
                """
            )
            deudas = cursor.fetchall()
        total_deudas = 0
        for idx, (
            id_deuda,
            cliente,
            productos,
            hora,
            fecha,
            total_deuda,
            zona,
        ) in enumerate(deudas, 1):
            if texto in cliente.lower() or texto == "":
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        id_deuda,
                        idx,
                        cliente,
                        productos,
                        hora,
                        fecha,
                        f"${total_deuda:,.0f}".replace(",", "."),
                        zona,
                        "No",
                    ),
                )
                try:
                    total_deudas += float(total_deuda)
                except (ValueError, TypeError):
                    pass
        self.var_total_deudas.set(f"${total_deudas:,.0f}".replace(",", "."))

    def format_currency(self, value):
        try:
            return "${:,.0f}".format(float(value)).replace(",", ".")
        except Exception:
            return str(value)

    def anular_deuda(self):
        seleccionado = self.tree.selection()
        if not seleccionado:
            messagebox.showwarning(
                "Advertencia",
                "Seleccione una deuda para anular.",
                parent=self,
            )
            return
        item = seleccionado[0]
        valores = self.tree.item(item, "values")
        id_deuda = int(valores[0])
        if messagebox.askyesno(
            "Confirmar",
            "¿Está seguro de anular esta deuda?",
            parent=self,
        ):
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE deudas SET estado = 'ANULADA' WHERE id_deuda = ?", (id_deuda,))
                # Registrar en historial_deudas
                registrar_historial_deuda(
                    id_deuda=id_deuda,
                    id_producto=None,
                    cantidad=0,
                    subtotal=0,
                    accion="ANULACIÓN",
                    usuario=os.getlogin() if hasattr(os, "getlogin") else "sistema",
                    detalle=f"Anulación de deuda ID {id_deuda}",
                    cursor=cursor,
                )
                conn.commit()
            self.cargar_deudas()
            messagebox.showinfo("Éxito", "Deuda anulada correctamente.", parent=self)

    def generar_deuda(self):
        seleccionado = self.tree.selection()
        if not seleccionado:
            messagebox.showwarning(
                "Advertencia",
                "Seleccione una deuda para generar.",
                parent=self,
            )
            return

        item = seleccionado[0]
        valores = self.tree.item(item, "values")
        id_deuda = int(valores[0])  # Usa el ID real directamente

        with get_connection() as conn:
            cursor = conn.cursor()
            # Obtener cliente, fecha, hora
            cursor.execute(
                "SELECT c.nombres || ' ' || c.apellidos, v.fecha, v.hora FROM deudas d JOIN ventas v ON d.id_ventas = v.id_ventas LEFT JOIN clientes c ON d.cliente_id = c.id_cliente WHERE d.id_deuda = ?",
                (id_deuda,),
            )
            res = cursor.fetchone()
            cliente = res[0] if res else "Cliente desconocido"
            fecha = res[1] if res else ""
            hora = res[2] if res else ""

            cursor.execute(
                """
                SELECT i.producto, hd.cantidad, hd.subtotal
                FROM historial_deudas hd
                JOIN inventario i ON hd.id_producto = i.id_producto
                WHERE hd.id_deuda = ? AND hd.accion != 'Abono'
                """,
                (id_deuda,),
            )
            productos_detalle = cursor.fetchall()

            # Obtener el total calculado desde historial
            cursor.execute(
                "SELECT COALESCE(SUM(subtotal), 0) FROM historial_deudas WHERE id_deuda = ? AND accion != 'Abono'",
                (id_deuda,),
            )
            total_calculado = cursor.fetchone()[0]

        # Usar el N° mostrado en la tabla (valores[1]) para el nombre del PDF
        deuda_idx = valores[1]
        archivo_pdf = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"Deuda_{deuda_idx}.pdf",
            title="Guardar deuda como",
            filetypes=[("Archivos PDF", "*.pdf")],
            initialdir=getattr(self, "ultimo_directorio", os.path.expanduser("~")),
            parent=self,
        )

        if archivo_pdf:
            self.ultimo_directorio = os.path.dirname(archivo_pdf)
            c = canvas.Canvas(archivo_pdf, pagesize=letter)
            c.setFont("Helvetica-Bold", 24)
            c.drawString(50, 750, "Detalles de Factura")

            # Usar rutas absolutas para el logo
            ruta_logo = rutas(os.path.join("img", "logo.png"))
            try:
                c.drawImage(ruta_logo, 250, 600, width=120, height=120)
            except Exception:
                pass

            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, 700, f"N° Factura: {deuda_idx}")
            c.drawString(50, 680, f"Cliente: {cliente}")
            c.drawString(50, 660, f"Fecha: {fecha}")
            c.drawString(50, 640, f"Hora: {hora}")

            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, 600, "Productos:")

            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, 580, "Producto")
            c.drawString(250, 580, "Cantidad")
            c.drawString(350, 580, "Subtotal")

            c.setFont("Helvetica", 10)
            y = 560
            for prod, cant, sub in productos_detalle:
                c.drawString(50, y, str(prod))
                c.drawString(250, y, str(cant))
                c.drawString(350, y, self.format_currency(sub))
                y -= 20

            c.setFont("Helvetica-Bold", 12)
            total_formateado = self.format_currency(total_calculado)
            c.drawString(50, y - 20, f"Total: {total_formateado}")

            c.save()
            messagebox.showinfo(
                "Éxito",
                f"Deuda generada correctamente en:\n{archivo_pdf}",
                parent=self,
            )
            try:
                open_file_silently(archivo_pdf)
                temp = tk.Toplevel(self)
                temp.withdraw()
                temp.attributes("-topmost", True)
                temp.after(1000, temp.destroy)
            except Exception:
                pass

    def generar_pdf_deuda(self):
        """
        Genera un PDF de la deuda seleccionada, con el mismo estilo que facturas.py.
        """
        seleccionado = self.tree.selection()
        if not seleccionado:
            messagebox.showwarning(
                "Advertencia",
                "Seleccione una deuda para imprimir.",
                parent=self,
            )
            return

        item = seleccionado[0]
        valores = self.tree.item(item, "values")
        # columnas = ("ID", "N°", "Cliente", "Productos", "Hora", "Fecha", "Total", "Zona", "¿Pagó?")
        id_deuda = int(valores[0])
        deuda_idx = valores[1]
        cliente = valores[2]
        hora = valores[4]
        fecha = valores[5]
        total = valores[6]
        zona = valores[7]

        with get_connection() as conn:
            cursor = conn.cursor()
            # Obtener datos adicionales: numero_factura, estado, usuario
            cursor.execute(
                """
                SELECT v.numero_factura, d.estado
                FROM deudas d
                JOIN ventas v ON d.id_ventas = v.id_ventas
                WHERE d.id_deuda = ?
                """,
                (id_deuda,),
            )
            res = cursor.fetchone()
            numero_factura = res[0] if res else f"DEUDA-{id_deuda}"
            estado_deuda = res[1] if res else "DESCONOCIDO"

            # Obtener los productos de la deuda desde historial_deudas (excluyendo abonos)
            cursor.execute(
                """
                SELECT i.producto, hd.cantidad, hd.subtotal, hd.hora, hd.fecha
                FROM historial_deudas hd
                JOIN inventario i ON hd.id_producto = i.id_producto
                WHERE hd.id_deuda = ? AND hd.accion != 'Abono'
                """,
                (id_deuda,),
            )
            productos_detalle = cursor.fetchall()

            # Calcular total desde historial (excluyendo abonos)
            cursor.execute(
                "SELECT COALESCE(SUM(subtotal), 0) FROM historial_deudas WHERE id_deuda = ? AND accion != 'Abono'",
                (id_deuda,),
            )
            total_calculado = cursor.fetchone()[0]

        if not productos_detalle:
            messagebox.showerror(
                "Error",
                f"No se encontraron productos para la deuda {id_deuda}",
                parent=self,
            )
            return

        archivo_pdf = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"Factura_{numero_factura}.pdf",
            title="Guardar factura de venta a crédito como PDF",
            filetypes=[("Archivos PDF", "*.pdf")],
            initialdir=getattr(self, "ultimo_directorio", os.path.expanduser("~")),
            parent=self,
        )

        if archivo_pdf:
            self.ultimo_directorio = os.path.dirname(archivo_pdf)
            c = canvas.Canvas(archivo_pdf, pagesize=letter)
            width, height = letter

            # Logo arriba derecha
            ruta_logo = obtener_ruta_logo("logo.png")
            try:
                c.drawImage(ruta_logo, width - 180, height - 150, width=140, height=140, mask='auto')
            except Exception as e:
                print(f"Error al cargar el logo: {e}")

            # Información del negocio
            c.setFont("Helvetica-Bold", 18)
            c.drawString(40, height - 80, "INNOBERT RETAIL")
            c.setFont("Helvetica", 12)
            c.drawString(40, height - 95, "NIT: 900123456-7")
            c.drawString(40, height - 110, f"Zona: {zona}")

            # Título grande
            c.setFont("Helvetica-Bold", 28)
            titulo = "Factura de Venta a Crédito"
            x_titulo = 40
            y_titulo = height - 140
            c.drawString(x_titulo, y_titulo, titulo)

            # Línea subrayando solo el título
            ancho_titulo = c.stringWidth(titulo, "Helvetica-Bold", 28)
            c.setStrokeColor(colors.black)
            c.setLineWidth(2)
            c.line(x_titulo, y_titulo - 6, x_titulo + ancho_titulo, y_titulo - 6)

            # Datos de la factura
            c.setFont("Helvetica-Bold", 13)
            y = height - 180
            c.drawString(40, y, f"Factura N°: {numero_factura}")
            c.drawString(40, y - 25, f"Referencia Deuda: {id_deuda}")
            c.drawString(40, y - 50, f"Cliente: {cliente}")
            c.drawString(40, y - 75, f"Fecha Venta: {fecha} {hora}")
            fecha_emision = datetime.now().strftime("%Y-%m-%d %H:%M")
            usuario = os.getlogin() if hasattr(os, "getlogin") else "sistema"
            c.drawString(40, y - 100, f"Fecha Emisión: {fecha_emision}")
            c.drawString(40, y - 125, f"Generado por: {usuario}")
            c.drawString(40, y - 150, f"Estado: {estado_deuda}")

            # Tabla de productos
            y_tabla = y - 170
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y_tabla, "Producto")
            c.drawString(200, y_tabla, "Hora")
            c.drawString(270, y_tabla, "Fecha")
            c.drawString(360, y_tabla, "Cantidad")
            c.drawString(440, y_tabla, "Subtotal")
            c.line(30, y_tabla - 5, width - 30, y_tabla - 5)

            # Mostrar hora y fecha para cada producto
            c.setFont("Helvetica", 11)
            y_fila = y_tabla - 25
            for prod, cant, sub, hora_prod, fecha_prod in productos_detalle:
                c.drawString(40, y_fila, str(prod))
                c.drawString(200, y_fila, str(hora_prod) if hora_prod else "")
                c.drawString(270, y_fila, str(fecha_prod) if fecha_prod else "")
                c.drawString(360, y_fila, str(cant))
                c.drawString(440, y_fila, self.format_currency(sub))
                y_fila -= 20

            # Línea antes del total
            c.line(30, y_fila + 10, width - 30, y_fila + 10)

            # Total destacado
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y_fila - 20, f"Total: {self.format_currency(total_calculado)}")

            # Footer profesional
            c.setFont("Helvetica-Oblique", 13)
            c.drawString(50, 60, "Gracias por su preferencia. ®INNOBERTDEV")
            c.setFont("Helvetica-Oblique", 12)
            c.drawString(50, 40, "Factura generada automáticamente por Innobert Retail")

            # Marca de agua
            c.saveState()
            c.setFont("Helvetica-Bold", 60)
            c.setFillColorRGB(0.93, 0.93, 0.93)
            c.translate(width/2, 200)
            c.rotate(30)
            c.drawCentredString(0, 0, "Innobert")
            c.restoreState()

            c.save()
            messagebox.showinfo(
                "Éxito",
                f"Factura PDF generada correctamente en:\n{archivo_pdf}",
                parent=self,
            )
            try:
                open_file_silently(archivo_pdf)
                temp = tk.Toplevel(self)
                temp.withdraw()
                temp.attributes("-topmost", True)
                temp.after(1000, temp.destroy)
            except Exception:
                pass

    def marcar_pagada(self):
        seleccionado = self.tree.selection()
        if not seleccionado:
            messagebox.showwarning(
                "Advertencia",
                "Seleccione una deuda para marcar como pagada.",
                parent=self,
            )
            return

        item = seleccionado[0]
        valores = self.tree.item(item, "values")
        id_deuda = int(valores[0])  # Usa el ID real
        cliente = valores[2]
        fecha = valores[5]
        hora = valores[4]
        total = float(str(valores[6]).replace("$", "").replace(".", "").replace(",", ""))
        zona = valores[7]

        if not messagebox.askyesno(
            "Confirmar",
            "¿Está seguro que desea marcar esta deuda como pagada?",
            parent=self,
        ):
            return

        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                # Insertar pago en pagos_deuda
                cursor.execute(
                    "INSERT INTO pagos_deuda (id_deuda, monto, fecha, hora, usuario) VALUES (?, ?, ?, ?, ?)",
                    (id_deuda, total, fecha, hora, os.getlogin() if hasattr(os, "getlogin") else "sistema"),
                )
                # Actualizar deuda a pagada
                cursor.execute(
                    "UPDATE deudas SET estado = 'PAGADA', saldo = 0 WHERE id_deuda = ?",
                    (id_deuda,),
                )
                conn.commit()
            messagebox.showinfo(
                "Éxito",
                "La deuda ha sido marcada como pagada.",
                parent=self,
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo marcar la deuda como pagada: {e}", parent=self)
        self.cargar_deudas()

    def abrir_agregar_productos_deuda(self, event=None):
        seleccionado = self.tree.selection()
        if not seleccionado:
            messagebox.showwarning(
                "Advertencia",
                "Seleccione una deuda para añadir productos.",
                parent=self,
            )
            return
        item = seleccionado[0]
        valores = self.tree.item(item, "values")
        id_deuda = int(valores[0])  # Usa el ID real, no el N°
        cliente = valores[2]

        # --- Ventana tipo inventario, organizado ---
        top = tk.Toplevel(self)
        top.title(f"Añadir productos a: {cliente}")
        top.geometry("1100x650+120+40")
        top.configure(bg="#E6D9E3")
        top.resizable(False, False)
        top.grab_set()

        label_titulo = tk.Label(
            top,
            text=f"Añadir productos a: {cliente}",
            font=("Helvetica", 15, "bold"),
            bg="#F44336",
            fg="#0A0A0A",
        )
        label_titulo.pack(fill="x", ipady=4)

        frame_main = tk.Frame(top, bg="#E6D9E3")
        frame_main.pack(fill="both", expand=True, padx=0, pady=(0, 0))

        lf_buscar = tk.LabelFrame(
            frame_main,
            text="Buscar producto",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
        )
        lf_buscar.pack(anchor="w", padx=20, pady=(10, 0))
        lf_buscar.configure(width=400, height=60)

        entry_buscar = ttk.Combobox(
            lf_buscar,
            font=("Helvetica", 11),
            width=25,
        )
        entry_buscar.pack(side="left", padx=10, pady=10, fill="x", expand=False)

        productos = obtener_productos()
        entry_buscar["values"] = [p[1] for p in productos]

        lf_productos = tk.LabelFrame(
            frame_main,
            text="Productos",
            font=("Helvetica", 12, "bold"),
            bg="#E6D9E3",
        )
        lf_productos.pack(fill="both", expand=True, padx=20, pady=15)

        canvas = tk.Canvas(
            lf_productos,
            bg="#E6D9E3",
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(lf_productos, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        frame_contenedor = tk.Frame(canvas, bg="#E6D9E3")
        canvas.create_window((0, 0), window=frame_contenedor, anchor="nw")
        frame_contenedor.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        def seleccionar_cantidad(producto):
            top_cant = tk.Toplevel(top)
            top_cant.title(f"Cantidad para {producto[1]}")
            top_cant.geometry("350x200+400+200")
            top_cant.configure(bg="#E6D9E3")
            top_cant.resizable(False, False)
            tk.Label(
                top_cant,
                text=f"Cliente: {cliente}",
                font=("Helvetica", 12, "bold"),
                bg="#E6D9E3",
                fg="#333333",
            ).pack(pady=(10, 2))
            tk.Label(
                top_cant,
                text=f"Producto: {producto[1]}",
                font=("Helvetica", 13, "bold"),
                bg="#E6D9E3",
            ).pack(pady=(5, 5))
            tk.Label(
                top_cant,
                text=f"Stock disponible: {producto[4]}",
                font=("Helvetica", 12),
                bg="#E6D9E3",
                fg="green" if producto[4] > 0 else "red",
            ).pack(pady=(0, 10))
            frame_cantidad = tk.Frame(top_cant, bg="#E6D9E3")
            frame_cantidad.pack(pady=(0, 10))
            tk.Label(
                frame_cantidad,
                text="Cantidad:",
                font=("Helvetica", 12),
                bg="#E6D9E3",
            ).pack(side="left")
            def validar_entero(valor):
                return valor == "" or (valor.isdigit() and int(valor) > 0)
            vcmd_entero = (top_cant.register(validar_entero), "%P")
            entry_cantidad = tk.Entry(frame_cantidad, font=("Helvetica", 12), width=8, validate="key", validatecommand=vcmd_entero)
            entry_cantidad.pack(side="left", padx=(10, 0))
            frame_botones = tk.Frame(top_cant, bg="#E6D9E3")
            frame_botones.pack(pady=(5, 0))

            def agregar():
                try:
                    cantidad = int(entry_cantidad.get())
                    if cantidad <= 0 or cantidad > producto[4]:
                        messagebox.showwarning(
                            "Cantidad inválida",
                            f"Ingrese una cantidad válida (1 a {producto[4]}).",
                            parent=top_cant,
                        )
                        return
                    subtotal = cantidad * producto[2]
                    hora_actual = datetime.now().strftime("%H:%M:%S")
                    fecha_actual = datetime.now().strftime("%Y-%m-%d")
                    conn = get_connection()
                    cursor = conn.cursor()
                    # Actualizar inventario
                    cursor.execute(
                        "UPDATE inventario SET stock = stock - ? WHERE id_producto = ?",
                        (cantidad, producto[0]),
                    )
                    # SIEMPRE crear un nuevo registro en historial_deudas
                    registrar_historial_deuda(
                        id_deuda=id_deuda,
                        id_producto=producto[0],
                        cantidad=cantidad,
                        subtotal=subtotal,
                        accion="Editado",
                        usuario=os.getlogin() if hasattr(os, "getlogin") else "sistema",
                        detalle=f"Editado producto '{producto[1]}' (ID:{producto[0]}) x{cantidad} a la deuda {id_deuda} para el cliente '{cliente}' desde el frame de añadir productos. Subtotal: {subtotal}, Fecha: {fecha_actual}, Hora: {hora_actual}",
                        cursor=cursor,
                    )
                    conn.commit()
                    conn.close()

                    messagebox.showinfo(
                        "Producto añadido",
                        f"Se añadieron {cantidad} unidades de '{producto[1]}' a la deuda.",
                        parent=top_cant,
                    )
                    self.cargar_deudas()
                    top_cant.destroy()
                except ValueError:
                    messagebox.showwarning(
                        "Cantidad inválida", "Ingrese un número válido.", parent=top_cant
                    )
                except Exception as e:
                    messagebox.showerror(
                        "Error", f"No se pudo agregar el producto: {e}", parent=top_cant
                    )
                    top_cant.destroy()

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
                command=top_cant.destroy,
                width=10,
            )
            btn_cancelar.pack(side="left", padx=10)

        def mostrar_productos_en_canvas(productos):
            for widget in frame_contenedor.winfo_children():
                widget.destroy()
            columnas = 0
            row = 0
            ancho_producto = 450
            alto_producto = 420
            separacion_x = 70
            separacion_y = 36
            for producto in productos:
                frame_producto = tk.Frame(
                    frame_contenedor,
                    bg="white",
                    width=ancho_producto,
                    height=alto_producto,
                    bd=1,
                    relief="solid",
                    highlightthickness=0
                )
                frame_producto.grid(row=row, column=columnas, padx=separacion_x//2, pady=separacion_y//2, sticky="nsew")
                frame_producto.grid_propagate(False)
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
                # Doble click en imagen o frame para agregar cantidad
                img_label.bind(
                    "<Double-Button-1>",
                    lambda e, p=producto: seleccionar_cantidad(p)
                )
                frame_producto.bind(
                    "<Double-Button-1>",
                    lambda e, p=producto: seleccionar_cantidad(p)
                )
                # Nombre y precio
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

        def filtrar_productos(event=None):
            texto = entry_buscar.get().strip().lower()
            if not texto:
                filtrados = productos
            else:
                filtrados = [p for p in productos if texto in p[1].lower()]
            entry_buscar["values"] = [p[1] for p in filtrados]
            mostrar_productos_en_canvas(filtrados)

        def seleccionar_producto_entry(event=None):
            nombre = entry_buscar.get().strip()
            if not nombre:
                mostrar_productos_en_canvas(productos)
                return
            seleccionados = [p for p in productos if p[1].lower() == nombre.lower()]
            if seleccionados:
                mostrar_productos_en_canvas(seleccionados)
            else:
                filtrados = [p for p in productos if nombre.lower() in p[1].lower()]
                mostrar_productos_en_canvas(filtrados)

        entry_buscar.bind("<KeyRelease>", filtrar_productos)
        entry_buscar.bind("<Return>", seleccionar_producto_entry)
        mostrar_productos_en_canvas(productos)

    def abrir_historial_cliente_seleccionado(self):
        seleccionado = self.tree.selection()
        if not seleccionado:
            messagebox.showwarning("Advertencia", "Seleccione una deuda para ver el historial.", parent=self)
            return
        item = seleccionado[0]
        valores = self.tree.item(item, "values")
        # columnas = (ID, N°, Cliente, Productos, Hora, Fecha, Total, Zona, ¿Pagó?)
        id_deuda = valores[0]  # ID de la deuda seleccionada
        cliente = valores[2]  # Cliente (nombre completo)
        # Obtener id_cliente para trazabilidad
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT cliente_id FROM deudas WHERE id_deuda = ?", (id_deuda,))
            res = cursor.fetchone()
            id_cliente = res[0] if res else None
        # Abrir historial solo para la deuda seleccionada
        from retail.deudas.historial_deudas import abrir_historial_deudas
        abrir_historial_deudas(self, nombre_cliente=str(id_cliente) if id_cliente else cliente, cliente_rapido=cliente, id_deuda=id_deuda)
