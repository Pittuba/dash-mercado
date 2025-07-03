import pandas as pd
from dash import html, dcc
from dash import dash_table
from dash.dash_table.Format import Format, Scheme
import os

# Caminho base para os dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
caminho_base = os.path.join(BASE_DIR, "Data", "Base - Indicadores.xlsx")

# Leitura da aba Retorno 
df_retorno = pd.read_excel(caminho_base, sheet_name="Retorno")
df_retorno.columns = df_retorno.columns.str.strip()
df_retorno['Data'] = pd.to_datetime(df_retorno['Data'])

df_risco = pd.read_excel(caminho_base, sheet_name="Risco")
df_risco.columns = df_risco.columns.str.strip()
df_risco['Data'] = pd.to_datetime(df_risco['Data'])

# Mapa categoria dos ativos (mantém o seu original)
mapa_categoria = {
    # Pós-fixado (antes 'Renda Fixa - Pós-fixado')
    'NTN-B 2026': 'Pós-fixado (IPCA+)',
    'NTN-B 2027': 'Pós-fixado (IPCA+)',
    'NTN-B 2028': 'Pós-fixado (IPCA+)',
    'NTN-B 2029': 'Pós-fixado (IPCA+)',
    'NTN-B 2030': 'Pós-fixado (IPCA+)',
    'NTN-B 2032': 'Pós-fixado (IPCA+)',
    'NTN-B 2033': 'Pós-fixado (IPCA+)',
    'NTN-B 2035': 'Pós-fixado (IPCA+)',
    'NTN-B 2040': 'Pós-fixado (IPCA+)',
    'NTN-B 2045': 'Pós-fixado (IPCA+)',
    'NTN-B 2050': 'Pós-fixado (IPCA+)',
    'NTN-B 2055': 'Pós-fixado (IPCA+)',
    'NTN-B 2060': 'Pós-fixado (IPCA+)',

    # Tesouro Selic (antes 'Selic'), incluindo LFT
    'LFT 1 3 2026': 'Tesouro Selic',
    'LFT 1 9 2026': 'Tesouro Selic',
    'LFT 1 3 2027': 'Tesouro Selic',
    'LFT 1 9 2027': 'Tesouro Selic',
    'LFT 1 3 2028': 'Tesouro Selic',
    'LFT 1 9 2028': 'Tesouro Selic',

    'CDI': 'Tesouro Selic',
    'IMA-S': 'Tesouro Selic',

    # Renda Fixa - Pré-fixado (mantém igual)
    'NTN-F 2027': 'Renda Fixa - Pré-fixado',
    'NTN-F 2029': 'Renda Fixa - Pré-fixado',
    'NTN-F 2031': 'Renda Fixa - Pré-fixado',
    'NTN-F 2033': 'Renda Fixa - Pré-fixado',
    'NTN-C 2031': 'Renda Fixa - Pré-fixado',

    # Renda Fixa - Pré-fixado
    'NTN-F 2027': 'Renda Fixa - Pré-fixado',
    'NTN-F 2029': 'Renda Fixa - Pré-fixado',
    'NTN-F 2031': 'Renda Fixa - Pré-fixado',
    'NTN-F 2033': 'Renda Fixa - Pré-fixado',
    'NTN-C 2031': 'Renda Fixa - Pré-fixado',

    # Renda Fixa (Índices)
    'IMA-G': 'Renda Fixa',
    'Ima-B': 'Renda Fixa',
    'Ima-B 5': 'Renda Fixa',
    'Ima-B 5+': 'Renda Fixa',
    'IRF-M': 'Renda Fixa',
    'IRF-M 1': 'Renda Fixa',
    'IRF-M 1+': 'Renda Fixa',

    # Selic
    'CDI': 'Selic',
    'IMA-S': 'Selic',
    
    # Crédito
    'IDA DI': 'Crédito',
    'IDA Geral': 'Crédito',
    'IDA IPCA': 'Crédito',
    'Jgp - CDI': 'Crédito',

    # Renda Variável
    'Ibovespa': 'Renda Variável',
    'IBRX': 'Renda Variável',
    'IDIV': 'Renda Variável',
    'Small Caps': 'Renda Variável',
    'Midlarge Cap': 'Renda Variável',
    'IFIX': 'Renda Variável',
    'IVBX-2': 'Renda Variável',
    'IGC-NM': 'Renda Variável',
    'ISEE': 'Renda Variável',
    'ICO-2': 'Renda Variável',

    # Internacional
    'S&P 500': 'Internacional',
    'Nasdaq': 'Internacional',
    'Dólar Ptax': 'Internacional',
    'Euro': 'Internacional',

    # Multimercado
    'IHFA': 'Multimercado',
}

