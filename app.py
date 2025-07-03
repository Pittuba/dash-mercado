# ADICIONAR TAXAS DE LTN - VER VENCIMENTOS DISPONIVEIS

import dash
from dash import dcc, html, Input, Output, no_update
import plotly.express as px
import plotly.express as go
import pandas as pd
import calendar
from dash import dash_table
from dash.dependencies import Input, Output, State
import os
from dateutil.relativedelta import relativedelta
from datetime import datetime
import numpy as np

# Importar layouts e dados
from retorno_layout import layout as layout_retorno, df_retorno_melt, df_retorno, meses_por_ano as meses_retorno
from volatilidade_layout import layout as layout_risco, df_risco_melt as df_risco_melt_vol, meses_por_ano as meses_risco
from taxas_layout import layout as layout_taxas, fechamentos_df, df_taxas_melted, df_duration_melted, meses_por_ano as meses_taxas
from inflacao_layout import layout as layout_inflacao, df_inflacao, meses_por_ano as meses_inflacao, gerar_grafico_e_tabela
from geral import layout as layout_geral, evolucao_taxas_3_meses_excel
from geral import layout, carregar_dados_retorno, calcular_retorno_acumulado_6m, criar_grafico_retorno_acumulado, calcular_retorno_acumulado_por_periodo, df_ret, criar_componente_retorno_ativo, carregar_dados_inflacao, obter_retorno_mensal_completo
from geral import indicadores

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.layout = html.Div([
    dcc.Tabs(id="tabs", value='geral', children=[
        dcc.Tab(label='📊 Geral', value='geral',
                style={'backgroundColor': '#444444', 'color': 'white', 'borderRight': '2px solid #222222'},
                selected_style={'backgroundColor': '#666666', 'color': '#34495e', 'borderRight': '2px solid #222222'}),
        dcc.Tab(label='💰 Retorno', value='retorno',
                style={'backgroundColor': '#444444', 'color': 'white', 'borderRight': '2px solid #222222'},
                selected_style={'backgroundColor': '#666666', 'color': '#34495e', 'borderRight': '2px solid #222222'}),
        dcc.Tab(label='⚠️ Risco', value='risco',
                style={'backgroundColor': '#444444', 'color': 'white', 'borderRight': '2px solid #222222'},
                selected_style={'backgroundColor': '#666666', 'color': '#34495e', 'borderRight': '2px solid #222222'}),
        dcc.Tab(label='📉 Inflação', value='inflacao',
                style={'backgroundColor': '#444444', 'color': 'white', 'borderRight': '2px solid #222222'},
                selected_style={'backgroundColor': '#666666', 'color': '#34495e', 'borderRight': '2px solid #222222'}),
        dcc.Tab(label='📈 Taxas', value='taxas',
                style={'backgroundColor': '#444444', 'color': 'white'},  # última aba, sem borda direita
                selected_style={'backgroundColor': '#666666', 'color': '#34495e'}),
    ]),
    html.Div(id='tabs-content')
])

# Dicionário com layouts para as abas
layouts = {
    'geral': layout_geral, 
    'retorno': layout_retorno,
    'risco': layout_risco,
    'inflacao': layout_inflacao,
    'taxas': layout_taxas
}
@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value')
)
def render_content(tab):
    return layouts.get(tab, html.Div("Aba não encontrada"))
# =================== ABA RETORNO ===================
from pandas.tseries.offsets import MonthEnd

@app.callback(
    Output('retorno-mes-dropdown', 'options'),
    Output('retorno-mes-dropdown', 'value'),
    Input('retorno-ano-dropdown', 'value')
)
def update_meses_retorno(ano):
    if ano is None:
        return [], None
    meses = [m for m in meses_retorno(ano) if pd.notnull(m) and 1 <= m <= 12]
    if not meses:
        return [], None
    opcoes = [{'label': calendar.month_name[m], 'value': m} for m in meses]
    return opcoes, meses[-1]

