import pandas as pd
import plotly.graph_objs as go
from dash import dcc, html
import re
import os
import warnings
warnings.simplefilter('always')

# Caminho base para os dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
caminho_base = os.path.join(BASE_DIR, "Data", "Base - Indicadores.xlsx")

# Dicionário de meses abreviados em português
meses_abrev_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
data_abrev = pd.read_excel(caminho_base, sheet_name="Retorno")
data_abrev.columns = data_abrev.columns.str.strip()
data_abrev['Data'] = pd.to_datetime(data_abrev['Data'])
data_tabela = data_abrev['Data'].max()
mes_abreviado = meses_abrev_pt[data_tabela.month].capitalize()

meses_pt = {
    'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
    'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
    'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
    'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
}

# Carregar dados de retornos diários (em %)
def carregar_dados_retorno():
    df_ret = pd.read_excel(caminho_base, sheet_name="Retorno")
    df_ret.columns = df_ret.columns.str.strip()
    df_ret['Data'] = pd.to_datetime(df_ret['Data'])
    return df_ret
# Calcular retorno acumulado dos últimos 6 meses (já em %)
def calcular_retorno_acumulado_6m(df_ret):
    ultima_data = df_ret['Data'].max()
    data_inicio = ultima_data - pd.DateOffset(months=6)
    df_6m = df_ret[df_ret['Data'] >= data_inicio].copy()

    # Ativos normais (exclui os de inflação)
    ativos_desejados = ['CDI', 'Ima-B', 'Ima-B 5', 'Ima-B 5+', 'IRF-M',
                        'Ibovespa', 'S&P 500']
    ativos = [col for col in df_6m.columns if col in ativos_desejados]
    df_6m[ativos] = df_6m[ativos].apply(pd.to_numeric, errors='coerce')

    retorno_acumulado = {}
    for ativo in ativos:
        serie = df_6m[ativo].dropna()
        retorno_acumulado[ativo] = (1 + serie).prod() - 1 if not serie.empty else None

    # Agora cálculo dos índices de inflação usando a aba Inflacao
    df_inflacao = carregar_dados_inflacao()
    df_inflacao = df_inflacao[df_inflacao['Data'] >= data_inicio]

    for indice in ['IPCA', 'INPC', 'IGP-M']:
        if indice in df_inflacao.columns:
            serie = df_inflacao[['Data', indice]].dropna()
            serie[indice] = pd.to_numeric(serie[indice], errors='coerce')
            serie = serie.dropna()
            if not serie.empty and len(serie) >= 2:
                preco_inicio = serie[indice].iloc[0]
                preco_fim = serie[indice].iloc[-1]
                retorno = (preco_fim / preco_inicio) - 1
                retorno_acumulado[indice] = retorno

    # Montar DataFrame final
    df_ret_acu = pd.DataFrame.from_dict(retorno_acumulado, orient='index',
                                        columns=['Retorno Acumulado'])
    return df_ret_acu.dropna().sort_values('Retorno Acumulado', ascending=False)

# Criar gráfico de retorno acumulado 6 meses
def criar_grafico_retorno_acumulado(df_retorno_acumulado):
    fig = go.Figure([go.Bar(
        x=df_retorno_acumulado.index,
        y=df_retorno_acumulado['Retorno Acumulado'],
        marker_color='royalblue',
        text=df_retorno_acumulado['Retorno Acumulado'].apply(lambda x: f"{x:.2%}"),
        textposition='auto'
    )])
    
    fig.update_layout(
        title=dict(
            text='Retorno dos Principais Índices - 6M',
            font=dict(color='white'),
            x=0.15,
            xanchor='center'
        ),
        yaxis_tickformat=".2%",
        plot_bgcolor="#34495e",
        paper_bgcolor="#34495e",
        margin=dict(l=20, r=20, t=50, b=20),  # Reduz margens
    )

    fig.update_xaxes(
        color='white',         # cor dos ticks e título do eixo X    
    )
    fig.update_yaxes(
        color='white',         # cor dos ticks e título do eixo Y
        tickformat=".1%"
    )

    # Ativa ajuste automático de margens para o texto das barras
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)

    return fig

