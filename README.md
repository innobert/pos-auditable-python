# 🧾 POS Auditable en Python

Sistema POS (Point of Sale) desarrollado en **Python** para pequeños y medianos negocios, diseñado con criterios de **auditoría, trazabilidad y control contable real**.

Este proyecto nace de una necesidad operativa real y se ha construido de forma incremental, aplicando buenas prácticas de ingeniería de software y diseño de bases de datos.

---

## 🚀 Características principales

- ✅ Ventas al contado y a crédito
- ✅ Gestión de clientes
- ✅ Control de inventario en tiempo real
- ✅ Gestión de deudas y abonos
- ✅ Facturación en PDF
- ✅ Historial completo de operaciones
- ✅ Diseño orientado a auditoría (no se pierden datos)

---

## 🧠 Enfoque de ingeniería

Este proyecto no es un demo académico. Está diseñado bajo principios utilizados en sistemas comerciales reales:

- **IDs inmutables:** los registros no se reordenan ni reutilizan.
- **Separación entre ID técnico y número visible:** preparado para facturación formal.
- **Ventas inmutables:** una venta no se elimina, solo se anula.
- **Historial como fuente de verdad:** toda acción queda registrada.
- **Separación de responsabilidades:** UI, lógica de negocio y base de datos desacopladas.
- **PDF derivado de la base de datos:** nunca de la interfaz gráfica.

---

## 🗄️ Arquitectura general

pos-auditable-python/
│
├── retail/ # Lógica de negocio y base de datos
├── img/ # Recursos gráficos
├── tools/ # Utilidades y herramientas de apoyo
├── index.py # Punto de entrada de la aplicación
├── README.md
└── .gitignore


---

## 🛠️ Tecnologías utilizadas

- **Lenguaje:** Python 3
- **Interfaz gráfica:** Tkinter
- **Base de datos:** SQLite
- **PDF:** ReportLab / PIL
- **Control de versiones:** Git y GitHub

---

## 📄 Facturación PDF

El sistema genera documentos PDF a partir de la información almacenada en la base de datos, garantizando:

- Consistencia con los registros reales
- Trazabilidad
- Posibilidad de regenerar documentos sin alterar la información

---

## 🧪 Estado del proyecto

📌 **Proyecto en evolución**

Actualmente se encuentra en desarrollo activo, enfocado en:
- Mejoras de arquitectura
- Refactorización para mayor mantenibilidad
- Preparación para futuras extensiones (API, web, multiusuario)

---

## ▶️ Cómo ejecutar el proyecto

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/innobert/pos-auditable-python.git
2. Crear y activar un entorno virtual (opcional pero recomendado):
   python -m venv venv
  source venv/bin/activate  # Linux / Mac
  venv\Scripts\activate     # Windows
3. Instalar dependencias (si aplica).
4. Ejecutar:
   python index.py

👤 Autor

Roberto Vásquez
Ingeniero de Software
📍 Colombia

Este proyecto forma parte de mi portafolio personal y refleja mi enfoque en el desarrollo de sistemas reales, mantenibles y auditables.

📌 Nota final

Este repositorio está pensado como una muestra de criterio técnico, diseño de sistemas y capacidad de aprendizaje continuo.
No pretende ser un producto final, sino una base sólida sobre la cual seguir construyendo.

