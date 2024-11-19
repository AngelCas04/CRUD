// Variables globales
let searchTimeout;
const dropZone = document.getElementById('pdf-drop-zone');

// Configuración de Drag & Drop para PDF
if (dropZone) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    dropZone.addEventListener('drop', handleDrop, false);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    dropZone.classList.add('drag-over');
}

function unhighlight(e) {
    dropZone.classList.remove('drag-over');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files[0]) {
        if (files[0].type === 'application/pdf') {
            document.getElementById('pdf_file').files = files;
            updatePdfFilename(document.getElementById('pdf_file'));
        } else {
            Swal.fire('Error', 'Por favor, selecciona un archivo PDF', 'error');
        }
    }
}

// Previsualización de portada
function previewCover(input) {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        
        // Validar tipo de archivo
        if (!file.type.startsWith('image/')) {
            Swal.fire('Error', 'Por favor, selecciona un archivo de imagen', 'error');
            input.value = '';
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('cover-preview').src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
}

// Actualizar nombre del PDF seleccionado
function updatePdfFilename(input) {
    const filename = input.files[0]?.name || 'Ningún archivo seleccionado';
    document.getElementById('pdf-filename').textContent = filename;
}

// Mostrar/Ocultar modal
function toggleAddForm() {
    const modal = document.getElementById('form-modal');
    const formContainer = modal.querySelector('.modal-transition');
    
    if (modal.classList.contains('hidden')) {
        // Mostrar modal
        modal.classList.remove('hidden');
        setTimeout(() => {
            formContainer.classList.remove('translate-y-full');
        }, 10);
    } else {
        // Ocultar modal
        formContainer.classList.add('translate-y-full');
        setTimeout(() => {
            modal.classList.add('hidden');
            resetForm();
        }, 300);
    }
}

// Resetear formulario
function resetForm() {
    const form = document.getElementById('libro-form');
    form.reset();
    document.getElementById('libro-id').value = '';
    document.getElementById('form-title').textContent = 'Añadir Nuevo Libro';
    document.getElementById('cover-preview').src = '/static/img/default-cover.png';
    document.getElementById('pdf-filename').textContent = '';
}

// Editar libro
function editarLibro(id) {
    fetch(`/libro/${id}`, {
        method: 'GET',
        headers: {
            'Accept': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) throw new Error('Error al cargar el libro');
        return response.json();
    })
    .then(libro => {
        document.getElementById('libro-id').value = libro.id;
        document.getElementById('form-title').textContent = 'Editar Libro';
        
        // Llenar campos del formulario
        document.querySelector('input[name="titulo"]').value = libro.titulo;
        document.querySelector('input[name="autor"]').value = libro.autor;
        document.querySelector('input[name="isbn"]').value = libro.isbn || '';
        document.querySelector('input[name="año_publicacion"]').value = libro.año_publicacion || '';
        document.querySelector('input[name="editorial"]').value = libro.editorial || '';
        document.querySelector('textarea[name="descripcion"]').value = libro.descripcion || '';
        
        // Mostrar portada si existe
        if (libro.cover_filename) {
            document.getElementById('cover-preview').src = `/cover/${libro.cover_filename}`;
        }
        
        toggleAddForm();
    })
    .catch(error => {
        console.error('Error:', error);
        Swal.fire('Error', 'No se pudo cargar la información del libro', 'error');
    });
}

// Eliminar libro
function eliminarLibro(id) {
    Swal.fire({
        title: '¿Estás seguro?',
        text: "Esta acción no se puede deshacer",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#6b7280',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/libro/${id}`, {
                method: 'DELETE',
                headers: {
                    'Accept': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) throw new Error('Error al eliminar el libro');
                return response.json();
            })
            .then(data => {
                Swal.fire('¡Eliminado!', 'El libro ha sido eliminado.', 'success')
                .then(() => {
                    window.location.reload();
                });
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire('Error', 'No se pudo eliminar el libro', 'error');
            });
        }
    });
}

