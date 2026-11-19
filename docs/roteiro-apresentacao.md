# Roteiro da apresentação (Checkpoint 2)

Duração prevista: cerca de 8 minutos. Quem conduz a tela: Davi. Quem fala da interface: Vinícius.

## Antes de começar

1. Banco novo e dados de exemplo:

   ```bash
   python manage.py migrate
   python manage.py loaddata dados_exemplo
   python manage.py runserver
   ```

2. Navegador em `http://127.0.0.1:8000/`, sem ninguém logado, no tema claro.
3. Uma segunda janela anônima aberta, para o teste de permissão.
4. Usuários: `ana`, `bruno` e `admin`, todos com a senha `demo12345`.

## Fluxo

| # | O que mostrar | O que dizer |
|---|---|---|
| 1 | Abrir `/`. O site manda para o login. | A área do usuário exige login. |
| 2 | Clicar em "Cadastre-se" e criar um usuário novo (ex.: `davi_demo`). | Cadastro com validação de senha. Só cria anfitrião comum, nunca administrador. Depois do cadastro, o usuário já entra logado. |
| 3 | Na lista vazia, criar uma festa (nome, tipo, data, horário, local, orçamento R$ 500, custo por pessoa R$ 50). | Cada festa pertence ao usuário que a criou. |
| 4 | No detalhe, adicionar 3 convidados e mudar o status de dois para "Vou". | Os convidados ficam na mesma tela e atualizam sem recarregar a página. |
| 5 | Mostrar o custo estimado e marcar mais convidados como "Vou" até passar de R$ 500. | Custo = custo por pessoa × confirmados. Ao passar do orçamento aparece o aviso. |
| 6 | Adicionar duas tarefas e marcar uma como concluída. | Lista de preparativos com barra de progresso. |
| 7 | Tentar excluir um convidado ou a festa e ler a confirmação. | Antes de excluir a festa, o sistema avisa quantos convidados e tarefas vão junto. |
| 8 | Sair e entrar como `ana`. Na lista, usar a busca ("aniversário"), o filtro de tipo e o de período. | Cards com confirmados e custo. Filtros combináveis. |
| 9 | Alternar para o tema escuro e recarregar a página. | O tema escuro fica salvo no navegador. Layout responsivo com Bootstrap: diminuir a janela para mostrar. |
| 10 | Copiar o endereço de uma festa do `bruno` (ex.: `/festas/2/`) e abrir logado como `ana`. | Resposta 404: um anfitrião nunca vê as festas de outro. |
| 11 | Abrir `/contas/perfil/`. | Tela de perfil com os dados do usuário. |
| 12 | Sair. Entrar em `/admin/` como `admin`. Mostrar a lista de festas com filtros, busca e a coluna de confirmados, e abrir uma festa com convidados e tarefas na mesma página. | O mesmo banco é gerenciado pelo ambiente administrativo, com tema Jazzmin e filtros. |

## Pontos a destacar (critérios do professor)

- **Login, logout e cadastro:** passos 1, 2 e 8. O logout é por POST.
- **Banco integrado ao admin:** passo 12. Os dados criados no site aparecem no admin.
- **Framework CSS e interface amigável:** Bootstrap 5.3.3 local, passos 9 e 4.
- **Documentação:** README com instalação, execução, funcionalidades, rotas e estrutura.
- **Complexidade:** permissão por dono, custo calculado, filtros, atualização sem recarregar, 136 testes automatizados.

## Perguntas prováveis

- **Por que 404 e não 403 na festa de outro usuário?** Para não revelar que a festa existe.
- **Onde está o cálculo do custo?** Propriedades `confirmados`, `custo_estimado` e `acima_do_orcamento` no modelo `Festa`.
- **O Bootstrap vem de CDN?** Não, está em `static/vendor/bootstrap`, então funciona sem internet no laboratório.
- **Quem é administrador?** Só quem é criado por `createsuperuser` ou pelos dados de exemplo. O cadastro do site nunca dá acesso ao admin.

## Se algo der errado

- Banco bagunçado: apagar `db.sqlite3` e repetir `migrate` e `loaddata dados_exemplo`.
- Sem internet no laboratório: nada depende dela.
- Porta ocupada: `python manage.py runserver 8001`.