# Obter retorno mensal (ultimo mês)
def obter_retorno_mensal_completo():
    # Parte 1: ativos financeiros (aba Retorno)
    df_ret = carregar_dados_retorno()
    ultimo_mes = df_ret['Data'].max().to_period('M')
    df_mes = df_ret[df_ret['Data'].dt.to_period('M') == ultimo_mes].copy()
    ativos = [col for col in df_mes.columns if col != 'Data']

    def tentar_converter_percentual(valor):
        try:
            if isinstance(valor, str) and '%' in valor:
                return float(valor.replace('%', '').replace(',', '.')) / 100
            return float(valor)
        except:
            return None

    for ativo in ativos:
        df_mes[ativo] = df_mes[ativo].apply(tentar_converter_percentual)

    retornos = {}
    for ativo in ativos:
        serie = df_mes[ativo].dropna()
        if not serie.empty:
            retorno = (1 + serie).prod() - 1
            retornos[ativo] = retorno

    # Parte 2: índices de inflação (aba Inflacao)
    df_inf = carregar_dados_inflacao()
    df_inf['Periodo'] = df_inf['Data'].dt.to_period('M')
    meses_ordenados = df_inf['Periodo'].drop_duplicates().sort_values()

    if len(meses_ordenados) >= 2:
        mes_atual = meses_ordenados.iloc[-1]
        mes_anterior = meses_ordenados.iloc[-2]

        df_atual = df_inf[df_inf['Periodo'] == mes_atual]
        df_anterior = df_inf[df_inf['Periodo'] == mes_anterior]

        for indice in ['IPCA', 'INPC', 'IGP-M']:
            if indice in df_inf.columns:
                valor_atual = df_atual[indice].dropna().astype(float).iloc[-1] if not df_atual[indice].dropna().empty else None
                valor_anterior = df_anterior[indice].dropna().astype(float).iloc[-1] if not df_anterior[indice].dropna().empty else None

                if valor_atual is not None and valor_anterior is not None:
                    retorno = (valor_atual / valor_anterior) - 1
                    retornos[indice] = retorno

    return retornos, ultimo_mes

def carregar_dados_inflacao():
    df_inflacao = pd.read_excel(caminho_base, sheet_name="Inflacao")
    df_inflacao.columns = df_inflacao.columns.str.strip()
    df_inflacao['Data'] = pd.to_datetime(df_inflacao['Data'])
    return df_inflacao

# Função para converter string percentual "0,07%" em float decimal 0.0007
def converte_str_para_decimal(valor):
    if isinstance(valor, str):
        return float(valor.replace('%', '').replace(',', '.')) / 100
    return float(valor)
def carregar_dados_retorno():
    df_ret = pd.read_excel(caminho_base, sheet_name="Retorno")
    df_ret.columns = df_ret.columns.str.strip()
    df_ret['Data'] = pd.to_datetime(df_ret['Data'])
    # Convertendo as colunas (exceto 'Data') de percentual string para decimal float
    colunas = [col for col in df_ret.columns if col != 'Data']
    for col in colunas:
        df_ret[col] = df_ret[col].apply(lambda x: converte_str_para_decimal(x) if pd.notnull(x) else x)
    return df_ret

# Funções auxiliares para exibição visual
def criar_componente_retorno_mensal_minimalista(retornos):
    # Aqui o retorno já deve estar em float decimal (0.0007), exibe formatado
    return html.Div([html.P(f"{ativo}: {retorno:.2%}") for ativo, retorno in retornos.items()])
def criar_componente_piores_ativos_minimalista(n=5):
    retornos, mes = obter_retorno_mensal_completo()
    piores = sorted(retornos.items(), key=lambda x: x[1])[:n]
    return html.Div([html.P(f"{a}: {r:.2%}") for a, r in piores]), mes

def criar_componente_melhores_ativos_minimalista(n=5):
    retornos, mes = obter_retorno_mensal_completo()
    melhores = sorted(retornos.items(), key=lambda x: x[1], reverse=True)[:n]
    return html.Div([html.P(f"{a}: {r:.2%}") for a, r in melhores]), mes

    
