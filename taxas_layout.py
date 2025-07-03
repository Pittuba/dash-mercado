import pandas as pd
from dash import html, dcc, dash_table
import re
import os

# ADICIONAR COLUNA DE FECHAMENTO DE TAXA
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path= os.path.join(BASE_DIR, "Data", "Base - Indicadores.xlsx")

# os.path.join(os.path.dirname(__file__), 'Base - Indicadores.xlsx')

# Leitura dos dados
df_taxas = pd.read_excel(file_path, sheet_name='Taxas')
df_retorno = pd.read_excel(file_path, sheet_name='Retorno')  
df_duration = pd.read_excel(file_path, sheet_name='Duration')

# Ajustes datas
df_taxas['Data'] = pd.to_datetime(df_taxas['Data'])
df_retorno['Data'] = pd.to_datetime(df_retorno['Data'])  
df_duration['Data'] = pd.to_datetime(df_duration['Data'])

# Transformação dados taxas
df_taxas_melted = df_taxas.melt(id_vars=['Data'], var_name='Titulo', value_name='Taxas')

# Função para converter porcentagem string para decimal float
def porcentagem_para_decimal(valor):
    if isinstance(valor, str) and valor.endswith('%'):
        try:
            return float(valor.rstrip('%').replace(',', '.')) / 100
        except:
            return None
    elif pd.isna(valor):
        return None
    else:
        try:
            return float(valor)
        except:
            return None

# Normaliza 'Taxas' para decimal
df_taxas_melted['Taxas'] = df_taxas_melted['Taxas'].apply(porcentagem_para_decimal)

# Tipo de indexação: Prefixado, Pós-fixado ou Tesouro Selic
def classificar_tipo(titulo):
    titulo_lower = titulo.lower()
    if 'lft' in titulo_lower:
        return 'Pós Fixado (Selic)'
    elif 'ntn-b' in titulo_lower:
        return 'Pós Fixado (IPCA)'
    elif 'ntn-c' in titulo_lower:
        return 'Pós Fixado (IGP-M)'
    else:
        return 'Pré-fixados'

df_taxas_melted['Tipo'] = df_taxas_melted['Titulo'].apply(classificar_tipo)

# Função para extrair ano de vencimento do título
def extrair_ano_venc(titulo):
    anos = re.findall(r'20\d{2}', titulo)
    if anos:
        return int(anos[-1])
    return None

df_taxas_melted['AnoVencimento'] = df_taxas_melted['Titulo'].apply(extrair_ano_venc)

# Duration transformado
df_duration_melted = df_duration.melt(id_vars=['Data'], var_name='Titulo', value_name='Duration')

# Converter Duration para numérico (float), para evitar problemas
df_duration_melted['Duration'] = pd.to_numeric(df_duration_melted['Duration'], errors='coerce')

# Merge das taxas com duration usando outer para manter todos ativos de ambas abas
df_merged = pd.merge(
    df_taxas_melted,
    df_duration_melted,
    how='outer',  # manter todos ativos de ambos os datasets
    on=['Data', 'Titulo']
)

# Preencher NaNs após merge (para evitar erros na agregação)
df_merged['Taxas'] = df_merged['Taxas'].fillna(0)
df_merged['Duration'] = df_merged['Duration'].fillna(0)

# Garantir tipos numéricos coerentes
df_merged['Taxas'] = pd.to_numeric(df_merged['Taxas'], errors='coerce').fillna(0)
df_merged['Duration'] = pd.to_numeric(df_merged['Duration'], errors='coerce').fillna(0)

# Preparar coluna Duration formatada para a tabela (com "-" nos valores originalmente ausentes)
def formatar_duration(valor):
    if valor == 0:
        return '-'
    else:
        return round(float(valor), 2)

df_merged['Duration'] = df_merged['Duration'].apply(formatar_duration)

# Fechamentos mensais para dropdown (mantido o uso de df_taxas)
fechamentos_df = df_taxas.groupby(pd.Grouper(key='Data', freq='ME')).tail(1)
anos_disponiveis = sorted(fechamentos_df['Data'].dt.year.unique())

def meses_por_ano(ano):
    return sorted(fechamentos_df[fechamentos_df['Data'].dt.year == ano]['Data'].dt.month.unique())

def adicionar_fechamento_na_data(df_base, df_taxas, data_selecionada):
    
    df_fechamento = df_taxas[df_taxas['Data'] == data_selecionada][['Titulo', 'Taxas']].rename(columns={'Taxas': 'Fechamento'})
    df_result = pd.merge(df_base, df_fechamento, how='left', left_on='Titulo', right_on='Titulo')

    return df_result

