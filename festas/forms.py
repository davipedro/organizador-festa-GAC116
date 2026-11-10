from django import forms

from .models import Festa


class FestaForm(forms.ModelForm):
    """Formulário da festa. O dono não aparece: é sempre o usuário logado."""

    class Meta:
        model = Festa
        fields = (
            'nome',
            'tipo',
            'data',
            'horario',
            'local',
            'descricao',
            'orcamento_estimado',
            'custo_medio_por_pessoa',
        )
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'horario': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'orcamento_estimado': forms.NumberInput(
                attrs={'step': '0.01', 'min': '0'}
            ),
            'custo_medio_por_pessoa': forms.NumberInput(
                attrs={'step': '0.01', 'min': '0'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            classe = 'form-select' if isinstance(
                campo.widget, forms.Select
            ) else 'form-control'
            campo.widget.attrs['class'] = classe
