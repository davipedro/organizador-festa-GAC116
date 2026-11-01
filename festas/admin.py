from django.contrib import admin

from .models import TipoFesta


@admin.register(TipoFesta)
class TipoFestaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)
