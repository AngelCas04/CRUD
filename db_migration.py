import sqlite3
import os
from datetime import datetime

def migrate_database():
    # Ruta de la base de datos
    db_path = 'biblioteca.db'
    
    # Verificar si existe la base de datos
    if not os.path.exists(db_path):
        print("No se encontró la base de datos.")
        return

    # Hacer backup de la base de datos original
    backup_path = f'biblioteca_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    with open(db_path, 'rb') as source:
        with open(backup_path, 'wb') as backup:
            backup.write(source.read())
    print(f"Backup creado: {backup_path}")

    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Verificar si ya existe la columna cover_filename
        cursor.execute("PRAGMA table_info(libros)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'cover_filename' not in columns:
            print("Iniciando migración...")
            
            # Crear tabla temporal con la nueva estructura
            cursor.execute('''
                CREATE TABLE libros_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    autor TEXT NOT NULL,
                    isbn TEXT,
                    año_publicacion INTEGER,
                    editorial TEXT,
                    pdf_filename TEXT,
                    cover_filename TEXT,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    descripcion TEXT
                )
            ''')

            # Copiar datos existentes
            cursor.execute('''
                INSERT INTO libros_new (
                    id, titulo, autor, isbn, año_publicacion,
                    editorial, pdf_filename, fecha_registro
                )
                SELECT 
                    id, titulo, autor, isbn, año_publicacion,
                    editorial, pdf_filename, fecha_registro
                FROM libros
            ''')

            # Eliminar tabla antigua
            cursor.execute('DROP TABLE libros')

            # Renombrar nueva tabla
            cursor.execute('ALTER TABLE libros_new RENAME TO libros')

            # Crear índices para mejorar el rendimiento
            cursor.execute('CREATE INDEX idx_titulo ON libros(titulo)')
            cursor.execute('CREATE INDEX idx_autor ON libros(autor)')
            cursor.execute('CREATE INDEX idx_isbn ON libros(isbn)')

            # Guardar cambios
            conn.commit()
            print("Migración completada exitosamente.")
            
            # Mostrar estructura actual de la tabla
            cursor.execute("PRAGMA table_info(libros)")
            print("\nEstructura actual de la tabla:")
            for column in cursor.fetchall():
                print(f"- {column[1]} ({column[2]})")

        else:
            print("La base de datos ya tiene la estructura actualizada.")

    except sqlite3.Error as e:
        print(f"Error durante la migración: {e}")
        print("Restaurando backup...")
        conn.close()
        
        # Restaurar backup si algo salió mal
        os.remove(db_path)
        os.rename(backup_path, db_path)
        print("Backup restaurado.")
        
    finally:
        conn.close()

def create_upload_folders():
    """Crear estructura de carpetas necesaria"""
    folders = [
        'static/uploads',
        'static/uploads/pdfs',
        'static/uploads/covers',
        'static/img'
    ]
    
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Carpeta creada: {folder}")

def setup_default_cover():
    """Crear imagen de portada por defecto si no existe"""
    default_cover_path = 'static/img/default-cover.png'
    if not os.path.exists(default_cover_path):
        # Crear una imagen por defecto simple
        from PIL import Image, ImageDraw
        
        # Crear imagen 3:4
        img = Image.new('RGB', (300, 400), color='#f3f4f6')
        draw = ImageDraw.Draw(img)
        
        # Dibujar icono de libro (rectángulo simple)
        draw.rectangle([100, 150, 200, 250], fill='#d1d5db')
        
        # Guardar imagen
        img.save(default_cover_path)
        print("Imagen de portada por defecto creada.")

if __name__ == "__main__":
    print("Iniciando proceso de actualización de la biblioteca...")
    
    # Crear estructura de carpetas
    create_upload_folders()
    
    # Configurar imagen por defecto
    try:
        from PIL import Image
        setup_default_cover()
    except ImportError:
        print("Pillow no está instalado. La imagen por defecto no se creará.")
        print("Instala Pillow con: pip install Pillow")
    
    # Migrar base de datos
    migrate_database()
    
    print("\nProceso completado.")