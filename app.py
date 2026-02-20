import os
from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv

# Carga las variables de entorno desde un archivo .env si existe (para desarrollo local)
load_dotenv()

app = Flask(__name__)

# --- Configuración de Supabase ---
# Lee las credenciales desde las variables de entorno
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

# Verifica si las credenciales están presentes
if not url or not key:
    raise ValueError("Las variables de entorno SUPABASE_URL y SUPABASE_KEY son necesarias.")

# Inicializa el cliente de Supabase
supabase: Client = create_client(url, key)

# --- Rutas de la Aplicación ---

@app.route('/')
def page_register():
    """Sirve la página de registro."""
    return render_template('index.html')

@app.route('/login')
def page_login():
    """Sirve la página de inicio de sesión."""
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register_user():
    """API endpoint para registrar un nuevo usuario usando Supabase Auth."""
    try:
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Email y contraseña son requeridos."}), 400

        email = data.get('email')
        password = data.get('password')

        # Usa el método de autenticación de Supabase para registrar al usuario.
        # Esto crea el usuario en la tabla 'auth.users' y nuestro trigger se encarga del perfil.
        session = supabase.auth.sign_up({
            "email": email,
            "password": password,
        })

        # Supabase puede requerir confirmación por email dependiendo de tu configuración
        if session.user:
            return jsonify({"message": f"Usuario {session.user.email} registrado. Revisa tu email para confirmar la cuenta."}), 201
        else:
            return jsonify({"error": "No se pudo registrar el usuario. Puede que ya exista."}), 500

    except Exception as e:
        print(f"Error al registrar: {e}")
        # El objeto de error de Supabase a menudo está en e.args[0]
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

        # Usa el método de autenticación de Supabase para iniciar sesión.
        session = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        # Si el login es exitoso, la sesión contiene el access_token (JWT) y datos del usuario.
        return jsonify(session.dict()), 200

    except Exception as e:
        print(f"Error al iniciar sesión: {e}")
        return jsonify({"error": "Email o contraseña incorrectos."}), 401

# --- Arranque del Servidor ---

if __name__ == '__main__':
    # El puerto es proporcionado por el entorno (ej. Railway) o usa 5000 por defecto
    port = int(os.environ.get('PORT', 5000))
    # Escucha en todas las interfaces de red, requerido por los servicios de hosting
    app.run(host='0.0.0.0', port=port, debug=True)
