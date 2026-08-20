from pathlib import Path
from datetime import date
from datetime import datetime
import json
import shutil
import kagglehub

DATASET = "ziya07/music-education-performance-data"
BRONZE = Path("dados/bronze/music")

def baixar():
    pasta = kagglehub.dataset_download(DATASET)
    print("Baixado em: ", pasta)
    return Path(pasta)

def localizar(pasta):
    arquivos = list(pasta.glob("*.csv"))
    if not arquivos:
        raise FileNotFoundError("Nenhum CSV")
    print("Encontrados: ", [a.name for a in arquivos])
    return arquivos[0]   

def copiar(origem):
    BRONZE.mkdir(parents=True, exist_ok=True)
    hoje = date.today().strftime("%Y%m%d")
    destino = BRONZE / f"music_{hoje}.csv"
    shutil.copy(origem, destino)
    return destino

def registrar(origem, destino):
    info = {
        "Fonte: ": DATASET,
        "Arquivo_origem: ": origem.name,
        "Arquivo_bronze: ": destino.name,
        "Extraido_em: ": datetime.now().isoformat(),
    }
    (BRONZE / "proveniencia.json").write_text(
        json.dumps(info, indent=2))

def main():
    pasta = baixar()
    origem = localizar(pasta)
    destino = copiar(origem)
    registrar(origem, destino)

if __name__ == "__main__":
    main()