def melt_df(df, valor_nome):
    df_melt = df.melt(id_vars=['Data'], var_name='Ativo', value_name=valor_nome)
    df_melt['Categoria'] = df_melt['Ativo'].map(mapa_categoria)
    return df_melt

# Derretendo o DataFrame de retorno e risco
df_retorno_melt = melt_df(df_retorno, 'Retorno')
df_risco_melt = melt_df(df_risco, 'Risco')

# Fechamentos mensais (para retorno, pode manter se for útil)
df_fechamento = df_retorno.groupby(pd.Grouper(key='Data', freq='ME')).tail(1)

# Anos disponíveis para filtro com base no retorno
anos_unicos = sorted(df_fechamento['Data'].dt.year.unique())

def meses_por_ano(ano):
    dados_ano = df_fechamento[df_fechamento['Data'].dt.year == ano].copy()
    return sorted(dados_ano['Data'].dt.month.unique())

# Categorias únicas
categorias_unicas = [
    'Renda Fixa',
    'Renda Fixa - Pré-fixado',
    'Pós-fixado (IPCA+)',  
    'Tesouro Selic',  
    'Selic',
    'Renda Variável',
    'Crédito',
    'Multimercado',
    'Internacional'
]

opcoes_categorias = [{'label': cat, 'value': cat} for cat in categorias_unicas]

