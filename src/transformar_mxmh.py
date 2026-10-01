import json
from datetime import datetime
from pathlib import Path
import pandas as pd
import limpeza

BRONZE = Path("dados/bronze/mxmh")
PRATA = Path("dados/prata")
PADRAO = "mxmh_*.csv"

COLUNAS_SIM_NAO = [
    "While working", "Instrumentalist", "Composer",
    "Exploratory", "Foreign languages",
]

COLUNAS_FREQUENCIA = [c for c in [
    "Frequency [Classical]", "Frequency [Country]", "Frequency [EDM]",
    "Frequency [Folk]", "Frequency [Gospel]", "Frequency [Hip hop]",
    "Frequency [Jazz]", "Frequency [K pop]", "Frequency [Latin]",
    "Frequency [Lofi]", "Frequency [Metal]", "Frequency [Pop]",
    "Frequency [R&B]", "Frequency [Rap]", "Frequency [Rock]",
    "Frequency [Video game music]",
]]

ORDEM_FREQUENCIA = ["Never", "Rarely", "Sometimes", "Very frequently"]
ORDEM_EFEITO = ["Worsen", "No effect", "Improve"]

BPM_MIN, BPM_MAX = 20, 300

COLUNAS_NUMERICAS_CHECAR = [
    "Age", "Hours per day", "BPM", "Anxiety", "Depression", "Insomnia", "OCD",
]

#Funcao responsavel por carregar o arquivo CSV mais recente da camada bronze
def carregar():
    arquivos = sorted(BRONZE.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError(f"nada em {BRONZE}")
    caminho = arquivos[-1]
    df = pd.read_csv(caminho)
    print("lido:", caminho.name, df.shape)
    return df, caminho

#Funcao responsavel por criar uma chave identificadora unica para cada respondente
def criar_chave(df):
    df = df.reset_index(drop=True)
    df.insert(0, "respondente_id", ["R" + str(i + 1).zfill(4) for i in df.index])
    return df

#Funcao responsavel por remover colunas sem variabilidade que nao agregam informacao
def remover_coluna_constante(df, coluna="Permissions"):
    if coluna in df.columns:
        print(f"removendo coluna constante: {coluna} ({df[coluna].nunique()} valor unico)")
        df = df.drop(columns=[coluna])
    return df

#Funcao responsavel por converter os tipos das colunas para booleano, categoricas ordenadas e datetime
def tipar_colunas(df):
    for c in COLUNAS_SIM_NAO:
        df[c] = df[c].map({"Yes": True, "No": False}).astype("boolean")

    df["Fav genre"] = df["Fav genre"].astype("category")
    df["Primary streaming service"] = df["Primary streaming service"].astype("category")

    for c in COLUNAS_FREQUENCIA:
        antes = df[c].isna().sum()
        df[c] = pd.Categorical(df[c], categories=ORDEM_FREQUENCIA, ordered=True)
        extra = df[c].isna().sum() - antes
        if extra:
            print(f"{c}: {extra} valor(es) fora da escala viraram ausente")

    antes = df["Music effects"].isna().sum()
    df["Music effects"] = pd.Categorical(df["Music effects"], categories=ORDEM_EFEITO, ordered=True)
    print("Music effects ausentes (originais + fora de escala):", df["Music effects"].isna().sum())
    if df["Music effects"].isna().sum() != antes:
        print("  (nenhum valor novo caiu fora da escala; a diferenca e so a original)")

    # Timestamp no formato mes/dia/ano - ambiguo sem declarar o formato.
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], format="%m/%d/%Y %H:%M:%S")

    return df

#Funcao responsavel por verificar as colunas que estao fora do limite usando as funcoes de limpeza.py
def checar_extremos(df):
    for c in COLUNAS_NUMERICAS_CHECAR:
        df = limpeza.marcar_extremos(df, c)
        df = limpeza.marcar_zscore(df, c)
        n_iqr = df[c + "_extremo_iqr"].sum()
        n_z = df[c + "_extremo_z"].sum()
        print(f"{c}: IQR={n_iqr} | z-score={n_z}")
    return df