# Carregar dados e montar dashboard
df_ret = carregar_dados_retorno()
df_ret_acu = calcular_retorno_acumulado_6m(df_ret)
fig_retorno_6m = criar_grafico_retorno_acumulado(df_ret_acu)
retornos_mensais, mes_ultimo = obter_retorno_mensal_completo()
# Aqui, retornos_mensais pode estar no formato string "0,07%", converte antes para exibir
retornos_mensais_decimal = {ativo: converte_str_para_decimal(ret) for ativo, ret in retornos_mensais.items()}
componente_retorno_mensal = criar_componente_retorno_mensal_minimalista(retornos_mensais_decimal)
componente_piores_ativos, _ = criar_componente_piores_ativos_minimalista(n=5)
componente_melhores_ativos, _ = criar_componente_melhores_ativos_minimalista(n=5)

nome_mes_en = mes_ultimo.strftime('%B')  
ano = mes_ultimo.strftime('%Y')      
nome_mes_pt = meses_pt.get(nome_mes_en, nome_mes_en)  # fallback caso falhe

titulo_mes = f"{nome_mes_pt}/{ano}"    

# Função para extrair e filtrar dados de taxas dos últimos 3 meses
def evolucao_taxas_3_meses_excel(file_path):
    df_taxas = pd.read_excel(file_path, sheet_name='Taxas')
    df_taxas['Data'] = pd.to_datetime(df_taxas['Data'])

    # Formatar dados para formato longo
    df_taxas_melted = df_taxas.melt(id_vars=['Data'], var_name='Titulo', value_name='Taxas')

    # Filtrar últimos 3 meses
    data_max = df_taxas_melted['Data'].max()
    data_min = data_max - pd.DateOffset(months=3)
    df_filtrado = df_taxas_melted[(df_taxas_melted['Data'] >= data_min) & (df_taxas_melted['Data'] <= data_max)]

    # Classificar os títulos em grupos (Pré e Pós) via nome
    def classificar_grupo(titulo):
        if re.search(r'NTN-F|prefixado|prefixado', titulo, re.IGNORECASE):
            return 'Pré-fixado'
        elif re.search(r'NTN-B|ipca\+', titulo, re.IGNORECASE):
            return 'Pós-fixado (IPCA+)'
        else:
            return 'Outro'

    df_filtrado = df_filtrado.copy()
    df_filtrado.loc[:, 'Grupo'] = df_filtrado['Titulo'].apply(classificar_grupo)

    # Data do último dia para cálculo de fechamento
    ultima_data = df_filtrado['Data'].max()
    df_ultimo_dia = df_filtrado[df_filtrado['Data'] == ultima_data]

    # Para cada grupo, pegar o título com maior taxa no último dia
    titulos_maiores = (
        df_ultimo_dia[df_ultimo_dia['Grupo'] != 'Outro']  # Ignorar grupo "Outro"
        .groupby('Grupo')
        .apply(lambda g: g.loc[g['Taxas'].idxmax()], include_groups=False)
        .reset_index(drop=True)
    )

    # Selecionar somente os dados desses títulos para plotar
    titulos_selecionados = titulos_maiores['Titulo'].unique()
    df_plot = df_filtrado[df_filtrado['Titulo'].isin(titulos_selecionados)]

    return df_plot[['Data', 'Titulo', 'Taxas']]

