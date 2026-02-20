import os
from flask import Flask, request, jsonify # Se elimina render_template
from supabase import create_client, Client
from dotenv import load_dotenv
from flask_cors import CORS
from datetime import datetime, timedelta, timezone

# Carga las variables de entorno desde un archivo .env si existe (para desarrollo local)
load_dotenv()

app = Flask(__name__)
CORS(app) # Habilita CORS para toda la aplicación

# --- Configuración de Supabase ---
# Lee las credenciales desde las variables de entorno
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

# Verifica si las credenciales están presentes
if not url or not key:
    raise ValueError("Las variables de entorno SUPABASE_URL y SUPABASE_KEY son necesarias.")

# Inicializa el cliente de Supabase
supabase: Client = create_client(url, key)

# --- Endpoints de la API de Autenticación ---

# Se eliminan las rutas @app.route('/') y @app.route('/login') que servían HTML.
# Este backend ahora solo responde a peticiones de API.

@app.route('/register', methods=['POST'])
def register_user():
    """API endpoint para registrar un nuevo usuario usando Supabase Auth."""
    try:
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Email y contraseña son requeridos."}), 400

        email = data.get('email')
        password = data.get('password')

        session = supabase.auth.sign_up({
            "email": email,
            "password": password,
        })

        if session.user:
            return jsonify({"message": f"Usuario {session.user.email} registrado."}), 201
        else:
            # Esto puede ocurrir si el usuario ya existe pero no está confirmado, etc.
            return jsonify({"error": "No se pudo registrar el usuario. Revisa los datos o el usuario puede que ya exista."}), 500

    except Exception as e:
        print(f"Error al registrar: {e}")
        error_message = str(e.args[0]) if e.args else str(e)
        return jsonify({"error": error_message}), 500

@app.route('/token', methods=['POST'])
def get_token():
    """API endpoint para iniciar sesión y obtener un token de sesión."""
    try:
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Email y contraseña son requeridos."}), 400

        email = data.get('email')
        password = data.get('password')

        session = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        return jsonify(session.dict()), 200

    except Exception as e:
        print(f"Error al iniciar sesión: {e}")
        return jsonify({"error": "Email o contraseña incorrectos."}), 401

# --- Endpoints de la API de Publicaciones ---

@app.route('/publications', methods=['POST'])
def create_publication():
    """Crea una nueva publicación."""
    try:
        # 1. Leer el token y validar usuario
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Token no proporcionado o en formato incorrecto."}), 401
        
        jwt = auth_header.split(' ')[1]
        user_session = supabase.auth.get_user(jwt)
        if not user_session or not user_session.user:
            return jsonify({"error": "Token inválido o expirado."}), 401
        
        user = user_session.user

        # 2. Leer el body de la petición
        data = request.get_json()
        required_fields = ['title', 'content', 'language', 'publish_period', 'pub_code']
        if not all(field in data for field in required_fields):
            return jsonify({"error": f"Faltan campos requeridos: {required_fields}"}), 400

        # 3. Calcular expires_at
        expires_at = datetime.now(timezone.utc) + timedelta(days=28)

        # 4. Preparar e insertar en Supabase
        new_publication = {
            'user_id': user.id,
            'user_email': user.email,
            'title': data['title'],
            'content': data['content'],
            'language': data['language'],
            'publish_period': data['publish_period'],
            'pub_code': data['pub_code'],
            'cover_image': data.get('cover_image'), # Opcional
            'style': data.get('style'),             # Opcional
            'expires_at': expires_at.isoformat()
        }

        result, count = supabase.table('publications').insert(new_publication).execute()

        # 5. Retornar el objeto insertado
        return jsonify(result[1][0]), 201

    except Exception as e:
        print(f"Error al crear publicación: {e}")
        return jsonify({"error": "Error interno del servidor al crear la publicación."}), 500

@app.route('/publications/<language>', methods=['GET'])
def get_publications_by_language(language):
    """Obtiene las publicaciones de un salón (idioma)."""
    try:
        # 1. Validar que el usuario esté autenticado
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Token no proporcionado o en formato incorrecto."}), 401
        
        jwt = auth_header.split(' ')[1]
        user_session = supabase.auth.get_user(jwt)
        if not user_session or not user_session.user:
            return jsonify({"error": "Token inválido o expirado."}), 401

        # 2. Consultar Supabase
        now = datetime.now(timezone.utc).isoformat()
        result, count = supabase.table('publications').select('*').eq('language', language).gt('expires_at', now).order('created_at', desc=True).execute()

        # 3. Retornar lista de publicaciones
        return jsonify(result[1]), 200

    except Exception as e:
        print(f"Error al leer publicaciones: {e}")
        return jsonify({"error": "Error interno del servidor al leer las publicaciones."}), 500

@app.route('/publications/<publication_id>', methods=['DELETE'])
def delete_publication(publication_id):
    """Elimina una publicación."""
    try:
        # 1. Validar usuario
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Token no proporcionado o en formato incorrecto."}), 401
        
        jwt = auth_header.split(' ')[1]
        user_session = supabase.auth.get_user(jwt)
        if not user_session or not user_session.user:
            return jsonify({"error": "Token inválido o expirado."}), 401

        # 2. Intentar eliminar de Supabase
        # La Política de Seguridad (RLS) se encarga de verificar que el usuario sea el dueño.
        result, count = supabase.table('publications').delete().eq('id', publication_id).execute()
        
        # data, count
        if len(result[1]) == 0:
             return jsonify({"error": "Publicación no encontrada o no tienes permiso para eliminarla."}), 404

        # 3. Retornar éxito
        return jsonify({"message": f"Publicación {publication_id} eliminada con éxito."}), 200

    except Exception as e:
        print(f"Error al eliminar publicación: {e}")
        return jsonify({"error": "Error interno del servidor al eliminar la publicación."}), 500

# --- Arranque del Servidor ---

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) # debug=True se puede quitar para producción