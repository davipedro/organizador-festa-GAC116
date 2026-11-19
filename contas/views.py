from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import CadastroForm


class CadastroView(CreateView):
    """Cadastra um anfitrião e já o deixa logado."""

    form_class = CadastroForm
    template_name = 'registration/cadastro.html'
    success_url = reverse_lazy('festas:festa_lista')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        resposta = super().form_valid(form)
        login(self.request, self.object)
        return resposta


class PerfilView(LoginRequiredMixin, TemplateView):
    """Perfil: mostra os dados do usuário logado, só para leitura."""

    template_name = 'registration/perfil.html'
