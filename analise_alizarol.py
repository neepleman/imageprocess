import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import r2_score
import os

# ==========================================
# 1. CARREGAMENTO E LIMPEZA DE DADOS (BLINDADO)
# ==========================================
arquivo_csv = 'dados_consolidados.csv'

print(f"[DEBUG] Tentando ler o arquivo: {arquivo_csv}")

if not os.path.exists(arquivo_csv):
    print(f"[ERRO CRÍTICO] O arquivo '{arquivo_csv}' não foi encontrado na mesma pasta do script.")
    exit()

# Lê o arquivo forçando o Pandas a tentar adivinhar se é separado por vírgula ou ponto-e-vírgula
df = pd.read_csv(arquivo_csv, sep=None, engine='python')

# Limpa os nomes das colunas (tira espaços extras que o Excel coloca)
df.columns = df.columns.str.strip()

# Função para forçar a conversão de qualquer coisa (vírgula ou ponto) para Decimal matemático
def blindar_decimal(valor):
    if pd.isna(valor): return np.nan
    valor_str = str(valor).strip()
    valor_str = valor_str.replace(',', '.') # Transforma vírgula BR em ponto US
    return float(valor_str)

df['Angulo_Rad'] = df['Angulo_Rad'].apply(blindar_decimal)
df['pH_Real'] = df['pH_Real'].apply(blindar_decimal)

# Limpa a coluna de Concentração (garante que todas tenham o % no final e sem espaços)
df['Concentracao'] = df['Concentracao'].astype(str).str.strip()
df['Concentracao'] = df['Concentracao'].apply(lambda x: x + '%' if not x.endswith('%') else x)

print("\n[DEBUG] Dados lidos e limpos com sucesso. Amostras encontradas:")
print(df['Concentracao'].value_counts())

# ==========================================
# 2. FUNÇÃO DE CÁLCULO POLINOMIAL (GRAU 3)
# ==========================================
def calcular_curva(x, y, nome_modelo):
    # Evita que o programa crashe se uma concentração não tiver dados suficientes
    if len(x) < 4:
        print(f"\n--- MODELO: {nome_modelo.upper()} (DADOS INSUFICIENTES) ---")
        return None, 0

    # Calcula os coeficientes [C3, C2, C1, Intercept]
    coefs = np.polyfit(x, y, 3)
    # Cria a função matemática
    polinomio = np.poly1d(coefs)
    # Previsões para calcular o R²
    y_pred = polinomio(x)
    r2 = r2_score(y, y_pred)
    
    print(f"\n--- MODELO: {nome_modelo.upper()} ---")
    print(f"R²: {r2:.4f}")
    print("Copie para o App (Configurações):")
    print(f"phEstimatedC3:       {coefs[0]:.8f}")
    print(f"phEstimatedC2:       {coefs[1]:.8f}")
    print(f"phEstimatedC1:       {coefs[2]:.8f}")
    print(f"phEstimatedIntercept: {coefs[3]:.8f}")
    
    return polinomio, r2

# ==========================================
# 3. EXTRAÇÃO DOS COEFICIENTES E R²
# ==========================================
print("\n" + "="*50)
print("ANÁLISE ESTATÍSTICA - CALIBRAÇÃO ALIZAROL")
print("="*50)

# Curva Universal (Todos os dados juntos)
poly_univ, r2_univ = calcular_curva(df['Angulo_Rad'], df['pH_Real'], "Universal (78% + 80%)")

# Separando os dados de forma inteligente (busca apenas se contém o número)
df_78 = df[df['Concentracao'].astype(str).str.contains('78', na=False)]
df_80 = df[df['Concentracao'].astype(str).str.contains('80', na=False)]

# Curvas Individuais
poly_78, r2_78 = calcular_curva(df_78['Angulo_Rad'], df_78['pH_Real'], "Alizarol 78%")
poly_80, r2_80 = calcular_curva(df_80['Angulo_Rad'], df_80['pH_Real'], "Alizarol 80%")

# ==========================================
# 4. PLOTAGEM DO GRÁFICO (PADRÃO CIENTÍFICO)
# ==========================================
sns.set_theme(style="whitegrid")
plt.figure(figsize=(10, 6))

# Plotando os pontos reais (Scatter)
sns.scatterplot(data=df, x='Angulo_Rad', y='pH_Real', hue='Concentracao', 
                palette=['#1f77b4', '#d62728'], alpha=0.6, s=60, edgecolor='k')

# Criamos um eixo X para traçar as linhas de tendência de forma lisa
x_plot = np.linspace(df['Angulo_Rad'].min(), df['Angulo_Rad'].max(), 200)

if poly_78 is not None:
    plt.plot(x_plot, poly_78(x_plot), color='#1f77b4', linestyle='-', linewidth=2, label=f'Curva 78% (R²={r2_78:.3f})')
if poly_80 is not None:
    plt.plot(x_plot, poly_80(x_plot), color='#d62728', linestyle='-', linewidth=2, label=f'Curva 80% (R²={r2_80:.3f})')
if poly_univ is not None:
    plt.plot(x_plot, poly_univ(x_plot), color='black', linestyle='--', linewidth=2, label=f'Curva Universal (R²={r2_univ:.3f})')

# Estética do Gráfico
plt.title('Calibração Colorimétrica: Matiz (Radiano) vs pH Real', fontsize=14, fontweight='bold')
plt.xlabel('Matiz Extraída (Ângulo Radiano)', fontsize=12)
plt.ylabel('pH Medido (pHâmetro)', fontsize=12)
plt.legend(loc='best', fontsize=10)
plt.tight_layout()

# Salva o gráfico em alta resolução
plt.savefig('Curva_Calibracao_Alizarol.png', dpi=300)
print("\n[INFO] Gráfico salvo como 'Curva_Calibracao_Alizarol.png'. Feche a janela do gráfico para encerrar o script.")
plt.show()