@app.callback(
    Output('grafico-retorno', 'figure'),
    Input('retorno-ano-dropdown', 'value'),
    Input('retorno-mes-dropdown', 'value'),
    Input('retorno-categoria-dropdown', 'value'),
    Input('retorno-intervalo-dropdown', 'value')
)
def atualizar_grafico_precos(ano, mes, categoria, intervalo):
    if None in [ano, mes, categoria, intervalo]:
        return {}

    dia_fim = calendar.monthrange(ano, mes)[1]
    data_fim = pd.Timestamp(year=ano, month=mes, day=dia_fim)
    data_inicio = (data_fim - relativedelta(months=intervalo - 1)).replace(day=1)

    df_filtrado = df_retorno_melt[
        (df_retorno_melt['Data'] >= data_inicio) & (df_retorno_melt['Data'] <= data_fim)
    ].copy()

    if categoria != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Categoria'] == categoria]

    if df_filtrado.empty:
        return {}

    df_filtrado.sort_values(by=['Ativo', 'Data'], inplace=True)
    df_filtrado['RetornoAcumulado'] = df_filtrado.groupby('Ativo')['Retorno'].transform(
        lambda x: (1 + x).cumprod() - 1
    )

    fig = px.line(
        df_filtrado,
        x='Data',
        y='RetornoAcumulado',
        color='Ativo',
        markers=True,
        template='plotly_dark'
    )

    fig.update_layout(
        title=f"Retorno Acumulado - {intervalo} Meses",
        title_x=0.05,
        title_y=0.98,
        title_font=dict(size=16, color='white'),
        paper_bgcolor='#34495e',
        plot_bgcolor='#34495e',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=0.85,
            xanchor='center',
            x=0.5,
            font=dict(color='white')
        ),
        hovermode=False,
        yaxis=dict(tickformat=".1f", color='white', automargin=True),
        annotations=[
            dict(
                text='*Clique 2x no ativo para visualização única',
                xref='paper', yref='paper',
                x=0.98, y=1.05,     
                showarrow=False,
                font=dict(size=12, color='white')
            )
        ],
        margin=dict(l=10, r=10, t=20, b=30),  # margens reduzidas para usar mais espaço
        autosize=True,
)

    fig.update_xaxes(domain=[0.05, 0.95])  # ocupa quase toda largura
    fig.update_yaxes(domain=[0.05, 0.85])  # ocupa quase toda altura

    fig.update_xaxes(title_text=None)
    fig.update_yaxes(tickformat=".0%", title_text=None)
    fig.update_traces(hoverinfo='skip', hovertemplate=None)

    return fig

@app.callback(
    Output('tabela-retorno-varios', 'data'),
    Input('retorno-ano-dropdown', 'value'),
    Input('retorno-mes-dropdown', 'value'),
    Input('retorno-categoria-dropdown', 'value'),
    Input('retorno-intervalo-dropdown', 'value')
)
def atualizar_tabela_retorno(ano, mes, categoria, intervalo):
    if None in [ano, mes, categoria, intervalo]:
        return []

    # Define a data final com base no ano e mês selecionados
    data_fim = pd.Timestamp(year=ano, month=mes, day=1) + pd.offsets.MonthEnd(0)

    # Filtra por categoria
    df_base = df_retorno_melt.copy()
    if categoria != 'Todos':
        df_base = df_base[df_base['Categoria'] == categoria]

    if df_base.empty:
        return []

    # Retorno do mês selecionado (não acumulado)
    df_retorno_mes = df_base[
        (df_base['Data'].dt.year == ano) & (df_base['Data'].dt.month == mes)
    ].groupby('Ativo')['Retorno'].sum().reset_index()
    df_retorno_mes.rename(columns={'Retorno': 'Retorno_mes'}, inplace=True)
    df_retorno_mes['Retorno_mes'] *= 100

    # Define função de cálculo do retorno acumulado por período (em meses), exceto 3 meses
    def retorno_acumulado_por_periodo(meses):
        data_inicio = (data_fim - pd.DateOffset(months=meses - 1)).replace(day=1)
        df_periodo = df_base[(df_base['Data'] >= data_inicio) & (df_base['Data'] <= data_fim)].copy()
        retorno = df_periodo.groupby('Ativo')['Retorno'].apply(lambda x: (1 + x).prod() - 1)
        retorno = retorno.reset_index(name=f'Retorno_{meses}')
        retorno[f'Retorno_{meses}'] *= 100
        return retorno

    # Retornos acumulados para 6, 12, 24, 36 meses (sem o de 3 meses)
    retornos = [retorno_acumulado_por_periodo(m) for m in [6, 12, 24, 36]]

    # Retorno YTD
    def retorno_ytd():
        data_inicio_ano = pd.Timestamp(year=ano, month=1, day=1)
        df_ytd = df_base[(df_base['Data'] >= data_inicio_ano) & (df_base['Data'] <= data_fim)].copy()
        retorno = df_ytd.groupby('Ativo')['Retorno'].apply(lambda x: (1 + x).prod() - 1)
        retorno = retorno.reset_index(name='Retorno_YTD')
        retorno['Retorno_YTD'] *= 100
        return retorno

    retorno_ytd_df = retorno_ytd()

    # Cálculo do risco (volatilidade) anualizada com base no intervalo selecionado
    data_inicio_risco = (data_fim - pd.DateOffset(months=intervalo - 1)).replace(day=1)
    df_risco_periodo = df_base[(df_base['Data'] >= data_inicio_risco) & (df_base['Data'] <= data_fim)].copy()
    risco = df_risco_periodo.groupby('Ativo')['Retorno'].std().reset_index()
    risco['Risco'] = risco['Retorno'] * (252 ** 0.5) * 100
    risco.drop(columns='Retorno', inplace=True)

    # Junta todos os DataFrames - começa com Retorno_mes
    df_final = df_retorno_mes

    for df_r in retornos:
        df_final = df_final.merge(df_r, on='Ativo', how='outer')

    df_final = df_final.merge(retorno_ytd_df, on='Ativo', how='outer')
    df_final = df_final.merge(risco, on='Ativo', how='outer')

    df_final = df_final.round(2)

    return df_final.to_dict('records')

