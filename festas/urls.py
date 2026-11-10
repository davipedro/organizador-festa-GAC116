from django.urls import path

from . import views

app_name = 'festas'

urlpatterns = [
    path('', views.em_construcao, name='festa_lista'),
    path('festas/nova/', views.FestaNovaView.as_view(), name='festa_nova'),
    path(
        'festas/<int:pk>/',
        views.FestaDetalheView.as_view(),
        name='festa_detalhe',
    ),
    path(
        'festas/<int:pk>/editar/',
        views.FestaEditarView.as_view(),
        name='festa_editar',
    ),
    path(
        'festas/<int:pk>/excluir/',
        views.FestaExcluirView.as_view(),
        name='festa_excluir',
    ),
    path(
        'festas/<int:festa_pk>/convidados/novo/',
        views.em_construcao,
        name='convidado_novo',
    ),
    path(
        'convidados/<int:pk>/editar/',
        views.em_construcao,
        name='convidado_editar',
    ),
    path(
        'convidados/<int:pk>/excluir/',
        views.em_construcao,
        name='convidado_excluir',
    ),
    path(
        'festas/<int:festa_pk>/tarefas/nova/',
        views.em_construcao,
        name='tarefa_nova',
    ),
    path(
        'tarefas/<int:pk>/alternar/',
        views.em_construcao,
        name='tarefa_alternar',
    ),
    path('tarefas/<int:pk>/editar/', views.em_construcao, name='tarefa_editar'),
    path(
        'tarefas/<int:pk>/excluir/',
        views.em_construcao,
        name='tarefa_excluir',
    ),
]
