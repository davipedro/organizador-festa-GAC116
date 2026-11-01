from django.contrib import admin

from .models import Convidado, Festa, Tarefa, TipoFesta


class StatusConvidadoFilter(admin.SimpleListFilter):
    """Filtra as festas que têm convidados com um certo status."""

    title = 'status dos convidados'
    parameter_name = 'status_convidado'

    def lookups(self, request, model_admin):
        return Convidado.Status.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(convidados__status=self.value()).distinct()
        return queryset


@admin.register(TipoFesta)
class TipoFestaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)


@admin.register(Festa)
class FestaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'data', 'horario', 'local', 'dono')
    list_filter = ('tipo', 'data', StatusConvidadoFilter)
    search_fields = ('nome', 'local', 'dono__username', 'dono__first_name')
    date_hierarchy = 'data'


@admin.register(Convidado)
class ConvidadoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'festa', 'status', 'contato')


@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'festa', 'concluida')
