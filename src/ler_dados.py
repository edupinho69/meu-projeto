import pandas as pd
CAMINHO = "dados/bronze/music.csv"
df = pd.read_csv(CAMINHO)
print(df.shape)

for coluna in df.columns:
    print(f'"{coluna}"')