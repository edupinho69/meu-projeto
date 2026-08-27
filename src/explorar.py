from pathlib import Path
import pandas as pd
from data_profiling import ProfileReport

BRONZE = Path("dados/bronze/music")
PADRAO = "music_*.csv"

RELATORIOS = Path("relatorios")

def mais_recente():
    arquivos = sorted(BRONZE.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError("Bronze vazia")
    return arquivos[-1]

def gerar(caminho):
    df = pd.read_csv(caminho)
    perfil = ProfileReport(df, title=caminho.name)
    RELATORIOS.mkdir(exist_ok=True)
    saida = RELATORIOS / f"{caminho.stem}.html"
    perfil.to_file(saida)
    return saida

def main():
    caminho = mais_recente()
    print("Perfilando: ", caminho.name)
    print(gerar(caminho))

if __name__ == "__main__":
    main()