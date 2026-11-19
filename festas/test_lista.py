from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from contas.models import Usuario

from .models import Convidado, Festa, TipoFesta


class ListaDeFestasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = Usuario.objects.create_user('ana', password='senha-forte-123')
        cls.bruno = Usuario.objects.create_user(
            'bruno', password='senha-forte-123'
        )
        cls.churrasco = TipoFesta.objects.create(nome='Churrasco')
        cls.aniversario = TipoFesta.objects.create(nome='Aniversário')
        hoje = timezone.localdate()
        cls.proxima_churrasco = cls.festa(
            cls.ana, cls.churrasco, 'Churrasco da turma', 'Chácara do Zé',
            hoje + timedelta(days=10),
        )
        cls.proxima_aniversario = cls.festa(
            cls.ana, cls.aniversario, 'Bolo da Ana', 'Salão Vila Bela',
            hoje + timedelta(days=5),
        )
        cls.passada = cls.festa(
            cls.ana, cls.churrasco, 'Churrasco antigo', 'Quintal',
            hoje - timedelta(days=3),
        )
        cls.do_bruno = cls.festa(
            cls.bruno, cls.churrasco, 'Churrasco do Bruno', 'Sítio',
            hoje + timedelta(days=2),
        )

    @staticmethod
    def festa(dono, tipo, nome, local, data):
        return Festa.objects.create(
            dono=dono, tipo=tipo, nome=nome, local=local, data=data,
            horario='19:00', custo_medio_por_pessoa=Decimal('50'),
            orcamento_estimado=Decimal('1000'),
        )

    def nomes(self, **parametros):
        self.client.force_login(self.ana)
        resposta = self.client.get(reverse('festas:festa_lista'), parametros)
        self.assertEqual(resposta.status_code, 200)
        return [f.nome for f in resposta.context['festas']]

    def test_visitante_e_redirecionado_ao_login(self):
        resposta = self.client.get(reverse('festas:festa_lista'))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse('contas:login'), resposta['Location'])

    def test_ana_so_ve_as_proprias_festas(self):
        nomes = self.nomes(periodo='todas')
        self.assertNotIn('Churrasco do Bruno', nomes)
        self.assertEqual(len(nomes), 3)

    def test_padrao_e_proximas_ordenadas_por_data(self):
        self.assertEqual(
            self.nomes(), ['Bolo da Ana', 'Churrasco da turma']
        )

    def test_periodo_passadas(self):
        self.assertEqual(self.nomes(periodo='passadas'), ['Churrasco antigo'])

    def test_periodo_todas(self):
        self.assertEqual(
            self.nomes(periodo='todas'),
            ['Churrasco antigo', 'Bolo da Ana', 'Churrasco da turma'],
        )

    def test_busca_por_nome_sem_diferenciar_maiuscula(self):
        self.assertEqual(self.nomes(q='BOLO'), ['Bolo da Ana'])

    def test_busca_por_local(self):
        self.assertEqual(self.nomes(q='chácara'), ['Churrasco da turma'])

    def test_filtro_por_tipo(self):
        self.assertEqual(
            self.nomes(tipo=self.aniversario.pk), ['Bolo da Ana']
        )

    def test_filtros_combinados(self):
        self.assertEqual(
            self.nomes(
                q='churrasco', tipo=self.churrasco.pk, periodo='todas'
            ),
            ['Churrasco antigo', 'Churrasco da turma'],
        )
        self.assertEqual(
            self.nomes(q='churrasco', tipo=self.aniversario.pk), []
        )

    def test_parametros_invalidos_nao_quebram(self):
        for parametros in (
            {'tipo': 'abc'},
            {'tipo': '99999999999999999999999'},
            {'tipo': '-1'},
            {'periodo': 'xyz'},
            {'q': "'; DROP TABLE festas_festa; --"},
        ):
            with self.subTest(parametros=parametros):
                self.nomes(**parametros)
        # parâmetro inválido de período cai no padrão
        self.assertEqual(
            self.nomes(periodo='xyz'), ['Bolo da Ana', 'Churrasco da turma']
        )

    def test_card_mostra_confirmados_e_custo_estimado(self):
        Convidado.objects.create(
            festa=self.proxima_aniversario, nome='A', status='vou'
        )
        Convidado.objects.create(
            festa=self.proxima_aniversario, nome='B', status='vou'
        )
        Convidado.objects.create(
            festa=self.proxima_aniversario, nome='C', status='talvez'
        )
        self.client.force_login(self.ana)
        resposta = self.client.get(reverse('festas:festa_lista'))
        festa = resposta.context['festas'][0]
        self.assertEqual(festa.confirmados, 2)
        self.assertEqual(festa.custo_estimado, Decimal('100'))
        self.assertContains(resposta, 'R$ 100,00')

    def test_lista_nao_faz_consulta_por_card(self):
        for i in range(5):
            self.festa(
                self.ana, self.churrasco, f'Extra {i}', 'Local',
                timezone.localdate() + timedelta(days=20 + i),
            )
        self.client.force_login(self.ana)
        # sessão, usuário, existe festa, tipos e a lista (sem consulta por card)
        with self.assertNumQueries(5):
            self.client.get(reverse('festas:festa_lista'))

    def test_card_leva_ao_detalhe(self):
        self.client.force_login(self.ana)
        resposta = self.client.get(reverse('festas:festa_lista'))
        self.assertContains(
            resposta,
            reverse('festas:festa_detalhe', args=[self.proxima_aniversario.pk]),
        )

    def test_formulario_mantem_os_valores_escolhidos(self):
        self.client.force_login(self.ana)
        resposta = self.client.get(
            reverse('festas:festa_lista'),
            {'q': 'bolo', 'tipo': self.aniversario.pk, 'periodo': 'todas'},
        )
        self.assertContains(resposta, 'value="bolo"')
        self.assertContains(
            resposta, f'<option value="{self.aniversario.pk}" selected>'
        )
        self.assertContains(resposta, '<option value="todas" selected>')

    def test_botao_limpar_volta_a_url_sem_parametros(self):
        self.client.force_login(self.ana)
        resposta = self.client.get(reverse('festas:festa_lista'), {'q': 'x'})
        self.assertContains(
            resposta, f'href="{reverse("festas:festa_lista")}">Limpar'
        )

    def test_estado_vazio_sem_festas_oferece_criar_a_primeira(self):
        novo = Usuario.objects.create_user('novo', password='senha-forte-123')
        self.client.force_login(novo)
        resposta = self.client.get(reverse('festas:festa_lista'))
        self.assertContains(resposta, 'Criar primeira festa')
        self.assertContains(resposta, reverse('festas:festa_nova'))

    def test_estado_vazio_com_filtro_sem_resultado(self):
        self.client.force_login(self.ana)
        resposta = self.client.get(reverse('festas:festa_lista'), {'q': 'zzz'})
        self.assertContains(resposta, 'Nenhuma festa encontrada')
        self.assertNotContains(resposta, 'Criar primeira festa')

    def test_botao_nova_festa_visivel(self):
        self.client.force_login(self.ana)
        resposta = self.client.get(reverse('festas:festa_lista'))
        self.assertContains(resposta, reverse('festas:festa_nova'))
