from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


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


class CadastroTests(TestCase):
    def dados(self, **extra):
        dados = {
            'username': 'carla',
            'email': 'carla@example.com',
            'first_name': 'Carla',
            'last_name': 'Souza',
            'password1': 'senha-forte-9182',
            'password2': 'senha-forte-9182',
        }
        dados.update(extra)
        return dados

    def test_tela_de_cadastro_abre_para_visitante(self):
        resposta = self.client.get(reverse('contas:cadastro'))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Criar conta')

    def test_cadastro_cria_usuario_comum_e_ja_deixa_logado(self):
        resposta = self.client.post(reverse('contas:cadastro'), self.dados())
        self.assertRedirects(resposta, reverse('festas:festa_lista'))
        usuario = get_user_model().objects.get(username='carla')
        self.assertEqual(usuario.email, 'carla@example.com')
        self.assertEqual(usuario.get_full_name(), 'Carla Souza')
        self.assertTrue(usuario.check_password('senha-forte-9182'))
        self.assertEqual(int(self.client.session['_auth_user_id']), usuario.pk)

    def test_cadastro_nunca_cria_administrador(self):
        self.client.post(
            reverse('contas:cadastro'),
            self.dados(is_staff='on', is_superuser='on'),
        )
        usuario = get_user_model().objects.get(username='carla')
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)

    def test_senhas_diferentes_nao_cadastram(self):
        resposta = self.client.post(
            reverse('contas:cadastro'), self.dados(password2='outra-senha-123')
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(username='carla').exists())

    def test_email_nome_e_sobrenome_sao_obrigatorios(self):
        for campo in ('email', 'first_name', 'last_name'):
            with self.subTest(campo=campo):
                resposta = self.client.post(
                    reverse('contas:cadastro'), self.dados(**{campo: ''})
                )
                self.assertEqual(resposta.status_code, 200)
                self.assertIn(campo, resposta.context['form'].errors)
        self.assertFalse(get_user_model().objects.filter(username='carla').exists())

    def test_usuario_logado_nao_ve_a_tela_de_cadastro(self):
        usuario = get_user_model().objects.create_user(
            username='ana', password='senha-de-teste-123'
        )
        self.client.force_login(usuario)
        resposta = self.client.get(reverse('contas:cadastro'))
        self.assertRedirects(resposta, reverse('festas:festa_lista'))


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username='ana', password='senha-de-teste-123'
        )

    def test_login_por_usuario_e_senha_leva_para_minhas_festas(self):
        resposta = self.client.post(
            reverse('contas:login'),
            {'username': 'ana', 'password': 'senha-de-teste-123'},
        )
        self.assertRedirects(resposta, reverse('festas:festa_lista'))

    def test_login_com_senha_errada_fica_na_tela(self):
        resposta = self.client.post(
            reverse('contas:login'), {'username': 'ana', 'password': 'errada'}
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_respeita_o_next_da_pagina_protegida(self):
        resposta = self.client.get(reverse('festas:festa_nova'))
        self.assertRedirects(
            resposta, f"{reverse('contas:login')}?next=/festas/nova/"
        )
        resposta = self.client.post(
            f"{reverse('contas:login')}?next=/festas/nova/",
            {'username': 'ana', 'password': 'senha-de-teste-123'},
        )
        self.assertRedirects(resposta, reverse('festas:festa_nova'))

    def test_usuario_logado_que_abre_o_login_vai_para_minhas_festas(self):
        self.client.force_login(self.usuario)
        resposta = self.client.get(reverse('contas:login'))
        self.assertRedirects(resposta, reverse('festas:festa_lista'))

    def test_logout_encerra_a_sessao_e_volta_ao_login(self):
        self.client.force_login(self.usuario)
        resposta = self.client.post(reverse('contas:logout'))
        self.assertRedirects(resposta, reverse('contas:login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_por_get_nao_e_aceito(self):
        self.client.force_login(self.usuario)
        resposta = self.client.get(reverse('contas:logout'))
        self.assertEqual(resposta.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)
