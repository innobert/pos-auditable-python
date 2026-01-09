import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import webbrowser
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from datetime import datetime
from PIL import Image, ImageTk
from retail.core.database import (
    get_connection,
    anular_venta,
    registrar_historial_deuda,
    obtener_productos,
)
from retail.core.config import rutas, obtener_ruta_logo
from retail.ventas.historial_ventas import abrir_historial_ventas
from retail.utils.logo import cambiar_logo
from retail.utils.fileops import open_file_silently


def ver_facturas(parent):
    ventana_facturas = tk.Toplevel(parent)
    ventana_facturas.title("Facturas")
    ventana_facturas.geometry("1100x600+130+20")
    ventana_facturas.configure(bg="#E6D9E3")
    ventana_facturas.resizable(False, False)
    ventana_facturas.transient(parent)
    ventana_facturas.grab_set()
    ventana_facturas.lift()

    # Guardar el último directorio como atributo de la ventana
    ventana_facturas.ultimo_directorio = os.path.expanduser("~")

    # Frame principal para la tabla
    frame_tabla = tk.Frame(ventana_facturas, bg="#F5F5F5", padx=10, pady=10)
    frame_tabla.place(x=10, y=10, width=870, height=580)

    # Reordenado: queremos que "Recibido" y "Vuelto" aparezcan ANTES de "Total"
    columnas = (
        "ID",
        "N°",
        "Cliente",
        "Productos",
        "Hora",
        "Fecha",
        "Recibido",
        "Vuelto",
        "Total",
        "Zona",
        "¿Pagó?",
    )
    tree = ttk.Treeview(
        frame_tabla,
        columns=columnas,
        show="headings",
        selectmode="browse",
    )

    # Definir las columnas con sus identificadores y anchos
    config_columnas = [
        ("ID", 0),
        ("N°", 50),
        ("Cliente", 130),
        ("Productos", 220),
        ("Hora", 80),
        ("Fecha", 100),
        ("Recibido", 90),
        ("Vuelto", 90),
        ("Total", 90),
        ("Zona", 100),
        ("¿Pagó?", 60),
    ]
    for col, width in config_columnas:
        tree.heading(col, text=col)
        tree.column(col, width=width, anchor="center")
    tree.column("ID", width=0, stretch=tk.NO)

    # Scrollbars
    scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical")
    scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal")
    tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    scroll_y.config(command=tree.yview)
    scroll_x.config(command=tree.xview)

    # Colocar widgets usando grid para mejor control
    tree.grid(row=0, column=0, sticky="nsew")
    scroll_y.grid(row=0, column=1, sticky="ns")
    scroll_x.grid(row=1, column=0, sticky="ew")

    # Configurar el frame para expandir el treeview correctamente
    frame_tabla.grid_rowconfigure(0, weight=1)
    frame_tabla.grid_columnconfigure(0, weight=1)

    # Label Frame Búscar
    frame_buscar = tk.LabelFrame(
        ventana_facturas,
        text="Búsqueda de Ventas",
        font=("Helvetica", 12, "bold"),
        bg="#E6D9E3",
    )
    frame_buscar.place(x=900, y=10, width=190, height=70)

    combo_buscar = ttk.Combobox(
        frame_buscar,
        font=("Calibri", 12),
        state="normal",  # Permite escribir para búsqueda
    )
    combo_buscar.pack(pady=5, padx=10, fill="x")
    combo_buscar.bind("<KeyRelease>", lambda event: filtrar_facturas())
    combo_buscar.bind("<<ComboboxSelected>>", lambda event: filtrar_facturas())

    # Label Frame Opciones
    lf_opciones = tk.LabelFrame(
        ventana_facturas,
        text="Opciones",
        font=("Helvetica", 12, "bold"),
        bg="#E6D9E3",
    )
    lf_opciones.place(x=900, y=90, width=190, height=270)  # <-- altura aumentada

    def cargar_facturas():
        tree.delete(*tree.get_children())
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT v.id_ventas,
                   COALESCE(c.nombres || ' ' || c.apellidos, v.cliente_rapido) AS cliente,
                   GROUP_CONCAT(i.producto || ' x' || dv.cantidad, ', '),
                   v.hora, v.fecha, v.total, v.monto_recibido, v.vuelto,
                   COALESCE(c.zona, 'Local') AS zona,
                   dv.pago
            FROM ventas v
            LEFT JOIN clientes c ON v.cliente_venta = c.id_cliente
            JOIN detalle_venta dv ON v.id_ventas = dv.id_ventas
            JOIN inventario i ON dv.id_producto = i.id_producto
            GROUP BY v.id_ventas
            ORDER BY v.id_ventas ASC
            """
        )
        facturas = cursor.fetchall()
        conn.close()
        # Actualizar el combobox de búsqueda con los nombres de clientes únicos
        clientes_unicos = list({factura[1] for factura in facturas})
        combo_buscar["values"] = clientes_unicos
        combo_buscar.set("")
        for idx, factura in enumerate(facturas, 1):
            # Desempaquetar en el mismo orden de las columnas: (ID, N°, Cliente, Productos, Hora, Fecha, Total, Recibido, Vuelto, Zona, ¿Pagó?)
            id_ventas = factura[0]
            cliente = factura[1]
            productos = factura[2]
            hora = factura[3]
            fecha = factura[4]
            total = factura[5]
            recibido = factura[6] if len(factura) > 6 and factura[6] is not None else 0
            vuelto = factura[7] if len(factura) > 7 and factura[7] is not None else 0
            zona = factura[8]
            pago = factura[9]
            # Insertar valores respetando el nuevo orden de columnas: Recibido, Vuelto ANTES de Total
            tree.insert(
                "",
                "end",
                values=(
                    id_ventas,   # ID (oculto)
                    idx,         # N° (secuencial)
                    cliente,
                    productos,
                    hora,
                    fecha,
                    f"${recibido:,.0f}".replace(",", "."),
                    f"${vuelto:,.0f}".replace(",", "."),
                    f"${total:,.0f}".replace(",", "."),
                    zona,
                    "Sí" if pago == 1 else "No",
                ),
            )
        actualizar_total_facturas()  # <-- Asegura que el total se actualice siempre

    def actualizar_total_facturas():
        # Sumar SIEMPRE el total de todas las ventas existentes en la tabla ventas
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT SUM(total)
            FROM ventas
            """
        )
        resultado = cursor.fetchone()
        conn.close()
        total = resultado[0] if resultado and resultado[0] else 0
        var_total_facturas.set(f"${total:,.0f}".replace(",", "."))

    def filtrar_facturas():
        texto = combo_buscar.get().strip().lower()
        tree.delete(*tree.get_children())
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
         SELECT v.id_ventas,
             COALESCE(c.nombres || ' ' || c.apellidos, v.cliente_rapido) AS cliente,
             GROUP_CONCAT(i.producto || ' x' || dv.cantidad, ', '),
             v.hora, v.fecha, v.total, v.monto_recibido, v.vuelto,
             COALESCE(c.zona, 'Local') AS zona,
             dv.pago
            FROM ventas v
            LEFT JOIN clientes c ON v.cliente_venta = c.id_cliente
            JOIN detalle_venta dv ON v.id_ventas = dv.id_ventas
            JOIN inventario i ON dv.id_producto = i.id_producto
            GROUP BY v.id_ventas
            ORDER BY v.id_ventas ASC
            """
        )
        facturas = cursor.fetchall()
        conn.close()
        total_filtrado = 0  # <-- Nuevo: acumulador para el total filtrado
        if texto == "":
            for idx, factura in enumerate(facturas, 1):
                id_ventas = factura[0]
                cliente = factura[1]
                productos = factura[2]
                hora = factura[3]
                fecha = factura[4]
                total = factura[5]
                recibido = factura[6] if len(factura) > 6 and factura[6] is not None else 0
                vuelto = factura[7] if len(factura) > 7 and factura[7] is not None else 0
                zona = factura[8]
                pago = factura[9]
                tree.insert(
                    "",
                    "end",
                    values=(
                        id_ventas,   # ID (oculto)
                        idx,         # N° (secuencial)
                        cliente,
                        productos,
                        hora,
                        fecha,
                        f"${recibido:,.0f}".replace(",", "."),
                        f"${vuelto:,.0f}".replace(",", "."),
                        f"${total:,.0f}".replace(",", "."),
                        zona,
                        "Sí" if pago == 1 else "No",
                    ),
                )
                total_filtrado += float(total) if total else 0  # <-- Sumar total
        else:
            idx = 1
            for factura in facturas:
                id_ventas = factura[0]
                cliente = factura[1]
                productos = factura[2]
                hora = factura[3]
                fecha = factura[4]
                total = factura[5]
                recibido = factura[6] if len(factura) > 6 and factura[6] is not None else 0
                vuelto = factura[7] if len(factura) > 7 and factura[7] is not None else 0
                zona = factura[8]
                pago = factura[9]
                if texto in cliente.lower():
                    tree.insert(
                        "",
                        "end",
                        values=(
                            id_ventas,   # ID (oculto)
                            idx,         # N° (secuencial filtrado)
                            cliente,
                            productos,
                            hora,
                            fecha,
                            f"${recibido:,.0f}".replace(",", "."),
                            f"${vuelto:,.0f}".replace(",", "."),
                            f"${total:,.0f}".replace(",", "."),
                            zona,
                            "Sí" if pago == 1 else "No",
                        ),
                    )
                    total_filtrado += float(total) if total else 0 # <-- Sumar total solo de los filtrados
                    idx += 1
        var_total_facturas.set(f"${total_filtrado:,.0f}".replace(",", "."))  # <-- Mostrar total filtrado

    def anular_factura():
        seleccionado = tree.selection()
        if not seleccionado:
            messagebox.showwarning(
                "Advertencia",
                "Seleccione una factura para anular.",
                parent=ventana_facturas,
            )
            return
        item = seleccionado[0]
        valores = tree.item(item, "values")
        # columnas = ("ID", "N°", "Cliente", "Productos", "Hora", "Fecha", "Total", "Zona", "¿Pagó?")
        id_ventas = int(valores[0])
        if messagebox.askyesno(
            "Confirmar",
            "¿Está seguro de anular esta factura?",
            parent=ventana_facturas,
        ):
            anular_venta(id_ventas)
            cargar_facturas()
            messagebox.showinfo(
                "Éxito", "Factura anulada correctamente.", parent=ventana_facturas
            )

    def format_currency(value):
        try:
            return "${:,.0f}".format(float(value)).replace(",", ".")
        except Exception:
            return str(value)

    def generar_factura():
        seleccionado = tree.selection()
        if not seleccionado:
            messagebox.showwarning(
                "Advertencia",
                "Seleccione una factura para generar.",
                parent=ventana_facturas,
            )
            return

        item = seleccionado[0]
        valores = tree.item(item, "values")
        # Asegúrate de que los índices coincidan con las columnas definidas arriba
        # columnas = ("ID", "N°", "Cliente", "Productos", "Hora", "Fecha", "Recibido", "Vuelto", "Total", "Zona", "¿Pagó?")
        id_ventas = int(valores[0])
        factura_idx = valores[1]
        cliente = valores[2]
        productos = valores[3]
        hora = valores[4]
        fecha = valores[5]
        recibido = valores[6]
        vuelto = valores[7]
        total = valores[8]
        zona = valores[9]
        pago = valores[10]

        # Usar id_ventas para buscar detalles
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT i.producto, dv.cantidad, dv.subtotal, dv.hora_producto, dv.fecha_producto
            FROM detalle_venta dv
            JOIN inventario i ON dv.id_producto = i.id_producto
            WHERE dv.id_ventas = ?
            """,
            (id_ventas,),
        )
        productos_detalle = cursor.fetchall()
        conn.close()

        if not productos_detalle:
            messagebox.showerror(
                "Error",
                f"No se encontraron productos para la factura {id_ventas}",
                parent=ventana_facturas,
            )
            return

        archivo_pdf = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"Factura_{factura_idx}.pdf",
            title="Guardar factura como",
            filetypes=[("Archivos PDF", "*.pdf")],
            initialdir=getattr(
                ventana_facturas, "ultimo_directorio", os.path.expanduser("~")
            ),
            parent=ventana_facturas,
        )

        if archivo_pdf:
            ventana_facturas.ultimo_directorio = os.path.dirname(archivo_pdf)
            c = canvas.Canvas(archivo_pdf, pagesize=letter)
            width, height = letter

            # Logo arriba derecha
            ruta_logo = obtener_ruta_logo("logo.png")
            try:
                c.drawImage(ruta_logo, width - 180, height - 150, width=140, height=140, mask='auto')
            except Exception as e:
                print(f"Error al cargar el logo: {e}")

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

            # Datos de la factura
            c.setFont("Helvetica-Bold", 13)
            y = height - 120
            c.drawString(40, y, f"N° Factura: {factura_idx}")
            c.drawString(40, y - 25, f"Cliente: {cliente}")

            # Tabla de productos
            y_tabla = y - 70
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y_tabla, "Producto")
            c.drawString(200, y_tabla, "Hora")
            c.drawString(270, y_tabla, "Fecha")
            c.drawString(360, y_tabla, "Cantidad")
            c.drawString(440, y_tabla, "Subtotal")
            c.line(30, y_tabla - 5, width - 30, y_tabla - 5)

            # Mostrar hora_producto y fecha_producto para cada producto
            c.setFont("Helvetica", 11)
            y_fila = y_tabla - 25
            total_calculado = 0
            for prod, cant, sub, hora_prod, fecha_prod in productos_detalle:
                c.drawString(40, y_fila, str(prod))
                c.drawString(200, y_fila, str(hora_prod) if hora_prod else "")
                c.drawString(270, y_fila, str(fecha_prod) if fecha_prod else "")
                c.drawString(360, y_fila, str(cant))
                c.drawString(440, y_fila, format_currency(sub))
                total_calculado += float(sub)
                y_fila -= 20

            # Línea antes del total
            c.line(30, y_fila + 10, width - 30, y_fila + 10)

            # Total destacado
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y_fila - 20, f"Total: {format_currency(total_calculado)}")

            # Mostrar Recibido y Vuelto (siempre): usamos los valores obtenidos de la fila seleccionada
            try:
                recibido_str = str(recibido)
            except Exception:
                recibido_str = format_currency(0)
            try:
                vuelto_str = str(vuelto)
            except Exception:
                vuelto_str = format_currency(0)

            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y_fila - 45, f"Recibido: {recibido_str}")
            c.drawString(40, y_fila - 65, f"Vuelto: {vuelto_str}")

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
                f"Factura generada correctamente en:\n{archivo_pdf}",
                parent=ventana_facturas,
            )
            try:
                from retail.utils.fileops import open_file_silently
                open_file_silently(archivo_pdf)
                temp = tk.Toplevel(ventana_facturas)
                temp.withdraw()
                temp.attributes("-topmost", True)
                temp.after(1000, temp.destroy)
            except Exception:
                pass

    def marcar_como_deuda():
        seleccionado = tree.selection()
        if not seleccionado:
            messagebox.showwarning(
                "Advertencia",
                "Seleccione una factura para marcar como deuda.",
                parent=ventana_facturas,
            )
            return
        item_values = tree.item(seleccionado[0], "values")
        cliente_display = item_values[2]
        hora_display = item_values[4]
        fecha_display = item_values[5]
        # Con el nuevo orden de columnas, el Total está en la posición 8
        total_display = float(item_values[8].replace("$", "").replace(".", "").replace(",", "."))

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT v.id_ventas, v.cliente_venta, v.cliente_rapido, v.total
            FROM ventas v
            LEFT JOIN clientes c ON v.cliente_venta = c.id_cliente
            WHERE (COALESCE(c.nombres || ' ' || c.apellidos, v.cliente_rapido) = ? OR v.cliente_rapido = ?)
              AND v.fecha = ? AND v.hora = ? AND v.total = ?
            """,
            (cliente_display, cliente_display, fecha_display, hora_display, total_display)
        )
        venta_data = cursor.fetchone()

        if not venta_data:
            conn.close()
            messagebox.showerror(
                "Error",
                "No se pudo identificar la factura en la base de datos. Por favor, recargue la ventana e intente de nuevo.",
                parent=ventana_facturas,
            )
            return

        id_ventas, cliente_venta, cliente_rapido, total = venta_data
        if not messagebox.askyesno(
            "Confirmar",
            "¿Está seguro que desea marcar esta factura como deuda?\n"
            "El registro se moverá a la sección de Deudas.",
            parent=ventana_facturas,
        ):
            conn.close()
            return
        cursor.execute(
            "SELECT id_producto, cantidad, subtotal FROM detalle_venta WHERE id_ventas = ?",
            (id_ventas,),
        )
        detalles = cursor.fetchall()
        if not detalles:
            conn.close()
            messagebox.showerror(
                "Error",
                "No se encontraron detalles para la factura seleccionada.",
                parent=ventana_facturas,
            )
            return

        from datetime import datetime
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        hora_actual = datetime.now().strftime("%H:%M:%S")

        # Actualizar la venta a crédito y crear deuda
        cursor.execute(
            "UPDATE ventas SET tipo = 'CREDITO' WHERE id_ventas = ?",
            (id_ventas,)
        )
        cursor.execute(
            "INSERT INTO deudas (id_ventas, cliente_id, fecha, total, saldo) VALUES (?, ?, ?, ?, ?)",
            (id_ventas, cliente_venta, fecha_actual, total, total),
        )
        id_deuda = cursor.lastrowid

        # --- REGISTRO ÚNICO POR MOVIMIENTO EN HISTORIAL_DEUDAS ---
        for id_producto, cantidad, subtotal in detalles:
            registrar_historial_deuda(
                id_deuda=id_deuda,
                id_producto=id_producto,
                cantidad=cantidad,
                subtotal=subtotal,
                accion="Deuda",
                usuario=os.getlogin() if hasattr(os, "getlogin") else "sistema",
                detalle=f"Factura marcada como deuda: Producto ID {id_producto} x{cantidad} para cliente '{cliente_venta or cliente_rapido}'. Subtotal: {subtotal}, Fecha: {fecha_actual}, Hora: {hora_actual}",
                cursor=cursor,
            )
        # No eliminar nada, mantener la venta para auditoría
        conn.commit()
        conn.close()
        cargar_facturas()
        actualizar_total_facturas()
        messagebox.showinfo(
            "Éxito",
            "La factura ha sido marcada como deuda.",
            parent=ventana_facturas,
        )
        # Actualizar deudas si la vista está abierta
        parent = ventana_facturas.master
        while parent:
            if hasattr(parent, "frames"):
                for frame in parent.frames.values():
                    if frame.__class__.__name__.lower() == "deudas":
                        if hasattr(frame, "cargar_deudas"):
                            frame.cargar_deudas()
                break
            parent = getattr(parent, "master", None)

    # Cargar imágenes para los botones

    ruta_img = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "img"))

    def cargar_img(nombre):
        try:
            return ImageTk.PhotoImage(Image.open(os.path.join(ruta_img, nombre)).resize((28, 28)))
        except Exception:
            return None

    img_imprimir = cargar_img("imprimir.png")
    img_mora = cargar_img("mora.png")
    img_eliminar = cargar_img("eliminar.png")
    img_historial = cargar_img("historial.png")
    img_cambiar = cargar_img("cambiar.png")

    # Botón Generar Factura
    btn_generar = tk.Button(
        lf_opciones,
        text="  Factura PDF",
        image=img_imprimir,
        compound="left",
        font=("Helvetica", 13, "bold"),
        bg="#1976D2",
        fg="white",
        activebackground="#388E3C",
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        command=generar_factura,
        padx=10,
        anchor="w"
    )
    btn_generar.image = img_imprimir
    btn_generar.pack(pady=7, padx=10, fill="x")

    # Botón Anular Factura
    btn_eliminar = tk.Button(
        lf_opciones,
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
        command=anular_factura,
        padx=10,
        anchor="w"
    )
    btn_eliminar.image = img_eliminar
    btn_eliminar.pack(pady=7, padx=10, fill="x")

    # Botón Deuda (Pagada/Mora)
    btn_deuda = tk.Button(
        lf_opciones,
        text="  Deuda",
        image=img_mora,
        compound="left",
        font=("Helvetica", 13, "bold"),
        bg="#DC143C",
        fg="white",
        activebackground="#8B0000",
        activeforeground="white",
        relief="flat",
        bd=0,
        cursor="hand2",
        command=marcar_como_deuda,
        padx=10,
        anchor="w"
    )
    btn_deuda.image = img_mora
    btn_deuda.pack(pady=7, padx=10, fill="x")

    # Botón Historial
    def abrir_historial_cliente_seleccionado():
        seleccionado = tree.selection()
        if not seleccionado:
            messagebox.showwarning(
                "Advertencia",
                "Seleccione una factura para ver el historial del cliente.",
                parent=ventana_facturas,
            )
            return
        item = seleccionado[0]
        valores = tree.item(item, "values")
        id_ventas = valores[0]
        cliente = valores[2]
        abrir_historial_ventas(ventana_facturas, id_ventas=id_ventas, nombre_cliente=cliente, facturas_window=ventana_facturas)

    btn_historial = tk.Button(
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
        command=abrir_historial_cliente_seleccionado,
        padx=10,
        anchor="w"
    )
    btn_historial.image = img_historial
    btn_historial.pack(pady=7, padx=10, fill="x")

    # Botón Cambiar Logo
    btn_logo = tk.Button(
        lf_opciones,
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
        command=lambda: cambiar_logo(ventana_facturas),
        padx=10,
        anchor="w"
    )
    btn_logo.image = img_cambiar
    btn_logo.pack(pady=7, padx=10, fill="x")

    # LabelFrame para el Total de Facturas
    lf_total_facturas = tk.LabelFrame(
        ventana_facturas,
        text="Total Ventas",
        font=("Helvetica", 12, "bold"),
        bg="#E6D9E3",
    )
    lf_total_facturas.place(x=900, y=370, width=190, height=70)

    var_total_facturas = tk.StringVar(value="$0")
    lbl_total_facturas = tk.Label(
        lf_total_facturas,
        textvariable=var_total_facturas,
        font=("Helvetica", 16, "bold"),
        bg="#E6D9E3",
        fg="#008B8B",
    )
    lbl_total_facturas.pack(expand=True, fill="both", pady=10)

    # --- NUEVO: Permitir actualización externa desde historial ---
    # Esto permite que desde otras ventanas (como historial) se pueda actualizar correctamente
    ventana_facturas.cargar_facturas = cargar_facturas
    ventana_facturas.actualizar_total_facturas = actualizar_total_facturas

    cargar_facturas()

    # --- Al final de ver_facturas, después de cargar_facturas() ---
    def abrir_agregar_productos_cliente(event=None):
        seleccionado = tree.selection()
        if not seleccionado:
            messagebox.showwarning(
                "Advertencia",
                "Seleccione una factura para añadir productos.",
                parent=ventana_facturas,
            )
            return
        item = seleccionado[0]
        valores = tree.item(item, "values")
        id_ventas = int(valores[0])
        cliente = valores[2]

        top = tk.Toplevel(ventana_facturas)
        top.title(f"Añadir productos a: {cliente}")
        top.geometry("1100x650+120+40")
        top.configure(bg="#E6D9E3")
        top.resizable(False, False)
        top.grab_set()

        label_titulo = tk.Label(
            top,
            text=f"Añadir productos a: {cliente}",
            font=("Helvetica", 15, "bold"),
            bg="#4CAF50",
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

        # --- Diálogo para seleccionar cantidad y validar stock ---
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
                    conn = get_connection()
                    cursor = conn.cursor()
                    subtotal = cantidad * producto[2]
                    hora_actual = datetime.now().strftime("%H:%M:%S")
                    fecha_actual = datetime.now().strftime("%Y-%m-%d")
                    cursor.execute(
                        "INSERT INTO detalle_venta (id_producto, cantidad, subtotal, pago, id_ventas, id_deuda, hora_producto, fecha_producto) VALUES (?, ?, ?, 1, ?, NULL, ?, ?)",
                        (
                            producto[0],
                            cantidad,
                            subtotal,
                            id_ventas,
                            hora_actual,
                            fecha_actual,
                        ),
                    )
                    cursor.execute(
                        "UPDATE inventario SET stock = stock - ? WHERE id_producto = ?",
                        (cantidad, producto[0]),
                    )
                    cursor.execute(
                        "SELECT SUM(subtotal) FROM detalle_venta WHERE id_ventas = ?",
                        (id_ventas,),
                    )
                    nuevo_total = cursor.fetchone()[0] or 0
                    cursor.execute(
                        "UPDATE ventas SET total = ? WHERE id_ventas = ?",
                        (nuevo_total, id_ventas),
                    )
                    conn.commit()
                    conn.close()
                    # Registrar SIEMPRE un nuevo registro en historial_ventas
                    from retail.core.database import registrar_historial_venta
                    registrar_historial_venta(
                        id_ventas=id_ventas,
                        id_producto=producto[0],
                        cantidad=cantidad,
                        subtotal=subtotal,
                        accion="Editado",
                        usuario=os.getlogin() if hasattr(os, "getlogin") else "sistema",
                        detalle=f"Editado producto '{producto[1]}' (ID:{producto[0]}) x{cantidad} a la factura {id_ventas} para el cliente '{cliente}' desde el frame de añadir productos. Subtotal: {subtotal}, Fecha: {fecha_actual}, Hora: {hora_actual}",
                    )
                    cargar_facturas()
                    actualizar_total_facturas()
                    messagebox.showinfo(
                        "Producto añadido",
                        f"Se añadieron {cantidad} unidades de '{producto[1]}' a la factura del cliente '{cliente}'.",
                        parent=top_cant,
                    )
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

    # Asocia el doble click en la tabla de facturas
    tree.bind("<Double-1>", abrir_agregar_productos_cliente)
