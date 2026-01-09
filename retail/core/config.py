import json
import os
import sys
import shutil  # <-- Añadido para copiar carpetas
from typing import Optional

APPDATA_PATH = os.path.join(os.environ["APPDATA"], "InnobertRetail")
FOTOS_PATH = os.path.join(APPDATA_PATH, "fotos")
LOGO_PATH = os.path.join(APPDATA_PATH, "Logo")


def copiar_fotos_default():
    """
    Copia la carpeta 'fotos' (y su contenido) desde la raíz del proyecto a APPDATA_PATH/fotos si no existe.
    """
    # Ruta absoluta a la carpeta 'fotos' en la raíz del proyecto
    ruta_proyecto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    carpeta_fotos_origen = os.path.join(ruta_proyecto, "fotos")
    if os.path.exists(carpeta_fotos_origen):
        if not os.path.exists(FOTOS_PATH):
            try:
                shutil.copytree(carpeta_fotos_origen, FOTOS_PATH)
            except Exception as e:
                print(f"Error al copiar la carpeta de fotos por defecto: {e}")
        else:
            # Si la carpeta existe pero falta default.png, solo copia ese archivo
            default_src = os.path.join(carpeta_fotos_origen, "default.png")
            default_dst = os.path.join(FOTOS_PATH, "default.png")
            if os.path.exists(default_src) and not os.path.exists(default_dst):
                try:
                    shutil.copy2(default_src, default_dst)
                except Exception as e:
                    print(f"Error al copiar default.png: {e}")


def copiar_logo_default():
    """
    Copia la imagen 'logo.png' desde la carpeta img del proyecto a APPDATA_PATH/Logo si no existe.
    """
    ruta_proyecto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    logo_src = os.path.join(ruta_proyecto, "img", "logo.png")  # <-- Cambiado aquí
    logo_dst = os.path.join(LOGO_PATH, "logo.png")
    if os.path.exists(logo_src):
        if not os.path.exists(LOGO_PATH):
            os.makedirs(LOGO_PATH, exist_ok=True)
        if not os.path.exists(logo_dst):
            try:
                shutil.copy2(logo_src, logo_dst)
            except Exception as e:
                print(f"Error al copiar logo.png por defecto: {e}")


def asegurar_directorios():
    os.makedirs(APPDATA_PATH, exist_ok=True)
    os.makedirs(FOTOS_PATH, exist_ok=True)
    os.makedirs(LOGO_PATH, exist_ok=True)
    copiar_logo_default()  # <-- Asegura que la carpeta Logo y login.png existan


def rutas(rel_path):
    return os.path.join(APPDATA_PATH, rel_path)


def obtener_ruta_base_datos():
    return os.path.join(APPDATA_PATH, "licoreria.db")


def obtener_ruta_config():
    return os.path.join(APPDATA_PATH, "config.json")


def obtener_ruta_img(nombre_img=""):
    if nombre_img:
        return os.path.join(FOTOS_PATH, nombre_img)
    return FOTOS_PATH


def obtener_ruta_fotos(nombre_foto=""):
    if nombre_foto:
        return os.path.join(FOTOS_PATH, nombre_foto)
    return FOTOS_PATH


def obtener_ruta_icon(nombre_icon=""):
    if nombre_icon:
        return os.path.join(APPDATA_PATH, nombre_icon)
    return APPDATA_PATH


def obtener_ruta_logo(nombre_logo=""):
    """
    Devuelve la ruta absoluta a la carpeta Logo o a una imagen específica dentro de Logo.
    """
    if nombre_logo:
        return os.path.join(LOGO_PATH, nombre_logo)
    return LOGO_PATH


def resource_path(relative_path: str) -> str:
    """
    Devuelve la ruta absoluta para `relative_path` funcionando tanto en modo desarrollo
    como cuando la aplicación está empacada con PyInstaller.
    """
    if getattr(sys, "frozen", False):
        # PyInstaller crea un atributo temporal _MEIPASS con la ruta
        base_path = sys._MEIPASS
    else:
        # Ruta del proyecto en desarrollo
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(base_path, relative_path)


def eliminar_base_datos():
    db_path = obtener_ruta_base_datos()
    if os.path.exists(db_path):
        os.remove(db_path)


def eliminar_datos_completos():
    """
    Elimina completamente la carpeta de datos del programa (APPDATA_PATH) incluyendo
    base de datos, fotos, logo y archivos de configuración.

    Retorna True si se eliminaron datos, False si no existía la carpeta o hubo error.
    """
    if os.path.exists(APPDATA_PATH):
        try:
            shutil.rmtree(APPDATA_PATH)
            return True
        except Exception as e:
            print(f"Error al eliminar la carpeta de datos: {e}")
            return False
    return False


def guardar_usuario(usuario, contrasena, recordar):
    with open(obtener_ruta_config(), "w") as f:
        json.dump(
            {"usuario": usuario, "contrasena": contrasena, "recordar": recordar}, f
        )


def cargar_usuario():
    try:
        with open(obtener_ruta_config(), "r") as f:
            config = json.load(f)
            recordar = config.get("recordar", False)
            if recordar:
                return config.get("usuario", ""), config.get("contrasena", ""), recordar
            else:
                return "", "", recordar
    except FileNotFoundError:
        return "", "", False
