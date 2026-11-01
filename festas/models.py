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
