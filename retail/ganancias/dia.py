import tkinter as tk
from tkinter import ttk
from retail.core.database import get_connection
import datetime
from tkinter import filedialog, messagebox
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from retail.core.config import rutas, obtener_ruta_logo
from retail.utils.fileops import open_file_silently
import os
import webbrowser
from PIL import Image, ImageTk
import threading


class Dia(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#F5F5F5")

        # Frame principal para la tabla y totales
        frame_main = tk.Frame(self, bg="#F5F5F5")
        frame_main.pack(fill="both", expand=True, padx=18, pady=12)

        # Frame para la tabla de ventas
        frame_tabla = tk.Frame(frame_main, bg="#FFFFFF", bd=2, relief="groove")
        frame_tabla.pack(fill="both", expand=False, padx=0, pady=(0, 10))

        columns = (
            "#",
            "dia_semana",
            "cliente",
            "fecha",
            "hora",
            "producto",
            "cantidad",
            "costo",
            "precio",
            "ganancia",
        )
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Treeview.Heading",
            font=("Helvetica", 13, "bold"),
            background="#F5F5F5",
            foreground="#222",
        )
        style.configure(
            "Treeview",
            font=("Helvetica", 12),
            rowheight=28,
            background="#fff",
            fieldbackground="#fff",
        )
        style.map("Treeview", background=[("selected", "#e0e0e0")], foreground=[("selected", "#222")])

        self.tree = ttk.Treeview(
            frame_tabla,
            columns=columns,
            show="headings",
            height=9,
            style="Treeview",
        )
        for col, ancho in zip(
            columns,
            [50, 90, 140, 90, 70, 140, 90, 90, 90, 110]
        ):
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=ancho, anchor="center")

        # Scrollbars vertical y horizontal
        scrollbar_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(frame_tabla, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        frame_tabla.grid_rowconfigure(0, weight=1)
        frame_tabla.grid_columnconfigure(0, weight=1)

        # Frame para los totales debajo de la tabla
        lf_totales = tk.LabelFrame(
            frame_main,
            text="Totales del Día",
            font=("Helvetica", 13, "bold"),
            bg="#FFFFFF",
            fg="#222",
            padx=18,
            pady=12,
            bd=2,
            relief="groove"
        )
        lf_totales.pack(fill="x", padx=0, pady=(0, 5))

        self.var_total_ganancia = tk.StringVar(value="$0")
        self.var_total_ventas = tk.StringVar(value="$0")

        totales_frame = tk.Frame(lf_totales, bg="#FFFFFF")
        totales_frame.pack(fill="x")

        # Solo mostrar Ganancia y Ventas
        for text, var in [
            ("Total Ganancia:", self.var_total_ganancia),
            ("Total Ventas:", self.var_total_ventas),
        ]:
            tk.Label(
                totales_frame,
                text=text,
                font=("Helvetica", 13, "bold"),
                bg="#FFFFFF",
                fg="#222",
            ).pack(side="left", padx=(0, 10))
            tk.Label(
                totales_frame,
                textvariable=var,
                font=("Helvetica", 13, "bold"),
                bg="#FFFFFF",
                fg="#222",
            ).pack(side="left", padx=(0, 30))

        # Botón profesional igual al de Factura PDF with imagen
        ruta_img = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "img"))
        try:
            img_pdf = ImageTk.PhotoImage(Image.open(os.path.join(ruta_img, "imprimir.png")).resize((28, 28)))
        except Exception:
            img_pdf = None

        self.btn_pdf = tk.Button(
            lf_totales,
            text="  Imprimir PDF",
            image=img_pdf,
            compound="left",
            font=("Helvetica", 13, "bold"),
            bg="#1976D2",
            fg="white",
            activebackground="#388E3C",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.generar_pdf_registro,
            padx=10,
            anchor="w"
        )
        self.btn_pdf.image = img_pdf
        self.btn_pdf.pack(side="right", padx=(0, 10), pady=(0, 5))

        # Carga los datos en un hilo para que la interfaz sea inmediata
        threading.Thread(target=self.cargar_datos, daemon=True).start()

    def cargar_datos(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT v.fecha, v.hora,
                   COALESCE(c.nombres || ' ' || c.apellidos, v.cliente_rapido) AS cliente,
                   i.producto, dv.cantidad, i.costo, i.precio
            FROM ventas v
            JOIN detalle_venta dv ON v.id_ventas = dv.id_ventas
            JOIN inventario i ON dv.id_producto = i.id_producto
            LEFT JOIN clientes c ON v.cliente_venta = c.id_cliente
            WHERE dv.pago=1
            ORDER BY v.fecha ASC, cliente ASC, v.hora ASC
            """
        )
        rows = cursor.fetchall()
        conn.close()

        dias = [
            "Lunes",
            "Martes",
            "Miércoles",
            "Jueves",
            "Viernes",
            "Sábado",
            "Domingo",
        ]
        # Calcula totales y prepara datos para actualizar la interfaz
        total_ganancia = 0
        total_ventas = 0
        total_cantidad = 0
        tabla_data = []

        # Contador secuencial que se reinicia al cambiar el nombre del día (Lunes, Martes, ...)
        idx = 1
        last_dia_semana = None

        for row in rows:
            fecha, hora, cliente, producto, cantidad, costo, precio = row
            fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
            dia_semana = dias[fecha_dt.weekday()]

            # Si cambia el nombre del día, reiniciamos el contador
            if dia_semana != last_dia_semana:
                idx = 1
                last_dia_semana = dia_semana

            ganancia = (precio - costo) * cantidad
            total_ganancia += ganancia
            total_ventas += precio * cantidad
            total_cantidad += cantidad

            tabla_data.append((
                idx,
                dia_semana,
                cliente,
                fecha,
                hora,
                producto,
                cantidad,
                f"${costo:,.0f}".replace(",", "."),
                f"${precio:,.0f}".replace(",", "."),
                f"${ganancia:,.0f}".replace(",", "."),
            ))

            idx += 1

        # Actualiza la interfaz en el hilo principal
        self.after(0, self._actualizar_tabla, tabla_data, total_ganancia, total_ventas, total_cantidad)

    def _actualizar_tabla(self, tabla_data, total_ganancia, total_ventas, total_cantidad):
        self.tree.delete(*self.tree.get_children())
        for row in tabla_data:
            self.tree.insert("", "end", values=row)
        self.var_total_ganancia.set(f"${total_ganancia:,.0f}".replace(",", "."))
        self.var_total_ventas.set(f"${total_ventas:,.0f}".replace(",", "."))
        # Elimina la actualización de cantidad total

    def generar_pdf_registro(self):
        """
        Genera un PDF del registro seleccionado en la tabla de ventas diarias con el mismo estilo que facturas y deudas.
        """
        seleccionado = self.tree.selection()
        if not seleccionado:
            messagebox.showwarning(
                "Advertencia",
                "Seleccione un registro de venta para imprimir.",
                parent=self,
            )
            return

        item = seleccionado[0]
        (
            idx,
            dia_semana,
            cliente,
            fecha,
            hora,
            producto,
            cantidad,
            costo,
            precio,
            ganancia,
        ) = self.tree.item(item, "values")

        archivo_pdf = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"Venta_{fecha}_{hora.replace(':','-')}.pdf",
            title="Guardar venta como PDF",
            filetypes=[("Archivos PDF", "*.pdf")],
            initialdir=os.path.expanduser("~"),
            parent=self,
        )

        if archivo_pdf:
            c = canvas.Canvas(archivo_pdf, pagesize=letter)
            width, height = letter

            # Logo arriba derecha usando el logo personalizado
            ruta_logo = obtener_ruta_logo("logo.png")
            try:
                c.drawImage(ruta_logo, width - 180, height - 150, width=140, height=140, mask='auto')
            except Exception:
                pass

            # Título grande
            c.setFont("Helvetica-Bold", 28)
            titulo = "Factura de Venta"
            x_titulo = 40
            y_titulo = height - 70
            c.drawString(x_titulo, y_titulo, titulo)

            # Línea subrayando solo el título
            ancho_titulo = c.stringWidth(titulo, "Helvetica-Bold", 28)
            c.setStrokeColor(colors.black)
            c.setLineWidth(2)
            c.line(x_titulo, y_titulo - 6, x_titulo + ancho_titulo, y_titulo - 6)

            # Datos principales
            c.setFont("Helvetica-Bold", 13)
            y = height - 120
            c.drawString(40, y, f"Cliente: {cliente}")
            c.drawString(40, y - 25, f"Fecha: {fecha}")
            c.drawString(40, y - 50, f"Hora: {hora}")
            c.drawString(40, y - 75, f"Día de la semana: {dia_semana}")

            # Tabla de producto
            y_tabla = y - 110
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y_tabla, "Producto")
            c.drawString(200, y_tabla, "Cantidad")
            c.drawString(270, y_tabla, "Costo")
            c.drawString(360, y_tabla, "Precio")
            c.drawString(440, y_tabla, "Ganancia")
            c.line(30, y_tabla - 5, width - 30, y_tabla - 5)

            c.setFont("Helvetica", 11)
            y_fila = y_tabla - 25
            c.drawString(40, y_fila, str(producto))
            c.drawString(200, y_fila, str(cantidad))
            c.drawString(270, y_fila, str(costo))
            c.drawString(360, y_fila, str(precio))
            c.drawString(440, y_fila, str(ganancia))

            # Línea antes del total
            c.line(30, y_fila + 10, width - 30, y_fila + 10)

            # Totales destacados
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y_fila - 20, f"Total Venta: {precio}")
            c.drawString(240, y_fila - 20, f"Ganancia: {ganancia}")

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
                f"PDF generado correctamente en:\n{archivo_pdf}",
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
