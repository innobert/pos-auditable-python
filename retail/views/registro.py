import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import retail.core.database as database
import datetime
import uuid
import hashlib

class VentanaRegistro(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Gestión de Usuarios")
        self.geometry("700x480+450+100")
        self.resizable(False, False)
        self.config(bg="#E6D9E3")

        self.transient(parent)
        self.grab_set()
        self.focus_set()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.widgets()

    def widgets(self):
        # Ajusta el tamaño de la ventana para mostrar mejor la imagen
        self.geometry("820x520+300+60")

        # Frame principal
        frame = tk.Frame(self, bg="#FFFFFF", bd=2, relief="groove")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Título
        tk.Label(
            frame,
            text="Registro de Usuarios",
            font=("Helvetica", 18, "bold"),
            bg="#FFFFFF",
            fg="#333333"
        ).pack(pady=(10, 10))

        # Frame para formulario y imagen
        form_img_frame = tk.Frame(frame, bg="#FFFFFF")
        form_img_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        # Frame para formulario
        form_frame = tk.Frame(form_img_frame, bg="#FFFFFF")
        form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 30))

        tk.Label(form_frame, text="Usuario:", font=("Helvetica", 13), bg="#FFFFFF").grid(row=0, column=0, sticky="e", pady=8, padx=5)
        self.entry_usuario = ttk.Entry(form_frame, font=("Helvetica", 13))
        self.entry_usuario.grid(row=0, column=1, pady=8, padx=5)

        tk.Label(form_frame, text="Contraseña:", font=("Helvetica", 13), bg="#FFFFFF").grid(row=1, column=0, sticky="e", pady=8, padx=5)
        self.entry_contrasena = ttk.Entry(form_frame, font=("Helvetica", 13), show="*")
        self.entry_contrasena.grid(row=1, column=1, pady=8, padx=5)

        tk.Label(form_frame, text="Confirmar Contraseña:", font=("Helvetica", 13), bg="#FFFFFF").grid(row=2, column=0, sticky="e", pady=8, padx=5)
        self.entry_confirmar = ttk.Entry(form_frame, font=("Helvetica", 13), show="*")
        self.entry_confirmar.grid(row=2, column=1, pady=8, padx=5)

        # Botones organizados y modernos
        btn_frame = tk.Frame(form_frame, bg="#FFFFFF")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=15)

        self.btn_registrar = tk.Button(
            btn_frame, text="Registrar", bg="#2196F3", fg="#fff", font=("Helvetica", 12, "bold"),
            command=self.registrar_usuario, relief="flat", cursor="hand2", width=12
        )
        self.btn_registrar.pack(side=tk.LEFT, padx=8)

        self.btn_actualizar = tk.Button(
            btn_frame, text="Actualizar", bg="#FFC107", fg="#fff", font=("Helvetica", 12, "bold"),
            command=self.actualizar_usuario, relief="flat", cursor="hand2", width=12
        )
        self.btn_actualizar.pack(side=tk.LEFT, padx=8)

        self.btn_eliminar = tk.Button(
            btn_frame, text="Eliminar", bg="#F44336", fg="#fff", font=("Helvetica", 12, "bold"),
            command=self.eliminar_usuario, relief="flat", cursor="hand2", width=12
        )
        self.btn_eliminar.pack(side=tk.LEFT, padx=8)

        # Imagen login.png en el registro (más grande y centrada)
        img_frame = tk.Frame(form_img_frame, bg="#FFFFFF")
        img_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
        try:
            ruta_login = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "img", "login.png"))
            img_login = Image.open(ruta_login).resize((260, 260), Image.LANCZOS)
            self.img_login_tk = ImageTk.PhotoImage(img_login)
            tk.Label(img_frame, image=self.img_login_tk, bg="#FFFFFF").pack(padx=10, pady=10)
        except Exception:
            tk.Label(img_frame, text="Sin imagen", bg="#FFFFFF", fg="red", font=("Helvetica", 12, "bold")).pack(padx=10, pady=10)

        # Tabla de usuarios con estilo profesional
        tabla_frame = tk.Frame(frame, bg="#FFFFFF")
        tabla_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview.Heading", font=("Helvetica", 14, "bold"), background="#E6D9E3", foreground="#333")
        style.configure("Treeview", font=("Helvetica", 13), rowheight=32, background="#fff", fieldbackground="#fff")
        style.map("Treeview", background=[("selected", "#222")], foreground=[("selected", "#fff")])

        columns = ("usuario", "contrasena", "fecha_inicio", "fecha_fin", "serial")
        self.tabla = ttk.Treeview(tabla_frame, columns=columns, show="headings", height=7, style="Treeview")
        self.tabla.heading("usuario", text="Usuario")
        self.tabla.heading("contrasena", text="Contraseña")
        self.tabla.heading("fecha_inicio", text="Inicio")
        self.tabla.heading("fecha_fin", text="Fin")
        self.tabla.heading("serial", text="Serial")
        self.tabla.column("usuario", width=120, anchor="center")
        self.tabla.column("contrasena", width=120, anchor="center")
        self.tabla.column("fecha_inicio", width=90, anchor="center")
        self.tabla.column("fecha_fin", width=90, anchor="center")
        self.tabla.column("serial", width=120, anchor="center")
        self.tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.tabla.yview)
        self.tabla.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tabla.bind("<Double-1>", self.seleccionar_usuario)
        self.cargar_usuarios()

    def on_close(self):
        self.grab_release()
        self.destroy()

    def registrar_usuario(self):
        usuario = self.entry_usuario.get().strip()
        contrasena = self.entry_contrasena.get().strip()
        confirmar = self.entry_confirmar.get().strip()
        if not usuario or not contrasena or not confirmar:
            messagebox.showwarning("Campos requeridos", "Complete todos los campos.", parent=self)
            return
        if contrasena != confirmar:
            messagebox.showwarning("Contraseña", "Las contraseñas no coinciden.", parent=self)
            return
        if len(contrasena) < 6:
            messagebox.showwarning("Contraseña", "La contraseña debe tener al menos 6 caracteres.", parent=self)
            return
        fecha_inicio = datetime.datetime.now().strftime("%Y-%m-%d")
        fecha_fin = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        serial = str(uuid.uuid4())  # Serial seguro y único
        contrasena_hash = hashlib.sha256(contrasena.encode()).hexdigest()
        try:
            with database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO usuarios (usuario, contrasena, fecha_inicio, fecha_fin, serial) VALUES (?, ?, ?, ?, ?)",
                    (usuario, contrasena_hash, fecha_inicio, fecha_fin, serial)
                )
                conn.commit()
            self.cargar_usuarios()
            messagebox.showinfo("Éxito", "Usuario registrado correctamente.", parent=self)
            self.entry_usuario.delete(0, tk.END)
            self.entry_contrasena.delete(0, tk.END)
            self.entry_confirmar.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar el usuario: {e}", parent=self)

    def seleccionar_usuario(self, event):
        seleccionado = self.tabla.selection()
        if not seleccionado:
            return
        item = seleccionado[0]
        valores = self.tabla.item(item, "values")

        # Abrir ventana toplevel para editar usuario y contraseña
        edit_win = tk.Toplevel(self)
        edit_win.title("Editar Usuario")
        edit_win.geometry("540x400+500+200")  # Tamaño más grande y cómodo
        edit_win.config(bg="#FFFFFF")
        edit_win.transient(self)
        edit_win.grab_set()

        # Frame principal para los campos
        frame = tk.Frame(edit_win, bg="#FFFFFF", bd=2, relief="groove")
        frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        tk.Label(frame, text="Usuario:", font=("Helvetica", 16, "bold"), bg="#FFFFFF", fg="#333").pack(pady=(10, 5))
        entry_usuario = ttk.Entry(frame, font=("Helvetica", 15))
        entry_usuario.pack(pady=5, fill=tk.X, padx=10)
        entry_usuario.insert(0, valores[0])

        tk.Label(frame, text="Nueva Contraseña:", font=("Helvetica", 16, "bold"), bg="#FFFFFF", fg="#333").pack(pady=(15, 5))
        entry_contrasena = ttk.Entry(frame, font=("Helvetica", 15), show="*")
        entry_contrasena.pack(pady=5, fill=tk.X, padx=10)

        tk.Label(frame, text="Confirmar Contraseña:", font=("Helvetica", 16, "bold"), bg="#FFFFFF", fg="#333").pack(pady=(15, 5))
        entry_confirmar = ttk.Entry(frame, font=("Helvetica", 15), show="*")
        entry_confirmar.pack(pady=5, fill=tk.X, padx=10)

        def guardar_edicion():
            nuevo_usuario = entry_usuario.get().strip()
            nueva_contrasena = entry_contrasena.get().strip()
            confirmar = entry_confirmar.get().strip()
            if not nuevo_usuario:
                messagebox.showwarning("Campos requeridos", "El usuario no puede estar vacío.", parent=edit_win)
                return
            if nueva_contrasena:
                if nueva_contrasena != confirmar:
                    messagebox.showwarning("Contraseña", "Las contraseñas no coinciden.", parent=edit_win)
                    return
                if len(nueva_contrasena) < 6:
                    messagebox.showwarning("Contraseña", "La contraseña debe tener al menos 6 caracteres.", parent=edit_win)
                    return
            try:
                with database.get_connection() as conn:
                    cursor = conn.cursor()
                    if nueva_contrasena:
                        contrasena_hash = hashlib.sha256(nueva_contrasena.encode()).hexdigest()
                        cursor.execute(
                            "UPDATE usuarios SET usuario = ?, contrasena = ? WHERE usuario = ?",
                            (nuevo_usuario, contrasena_hash, valores[0])
                        )
                    else:
                        cursor.execute(
                            "UPDATE usuarios SET usuario = ? WHERE usuario = ?",
                            (nuevo_usuario, valores[0])
                        )
                    conn.commit()
                self.cargar_usuarios()
                messagebox.showinfo("Éxito", "Usuario editado correctamente.", parent=edit_win)
                edit_win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo editar el usuario: {e}", parent=edit_win)

        def cancelar_edicion():
            edit_win.destroy()

        btn_frame = tk.Frame(frame, bg="#FFFFFF")
        btn_frame.pack(pady=28)

        btn_confirmar = tk.Button(
            btn_frame, text="Confirmar", bg="#2196F3", fg="#fff", font=("Helvetica", 14, "bold"),
            command=guardar_edicion, relief="flat", cursor="hand2", width=14
        )
        btn_confirmar.pack(side=tk.LEFT, padx=12)

        btn_cancelar = tk.Button(
            btn_frame, text="Cancelar", bg="#F44336", fg="#fff", font=("Helvetica", 14, "bold"),
            command=cancelar_edicion, relief="flat", cursor="hand2", width=14
        )
        btn_cancelar.pack(side=tk.LEFT, padx=12)

    def actualizar_usuario(self):
        seleccionado = self.tabla.selection()
        if not seleccionado:
            messagebox.showwarning("Seleccione", "Seleccione un usuario para actualizar.", parent=self)
            return
        item = seleccionado[0]
        valores = self.tabla.item(item, "values")
        usuario = valores[0]

        # Generar nuevas fechas y serial seguro
        fecha_inicio = datetime.datetime.now().strftime("%Y-%m-%d")
        fecha_fin = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        serial = str(uuid.uuid4())  # Serial seguro y único

        try:
            with database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE usuarios SET fecha_inicio = ?, fecha_fin = ?, serial = ? WHERE usuario = ?",
                    (fecha_inicio, fecha_fin, serial, usuario)
                )
                conn.commit()
            self.cargar_usuarios()
            messagebox.showinfo("Éxito", "Suscripción actualizada correctamente.", parent=self)
            self.entry_usuario.delete(0, tk.END)
            self.entry_contrasena.delete(0, tk.END)
            self.entry_confirmar.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar la suscripción: {e}", parent=self)

    def eliminar_usuario(self):
        seleccionado = self.tabla.selection()
        if not seleccionado:
            messagebox.showwarning("Seleccione", "Seleccione un usuario para eliminar.", parent=self)
            return
        item = seleccionado[0]
        valores = self.tabla.item(item, "values")
        usuario = valores[0]
        if not messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar el usuario '{usuario}'?", parent=self):
            return
        try:
            with database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM usuarios WHERE usuario = ?", (usuario,))
                conn.commit()
            self.cargar_usuarios()
            messagebox.showinfo("Éxito", "Usuario eliminado correctamente.", parent=self)
            self.entry_usuario.delete(0, tk.END)
            self.entry_contrasena.delete(0, tk.END)
            self.entry_confirmar.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el usuario: {e}", parent=self)

    def cargar_usuarios(self):
        self.tabla.delete(*self.tabla.get_children())
        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT usuario, '********', fecha_inicio, fecha_fin, serial FROM usuarios WHERE usuario != ? ORDER BY id ASC",
                ("innobertdev",)
            )
            usuarios = cursor.fetchall()
        for usuario in usuarios:
            self.tabla.insert("", tk.END, values=usuario)
