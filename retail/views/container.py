"""
container.py

Vista principal del sistema de gestión de licorería.
Contiene el contenedor principal que organiza y muestra las diferentes secciones del software:
Ventas, Clientes, Inventario y Deudas. Proporciona un menú superior para navegar entre ellas.

Autor: [Innobert]
"""

import tkinter as tk
import os
from PIL import Image, ImageTk
from retail.views.ventas import Ventas
from retail.views.clientes import Clientes
from retail.views.inventario import Inventario
from retail.views.deudas import Deudas
from retail.core.config import rutas

VENTANA_ANCHO = 1100
VENTANA_ALTO = 650
MENU_ALTO = 40


class Container(tk.Frame):
    """
    Contenedor principal de la aplicación.
    Gestiona la visualización de las diferentes secciones mediante un menú superior.
    """

    def __init__(self, padre, controlador):
        super().__init__(padre, width=VENTANA_ANCHO, height=VENTANA_ALTO, bg="#E6D9E3")
        self.controlador = controlador
        self.frames = {}
        self.menu_buttons = {}
        self.seccion_activa = "Ventas"

        # Ruta absoluta a la carpeta img en la raíz del proyecto
        RUTA_IMG = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "img"))

        # Cargar imágenes y mantener referencias
        self.iconos = {
            "Ventas": ImageTk.PhotoImage(
                Image.open(os.path.join(RUTA_IMG, "ventas.png")).resize((26, 26))
            ),
            "Clientes": ImageTk.PhotoImage(
                Image.open(os.path.join(RUTA_IMG, "clientes.png")).resize((26, 26))
            ),
            "Inventario": ImageTk.PhotoImage(
                Image.open(os.path.join(RUTA_IMG, "inventario.png")).resize((26, 26))
            ),
            "Deudas": ImageTk.PhotoImage(
                Image.open(os.path.join(RUTA_IMG, "deuda.png")).resize((26, 26))
            ),
        }

        self.crear_frames()
        self.crear_menu()

    def crear_frames(self):
        """
        Crea y configura los frames de cada sección (Ventas, Clientes, Inventario, Deudas).
        Los frames se apilan y se muestran según la selección del menú.
        """
        ventanas = {
            Ventas: "Ventas",
            Clientes: "Clientes",
            Inventario: "Inventario",
            Deudas: "Deudas",
        }

        for clase_ventana, nombre in ventanas.items():
            frame = clase_ventana(self, self.controlador)
            self.frames[clase_ventana] = frame
            # Guarda referencia directa a la vista Ventas
            if clase_ventana is Ventas:
                self.ventas_view = frame
            # Cada frame ocupa todo el espacio disponible debajo del menú
            frame.place(
                x=0, y=MENU_ALTO, width=VENTANA_ANCHO, height=VENTANA_ALTO - MENU_ALTO
            )

        # Mostrar la ventana por defecto
        self.frames[Ventas].tkraise()

    def crear_menu(self):
        """
        Crea el menú superior con botones para cambiar entre las diferentes secciones.
        Los botones están alineados horizontalmente y cada uno muestra su sección correspondiente.
        """
        frame_menu = tk.Frame(self, height=MENU_ALTO, bg="#E6D9E3")
        frame_menu.place(x=0, y=0, width=VENTANA_ANCHO, height=MENU_ALTO)

        # Definición de secciones y colores asociados
        secciones = [
            ("Ventas", Ventas, "#2196F3"),
            ("Clientes", Clientes, "#FF9800"),
            ("Inventario", Inventario, "#4CAF50"),
            ("Deudas", Deudas, "#F44336"),
        ]
        ancho_boton = VENTANA_ANCHO // len(secciones)

        for idx, (nombre, clase, color) in enumerate(secciones):
            btn = tk.Button(
                frame_menu,
                text=nombre,
                image=self.iconos[nombre],
                compound="left",
                font=("Calibri", 13, "bold"),
                bg=color,
                fg="#fff" if nombre == self.seccion_activa else "#222",
                bd=0,
                relief="flat",
                activebackground=color,
                activeforeground="#fff",
                cursor="hand2",
                highlightthickness=0,
                command=lambda c=clase, n=nombre: self.cambiar_seccion(c, n),
            )
            btn.place(x=idx * ancho_boton, y=0, width=ancho_boton, height=MENU_ALTO)
            self.menu_buttons[nombre] = btn

        # Línea divisoria bajo el menú
        tk.Frame(self, bg="#BDBDBD", height=2).place(x=0, y=MENU_ALTO, width=VENTANA_ANCHO)

        # Inicializa el efecto visual
        self.actualizar_menu_visual()

    def cambiar_seccion(self, clase_ventana, nombre):
        self.seccion_activa = nombre
        self.show_frames(clase_ventana)
        self.actualizar_menu_visual()

    def actualizar_menu_visual(self):
        # Efecto de selección profesional: fondo, texto y subrayado
        for nombre, btn in self.menu_buttons.items():
            if nombre == self.seccion_activa:
                btn.config(
                    bg="#212121",  # Fondo oscuro para el activo
                    fg="#FFD600",  # Amarillo para el texto activo
                    relief="flat",
                    bd=0,
                )
                # Subrayado visual (línea inferior)
                btn.place_configure(rely=0, height=MENU_ALTO - 2)
                if not hasattr(btn, "underline"):
                    underline = tk.Frame(btn.master, bg="#FFD600", height=4)
                    underline.place(x=btn.winfo_x(), y=MENU_ALTO-4, width=btn.winfo_width())
                    btn.underline = underline
                else:
                    btn.underline.place(x=btn.winfo_x(), y=MENU_ALTO-4, width=btn.winfo_width())
            else:
                color = {
                    "Ventas": "#2196F3",
                    "Clientes": "#FF9800",
                    "Inventario": "#4CAF50",
                    "Deudas": "#F44336",
                }[nombre]
                btn.config(
                    bg=color,
                    fg="#fff",
                    relief="flat",
                    bd=0,
                )
                if hasattr(btn, "underline"):
                    btn.underline.place_forget()

    def show_frames(self, clase_ventana):
        """Muestra el frame correspondiente a la sección seleccionada."""
        # Desactivar bindings en todos los frames antes de mostrar el nuevo
        for frame in self.frames.values():
            if hasattr(frame, "_desactivar_bindings"):
                frame._desactivar_bindings()
        # Activar bindings solo en el frame visible
        frame = self.frames[clase_ventana]
        if hasattr(frame, "_activar_bindings"):
            frame._activar_bindings()
        frame.tkraise()
        self.actualizar_menu_visual()


# No cambies nada aquí, deja el archivo como estaba antes de los cambios de bindings.
