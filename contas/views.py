from django.shortcuts import render


def cadastro(request):
    """Tela provisória de cadastro: o formulário real vem na tarefa D9."""
    return render(request, 'registration/cadastro.html')
