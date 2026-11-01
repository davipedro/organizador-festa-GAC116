from django.contrib import admin

from .models import Convidado, Festa, TipoFesta


@admin.register(TipoFesta)
class TipoFestaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)


@admin.register(Festa)
class FestaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'data', 'horario', 'local', 'dono')


@admin.register(Convidado)
class ConvidadoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'festa', 'status', 'contato')
