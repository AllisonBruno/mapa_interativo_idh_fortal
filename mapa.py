import pandas as pd
import folium
import branca.colormap as cm

# --- 1. Ler o arquivo principal (IDH) ---
# NOTE: Você deve ter o arquivo 'IDH.xlsx' na mesma pasta.
df = pd.read_excel('IDH.xlsx')
df['Latitude'] = pd.to_numeric(df['Latitude (generated)'], errors='coerce')
df['Longitude'] = pd.to_numeric(df['Longitude (generated)'], errors='coerce')
df_mapa = df.dropna(subset=['Latitude', 'Longitude'])

# --- 2. Ler o segundo arquivo (Condições Urbanas) ---
# NOTE: Você deve ter o arquivo 'IBEU_data.xlsx' na mesma pasta.
df_cond = pd.read_excel('IBEU_data.xlsx')
df_cond['Latitude'] = pd.to_numeric(df_cond['Latitude (generated)'], errors='coerce')
df_cond['Longitude'] = pd.to_numeric(df_cond['Longitude (generated)'], errors='coerce')
df_cond = df_cond.dropna(subset=['Latitude', 'Longitude'])

# -------------------------------------------------------------------------
# --- 3. Ler o arquivo IDE (Índice Educacional) - TRATAMENTO E NORMALIZAÇÃO ---
# -------------------------------------------------------------------------
# NOTE: Você deve ter o arquivo 'IDE.xlsx' na mesma pasta.
df_ide = pd.read_excel('IDE.xlsx')

colunas_percentuais = [
    'IDE-1: Sem instrução e fundamental incompleto (A)',
    'IDE-2: Fundamental completo e médio incompleto (B)',
    'IDE-3: Médio completo e superior incompleto (C)',
    'IDE-4: Superior completo (D)'
]
colunas_coordenadas = ['Latitude (gerada)', 'Longitude (gerada)']

# Converte todas as colunas relevantes para numérico e limpa vírgulas
for col in colunas_percentuais + colunas_coordenadas:
    if col in df_ide.columns:
        df_ide[col] = df_ide[col].astype(str).str.replace(',', '.').str.strip()
        df_ide[col] = pd.to_numeric(df_ide[col], errors='coerce')

# 🔑 MODIFICAÇÃO 1: Renomear a coluna para facilitar o uso no pop-up
if 'Nome da Área de Ponderação' in df_ide.columns:
    df_ide.rename(columns={'Nome da Área de Ponderação': 'Area_Ponderacao'}, inplace=True)
else:
    # Caso o nome da coluna mude, use o primeiro nome disponível (coluna 1)
    df_ide.rename(columns={df_ide.columns[0]: 'Area_Ponderacao'}, inplace=True)

# Normalização: Divide os percentuais por 100
for col in colunas_percentuais:
    df_ide[f'{col}_NORM'] = df_ide[col] / 100.0
    
# Define as novas colunas simplificadas
df_ide['Latitude'] = df_ide['Latitude (gerada)']
df_ide['Longitude'] = df_ide['Longitude (gerada)']

df_ide = df_ide.dropna(subset=['Latitude', 'Longitude'])

print(f"Total de pontos no DataFrame IDE com coordenadas válidas: {len(df_ide)}")

# -------------------------------------------------------------------------
# --- 4. Criar o mapa base ---
# -------------------------------------------------------------------------
lat_centro = df_mapa['Latitude'].mean()
lon_centro = df_mapa['Longitude'].mean()
mapa = folium.Map(location=[lat_centro, lon_centro], zoom_start=11, tiles='OpenStreetMap')

# --- 5. Função de cor (para IDH e Condições Urbanas) ---
def get_color_idh_cond(classificacao):
    if 'Muito baixo' in classificacao:
        return 'darkred'
    elif 'Baixo' in classificacao:
        return 'red'
    elif 'Médio' in classificacao:
        return 'orange'
    elif 'Alto' in classificacao:
        return 'lightgreen'
    elif 'Muito alto' in classificacao:
        return 'green'
    return 'gray'

# --- 6. Camada IDH (Círculos Coloridos com classificação IDH) ---
idh_layer = folium.FeatureGroup(name='IDH dos Bairros').add_to(mapa)

for index, row in df_mapa.iterrows():
    popup_text = (
        f"<b>Bairro:</b> {row['Bairro']}<br>"
        f"<b>IDH:</b> {row['Valor']:.4f}<br>"
        f"<b>Classificação:</b> {row['Classificação IDH']}"
    )
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=5 + (row['Valor'] * 10),
        popup=popup_text,
        color=get_color_idh_cond(row['Classificação IDH']),
        fill=True,
        fill_color=get_color_idh_cond(row['Classificação IDH'])
    ).add_to(idh_layer)

# --- 7. Camada Condições Urbanas (Ícones de Casa) ---
cond_layer = folium.FeatureGroup(name='Condições Urbanas').add_to(mapa)

