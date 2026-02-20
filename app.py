import os
from flask import Flask, request, jsonify # Se elimina render_template
from supabase import create_client, Client
from dotenv import load_dotenv
from flask_cors import CORS

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

# --- Arranque del Servidor ---

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) # debug=True se puede quitar para producción