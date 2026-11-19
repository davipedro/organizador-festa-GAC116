from datetime import date, time
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from contas.models import Usuario

from .models import Convidado, Festa, TipoFesta


class ConvidadosNoDetalheTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = Usuario.objects.create_user('ana', password='senha-forte-123')
        cls.bruno = Usuario.objects.create_user(
            'bruno', password='senha-forte-123'
        )
        tipo = TipoFesta.objects.create(nome='Churrasco')
        dados = dict(
            tipo=tipo, data=date(2027, 1, 10), horario=time(12, 0),
            local='Chácara', custo_medio_por_pessoa=Decimal('50'),
            orcamento_estimado=Decimal('1000'),
        )
        cls.festa = Festa.objects.create(dono=cls.ana, nome='Da Ana', **dados)
        cls.festa_do_bruno = Festa.objects.create(
            dono=cls.bruno, nome='Do Bruno', **dados
        )
        cls.convidado = Convidado.objects.create(
            festa=cls.festa, nome='Carla', contato='carla@example.com'
        )
        cls.convidado_do_bruno = Convidado.objects.create(
            festa=cls.festa_do_bruno, nome='Daniel'
        )

    def setUp(self):
        self.client.force_login(self.ana)

    def detalhe(self):
        return reverse('festas:festa_detalhe', args=[self.festa.pk])

    def test_detalhe_lista_convidados_com_status_e_contagem(self):
        Convidado.objects.create(festa=self.festa, nome='Eva', status='vou')
        Convidado.objects.create(festa=self.festa, nome='Fabio', status='vou')
        Convidado.objects.create(festa=self.festa, nome='Gil', status='talvez')
        resposta = self.client.get(self.detalhe())
        self.assertContains(resposta, 'Carla')
        self.assertContains(resposta, 'Pendente: 1')
        self.assertContains(resposta, 'Vou: 2')
        self.assertContains(resposta, 'Talvez: 1')
        self.assertContains(resposta, 'Não vou: 0')
        self.assertContains(resposta, 'text-bg-success')

    def test_detalhe_nao_mostra_convidados_de_outra_festa(self):
        self.assertNotContains(self.client.get(self.detalhe()), 'Daniel')

    def test_adicionar_convidado_mostra_mensagem(self):
        resposta = self.client.post(
            reverse('festas:convidado_novo', args=[self.festa.pk]),
            {'nome': 'Helena', 'contato': '(35) 99999-0000', 'status': 'vou'},
            follow=True,
        )
        self.assertRedirects(resposta, self.volta_para_convidados())
        self.assertContains(resposta, 'Convidado &quot;Helena&quot; adicionado.')
        novo = Convidado.objects.get(nome='Helena')
        self.assertEqual(novo.festa, self.festa)
        self.assertEqual(novo.status, 'vou')

    def test_adicionar_sem_status_fica_pendente(self):
        self.client.post(
            reverse('festas:convidado_novo', args=[self.festa.pk]),
            {'nome': 'Igor', 'status': 'pendente'},
        )
        self.assertEqual(Convidado.objects.get(nome='Igor').status, 'pendente')

    def test_adicionar_invalido_mostra_erro_e_nao_cria(self):
        total = Convidado.objects.count()
        resposta = self.client.post(
            reverse('festas:convidado_novo', args=[self.festa.pk]),
            {'nome': '', 'status': 'vou'},
            follow=True,
        )
        self.assertRedirects(resposta, self.volta_para_convidados())
        self.assertContains(resposta, 'Não foi possível adicionar')
        self.assertEqual(Convidado.objects.count(), total)

    def test_adicionar_com_status_invalido_nao_cria(self):
        total = Convidado.objects.count()
        self.client.post(
            reverse('festas:convidado_novo', args=[self.festa.pk]),
            {'nome': 'Jair', 'status': 'inventado'},
        )
        self.assertEqual(Convidado.objects.count(), total)

    def test_adicionar_por_get_so_volta_ao_detalhe(self):
        resposta = self.client.get(
            reverse('festas:convidado_novo', args=[self.festa.pk])
        )
        self.assertRedirects(resposta, self.volta_para_convidados())
        self.assertEqual(Convidado.objects.filter(festa=self.festa).count(), 1)

    def test_editar_muda_nome_contato_e_status(self):
        url = reverse('festas:convidado_editar', args=[self.convidado.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        resposta = self.client.post(
            url,
            {'nome': 'Carla Souza', 'contato': '(35) 98888-0000',
             'status': 'talvez'},
            follow=True,
        )
        self.assertRedirects(resposta, self.volta_para_convidados())
        self.assertContains(resposta, 'atualizado')
        self.convidado.refresh_from_db()
        self.assertEqual(self.convidado.nome, 'Carla Souza')
        self.assertEqual(self.convidado.contato, '(35) 98888-0000')
        self.assertEqual(self.convidado.status, 'talvez')

    def test_excluir_so_apaga_depois_de_confirmar(self):
        url = reverse('festas:convidado_excluir', args=[self.convidado.pk])
        tela = self.client.get(url)
        self.assertEqual(tela.status_code, 200)
        self.assertContains(tela, 'Carla')
        self.assertTrue(Convidado.objects.filter(pk=self.convidado.pk).exists())
        resposta = self.client.post(url, follow=True)
        self.assertRedirects(resposta, self.volta_para_convidados())
        self.assertContains(resposta, 'removido')
        self.assertFalse(Convidado.objects.filter(pk=self.convidado.pk).exists())

    def test_mudar_para_vou_altera_o_custo_estimado(self):
        self.assertEqual(self.festa.custo_estimado, 0)
        self.client.post(
            reverse('festas:convidado_editar', args=[self.convidado.pk]),
            {'nome': 'Carla', 'contato': '', 'status': 'vou'},
        )
        festa = Festa.objects.get(pk=self.festa.pk)
        self.assertEqual(festa.confirmados, 1)
        self.assertEqual(festa.custo_estimado, Decimal('50'))
        self.assertContains(self.client.get(self.detalhe()), 'R$ 50,00')

    def test_convidado_de_outro_usuario_da_404_ao_editar_e_excluir(self):
        for nome in ('festas:convidado_editar', 'festas:convidado_excluir'):
            url = reverse(nome, args=[self.convidado_do_bruno.pk])
            with self.subTest(nome=nome, metodo='get'):
                self.assertEqual(self.client.get(url).status_code, 404)
            with self.subTest(nome=nome, metodo='post'):
                self.assertEqual(
                    self.client.post(url, {'nome': 'X', 'status': 'vou'}).status_code,
                    404,
                )
        self.convidado_do_bruno.refresh_from_db()
        self.assertEqual(self.convidado_do_bruno.nome, 'Daniel')

    def test_adicionar_em_festa_de_outro_usuario_da_404_e_nao_cria(self):
        total = Convidado.objects.count()
        resposta = self.client.post(
            reverse('festas:convidado_novo', args=[self.festa_do_bruno.pk]),
            {'nome': 'Intruso', 'status': 'vou'},
        )
        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(Convidado.objects.count(), total)

    def test_visitante_vai_para_o_login(self):
        self.client.logout()
        for nome, args in (
            ('festas:convidado_novo', [self.festa.pk]),
            ('festas:convidado_editar', [self.convidado.pk]),
            ('festas:convidado_excluir', [self.convidado.pk]),
        ):
            with self.subTest(nome=nome):
                resposta = self.client.get(reverse(nome, args=args))
                self.assertEqual(resposta.status_code, 302)
                self.assertIn(reverse('contas:login'), resposta['Location'])
