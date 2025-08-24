from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from usuarios.models import Usuario

class AuthEndpointTest(APITestCase):

    databases = ('default',)

    def setUp(self):
        self.password = "123456"
        self.user = Usuario.objects.create_user(
            username="loginuser",
            password=self.password,
            correo="log@example.com",
            nombre="Usuario Login"
        )

    def test_registro_usuario(self):
        url = reverse("registro-list")
        data = {
            "username": "nuevo_user",
            "password": "123456",
            "correo": "nuevo@example.com",
            "nombre": "Usuario Prueba"  # obligatorio
        }
        response = self.client.post(url, data)
        print(response.data)  # opcional, para debug
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Usuario.objects.filter(username="nuevo_user").exists())

    def test_login_usuario(self):
        url = reverse("login-list")
        data = {"username": self.user.username, "password": self.password}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
