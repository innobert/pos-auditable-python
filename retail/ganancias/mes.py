import tkinter as tk
from tkinter import ttk
from retail.core.database import get_connection
import datetime
from tkinter import filedialog, messagebox
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from retail.core.config import obtener_ruta_logo  # Asegura que rutas esté importado
import os
import webbrowser
from PIL import Image, ImageTk
import threading

# Lista de nombres de meses en español
MESES_ES = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]


class Mes(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#F5F5F5")

        # Frame principal para la tabla y totales
        frame_main = tk.Frame(self, bg="#F5F5F5")
        frame_main.pack(fill="both", expand=True, padx=18, pady=12)

        # --- Primero la tabla ---
        columns = (
            "num_mes",
            "mes",
            "desde",
            "hasta",
            "total_ventas",
            "total_ganancia",
            "productos_vendidos",
            "clientes",
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
        style.map(
            "Treeview",
            background=[("selected", "#e0e0e0")],
            foreground=[("selected", "#222")],
        )

        frame_tabla = tk.Frame(frame_main, bg="#FFFFFF", bd=2, relief="groove")
        frame_tabla.pack(fill="both", expand=False, padx=0, pady=(0, 10))

        self.tree = ttk.Treeview(
            frame_tabla,
            columns=columns,
            show="headings",
            height=9,
            style="Treeview",
        )
        self.tree.heading("num_mes", text="#")
        self.tree.heading("mes", text="Mes")
        self.tree.heading("desde", text="Desde (Fecha)")
        self.tree.heading("hasta", text="Hasta (Fecha)")
        self.tree.heading("total_ventas", text="Total Ventas")
        self.tree.heading("total_ganancia", text="Total Ganancia")
        self.tree.heading("productos_vendidos", text="P.Vendidos")
        self.tree.heading("clientes", text="Clientes")

        self.tree.column("num_mes", width=70, anchor="center")
        self.tree.column("mes", width=180, anchor="center")
        self.tree.column("desde", width=120, anchor="center")
        self.tree.column("hasta", width=120, anchor="center")
        self.tree.column("total_ventas", width=120, anchor="center")
        self.tree.column("total_ganancia", width=120, anchor="center")
        self.tree.column("productos_vendidos", width=120, anchor="center")
        self.tree.column("clientes", width=120, anchor="center")

        scrollbar_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(frame_tabla, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        frame_tabla.grid_rowconfigure(0, weight=1)
        frame_tabla.grid_columnconfigure(0, weight=1)

        # --- Luego el label frame de los totales ---
        lf_totales = tk.LabelFrame(
            frame_main,
            text="Totales del Mes",
            font=("Helvetica", 13, "bold"),
            bg="#FFFFFF",
            fg="#222",
            padx=18,
            pady=12,
            bd=2,
            relief="groove",
        )
        lf_totales.pack(fill="x", padx=0, pady=(0, 5))

        self.var_total_ganancia = tk.StringVar(value="$0")
        self.var_total_ventas = tk.StringVar(value="$0")

        totales_frame = tk.Frame(lf_totales, bg="#FFFFFF")
        totales_frame.pack(fill="x")

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

        # Botón profesional igual al de Factura PDF con imagen
        ruta_img = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "img")
        )
        try:
            img_pdf = ImageTk.PhotoImage(
                Image.open(os.path.join(ruta_img, "imprimir.png")).resize((28, 28))
            )
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
            command=self.generar_pdf_mes,
            padx=10,
            anchor="w",
        )
        self.btn_pdf.image = img_pdf
        self.btn_pdf.pack(side="right", padx=(0, 10), pady=(0, 5))

        # Carga los datos en un hilo para que la interfaz sea inmediata
        threading.Thread(target=self.cargar_datos, daemon=True).start()

    def cargar_datos(self):
        conn = get_connection()
        cursor = conn.cursor()
        # Traer ventas pagadas con detalle, producto, hora y cliente (incluyendo ventas rápidas)
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
            ORDER BY v.fecha ASC, v.hora ASC
            """
        )
        rows = cursor.fetchall()
        conn.close()

        # Agrupar por meses personalizados (cada 30 días desde la fecha más antigua)
        if not rows:
            return

        fechas = [datetime.datetime.strptime(r[0], "%Y-%m-%d") for r in rows]
        fecha_inicio = min(fechas)
        fecha_fin = max(fechas)

        meses = []
        actual_inicio = fecha_inicio
        num_mes = 1

        # Mostrar siempre el rango completo de 30 días, aunque no haya ventas en todos los días
        while actual_inicio <= fecha_fin:
            actual_fin = actual_inicio + datetime.timedelta(days=29)
            # El campo "Hasta (Fecha)" siempre será 29 días después de "Desde (Fecha)"
            # aunque no haya ventas en todos esos días
            nombre_mes_actual = MESES_ES[actual_inicio.month - 1]
            mes_siguiente_num = actual_inicio.month % 12 + 1
            nombre_mes_siguiente = MESES_ES[mes_siguiente_num - 1]
            nombre_meses = f"{nombre_mes_actual} - {nombre_mes_siguiente}"
            meses.append((num_mes, nombre_meses, actual_inicio, actual_fin))
            actual_inicio = actual_fin + datetime.timedelta(days=1)
            num_mes += 1

        # Agrupar ventas por mes personalizado
        resumen_mensual = []
        for num_mes, nombre_meses, mes_ini, mes_fin in meses:
            total_ventas = 0
            total_ganancia = 0
            productos_vendidos = 0
            clientes_set = set()
            for fecha, hora, cliente, producto, cantidad, costo, precio in rows:
                fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
                if mes_ini <= fecha_dt <= mes_fin:
                    total_ventas += precio * cantidad
                    total_ganancia += (precio - costo) * cantidad
                    productos_vendidos += cantidad
                    clientes_set.add(cliente)
            # Mostrar el registro aunque no haya ventas en todos los días del rango
            if productos_vendidos > 0:
                resumen_mensual.append(
                    (
                        num_mes,
                        nombre_meses,
                        mes_ini.strftime("%Y-%m-%d"),  # Desde (Fecha)
                        mes_fin.strftime(
                            "%Y-%m-%d"
                        ),  # Hasta (Fecha) SIEMPRE 29 días después
                        f"${total_ventas:,.0f}".replace(",", "."),
                        f"${total_ganancia:,.0f}".replace(",", "."),
                        productos_vendidos,
                        len(clientes_set),
                    )
                )

        self.tree.delete(*self.tree.get_children())
        total_ganancia = 0
        total_ventas = 0
        for row in resumen_mensual:
            self.tree.insert("", "end", values=row)
            total_ventas += float(
                row[4].replace("$", "").replace(".", "").replace(",", "")
            )
            total_ganancia += float(
                row[5].replace("$", "").replace(".", "").replace(",", "")
            )
        self.var_total_ganancia.set(f"${total_ganancia:,.0f}".replace(",", "."))
        self.var_total_ventas.set(f"${total_ventas:,.0f}".replace(",", "."))

    def generar_pdf_mes(self):
        """
        Genera un PDF del registro mensual seleccionado en la tabla.
        """
        seleccionado = self.tree.selection()
        if not seleccionado:
            messagebox.showwarning(
                "Advertencia",
                "Seleccione un registro mensual para imprimir.",
                parent=self,
            )
            return

        item = seleccionado[0]
        (
            num_mes,
            nombre_meses,
            fecha_de,
            fecha_hasta,
            total_ventas,
            total_ganancia,
            productos_vendidos,
            clientes,
        ) = self.tree.item(item, "values")

        archivo_pdf = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"Mes_{fecha_de}_a_{fecha_hasta}.pdf",
            title="Guardar mes como PDF",
            filetypes=[("Archivos PDF", "*.pdf")],
            initialdir=os.path.expanduser("~"),
            parent=self,
        )

        if archivo_pdf:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.pdfgen import canvas

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
            titulo = "Factura Mensual"
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
            c.drawString(40, y, f"Mes N°: {num_mes}")
            c.drawString(40, y - 25, f"Periodo: {nombre_meses}")
            c.drawString(40, y - 50, f"Desde: {fecha_de}")
            c.drawString(40, y - 75, f"Hasta: {fecha_hasta}")

            # Totales destacados
            y_totales = y - 120
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y_totales, f"Total Ventas: {total_ventas}")
            c.drawString(240, y_totales, f"Ganancia: {total_ganancia}")
            c.drawString(40, y_totales - 25, f"Productos Vendidos: {productos_vendidos}")
            c.drawString(240, y_totales - 25, f"Clientes: {clientes}")

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
                from retail.utils.fileops import open_file_silently
                open_file_silently(archivo_pdf)
                temp = tk.Toplevel(self)
                temp.withdraw()
                temp.attributes("-topmost", True)
                temp.after(1000, temp.destroy)
            except Exception:
                pass
