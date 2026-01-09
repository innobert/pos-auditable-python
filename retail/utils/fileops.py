import os
import sys
import subprocess
import webbrowser


def open_file_silently(path):
    """Abrir un archivo con la aplicación asociada de forma silenciosa.

    En Windows usa os.startfile (no abre consola). En macOS/Linux usa
    los comandos 'open'/'xdg-open' con stdout/stderr redirigidos a DEVNULL.
    Como fallback intenta webbrowser.open_new.
    """
    try:
        if os.name == "nt":
            os.startfile(path)
        else:
            if sys.platform == "darwin":
                cmd = ["open", path]
            else:
                cmd = ["xdg-open", path]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        try:
            webbrowser.open_new(path)
        except Exception:
            pass
