# Projeto: o impacto da música na saúde dos alunos

Esse é o projeto da disciplina ECOX14. A ideia é montar um pipeline de dados
em três camadas (bronze, prata e ouro) e documentar aqui tudo que eu for
descobrindo e decidindo no caminho.

## Minha pergunta

Eu quero entender **como a música afeta a saúde dos alunos** — tanto o corpo,
enquanto a pessoa está praticando um instrumento, quanto a mente, no hábito
do dia a dia de ouvir música.

Pra isso eu uso duas fontes diferentes, porque nenhuma das duas sozinha
responde isso direito:

- **Música**: dados de alunos praticando instrumento (violão, violino,
  piano), com coisas como precisão, ritmo, foco, batimento cardíaco, pressão
  e nível de estresse durante a prática. Isso me mostra o lado físico.
- **MxMH (Music & Mental Health Survey)**: uma pesquisa com 736 pessoas sobre
  hábito de escutar música (quantas horas por dia, que gênero, etc.) e sobre
  como elas se sentem em relação a ansiedade, depressão, insônia e TOC. Isso
  me mostra o lado mental.

As duas fontes não têm as mesmas pessoas, então eu não consigo cruzar aluno
por aluno — mas dá pra comparar os padrões gerais de uma com os da outra.

## De onde vieram os dados

| Fonte | Formato | Como peguei | Quando | Quantas linhas |
|---|---|---|---|---|
| Música | CSV | arquivo que recebi pronto | 24/09/2026 | 100 |
| MxMH | CSV | arquivo que recebi pronto | 01/10/2026 | 736 |

## O que eu encontrei de errado (ou não) em cada fonte

### Música
Essa fonte veio bem limpa, pra ser sincero. Rodei o relatório automático
(`fg-data-profiling`) e:
- Não tem nenhum valor faltando em nenhuma das 22 colunas.
- Não tem linha duplicada, nem `Student_ID` repetido.
- O relatório não achou nenhuma correlação estranha nem coluna redundante.
  Os 12 alertas que ele deu são todos do tipo "essa coluna tem valores
  únicos", que é normal pra coluna de medição.

Mesmo assim achei duas coisas que o relatório sozinho não ia me contar:

- O `Timestamp` tem só 94 valores diferentes em 100 linhas — ou seja, 5
  pares de alunos foram registrados exatamente no mesmo minuto. Não sei se
  é coincidência (a amostra é pequena) ou se é algo de como o dado foi
  gerado. Deixei do jeito que está, só anotando aqui.
- `Stress_Level`, `Engagement_Level`, `Skill_Development` e
  `Behavioral_Patterns` chegam como número (tipo `int64`), mas na verdade
  são escalas limitadas (de 1 a 10, por exemplo) que têm uma ordem. O
  pandas não sabe disso sozinho, então mais na frente eu preciso dizer pra
  ele que isso é uma categoria com ordem, não só um número qualquer.

Os valores também fazem sentido pro domínio: idade entre 10 e 17 anos (são
alunos mesmo), porcentagens entre 0 e 100, batimento e pressão dentro do
que é fisiologicamente possível. Nada fora da faixa.

### MxMH
Essa fonte já tem defeito de verdade, então deu mais trabalho:

- Tem valor faltando em 8 colunas: `Age` (1), `Primary streaming service`
  (1), `While working` (3), `Instrumentalist` (4), `Composer` (1),
  `Foreign languages` (4), `BPM` (107 — isso é 14,5% da coluna!) e `Music
  effects` (8).
- Não tem linha duplicada inteira, só um `Timestamp` repetido, mas isso é
  coincidência (são pessoas diferentes).
- A coluna `Permissions` só tem um valor possível (`"I understand."`) nas
  736 linhas. Ou seja, ela não me diz nada — é tipo uma coluna "decorativa".
- **O `BPM` tem erro grande:** tem gente com BPM igual a 0, 4, 8, e teve um
  caso de **999999999**. Isso é impossível pra tempo de música. O relatório
  automático também avisou que essa coluna está muito torta (bem
  assimétrica), o que faz sentido com esse valor absurdo lá dentro.
