## Fontes de dados

| Fonte | Formato | Acesso | Extraido | Link |
| --- | --- | --- | --- | --- |
| Music | CSV | token | 20/08/2026 | kaggle.com/... |
| Banco Mundial | JSON | aberto | 20/08/2026 | api.worldbank.org/... |

## Defeitos conhecidos das fontes

- A API do Banco Mundial devolve agregados regionais junto com os paises.

## Decisoes de tratamento

### Banco Mundial
- Espacos removidos de nomes de coluna e de texto.
- Agregados regionais separados: N linhas retiradas.
  Motivo: granularidade diferente da dos paises.
- Longitude e latitude convertidas para numero.
  Vazios viraram ausentes: N ocorrencias.
- Capital vazia mantida. Nao se aplica a agregados.