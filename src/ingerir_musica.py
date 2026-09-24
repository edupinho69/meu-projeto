import json
import shutil
from datetime import date, datetime
from pathlib import Path

ORIGEM = Path("music_original_recebido.csv")
BRONZE = Path("dados/bronze/musica")


def copiar(origem: Path) -> Path:
    """Copia o arquivo recebido para a bronze, com a data no nome."""
    BRONZE.mkdir(parents=True, exist_ok=True)
    hoje = date.today().strftime("%Y%m%d")
    destino = BRONZE / f"music_{hoje}.csv"
    shutil.copy(origem, destino)
    return destino


def registrar(origem: Path, destino: Path):
    info = {
        "fonte": "arquivo recebido do usuario (music.csv)",
        "canal": "arquivo baixado/recebido",
        "arquivo_origem": origem.name,
        "arquivo_bronze": destino.name,
        "extraido_em": datetime.now().isoformat(timespec="seconds"),
    }
    caminho = BRONZE / "proveniencia.jsonl"
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")


def main():
    destino = copiar(ORIGEM)
    registrar(ORIGEM, destino)
    print("bronze gravada em:", destino)
    print("proveniencia registrada em:", BRONZE / "proveniencia.jsonl")


if __name__ == "__main__":
    main()
