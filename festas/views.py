from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from .forms import FestaForm
from .models import Festa


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
