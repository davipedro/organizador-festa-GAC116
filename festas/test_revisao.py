from datetime import date, time

from django.conf import settings
from django.contrib.messages import constants as message_constants
from django.test import TestCase, override_settings
from django.urls import reverse

from contas.models import Usuario

from .models import Convidado, Festa, Tarefa, TipoFesta


class RevisaoVisualTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = Usuario.objects.create_user('ana', password='senha-forte-123')
        cls.bruno = Usuario.objects.create_user(
            'bruno', password='senha-forte-123'
        )
        tipo = TipoFesta.objects.create(nome='Churrasco')
        dados = dict(
            tipo=tipo, data=date(2027, 1, 10), horario=time(12, 0),
            local='Chácara',
        )
        cls.festa = Festa.objects.create(dono=cls.ana, nome='Da Ana', **dados)
        cls.festa_do_bruno = Festa.objects.create(
            dono=cls.bruno, nome='Do Bruno', **dados
        )
        cls.convidado = Convidado.objects.create(festa=cls.festa, nome='Carla')
        cls.tarefa = Tarefa.objects.create(festa=cls.festa, titulo='Bebidas')

    def setUp(self):
        self.client.force_login(self.ana)

    # Mensagens como alertas do Bootstrap

    def test_os_quatro_niveis_viram_classes_do_bootstrap(self):
        esperado = {
            message_constants.SUCCESS: 'success',
            message_constants.INFO: 'info',
            message_constants.WARNING: 'warning',
            message_constants.ERROR: 'danger',
        }
        for nivel, classe in esperado.items():
            with self.subTest(classe=classe):
                self.assertEqual(settings.MESSAGE_TAGS[nivel], classe)

    def test_mensagem_de_sucesso_aparece_como_alerta(self):
        resposta = self.client.post(
            reverse('festas:tarefa_nova', args=[self.festa.pk]),
            {'titulo': 'Alugar mesas'},
            follow=True,
        )
        self.assertContains(resposta, 'alert alert-success')

    def test_mensagem_de_erro_aparece_como_alert_danger(self):
        resposta = self.client.post(
            reverse('festas:tarefa_nova', args=[self.festa.pk]),
            {'titulo': ''},
            follow=True,
        )
        self.assertContains(resposta, 'alert alert-danger')
        self.assertNotContains(resposta, 'alert-error')

    # Uma única tela de confirmação para as três exclusões

    def test_festa_convidado_e_tarefa_usam_o_mesmo_template_de_exclusao(self):
        for nome, args in (
            ('festas:festa_excluir', [self.festa.pk]),
            ('festas:convidado_excluir', [self.convidado.pk]),
            ('festas:tarefa_excluir', [self.tarefa.pk]),
        ):
            with self.subTest(nome=nome):
                resposta = self.client.get(reverse(nome, args=args))
                self.assertTemplateUsed(
                    resposta, 'festas/confirmar_exclusao.html'
                )
                self.assertContains(resposta, 'Cancelar')
                self.assertContains(resposta, 'Sim, excluir')

    # Página 404 com o visual do site (só aparece com DEBUG desligado)

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver'])
    def test_pagina_404_tem_o_visual_do_site(self):
        resposta = self.client.get('/pagina-que-nao-existe/')
        self.assertEqual(resposta.status_code, 404)
        self.assertTemplateUsed(resposta, '404.html')
        self.assertContains(
            resposta, 'Página não encontrada', status_code=404
        )
        self.assertContains(resposta, 'css/site.css', status_code=404)
        self.assertContains(resposta, 'Minhas festas', status_code=404)

    @override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver'])
    def test_festa_de_outro_usuario_mostra_a_pagina_404_do_site(self):
        resposta = self.client.get(
            reverse('festas:festa_detalhe', args=[self.festa_do_bruno.pk])
        )
        self.assertEqual(resposta.status_code, 404)
        self.assertTemplateUsed(resposta, '404.html')
