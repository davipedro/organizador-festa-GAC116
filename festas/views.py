from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def em_construcao(request, **kwargs):
    """Página provisória das URLs do contrato, trocada por cada tarefa."""
    return render(request, 'festas/em_construcao.html')
