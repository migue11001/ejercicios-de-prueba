document.getElementById('login-form').addEventListener('submit', async function(event) {
    event.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const messageElement = document.getElementById('message');

    messageElement.textContent = '';
    messageElement.className = '';

    try {
        const response = await fetch('/token', { // Usaremos la ruta /token para el login
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        });

        const result = await response.json();

        if (response.ok) {
            messageElement.textContent = '¡Login exitoso!';
            messageElement.className = 'success';
            // Aquí podrías guardar el token de sesión (result.access_token) y redirigir al usuario
            // Por ejemplo: localStorage.setItem('supabase.auth.token', JSON.stringify(result));
            // window.location.href = '/dashboard'; // Redirigir a una página protegida
            console.log('Sesión iniciada:', result);
        } else {
            throw new Error(result.error || 'Email o contraseña incorrectos.');
        }
    } catch (error) {
        messageElement.textContent = error.message;
        messageElement.className = 'error';
    }
});
