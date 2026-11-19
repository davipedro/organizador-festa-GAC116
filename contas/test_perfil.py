from django.test import TestCase
from django.urls import reverse

from .models import Usuario


class PerfilTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = Usuario.objects.create_user(
            'ana', 'ana@example.com', 'senha-forte-123',
            first_name='Ana', last_name='Souza',
        )
        cls.bruno = Usuario.objects.create_user(
            'bruno', 'bruno@example.com', 'senha-forte-123',
            first_name='Bruno', last_name='Lima',
        )
        cls.sem_dados = Usuario.objects.create_user(
            'sem_dados', password='senha-forte-123'
        )

    def test_visitante_vai_para_o_login(self):
        resposta = self.client.get(reverse('contas:perfil'))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse('contas:login'), resposta['Location'])

    def test_mostra_nome_sobrenome_email_e_usuario(self):
        self.client.force_login(self.ana)
        resposta = self.client.get(reverse('contas:perfil'))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Ana')
        self.assertContains(resposta, 'Souza')
        self.assertContains(resposta, 'ana@example.com')
        self.assertContains(resposta, 'ana')

    def test_mostra_so_os_dados_de_quem_esta_logado(self):
        self.client.force_login(self.ana)
        resposta = self.client.get(reverse('contas:perfil'))
        self.assertNotContains(resposta, 'bruno@example.com')
        self.assertNotContains(resposta, 'Lima')

    def test_campos_vazios_mostram_nao_informado(self):
        self.client.force_login(self.sem_dados)
        resposta = self.client.get(reverse('contas:perfil'))
        self.assertContains(resposta, 'Não informado', count=3)
        self.assertContains(resposta, 'sem_dados')

    def test_perfil_e_somente_leitura(self):
        self.client.force_login(self.ana)
        resposta = self.client.get(reverse('contas:perfil'))
        self.assertNotContains(resposta, 'name="first_name"')
        self.assertNotContains(resposta, 'name="email"')
        # o único formulário da página é o botão Sair
        self.assertEqual(resposta.content.decode().count('<form'), 1)
        resposta = self.client.post(
            reverse('contas:perfil'), {'first_name': 'Outro'}
        )
        self.assertEqual(resposta.status_code, 405)
        self.ana.refresh_from_db()
        self.assertEqual(self.ana.first_name, 'Ana')

    def test_link_do_perfil_aparece_na_navbar_so_para_quem_esta_logado(self):
        resposta = self.client.get(reverse('contas:login'))
        self.assertNotContains(resposta, reverse('contas:perfil'))
        self.client.force_login(self.ana)
        resposta = self.client.get(reverse('festas:festa_lista'))
        self.assertContains(resposta, reverse('contas:perfil'))