@app.callback(
    Output('grafico-risco-retorno', 'figure'),
    Input('retorno-ano-dropdown', 'value'),
    Input('retorno-mes-dropdown', 'value'),
    Input('retorno-categoria-dropdown', 'value'),
    Input('retorno-intervalo-dropdown', 'value')
)
def atualizar_grafico(ano, mes, categoria, intervalo):
    if None in [ano, mes, categoria, intervalo]:
        return {}

    dia_fim = calendar.monthrange(ano, mes)[1]
    data_fim = pd.Timestamp(year=ano, month=mes, day=dia_fim)
    mes_inicio = mes - intervalo + 1
    ano_inicio = ano
    if mes_inicio <= 0:
        ano_inicio -= 1
        mes_inicio += 12
    data_inicio = pd.Timestamp(year=ano_inicio, month=mes_inicio, day=1)

    df_filtrado = df_retorno_melt[
        (df_retorno_melt['Data'] >= data_inicio) & (df_retorno_melt['Data'] <= data_fim)
    ].copy()
    if categoria != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Categoria'] == categoria]
    if df_filtrado.empty:
        return {}

    df_filtrado.sort_values(by=['Ativo', 'Data'], inplace=True)
    data_fim_real = df_filtrado['Data'].max()

    def retorno_ytd(df, data_fim):
        data_inicio_ano = pd.Timestamp(year=data_fim.year, month=1, day=1)
        df_ytd = df[(df['Data'] >= data_inicio_ano) & (df['Data'] <= data_fim)]
        retorno = df_ytd.groupby('Ativo')['Retorno'].apply(
            lambda x: (1 + x).prod() - 1
        ).reset_index(name='Retorno_YTD')
        retorno['Retorno_YTD'] = retorno['Retorno_YTD'] * 100
        return retorno

    retorno_ytd_df = retorno_ytd(df_filtrado, data_fim_real)

    risco = df_filtrado.groupby('Ativo')['Retorno'].std().reset_index()
    risco['Risco'] = risco['Retorno'] * (252 ** 0.5) * 100
    risco.drop(columns=['Retorno'], inplace=True)

    df_final = pd.merge(retorno_ytd_df, risco, on='Ativo', how='inner')
    df_final = df_final.round(2)

    fig = px.scatter(
    df_final,
    x='Risco',
    y='Retorno_YTD',
    text='Ativo',
    labels={'Risco': 'Risco (%)', 'Retorno_YTD': 'Retorno YTD (%)'},
    title='Risco x Retorno (YTD)',
    template='plotly_dark'
)

    fig.update_traces(textposition='top center')

    fig.update_layout(
        height=375,
        title={
            'text': 'Risco x Retorno (YTD)',
            'font': {'size': 13},
            'x': 0.5,
            'xanchor': 'center'
    },
        margin=dict(l=20, r=20, t=40, b=30),  # margens mais compactas
        plot_bgcolor='#34495e',
        paper_bgcolor='#34495e',
        xaxis=dict(
            title=dict(
                text='Risco (%)',
                font=dict(size=11)
            ),
            tickfont=dict(size=10)
        ),
        yaxis=dict(
                title=dict(
                    text='Retorno (%)',
                    font=dict(size=11)
                ),
                tickfont=dict(size=10)
        )

)

    return fig

# =================== ABA RISCO ===================
@app.callback(
    Output('risco-mes-dropdown', 'options'),
    Output('risco-mes-dropdown', 'value'),
    Input('risco-ano-dropdown', 'value')
)
def update_meses_risco(ano):
    if ano is None:
        return [], None
    meses = [m for m in meses_risco(ano) if pd.notnull(m) and 1 <= m <= 12]
    if not meses:
        return [], None
    opcoes = [{'label': calendar.month_name[m], 'value': m} for m in meses]
    return opcoes, meses[-1]
@app.callback(
    Output('grafico-risco', 'figure'),
    Input('risco-ano-dropdown', 'value'),
    Input('risco-mes-dropdown', 'value'),
    Input('risco-categoria-dropdown', 'value')   # novo input
)
def atualizar_grafico_risco(ano, mes, categoria):
    if ano is None or mes is None or categoria is None:
        return {}
    data_inicio = pd.Timestamp(year=ano, month=1, day=1)
    data_fim = df_risco_melt_vol[(df_risco_melt_vol['Data'].dt.year == ano) & (df_risco_melt_vol['Data'].dt.month == mes)]['Data'].max()
    if pd.isna(data_fim):
        return {}
    df_filtrado = df_risco_melt_vol[(df_risco_melt_vol['Data'] >= data_inicio) & (df_risco_melt_vol['Data'] <= data_fim)].copy()
    # Filtra pela categoria, se não for 'Todos'
    if categoria != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Categoria'] == categoria]
    if df_filtrado.empty:
        return {}
    fig = px.line(df_filtrado, x='Data', y='Volatilidade', color='Ativo',
                  title='Volatilidade (Risco)', markers=True, template='plotly_dark')
    fig.update_traces(hoverinfo='skip')

    fig.update_layout(
    paper_bgcolor='#34495e',
    plot_bgcolor='#34495e',
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.05,
        xanchor='center',
        x=0.5,
        font=dict(color='white')
    ),
    annotations=[
        dict(
            text="*Clique 2x no ativo para visualização única",
            xref="paper",
            yref="paper",
            x=0.99,
            y=1.25,
            showarrow=False,
            font=dict(color="white", size=13),
            align="right"
        )
    ]
)

    return fig