# Criar gráfico fixo de evolução das taxas
def criar_grafico_taxas(df_taxas):
    import plotly.graph_objects as go

    # Converter coluna 'Data' para datetime se ainda não for
    df_taxas['Data'] = pd.to_datetime(df_taxas['Data'])

    # Filtro: últimos 3 meses
    data_limite = df_taxas['Data'].max() - pd.DateOffset(months=3)
    df_ultimos_3_meses = df_taxas[df_taxas['Data'] >= data_limite].copy()

    # Agrupar os títulos por tipo
    df_ultimos_3_meses['Grupo'] = df_ultimos_3_meses['Titulo'].apply(
        lambda x: 'Pré-fixado' if 'NTN-F' in x else 'Pós-fixado (IPCA+)' if 'NTN-B' in x else 'Outro'
    )

    # Pegar a última data do mês (atual)
    ultima_data = df_ultimos_3_meses['Data'].max()

    # Para cada grupo, pegar o título com maior taxa no último dia
    titulos_maiores = (
        df_ultimos_3_meses[df_ultimos_3_meses['Grupo'] != 'Outro']
        .groupby('Grupo')
        .apply(lambda g: g.loc[g['Taxas'].idxmax()], include_groups=False)
        .reset_index(drop=True)
    )

    # Selecionar somente os dados desses títulos para plotar
    titulos_selecionados = titulos_maiores['Titulo'].unique()
    df_plot = df_ultimos_3_meses[df_ultimos_3_meses['Titulo'].isin(titulos_selecionados)]

    fig = go.Figure()

    for titulo in titulos_selecionados:
        df_titulo = df_plot[df_plot['Titulo'] == titulo]

        # Linha principal
        fig.add_trace(go.Scatter(
            x=df_titulo['Data'],
            y=df_titulo['Taxas'],
            mode='lines+markers',
            name=titulo
        ))

        # Adicionar rótulo de fechamento na última data
        fechamento = df_titulo[df_titulo['Data'] == ultima_data]
        if not fechamento.empty:
            taxa_fechamento = fechamento['Taxas'].values[0]
            fig.add_trace(go.Scatter(
            x=[ultima_data],
            y=[taxa_fechamento],
            mode='text',
            text=[f"{taxa_fechamento:.1%}"],  # 1 casa decimal
            textposition='top right',
            textfont=dict(size=14, color='white'),
            showlegend=False,
            hoverinfo='skip'
))

    nomes_ativos = ', '.join(titulos_selecionados)
    fig.update_layout(
    title={
        'text': f'Maior Fechamento (Pré e Pós) - {nomes_ativos}',
        'font': dict(color='white'),
        'x': 0.5,
    },
    xaxis_title=None,  # Remove título do eixo X
    yaxis_title=None,  # Remove título do eixo Y
    yaxis_tickformat=',.0%',  # Sem casas decimais no eixo Y
    hovermode='x unified',
    legend=dict(  
        orientation="v",
        x=0.012,
        y=0.5,
        xanchor="left",
        yanchor="middle",
        bgcolor="#34495e",
        bordercolor="#34495e",
        borderwidth=2,
        font=dict(color='white')
    ),
    plot_bgcolor="#34495e",
    paper_bgcolor="#34495e",
    margin=dict(l=20, r=20, t=60, b=20)  # Margens reduzidas para melhor aproveitamento
    )

    fig.update_xaxes(
    color='white',        # Cor dos ticks e labels do eixo X
    )

    fig.update_yaxes(
    color='white',        
    )

    fig.add_annotation(
    text="(Últimos 3 meses)",
    xref="paper", yref="paper",
    x=0.9, y=1.08,
    showarrow=False,
    font=dict(size=12, color="white"),
    align="right",
    xanchor="right",
    yanchor="bottom"
    )

    fig.update_xaxes(automargin=True)  # Ajusta margens automaticamente no eixo X
    fig.update_yaxes(automargin=True)  # Ajusta margens automaticamente no eixo Y

    return fig

def calcular_retorno_acumulado_por_periodo(df_ret, ativo, mes_abreviado, meses_lista=[1, 12, 36, 60]):
    ativos_sem_retorno = ["IPCA", "NTN-B", "NTN-F", "LFT", "INPC", "IGP-M"]
    if ativo in ativos_sem_retorno:
        return {"Mensagem": "Retorno acumulado não aplicável para este índice."}

    retornos = {}
    df_serie = df_ret[['Data', ativo]].dropna().copy()
    if df_serie.empty:
        return None

    df_serie.sort_values('Data', inplace=True)
    df_serie['Data'] = pd.to_datetime(df_serie['Data'])

    ultima_data = df_serie['Data'].max()
    preco_fim = df_serie[df_serie['Data'] == ultima_data][ativo].values[0]

    # Função para encontrar o último dia útil do mês específico
    def ultimo_dia_util_mes(df, ano, mes):
        dados_mes = df[(df['Data'].dt.year == ano) & (df['Data'].dt.month == mes)]
        if dados_mes.empty:
            return None
        return dados_mes['Data'].max()

    # Função para calcular retorno entre dois pontos
    def calcular_retorno(df, data_inicio, data_fim, coluna):
        dados = df[(df['Data'] > data_inicio) & (df['Data'] <= data_fim)][coluna]
        if dados.empty:
            return None
        return (1 + dados).prod() - 1

    # Loop para cada período solicitado
    for meses in meses_lista:
        ano_referencia = ultima_data.year
        mes_referencia = ultima_data.month - meses

        # Ajusta ano/mês para datas retroativas
        while mes_referencia <= 0:
            mes_referencia += 12
            ano_referencia -= 1

        data_inicio = ultimo_dia_util_mes(df_serie, ano_referencia, mes_referencia)
        if data_inicio is None:
            retornos[f"{meses} M"] = None
            continue

        retorno = calcular_retorno(df_serie, data_inicio, ultima_data, ativo)
        if retorno is not None:
            retornos[f"{meses} M"] = retorno

    return retornos



