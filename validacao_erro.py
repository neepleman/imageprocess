import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error

# ==========================================
# 1. CARREGAMENTO E LIMPEZA (Mesmo padrão blindado)
# ==========================================
arquivo_csv = 'dados_consolidados.csv'

df = pd.read_csv(arquivo_csv, sep=None, engine='python')
df.columns = df.columns.str.strip()

def blindar_decimal(valor):
    if pd.isna(valor): return np.nan
    valor_str = str(valor).strip().replace(',', '.')
    return float(valor_str)

df['Angulo_Rad'] = df['Angulo_Rad'].apply(blindar_decimal)
df['pH_Real'] = df['pH_Real'].apply(blindar_decimal)

# Remove linhas com valores nulos para não quebrar a estatística
df = df.dropna(subset=['Angulo_Rad', 'pH_Real'])

# ==========================================
# 2. CÁLCULO DA PREDIÇÃO E DO ERRO (RMSE)
# ==========================================
# Recalcula a curva universal
coefs_univ = np.polyfit(df['Angulo_Rad'], df['pH_Real'], 3)
polinomio_univ = np.poly1d(coefs_univ)

# Simula o Aplicativo: Calcula qual seria o pH lido para cada foto
df['pH_App'] = polinomio_univ(df['Angulo_Rad'])

# Calcula o Erro (Resíduo)
df['Erro'] = df['pH_App'] - df['pH_Real']

# Calcula o RMSE (Root Mean Square Error)
rmse = np.sqrt(mean_squared_error(df['pH_Real'], df['pH_App']))

print("\n" + "="*50)
print("ANÁLISE DE ERRO E EQUIVALÊNCIA")
print("="*50)
print(f"Erro Médio Quadrático (RMSE): ± {rmse:.4f} unidades de pH")
print(f"Erro Máximo Encontrado: {df['Erro'].abs().max():.4f} unidades de pH")

# ==========================================
# 3. ANÁLISE DE BLAND-ALTMAN
# ==========================================
# Eixo X = Média entre o pHâmetro e o App
df['Media_Metodos'] = (df['pH_Real'] + df['pH_App']) / 2
# Eixo Y = Diferença (Erro)
diferenca = df['Erro']

bias = diferenca.mean() # Viés médio (quão longe do zero a média de erro está)
sd = diferenca.std()    # Desvio padrão do erro
limite_sup = bias + 1.96 * sd # Limite de Concordância Superior (95%)
limite_inf = bias - 1.96 * sd # Limite de Concordância Inferior (95%)

print(f"\nViés Médio (Bias): {bias:.4f}")
print(f"Limites de Concordância (95%): de {limite_inf:.4f} a {limite_sup:.4f}")

# ==========================================
# 4. PLOTAGEM DO GRÁFICO BLAND-ALTMAN
# ==========================================
plt.figure(figsize=(10, 6))
sns.scatterplot(x=df['Media_Metodos'], y=diferenca, alpha=0.7, s=60, color='purple', edgecolor='k')

# Linha do Viés (Bias)
plt.axhline(bias, color='blue', linestyle='--', linewidth=2, label=f'Viés Médio: {bias:.3f}')
# Linhas dos Limites de Concordância de 95%
plt.axhline(limite_sup, color='red', linestyle=':', linewidth=2, label=f'+1.96 SD: {limite_sup:.3f}')
plt.axhline(limite_inf, color='red', linestyle=':', linewidth=2, label=f'-1.96 SD: {limite_inf:.3f}')
# Linha do Zero (Perfeição)
plt.axhline(0, color='black', linestyle='-', linewidth=1)

plt.title('Gráfico de Bland-Altman: App Alizarol vs pHâmetro', fontsize=14, fontweight='bold')
plt.xlabel('Média dos dois métodos: (App + pHâmetro) / 2', fontsize=12)
plt.ylabel('Diferença entre os métodos (App - pHâmetro)', fontsize=12)
plt.legend(loc='best')
plt.tight_layout()

plt.savefig('Bland_Altman_Alizarol.png', dpi=300)
print("\n[INFO] Gráfico salvo como 'Bland_Altman_Alizarol.png'.")
plt.show()