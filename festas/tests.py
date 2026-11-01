from datetime import date, time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase

from .models import Festa, TipoFesta


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
            },
        )
        erros = resposta.context['adminform'].form.errors if resposta.context else ''
        self.assertEqual(resposta.status_code, 302, erros)
        festa = Festa.objects.get(nome='Churrasco de fim de ano')
        self.assertEqual(festa.dono, self.admin)
        self.assertEqual(festa.tipo, tipo)
        self.assertEqual(festa.custo_medio_por_pessoa, Decimal('45.50'))
