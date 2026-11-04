# Dicionário de dados

O banco tem 5 tabelas. Os nomes batem com `contas/models.py` e `festas/models.py`.

## contas_usuario

Herda do usuário padrão do Django; aqui estão os campos usados pelo projeto.

| Campo | Tipo | Obrigatório | Padrão | Descrição |
|---|---|---|---|---|
| id | inteiro, chave primária | sim | automático | Identificador do usuário |
| username | texto (150), único | sim | nenhum | Nome de login, não se repete |
| email | texto (254) | não | vazio | E-mail de contato do usuário |
| first_name | texto (150) | não | vazio | Primeiro nome |
| last_name | texto (150) | não | vazio | Sobrenome |
| is_staff | verdadeiro ou falso | sim | falso | Indica se pode entrar no admin |
| is_active | verdadeiro ou falso | sim | verdadeiro | Indica se a conta está ativa |

## festas_tipofesta

| Campo | Tipo | Obrigatório | Padrão | Descrição |
|---|---|---|---|---|
| id | inteiro, chave primária | sim | automático | Identificador do tipo |
| nome | texto (60), único | sim | nenhum | Nome da categoria, como Churrasco ou Aniversário |

## festas_festa

| Campo | Tipo | Obrigatório | Padrão | Descrição |
|---|---|---|---|---|
| id | inteiro, chave primária | sim | automático | Identificador da festa |
| dono_id | chave estrangeira para contas_usuario | sim | nenhum | Usuário que organiza a festa; apagar o usuário apaga a festa |
| tipo_id | chave estrangeira para festas_tipofesta | sim | nenhum | Categoria da festa; um tipo em uso não pode ser apagado |
| nome | texto (120) | sim | nenhum | Nome da festa, como aparece nas listas |
| data | data | sim | nenhum | Dia em que a festa acontece |
| horario | hora | sim | nenhum | Hora em que a festa começa |
| local | texto (200) | sim | nenhum | Endereço ou nome do lugar |
| descricao | texto longo | não | vazio | Detalhes e observações sobre a festa |
| orcamento_estimado | decimal (10,2) | sim | 0 | Valor total previsto para gastar; não aceita negativo |
| custo_medio_por_pessoa | decimal (8,2) | sim | 0 | Gasto médio por convidado; não aceita negativo |

## festas_convidado

| Campo | Tipo | Obrigatório | Padrão | Descrição |
|---|---|---|---|---|
| id | inteiro, chave primária | sim | automático | Identificador do convidado |
| festa_id | chave estrangeira para festas_festa | sim | nenhum | Festa para a qual a pessoa foi convidada; apagar a festa apaga o convidado |
| nome | texto (120) | sim | nenhum | Nome do convidado |
| contato | texto (120) | não | vazio | Telefone ou e-mail para falar com o convidado |
| status | texto (10) | sim | pendente | Resposta do convite: pendente, vou, talvez ou nao_vou |

## festas_tarefa

| Campo | Tipo | Obrigatório | Padrão | Descrição |
|---|---|---|---|---|
| id | inteiro, chave primária | sim | automático | Identificador da tarefa |
| festa_id | chave estrangeira para festas_festa | sim | nenhum | Festa a que a tarefa pertence; apagar a festa apaga a tarefa |
| titulo | texto (160) | sim | nenhum | O que precisa ser feito, como "Comprar bebidas" |
| concluida | verdadeiro ou falso | sim | falso | Indica se a tarefa já foi feita |