def criar_componente_retorno_ativo(retornos_dict, mes_abreviado):
    if not retornos_dict:
        return html.P("Sem dados disponíveis para este ativo.", style={'color': 'white', 'textAlign': 'center'})

    if "Mensagem" in retornos_dict:
        return html.Div([
            html.H5("📈 Retorno do Índice", style={
                'fontSize': '16px',
                'marginTop': '0px',
                'marginBottom': '3px',
                'color': '#000000',
                'textAlign': 'center'
            }),
            html.P(retornos_dict["Mensagem"], style={'color': 'white', 'textAlign': 'center'})
        ])

    # Pega os retornos dos períodos, usando o mês abreviado como chave para o retorno de 1 mês
    r1 = retornos_dict.get("1 M")
    r12 = retornos_dict.get("12 M")
    r36 = retornos_dict.get("36 M")
    r60 = retornos_dict.get("60 M")

    def format_ret(ret):
        return f"{ret:.2%}" if ret is not None else "N/A"

    return html.Div([
        html.H5("📈 Retorno (Intervalos)", style={
            'fontSize': '16px',
            'marginTop': '1px',
            'marginBottom': '1px',
            'color': '#000000',
            'textAlign': 'center'
        }),
        html.Div([
            html.Div([
                html.Div(mes_abreviado, style={'fontSize': '14px', 'color': 'white'}),
                html.Div(format_ret(r1), style={'fontSize': '16px', 'fontWeight': '600', 'color': 'white'})
            ], style={'textAlign': 'center', 'padding': '4px'}),
            html.Div([
                html.Div("12 M", style={'fontSize': '14px', 'color': 'white'}),
                html.Div(format_ret(r12), style={'fontSize': '16px', 'fontWeight': '600', 'color': 'white'})
            ], style={'textAlign': 'center', 'padding': '4px'}),
            html.Div([
                html.Div("36 M", style={'fontSize': '14px', 'color': 'white'}),
                html.Div(format_ret(r36), style={'fontSize': '16px', 'fontWeight': '600', 'color': 'white'})
            ], style={'textAlign': 'center', 'padding': '4px'}),
            html.Div([
                html.Div("60 M", style={'fontSize': '14px', 'color': 'white'}),
                html.Div(format_ret(r60), style={'fontSize': '16px', 'fontWeight': '600', 'color': 'white'})
            ], style={'textAlign': 'center', 'padding': '4px'}),
        ], style={
            'display': 'flex',
            'justifyContent': 'space-between',
            'alignItems': 'center',
            'backgroundColor': '#34495e',
            'borderRadius': '8px',
            'padding': '4px',
            'width': '100%',
            'maxWidth': '400px',
            'margin': '0 auto'
        })
    ])