@app.callback(
    Output('tabela-risco', 'data'),
    Input('risco-ano-dropdown', 'value'),
    Input('risco-mes-dropdown', 'value'),
    Input('risco-categoria-dropdown', 'value')
)
def atualizar_tabela_risco(ano, mes, categoria):
    if ano is None or mes is None or categoria is None:
        return []

    try:
        df_retorno = df_retorno_melt.copy()
        df_volatilidade = df_risco_melt_vol.copy()

        # Data final do período: último dia do mês selecionado
        dia_final = calendar.monthrange(ano, mes)[1]
        data_fim = pd.Timestamp(year=ano, month=mes, day=dia_final)

        # Função para calcular volatilidade anualizada para N meses anteriores a data_fim
        def vol_periodo_por_data(df, meses):
            data_inicio_periodo = (data_fim - pd.DateOffset(months=meses - 1)).replace(day=1)
            df_periodo = df[(df['Data'] >= data_inicio_periodo) & (df['Data'] <= data_fim)]
            rets = df_periodo['Retorno'].dropna().values
            if len(rets) < 2:
                return np.nan
            return np.std(rets, ddof=1) * np.sqrt(252)

        # Filtra categoria, se aplicável
        if categoria != 'Todos':
            df_retorno = df_retorno[df_retorno['Categoria'] == categoria]
            df_volatilidade = df_volatilidade[df_volatilidade['Categoria'] == categoria]

        resultados = []

        for ativo in df_retorno['Ativo'].unique():
            df_ret = df_retorno[df_retorno['Ativo'] == ativo].copy()
            df_vol = df_volatilidade[df_volatilidade['Ativo'] == ativo].copy()

            # Volatilidade mensal do mês selecionado
            df_vol_mes = df_vol[df_vol['Data'].dt.to_period('M') == data_fim.to_period('M')]
            vol_mensal = df_vol_mes['Volatilidade'].dropna().values[-1] if not df_vol_mes.empty else np.nan

            vol_6m = vol_periodo_por_data(df_ret, 6)
            vol_12m = vol_periodo_por_data(df_ret, 12)
            vol_24m = vol_periodo_por_data(df_ret, 24)
            vol_36m = vol_periodo_por_data(df_ret, 36)

            # Volatilidade anualizada no ano corrente até data_fim
            df_ano = df_ret[(df_ret['Data'] >= pd.Timestamp(year=ano, month=1, day=1)) & (df_ret['Data'] <= data_fim)]
            retornos_ano = df_ano['Retorno'].dropna().values
            vol_ano = np.std(retornos_ano, ddof=1) * np.sqrt(252) if len(retornos_ano) >= 2 else np.nan

            resultados.append({
                'Ativo': ativo,
                'Volatilidade Mensal (%)': round(vol_mensal * 100, 2) if pd.notnull(vol_mensal) else 0.0,
                'Volatilidade 6 Meses (%)': round(vol_6m * 100, 2) if pd.notnull(vol_6m) else 0.0,
                'Volatilidade 12 Meses (%)': round(vol_12m * 100, 2) if pd.notnull(vol_12m) else 0.0,
                'Volatilidade 24 Meses (%)': round(vol_24m * 100, 2) if pd.notnull(vol_24m) else 0.0,
                'Volatilidade 36 Meses (%)': round(vol_36m * 100, 2) if pd.notnull(vol_36m) else 0.0,
                'Volatilidade Anualizada no Ano (%)': round(vol_ano * 100, 2) if pd.notnull(vol_ano) else 0.0,
            })

        return resultados

    except Exception as e:
        print(f"[Erro atualizar tabela risco]: {e}")
        return []

# =================== ABA INFLAÇÃO ===================
@app.callback(
    [Output('inflacao-mes-dropdown', 'options'),
     Output('inflacao-mes-dropdown', 'value')],
    Input('inflacao-ano-dropdown', 'value')
)
def atualizar_meses_inflacao(ano):
    if ano is None:
        return [], None
    meses = meses_inflacao(ano)
    if not meses:
        return [], None
    opcoes = [{'label': calendar.month_name[mes], 'value': mes} for mes in meses]
    return opcoes, meses[-1]
@app.callback(
    [Output('grafico-inflacao', 'figure'),
     Output('tabela-inflacao', 'columns'),
     Output('tabela-inflacao', 'data')],
    [Input('inflacao-ano-dropdown', 'value'),
     Input('inflacao-mes-dropdown', 'value')]
)
def atualizar_grafico_tabela_inflacao(ano, mes):
    if ano is None or mes is None:
        return no_update, no_update, no_update
    fig, colunas, dados = gerar_grafico_e_tabela(ano, mes)
    return fig, colunas, dados
# =================== ABA TAXAS ===================
def meses_taxas(ano):
    return sorted(fechamentos_df[fechamentos_df['Data'].dt.year == ano]['Data'].dt.month.unique())