// Manejar envío del formulario
document.getElementById('libro-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const id = document.getElementById('libro-id').value;
    
    // Validar archivos requeridos
    if (!id && !formData.get('pdf_file').size) {
        Swal.fire('Error', 'Por favor, selecciona un archivo PDF', 'error');
        return;
    }

    // Mostrar indicador de carga
    Swal.fire({
        title: 'Guardando...',
        text: 'Por favor espera',
        allowOutsideClick: false,
        showConfirmButton: false,
        willOpen: () => {
            Swal.showLoading();
        }
    });

    if (id) {
        // Actualizar libro existente
        const data = {};
        formData.forEach((value, key) => {
            if (value instanceof File) {
                if (value.size > 0) data[key] = value;
            } else {
                data[key] = value;
            }
        });

        fetch(`/libro/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(handleResponse)
        .then(() => handleSuccess('Libro actualizado correctamente'))
        .catch(handleError);
    } else {
        // Agregar nuevo libro
        fetch('/libro', {
            method: 'POST',
            body: formData
        })
        .then(handleResponse)
        .then(() => handleSuccess('Libro agregado correctamente'))
        .catch(handleError);
    }
});

// Funciones auxiliares para manejar respuestas
function handleResponse(response) {
    if (!response.ok) throw new Error('Error en la respuesta del servidor');
    return response.text().then(text => text ? JSON.parse(text) : {});
}

function handleSuccess(message) {
    Swal.fire({
        icon: 'success',
        title: '¡Éxito!',
        text: message,
        timer: 1500,
        showConfirmButton: false
    }).then(() => {
        window.location.reload();
    });
}

function handleError(error) {
    console.error('Error:', error);
    Swal.fire('Error', error.message, 'error');
}

// Búsqueda en tiempo real
document.getElementById('search').addEventListener('input', function(e) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        const searchTerm = e.target.value;
        if (searchTerm.length > 2) {
            fetch(`/buscar?q=${encodeURIComponent(searchTerm)}`)
                .then(handleResponse)
                .then(actualizarLibros)
                .catch(error => {
                    console.error('Error en la búsqueda:', error);
                });
        } else if (searchTerm.length === 0) {
            window.location.reload();
        }
    }, 300);
});

// Actualizar grid de libros
function actualizarLibros(libros) {
    const grid = document.getElementById('books-grid');
    grid.innerHTML = '';
    
    libros.forEach(libro => {
        const bookElement = document.createElement('div');
        bookElement.className = 'book-item group';
        bookElement.innerHTML = `
            <div class="book-cover bg-white rounded-lg shadow-md overflow-hidden relative aspect-[3/4]">
                ${libro.cover_filename 
                    ? `<img src="/cover/${libro.cover_filename}" alt="${libro.titulo}" class="w-full h-full object-cover">`
                    : `<div class="w-full h-full bg-gray-200 flex items-center justify-center">
                         <i class="fas fa-book text-gray-400 text-4xl"></i>
                       </div>`
                }
                <div class="absolute inset-0 bg-black bg-opacity-60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center space-y-2">
                    <a href="/leer/${libro.id}" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                        <i class="fas fa-book-reader mr-2"></i>Leer
                    </a>
                    <div class="flex space-x-2">
                        <button onclick="editarLibro(${libro.id})" class="bg-white text-gray-800 p-2 rounded-lg hover:bg-gray-100">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="eliminarLibro(${libro.id})" class="bg-white text-red-600 p-2 rounded-lg hover:bg-gray-100">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
            <div class="mt-3">
                <h3 class="font-semibold text-gray-900 truncate">${libro.titulo}</h3>
                <p class="text-sm text-gray-600 truncate">${libro.autor}</p>
            </div>
        `;
        grid.appendChild(bookElement);
    });
}

// Ordenamiento
document.getElementById('sort-select').addEventListener('change', function(e) {
    const sortBy = e.target.value;
    const booksGrid = document.getElementById('books-grid');
    const books = Array.from(booksGrid.children);
    
    books.sort((a, b) => {
        const aValue = a.querySelector(sortBy === 'author' ? 'p' : 'h3').textContent;
        const bValue = b.querySelector(sortBy === 'author' ? 'p' : 'h3').textContent;
        return aValue.localeCompare(bValue);
    });
    
    booksGrid.innerHTML = '';
    books.forEach(book => booksGrid.appendChild(book));
});

// Cerrar modal al hacer clic fuera
document.getElementById('form-modal').addEventListener('click', function(e) {
    if (e.target === this) {
        toggleAddForm();
    }
});