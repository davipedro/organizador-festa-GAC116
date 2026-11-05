# Diagrama ER

```mermaid
erDiagram
    Usuario ||--o{ Festa : organiza
    TipoFesta ||--o{ Festa : classifica
    Festa ||--o{ Convidado : tem
    Festa ||--o{ Tarefa : tem

    Usuario {
        int id PK
        string username UK
        string email
        string first_name
        string last_name
        boolean is_staff
        boolean is_active
    }
    TipoFesta {
        int id PK
        string nome UK
    }
    Festa {
        int id PK
        int dono_id FK
        int tipo_id FK
        string nome
        date data
        time horario
        string local
        text descricao
        decimal orcamento_estimado
        decimal custo_medio_por_pessoa
    }
    Convidado {
        int id PK
        int festa_id FK
        string nome
        string contato
        string status
    }
    Tarefa {
        int id PK
        int festa_id FK
        string titulo
        boolean concluida
    }
```

## Como ler

- `||--o{` significa "um para muitos": um usuário organiza muitas festas.
- `PK` é a chave primária, `UK` é um valor único e `FK` é a chave estrangeira.

## Regras de exclusão

- Apagar um **usuário** apaga as festas dele (cascata).
- Um **tipo de festa** que tem festas não pode ser apagado (protegido).
- Apagar uma **festa** apaga os convidados e as tarefas dela (cascata).