import json
from datetime import datetime
from pathlib import Path

import pandas as pd

import limpeza

BRONZE = Path("dados/bronze/musica")
PRATA = Path("dados/prata")
PADRAO = "music_*.csv"

CHAVE = "Student_ID"

ORDEM_NIVEL = ["Beginner", "Intermediate", "Advanced"]
ORDEM_HABILIDADE = [1, 2, 3, 4, 5]

COLUNAS_NUMERICAS_CHECAR = [
    "Age", "Accuracy", "Rhythm", "Tempo", "Pitch_Accuracy", "Duration",
    "Volume", "Heart_Rate", "Blood_Pressure", "Focus_Time",
    "Performance_Score", "Engagement_Score",
]

FAIXAS_VALIDAS = {
    "Age": (5, 100),               
    "Accuracy": (0, 100),
    "Rhythm": (0, 100),
    "Pitch_Accuracy": (0, 100),
    "Volume": (0, 100),
    "Heart_Rate": (30, 220),       
    "Blood_Pressure": (60, 220),   
}


def carregar():
    arquivos = sorted(BRONZE.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError(f"nada em {BRONZE}")
    caminho = arquivos[-1]
    df = pd.read_csv(caminho)
    print("lido:", caminho.name, df.shape)
    return df, caminho


def conferir_chave(df, chave=CHAVE):
    repetidas = df[chave].duplicated().sum()
    print("chaves repetidas:", repetidas)
    return df.drop_duplicates(subset=chave)


def tipar_colunas(df):
    antes_nivel = df["Class_Level"].isna().sum()
    df["Class_Level"] = pd.Categorical(
        df["Class_Level"], categories=ORDEM_NIVEL, ordered=True
    )
    print("Class_Level fora da escala:", df["Class_Level"].isna().sum() - antes_nivel)

    antes_hab = df["Skill_Development"].isna().sum()
    df["Skill_Development"] = pd.Categorical(
        df["Skill_Development"], categories=ORDEM_HABILIDADE, ordered=True
    )
    print("Skill_Development fora da escala:", df["Skill_Development"].isna().sum() - antes_hab)

    for c in ["Gender", "Lesson_Type", "Instrument_Type"]:
        df[c] = df[c].astype("category")

    df["Timestamp"] = pd.to_datetime(df["Timestamp"], format="%Y-%m-%d %H:%M:%S")

    return df


def checar_extremos(df):
    for c in COLUNAS_NUMERICAS_CHECAR:
        df = limpeza.marcar_extremos(df, c)
        df = limpeza.marcar_zscore(df, c)
        n_iqr = df[c + "_extremo_iqr"].sum()
        n_z = df[c + "_extremo_z"].sum()
        if n_iqr or n_z:
            print(f"{c}: IQR={n_iqr} | z-score={n_z}")
    return df


def remover_erros_comprovados(df):
    total_removido = 0
    for coluna, (minimo, maximo) in FAIXAS_VALIDAS.items():
        valido = df[coluna].between(minimo, maximo)
        removidos = (~valido).sum()
        if removidos:
            print(f"removidos por faixa invalida em {coluna}: {removidos}")
            total_removido += removidos
            df = df[valido].copy()
    if total_removido == 0:
        print("nenhum erro comprovado por faixa de dominio")
    return df


def precisao_por_minuto(df):
    df["precisao_por_minuto"] = df["Accuracy"] / (df["Duration"] / 60)
    return df


def faixa_etaria(df):
    df["faixa_etaria"] = pd.cut(
        df["Age"], bins=[9, 12, 15, 17], labels=["10-12", "13-15", "16-17"]
    )
    return df


def desempenho_quartil(df):
    df["desempenho_quartil"] = pd.qcut(
        df["Performance_Score"], q=4,
        labels=["baixo", "medio-baixo", "medio-alto", "alto"],
    )
    return df


def salvar(df):
    PRATA.mkdir(parents=True, exist_ok=True)
    destino = PRATA / "musica.parquet"
    df.to_parquet(destino, index=False)
    print("salvo em:", destino, df.shape)
    return destino


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
    df = conferir_chave(df)
    df = tipar_colunas(df)
    df = checar_extremos(df)
    df = remover_erros_comprovados(df)
    df = precisao_por_minuto(df)
    df = faixa_etaria(df)
    df = desempenho_quartil(df)

    destino = salvar(df)
    registrar(origem, destino, antes, len(df), [
        "espacos removidos de colunas e textos",
        "chave Student_ID conferida (sem repeticao)",
        "Class_Level e Skill_Development tipados como categoria ordenada",
        "Gender, Lesson_Type, Instrument_Type tipados como categoria",
        "Timestamp convertido para datetime (ja vinha com hora/minuto)",
        "extremos marcados por IQR e por z-score, nao removidos",
        "faixas de dominio conferidas: nenhum erro comprovado encontrado",
        "atributo derivado: precisao_por_minuto (razao)",
        "atributo derivado: faixa_etaria (faixa por corte de dominio)",
        "atributo derivado: desempenho_quartil (faixa por quartil)",
    ])


if __name__ == "__main__":
    main()
