import pandas as pd
import folium
import branca.colormap as cm

# -------------------------------------------------------------------------
# --- 1. Ler o arquivo principal (IDH) ---
# -------------------------------------------------------------------------
df = pd.read_excel('IDH.xlsx')
df['Latitude'] = pd.to_numeric(df['Latitude (generated)'], errors='coerce')
df['Longitude'] = pd.to_numeric(df['Longitude (generated)'], errors='coerce')
df_mapa = df.dropna(subset=['Latitude', 'Longitude'])

# -------------------------------------------------------------------------
# --- 2. Ler o segundo arquivo (Condições Urbanas) ---
# -------------------------------------------------------------------------
df_cond = pd.read_excel('IBEU_data.xlsx')
df_cond['Latitude'] = pd.to_numeric(df_cond['Latitude (generated)'], errors='coerce')
df_cond['Longitude'] = pd.to_numeric(df_cond['Longitude (generated)'], errors='coerce')
df_cond = df_cond.dropna(subset=['Latitude', 'Longitude'])

# -------------------------------------------------------------------------
# --- 3. Ler o arquivo IDE (Índice Educacional) - TRATAMENTO E NORMALIZAÇÃO ---
# -------------------------------------------------------------------------
df_ide = pd.read_excel('IDE.xlsx')

colunas_percentuais = [
    'IDE-1: Sem instrução e fundamental incompleto (A)',
    'IDE-2: Fundamental completo e médio incompleto (B)',
    'IDE-3: Médio completo e superior incompleto (C)',
    'IDE-4: Superior completo (D)'
]
colunas_coordenadas = ['Latitude (gerada)', 'Longitude (gerada)']

for col in colunas_percentuais + colunas_coordenadas:
    if col in df_ide.columns:
        df_ide[col] = df_ide[col].astype(str).str.replace(',', '.').str.strip()
        df_ide[col] = pd.to_numeric(df_ide[col], errors='coerce')

if 'Nome da Área de Ponderação' in df_ide.columns:
    df_ide.rename(columns={'Nome da Área de Ponderação': 'Area_Ponderacao'}, inplace=True)
else:
    df_ide.rename(columns={df_ide.columns[0]: 'Area_Ponderacao'}, inplace=True)

for col in colunas_percentuais:
    df_ide[f'{col}_NORM'] = df_ide[col] / 100.0
    
df_ide['Latitude'] = df_ide['Latitude (gerada)']
df_ide['Longitude'] = df_ide['Longitude (gerada)']

df_ide = df_ide.dropna(subset=['Latitude', 'Longitude'])

print(f"Total de pontos no DataFrame IDE com coordenadas válidas: {len(df_ide)}")

# -------------------------------------------------------------------------
# --- 4. Ler o arquivo de Renda Familiar (NOVA CAMADA) ---
# --- GARANTIA DAS COLUNAS 'Renda' e 'Faixa_Renda' (Classificação_Renda) ---
# -------------------------------------------------------------------------
# Assumindo o nome exato do arquivo
df_renda = pd.read_excel('IDH_Demografia_Merged.xlsx')

# 1. Tratamento das coordenadas e colunas essenciais
df_renda['Latitude'] = pd.to_numeric(df_renda['Latitude (generated)'], errors='coerce')
df_renda['Longitude'] = pd.to_numeric(df_renda['Longitude (generated)'], errors='coerce')
df_renda['Renda'] = pd.to_numeric(df_renda['Renda'], errors='coerce') # <-- Coluna Renda é lida
# Renomeia 'Faixa_Renda' para uso no código (mantém a coluna)
df_renda.rename(columns={'Bairro_y': 'Bairro', 'Faixa_Renda': 'Classificação_Renda'}, inplace=True) 

# Filtra pontos com coordenadas e renda válidas
df_renda = df_renda.dropna(subset=['Latitude', 'Longitude', 'Renda'])

print(f"Total de pontos no DataFrame Renda com coordenadas válidas: {len(df_renda)}")

# -------------------------------------------------------------------------
# --- 5. Criar o mapa base ---
# -------------------------------------------------------------------------
lat_centro = df_mapa['Latitude'].mean()
lon_centro = df_mapa['Longitude'].mean()
mapa = folium.Map(location=[lat_centro, lon_centro], zoom_start=11, tiles='OpenStreetMap')