@app.callback(
    [Output('taxas-mes-dropdown', 'options'),
     Output('taxas-mes-dropdown', 'value')],
    Input('taxas-ano-dropdown', 'value')
)
def update_meses_taxas(ano):
    if ano is None:
        return [], None
    meses = meses_taxas(ano)
    if not meses:
        return [], None
    opcoes = [{'label': calendar.month_name[mes], 'value': mes} for mes in meses]
    return opcoes, meses[-1]

@app.callback(
    Output('grafico-taxas', 'figure'),
    [
        Input('taxas-ano-dropdown', 'value'),
        Input('taxas-mes-dropdown', 'value'),
        Input('taxas-tipo-radio', 'value'),
        Input('taxas-venc-dropdown', 'value'),
        Input('taxas-periodo-dropdown', 'value')
    ]
)
def atualizar_grafico_taxas(ano, mes, tipo_indexacao, anos_venc, periodo_meses):
    if None in [ano, mes, periodo_meses]:
        return go.Figure(layout=dict(
            title='Sem dados disponíveis',
            template='plotly_dark',
            paper_bgcolor='#34495e',
            plot_bgcolor='#34495e'
        ))

    try:
        dia_final = calendar.monthrange(ano, mes)[1]
        data_fim = pd.Timestamp(year=ano, month=mes, day=dia_final)
        data_fim = pd.Timestamp(year=ano, month=mes, day=calendar.monthrange(ano, mes)[1])
        data_inicio = data_fim - pd.DateOffset(months=periodo_meses - 1)
        data_inicio = data_inicio.replace(day=1)  # Garante início do mês

    except Exception as e:
        print(f"[Erro datas]: {e}")
        return go.Figure()

    df_filtrado = df_taxas_melted[
        (df_taxas_melted['Data'] >= data_inicio) & 
        (df_taxas_melted['Data'] <= data_fim)
    ].copy()

    if tipo_indexacao and tipo_indexacao != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Tipo'] == tipo_indexacao]

    if anos_venc:
        if isinstance(anos_venc, list):
            df_filtrado = df_filtrado[df_filtrado['AnoVencimento'].isin(anos_venc)]
        else:
            df_filtrado = df_filtrado[df_filtrado['AnoVencimento'] == anos_venc]

    df_filtrado = df_filtrado[df_filtrado['Taxas'].notnull()]

    if df_filtrado.empty:
        return go.Figure(layout=dict(
            title='Sem dados disponíveis para os filtros selecionados',
            template='plotly_dark',
            paper_bgcolor='#34495e',
            plot_bgcolor='#34495e'
        ))

    fig = px.line(
        df_filtrado,
        x='Data',
        y='Taxas',
        color='Titulo',
        title='Evolução das Taxas dos Títulos',
        markers=True,
        template='plotly_dark'
    )
    fig.update_traces(hoverinfo='skip')

    fig.update_layout(
    yaxis=dict(
        tickformat=',.1%',  
        title='Taxa',
        color='white'  # para o texto ficar visível no tema dark
    ),
    paper_bgcolor='#34495e',
    plot_bgcolor='#34495e',
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.05,
        xanchor='center',
        x=0.5,
        font=dict(color='white')
    ),
    annotations=[
        dict(
            x=1,
            y=1.3,
            xref='paper',
            yref='paper',
            text='*Clique 2x no ativo para visualização única',
            showarrow=False,
            font=dict(color='white', size=12),
            align='right',
            xanchor='right',
            yanchor='top'
        )
    ]
)

    return fig

@app.callback(
    Output('grafico-duration', 'figure'),
    Input('taxas-ano-dropdown', 'value'),
    Input('taxas-mes-dropdown', 'value')
)
def atualizar_grafico_duration(ano, mes):
    if ano is None or mes is None or df_duration_melted.empty:
        return go.Figure()

    data_inicio = pd.Timestamp(year=ano, month=1, day=1)
    dia_final = calendar.monthrange(ano, mes)[1]
    data_fim = pd.Timestamp(year=ano, month=mes, day=dia_final)

    df_filtrado = df_duration_melted[
        (df_duration_melted['Data'] >= data_inicio) &
        (df_duration_melted['Data'] <= data_fim)
    ].copy()

    fig = px.line(
        df_filtrado, x='Data', y='Duration', color='Titulo',
        title='Duration', markers=True, template='plotly_dark'
    )
    fig.update_layout(paper_bgcolor='#34495e', plot_bgcolor='#34495e')
    return fig

