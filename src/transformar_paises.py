import json
from datetime import datetime
from pathlib import Path

import pandas as pd

BRONZE = Path("dados/bronze/banco_mudndial")
PRATA = Path("dados/prata")
PADRAO = "paises_*.csv"

def carregar():
    arquivos = sorted(BRONZE.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError(f"nada em {BRONZE}")
    caminho = arquivos[-1]
    df = pd.read_csv(caminho)
    print("Lido: ", caminho.name, df.shape)
    print("Clounas: ", df.columns.tolist())
    print("Ausentes por colunas: ", df.isna().sum())
    return df, caminho

def tirar_espacos(df):
    df.columns = df.columns.str.strip()
    for coluna in df.select_dtypes(include="object"):
        df[coluna] = df[coluna].str.strip()
    return df

def separar_agregados(df):
    e_pais = df["region.value"] != "Aggregates"
    print("Paises   : ", e_pais.sum())
    print("Agregados: ", (~e_pais).sum())
    return df[e_pais].copy()

def conferir_chave(df, chave="id"):
    repetidas = df[chave].duplicated().sum()
    print("Chaves repetidas: ", repetidas)
    if repetidas:
        print(df[df[chave].duplicated(keep=False)])
    return df.drop_duplicates(subset=chave)

def converter_tipos(df):
    for coluna in ["Longitude", "Latitude"]:
        df[coluna] = pd.to_numeric(df[coluna], errors="corece")
    return df

def limites_iqr(serie):
    q1 = serie.quantile(0.25)
    q3 = serie.quantile(0.75)
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr

def marcar_extremos(df, coluna):
    baixo, alto = limites_iqr(df[coluna])
    df[coluna + "_extremo"] = ((df[coluna] < baixo) | (df[coluna] > alto))
    print(coluna, df[coluna + "_extremo"].sum())
    return df

def marcar_zscore(df, coluna, limite=3):
    z = (df[coluna] - df[coluna].mean()) / df[coluna].std()
    df[coluna + "_z"] = z.abs() > limite
    print(coluna, "Z acima de ", limite, ": ", df[coluna + "_z"].sum())
    return df

def remover_erros(df, coluna, minimo, maximo):
    valido = df[coluna].between(minimo, maximo)
    print("Removidas: ", (~valido).sum())
    return df[valido].copy()

def salvar(df):
    PRATA.mkdir(parents=True, exist_ok=True)
    destino = PRATA / "paises.parquet"
    df.to_parquet(destino, index=False)
    print("Salvo em: ", destino, df.shape)
    return destino

def registrar(origem, destino, antes, depois, decisoes):
    info = {
        "origem": origem.name,
        "arquivo_prata": destino.name,
        "linhas_antes": antes,
        "linhas_depois": depois,
        "decisoes": decisoes,
        "transformado_em": datetime.now().isoformat(timespec="seconds")
    }
    caminho = PRATA / "proveniencia.jsonl"
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")


def main():
    df, origem = carregar()
    antes = len(df)
    df = tirar_espacos(df)
    df = separar_agregados(df)
    df = conferir_chave(df)
    df = converter_tipos(df)
    destino = salvar(df)
    registrar(origem, destino, antes, len(df), ["espacos removidos", "agregados separados", "longitude e latitude convertidas"])

if __name__ == "__main__":
    main()