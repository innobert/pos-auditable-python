import multiprocessing
from retail.core.manager import Manager
from retail.core.database import create_tables
from retail.core.config import asegurar_directorios, copiar_fotos_default  # <-- Agrega esta importación

if __name__ == "__main__":
    # Necesario en Windows para aplicaciones "frozen" que puedan crear procesos
    multiprocessing.freeze_support()
    asegurar_directorios()
    copiar_fotos_default()  # <-- Añade esta línea para copiar default.png si no existe
    create_tables()
    app = Manager()
    app.mainloop()
