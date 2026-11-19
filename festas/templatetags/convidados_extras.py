from django import template

from festas.forms import ConvidadoForm
from festas.models import Convidado

register = template.Library()

# Cor do badge do Bootstrap para cada status do convidado
CLASSES_STATUS = {
    Convidado.Status.PENDENTE: 'text-bg-secondary',
    Convidado.Status.VOU: 'text-bg-success',
    Convidado.Status.TALVEZ: 'text-bg-warning',
    Convidado.Status.NAO_VOU: 'text-bg-danger',
}


@register.filter
def classe_status(status):
    """Classe do badge do Bootstrap para o status de um convidado."""
    return CLASSES_STATUS.get(status, 'text-bg-secondary')


@register.simple_tag
def resumo_convidados(festa):
    """Quantos convidados há em cada status, na ordem dos status."""
    contagem = {status: 0 for status, _ in Convidado.Status.choices}
    for status in festa.convidados.values_list('status', flat=True):
        contagem[status] += 1
    return [
        {
            'status': status,
            'rotulo': rotulo,
            'total': contagem[status],
            'classe': CLASSES_STATUS[status],
        }
        for status, rotulo in Convidado.Status.choices
    ]


@register.simple_tag
def form_novo_convidado():
    """Formulário vazio para adicionar um convidado dentro da festa."""
    return ConvidadoForm()