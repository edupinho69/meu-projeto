import unicodedata
import pandas as pd

#Funcao responsavel por retirar os espacos em branco no inicio e no final dos nomes de colunas e textos no geral
def tirar_espacos(df):
    df.columns = df.columns.str.strip()
    for c in df.select_dtypes(include="object"):
        df[c] = df[c].str.strip()
    return df

#Funcao responsavel por uniformizar o texto(minusculo, sem acento, sem espaco)
def chave_texto(serie):
    s = serie.str.strip().str.lower()
    s = s.str.normalize("NFKD")
    s = s.str.encode("ascii", errors="ignore")
    return s.str.decode("utf-8")


def aplicar_mapa(serie, mapa):
    return serie.replace(mapa)

#Funcao responsavel por calcular os limites superiores e inferiores do IQR
def limites_iqr(serie):
    q1 = serie.quantile(0.25)
    q3 = serie.quantile(0.75)
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr

#Funcao responsavel por encontrar e marcar colunas que estao fora do intervalo dos limites do IQR
def marcar_extremos(df, coluna):
    baixo, alto = limites_iqr(df[coluna])
    df[coluna + "_extremo_iqr"] = (df[coluna] < baixo) | (df[coluna] > alto)
    return df

#Funcao responsavel por encontrar e marcar colunas que os desvios-padrao dos valores sao maiores que o limite
def marcar_zscore(df, coluna, limite=3):
    z = (df[coluna] - df[coluna].mean()) / df[coluna].std()
    df[coluna + "_extremo_z"] = z.abs() > limite
    return df

#Funcao responsavel por remover as colunas que foram marcadas como fora do limite
def remover_erros(df, coluna, minimo, maximo):
    valido = df[coluna].between(minimo, maximo)
    print("removidas:", (~valido).sum())
    return df[valido].copy()