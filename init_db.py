import os
from app import db, app

# Eliminar la base de datos existente si existe
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'biblioteca.db')
if os.path.exists(db_path):
    os.remove(db_path)
    print("Base de datos anterior eliminada.")

# Crear nueva base de datos con la estructura actualizada
with app.app_context():
    db.create_all()
    print("Nueva base de datos creada con éxito.")