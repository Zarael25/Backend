from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from usuarios.models import Usuario
from django.test import override_settings


@override_settings(DATABASE_ROUTERS=[])  # Deshabilitamos routers para evitar conflictos en tests
class PerfilEndpointTest(APITestCase):
    """
    Pruebas de integración para los endpoints de perfil de usuario:
    - Obtener perfil
    - Editar perfil
    """

    def setUp(self):
        """
        Configuración inicial antes de cada test:
        - Crea un usuario de prueba
        - Lo autentica vía /login/
        - Guarda el access token y lo añade a los headers
        """
        self.password = "123456"
        self.user = Usuario.objects.create_user(
            username="testuser",
            password=self.password,
            correo="test@example.com",
            nombre="Usuario Test"
        )

        # Hacemos login para obtener el token de acceso
        url_login = reverse("login-list")
        data_login = {"username": self.user.username, "password": self.password}
        response = self.client.post(url_login, data_login)
        self.access_token = response.data["access"]

        # Usamos el token en todas las requests siguientes
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_obtener_perfil(self):
        """
        Verifica que el usuario autenticado puede obtener sus datos de perfil.
        - GET /perfil/
        - Debe retornar 200 OK
        - Los datos devueltos deben coincidir con los del usuario autenticado
        """
        url = reverse("perfil-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["correo"], self.user.correo)

    def test_editar_perfil(self):
        """
        Verifica que el usuario autenticado puede editar su perfil.
        - PATCH /usuarios/editar-perfil/
        - Se actualizan nombre, correo y password
        - Luego se valida que los cambios se reflejen en la DB
        """
        url = "/api/usuarios/editar-perfil/"  # url_path definido en el ViewSet
        nuevos_datos = {
            "nombre": "Nombre Actualizado",
            "correo": "nuevoemail@example.com",
            "password": "nuevopass"
        }
        response = self.client.patch(url, nuevos_datos)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refrescamos el usuario en memoria desde la DB
        self.user.refresh_from_db()
        self.assertEqual(self.user.nombre, nuevos_datos["nombre"])
        self.assertEqual(self.user.correo, nuevos_datos["correo"])
        self.assertTrue(self.user.check_password(nuevos_datos["password"]))
