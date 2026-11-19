from datetime import date, time

from django.test import TestCase
from django.urls import reverse

from contas.models import Usuario

from .models import Convidado, Festa, Tarefa, TipoFesta


class DetalheDaFestaUxTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = Usuario.objects.create_user('ana', password='senha-forte-123')
        tipo = TipoFesta.objects.create(nome='Churrasco')
        cls.festa = Festa.objects.create(
            dono=cls.ana, tipo=tipo, nome='Da Ana', data=date(2027, 1, 10),
            horario=time(12, 0), local='Chácara',
        )
        Convidado.objects.create(festa=cls.festa, nome='Carla')
        Tarefa.objects.create(festa=cls.festa, titulo='Bebidas')

    def setUp(self):
        self.client.force_login(self.ana)
        self.html = self.client.get(
            reverse('festas:festa_detalhe', args=[self.festa.pk])
        ).content.decode()

    def test_formulario_de_convidado_vem_antes_da_lista(self):
        self.assertLess(
            self.html.index('id="form-novo-convidado"'),
            self.html.index('<table'),
        )

    def test_formulario_de_tarefa_vem_antes_da_lista(self):
        self.assertLess(
            self.html.index('id="form-nova-tarefa"'),
            self.html.index('<ul class="list-group">'),
        )

    def test_formularios_de_acao_atualizam_so_a_secao(self):
        # adicionar convidado, adicionar tarefa e o "check" da tarefa
        self.assertEqual(self.html.count('data-atualiza-secao'), 3)

    def test_secoes_que_o_script_atualiza_existem(self):
        for secao in ('bloco-resumo', 'bloco-convidados', 'bloco-tarefas'):
            with self.subTest(secao=secao):
                self.assertIn(f'id="{secao}"', self.html)

    def test_area_de_mensagens_e_o_script_estao_na_pagina(self):
        self.assertIn('id="mensagens"', self.html)
        self.assertIn('js/secoes.js', self.html)

    def test_sem_javascript_o_formulario_ainda_funciona(self):
        # o envio normal (POST) continua redirecionando para a seção certa
        resposta = self.client.post(
            reverse('festas:tarefa_nova', args=[self.festa.pk]),
            {'titulo': 'Alugar mesas'},
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta['Location'].endswith('#bloco-tarefas'))
