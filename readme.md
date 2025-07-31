# RepetiScan Music 🎵

**ENGLISH BELOW | INGLÉS ABAJO**

## 🇪🇸 Descripción (Español)

**RepetiScan Music** es una aplicación de escritorio hecha en Python para ayudarte a encontrar canciones repetidas o similares en tu biblioteca MP3 local. Permite comparar archivos según su título y agruparlos si son similares. Además, te da opciones para eliminar canciones (enviándolas a la papelera), exportar resultados a CSV y filtrar por artista.

### 🔧 Funcionalidades

- Buscar similitudes por:
  - Porcentaje de coincidencia de título
  - Coincidencia de palabras clave
- Excluir canciones de un artista específico
- Agrupar canciones similares en una sola fila
- Reproducir canciones directamente desde la app
- Eliminar canciones a la papelera (¡no se borran permanentemente!)
- Exportar los resultados a archivo `.csv`
- Interfaz gráfica (GUI) con `Tkinter`
- Soporte para clic derecho, selección múltiple, y scroll horizontal
- Soporte para nombres de archivos y metadatos ID3 (`title`, `artist`)

---

## 🇬🇧 Description (English)

**RepetiScan Music** is a desktop Python app designed to help you find duplicate or similar MP3 songs in your local music library. It compares files based on their titles and groups them when they are similar. You can delete songs (safely sent to recycle bin), export results to CSV, and filter by artist name.

### 🔧 Features

- Search for:
  - Title similarity by percentage
  - Keyword-based match
- Exclude songs by a specific artist
- Group similar songs in a single row
- Play songs with your default media player
- Delete songs (sent to recycle bin, not permanently erased!)
- Export results to `.csv` file
- User interface (GUI) using `Tkinter`
- Right-click support, multi-selection, and horizontal scrolling
- Supports file names and ID3 tags (`title`, `artist`)

---

## 💻 Requisitos / Requirements

- Python 3.10 o superior
- Librerías: `tkinter`, `mutagen`, `difflib`, `send2trash`, `csv`, `subprocess`, etc.

Instalar dependencias:
```bash
pip install mutagen send2trash