# --- Execução principal ---
# Carregar dados
df_preco = carregar_dados_retorno()
# Calcular gráfico de retorno acumulado 6 meses
df_retorno_acumulado = calcular_retorno_acumulado_6m(df_preco)
fig_retorno_6m = criar_grafico_retorno_acumulado(df_retorno_acumulado)
# Criar componente minimalista CDI e Ibovespa
componente_retorno_mensal = criar_componente_retorno_mensal_minimalista(retornos_mensais)
# Criar componente minimalista piores ativos + mês
componente_piores_ativos, mes_piores = criar_componente_piores_ativos_minimalista(n=5)
# Criar componente minimalista melhores ativos + mês
componente_melhores_ativos, mes_melhores = criar_componente_melhores_ativos_minimalista(n=5)
# Formatar título do mês para exibição
titulo_mes = mes_ultimo.strftime('%B/%Y').capitalize()
# Carregar dados de taxas e criar gráfico fixo
df_taxas_filtrado = evolucao_taxas_3_meses_excel(caminho_base)
fig_taxas = criar_grafico_taxas(df_taxas_filtrado)
# Dicionário com indicadores e seus significados
indicadores = {
    # Renda Fixa - Pós-Fixado
    "CDI": "Taxa usada como referência para empréstimos entre bancos.",
    "Jgp - CDI": "Índice de crédito privado atrelado ao CDI.",
    "LFT": "Título público que acompanha a taxa Selic.",
    "IMA-S": "Índice de títulos públicos atrelados à taxa Selic.",
    # Renda Fixa - Pré-Fixado
    "IRF-M": "Índice que mede o desempenho de títulos públicos prefixados.",
    "IRF-M 1": "Índice que mede o desempenho de títulos públicos prefixados com vencimento em até 1 ano.",
    "IRF-M 1+": "Índice que mede o desempenho de títulos públicos prefixados com vencimento acima de 1 ano.",
    "NTN-F": "Título público prefixado.",
    # Debêntures
    "IDA IPCA": "Índices que acompanham carteiras de debêntures incentivadas atreladas à inflação.",
    "IDA Geral": "Índices que acompanham carteiras de debêntures incentivadas atreladas à inflação.",
    "IDA DI": "Índices que acompanham carteiras de debêntures incentivadas atreladas ao DI.",
    # Renda Variável
    "Ibovespa": "Índice das ações mais negociadas da bolsa.",
    "IBRX": "Índice das 50 ou 100 ações mais representativas.",
    "IDIV": "Índice de ações que mais pagam dividendos.",
    "Small Caps": "Índice de empresas pequenas da bolsa.",
    "Midlarge Cap": "Índice de empresas médias e grandes.",
    "IFIX": "Índice que mede o desempenho dos principais fundos imobiliários (FIIs).",
    "IVBX-2": "Índice com ações de empresas bem avaliadas, mas fora do top 10 em valor de mercado e liquidez.",
    "IGC-NM": "Índice de ações de empresas listadas no Novo Mercado, com alto padrão de governança.",
    "ISEE": "Índice de Sustentabilidade Empresarial, com empresas comprometidas com práticas ESG.",
    "ICO-2": "Índice com empresas que adotam boas práticas de gestão de carbono.",
    "IHFA": "Índice de fundos multimercado.",
    # Inflação
    "IPCA": "Índice oficial da inflação no Brasil.",
    "IGP-M": "Índice usado em contratos de aluguel.",
    "INPC": "Índice que mede a inflação para famílias de menor renda.",
    "Ima-B": "Índice de títulos públicos indexados à inflação (IPCA), como as NTN-Bs.",
    "Ima-B 5": "Índice de títulos públicos indexados à inflação (IPCA) com vencimento até 5 anos.",
    "Ima-B 5+": "Índice de títulos públicos indexados à inflação (IPCA) com vencimento acima de 5 anos.",
    "NTN-B": "Título público que paga IPCA + juros até o seu vencimento.",
    "NTN-C 2031": "Título antigo atrelado ao IGP-M com vencimento em 2031.",
    # Moedas
    "Dólar Ptax": "Taxa média do dólar usada em contratos financeiros.",
    "Euro": "Moeda oficial da zona do euro.",
    # Renda Variável Internacional
    "S&P 500": "Índice das 500 maiores empresas dos EUA.",
    "Nasdaq": "Índice das principais empresas de tecnologia dos EUA."
}
dropdown_indicadores = dcc.Dropdown(
    id='dropdown-indicadores',
    options=[{'label': k, 'value': k} for k in indicadores.keys()],
    value='Ibovespa',  # Mantém o Ibovespa selecionado inicialmente
    placeholder="Selecione um indicador",
    style={'color': '#000000'}
)
descricao_indicador = html.Div(
    id='descricao-indicador',
    children=[
        html.H5("📘 Conceito dos Indicadores", style={
            'fontSize': '16px',
            'marginBottom': '1px',
            'color': '#000000',
            'textAlign': 'center'
        }),
        html.P("Selecione o índice:", style={
            'color': 'white',
            'marginTop': '1px',
            'fontSize': '16px',
            'textAlign': 'center'
        })
    ],
)