# -------------------------------------------------------------------------
# --- 6. Função de cor (para IDH, Condições Urbanas e Renda) ---
# -------------------------------------------------------------------------
# -------------------------------------------------------------------------
# --- 6. Função de cor (para IDH, Condições Urbanas e Renda) ---
# --- AGORA FLEXÍVEL PARA CLASSIFICAÇÕES MASCULINAS (o) E FEMININAS (a) ---
# -------------------------------------------------------------------------
# -------------------------------------------------------------------------
# --- 6. Função de cor (para IDH, Condições Urbanas e Renda) ---
# --- CORRIGIDA: Trata "Muito alto" antes de "Alto" ---
# -------------------------------------------------------------------------
def get_color_idh_cond(classificacao):
    # Converte para minúsculas para garantir a correspondência
    classificacao_lower = classificacao.lower()
    
    # 1. Muito Baixo
    if 'muito baix' in classificacao_lower:
        return 'darkred'
    # 2. Baixo
    elif 'baix' in classificacao_lower:
        return 'red'
    # 3. Médio
    elif 'médi' in classificacao_lower:
        return 'orange'
        
    # 4. MUITO ALTO DEVE VIR ANTES DE ALTO
    elif 'muito alt' in classificacao_lower:
        return 'green' # <-- Cor mais escura para a classificação mais alta
        
    # 5. Alto
    elif 'alt' in classificacao_lower:
        return 'lightgreen'
        
    return 'gray'

# -------------------------------------------------------------------------
# --- 7. Camada IDH (Círculos Coloridos com classificação IDH) ---
# -------------------------------------------------------------------------
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

# -------------------------------------------------------------------------
# --- 8. Camada Condições Urbanas (Ícones de Casa) ---
# -------------------------------------------------------------------------
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
# --- 9. Camada Índice de Desenvolvimento Educacional (IDE) - Ícones de Livro ---
# -------------------------------------------------------------------------
ide_layer = folium.FeatureGroup(name='Índice de Desenvolvimento Educacional (IDE)').add_to(mapa)

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
    elif not maior_categoria:
        return "⚪ Distribuição equilibrada entre os níveis educacionais."
    else:
        return "⚪ Distribuição equilibrada entre os níveis educacionais."


if len(df_ide) > 0:
    for index, row in df_ide.iterrows():

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

        if media_educ < 1.8:
            cor_pin_ide = 'darkred'      
        elif media_educ < 2.1:
            cor_pin_ide = 'red'          
        elif media_educ < 2.4:
            cor_pin_ide = 'orange'       
        elif media_educ < 2.8:
            cor_pin_ide = 'lightgreen'   
        else:
            cor_pin_ide = 'green'        

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
# --- 10. Camada Renda Familiar (NOVA CAMADA) ---
# -------------------------------------------------------------------------
renda_layer = folium.FeatureGroup(name='Renda Familiar dos Bairros').add_to(mapa)

if len(df_renda) > 0:
    min_renda = df_renda['Renda'].min()
    max_renda = df_renda['Renda'].max()

    def calcular_raio_renda(renda, min_val, max_val):
        if max_val == min_val:
            return 5
        escala = (renda - min_val) / (max_val - min_val)
        return 3 + (escala * 15)
        
    for index, row in df_renda.iterrows():
        # Uso da coluna Classificação_Renda (Faixa_Renda) para cor
        cor = get_color_idh_cond(row['Classificação_Renda']) 
        # Uso da coluna Renda para o tamanho
        raio = calcular_raio_renda(row['Renda'], min_renda, max_renda)
        
        popup_text = (
            f"<b>Bairro:</b> {row['Bairro']}<br>"
            f"<b>Renda Familiar Média:</b> R$ {row['Renda']:.2f}<br>"
            f"<b>Classificação:</b> {row['Classificação_Renda']}"
        )
        
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=raio,
            popup=folium.Popup(popup_text, max_width=250),
            color=cor,
            fill=True,
            fill_color=cor
        ).add_to(renda_layer)

# -------------------------------------------------------------------------
# --- 11. Controle de camadas ---
# -------------------------------------------------------------------------
folium.LayerControl().add_to(mapa)

# -------------------------------------------------------------------------
# --- 12. Salvar o mapa ---
# -------------------------------------------------------------------------
mapa.save("index.html")

print("✅ Mapa interativo salvo como 'mapa_interativo_final_com_renda.html'.")
print("✅ As colunas Renda e Faixa_Renda (Classificação_Renda) estão sendo utilizadas para cor e tamanho dos círculos.")