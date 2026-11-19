from django import template

from festas.forms import TarefaForm

register = template.Library()


@register.simple_tag
def progresso_tarefas(festa):
    """Quantas tarefas da festa estão concluídas, do total, e a porcentagem."""
    tarefas = festa.tarefas.all()
    total = len(tarefas)
    concluidas = sum(1 for tarefa in tarefas if tarefa.concluida)
    return {
        'concluidas': concluidas,
        'total': total,
        'percentual': round(100 * concluidas / total) if total else 0,
    }


@register.simple_tag
def form_nova_tarefa():
    """Formulário vazio para adicionar uma tarefa dentro da festa."""
    return TarefaForm()