- `Anxiety` e `Depression` são bem correlacionadas entre si, e `Frequency
  [Hip hop]` com `Frequency [Rap]` também. Isso não é erro — faz sentido
  ansiedade e depressão andarem juntas, e quem gosta de hip hop costuma
  gostar de rap também.
- Os zeros em `Anxiety`, `Depression`, `Insomnia` e `OCD` não são valor
  faltando — a escala vai de 0 a 10, e 0 é uma resposta válida (a pessoa
  disse que não sente nada daquilo).
- Essa fonte não tem nenhum identificador de pessoa, porque é uma pesquisa
  anônima.
- A coluna `Music effects` é bem importante pro meu projeto: é a própria
  pessoa dizendo se a música melhora, piora ou não muda nada na saúde
  mental dela.

## O que eu decidi fazer com cada defeito

### Música
- Tirei espaço sobrando dos nomes de coluna e dos textos (não achei nenhum,
  mas rodei a função assim mesmo, por garantia).
- Conferi a chave: `Student_ID` é único nas 100 linhas, então uso ela como
  identificador.
- Falei pro pandas que `Class_Level` tem ordem (`Beginner` < `Intermediate`
  < `Advanced`) e que `Skill_Development` também (de 1 a 5).
- Uma coisa que descobri na marra: quando eu salvo em Parquet e leio de
  novo, a coluna `Skill_Development` volta como número comum, perdendo a
  ordem que eu tinha declarado. Isso não acontece com `Class_Level`, que é
  texto. Parece que o Parquet não guarda bem categoria feita de número
  inteiro. Deixei anotado aqui pra não esquecer — se for usar essa coluna
  depois, talvez precise tipar de novo.
- `Gender`, `Lesson_Type` e `Instrument_Type` virraram categoria também, só
  que sem ordem (não faz sentido dizer que "Piano" é maior que "Violão").
- O `Timestamp` virou data de verdade, com hora e minuto, porque a fonte já
  trazia isso — não é uma data inventada, é um dado que já existia.
- Procurei valor extremo em 12 colunas numéricas, usando dois jeitos
  diferentes (IQR e z-score). **Nenhum dos dois achou nada estranho.**
  Deixei as colunas marcando isso mesmo assim (tudo `False`), pra manter o
  padrão do projeto.
- Conferi se os valores faziam sentido pra faixa esperada (idade, batimento,
  pressão etc) e não achei nenhum erro comprovado. Não tirei nenhuma linha.
- Resultado: comecei com 100 linhas e terminei com 100.

### MxMH
- Tirei espaço sobrando (de novo, não tinha nada, mas rodei mesmo assim).
- Essa fonte não tem identificador de pessoa, então eu **criei um na mão**:
  `respondente_id` (tipo `R0001`, `R0002`...). É só um número pra eu poder
  identificar a linha dentro do meu projeto, não significa nada sobre a
  pessoa de verdade.
- Tirei a coluna `Permissions` porque ela só tinha um valor possível e não
  ajudava em nada.
- As colunas de Sim/Não virraram um tipo booleano especial do pandas (que
  aceita valor faltando) em vez de `True`/`False` comum — se eu usasse o
  comum, o pandas ia esconder os valores faltando sem eu perceber.
- As 16 colunas de `Frequency [...]` (uma pra cada gênero musical) viraram
  categoria com ordem: Never < Rarely < Sometimes < Very frequently.
- `Music effects` também virou categoria com ordem (Worsen < No effect <
  Improve), porque essa é a coluna mais importante do projeto.
- O `Timestamp` virou data, mas precisei dizer pro pandas exatamente o
  formato (mês/dia/ano), porque senão ele ficaria em dúvida se "8/27/2022"
  é 27 de agosto ou alguma coisa impossível.
- Os valores faltando eu **não inventei**. Deixei como estão e só marquei
  que faltam, porque não tenho como saber o que a pessoa responderia.
