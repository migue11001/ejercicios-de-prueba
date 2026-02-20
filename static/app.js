document.getElementById('register-form').addEventListener('submit', async function(event) {
    event.preventDefault(); // Evita que el formulario se envíe de la forma tradicional

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const messageElement = document.getElementById('message');

    messageElement.textContent = '';
    messageElement.className = '';

    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        });

        const result = await response.json();

        if (response.ok) {
            messageElement.textContent = result.message;
            messageElement.className = 'success';
            document.getElementById('register-form').reset();
        } else {
            throw new Error(result.error || 'Ocurrió un error');
        }
    } catch (error) {
        messageElement.textContent = error.message;
        messageElement.className = 'error';
    }
});