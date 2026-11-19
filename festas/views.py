from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import ConvidadoForm, FestaForm, TarefaForm
from .models import Convidado, Festa, Tarefa, TipoFesta


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
    return redirect(
        reverse('festas:festa_detalhe', kwargs={'pk': festa.pk})
        + '#bloco-convidados'
    )


class ConvidadoDoUsuarioMixin(LoginRequiredMixin):
    """Só enxerga convidados de festas do usuário logado: os outros dão 404."""

    model = Convidado
    context_object_name = 'convidado'

    def get_queryset(self):
        return Convidado.objects.filter(
            festa__dono=self.request.user
        ).select_related('festa')

    def get_success_url(self):
        # volta para a lista de convidados, não para o topo da página
        return (
            reverse('festas:festa_detalhe', kwargs={'pk': self.object.festa_id})
            + '#bloco-convidados'
        )


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
            ) + '#bloco-convidados',
            **kwargs,
        )

    def form_valid(self, form):
        nome = self.object.nome
        resposta = super().form_valid(form)
        messages.success(self.request, f'Convidado "{nome}" removido.')
        return resposta


class FestaListaView(LoginRequiredMixin, ListView):
    """Minhas festas: só as do usuário logado, com busca e filtros via GET.

    Parâmetros: ``q`` (nome ou local), ``tipo`` (id do tipo de festa) e
    ``periodo`` (todas, proximas ou passadas; o padrão é proximas). Valores
    inválidos são ignorados em vez de gerar erro.
    """

    template_name = 'festas/festa_lista.html'
    context_object_name = 'festas'
    PERIODOS = ('todas', 'proximas', 'passadas')
    PERIODO_PADRAO = 'proximas'

    def get_busca(self):
        return self.request.GET.get('q', '').strip()

    def get_tipo(self):
        try:
            tipo = int(self.request.GET.get('tipo', ''))
        except ValueError:
            return None
        # fora desse intervalo o banco nem teria um tipo com esse id
        return tipo if 0 < tipo < 2**31 else None

    def get_periodo(self):
        periodo = self.request.GET.get('periodo', '')
        return periodo if periodo in self.PERIODOS else self.PERIODO_PADRAO

    def get_queryset(self):
        festas = (
            Festa.objects.filter(dono=self.request.user)
            .select_related('tipo')
            .annotate(
                total_confirmados=Count(
                    'convidados',
                    filter=Q(convidados__status=Convidado.Status.VOU),
                )
            )
        )

        busca = self.get_busca()
        if busca:
            festas = festas.filter(
                Q(nome__icontains=busca) | Q(local__icontains=busca)
            )

        tipo = self.get_tipo()
        if tipo is not None:
            festas = festas.filter(tipo_id=tipo)

        hoje = timezone.localdate()
        periodo = self.get_periodo()
        if periodo == 'proximas':
            festas = festas.filter(data__gte=hoje)
        elif periodo == 'passadas':
            festas = festas.filter(data__lt=hoje)

        return festas.order_by('data', 'horario')

    def get_context_data(self, **kwargs):
        periodo = self.get_periodo()
        busca = self.get_busca()
        tipo = self.get_tipo()
        return super().get_context_data(
            busca=busca,
            tipo_selecionado=tipo,
            periodo=periodo,
            tipos=TipoFesta.objects.all(),
            tem_festas=Festa.objects.filter(dono=self.request.user).exists(),
            filtro_ativo=bool(busca) or tipo is not None
            or periodo != self.PERIODO_PADRAO,
        )


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
    return redirect(
        reverse('festas:festa_detalhe', kwargs={'pk': festa.pk})
        + '#bloco-tarefas'
    )


class TarefaDoUsuarioMixin(LoginRequiredMixin):
    """Só enxerga tarefas de festas do usuário logado: as outras dão 404."""

    model = Tarefa
    context_object_name = 'tarefa'

    def get_queryset(self):
        return Tarefa.objects.filter(
            festa__dono=self.request.user
        ).select_related('festa')

    def get_success_url(self):
        # volta para a lista de tarefas, não para o topo da página
        return (
            reverse('festas:festa_detalhe', kwargs={'pk': self.object.festa_id})
            + '#bloco-tarefas'
        )


@login_required
@require_POST
def tarefa_alternar(request, pk):
    """Inverte o "concluída" da tarefa. Só aceita POST (GET dá 405)."""
    tarefa = get_object_or_404(
        Tarefa, pk=pk, festa__dono=request.user
    )
    tarefa.concluida = not tarefa.concluida
    tarefa.save(update_fields=['concluida'])
    # sem a âncora a página voltaria para o topo a cada clique no "check"
    return redirect(
        reverse('festas:festa_detalhe', kwargs={'pk': tarefa.festa_id})
        + '#bloco-tarefas'
    )


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
            ) + '#bloco-tarefas',
            **kwargs,
        )

    def form_valid(self, form):
        titulo = self.object.titulo
        resposta = super().form_valid(form)
        messages.success(self.request, f'Tarefa "{titulo}" removida.')
        return resposta
