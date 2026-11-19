from datetime import date, time

from django.test import TestCase
from django.urls import reverse

from contas.models import Usuario

from .models import Festa, Tarefa, TipoFesta


class TarefasNoDetalheTests(TestCase):
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
        cls.tarefa = Tarefa.objects.create(
            festa=cls.festa, titulo='Comprar bebidas'
        )
        cls.tarefa_do_bruno = Tarefa.objects.create(
            festa=cls.festa_do_bruno, titulo='Reservar o salão'
        )

    def setUp(self):
        self.client.force_login(self.ana)

    def detalhe(self):
        return reverse('festas:festa_detalhe', args=[self.festa.pk])

    def volta_para_tarefas(self):
        # as ações voltam para a seção de tarefas, não para o topo da página
        return self.detalhe() + '#bloco-tarefas'

    def test_detalhe_lista_as_tarefas_da_festa(self):
        resposta = self.client.get(self.detalhe())
        self.assertContains(resposta, 'Comprar bebidas')
        self.assertNotContains(resposta, 'Reservar o salão')

    def test_progresso_bate_com_os_dados(self):
        Tarefa.objects.create(festa=self.festa, titulo='B', concluida=True)
        Tarefa.objects.create(festa=self.festa, titulo='C', concluida=True)
        Tarefa.objects.create(festa=self.festa, titulo='D')
        resposta = self.client.get(self.detalhe())
        self.assertContains(resposta, '2 de 4 concluídas')
        self.assertContains(resposta, 'aria-valuenow="50"')

    def test_progresso_atualiza_ao_alternar(self):
        self.assertContains(self.client.get(self.detalhe()), '0 de 1 concluída')
        self.client.post(
            reverse('festas:tarefa_alternar', args=[self.tarefa.pk])
        )
        resposta = self.client.get(self.detalhe())
        self.assertContains(resposta, '1 de 1 concluída')
        self.assertContains(resposta, 'aria-valuenow="100"')

    def test_sem_tarefas_nao_mostra_progresso(self):
        Tarefa.objects.filter(festa=self.festa).delete()
        resposta = self.client.get(self.detalhe())
        self.assertNotContains(resposta, 'progresso-tarefas')
        self.assertContains(resposta, 'Nenhuma tarefa ainda')

    def test_tarefa_concluida_aparece_riscada(self):
        Tarefa.objects.filter(pk=self.tarefa.pk).update(concluida=True)
        self.assertContains(
            self.client.get(self.detalhe()), 'text-decoration-line-through'
        )

    def test_adicionar_tarefa_mostra_mensagem(self):
        resposta = self.client.post(
            reverse('festas:tarefa_nova', args=[self.festa.pk]),
            {'titulo': 'Alugar mesas'},
            follow=True,
        )
        self.assertRedirects(resposta, self.volta_para_tarefas())
        self.assertContains(resposta, 'Tarefa &quot;Alugar mesas&quot; adicionada.')
        nova = Tarefa.objects.get(titulo='Alugar mesas')
        self.assertEqual(nova.festa, self.festa)
        self.assertFalse(nova.concluida)

    def test_adicionar_sem_titulo_mostra_erro_e_nao_cria(self):
        total = Tarefa.objects.count()
        resposta = self.client.post(
            reverse('festas:tarefa_nova', args=[self.festa.pk]),
            {'titulo': ''},
            follow=True,
        )
        self.assertContains(resposta, 'Não foi possível adicionar')
        self.assertEqual(Tarefa.objects.count(), total)

    def test_adicionar_por_get_so_volta_ao_detalhe(self):
        resposta = self.client.get(
            reverse('festas:tarefa_nova', args=[self.festa.pk])
        )
        self.assertRedirects(resposta, self.volta_para_tarefas())

    def test_editar_muda_o_titulo(self):
        url = reverse('festas:tarefa_editar', args=[self.tarefa.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        resposta = self.client.post(url, {'titulo': 'Comprar gelo'}, follow=True)
        self.assertRedirects(resposta, self.volta_para_tarefas())
        self.assertContains(resposta, 'atualizada')
        self.tarefa.refresh_from_db()
        self.assertEqual(self.tarefa.titulo, 'Comprar gelo')

    def test_alternar_inverte_e_duas_vezes_volta_ao_original(self):
        url = reverse('festas:tarefa_alternar', args=[self.tarefa.pk])
        resposta = self.client.post(url)
        self.assertRedirects(resposta, self.volta_para_tarefas())
        self.tarefa.refresh_from_db()
        self.assertTrue(self.tarefa.concluida)
        self.client.post(url)
        self.tarefa.refresh_from_db()
        self.assertFalse(self.tarefa.concluida)

    def test_alternar_por_get_responde_405(self):
        resposta = self.client.get(
            reverse('festas:tarefa_alternar', args=[self.tarefa.pk])
        )
        self.assertEqual(resposta.status_code, 405)
        self.tarefa.refresh_from_db()
        self.assertFalse(self.tarefa.concluida)

    def test_excluir_so_apaga_depois_de_confirmar(self):
        url = reverse('festas:tarefa_excluir', args=[self.tarefa.pk])
        tela = self.client.get(url)
        self.assertEqual(tela.status_code, 200)
        self.assertContains(tela, 'Comprar bebidas')
        self.assertTrue(Tarefa.objects.filter(pk=self.tarefa.pk).exists())
        resposta = self.client.post(url, follow=True)
        self.assertRedirects(resposta, self.volta_para_tarefas())
        self.assertContains(resposta, 'removida')
        self.assertFalse(Tarefa.objects.filter(pk=self.tarefa.pk).exists())

    def test_tarefa_de_outro_usuario_da_404_em_todas_as_acoes(self):
        pk = self.tarefa_do_bruno.pk
        for nome in (
            'festas:tarefa_editar',
            'festas:tarefa_excluir',
            'festas:tarefa_alternar',
        ):
            url = reverse(nome, args=[pk])
            with self.subTest(nome=nome):
                self.assertEqual(
                    self.client.post(url, {'titulo': 'X'}).status_code, 404
                )
        self.assertEqual(
            self.client.get(
                reverse('festas:tarefa_editar', args=[pk])
            ).status_code,
            404,
        )
        self.tarefa_do_bruno.refresh_from_db()
        self.assertEqual(self.tarefa_do_bruno.titulo, 'Reservar o salão')
        self.assertFalse(self.tarefa_do_bruno.concluida)

    def test_adicionar_em_festa_de_outro_usuario_da_404_e_nao_cria(self):
        total = Tarefa.objects.count()
        resposta = self.client.post(
            reverse('festas:tarefa_nova', args=[self.festa_do_bruno.pk]),
            {'titulo': 'Intrusa'},
        )
        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(Tarefa.objects.count(), total)

    def test_visitante_vai_para_o_login(self):
        self.client.logout()
        for nome, args in (
            ('festas:tarefa_nova', [self.festa.pk]),
            ('festas:tarefa_editar', [self.tarefa.pk]),
            ('festas:tarefa_excluir', [self.tarefa.pk]),
        ):
            with self.subTest(nome=nome):
                resposta = self.client.get(reverse(nome, args=args))
                self.assertEqual(resposta.status_code, 302)
                self.assertIn(reverse('contas:login'), resposta['Location'])