# Layout do dashboard da aba Taxas (mantido igual)
layout = html.Div(style={'backgroundColor': '#34495e', 'padding': '20px', 'minHeight': '100vh'}, children=[

    # Linha de filtros (com whiteSpace para alinhar horizontalmente)
    html.Div([

        html.Div([  # Ano
            html.Label("Ano:", style={'color': '#ecf0f1'}),
            dcc.Dropdown(
                id='taxas-ano-dropdown',
                options=[{'label': str(ano), 'value': ano} for ano in anos_disponiveis],
                value=anos_disponiveis[-1] if anos_disponiveis else None,
                clearable=False,
                style={
                    'color': '#ecf0f1',
                    'backgroundColor': '#2c3e50',
                    'borderColor': '#1f2c3d',
                    'borderRadius': '4px'
                }
            ),
        ], style={'width': '7%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginRight': '1%'}),

        html.Div([  # Mês
            html.Label("Mês:", style={'color': '#ecf0f1'}),
            dcc.Dropdown(
                id='taxas-mes-dropdown',
                clearable=False,
                style={
                    'color': '#ecf0f1',
                    'backgroundColor': '#2c3e50',
                    'borderColor': '#1f2c3d',
                    'borderRadius': '4px'
                }
            )
        ], style={'width': '8%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginRight': '1%'}),

        html.Div([  # Ano de Vencimento
            html.Label("Ano de Vencimento:", style={'color': '#ecf0f1'}),
            dcc.Dropdown(
                id='taxas-venc-dropdown',
                options=[{'label': str(ano), 'value': ano} for ano in sorted(df_taxas_melted['AnoVencimento'].dropna().unique())],
                value=None,
                clearable=True,
                multi=True,
                style={
                    'color': '#ecf0f1',
                    'backgroundColor': '#2c3e50',
                    'borderColor': '#1f2c3d',
                    'borderRadius': '4px'
                }
            ),
        ], style={'width': '15%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginRight': '1%'}),

        html.Div([  # Intervalo
            html.Label("Intervalo:", style={'color': '#ecf0f1'}),
            dcc.Dropdown(
                id='taxas-periodo-dropdown',
                options=[
                    {'label': '3 meses', 'value': 3},
                    {'label': '6 meses', 'value': 6},
                    {'label': '12 meses', 'value': 12},
                    {'label': '24 meses', 'value': 24},
                    {'label': '36 meses', 'value': 36},
                ],
                value=12,
                clearable=False,
                style={
                    'color': '#ecf0f1',
                    'backgroundColor': '#2c3e50',
                    'borderColor': '#1f2c3d',
                    'borderRadius': '4px',
                    'height': '35px'
                }
            )
        ], style={'width': '8%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginRight': '1%'}),

        html.Div([  # Tipo de Indexação
    html.Label("Tipo de Indexação:", style={'color': '#ecf0f1'}),
    html.Div(
        dcc.RadioItems(
            id='taxas-tipo-radio',
            options=[
                {'label': 'Pré-fixados', 'value': 'Pré-fixados'},
                {'label': 'Pós Fixado (IPCA)', 'value': 'Pós Fixado (IPCA)'},
                {'label': 'Pós Fixado (Selic)', 'value': 'Pós Fixado (Selic)'},
                {'label': 'Pós Fixado (IGP-M)', 'value': 'Pós Fixado (IGP-M)'}
            ],
            value='Pré-fixados',
            labelStyle={'display': 'inline-block', 'marginRight': '10px', 'color': '#ecf0f1','fontSize': '15px',},
            style={
                'backgroundColor': '#2c3e50',
                'padding': '3px 6px',
                'borderRadius': '4px',
                'height': '30px',
                # 'border': '1.5px solid #1f2c3d',  <-- Removido daqui
                'display': 'flex',
                'alignItems': 'center',
                'justifyContent': 'center',
            }
        ),
        style={
            'border': '1.5px solid #1f2c3d',  # Mantém só essa borda
            'borderRadius': '4px',
            'padding': '5px',
            'backgroundColor': '#2c3e50',
            'height': '36px',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
        }
    )
], style={'width': '47%', 'minWidth': '400px','display': 'inline-block', 'verticalAlign': 'top'}),

    ], style={
        'display': 'flex',
        'justifyContent': 'center',
        'gap': '0.2%',  # mantém a margem entre os filtros, já que você usa marginRight em cada um
        'flexWrap': 'nowrap',
        'whiteSpace': 'nowrap',
        'padding': '0 5px'
    }),

    dcc.Graph(
        id='grafico-taxas',
        style={'marginBottom': '10px'},
        figure={
            'layout': {
                'plot_bgcolor': '#34495e',
                'paper_bgcolor': '#34495e',
                'font': {'color': '#ecf0f1'},
            }
        }
    ),

    dash_table.DataTable(
        id='tabela-taxas',
        columns=[
            {'name': 'Ativo', 'id': 'Ativo'},
            {'name': 'Fechamento (%)', 'id': 'Fechamento (%)', 'type': 'numeric', 'format': {'specifier': '.4f'}},
            {'name': 'Basis Points (Mês)', 'id': 'BP_Mes', 'type': 'numeric', 'format': {'specifier': '.2f'}},
            {'name': 'Basis Points (Ano)', 'id': 'BP_Ano', 'type': 'numeric', 'format': {'specifier': '.2f'}},
            {'name': 'Duration', 'id': 'Duration', 'type': 'text'}
        ],
        data=[],
        style_header={
            'backgroundColor': '#34495e',
            'color': '#ecf0f1',
            'fontWeight': 'bold'
        },
        style_cell={
            'backgroundColor': '#2c3e50',
            'color': '#ecf0f1',
            'textAlign': 'center',
            'border': '1px solid #1f2c3d'
        },
        style_table={'overflowX': 'auto'},
        page_size=15,
    ),

    dcc.Store(id='tabela-retorno-store'),
    dcc.Store(id='tabela-bp-store'),
    dcc.Store(id='tabela-duration-store')

])