@app.callback(
    Output('tabela-taxas', 'data'),
    [
        Input('taxas-ano-dropdown', 'value'),
        Input('taxas-mes-dropdown', 'value'),
        Input('taxas-tipo-radio', 'value'),
        Input('taxas-venc-dropdown', 'value'),
        Input('taxas-periodo-dropdown', 'value')
    ]
)
def atualizar_tabela_taxas(ano, mes, tipo_indexacao, anos_venc, periodo_meses):
    if None in [ano, mes, periodo_meses]:
        return []

    try:
        dia_final = calendar.monthrange(ano, mes)[1]
        data_fim = pd.Timestamp(year=ano, month=mes, day=dia_final)
        data_inicio = data_fim - pd.DateOffset(months=periodo_meses - 1)
        data_inicio = data_inicio.replace(day=1)

    except Exception as e:
        print(f"[Erro datas]: {e}")
        return []

    df_filtrado = df_taxas_melted[
        (df_taxas_melted['Data'] >= data_inicio) & 
        (df_taxas_melted['Data'] <= data_fim)
    ].copy()

    if tipo_indexacao:
        df_filtrado = df_filtrado[df_filtrado['Tipo'] == tipo_indexacao]

    if anos_venc:
        if isinstance(anos_venc, list):
            df_filtrado = df_filtrado[df_filtrado['AnoVencimento'].isin(anos_venc)]
        else:
            df_filtrado = df_filtrado[df_filtrado['AnoVencimento'] == anos_venc]

    df_filtrado = df_filtrado[df_filtrado['Taxas'].notnull()]
    if df_filtrado.empty:
        return []

    data_inicio_mes = pd.Timestamp(year=ano, month=mes, day=1)
    dia_final_mes = calendar.monthrange(ano, mes)[1]
    data_fim_mes = pd.Timestamp(year=ano, month=mes, day=dia_final_mes)
    data_inicio_ano = pd.Timestamp(year=ano, month=1, day=1)

    df_mensal = df_filtrado[(df_filtrado['Data'] >= data_inicio_mes) & (df_filtrado['Data'] <= data_fim_mes)]
    df_inicio_mes = df_mensal.groupby('Titulo')['Data'].min().reset_index().merge(df_mensal, on=['Titulo', 'Data'])
    df_fim_mes = df_mensal.groupby('Titulo')['Data'].max().reset_index().merge(df_mensal, on=['Titulo', 'Data'])
    df_bp_mensal = df_inicio_mes[['Titulo', 'Taxas']].rename(columns={'Taxas': 'Taxa_Inicial'}) \
        .merge(df_fim_mes[['Titulo', 'Taxas']].rename(columns={'Taxas': 'Taxa_Final'}), on='Titulo')
    df_bp_mensal['BP_Mes'] = (df_bp_mensal['Taxa_Final'] - df_bp_mensal['Taxa_Inicial']) * 10000
    df_bp_mensal = df_bp_mensal[['Titulo', 'BP_Mes']]

    df_anual = df_filtrado[(df_filtrado['Data'] >= data_inicio_ano) & (df_filtrado['Data'] <= data_fim)]
    df_inicio_ano = df_anual.groupby('Titulo')['Data'].min().reset_index().merge(df_anual, on=['Titulo', 'Data'])
    df_fim_ano = df_anual.groupby('Titulo')['Data'].max().reset_index().merge(df_anual, on=['Titulo', 'Data'])
    df_bp_anual = df_inicio_ano[['Titulo', 'Taxas']].rename(columns={'Taxas': 'Taxa_Inicial'}) \
        .merge(df_fim_ano[['Titulo', 'Taxas']].rename(columns={'Taxas': 'Taxa_Final'}), on='Titulo')
    df_bp_anual['BP_Ano'] = (df_bp_anual['Taxa_Final'] - df_bp_anual['Taxa_Inicial']) * 10000
    df_bp_anual = df_bp_anual[['Titulo', 'BP_Ano']]

    df_duration_filtrado = df_duration_melted[
        (df_duration_melted['Data'] >= data_inicio) & 
        (df_duration_melted['Data'] <= data_fim)
    ]
    df_duration_last = (
        df_duration_filtrado.sort_values(['Titulo', 'Data'])
        .groupby('Titulo')
        .last()
        .reset_index()
    )
    df_duration_last['Duration'] = df_duration_last['Duration'] / 252

    df_bp_mensal['Titulo'] = df_bp_mensal['Titulo'].str.strip().str.upper()
    df_bp_anual['Titulo'] = df_bp_anual['Titulo'].str.strip().str.upper()
    df_duration_last['Titulo'] = df_duration_last['Titulo'].str.strip().str.upper()

    df_result = (
        df_bp_mensal
        .merge(df_bp_anual, on='Titulo', how='outer')
        .merge(df_duration_last[['Titulo', 'Duration']], on='Titulo', how='left')
    )

    # --- Início da parte nova para Fechamento ---
    data_fechamento = pd.Timestamp(year=ano, month=mes, day=dia_final)
    df_fechamento = df_taxas_melted[
        (df_taxas_melted['Data'] == data_fechamento) & 
        (df_taxas_melted['Taxas'].notnull())
    ].copy()
    df_fechamento = df_fechamento[['Titulo', 'Taxas']].rename(columns={'Taxas': 'Fechamento'})
    df_fechamento['Titulo'] = df_fechamento['Titulo'].str.strip().str.upper()

    df_result = df_result.merge(df_fechamento, left_on='Titulo', right_on='Titulo', how='left')
    # --- Fim da parte nova ---

    df_result.rename(columns={'Titulo': 'Ativo'}, inplace=True)

    df_result['BP_Mes'] = df_result['BP_Mes'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else '-')
    df_result['BP_Ano'] = df_result['BP_Ano'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else '-')
    df_result['Duration'] = df_result['Duration'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else '-')
    df_result['Fechamento'] = df_result['Fechamento'].apply(lambda x: f"{x*100:.2f}" if pd.notna(x) else '-')

    df_result.rename(columns={'Fechamento': 'Fechamento (%)'}, inplace=True)
    
    return df_result.to_dict('records')

