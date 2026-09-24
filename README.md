# Projeto: desempenho de alunos em aulas de música

Pipeline de dados em três camadas (bronze, prata, ouro), construído passo a
passo seguindo a disciplina ECOX14 — Engenharia de Dados na Prática.

**Pergunta norteadora (assumida para este exemplo — ajuste para a sua):**
Quais fatores de prática (duração, foco, ritmo, instrumento) se associam a
maior desempenho e engajamento dos alunos, e como o estresse entra nisso?

## Fontes de dados

| Fonte | Formato | Acesso | Extraído | Registros |
|---|---|---|---|---|
| Música (arquivo do usuário) | CSV | arquivo recebido | 24/09/2026 | 100 |

## Defeitos conhecidos das fontes

### Música
- Nenhum valor ausente em nenhuma das 22 colunas (`df.isna().sum()` = 0 em tudo).
- Nenhuma linha duplicada e nenhum `Student_ID` repetido.
- O relatório automatizado (`fg-data-profiling`) não acusou nenhuma correlação alta,
  nenhum zero suspeito e nenhuma coluna redundante — os 12 alertas gerados são todos
  do tipo "valores únicos", esperado para colunas de medição contínua.
- **Consistência a observar, não um erro:** `Timestamp` tem apenas 94 valores únicos
  em 100 linhas — 5 pares de alunos foram registrados no mesmo minuto exato. Pode ser
  coincidência de uma amostra pequena ou um artefato de geração dos dados; mantido
  sem alteração, sinalizado aqui para quem for usar a coluna como identificador de evento.
- **Tipos frouxos (Aula 6):** `Stress_Level`, `Engagement_Level` (1–10),
  `Skill_Development` (1–5) e `Behavioral_Patterns` (0–2) chegam como `int64`, mas são
  escalas limitadas e ordenadas — o pandas não sabe disso e trataria `10` como maior
  que `9` só por acaso serem números, não porque declaramos uma ordem.
- Faixas de valor plausíveis: `Age` entre 10 e 17, `Accuracy`/`Rhythm`/`Pitch_Accuracy`/
  `Volume` entre 0 e 100 (formato percentual), `Heart_Rate` e `Blood_Pressure` dentro de
  faixas fisiológicas humanas. Nenhum valor fora do que o domínio permite.

## Decisões de tratamento

### Música
- Espaços removidos de nomes de coluna e de textos (nenhum encontrado — função rodada
  por padronização, não porque havia defeito).
- Chave conferida: `Student_ID` é único nas 100 linhas. É a chave declarada do projeto.
- `Class_Level` tipado como categoria **ordenada** (`Beginner < Intermediate < Advanced`).
- `Skill_Development` tipado como categoria ordenada (1 a 5). **Atenção:** ao gravar em
  Parquet, essa coluna específica volta como `int64` na releitura — categorias inteiras
  não são preservadas pelo `pyarrow` nesta versão, diferente de categorias em texto
  (`Class_Level`, `Gender` voltam corretas como `category`). Documentado aqui para quem
  reusar a Prata: reaplique `tipar_colunas()` se precisar da ordem categórica de volta.
- `Gender`, `Lesson_Type`, `Instrument_Type` tipados como categoria (sem ordem natural).
- `Timestamp` convertido para `datetime` com formato explícito (`%Y-%m-%d %H:%M:%S`).
  Diferente do exemplo do Banco Mundial na Aula 6, aqui a conversão é legítima: a fonte
  já trazia hora e minuto, então nenhuma precisão falsa foi acrescentada.
- Valores extremos marcados por IQR e por z-score em 12 colunas numéricas.
  **Resultado: nenhuma das duas técnicas marcou nenhum valor como extremo.** As colunas
  de sinalização (`*_extremo_iqr`, `*_extremo_z`) foram mantidas na Prata mesmo assim,
  por padronização do pipeline — todas vêm com `False` nesta versão dos dados.
- Faixas de domínio conferidas (não estatística) em `Age`, `Accuracy`, `Rhythm`,
  `Pitch_Accuracy`, `Volume`, `Heart_Rate`, `Blood_Pressure`: **nenhum erro comprovado
  encontrado.** Nenhuma linha removida.
- Linhas antes: 100. Linhas depois: 100.

## Atributos derivados

### precisao_por_minuto
`Accuracy / (Duration em minutos)`. Família razão/taxa. Serve para comparar o
aproveitamento de alunos que praticaram por tempos diferentes — sem isso, uma sessão
mais longa parece "melhor" só por durar mais.

### faixa_etaria
Corte de `Age` em três blocos (`10-12`, `13-15`, `16-17`) por regra de domínio (`cut`),
não por quantidade de casos. Serve para comparar desempenho por estágio de
desenvolvimento sem assumir que o efeito da idade é linear.

### desempenho_quartil
Quartil de `Performance_Score` (`qcut`, um quarto dos alunos por faixa: baixo,
médio-baixo, médio-alto, alto). Serve para comparar grupos de tamanho parecido, ao
contrário de `faixa_etaria`, que usa limites fixos de domínio — a diferença entre
`cut` e `qcut` discutida na Aula 6.

## Chave da fonte

`Student_ID` — identificador do aluno, único por definição nesta amostra.

## O que sobe para o repositório

| Sobe | Não sobe |
|---|---|
| `src/*.py` — o código que reconstrói tudo | `dados/prata/musica.parquet` — um comando refaz |
| `README.md`, `.gitignore`, `requirements.txt` | `relatorios/` — o HTML do profiling, o script refaz |
| `dados/bronze/musica/*.csv` — insubstituível se a fonte sumir | `.venv/` |
| `dados/bronze/musica/proveniencia.jsonl` | |
| `dados/prata/proveniencia.jsonl` — registro histórico, não se reconstrói igual | |

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

python src/ingerir_musica.py       # cria a bronze datada + proveniência
python src/explorar.py             # gera relatorios/<arquivo>.html (Aula 4)
python src/transformar_musica.py   # gera dados/prata/musica.parquet (Aulas 5 e 6)
```
