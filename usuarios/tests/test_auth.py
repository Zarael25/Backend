from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from usuarios.models import Usuario
from django.test import override_settings


# ---------------- Forzamos que no se usen los routers personalizados de DB ----------------
@override_settings(DATABASE_ROUTERS=[])
class AuthEndpointTest(APITestCase):
    """
    Pruebas de integración para los endpoints de autenticación:
    - Registro de usuario
    - Login de usuario
    """

    def setUp(self):
        """
        Configuración inicial antes de cada test.
        Creamos un usuario en la base de datos para probar login.
        """
        self.password = "123456"
        self.user = Usuario.objects.create_user(
            username="loginuser",
            password=self.password,
            correo="log@example.com",
            nombre="Usuario Login"
        )

    def test_registro_usuario(self):
        """
        Verifica que el endpoint de registro crea un nuevo usuario.
        - Envía los datos al endpoint /registro/
        - Confirma que responde 201 CREATED
        - Confirma que el usuario efectivamente se guardó en la DB
        """
        url = reverse("registro-list")  # Obtiene la URL del endpoint de registro
        data = {
            "username": "nuevo_user",
            "password": "123456",
            "correo": "nuevo@example.com",
            "nombre": "Usuario Prueba"  # campo obligatorio
        }
        response = self.client.post(url, data)
        print(response.data)  # opcional, útil para depuración
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Usuario.objects.filter(username="nuevo_user").exists())

    def test_login_usuario(self):
        """
        Verifica que un usuario pueda iniciar sesión.
        - Envía credenciales al endpoint /login/
        - Confirma que responde 200 OK
        - Confirma que en la respuesta estén los tokens 'access' y 'refresh'
        """
        url = reverse("login-list")  # Obtiene la URL del endpoint de login
        data = {"username": self.user.username, "password": self.password}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)   # token de acceso
        self.assertIn("refresh", response.data)  # token de refresco
