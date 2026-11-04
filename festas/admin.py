from django.contrib import admin
from django.db.models import Count, Q

from .models import Convidado, Festa, Tarefa, TipoFesta


class StatusConvidadoFilter(admin.SimpleListFilter):
    """Filtra as festas que têm convidados com um certo status."""

    title = 'status dos convidados'
    parameter_name = 'status_convidado'

    def lookups(self, request, model_admin):
        return Convidado.Status.choices

    def queryset(self, request, queryset):
        if self.value():
            # subconsulta em vez de join: não repete a festa quando ela tem
            # vários convidados com o mesmo status e não altera a contagem
            com_status = Convidado.objects.filter(status=self.value())
            return queryset.filter(pk__in=com_status.values('festa_id'))
        return queryset


@admin.register(TipoFesta)
class TipoFestaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'total_festas')
    search_fields = ('nome',)
    ordering = ('nome',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            qtd_festas=Count('festas')
        )

    @admin.display(description='festas', ordering='qtd_festas')
    def total_festas(self, obj):
        return obj.qtd_festas


class ConvidadoInline(admin.TabularInline):
    model = Convidado
    extra = 1


class TarefaInline(admin.TabularInline):
    model = Tarefa
    extra = 1


@admin.register(Festa)
class FestaAdmin(admin.ModelAdmin):
    list_display = (
        'nome', 'tipo', 'data', 'horario', 'local', 'dono', 'confirmados'
    )
    list_filter = ('tipo', 'data', StatusConvidadoFilter)
    search_fields = ('nome', 'local', 'dono__username', 'dono__first_name')
    date_hierarchy = 'data'
    inlines = [ConvidadoInline, TarefaInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            total_confirmados=Count(
                'convidados',
                filter=Q(convidados__status=Convidado.Status.VOU),
            )
        )

    @admin.display(description='confirmados', ordering='total_confirmados')
    def confirmados(self, obj):
        return obj.total_confirmados


@admin.register(Convidado)
class ConvidadoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'festa', 'status', 'contato')
    list_filter = ('status', 'festa')
    search_fields = ('nome', 'contato', 'festa__nome')
    ordering = ('festa', 'nome')


@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'festa', 'concluida')
    list_filter = ('concluida', 'festa')
    search_fields = ('titulo', 'festa__nome')
    ordering = ('festa', 'concluida', 'titulo')