# Função auxiliar para filtrar retornos numéricos
def filtrar_retorno_numerico(retornos):
    return {k: v for k, v in retornos.items() if isinstance(v, (int, float))}
retornos_mensais, mes_ultimo = obter_retorno_mensal_completo()
retornos_filtrados = filtrar_retorno_numerico(retornos_mensais)
# Maiores altas - ordenando pelo retorno, do maior para o menor
melhores = sorted(retornos_filtrados.items(), key=lambda x: x[1], reverse=True)[:5]
# Maiores baixas - ordenando do menor para o maior
piores = sorted(retornos_filtrados.items(), key=lambda x: x[1])[:5]


frase_data_base = f"📅 Data-base: {titulo_mes}"
print(frase_data_base)

layout = html.Div([
    # Cabeçalho
    html.Div([
        html.Div([
            html.P(frase_data_base, style={
                'color': 'white',
                'fontSize': '20px',
                'margin': '0',
                'textAlign': 'left'
            })
        ], style={'flex': 1, 'display': 'flex', 'alignItems': 'center'}),

        html.Div([
            html.H2("Indicadores Financeiros - Dashboard", style={
                'color': 'white',
                'textAlign': 'center',
                'margin': '0',
                'fontFamily': "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
                'fontWeight': '700',
                'fontSize': '32px',
                'textShadow': '1px 1px 3px rgba(0,0,0,0.7)'
            })
        ], style={'flex': 2, 'textAlign': 'center'}),

        html.Div([
            html.Img(src='/assets/logo_itau.png', style={
                'height': '105px',
                'transform': 'scaleX(1.2)',
                'marginLeft': '10px'
            }),
            html.Img(src='/assets/funbep.png', style={
                'height': '60px',
                'marginLeft': '10px'
            }),
        ], style={
            'flex': 1,
            'display': 'flex',
            'justifyContent': 'flex-end',
            'alignItems': 'center',
            'gap': '10px'
        })
    ], style={
        'display': 'flex',
        'alignItems': 'center',
        'justifyContent': 'space-between',
        'marginBottom': '10px'
    }),

    # Gráfico de barras no topo
    html.Div([
        dcc.Graph(
            id='grafico-retorno-6m',
            figure=fig_retorno_6m,
            config={
                'displaylogo': False,
                'modeBarButtonsToAdd': ['toImage'],
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': 'retorno_acumulado_6m',
                    'height': 600,
                    'width': 1000,
                    'scale': 2
                }
            },
            style={
                'height': '35vh',
                'borderRadius': '12px',
                'border': '2px solid #1f2c3d',
                'boxShadow': '0 4px 12px rgba(0,0,0,0.5)',
                'marginBottom': '20px'
            }
        )
    ]),

    # Área com as 3 colunas abaixo do gráfico
    html.Div([
        # Coluna 1: Tabela melhores/piores ativos
        html.Div([
            html.H4(f"Destaque - {titulo_mes}", style={
                'color': 'white',
                'marginBottom': '0px',
                'marginTop': '0px',
                'fontWeight': '700',
                'fontSize': '18px',
                'textAlign': 'center'
            }),

            html.Div([
                html.Div("📈 Maiores altas", style={
                    'color': '#39ff14',
                    'fontWeight': '600',
                    'marginBottom': '1px',
                    'marginTop': '1px',
                    'fontSize': '16px'
                }),
                html.Div([
                    html.Div(f"{ativo}: {retorno:.2%}",
                             style={
                                 'fontSize': '14px',
                                 'margin': '2px 0',
                                 'color': 'white',
                                 'width': '100%',
                                 #'minWidth': '180px',
                                 #'maxWidth': '300px',
                                 # 'maxWidth': '100%',
                                 'boxSizing': 'border-box',
                                 #'overflow': 'hidden',
                                 #'textOverflow': 'ellipsis',
                                 # 'whiteSpace': 'nowrap',
                                 'wordBreak': 'break-word'
                             })
                    for ativo, retorno in sorted(
                        filtrar_retorno_numerico(obter_retorno_mensal_completo()[0]).items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]
                ]),
                html.Div("📉 Maiores baixas", style={
                    'color': 'tomato',
                    'marginTop': '1px',
                    'marginBottom': '1px',
                    'fontWeight': '600',
                    'fontSize': '16px'
                }),
                html.Div([
                    html.Div(f"{ativo}: {retorno:.2%}",
                             style={
                                 'fontSize': '14px',
                                 'margin': '2px 0',
                                 'color': 'white',
                                 'width': '100%',
                                 #'minWidth': '180px',
                                 #'maxWidth': '300px',
                                 # 'maxWidth': '100%',
                                 'boxSizing': 'border-box',
                                 #'overflow': 'hidden',
                                 #'textOverflow': 'ellipsis',
                                 #'whiteSpace': 'nowrap',
                                 'wordBreak': 'break-word'
                             })
                    for ativo, retorno in sorted(
                        filtrar_retorno_numerico(obter_retorno_mensal_completo()[0]).items(),
                        key=lambda x: x[1]
                    )[:5]
                ]),
            ])
        ], style={
            'width': '100%', # permite que ele se ajuste ao espaço disponível
            'minWidth': '180px',
            'maxWidth': '300px',
            'backgroundColor': '#34495e',
            'borderRadius': '12px',
            'border': '2px solid #1f2c3d',
            'boxShadow': '0 4px 10px rgba(0,0,0,0.5)',
            'padding': '3px 8px',
            'textAlign': 'center',
            'fontFamily': "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
            'color': '#000',
            'minHeight': '35vh',
            'maxHeight': '305px',
            'boxSizing': 'border-box',
            'display': 'flex',
            'flexDirection': 'column',
            'gap': '2px',
            'flexGrow': 1
  # importante para conter padding e borda
        }),

        # Coluna 2: Gráfico de taxas
        html.Div([
            dcc.Graph(
                id='grafico-taxas-titulos',
                figure=fig_taxas,
                style={
                    'height': '45vh',
                    'width': '100%',
                    'borderRadius': '12px',
                    'boxShadow': '0 4px 12px rgba(0,0,0,0.5)',
                }
            )
        ], style={
            'width': '58%',
            'minWidth': '320px',
            'padding': '0',
            'boxSizing': 'border-box',
            'border': '2px solid #1f2c3d',
            'borderRadius': '12px',
            'display': 'flex',
            'flexDirection': 'column',
            'justifyContent': 'stretch',
            'overflow': 'hidden',
        }),

        # Coluna 3: Tabela conceitos dos indicadores
        html.Div([
            html.H4("Selecione o índice:", style={
                'color': 'white',
                'fontSize': '16px',
                'fontWeight': '600',
                'marginTop': '0px',
                'marginBottom': '2px',
                'textAlign': 'center'
            }),
            dropdown_indicadores,
            descricao_indicador,
        ], style={
            'backgroundColor': '#34495e',
            'color': 'white',
            'padding': '8px 12px',
            'border': '2px solid #1f2c3d',
            'borderRadius': '12px',
            'width': '28%',
            'minWidth': '240px',
            'maxWidth': '300px',
            'maxHeight': '35vh',
            'minHeight': '250px',
            'overflowY': 'hidden',
            'boxShadow': '0 4px 15px rgba(255, 255, 255, 0.15)',
            'fontFamily': "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
            'display': 'flex',
            'flexDirection': 'column',
            'gap': '2px',
            'boxSizing': 'border-box',
            'flexGrow': 1
        }),
    ], style={
        'display': 'flex',
        'justifyContent': 'space-between',
        'alignItems': 'flex-start',
        'gap': '20px',
        'flexWrap': 'nowrap'
    }),

    # Dummy output invisível para manter conexão ativa
    html.Div(id='dummy-output', style={'display': 'none'}),

    # Intervalo para callback de manter conexão
    dcc.Interval(id='interval-component', interval=300000, n_intervals=0)
], style={
    'padding': '10px 30px',          # 20px 30px
    'backgroundColor': '#2c3e50',
    'minHeight': '100vh',
    'boxSizing': 'border-box',
    'fontFamily': "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
})

# print(df_taxas_filtrado.head())
# print(df_taxas_filtrado['Data'].min(), df_taxas_filtrado['Data'].max())



