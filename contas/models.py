from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):
    """Usuário do sistema.

    Herda tudo do usuário padrão do Django (login, senha, nome, e-mail,
    permissões). Fica como modelo próprio para podermos acrescentar campos
    depois sem precisar refazer o banco.
    """
