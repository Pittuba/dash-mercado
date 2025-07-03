
import pandas as pd
from dash import html, dcc, dash_table
import plotly.express as px
from datetime import datetime
import os
# Leitura dos dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
caminho_base = os.path.join(BASE_DIR, "Data", "Base - Indicadores.xlsx")

# os.path.join(os.path.dirname(__file__), 'Base - Indicadores.xlsx')
df_inflacao = pd.read_excel(caminho_base, sheet_name="Inflacao")
df_inflacao['Data'] = pd.to_datetime(df_inflacao['Data'], dayfirst=True)
anos_disponiveis = sorted(df_inflacao['Data'].dt.year.unique())
def meses_por_ano(ano):
    return sorted(df_inflacao[df_inflacao['Data'].dt.year == ano]['Data'].dt.month.unique())
# Layout da aba de inflação
layout = html.Div(style={'backgroundColor': '#34495e', 'padding': '15px 30px 30px 30px', 'fontFamily': 'Arial', 'minHeight': '100vh'}, children=[
    # html.H2("Dashboard de Inflação", style={'color': '#ecf0f1', 'textAlign': 'center', 'fontSize': '30px', 'marginBottom': '30px'}),  # removido
    html.Div([
        html.Div([
            html.Label("Ano:", style={'color': 'white', 'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='inflacao-ano-dropdown',
                options=[{'label': str(ano), 'value': ano} for ano in anos_disponiveis],
                value=anos_disponiveis[-1],
                clearable=False,
                style={'color': '#34495e'}
            )
        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '20px'}),
        html.Div([
            html.Label("Mês:", style={'color': 'white', 'fontWeight': 'bold'}),
            dcc.Dropdown(id='inflacao-mes-dropdown', clearable=False, style={'color': '#34495e'})
        ], style={'width': '30%', 'display': 'inline-block'})
    ], style={'marginBottom': '20px', 'textAlign': 'center'}),  # diminui marginBottom para subir um pouco
    dcc.Graph(id='grafico-inflacao', style={'height': '50vh'}),
    html.Div([
        dash_table.DataTable(
            id='tabela-inflacao',
            style_table={'overflowX': 'auto', 'maxHeight': 'none', 'marginTop': '10px'},
            style_cell={
                'backgroundColor': '#2c3e50',
                'color': 'white',
                'textAlign': 'center',
                'fontSize': 14,
                'padding': '10px',
                'border': '1px solid #1f2c3d'
            },
            style_header={
                'backgroundColor': '#34495e',
                'fontWeight': 'bold',
                'color': '#ecf0f1',
                'border': '1px solid #1f2c3d'
            },
            style_data_conditional=[
    {
        'if': {
            'filter_query': '{IPCA} contains "-"',
            'column_id': 'IPCA'
        },
        'color': 'red'
    },
    {
        'if': {
            'filter_query': '{INPC} contains "-"',
            'column_id': 'INPC'
        },
        'color': 'red'
    },
    {
        'if': {
            'filter_query': '{IGP-M} contains "-"',
            'column_id': 'IGP-M'
        },
        'color': 'red'
    },
    {
        'if': {
            'filter_query': '{Acumulado} contains "-"',
            'column_id': 'Acumulado'
        },
        'color': 'red'
    }
]
        )
    ], style={'textAlign': 'center'})
])
def gerar_grafico_e_tabela(ano, mes):
    # Data inicial = 1 de dezembro do ano anterior (para cálculo do retorno de janeiro)
    data_inicio = pd.Timestamp(year=ano-1, month=12, day=1)
    data_fim = df_inflacao[
        (df_inflacao['Data'].dt.year == ano) & (df_inflacao['Data'].dt.month == mes)
    ]['Data'].max()
    df_filtrado = df_inflacao[(df_inflacao['Data'] >= data_inicio) & (df_inflacao['Data'] <= data_fim)].copy()
    df_filtrado['Mês'] = df_filtrado['Data'].dt.strftime('%b - %y')
    # Calcular retorno mensal
    for indice in ['IPCA', 'INPC', 'IGP-M']:
        df_filtrado[f'Retorno {indice}'] = df_filtrado[indice] / df_filtrado[indice].shift(1) - 1
    # Calcular acumulado
    for indice in ['IPCA', 'INPC', 'IGP-M']:
        df_filtrado[f'Acumulado {indice}'] = ((1 + df_filtrado[f'Retorno {indice}']).cumprod() - 1) * 100
    # Para o gráfico e tabela, remova a linha de dezembro do ano anterior (usada só para cálculo)
    df_exibicao = df_filtrado[df_filtrado['Data'] >= pd.Timestamp(year=ano, month=1, day=1)].copy()
    # Preparar dados para gráfico
    df_melt = df_exibicao.melt(
        id_vars='Mês',
        value_vars=[f'Acumulado IPCA', f'Acumulado INPC', f'Acumulado IGP-M'],
        var_name='Índice',
        value_name='Variação Acumulada (%)'
    )
    df_melt['Índice'] = df_melt['Índice'].replace({
        'Acumulado IPCA': 'IPCA',
        'Acumulado INPC': 'INPC',
        'Acumulado IGP-M': 'IGP-M'
    })
    df_melt['Rótulo'] = df_melt['Variação Acumulada (%)'].round(2).astype(str) + '%'
    df_melt['Variação Acumulada (%)'] = df_melt['Variação Acumulada (%)'] / 100
    # Novo: só mostra rótulo para IPCA e IGP-M, INPC fica sem texto
    df_melt['Rótulo Grafico'] = df_melt.apply(
        lambda row: row['Rótulo'] if row['Índice'] != 'INPC' else '', axis=1
    )
    nome_mes = datetime(1900, mes, 1).strftime('%B').capitalize()
    fig = px.line(
        df_melt, x='Mês', y='Variação Acumulada (%)', color='Índice',
        title=f'Inflação acumulada até {nome_mes} de {ano}',
        template='plotly_dark', markers=True,   
        text='Rótulo Grafico'
)
    fig.update_traces(textposition="top center", textfont_size=12)
    fig.update_layout(
        template='plotly_dark',  # manter modo dark
        paper_bgcolor='#34495e',
        plot_bgcolor='#34495e',
        font=dict(color='#ecf0f1'),
        xaxis_tickangle=0,
        yaxis_tickformat='.1%',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.1,
            xanchor='center',
            x=0.5,
            bgcolor='#34495e',  
            borderwidth=1,
            font=dict(color='black')
        ),
        title_font=dict(color='#ecf0f1', size=20)
)
    # Preparar tabela (usando retornos mensais, excluindo dezembro do ano anterior)
    indices = ['IPCA', 'INPC', 'IGP-M']
    retorno_cols = [f'Retorno {indice}' for indice in indices]
    tabela = df_exibicao[['Mês'] + retorno_cols].copy()
    tabela.columns = ['Mês'] + indices
    tabela = tabela.set_index('Mês').T
    tabela.insert(0, 'Ativo', tabela.index)
    acumulado_valores = {
        indice: ((1 + df_exibicao[f'Retorno {indice}'].dropna()).prod() - 1) * 100 for indice in indices
    }
    tabela['Acumulado'] = tabela['Ativo'].map(lambda x: f"{acumulado_valores.get(x, 0):.2f}%")
    for col in tabela.columns[1:-1]:
        tabela[col] = tabela[col].apply(lambda x: f"{x * 100:.2f}%" if pd.notnull(x) else x)
    colunas = [{'name': col, 'id': col} for col in tabela.columns]
    dados = tabela.to_dict('records')
    fig.add_annotation(
    xref="paper", yref="paper",
    x=0.98, y=1.2,
    showarrow=False,
    text="*Clique 2x no ativo para visualização única",
    font=dict(color="lightgray", size=14),
    align="center"
)
    fig.update_traces(hoverinfo='skip')

    return fig, colunas, dados
