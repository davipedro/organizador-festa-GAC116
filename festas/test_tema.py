from django.test import TestCase
from django.urls import reverse

from contas.models import Usuario


class TemaVisualTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = Usuario.objects.create_user('ana', password='senha-forte-123')

    def test_pagina_tem_atributo_de_tema(self):
        resposta = self.client.get(reverse('contas:login'))
        self.assertContains(resposta, 'data-bs-theme=')

    def test_script_do_tema_roda_antes_do_css(self):
        html = self.client.get(reverse('contas:login')).content.decode()
        self.assertLess(
            html.index("localStorage.getItem('sua-festa-tema')"),
            html.index('css/site.css'),
        )

    def test_visitante_ve_entrar_e_cadastrar(self):
        resposta = self.client.get(reverse('contas:login'))
        self.assertContains(resposta, reverse('contas:cadastro'))
        self.assertContains(resposta, 'Entrar')
        self.assertNotContains(resposta, 'Minhas festas')
        self.assertNotContains(resposta, 'Sair')

    def test_logado_ve_menu_e_sair_por_post(self):
        self.client.force_login(self.ana)
        resposta = self.client.get(reverse('festas:festa_nova'))
        self.assertContains(resposta, 'Minhas festas')
        self.assertContains(resposta, 'Nova festa')
        self.assertContains(resposta, 'id="botao-tema"')
        self.assertContains(
            resposta, f'<form method="post" action="{reverse("contas:logout")}"'
        )
        self.assertContains(resposta, 'csrfmiddlewaretoken')
        self.assertNotContains(resposta, 'Cadastrar')

    def test_menu_recolhe_no_celular(self):
        resposta = self.client.get(reverse('contas:login'))
        self.assertContains(resposta, 'navbar-toggler')
        self.assertContains(resposta, 'navbar-collapse')

    def test_nada_vem_de_cdn(self):
        html = self.client.get(reverse('contas:login')).content.decode()
        self.assertNotIn('cdn.', html)
        self.assertNotIn('googleapis', html)
