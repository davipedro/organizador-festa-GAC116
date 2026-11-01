from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class TipoFesta(models.Model):
    """Categoria da festa (aniversário, churrasco, confraternização...)."""

    nome = models.CharField('nome', max_length=60, unique=True)

    class Meta:
        verbose_name = 'tipo de festa'
        verbose_name_plural = 'tipos de festa'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Festa(models.Model):
    """Uma festa organizada por um usuário."""

    dono = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='festas',
        verbose_name='dono',
    )
    tipo = models.ForeignKey(
        TipoFesta,
        on_delete=models.PROTECT,
        related_name='festas',
        verbose_name='tipo de festa',
    )
    nome = models.CharField('nome', max_length=120)
    data = models.DateField('data')
    horario = models.TimeField('horário')
    local = models.CharField('local', max_length=200)
    descricao = models.TextField('descrição', blank=True)
    orcamento_estimado = models.DecimalField(
        'orçamento estimado',
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    custo_medio_por_pessoa = models.DecimalField(
        'custo médio por pessoa',
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        verbose_name = 'festa'
        verbose_name_plural = 'festas'
        ordering = ['data', 'horario']

    def __str__(self):
        return f'{self.nome} ({self.data:%d/%m/%Y})'


class Convidado(models.Model):
    """Pessoa convidada para uma festa, com o status da confirmação."""

    class Status(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente'
        VOU = 'vou', 'Vou'
        TALVEZ = 'talvez', 'Talvez'
        NAO_VOU = 'nao_vou', 'Não vou'

    festa = models.ForeignKey(
        Festa,
        on_delete=models.CASCADE,
        related_name='convidados',
        verbose_name='festa',
    )
    nome = models.CharField('nome', max_length=120)
    contato = models.CharField('contato', max_length=120, blank=True)
    status = models.CharField(
        'status',
        max_length=10,
        choices=Status,
        default=Status.PENDENTE,
    )

    class Meta:
        verbose_name = 'convidado'
        verbose_name_plural = 'convidados'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Tarefa(models.Model):
    """Item da lista de preparativos de uma festa."""

    festa = models.ForeignKey(
        Festa,
        on_delete=models.CASCADE,
        related_name='tarefas',
        verbose_name='festa',
    )
    titulo = models.CharField('título', max_length=160)
    concluida = models.BooleanField('concluída', default=False)

    class Meta:
        verbose_name = 'tarefa'
        verbose_name_plural = 'tarefas'
        ordering = ['concluida', 'titulo']

    def __str__(self):
        return self.titulo