#Funcao responsavel por remover os erros encontrados na funcao anterior
def remover_erros_comprovados(df):
    df_bpm_ausente = df[df["BPM"].isna()]
    df_bpm_presente = df[df["BPM"].notna()]
    print("BPM", end=" - ")
    df_bpm_presente = limpeza.remover_erros(df_bpm_presente, "BPM", BPM_MIN, BPM_MAX)
    return pd.concat([df_bpm_presente, df_bpm_ausente]).sort_index()

#Funcao responsavel por calcular a proporcao de horas de musica ouvidas em relacao a idade
def horas_relativas_idade(df):
    df["horas_relativas_idade"] = df["Hours per day"] / df["Age"]
    return df

#Funcao responsavel por categorizar os respondentes em faixas etarias predefinidas
def faixa_etaria(df):
    df["faixa_etaria"] = pd.cut(
        df["Age"], bins=[9, 17, 25, 40, 100],
        labels=["adolescente", "jovem_adulto", "adulto", "acima_40"],
    )
    return df

#Funcao responsavel por calcular o indice medio de saude mental a partir das métricas de sofrimento
def indice_sofrimento_mental(df):
    df["indice_sofrimento_mental"] = df[["Anxiety", "Depression", "Insomnia", "OCD"]].mean(axis=1)
    return df

#Funcao responsavel por salvar os resultados no arquivo parquet na camada PRATA
def salvar(df):
    PRATA.mkdir(parents=True, exist_ok=True)
    destino = PRATA / "mxmh.parquet"
    df.to_parquet(destino, index=False)
    print("salvo em:", destino, df.shape)
    return destino

#Funcao responsavel por registrar tudo no arquivo jsonl proveniencia da camada PRATA
def registrar(origem, destino, antes, depois, decisoes):
    info = {
        "origem": origem.name,
        "arquivo_prata": destino.name,
        "linhas_antes": antes,
        "linhas_depois": depois,
        "decisoes": decisoes,
        "transformado_em": datetime.now().isoformat(timespec="seconds"),
    }
    caminho = PRATA / "proveniencia.jsonl"
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")


def main():
    df, origem = carregar()
    antes = len(df)

    df = limpeza.tirar_espacos(df)
    df = criar_chave(df)
    df = remover_coluna_constante(df)
    df = tipar_colunas(df)
    df = checar_extremos(df)
    df = remover_erros_comprovados(df)
    df = horas_relativas_idade(df)
    df = faixa_etaria(df)
    df = indice_sofrimento_mental(df)

    destino = salvar(df)
    registrar(origem, destino, antes, len(df), [
        "espacos removidos de colunas e textos",
        "chave substituta 'respondente_id' criada (pesquisa anonima, sem id natural)",
        "coluna 'Permissions' removida: valor constante, sem informacao",
        "colunas Sim/No convertidas para booleano",
        "16 colunas de Frequency tipadas como categoria ordenada (Never..Very frequently)",
        "Music effects tipada como categoria ordenada (Worsen..Improve)",
        "Timestamp convertido para datetime com formato explicito (mes/dia/ano)",
        "ausentes em While working, Instrumentalist, Composer, Foreign languages, "
        "Primary streaming service, Age e Music effects: mantidos e sinalizados, nao preenchidos",
        "extremos marcados por IQR e z-score, nao removidos (exceto BPM, ver abaixo)",
        f"BPM fora da faixa {BPM_MIN}-{BPM_MAX}: removido por erro comprovado de dominio",
        "atributo derivado: horas_relativas_idade (razao)",
        "atributo derivado: faixa_etaria (faixa por corte de dominio)",
        "atributo derivado: indice_sofrimento_mental (combinacao de colunas)",
    ])


if __name__ == "__main__":
    main()
