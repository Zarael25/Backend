from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from usuarios.models import Usuario

class PerfilEndpointTest(APITestCase):
    databases = ('default',)

    def setUp(self):
        self.password = "123456"
        self.user = Usuario.objects.create_user(
            username="testuser",
            password=self.password,
            correo="test@example.com",
            nombre="Usuario Test"
        )

        # Logueamos al usuario para endpoints que requieren autenticación
        url_login = reverse("login-list")
        data_login = {"username": self.user.username, "password": self.password}
        response = self.client.post(url_login, data_login)
        self.access_token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_obtener_perfil(self):
        """Probar que se puede obtener los datos del perfil del usuario autenticado"""
        url = reverse("perfil-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["correo"], self.user.correo)

    def test_editar_perfil(self):
        """Probar que se puede editar el perfil del usuario"""
        url = "/api/usuarios/editar-perfil/"  # url_path de tu ViewSet
        nuevos_datos = {
            "nombre": "Nombre Actualizado",
            "correo": "nuevoemail@example.com",
            "password": "nuevopass"
        }
        response = self.client.patch(url, nuevos_datos)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refrescamos el usuario de la DB
        self.user.refresh_from_db()
        self.assertEqual(self.user.nombre, nuevos_datos["nombre"])
        self.assertEqual(self.user.correo, nuevos_datos["correo"])
        self.assertTrue(self.user.check_password(nuevos_datos["password"]))