for index, row in df_cond.iterrows():
    popup_text = (
        f"<b>Bairro:</b> {row['Bairro']}<br>"
        f"<b>Classificação:</b> {row['Classificação']}<br>"
        f"<b>Condições Ambientais Urbanas:</b> {row['Condições Ambientais Urbanas (D2)']:.4f}<br>"
        f"<b>Condições Habitacionais Urbanas:</b> {row['Condições Habitacionais Urbanas (D3)']:.4f}"
    )
    cor = get_color_idh_cond(row['Classificação'])
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=popup_text,
        icon=folium.Icon(color=cor, icon='home', prefix='fa')
    ).add_to(cond_layer)

# -------------------------------------------------------------------------
# --- 8. Camada Índice de Desenvolvimento Educacional (IDE) - Ícones de Livro ---
# -------------------------------------------------------------------------
ide_layer = folium.FeatureGroup(name='Índice de Desenvolvimento Educacional (IDE)').add_to(mapa)

# Escala de cores (1 = baixo, 4 = alto) para a legenda
colormap_ide = cm.linear.RdYlGn_09.scale(1, 4)
colormap_ide.caption = 'Nível Médio de Educação (IDE)'
colormap_ide.add_to(mapa)

def resumo_educacional(row):
    valores = {
        'Sem instrução / Fund. incompleto': row['IDE-1: Sem instrução e fundamental incompleto (A)'],
        'Fund. completo / Médio incompleto': row['IDE-2: Fundamental completo e médio incompleto (B)'],
        'Médio completo / Sup. incompleto': row['IDE-3: Médio completo e superior incompleto (C)'],
        'Superior completo': row['IDE-4: Superior completo (D)']
    }
    valores = {k: v for k, v in valores.items() if pd.notna(v)}
    
    if not valores:
        return "⚪ Dados educacionais indisponíveis."

    maior_categoria = max(valores, key=valores.get)
    if 'Sem instrução' in maior_categoria:
        return "🔴 Predomínio de baixa escolaridade — maioria com ensino fundamental incompleto."
    elif 'Fund.' in maior_categoria:
        return "🟠 Nível educacional intermediário — predominância de ensino fundamental completo."
    elif 'Médio completo' in maior_categoria:
        return "🟢 Bom nível educacional — maioria com ensino médio completo."
    elif 'Superior completo' in maior_categoria:
        return "🟢 Alta escolaridade — grande proporção de moradores com ensino superior completo."
    else:
        return "⚪ Distribuição equilibrada entre os níveis educacionais."

if len(df_ide) > 0:
    for index, row in df_ide.iterrows():

        # Cálculo da Média Educacional normalizada (1.0 a 4.0)
        soma_norm = (
            row['IDE-1: Sem instrução e fundamental incompleto (A)_NORM'] +
            row['IDE-2: Fundamental completo e médio incompleto (B)_NORM'] +
            row['IDE-3: Médio completo e superior incompleto (C)_NORM'] +
            row['IDE-4: Superior completo (D)_NORM']
        )

        if soma_norm > 0:
            media_educ = (
                row['IDE-1: Sem instrução e fundamental incompleto (A)_NORM'] * 1 +
                row['IDE-2: Fundamental completo e médio incompleto (B)_NORM'] * 2 +
                row['IDE-3: Médio completo e superior incompleto (C)_NORM'] * 3 +
                row['IDE-4: Superior completo (D)_NORM'] * 4
            ) / soma_norm
        else:
            media_educ = None

        if media_educ is None or pd.isna(media_educ):
            continue

        # Escala de CORES para o marcador
        if media_educ < 1.8:
            cor_pin_ide = 'darkred'      # Muito Baixo
        elif media_educ < 2.1:
            cor_pin_ide = 'red'          # Baixo
        elif media_educ < 2.4:
            cor_pin_ide = 'orange'       # Intermediário
        elif media_educ < 2.8:
            cor_pin_ide = 'lightgreen'   # Bom
        else:
            cor_pin_ide = 'green'        # Muito Alto

        # 🔑 MODIFICAÇÃO 2: Inclusão da Área de Ponderação no pop-up
        popup_text = f"""
        <b>Área de Ponderação:</b> {row['Area_Ponderacao']}<br>
        <b>Bairro:</b> {row['Bairro']}<br>
        <b>Média Educacional:</b> {media_educ:.2f}<br><br>
        {resumo_educacional(row)}<br><br>
        <small>
        📊 <b>Distribuição (%):</b><br>
        A: {row['IDE-1: Sem instrução e fundamental incompleto (A)']:.2f} |
        B: {row['IDE-2: Fundamental completo e médio incompleto (B)']:.2f} |
        C: {row['IDE-3: Médio completo e superior incompleto (C)']:.2f} |
        D: {row['IDE-4: Superior completo (D)']:.2f}
        </small>
        """

        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color=cor_pin_ide, icon='book', prefix='fa', icon_color='white')
        ).add_to(ide_layer)

# -------------------------------------------------------------------------
# --- 9. Controle de camadas ---
# -------------------------------------------------------------------------
folium.LayerControl().add_to(mapa)

# --- 10. Salvar o mapa ---
mapa.save("index.html")

print("✅ Mapa interativo salvo como 'mapa_interativo_final_corrigido_educacao.html'.")
print("✅ A coluna 'Área de Ponderação' foi adicionada aos pop-ups da camada IDE.")