# Layout adaptado para Retorno (mantendo seu estilo)
layout = html.Div(style={'backgroundColor': '#2c3e50', 
                        'paddingTop': '5px',
                        'paddingLeft': '20px',
                        'paddingRight': '20px',
                        'paddingBottom': '20px', 
                        'fontFamily': 'Arial',
                        'minHeight': '100vh',
                        'height': 'auto'}, children=[
    html.Div([
        html.Div([
            html.Label("Ano:", style={'color': '#ecf0f1', 'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='retorno-ano-dropdown',
                options=[{'label': str(ano), 'value': ano} for ano in anos_unicos],
                value=anos_unicos[-1] if anos_unicos else None,
                clearable=False,
                style={'color': 'black', 'backgroundColor': '#ecf0f1'}
            )
        ], style={'width': '15%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginRight': '15px'}),
        html.Div([
            html.Label("Mês:", style={'color': '#ecf0f1', 'fontWeight': 'bold'}),
            dcc.Dropdown(id='retorno-mes-dropdown', clearable=False, style={'color': 'black', 'backgroundColor': '#ecf0f1'})
        ], style={'width': '15%', 'display': 'inline-block', 'marginLeft': '0', 'marginRight': '15px', 'verticalAlign': 'top'}),
        html.Div([
            html.Label("Categoria:", style={'color': '#ecf0f1', 'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='retorno-categoria-dropdown',
                options=opcoes_categorias,
                value='Renda Fixa',
                clearable=False,
                style={'color': 'black', 'backgroundColor': '#ecf0f1'}
            )
        ], style={'width': '25%', 'display': 'inline-block', 'marginLeft': '0', 'marginRight': '15px', 'verticalAlign': 'top'}),
        html.Div([
            html.Label("Intervalo (meses):", style={'color': '#ecf0f1', 'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='retorno-intervalo-dropdown',
                options=[
                    {'label': 'Últimos 3 meses', 'value': 3},
                    {'label': 'Últimos 6 meses', 'value': 6},
                    {'label': 'Últimos 12 meses', 'value': 12},
                    {'label': 'Últimos 24 meses', 'value': 24},
                    {'label': 'Últimos 36 meses', 'value': 36}
                ],
                value=3,
                clearable=False,
                style={'color': 'black', 'backgroundColor': '#ecf0f1'}
            )
        ], style={'width': '25%', 'display': 'inline-block', 'marginLeft': '0', 'verticalAlign': 'top'})
    ], style={'marginBottom': '20px', 'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center', 'gap': '15px'}),

    dcc.Graph(
        id='grafico-retorno',
        style={
            'height': '60vh', 
            'width': '100%',        # remover esse qlq coisa
            'border': '1px solid #1f2c3d',
            'borderRadius': '10px',
            'boxShadow': '0 4px 10px rgba(0, 0, 0, 0.3)',
            'marginBottom': '15px'  # 30
        }
    ),

    html.Div(id='grafico-tabela-wrapper', children=[
        html.Div([
            dash_table.DataTable(
                id='tabela-retorno-varios',
                columns=[
                    {"name": "Ativo", "id": "Ativo"},
                    {"name": "Retorno Mês", "id": "Retorno_mes", "type": "numeric", "format": Format(precision=2, scheme=Scheme.fixed)},
                    {"name": "Retorno (6M)", "id": "Retorno_6", "type": "numeric", "format": Format(precision=2, scheme=Scheme.fixed)},
                    {"name": "Retorno (12M)", "id": "Retorno_12", "type": "numeric", "format": Format(precision=2, scheme=Scheme.fixed)},
                    {"name": "Retorno (24M)", "id": "Retorno_24", "type": "numeric", "format": Format(precision=2, scheme=Scheme.fixed)},
                    {"name": "Retorno (36M)", "id": "Retorno_36", "type": "numeric", "format": Format(precision=2, scheme=Scheme.fixed)},
                    {"name": "Retorno YTD", "id": "Retorno_YTD", "type": "numeric", "format": Format(precision=2, scheme=Scheme.fixed)},
                    {"name": "Risco", "id": "Risco", "type": "numeric", "format": Format(precision=2, scheme=Scheme.fixed)},
                ],
                style_table={
                    'maxHeight': '400px',
                    'overflowY': 'auto',
                    'border': '1px solid #1f2c3d',
                    'backgroundColor': '#34495e',
                    'borderRadius': '10px',
                    'padding': '10px',
                    'boxShadow': '0 4px 10px rgba(0, 0, 0, 0.3)'
                },
                style_cell={
                    'backgroundColor': '#34495e',
                    'textAlign': 'center',
                    'color': '#ecf0f1',
                    'fontSize': 13,
                    'minWidth': '80px',
                    'maxWidth': '90px',
                    'whiteSpace': 'normal',
                    'padding': '4px',
                    'border': '1px solid #2c3e50'
                },
                style_header={
                    'backgroundColor': '#34495e',
                    'color': 'white',
                    'fontWeight': 'bold'
                }
            )
        ], style={'flex': '0 0 55%', 'marginRight': '3%', 'verticalAlign': 'top'}),

        html.Div([
            dcc.Graph(
                id='grafico-risco-retorno',
                style={
                    'minHeight': '300px',
                    'maxHeight': '500px',
                    'height': 'auto',
                    'width': '100%',
                    'maxWidth': '600px',
                    'margin': '0 auto',
                    # 'border': '1px solid #1f2c3d',
                    # 'borderRadius': '10px',
                    'boxShadow': '0 4px 10px rgba(0, 0, 0, 0.3)',
                    'marginLeft': '0 auto'  # move levemente à esquerda   # -10px
                }
            )
        ], style={'flex': '1 1 100%', 'minWidth': '300px','maxWidth': '100%', 'verticalAlign': 'top'})       # 'flex': '0 0 41%',
    ], style={
        'display': 'flex',
        'flexWrap': 'nowrap',
        'justifyContent': 'flex-start',
        'alignItems': 'flex-start',
        'gap': '7px'
    })
])