# =================== ABA GERAL ===================

@app.callback(
    Output('geral', 'figure'),
    Input('interval-component', 'n_intervals')
)
def atualizar_grafico_retorno(n):
    df_preco = carregar_dados_retorno()
    df_retorno_acumulado = calcular_retorno_acumulado_6m(df_preco)
    fig = criar_grafico_retorno_acumulado(df_retorno_acumulado)
    return fig

# Função para obter retorno mensal do CDI e Ibovespa
def obter_retorno_mensal(df, ativos=['CDI', 'Ibovespa']):
    ultimo_mes = df['Data'].max().to_period('M')
    df_mes = df[df['Data'].dt.to_period('M') == ultimo_mes].copy()

    retornos = {}
    for ativo in ativos:
        if ativo in df_mes.columns:
            serie = df_mes[ativo].dropna() / 100  # convertendo % para decimal
            if not serie.empty:
                retorno = (1 + serie).prod() - 1
                retornos[ativo] = retorno
    return retornos

# Callback para atualizar o texto minimalista dos retornos mensais
@app.callback(
    Output('retorno-mensal-minimalista', 'children'),
    Input('interval-component', 'n_intervals')
)
def atualizar_retorno_mensal(n_intervals):
    retornos_mensais, _ = obter_retorno_mensal_completo()

    itens = []
    for ativo, retorno in retornos_mensais.items():
        sinal = '+' if retorno >= 0 else ''
        texto = f"{ativo}: {sinal}{retorno:.3%}"
        itens.append(html.Div(texto, style={'font-size': '18px', 'margin': '2px 0', 'color': 'white'}))

    return itens

# Callback para mostrar os piores retornos
@app.callback(
    Output('ativos-pior-retorno', 'children'),
    Input('retorno-ano-dropdown', 'value'),
    Input('retorno-mes-dropdown', 'value'),
    Input('num-piores-retorno', 'value')
)

def mostrar_ativos_pior_retorno(ano, mes, n):
    if None in [ano, mes]:
        return "Selecione ano e mês"
    
    if n is None:
        n = 5

    df_ret = carregar_dados_retorno()
    df_inflacao = carregar_dados_inflacao()
    ativos_inflacao = ['IPCA', 'INPC', 'IGP-M']
    df_retorno_melt = df_ret.melt(id_vars='Data', var_name='Ativo', value_name='Retorno')
    df_retorno_melt['Data'] = pd.to_datetime(df_retorno_melt['Data'])

    dia_fim = calendar.monthrange(ano, mes)[1]
    data_inicio = pd.Timestamp(year=ano, month=mes, day=1)
    data_fim = pd.Timestamp(year=ano, month=mes, day=dia_fim)

    df_mes = df_retorno_melt[
        (df_retorno_melt['Data'] >= data_inicio) & (df_retorno_melt['Data'] <= data_fim)
    ].copy()

    if df_mes.empty:
        return "Nenhum dado para o período"

    df_mes = df_mes[~df_mes['Ativo'].isin(ativos_inflacao)]  # Exclui IPCA, INPC, IGP-M

    df_mes['Retorno'] = pd.to_numeric(df_mes['Retorno'], errors='coerce')
    df_mes['RetornoDecimal'] = df_mes['Retorno'] / 100

    df_retorno_acumulado = df_mes.groupby('Ativo').agg(
        retorno_acumulado=('RetornoDecimal', lambda x: (1 + x).prod() - 1)
    ).reset_index()

    # 🔧 Adiciona inflação
    df_inf_mes = df_inflacao[
        (df_inflacao['Data'] >= data_inicio) & (df_inflacao['Data'] <= data_fim)
    ]

    for ativo in ativos_inflacao:
        if ativo in df_inf_mes.columns:
            serie = df_inf_mes[ativo].dropna()
            if len(serie) >= 2:
                preco_inicio = serie.iloc[0]
                preco_fim = serie.iloc[-1]
                retorno = (preco_fim / preco_inicio) - 1
                df_retorno_acumulado = pd.concat([
                    df_retorno_acumulado,
                    pd.DataFrame([{'Ativo': ativo, 'retorno_acumulado': retorno}])
                ], ignore_index=True)

    df_piores = df_retorno_acumulado.sort_values('retorno_acumulado').head(n)
    linhas = [f"{row['Ativo']}: {row['retorno_acumulado'] * 100:.2f}%" for _, row in df_piores.iterrows()]
    return html.Ul([html.Li(linha) for linha in linhas])

