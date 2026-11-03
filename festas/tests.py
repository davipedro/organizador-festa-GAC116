from datetime import date, time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase

from .models import Convidado, Festa, Tarefa, TipoFesta


class FestaTests(TestCase):
    def setUp(self):
        self.dono = get_user_model().objects.create_user(
            username='ana', password='senha-de-teste-123'
        )
        self.tipo = TipoFesta.objects.create(nome='Aniversário')

    def criar_festa(self, **extra):
        dados = dict(
            dono=self.dono,
            tipo=self.tipo,
            nome='Aniversário da Ana',
            data=date(2026, 12, 5),
            horario=time(19, 30),
            local='Salão do prédio',
        )
        dados.update(extra)
        return Festa.objects.create(**dados)

    def test_festa_pertence_a_um_dono_e_a_um_tipo(self):
        festa = self.criar_festa()
        self.assertEqual(festa.dono, self.dono)
        self.assertEqual(festa.tipo, self.tipo)
        self.assertIn(festa, self.dono.festas.all())
        self.assertIn(festa, self.tipo.festas.all())

    def test_valores_padrao_de_custo_e_descricao_opcional(self):
        festa = self.criar_festa()
        festa.full_clean()
        self.assertEqual(festa.orcamento_estimado, Decimal('0'))
        self.assertEqual(festa.custo_medio_por_pessoa, Decimal('0'))
        self.assertEqual(festa.descricao, '')

    def test_custos_nao_aceitam_valor_negativo(self):
        festa = self.criar_festa(orcamento_estimado=Decimal('-1'))
        with self.assertRaises(ValidationError):
            festa.full_clean()

    def test_tipo_em_uso_nao_pode_ser_excluido(self):
        self.criar_festa()
        with self.assertRaises(ProtectedError):
            self.tipo.delete()

    def test_tipo_sem_festas_pode_ser_excluido(self):
        outro = TipoFesta.objects.create(nome='Churrasco')
        outro.delete()
        self.assertFalse(TipoFesta.objects.filter(nome='Churrasco').exists())

    def test_nome_legivel(self):
        self.assertEqual(str(self.tipo), 'Aniversário')
        self.assertEqual(str(self.criar_festa()), 'Aniversário da Ana (05/12/2026)')


class AdminFestasTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username='admin', password='senha-de-teste-123'
        )
        self.client.login(username='admin', password='senha-de-teste-123')

    def test_cadastra_tipo_de_festa_pelo_admin(self):
        resposta = self.client.post(
            '/admin/festas/tipofesta/add/', {'nome': 'Churrasco'}
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(TipoFesta.objects.filter(nome='Churrasco').exists())

    def test_cadastra_festa_pelo_admin(self):
        tipo = TipoFesta.objects.create(nome='Churrasco')
        resposta = self.client.post(
            '/admin/festas/festa/add/',
            {
                'dono': self.admin.pk,
                'tipo': tipo.pk,
                'nome': 'Churrasco de fim de ano',
                'data': '20/12/2026',
                'horario': '13:00',
                'local': 'Chácara do Zé',
                'descricao': '',
                # o campo numérico do navegador envia sempre com ponto
                'orcamento_estimado': '800.00',
                'custo_medio_por_pessoa': '45.50',
                # campos de controle dos inlines (nenhum convidado/tarefa novo)
                'convidados-TOTAL_FORMS': '0',
                'convidados-INITIAL_FORMS': '0',
                'tarefas-TOTAL_FORMS': '0',
                'tarefas-INITIAL_FORMS': '0',
            },
        )
        erros = resposta.context['adminform'].form.errors if resposta.context else ''
        self.assertEqual(resposta.status_code, 302, erros)
        festa = Festa.objects.get(nome='Churrasco de fim de ano')
        self.assertEqual(festa.dono, self.admin)
        self.assertEqual(festa.tipo, tipo)
        self.assertEqual(festa.custo_medio_por_pessoa, Decimal('45.50'))


class ConvidadoTarefaTests(TestCase):
    def setUp(self):
        dono = get_user_model().objects.create_user(
            username='ana', password='senha-de-teste-123'
        )
        tipo = TipoFesta.objects.create(nome='Aniversário')
        self.festa = Festa.objects.create(
            dono=dono,
            tipo=tipo,
            nome='Aniversário da Ana',
            data=date(2026, 12, 5),
            horario=time(19, 30),
            local='Salão do prédio',
        )

    def test_convidado_comeca_pendente(self):
        convidado = Convidado.objects.create(festa=self.festa, nome='Bruno')
        self.assertEqual(convidado.status, Convidado.Status.PENDENTE)
        self.assertEqual(convidado.contato, '')

    def test_status_aceita_so_os_quatro_valores(self):
        validos = {'pendente', 'vou', 'talvez', 'nao_vou'}
        self.assertEqual({valor for valor, _ in Convidado.Status.choices}, validos)
        convidado = Convidado(festa=self.festa, nome='Bruno', status='quem-sabe')
        with self.assertRaises(ValidationError):
            convidado.full_clean()

    def test_rotulos_do_status_em_portugues(self):
        rotulos = [rotulo for _, rotulo in Convidado.Status.choices]
        self.assertEqual(rotulos, ['Pendente', 'Vou', 'Talvez', 'Não vou'])

    def test_tarefa_comeca_nao_concluida(self):
        tarefa = Tarefa.objects.create(festa=self.festa, titulo='Comprar bebidas')
        self.assertFalse(tarefa.concluida)

    def test_excluir_festa_remove_convidados_e_tarefas(self):
        Convidado.objects.create(festa=self.festa, nome='Bruno')
        Tarefa.objects.create(festa=self.festa, titulo='Comprar bebidas')
        self.festa.delete()
        self.assertEqual(Convidado.objects.count(), 0)
        self.assertEqual(Tarefa.objects.count(), 0)

    def test_cadastra_convidado_e_tarefa_pelo_admin(self):
        get_user_model().objects.create_superuser(
            username='admin', password='senha-de-teste-123'
        )
        self.client.login(username='admin', password='senha-de-teste-123')
        r1 = self.client.post(
            '/admin/festas/convidado/add/',
            {'festa': self.festa.pk, 'nome': 'Carla', 'contato': '', 'status': 'vou'},
        )
        r2 = self.client.post(
            '/admin/festas/tarefa/add/',
            {'festa': self.festa.pk, 'titulo': 'Reservar o salão'},
        )
        self.assertEqual((r1.status_code, r2.status_code), (302, 302))
        self.assertEqual(Convidado.objects.get(nome='Carla').status, 'vou')
        self.assertTrue(Tarefa.objects.filter(titulo='Reservar o salão').exists())


class AdminListaDeFestasTests(TestCase):
    def setUp(self):
        ana = get_user_model().objects.create_user(username='ana', password='x')
        bruno = get_user_model().objects.create_user(username='bruno', password='x')
        get_user_model().objects.create_superuser(
            username='admin', password='senha-de-teste-123'
        )
        self.client.login(username='admin', password='senha-de-teste-123')
        self.aniversario = TipoFesta.objects.create(nome='Aniversário')
        self.churrasco = TipoFesta.objects.create(nome='Churrasco')

        def festa(dono, tipo, nome, dia, local):
            return Festa.objects.create(
                dono=dono, tipo=tipo, nome=nome, data=dia,
                horario=time(19, 0), local=local,
            )

        self.f1 = festa(ana, self.aniversario, 'Aniversário da Ana',
                        date(2026, 12, 5), 'Salão do prédio')
        self.f2 = festa(ana, self.churrasco, 'Churrasco de fim de ano',
                        date(2026, 12, 20), 'Chácara do Zé')
        self.f3 = festa(bruno, self.aniversario, 'Aniversário do Bruno',
                        date(2027, 1, 10), 'Casa do Bruno')
        for nome, status in [('Bia', 'vou'), ('Caio', 'vou'), ('Duda', 'talvez')]:
            Convidado.objects.create(festa=self.f1, nome=nome, status=status)
        for nome, status in [('Eva', 'nao_vou'), ('Fabio', 'pendente')]:
            Convidado.objects.create(festa=self.f2, nome=nome, status=status)

    def nomes(self, **filtros):
        resposta = self.client.get('/admin/festas/festa/', filtros)
        self.assertEqual(resposta.status_code, 200)
        return [festa.nome for festa in resposta.context['cl'].result_list]

    def test_lista_mostra_numero_de_confirmados(self):
        resposta = self.client.get('/admin/festas/festa/')
        confirmados = {
            f.nome: f.total_confirmados for f in resposta.context['cl'].result_list
        }
        self.assertEqual(confirmados['Aniversário da Ana'], 2)
        self.assertEqual(confirmados['Churrasco de fim de ano'], 0)
        self.assertEqual(confirmados['Aniversário do Bruno'], 0)

    def test_filtro_por_tipo(self):
        self.assertEqual(
            self.nomes(tipo__id__exact=self.churrasco.pk),
            ['Churrasco de fim de ano'],
        )

    def test_filtro_por_data(self):
        nomes = self.nomes(data__gte='2026-12-10', data__lt='2027-01-01')
        self.assertEqual(nomes, ['Churrasco de fim de ano'])

    def test_filtro_por_status_dos_convidados(self):
        self.assertEqual(self.nomes(status_convidado='talvez'), ['Aniversário da Ana'])
        self.assertEqual(self.nomes(status_convidado='pendente'),
                         ['Churrasco de fim de ano'])

    def test_filtro_por_status_nao_repete_festa_nem_muda_a_contagem(self):
        # a festa tem 2 convidados "vou": não pode aparecer duas vezes
        resposta = self.client.get('/admin/festas/festa/', {'status_convidado': 'vou'})
        lista = list(resposta.context['cl'].result_list)
        self.assertEqual([f.nome for f in lista], ['Aniversário da Ana'])
        self.assertEqual(lista[0].total_confirmados, 2)

    def test_filtro_por_status_com_talvez_mantem_contagem_de_confirmados(self):
        resposta = self.client.get('/admin/festas/festa/', {'status_convidado': 'talvez'})
        self.assertEqual(resposta.context['cl'].result_list[0].total_confirmados, 2)

    def test_busca_por_nome_local_e_dono(self):
        self.assertEqual(self.nomes(q='Churrasco'), ['Churrasco de fim de ano'])
        self.assertEqual(self.nomes(q='Chácara'), ['Churrasco de fim de ano'])
        self.assertEqual(self.nomes(q='bruno'), ['Aniversário do Bruno'])

    def test_navegacao_por_data(self):
        nomes = self.nomes(data__year=2026, data__month=12)
        self.assertEqual(
            nomes, ['Aniversário da Ana', 'Churrasco de fim de ano']
        )

    def test_tela_da_festa_tem_convidados_e_tarefas_editaveis(self):
        resposta = self.client.get(f'/admin/festas/festa/{self.f1.pk}/change/')
        self.assertEqual(resposta.status_code, 200)
        modelos = {
            formset.formset.model for formset in resposta.context['inline_admin_formsets']
        }
        self.assertEqual(modelos, {Convidado, Tarefa})
