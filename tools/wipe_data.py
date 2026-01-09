"""
Herramienta para borrar datos del entorno local de Innobert Retail durante pruebas.
Uso:
    python tools/wipe_data.py --help

Opciones:
    --db       : eliminar solo la base de datos
    --all      : eliminar toda la carpeta APPDATA del programa (fotos, logo, config, db)
    --yes      : confirmar sin preguntar
"""
import argparse
import sys
import os

# Añadir la raíz del proyecto al sys.path para permitir `import retail`
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import shutil
import stat
import ctypes

# Prefer using helpers from retail.core.config when available
try:
    from retail.core.config import (
        eliminar_base_datos,
        eliminar_datos_completos,
        obtener_ruta_base_datos,
        APPDATA_PATH,
    )
    HAS_CONFIG_HELPERS = True
except Exception:
    # Fallbacks si el módulo no está disponible por alguna razón
    HAS_CONFIG_HELPERS = False


def _clear_readonly_and_hidden(path):
    """Clear read-only and hidden attributes on Windows or chmod on POSIX so files can be removed."""
    try:
        if os.name == "nt":
            # Use Windows API to set FILE_ATTRIBUTE_NORMAL (removes readonly/hidden/system)
            FILE_ATTRIBUTE_NORMAL = 0x80
            SetFileAttributesW = ctypes.windll.kernel32.SetFileAttributesW
            try:
                SetFileAttributesW(ctypes.c_wchar_p(path), FILE_ATTRIBUTE_NORMAL)
            except Exception:
                # fallback to os.chmod for files
                if os.path.exists(path):
                    try:
                        os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
                    except Exception:
                        pass
        else:
            # POSIX: ensure writable
            if os.path.exists(path):
                try:
                    os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
                except Exception:
                    pass
    except Exception:
        # ignore any error here; removal will try and fail with clearer message
        pass


def _on_rm_error(func, path, exc_info):
    """Handler for shutil.rmtree onerror: try to clear readonly/hidden then retry."""
    try:
        _clear_readonly_and_hidden(path)
        # retry the operation that failed
        func(path)
    except Exception:
        # re-raise the original exception to be visible to caller
        raise


def _fallback_eliminar_datos_completos():
    """Fallback implementation to remove APPDATA_PATH if config helper not available.

    First clear attributes recursively, then remove folder with rmtree(onerror=_on_rm_error).
    """
    # Try to determine APPDATA path relative to env var or common locations
    appdata = os.environ.get("APPDATA")
    if not appdata:
        # Try local user home
        appdata = os.path.join(os.path.expanduser("~"), ".innobert_retail")
    app_path = os.path.join(appdata, "InnobertRetail")
    if os.path.exists(app_path):
        try:
            # Clear attributes for all files/dirs first (bottom-up)
            for root, dirs, files in os.walk(app_path, topdown=False):
                for name in files:
                    p = os.path.join(root, name)
                    _clear_readonly_and_hidden(p)
                for name in dirs:
                    p = os.path.join(root, name)
                    _clear_readonly_and_hidden(p)
            # Finally remove tree with robust onerror handler
            shutil.rmtree(app_path, onerror=_on_rm_error)
            return True
        except Exception as e:
            print(f"Error al eliminar la carpeta de datos (fallback): {e}")
            return False
    return False


def _fallback_eliminar_base_datos():
    # Attempt to remove a database file in the default location
    appdata = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".innobert_retail")
    db_path = os.path.join(appdata, "InnobertRetail", "licoreria.db")
    if os.path.exists(db_path):
        try:
            # clear attributes first
            _clear_readonly_and_hidden(db_path)
            os.remove(db_path)
            return True
        except Exception as e:
            try:
                _clear_readonly_and_hidden(db_path)
                os.remove(db_path)
                return True
            except Exception as e2:
                print(f"Error al eliminar la base de datos (fallback): {e2}")
                return False
    return False


def main():
    parser = argparse.ArgumentParser(description="Herramienta para limpiar datos locales de Innobert Retail")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--db", action="store_true", help="Eliminar solo la base de datos")
    group.add_argument("--all", action="store_true", help="Eliminar toda la carpeta de datos (APPDATA)")
    parser.add_argument("--yes", action="store_true", help="Confirmar sin preguntar")
    args = parser.parse_args()

    if args.db:
        # Use helper if available
        if HAS_CONFIG_HELPERS:
            try:
                db_path = obtener_ruta_base_datos()
            except Exception:
                db_path = "<ruta desconocida>"
        else:
            # best-effort path for prompt
            appdata = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".innobert_retail")
            db_path = os.path.join(appdata, "InnobertRetail", "licoreria.db")

        if not args.yes:
            confirm = input(f"Eliminar la base de datos en {db_path}? [y/N]: ")
            if confirm.lower() != "y":
                print("Cancelado")
                sys.exit(0)

        try:
            if HAS_CONFIG_HELPERS:
                eliminar_base_datos()
            else:
                ok = _fallback_eliminar_base_datos()
                if not ok:
                    raise RuntimeError("No se pudo eliminar la base de datos (fallback).")
            print("Base de datos eliminada (si existía).")
        except Exception as e:
            print(f"Error al eliminar la base de datos: {e}")
            print("Si el error es 'Acceso denegado', intente ejecutar esta terminal como Administrador.")
            sys.exit(2)
    elif args.all:
        if not args.yes:
            confirm = input("Eliminar toda la carpeta de datos del programa (esto borrará fotos, config y DB). Confirmar [y/N]: ")
            if confirm.lower() != "y":
                print("Cancelado")
                sys.exit(0)

        try:
            if HAS_CONFIG_HELPERS:
                ok = eliminar_datos_completos()
            else:
                ok = _fallback_eliminar_datos_completos()
            if ok:
                print("Todos los datos eliminados.")
            else:
                print("No se encontró la carpeta de datos o ocurrió un error.")
        except Exception as e:
            print(f"Error al eliminar datos: {e}")
            print("Si el error es 'Acceso denegado', intente ejecutar esta terminal como Administrador.")
            sys.exit(2)


if __name__ == "__main__":
    main()
