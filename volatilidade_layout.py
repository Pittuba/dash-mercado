import pandas as pd
from dash import html, dcc
from dash import dash_table
import os
import numpy as np

# Caminho da base de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
caminho_base = os.path.join(BASE_DIR, "Data", "Base - Indicadores.xlsx")

# Categorias associadas a cada ativo (exemplo)
categorias = {
    'Ibovespa': 'Renda Variável',
    'CDI': 'Renda Fixa',
    'Ida Geral': 'Crédito',
    'IHFA': 'Multimercado',
    'Ima-B 5': 'Renda Fixa',
    'Ima-B 5+': 'Renda Fixa',
    'Ima-B': 'Renda Fixa',
    'IRF-M': 'Renda Fixa',
    'S&P 500': 'Internacional',
    'Nasdaq': 'Internacional',
    'IDA DI': 'Crédito',
    'IDA IPCA': 'Renda Fixa',
    'IFIX': 'Renda Variável',
    'Small Caps': 'Renda Variável',
    'Jgp - CDI': 'Crédito',
    'Ibrx': 'Renda Variável',
    'IVBX-2': 'Renda Variável',
    'IGC-Nm': 'Renda Variável',
    'ISEE': 'Renda Variável',
    'ICO-2': 'Renda Variável',
    'IDIV': 'Renda Variável',
    'Midlarge Cap': 'Renda Variável',
    'Ima S': 'Renda Fixa',
    'Ima Geral': 'Renda Fixa',
    'Dólar Ptax': 'Internacional'
}

# Código para carregar e preparar df_risco_melt, antes dos callbacks
df_risco = pd.read_excel(caminho_base, sheet_name="Risco")
df_risco.columns = df_risco.columns.str.strip()
df_risco['Data'] = pd.to_datetime(df_risco['Data'])

# Substituir '-' por NaN de forma segura
for col in df_risco.columns:
    if col != 'Data':
        df_risco[col] = df_risco[col].where(df_risco[col] != '-', np.nan)
        df_risco[col] = (
            df_risco[col].astype(str)
            .str.replace('%', '', regex=False)
            .str.replace(',', '.', regex=False)
            .astype(float) 
        )

ativos = [col for col in df_risco.columns if col != 'Data']

df_risco_melt = df_risco.melt(
    id_vars='Data',
    value_vars=ativos,
    var_name='Ativo',
    value_name='Volatilidade'
)

df_risco_melt['Categoria'] = df_risco_melt['Ativo'].map(categorias)

# Se existir df_risco_melt_vol, faça a mesma coisa para ele
df_risco_melt_vol = df_risco_melt.copy()

# Lista única de categorias para o dropdown
ordem_categorias = ['Renda Fixa', 'Renda Variável', 'Crédito', 'Multimercado', 'Internacional', 'Todos']
categorias_unicas = [cat for cat in ordem_categorias if cat in df_risco_melt['Categoria'].unique()]

# Função para meses por ano
def meses_por_ano(ano):
    return sorted(df_risco[df_risco['Data'].dt.year == ano]['Data'].dt.month.unique())

# Lista de anos
anos_unicos = sorted(df_risco['Data'].dt.year.dropna().unique())
anos_unicos = [int(ano) for ano in anos_unicos if not pd.isna(ano)]

# Layout da aba Risco atualizado com a tabela de volatilidade
layout = html.Div([
    # 🔽 BLOCO DE FILTROS CENTRALIZADOS
    html.Div([
        html.Div([
            html.Label('Ano:', style={'color': 'white'}),
            dcc.Dropdown(
                id='risco-ano-dropdown',
                options=[{'label': str(ano), 'value': ano} for ano in anos_unicos],
                value=anos_unicos[-1] if anos_unicos else None
            )
        ], style={'width': '22%', 'minWidth': '250px', 'marginRight': '30px'}),      # 'width': '200px', 'margin': '5px'

        html.Div([
            html.Label('Mês:', style={'color': 'white'}),
            dcc.Dropdown(id='risco-mes-dropdown')
        ], style={'width': '22%', 'minWidth': '250px', 'marginRight': '30px'}),          # 'width': '200px', 'margin': '5px'

        html.Div([
            html.Label('Categoria:', style={'color': 'white'}),
            dcc.Dropdown(
                id='risco-categoria-dropdown',
                options=[{'label': 'Todos', 'value': 'Todos'}] + [{'label': cat, 'value': cat} for cat in categorias_unicas],
                value='Renda Fixa',
                clearable=False
            )
        ], style={'width': '22%', 'minWidth': '250px', 'marginRight': '30px'})
    ], style={
        'display': 'flex',
        'justifyContent': 'center',
        'marginBottom': '20px',
        'padding': '0 20px' 
    }),

    
    dcc.Graph(id='grafico-risco'),
    
    dash_table.DataTable(
    id='tabela-risco',
    columns=[
        {'name': 'Ativo', 'id': 'Ativo'},
        {'name': 'Volatilidade Mensal (%)', 'id': 'Volatilidade Mensal (%)'},
        {'name': 'Volatilidade 6 Meses (%)', 'id': 'Volatilidade 6 Meses (%)'},
        {'name': 'Volatilidade 12 Meses (%)', 'id': 'Volatilidade 12 Meses (%)'},
        {'name': 'Volatilidade 24 Meses (%)', 'id': 'Volatilidade 24 Meses (%)'},
        {'name': 'Volatilidade 36 Meses (%)', 'id': 'Volatilidade 36 Meses (%)'},
        {'name': 'Volatilidade Anualizada no Ano (%)', 'id': 'Volatilidade Anualizada no Ano (%)'}
    ],
    data=[],
    style_header={
        'backgroundColor': '#34495e',  
        'color': 'white',              
        'fontWeight': 'bold',
        'fontSize': '12px',
        'border': '1px solid #1f2c3d'  # só borda na cor do primeiro código
    },
    style_cell={
        'backgroundColor': '#2c3e50',  # mantive seu fundo original
        'color': 'white',
        'textAlign': 'center',
        'fontSize': '12px',
        'padding': '5px',
        'minWidth': '100px',
        'maxWidth': '150px',
        'whiteSpace': 'normal',
        'border': '1px solid #1f2c3d'  
    },
    style_table={'marginTop': '20px', 'overflowX': 'auto'},
)

],
style={
    'backgroundColor': '#2c3e50',
    'minHeight': '100vh',
    'padding': '15px 20px 10px 20px'
})