- Procurei extremo nas 7 colunas numéricas. `Age` e `Hours per day` tiveram
  bastante gente marcada (59 e 40 pessoas), mas isso não é erro — é porque
  a maioria é jovem e tem pouca gente mais velha, então a distribuição é
  torta mesmo. Deixei marcado, não tirei ninguém.
- Já o `BPM` eu realmente **tirei 7 linhas**, porque os valores (0, 4, 8,
  999999999, 624...) são impossíveis pra tempo de música de verdade — isso
  não é estatística achando outlier, é eu sabendo que música não tem 300
  milhões de BPM.
- Resultado: comecei com 736 linhas e terminei com 729.

## Colunas que eu criei (atributos derivados)

### Da fonte Música

**precisao_por_minuto** — pego a precisão (`Accuracy`) e divido pelo tempo de
prática em minutos. Serve pra comparar aluno que praticou pouco com aluno
que praticou muito, sem a duração sozinha definir quem "foi melhor".

**faixa_etaria** — separei os alunos em três grupos por idade (10-12, 13-15,
16-17). Assim dá pra comparar por fase, sem assumir que idade afeta tudo de
forma igual e constante.

**desempenho_quartil** — dividi os alunos em 4 grupos de tamanho igual
conforme o `Performance_Score` (baixo, médio-baixo, médio-alto, alto). A
diferença pra faixa etária é que aqui eu não escolhi os limites, o próprio
pandas dividiu pra cada grupo ficar com 25% dos alunos.

### Da fonte MxMH

**horas_relativas_idade** — horas de escuta por dia dividido pela idade.
Ideia parecida com a de precisão por minuto: compara gente de idade muito
diferente sem deixar "quem tem mais tempo livre" ganhar sempre.

**faixa_etaria** — agrupei em adolescente, jovem adulto, adulto e acima de
40. Os limites eu escolhi pensando no assunto, não no tamanho dos grupos.

**indice_sofrimento_mental** — fiz a média de `Anxiety`, `Depression`,
`Insomnia` e `OCD`, já que as quatro usam a mesma escala de 0 a 10. Isso não
é exatamente uma das ideias que vi no material da disciplina (razão, faixa,
etc), mas resolvi criar mesmo assim porque junta quatro números numa coisa
só, e é a coluna que mais se conecta com a minha pergunta sobre saúde
mental.

## Qual é a chave de cada fonte

- Música: `Student_ID` (já veio na fonte, só conferi que não repete).
- MxMH: `respondente_id` (eu que criei, porque a pesquisa é anônima).

## O que ainda falta pensar pra camada Ouro

Como as duas fontes não têm as mesmas pessoas, não dá pra simplesmente
juntar (`join`) linha com linha. O que dá pra fazer é comparar os *padrões*:
por exemplo, ver se o nível de estresse de quem pratica instrumento
(`Stress_Level`, da fonte Música) parece diferente do nível de sofrimento de
quem só escuta música (`indice_sofrimento_mental`, da fonte MxMH). Isso
ainda não fiz — é modelagem, fica pra próxima etapa.

## O que sobe pro GitHub e o que não sobe

| Sobe | Não sobe |
|---|---|
| Os scripts (`src/*.py`) | Os arquivos `.parquet` da prata (o script recria) |
| `README.md`, `.gitignore`, `requirements.txt` | A pasta `relatorios/` (o script recria) |
| Os CSVs da bronze (se a fonte sumir, não tenho como recuperar) | `.venv/` |
| Os arquivos de proveniência da bronze | |
| O arquivo de proveniência da prata (é histórico, não dá pra recriar igual) | |

## Como eu rodo o projeto

```bash
python -m venv .venv
source .venv/bin/activate          # no Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

python src/ingerir_musica.py       # traz a fonte musica pra bronze
python src/ingerir_mxmh.py         # traz a fonte mxmh pra bronze

python src/explorar.py musica      # gera o relatório da fonte musica
python src/explorar.py mxmh        # gera o relatório da fonte mxmh
python src/explorar.py todas       # gera os dois de uma vez

python src/transformar_musica.py   # gera a prata da fonte musica
python src/transformar_mxmh.py     # gera a prata da fonte mxmh
```
