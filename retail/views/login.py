import tkinter as tk
from tkinter import ttk, messagebox
from retail.core.config import (
    guardar_usuario,
    cargar_usuario,
)
import retail.core.database as database
import os
from PIL import Image, ImageTk
from retail.views.registro import VentanaRegistro  # Importa la ventana de registro


class Login(tk.Frame):
    def __init__(self, padre, controlador):
        super().__init__(padre)
        self.controlador = controlador
        self.pack(fill=tk.BOTH, expand=True)
        self.widgets()
        self.cargar_usuario()  # Cargar el usuario, la contraseña y el estado de la casilla al iniciar
        self.bind(
            "<Return>", lambda event: self.login()
        )  # Permitir iniciar sesión con Enter
        # Ajustar tamaño de ventana solo para login
        self.controlador.geometry("800x600+200+60")

    def widgets(self):
        # Frame principal para los campos de login
        frame2 = tk.Frame(
            self, bg="#FFFFFF", highlightthickness=1, highlightbackground="black"
        )
        frame2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Título del login
        titulo = tk.Label(
            frame2,
            text="INICIO DE SESIÓN",
            font=("Calibri", 20, "bold"),
            bg="#FFFFFF",
            fg="#333333",
        )
        titulo.pack(pady=5)

        # Campo para Usuario
        label_usuario = tk.Label(
            frame2, text="Usuario", font=("Calibri", 14), bg="#FFFFFF", fg="#333333"
        )
        label_usuario.pack(anchor="w", pady=5)
        self.entry_usuario = ttk.Entry(frame2, font=("Calibri", 14))
        self.entry_usuario.pack(fill=tk.X, pady=5)

        # Campo para Contraseña
        label_contrasena = tk.Label(
            frame2, text="Contraseña", font=("Calibri", 14), bg="#FFFFFF", fg="#333333"
        )
        label_contrasena.pack(anchor="w", pady=5)
        self.entry_contrasena = ttk.Entry(frame2, font=("Calibri", 14), show="*")
        self.entry_contrasena.pack(fill=tk.X, pady=5)

        # Checkbox para recordar datos
        self.recordar_var = tk.IntVar()
        self.checkbox_recordar = tk.Checkbutton(
            frame2,
            text="Recordar Datos",
            variable=self.recordar_var,
            bg="#FFFFFF",
            font=("Calibri", 12),
            fg="#333333",
            activebackground="#FFFFFF",
            activeforeground="#333333",
            highlightthickness=0,
        )
        self.checkbox_recordar.pack(anchor="w", pady=10)

        # Botón de login
        self.btn_login = tk.Button(
            frame2,
            text="Iniciar Sesión",
            command=self.login,
            font=("Calibri", 14, "bold"),
            bg="#4CAF50",
            fg="#FFFFFF",
            activebackground="#45A049",
            activeforeground="#FFFFFF",
            relief="flat",
            cursor="hand2",
        )
        self.btn_login.pack(pady=20, fill=tk.X)

        # Botón de registrar
        self.btn_registrar = tk.Button(
            frame2,
            text="Registrar",
            command=self.abrir_registro,
            font=("Calibri", 14, "bold"),
            bg="#2196F3",
            fg="#FFFFFF",
            activebackground="#1976D2",
            activeforeground="#FFFFFF",
            relief="flat",
            cursor="hand2",
        )
        self.btn_registrar.pack(pady=10, fill=tk.X)

        # Frame para mostrar la imagen del negocio
        frame_imagen = tk.Frame(
            self, bg="#ffffff", highlightthickness=1, highlightbackground="white"
        )
        frame_imagen.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=0)

        # Cargar la imagen del login usando rutas absolutas
        ruta_login = os.path.join(os.path.dirname(__file__), "..", "..", "img", "login.png")
        ruta_login = os.path.abspath(ruta_login)
        self.img_negocio = ImageTk.PhotoImage(Image.open(ruta_login))
        try:
            label_imagen = tk.Label(frame_imagen, image=self.img_negocio, bg="#FFFFFF")
            label_imagen.pack(expand=True)
        except Exception:
            tk.Label(
                frame_imagen, text="No se pudo cargar la imagen", bg="#FFFFFF", fg="red"
            ).pack()

        # Footer con tus datos e imágenes
        frame_footer = tk.Frame(frame_imagen, bg="#ffffff", highlightthickness=0)
        frame_footer.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        # Cargar imágenes para el footer
        ruta_software = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "img", "software.png"))
        ruta_wpp = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "img", "wpp.png"))
        ruta_instagram = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "img", "instagram.png"))
        ruta_gmail = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "img", "gmail.png"))
        try:
            img_software = ImageTk.PhotoImage(Image.open(ruta_software).resize((22, 22), Image.LANCZOS))
        except Exception:
            img_software = None
        try:
            img_wpp = ImageTk.PhotoImage(Image.open(ruta_wpp).resize((22, 22), Image.LANCZOS))
        except Exception:
            img_wpp = None
        try:
            img_instagram = ImageTk.PhotoImage(Image.open(ruta_instagram).resize((22, 22), Image.LANCZOS))
        except Exception:
            img_instagram = None
        try:
            img_gmail = ImageTk.PhotoImage(Image.open(ruta_gmail).resize((22, 22), Image.LANCZOS))
        except Exception:
            img_gmail = None

        # Nombre y software
        nombre_frame = tk.Frame(frame_footer, bg="#FFFFFF")
        nombre_frame.pack(anchor="center", pady=2)
        if img_software:
            tk.Label(nombre_frame, image=img_software, bg="#FFFFFF").pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(nombre_frame, text="Roberto Vásquez", font=("Calibri", 10, "bold"), bg="#FFFFFF", fg="#666666").pack(side=tk.LEFT)
        tk.Label(nombre_frame, text="Ingeniero de Software", font=("Calibri", 10), bg="#FFFFFF", fg="#666666").pack(side=tk.LEFT, padx=(5, 0))

        # WhatsApp
        wpp_frame = tk.Frame(frame_footer, bg="#FFFFFF")
        wpp_frame.pack(anchor="center", pady=2)
        if img_wpp:
            tk.Label(wpp_frame, image=img_wpp, bg="#FFFFFF").pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(wpp_frame, text="304 210 4313", font=("Calibri", 10, "bold"), bg="#FFFFFF", fg="#666666").pack(side=tk.LEFT)
        tk.Label(wpp_frame, text="WhatsApp", font=("Calibri", 10), bg="#FFFFFF", fg="#666666").pack(side=tk.LEFT, padx=(5, 0))

        # Instagram
        insta_frame = tk.Frame(frame_footer, bg="#FFFFFF")
        insta_frame.pack(anchor="center", pady=2)
        if img_instagram:
            tk.Label(insta_frame, image=img_instagram, bg="#FFFFFF").pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(insta_frame, text="innobertdev", font=("Calibri", 10, "bold"), bg="#FFFFFF", fg="#666666").pack(side=tk.LEFT)
        tk.Label(insta_frame, text="Instagram", font=("Calibri", 10), bg="#FFFFFF", fg="#666666").pack(side=tk.LEFT, padx=(5, 0))

        # Gmail
        gmail_frame = tk.Frame(frame_footer, bg="#FFFFFF")
        gmail_frame.pack(anchor="center", pady=2)
        if img_gmail:
            tk.Label(gmail_frame, image=img_gmail, bg="#FFFFFF").pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(gmail_frame, text="innobert07@gmail.com", font=("Calibri", 10, "bold"), bg="#FFFFFF", fg="#666666").pack(side=tk.LEFT)
        tk.Label(gmail_frame, text="Gmail", font=("Calibri", 10), bg="#FFFFFF", fg="#666666").pack(side=tk.LEFT, padx=(5, 0))

        # Marca
        tk.Label(
            frame_footer,
            text="®INNOBERTDEV",
            font=("Calibri", 10, "bold"),
            bg="#FFFFFF",
            fg="#666666",
        ).pack(anchor="center", pady=2)

        # Guardar referencias de imágenes para evitar que se eliminen
        self.img_software = img_software
        self.img_wpp = img_wpp
        self.img_instagram = img_instagram
        self.img_gmail = img_gmail

        # Cargar usuario y contraseña si están guardados
        self.cargar_usuario()

    def login(self):
        usuario = self.entry_usuario.get().strip()
        contrasena = self.entry_contrasena.get().strip()
        recordar = self.recordar_var.get()

        if not usuario or not contrasena:
            messagebox.showwarning(
                "Advertencia", "Por favor, ingrese el usuario y la contraseña."
            )
            return

        try:
            resultado = database.buscar_usuario(usuario, contrasena)
            if resultado:
                # Bloquear acceso para usuario y contraseña 'admin'
                if usuario.lower() == "admin":
                    messagebox.showerror("Error", "Acceso denegado para este usuario.")
                    return
                # Verificar suscripción y serial
                fecha_inicio = resultado[3]  # Fecha inicio
                fecha_fin = resultado[4]     # Fecha fin
                serial = resultado[5]        # Serial seguro y único
                import datetime
                hoy = datetime.datetime.now().date()
                fecha_fin_dt = datetime.datetime.strptime(fecha_fin, "%Y-%m-%d").date()
                if hoy > fecha_fin_dt:
                    messagebox.showerror(
                        "Suscripción vencida",
                        f"Su serial mensual ({serial}) ha vencido.\n"
                        f"Inicio: {fecha_inicio}\nFin: {fecha_fin}\n"
                        "Debe comunicarse con el desarrollador Roberto Vásquez. Teléfono: 304 210 4313 para que actualice su suscripción."
                    )
                    return
                messagebox.showinfo("Login exitoso", f"Bienvenido, {usuario}!\nSerial actual: {serial}")
                if recordar:
                    guardar_usuario(usuario, contrasena, True)
                else:
                    guardar_usuario("", "", False)
                self.controlador.geometry("1100x650+130+20")
                self.controlador.show_frame("Container")
            elif usuario == "innobertdev" and contrasena == "ingsoftware.99":
                messagebox.showinfo("Login exitoso", f"Bienvenido, {usuario}!")
                if recordar:
                    guardar_usuario(usuario, contrasena, True)
                else:
                    guardar_usuario("", "", False)
                self.controlador.geometry("1100x650+130+20")
                self.controlador.show_frame("Container")
            else:
                messagebox.showerror("Error", "Usuario o contraseña incorrectos.")
        except Exception as e:
            messagebox.showerror(
                "Error", f"Error al conectar con la base de datos: {e}"
            )

    def cargar_usuario(self):
        # Cargar el usuario, la contraseña y el estado de la casilla desde config.json
        usuario, contrasena, recordar = cargar_usuario()
        self.entry_usuario.delete(0, tk.END)  # Limpiar el campo antes de insertar
        self.entry_contrasena.delete(0, tk.END)  # Limpiar el campo antes de insertar
        if recordar:
            self.entry_usuario.insert(0, usuario)
            self.entry_contrasena.insert(0, contrasena)
            self.recordar_var.set(1)  # Marcar la casilla si estaba seleccionada
        else:
            self.recordar_var.set(0)  # Desmarcar la casilla si no estaba seleccionada

    def abrir_registro(self):
        usuario = self.entry_usuario.get().strip()
        contrasena = self.entry_contrasena.get().strip()
        if usuario == "innobertdev" and contrasena == "ingsoftware.99":
            VentanaRegistro(self)
        else:
            messagebox.showwarning(
                "Acceso restringido",
                "Solo el desarrollador del software puede acceder al registro de usuarios.",
            )
