from django.contrib.auth.forms import UserCreationForm

from .models import Usuario


class CadastroForm(UserCreationForm):
    """Cadastro público: só cria usuário comum (anfitrião).

    Os campos de permissão (is_staff, is_superuser) não fazem parte do
    formulário, então nada que venha no POST consegue ligá-los.
    """

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nome in ('email', 'first_name', 'last_name'):
            self.fields[nome].required = True