# ✅ Callback para mostrar os MELHORES retornos
@app.callback(
    Output('ativos-melhor-retorno', 'children'),
    Input('retorno-ano-dropdown', 'value'),
    Input('retorno-mes-dropdown', 'value'),
    Input('num-melhores-retorno', 'value')
)
def mostrar_ativos_melhor_retorno(ano, mes, n):
    if None in [ano, mes]:
        return "Selecione ano e mês"
    
    if n is None:
        n = 5

    df_ret = carregar_dados_retorno()
    df_inflacao = carregar_dados_inflacao()
    ativos_inflacao = ['IPCA', 'INPC', 'IGP-M']
    df_retorno_melt = df_ret.melt(id_vars='Data', var_name='Ativo', value_name='Retorno')
    df_retorno_melt['Data'] = pd.to_datetime(df_retorno_melt['Data'])

    dia_fim = calendar.monthrange(ano, mes)[1]
    data_inicio = pd.Timestamp(year=ano, month=mes, day=1)
    data_fim = pd.Timestamp(year=ano, month=mes, day=dia_fim)

    df_mes = df_retorno_melt[
        (df_retorno_melt['Data'] >= data_inicio) & (df_retorno_melt['Data'] <= data_fim)
    ].copy()

    if df_mes.empty:
        return "Nenhum dado para o período"

    df_mes = df_mes[~df_mes['Ativo'].isin(ativos_inflacao)]

    df_mes['Retorno'] = pd.to_numeric(df_mes['Retorno'], errors='coerce')
    df_mes['RetornoDecimal'] = df_mes['Retorno'] / 100

    df_retorno_acumulado = df_mes.groupby('Ativo').agg(
        retorno_acumulado=('RetornoDecimal', lambda x: (1 + x).prod() - 1)
    ).reset_index()

    # 🔧 Adiciona inflação
    df_inf_mes = df_inflacao[
        (df_inflacao['Data'] >= data_inicio) & (df_inflacao['Data'] <= data_fim)
    ]

    for ativo in ativos_inflacao:
        if ativo in df_inf_mes.columns:
            serie = df_inf_mes[ativo].dropna()
            if len(serie) >= 2:
                preco_inicio = serie.iloc[0]
                preco_fim = serie.iloc[-1]
                retorno = (preco_fim / preco_inicio) - 1
                df_retorno_acumulado = pd.concat([
                    df_retorno_acumulado,
                    pd.DataFrame([{'Ativo': ativo, 'retorno_acumulado': retorno}])
                ], ignore_index=True)

    df_melhores = df_retorno_acumulado.sort_values('retorno_acumulado', ascending=False).head(n)
    linhas = [f"{row['Ativo']}: {row['retorno_acumulado'] * 100:.2f}%" for _, row in df_melhores.iterrows()]
    return html.Ul([html.Li(linha) for linha in linhas])

# Callback para carregar e mostrar a evolução das taxas dos ativos
@app.callback(
    [
        Output('grafico-evolucao', 'figure'),
        Output('tabela-evolucao', 'data')
    ],
    [
        Input('btn-atualizar', 'n_clicks')
    ],
    [
        State('input-caminho-arquivo', 'value')
    ]
)
def atualizar_evolucao(n_clicks, caminho_arquivo):
    if not n_clicks:
        fig = px.line(title="Evolução das Taxas")
        return fig, []
    
    df_evolucao = evolucao_taxas_3_meses_excel(caminho_arquivo)
    fig = px.line(
        df_evolucao,
        x='Data',
        y='Taxas',
        color='Titulo',
        markers=True,
        title="Evolução das Taxas - NTNB 2026 e LTN 2045 (Últimos 3 meses)"
    )
    fig.update_layout(
    plot_bgcolor='#34495e',    # fundo da área do gráfico   
    paper_bgcolor='#34495e',   # fundo externo
    font_color='white',        # cor do texto
    legend=dict(
        x=0,
        y=0.5,
        xanchor='left',
        yanchor='middle',
        bgcolor='#34495e',  
        bordercolor='#34495e'   # 2c3e50
    )) 
    data_table = df_evolucao.to_dict('records')
    
    return fig, data_table

from dash import Input, Output, callback

# Callback para atualizar descrição do indicador selecionado
@app.callback(
    Output('descricao-indicador', 'children'),
    [Input('dropdown-indicadores', 'value')]
)
def atualizar_descricao_e_retorno(ativo_selecionado):
    conceito = indicadores.get(ativo_selecionado, "Sem descrição disponível.")

    # Correção: usa a última data do DataFrame para obter o mês correto
    meses_abrev_pt = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    }
    ultima_data = df_ret['Data'].max()
    mes_abreviado = meses_abrev_pt[ultima_data.month]

    retornos = calcular_retorno_acumulado_por_periodo(df_ret, ativo_selecionado, mes_abreviado)

    return [
        html.H5(f"📘 Conceito - {ativo_selecionado}", style={
            'fontSize': '16px',
            'marginTop': '2px',
            'marginBottom': '2px',
            'color': '#000000',
            'textAlign': 'center'
        }),
        html.P(conceito, style={
            'color': 'white',
            'marginTop': '2px',
            'marginBottom': '2px',
            'fontSize': '16px',
            'textAlign': 'center'
        }),
        criar_componente_retorno_ativo(retornos, mes_abreviado)
    ]

@app.callback(
    Output('dummy-output', 'children'),
    Input('interval-manter-conexao', 'n_intervals')
)
def manter_conexao_ativa(n):
    return ''

port = int(os.environ.get("PORT", 10000))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=port, debug=True)



