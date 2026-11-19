from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from .forms import ConvidadoForm, FestaForm
from .models import Convidado, Festa


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
def convidado_novo(request, festa_pk):
    """Adiciona um convidado pelo formulário do detalhe da festa (só POST).

    A festa precisa ser do usuário logado, senão dá 404. Por GET só volta
    para o detalhe.
    """
    festa = get_object_or_404(Festa, pk=festa_pk, dono=request.user)
    if request.method == 'POST':
        form = ConvidadoForm(request.POST)
        if form.is_valid():
            convidado = form.save(commit=False)
            convidado.festa = festa
            convidado.save()
            messages.success(
                request, f'Convidado "{convidado.nome}" adicionado.'
            )
        else:
            erros = ' '.join(
                erro for lista in form.errors.values() for erro in lista
            )
            messages.error(request, f'Não foi possível adicionar: {erros}')
    return redirect('festas:festa_detalhe', pk=festa.pk)


class ConvidadoDoUsuarioMixin(LoginRequiredMixin):
    """Só enxerga convidados de festas do usuário logado: os outros dão 404."""

    model = Convidado
    context_object_name = 'convidado'

    def get_queryset(self):
        return Convidado.objects.filter(
            festa__dono=self.request.user
        ).select_related('festa')

    def get_success_url(self):
        return reverse('festas:festa_detalhe', kwargs={'pk': self.object.festa_id})


class ConvidadoEditarView(
    ConvidadoDoUsuarioMixin, SuccessMessageMixin, UpdateView
):
    form_class = ConvidadoForm
    template_name = 'festas/convidado_form.html'
    success_message = 'Convidado "%(nome)s" atualizado.'


class ConvidadoExcluirView(ConvidadoDoUsuarioMixin, DeleteView):
    template_name = 'festas/confirmar_exclusao.html'

    def get_context_data(self, **kwargs):
        convidado = self.object
        return super().get_context_data(
            objeto=f'o convidado "{convidado.nome}"',
            cancelar_url=reverse(
                'festas:festa_detalhe', kwargs={'pk': convidado.festa_id}
            ),
            **kwargs,
        )

    def form_valid(self, form):
        nome = self.object.nome
        resposta = super().form_valid(form)
        messages.success(self.request, f'Convidado "{nome}" removido.')
        return resposta