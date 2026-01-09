import tkinter as tk
from tkinter import ttk, messagebox
from retail.core.database import obtener_productos, get_connection
import os
from PIL import Image, ImageTk

def mostrar_historial_inventario(parent):
    # Buscar el producto seleccionado en el frame de selección
    try:
        producto_nombre = parent.seleccion_vars["producto"].get()
    except Exception:
        producto_nombre = ""

    if not producto_nombre:
        messagebox.showwarning("Selecciona un producto", "Debes seleccionar un producto para ver su historial.", parent=parent)
        return

    # Buscar el producto en la base de datos
    productos = obtener_productos()
    producto = next((p for p in productos if p[1] == producto_nombre), None)
    if not producto:
        messagebox.showerror("Producto no encontrado", "No se encontró el producto seleccionado.", parent=parent)
        return

    id_producto = producto[0]

    # Obtener historial de la base de datos (sin mostrar el campo ID)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id_historial, dia, fecha, hora, accion, pedido, stock, precio, costo, ganancia, total
        FROM historial_inventario
        WHERE id_producto = ?
        ORDER BY fecha DESC, hora DESC
        """,
        (id_producto,)
    )
    historial = cursor.fetchall()
    conn.close()

    # Días de la semana en español
    dias_es = {
        "Monday": "Lunes",
        "Tuesday": "Martes",
        "Wednesday": "Miércoles",
        "Thursday": "Jueves",
        "Friday": "Viernes",
        "Saturday": "Sábado",
        "Sunday": "Domingo",
        "Lunes": "Lunes", "Martes": "Martes", "Miércoles": "Miércoles",
        "Jueves": "Jueves", "Viernes": "Viernes", "Sábado": "Sábado", "Domingo": "Domingo"
    }

    # Crear ventana modal profesional (más angosta)
    top = tk.Toplevel(parent)
    top.title(f"Historial de {producto_nombre}")
    top.geometry("1100x520+110+50")
    top.configure(bg="#F5F5F5")
    top.resizable(False, False)
    top.transient(parent)
    top.grab_set()

    # Cargar imagen de eliminar
    ruta_img = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "img"))
    try:
        img_delete = ImageTk.PhotoImage(Image.open(os.path.join(ruta_img, "eliminar.png")).resize((22, 22)))
    except Exception:
        img_delete = None

    # Título principal y botón eliminar
    frame_titulo = tk.Frame(top, bg="#4CAF50")
    frame_titulo.pack(fill="x")
    tk.Label(
        frame_titulo,
        text=f"Historial de {producto_nombre}",
        font=("Helvetica", 18, "bold"),
        bg="#4CAF50",
        fg="white",
        pady=14
    ).pack(side="left", fill="x", expand=True, padx=(10, 0))

    def eliminar_registro_historial():
        item = tree.selection()
        if not item:
            messagebox.showwarning("Selecciona un registro", "Seleccione un registro para eliminar.", parent=top)
            return
        # El id_historial está oculto en el primer valor de cada fila
        id_historial = tree.item(item[0], "tags")[0]
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este registro del historial?", parent=top):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM historial_inventario WHERE id_historial = ?", (id_historial,))
            conn.commit()
            conn.close()
            tree.delete(item[0])
            messagebox.showinfo("Eliminado", "Registro eliminado correctamente.", parent=top)

    btn_eliminar = tk.Button(
        frame_titulo,
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
        command=eliminar_registro_historial,
        padx=10,  # Igual que inventario.py
        anchor="w",
        width=150,  # No es necesario en Button, se usa place para tamaño
        height=40   # No es necesario en Button, se usa place para tamaño
    )
    btn_eliminar.image = img_delete
    btn_eliminar.pack_forget()  # Elimina el pack anterior si existe
    btn_eliminar.place(x=900, y=10, width=150, height=40)  # Ajusta la posición y tamaño igual que inventario.py

    # Frame para la tabla y scrollbar
    frame_tabla = tk.Frame(top, bg="#F5F5F5")
    frame_tabla.pack(fill="both", expand=True, padx=10, pady=(18, 10))

    columnas = [
        "Día", "Fecha", "Hora", "Acción", "Pedido", "Stock",
        "Precio", "Costo", "Ganancia", "Total"
    ]

    style = ttk.Style(top)
    style.theme_use("clam")
    style.configure("Treeview.Heading", font=("Calibri", 14, "bold"), background="#E6D9E3", foreground="#333")
    style.configure("Treeview", font=("Calibri", 13), rowheight=32, background="#fff", fieldbackground="#fff")
    style.map("Treeview", background=[("selected", "#222")], foreground=[("selected", "#fff")])

    tree = ttk.Treeview(
        frame_tabla,
        columns=columnas,
        show="headings",
        height=12,
        style="Treeview"
    )
    # Ajustar anchos y alineación para aprovechar el ancho de la ventana
    col_widths = [100, 110, 90, 110, 90, 90, 110, 110, 120, 120]
    for idx, col in enumerate(columnas):
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=col_widths[idx], minwidth=col_widths[idx])

    tree.pack(side="left", fill="both", expand=True)

    # Scrollbar
    scrollbar = ttk.Scrollbar(frame_tabla, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    # Formato de moneda
    def peso_colombiano(value):
        try:
            return f"${float(value):,.0f}".replace(",", ".")
        except Exception:
            return value

    # Insertar datos en la tabla (sin mostrar ID, pero lo guardamos en tags para eliminar)
    for row in historial:
        dia = dias_es.get(row[1], row[1])
        accion = row[4]
        tree.insert(
            "",
            "end",
            values=(
                dia,     # Día en español
                row[2],  # Fecha
                row[3],  # Hora
                accion,  # Acción
                row[5],  # Pedido
                row[6],  # Stock
                peso_colombiano(row[7]),  # Precio
                peso_colombiano(row[8]),  # Costo
                peso_colombiano(row[9]),  # Ganancia
                peso_colombiano(row[10]), # Total
            ),
            tags=(row[0],)  # Guardar id_historial en tags para eliminar
        )

    # Pie de ventana con botón cerrar
    frame_footer = tk.Frame(top, bg="#F5F5F5")
    frame_footer.pack(fill="x", pady=(0, 10))
    tk.Button(
        frame_footer,
        text="Cerrar",
        font=("Helvetica", 13, "bold"),
        bg="#4CAF50",
        fg="white",
        activebackground="#388E3C",
        activeforeground="white",
        relief="flat",
        bd=0,
        width=12,
        height=1,
        command=top.destroy
    ).pack(pady=8)

    # Mejorar visualización y experiencia
    tree.focus_set()
    if tree.get_children():
        tree.selection_set(tree.get_children()[0])
        tree.yview_moveto(0)
