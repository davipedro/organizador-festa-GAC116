from django.contrib.auth import get_user_model
from django.test import TestCase


class UsuarioTests(TestCase):
    def test_modelo_de_usuario_do_projeto(self):
        self.assertEqual(get_user_model()._meta.label, 'contas.Usuario')

    def test_superusuario_acessa_o_admin(self):
        get_user_model().objects.create_superuser(
            username='admin', password='senha-de-teste-123'
        )
        self.assertTrue(
            self.client.login(username='admin', password='senha-de-teste-123')
        )
        resposta = self.client.get('/admin/')
        self.assertEqual(resposta.status_code, 200)

    def test_usuario_comum_nao_acessa_o_admin(self):
        get_user_model().objects.create_user(
            username='comum', password='senha-de-teste-123'
        )
        self.client.login(username='comum', password='senha-de-teste-123')
        resposta = self.client.get('/admin/')
        self.assertEqual(resposta.status_code, 302)
