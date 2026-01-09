import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from retail.core.config import obtener_ruta_logo

def cambiar_logo(parent):
    logo_dir = obtener_ruta_logo()
    os.makedirs(logo_dir, exist_ok=True)
    logo_default = obtener_ruta_logo("logo.png")  # <-- Cambiado aquí

    # Ventana modal
    top = tk.Toplevel(parent)
    top.title("Cambiar Logo de Factura")
    top.geometry("420x420+400+120")
    top.configure(bg="#E6D9E3")
    top.resizable(False, False)
    top.grab_set()

    # LabelFrame para la imagen
    lf_img = tk.LabelFrame(top, text="Logo Actual", font=("Helvetica", 12, "bold"), bg="#E6D9E3")
    lf_img.place(x=30, y=20, width=360, height=280)

    # Cargar logo actual o default
    logo_path = logo_default if os.path.exists(logo_default) else None
    img_label = tk.Label(lf_img, bg="white")
    img_label.pack(fill="both", expand=True, padx=10, pady=10)
    image_tk = None

    def mostrar_logo(path):
        nonlocal image_tk
        try:
            img = Image.open(path)
            img = img.resize((300, 200), Image.LANCZOS)
            image_tk = ImageTk.PhotoImage(img)
            img_label.config(image=image_tk, text="")
        except Exception:
            img_label.config(image="", text="Sin logo")

    if logo_path:
        mostrar_logo(logo_path)
    else:
        img_label.config(text="Sin logo")

    # Función para cargar imagen nueva
    def cargar_imagen():
        file_path = filedialog.askopenfilename(
            parent=top,
            title="Seleccionar imagen",
            filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")],
            initialdir=os.path.expanduser("~"),
        )
        if file_path:
            try:
                # Copiar imagen a la carpeta Logo con nombre original (opcional)
                nombre = os.path.basename(file_path)
                destino = os.path.join(logo_dir, nombre)
                with open(file_path, "rb") as src, open(destino, "wb") as dst:
                    dst.write(src.read())
                # Actualizar logo principal (logo.png)
                logo_actual = os.path.join(logo_dir, "logo.png")
                with open(file_path, "rb") as src, open(logo_actual, "wb") as dst:
                    dst.write(src.read())
                mostrar_logo(logo_actual)
                messagebox.showinfo("Éxito", "Logo actualizado correctamente.", parent=top)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar el logo:\n{e}", parent=top)

    # Botón para cargar imagen
    btn_cargar = tk.Button(
        top,
        text="Cargar Imagen",
        font=("Helvetica", 12, "bold"),
        bg="#2196F3",
        fg="white",
        command=cargar_imagen,
        padx=10,
        pady=4,
        relief="flat",
        cursor="hand2"
    )
    btn_cargar.place(x=140, y=320, width=140, height=40)

    # Botón cerrar
    btn_cerrar = tk.Button(
        top,
        text="Cerrar",
        font=("Helvetica", 12, "bold"),
        bg="#F44336",
        fg="white",
        command=top.destroy,
        padx=10,
        pady=4,
        relief="flat",
        cursor="hand2"
    )
    btn_cerrar.place(x=140, y=370, width=140, height=35)
