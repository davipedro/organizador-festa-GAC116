from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from .forms import FestaForm, TarefaForm
from .models import Festa, Tarefa


@login_required
def em_construcao(request, **kwargs):
    """Página provisória das URLs do contrato, trocada por cada tarefa."""
    return render(request, 'festas/em_construcao.html')


class FestaDoUsuarioMixin(LoginRequiredMixin):
    """Só enxerga as festas do usuário logado: a de outro dá 404."""

    model = Festa
    context_object_name = 'festa'

    def get_queryset(self):
        return Festa.objects.filter(dono=self.request.user).select_related(
            'tipo'
        )


class FestaDetalheView(FestaDoUsuarioMixin, DetailView):
    template_name = 'festas/festa_detalhe.html'


class FestaNovaView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Festa
    form_class = FestaForm
    template_name = 'festas/festa_form.html'
    success_message = 'Festa "%(nome)s" criada.'

    def form_valid(self, form):
        form.instance.dono = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('festas:festa_detalhe', kwargs={'pk': self.object.pk})


class FestaEditarView(FestaDoUsuarioMixin, SuccessMessageMixin, UpdateView):
    form_class = FestaForm
    template_name = 'festas/festa_form.html'
    success_message = 'Festa "%(nome)s" atualizada.'

    def get_success_url(self):
        return reverse('festas:festa_detalhe', kwargs={'pk': self.object.pk})


class FestaExcluirView(FestaDoUsuarioMixin, DeleteView):
    template_name = 'festas/confirmar_exclusao.html'
    success_url = reverse_lazy('festas:festa_lista')

    def get_context_data(self, **kwargs):
        festa = self.object
        total_convidados = festa.convidados.count()
        total_tarefas = festa.tarefas.count()
        return super().get_context_data(
            objeto=f'a festa "{festa.nome}"',
            aviso=(
                f'Isso também apaga {total_convidados} convidado(s) e '
                f'{total_tarefas} tarefa(s) dessa festa.'
            ),
            cancelar_url=reverse('festas:festa_detalhe', kwargs={'pk': festa.pk}),
            **kwargs,
        )

    def form_valid(self, form):
        messages.success(self.request, f'Festa "{self.object.nome}" excluída.')
        return super().form_valid(form)


@login_required
def tarefa_nova(request, festa_pk):
    """Adiciona uma tarefa pelo formulário do detalhe da festa (só POST).

    A festa precisa ser do usuário logado, senão dá 404. Por GET só volta
    para o detalhe.
    """
    festa = get_object_or_404(Festa, pk=festa_pk, dono=request.user)
    if request.method == 'POST':
        form = TarefaForm(request.POST)
        if form.is_valid():
            tarefa = form.save(commit=False)
            tarefa.festa = festa
            tarefa.save()
            messages.success(request, f'Tarefa "{tarefa.titulo}" adicionada.')
        else:
            erros = ' '.join(
                erro for lista in form.errors.values() for erro in lista
            )
            messages.error(request, f'Não foi possível adicionar: {erros}')
    return redirect('festas:festa_detalhe', pk=festa.pk)


class TarefaDoUsuarioMixin(LoginRequiredMixin):
    """Só enxerga tarefas de festas do usuário logado: as outras dão 404."""

    model = Tarefa
    context_object_name = 'tarefa'

    def get_queryset(self):
        return Tarefa.objects.filter(
            festa__dono=self.request.user
        ).select_related('festa')

    def get_success_url(self):
        return reverse('festas:festa_detalhe', kwargs={'pk': self.object.festa_id})


@login_required
@require_POST
def tarefa_alternar(request, pk):
    """Inverte o "concluída" da tarefa. Só aceita POST (GET dá 405)."""
    tarefa = get_object_or_404(
        Tarefa, pk=pk, festa__dono=request.user
    )
    tarefa.concluida = not tarefa.concluida
    tarefa.save(update_fields=['concluida'])
    return redirect('festas:festa_detalhe', pk=tarefa.festa_id)


class TarefaEditarView(TarefaDoUsuarioMixin, SuccessMessageMixin, UpdateView):
    form_class = TarefaForm
    template_name = 'festas/tarefa_form.html'
    success_message = 'Tarefa "%(titulo)s" atualizada.'


class TarefaExcluirView(TarefaDoUsuarioMixin, DeleteView):
    template_name = 'festas/confirmar_exclusao.html'

    def get_context_data(self, **kwargs):
        tarefa = self.object
        return super().get_context_data(
            objeto=f'a tarefa "{tarefa.titulo}"',
            cancelar_url=reverse(
                'festas:festa_detalhe', kwargs={'pk': tarefa.festa_id}
            ),
            **kwargs,
        )

    def form_valid(self, form):
        titulo = self.object.titulo
        resposta = super().form_valid(form)
        messages.success(self.request, f'Tarefa "{titulo}" removida.')
        return resposta