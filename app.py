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
def index():
    """Sirve el archivo principal del frontend."""
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register_user():
    """API endpoint para registrar un nuevo usuario."""
    try:
        # Obtiene los datos del cuerpo de la solicitud (JSON)
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Email y contraseña son requeridos."}), 400

        email = data.get('email')
        password = data.get('password') # En un caso real, hashear la contraseña

        # Inserta el nuevo usuario en la tabla 'users' de Supabase
        # La tabla debe llamarse 'users'
        user_data, count = supabase.table('users').insert({
            'email': email,
            'password': password # NO HACER ESTO EN PRODUCCIÓN REAL
        }).execute()

        # user_data[1] contiene la lista de registros insertados
        if user_data[1]:
            return jsonify({"message": f"Usuario {user_data[1][0]['email']} registrado con éxito!"}), 201
        else:
            # Esto puede ocurrir si hay un error en la inserción que no lanza una excepción
            return jsonify({"error": "No se pudo registrar el usuario."}), 500

    except Exception as e:
        # Captura cualquier otro error (ej. violación de constraint, problema de red)
        print(f"Error al registrar: {e}")
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

# --- Arranque del Servidor ---

if __name__ == '__main__':
    # El puerto es proporcionado por el entorno (ej. Railway) o usa 5000 por defecto
    port = int(os.environ.get('PORT', 5000))
    # Escucha en todas las interfaces de red, requerido por los servicios de hosting
    app.run(host='0.0.0.0', port=port, debug=True)
