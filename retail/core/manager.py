import tkinter as tk
from tkinter import ttk
from retail.views.login import Login
from retail.views.container import Container
import retail.core.database as database


class Manager(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Innobert Retail")
        self.config(bg="#E6D9E3")
        self.resizable(False, False)

        # Asegurar que la base de datos y tablas existan en el primer arranque.
        # Esto creará el usuario de prueba con 30 días desde la primera ejecución.
        try:
            database.create_tables()
        except Exception as e:
            # No detener la inicialización de la UI si ocurre un error en la BD;
            # mostrar en consola para diagnóstico.
            print(f"Warning: error al crear o asegurar la base de datos: {e}")

        # Configurar tema ttk global
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background="#E6D9E3")  # Fondo widgets ttk
        style.configure("TLabel", background="#E6D9E3")
        style.configure("TFrame", background="#E6D9E3")
        style.configure("TButton", background="#E6D9E3")

        # Diccionario para almacenar las vistas
        self.frames = {}

        # Crear las vistas
        self.frames["Login"] = Login(self, self)
        self.frames["Container"] = Container(self, self)

        # Mostrar la vista inicial (Container)
        self.show_frame("Login")

    def show_frame(self, frame_name):
        """Muestra el frame especificado y ajusta el tamaño si es necesario."""
        # Ocultar todas las vistas
        for frame in self.frames.values():
            frame.place_forget()  # Asegúrate de ocultar todas las vistas

        # Mostrar la vista seleccionada
        frame = self.frames[frame_name]
        frame.place(x=0, y=0, relwidth=1, relheight=1)  # Mostrar la vista seleccionada

        # Ajustar el tamaño según la vista
        if frame_name == "Login":
            self.geometry("800x600+300+20")  # Tamaño para el Login
        else:
            self.geometry("1100x650+130+10")  # Tamaño para el Container

        # Ocultar todas las vistas
        for frame in self.frames.values():
            frame.place_forget()

        # Mostrar la vista seleccionada
        frame = self.frames[frame_name]
        frame.place(x=0, y=0, relwidth=1, relheight=1)
