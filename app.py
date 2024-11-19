from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename

# Configuración base
basedir = os.path.abspath(os.path.dirname(__file__))

# Configuración de carpetas para archivos
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
PDF_FOLDER = os.path.join(UPLOAD_FOLDER, 'pdfs')
COVERS_FOLDER = os.path.join(UPLOAD_FOLDER, 'covers')

ALLOWED_EXTENSIONS = {
    'pdf': {'pdf'},
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'}
}

# Crear directorios necesarios
for folder in [PDF_FOLDER, COVERS_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

app = Flask(__name__)

# Configuración de la aplicación
app.config.update(
    SECRET_KEY='tu_clave_secreta_muy_segura',
    SQLALCHEMY_DATABASE_URI=f'sqlite:///{os.path.join(basedir, "biblioteca.db")}',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB max-limit
)

db = SQLAlchemy(app)

class Libros(db.Model):
    __tablename__ = 'libros'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    autor = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(13))
    año_publicacion = db.Column(db.Integer)
    editorial = db.Column(db.String(200))
    pdf_filename = db.Column(db.String(255))
    cover_filename = db.Column(db.String(255))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    descripcion = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'autor': self.autor,
            'isbn': self.isbn,
            'año_publicacion': self.año_publicacion,
            'editorial': self.editorial,
            'pdf_filename': self.pdf_filename,
            'cover_filename': self.cover_filename,
            'fecha_registro': self.fecha_registro.strftime('%Y-%m-%d %H:%M:%S'),
            'descripcion': self.descripcion
        }

def allowed_file(filename, type_):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS[type_]

@app.route('/')
def index():
    libros = Libros.query.order_by(Libros.fecha_registro.desc()).all()
    return render_template('index.html', libros=libros)

@app.route('/libro', methods=['POST'])
def agregar_libro():
    try:
        if 'pdf_file' not in request.files:
            return jsonify({'error': 'No se seleccionó ningún archivo PDF'}), 400
            
        pdf_file = request.files['pdf_file']
        if pdf_file.filename == '':
            return jsonify({'error': 'No se seleccionó ningún archivo PDF'}), 400

        # Procesar imagen de portada
        cover_filename = None
        if 'cover_file' in request.files:
            cover_file = request.files['cover_file']
            if cover_file.filename != '' and allowed_file(cover_file.filename, 'image'):
                cover_filename = secure_filename(f"cover_{datetime.now().timestamp()}_{cover_file.filename}")
                cover_file.save(os.path.join(COVERS_FOLDER, cover_filename))

        # Procesar PDF
        if pdf_file and allowed_file(pdf_file.filename, 'pdf'):
            pdf_filename = secure_filename(f"pdf_{datetime.now().timestamp()}_{pdf_file.filename}")
            pdf_file.save(os.path.join(PDF_FOLDER, pdf_filename))
            
            nuevo_libro = Libros(
                titulo=request.form['titulo'],
                autor=request.form['autor'],
                isbn=request.form.get('isbn', ''),
                año_publicacion=request.form.get('año_publicacion', ''),
                editorial=request.form.get('editorial', ''),
                pdf_filename=pdf_filename,
                cover_filename=cover_filename,
                descripcion=request.form.get('descripcion', '')
            )
            
            db.session.add(nuevo_libro)
            db.session.commit()
            
            return jsonify({
                'message': 'Libro agregado exitosamente',
                'libro': nuevo_libro.to_dict()
            })
        else:
            return jsonify({'error': 'Formato de archivo PDF no permitido'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/libro/<int:id>', methods=['GET'])
def obtener_libro(id):
    try:
        libro = Libros.query.get_or_404(id)
        return jsonify(libro.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/libro/<int:id>', methods=['PUT'])
def actualizar_libro(id):
    try:
        libro = Libros.query.get_or_404(id)
        data = request.get_json()

        # Actualizar campos básicos
        campos_actualizables = ['titulo', 'autor', 'isbn', 'año_publicacion', 'editorial', 'descripcion']
        for campo in campos_actualizables:
            if campo in data:
                setattr(libro, campo, data[campo])

        db.session.commit()
        return jsonify({
            'message': 'Libro actualizado exitosamente',
            'libro': libro.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/libro/<int:id>', methods=['DELETE'])
def eliminar_libro(id):
    try:
        libro = Libros.query.get_or_404(id)
        
        # Eliminar archivos asociados
        if libro.pdf_filename:
            pdf_path = os.path.join(PDF_FOLDER, libro.pdf_filename)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                
        if libro.cover_filename:
            cover_path = os.path.join(COVERS_FOLDER, libro.cover_filename)
            if os.path.exists(cover_path):
                os.remove(cover_path)
        
        db.session.delete(libro)
        db.session.commit()
        
        return jsonify({'message': 'Libro eliminado exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/leer/<int:id>')
def leer_pdf(id):
    try:
        libro = Libros.query.get_or_404(id)
        return render_template('pdf_viewer.html', libro=libro)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/pdf/<int:id>')
def obtener_pdf(id):
    try:
        libro = Libros.query.get_or_404(id)
        if not libro.pdf_filename:
            return jsonify({'error': 'No hay PDF disponible para este libro'}), 404
            
        pdf_path = os.path.join(PDF_FOLDER, libro.pdf_filename)
        if not os.path.exists(pdf_path):
            return jsonify({'error': 'El archivo PDF no se encuentra en el servidor'}), 404
            
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=f"{libro.titulo}.pdf"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cover/<filename>')
def obtener_portada(filename):
    try:
        return send_file(
            os.path.join(COVERS_FOLDER, filename),
            mimetype='image/jpeg'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/buscar')
def buscar_libros():
    try:
        termino = request.args.get('q', '').lower()
        if not termino:
            return jsonify([])

        libros = Libros.query.filter(
            db.or_(
                Libros.titulo.ilike(f'%{termino}%'),
                Libros.autor.ilike(f'%{termino}%'),
                Libros.isbn.ilike(f'%{termino}%'),
                Libros.editorial.ilike(f'%{termino}%'),
                Libros.descripcion.ilike(f'%{termino}%')
            )
        ).all()
        
        return jsonify([libro.to_dict() for libro in libros])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    if request.accepts('json'):
        return jsonify({'error': 'Recurso no encontrado'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if request.accepts('json'):
        return jsonify({'error': 'Error interno del servidor'}), 500
    return render_template('500.html'), 500

def init_db():
    with app.app_context():
        db.create_all()
        if not Libros.query.first():
            print("Base de datos inicializada. Lista para agregar libros.")
        else:
            print("La base de datos ya contiene registros.")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)