import unicodedata

import pandas as pd


def tirar_espacos(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.strip()
    for c in df.select_dtypes(include="object"):
        df[c] = df[c].str.strip()
    return df


def chave_texto(serie: pd.Series) -> pd.Series:
    s = serie.str.strip().str.lower()
    s = s.str.normalize("NFKD")
    s = s.str.encode("ascii", errors="ignore")
    return s.str.decode("utf-8")


def aplicar_mapa(serie: pd.Series, mapa: dict) -> pd.Series:
    return serie.replace(mapa)


def limites_iqr(serie: pd.Series):
    q1 = serie.quantile(0.25)
    q3 = serie.quantile(0.75)
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def marcar_extremos(df: pd.DataFrame, coluna: str) -> pd.DataFrame:
    baixo, alto = limites_iqr(df[coluna])
    df[coluna + "_extremo_iqr"] = (df[coluna] < baixo) | (df[coluna] > alto)
    return df


def marcar_zscore(df: pd.DataFrame, coluna: str, limite: float = 3) -> pd.DataFrame:
    z = (df[coluna] - df[coluna].mean()) / df[coluna].std()
    df[coluna + "_extremo_z"] = z.abs() > limite
    return df
