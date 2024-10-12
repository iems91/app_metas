import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import pytz
import dash_auth
from datetime import datetime, timedelta
from dash.exceptions import PreventUpdate
from flask_caching import Cache
from flask_compress import Compress 
from feriados import *
from metas import *
from function import *
from config import *

# Definir usuário e senha válidos
VALID_USERNAME_PASSWORD_PAIRS = {
    'trepis': 'Tr@1234'
}

rca_nao_controla = [1,6,7,11,9998,9999]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
Compress(app.server)  # Ativa a compressão gzip para otimizar transferência de dados

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

# Configuração do cache
cache = Cache(app.server, config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300
})

ano_atual = int(datetime.now().year)
mes_atual = int(datetime.now().month)

df_data_rca = processar_dados(query_data_rca)

# Extraindo os anos únicos da coluna 'DATA' do df_vendas
anos_vendas = df_data_rca['DATA'].dt.year.unique()
opcoes_anos = [{'label': str(ano), 'value': ano} for ano in sorted(anos_vendas, reverse=True)]

meses_vendas = df_data_rca['DATA'].dt.month.unique()
opcoes_meses = [{'label': str(mes), 'value': mes} for mes in sorted(meses_vendas, reverse=True)]

seleciona_rca = df_data_rca['CODUSUR'].unique()
opcoes_rca = [{'label': str(rca), 'value': rca} for rca in sorted(seleciona_rca)]

# Adicionar a opção "Todos" no dropdown
opcoes_anos.insert(0, {'label': 'Todos', 'value': 'Todos'})
opcoes_meses.insert(0, {'label': 'Todos', 'value': 'Todos'})
opcoes_rca.insert(0, {'label': 'Todos', 'value': 'Todos'})

app.layout = html.Div([
    dbc.Container([
        dcc.Store(id='dataset_venda_liq', data={}),
        dcc.Store(id='dataset_metas_codusur', data={}),
        dcc.Store(id='dataset_vendas_completa', data={}),
        dcc.Store(id='data_atual', data={}),
        dcc.Store(id='meta_ano', data={}),
        dcc.Store(id='meta_mes', data={}),
        dcc.Store(id='meta_semana', data={}),
        dcc.Store(id='meta_sabado', data={}),
        dcc.Interval(id='interval-dynamic', interval=30*1000, n_intervals=0),
        dcc.Interval(id='interval-static', interval=43200*1000, n_intervals=0),
        dcc.Interval(id='interval-hora', interval=3600*1000, n_intervals=0),
        dbc.Row([
            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H5("Selecione o Ano"),
                                dcc.Dropdown(
                                    id='dropdown-ano',
                                    options=opcoes_anos,
                                    value=ano_atual,  # Valor padrão
                                    clearable=False,
                                    style={'width': '100%', 'color': 'black'}
                                )
                            ], sm=12, md=4),
                            dbc.Col([
                                html.H5("Selecione o Mês"),
                                dcc.Dropdown(
                                    id='dropdown-mes',
                                    options=opcoes_meses,
                                    value=mes_atual,  # Valor padrão
                                    clearable=False,
                                    style={'width': '100%', 'color': 'black'}
                                )
                            ], sm=12, md=4),
                            dbc.Col([
                                html.H5("Selecione o RCA"),
                                dcc.Dropdown(
                                    id='dropdown-rca',
                                    options=opcoes_rca,
                                    value='Todos',  # Valor padrão
                                    clearable=False,
                                    style={'width': '100%', 'color': 'black'}
                                )
                            ], sm=12, md=4)
                        ],className='g-2 my-auto', style={'margin-top': '7px'}),

                        dbc.Row([
                            dbc.Col([
                                dcc.Graph(id='indicator1', className='dbc', config=config_graph)
                            ], sm=12, md=2),
                            dbc.Col([
                                dcc.Graph(id='indicator2', className='dbc', config=config_graph)
                            ], sm=12, md=2),
                            dbc.Col([
                                dcc.Loading(
                                    dcc.Graph(id='indicator3', className='dbc', config=config_graph),
                                    type='default',
                                    color='green' 
                                )
                            ], sm=12, md=2),
                            dbc.Col([
                                dcc.Loading(
                                    dcc.Graph(id='indicator4', className='dbc', config=config_graph),
                                    type='default',
                                    color='green' 
                                )
                            ], sm=12, md=2),
                            dbc.Col([
                                dcc.Loading(
                                    dcc.Graph(id='indicator5', className='dbc', config=config_graph),
                                    type='default',
                                    color='green' 
                                )
                            ], sm=12, md=2),
                            dbc.Col([
                                dcc.Loading(
                                    dcc.Graph(id='indicator6', className='dbc', config=config_graph),
                                    type='default',
                                    color='green' 
                                )
                            ], sm=12, md=2),
                        ], className='g-2 my-auto', style={'margin-top': '7px'}),
                        dbc.Row([
                            dbc.Col([
                                dcc.Graph(id='graph1', className='dbc', config=config_graph)
                            ], sm=12, md=4),
                            dbc.Col([
                                dcc.Graph(id='graph2', className='dbc', config=config_graph)
                            ], sm=12, md=4),
                            dbc.Col([
                                dcc.Graph(id='graph3', className='dbc', config=config_graph)
                            ], sm=12, md=4)
                        ], className='g-2 my-auto', style={'margin-top': '7px'}),
                        dbc.Row([
                            dbc.Col([
                                dcc.Graph(id='graph4', className='dbc', config=config_graph)
                            ], sm=12, md=12)
                        ], className='g-2 my-auto', style={'margin-top': '7px'}),
                        dbc.Row([
                            dbc.Col([
                                html.H5("Selecione o Período de análise"),
                                dcc.Dropdown(
                                    id='dropdown-periodo',
                                    options=({'label':'Anual', 'value':'A'},{'label':'Mensal', 'value':'M'},{'label':'Diário', 'value':'D'}),
                                    value='M',  # Valor padrão
                                    clearable=False,
                                    style={'width': '50%', 'color': 'black', 'margin-bottom': '7px'}
                                ),
                                dcc.Graph(id='graph5', className='dbc', config=config_graph)
                            ], sm=12, md=12)              
                        ], className='g-2 my-auto', style={'margin-top': '7px'}),
                    ])
                , style=tab_card)
            ], sm=12, lg=12),
        ], className='g-2 my-auto', style={'margin-top': '7px'}),
    ], fluid=True, style={'height': '100vh'})
])

@app.callback(
    Output('dataset_metas_codusur', 'data'),
    Output('data_atual', 'data'),
    Output('meta_ano', 'data'),
    Output('meta_mes', 'data'),
    Output('meta_semana', 'data'),
    Output('meta_sabado', 'data'),
    Input('interval-static', 'n_intervals')    
)
@cache.memoize()
def update_data(n_intervals):
    tz = pytz.timezone('America/Sao_Paulo')
    data_atual = datetime.now(tz).date()
       
    df_metas_geral = pd.read_csv(csv_url_geral)
    primeira_linha = df_metas_geral.iloc[0]
    meta_ano = primeira_linha['META_ANO']
    meta_mes = primeira_linha['META_MES']
    meta_semana = primeira_linha['META_SEMANA']
    meta_sabado = primeira_linha['META_SABADO']

    df_metas_usuario = pd.read_csv(csv_url_codusur)

    df_metas_usuario = df_metas_usuario[~df_metas_usuario['CODUSUR'].isin(rca_nao_controla)]
    df_metas_usuario_store = df_metas_usuario.to_dict('records')
    
    return  df_metas_usuario_store, data_atual, meta_ano, meta_mes, meta_semana, meta_sabado
@app.callback(
    Output('dataset_venda_liq', 'data'),
    Input('interval-dynamic', 'n_intervals')
)
@cache.memoize()
def update_dynamic_data(n_intervals):
    df_venda_liq_geral = venda_liquida()
    df_venda_liq_geral_store = df_venda_liq_geral.to_dict('records')
       
    
    return df_venda_liq_geral_store

@app.callback(
    Output('dataset_vendas_completa', 'data'),
    Input('interval-hora', 'n_intervals')
)
@cache.memoize()
def update_dynamic_data(n_intervals):
    df_vendas_completa = processar_dados(query_vendas_completa)
    df_vendas_completa_store = df_vendas_completa.to_dict('records')
       
    
    return df_vendas_completa_store

@app.callback(
    Output('indicator1', 'figure'),
    Input('dataset_venda_liq', 'data'),
    Input('data_atual', 'data'),
    Input('dropdown-ano', 'value'),
    Input('dropdown-mes', 'value'),
    Input('dropdown-rca', 'value')

)
def indicator1 (dataset_venda_liq, data_atual, ano_selecionado, mes_selecionado, rca_selecionado):
    
    df_ind1 = pd.DataFrame.from_dict(dataset_venda_liq).reset_index()
    df_ind1['DATA'] = pd.to_datetime(df_ind1['DATA'], errors='coerce')  # Converter a coluna 'DATA' para datetime

    # Filtragem por ano
    if ano_selecionado != 'Todos':
        df_ind1 = df_ind1[df_ind1['DATA'].dt.year == ano_selecionado]
    
    # Filtragem por mês
    if mes_selecionado != 'Todos':
        df_ind1 = df_ind1[df_ind1['DATA'].dt.month == mes_selecionado]
        
    # Filtragem por rca
    if rca_selecionado != 'Todos':
        df_ind1 = df_ind1[df_ind1['CODUSUR'] == rca_selecionado]
    
    
    faturamento = df_ind1['VENDA_LIQ'].sum()
    
    
    
    
    ind1 = go.Figure(go.Indicator(
        mode = 'number',
        value = faturamento,
        number= {'prefix': 'R$'},
        title = {"text": "Faturamento"}
    ))
    ind1.update_layout(
        main_config,
        height=200,
        template=template_theme,
        margin=dict(t=10, b=10, l=10, r = 10)
    )
    
    return ind1

@app.callback(
    Output('indicator2', 'figure'),
    Input('dataset_venda_liq', 'data'),
    Input('data_atual', 'data'),
    Input('dropdown-ano', 'value'),
    Input('dropdown-mes', 'value'),
    Input('dropdown-rca', 'value')
)
def indicator2 (dataset_venda_liq, data_atual, ano_selecionado, mes_selecionado, rca_selecionado):
    
    df_ind2 = pd.DataFrame.from_dict(dataset_venda_liq).reset_index()
    df_ind2['DATA'] = pd.to_datetime(df_ind2['DATA'], errors='coerce')  # Converter a coluna 'DATA' para datetime

    # Filtragem por ano
    if ano_selecionado != 'Todos':
        df_ind2 = df_ind2[df_ind2['DATA'].dt.year == ano_selecionado]
    
    # Filtragem por mês
    if mes_selecionado != 'Todos':
        df_ind2 = df_ind2[df_ind2['DATA'].dt.month == mes_selecionado]

    # Filtragem por rca
    if rca_selecionado != 'Todos':
        df_ind2 = df_ind2[df_ind2['CODUSUR'] == rca_selecionado]    
    
    faturamento = df_ind2['VENDA_LIQ'].sum()
    custo = df_ind2['CUSTO_LIQ'].sum()
    lucro_bruto = faturamento - custo
    margem = (lucro_bruto/faturamento)*100
    
    
    ind2 = go.Figure(go.Indicator(
        mode = 'number',
        value = margem,
        number= {'suffix': '%'},
        title = {"text": "Margem"}
    ))
    ind2.update_layout(
        main_config,
        height=200,
        template=template_theme,
        margin=dict(t=10, b=10, l=10, r = 10)
    )
    return ind2

@app.callback(
    Output('indicator3', 'figure'),
    Input('dataset_vendas_completa', 'data'),
    Input('data_atual', 'data'),
    Input('dropdown-ano', 'value'),
    Input('dropdown-mes', 'value'),
    Input('dropdown-rca', 'value') 
)
def indicator3 (dataset_vendas_completa, data_atual, ano_selecionado, mes_selecionado, rca_selecionado):
    
    df_ind3 = pd.DataFrame.from_dict(dataset_vendas_completa).reset_index()
    df_ind3['DATA'] = pd.to_datetime(df_ind3['DATA'], errors='coerce')  # Converter a coluna 'DATA' para datetime

    # Filtragem por ano
    if ano_selecionado != 'Todos':
        df_ind3 = df_ind3[df_ind3['DATA'].dt.year == ano_selecionado]
    
    # Filtragem por mês
    if mes_selecionado != 'Todos':
        df_ind3 = df_ind3[df_ind3['DATA'].dt.month == mes_selecionado]
    
    # Filtragem por rca
    if rca_selecionado != 'Todos':
        df_ind3 = df_ind3[df_ind3['CODUSUR'] == rca_selecionado]  
    
    faturamento = df_ind3['VALOR'].sum()
    clientes_positivados = df_ind3['CODCLIPRINC'].nunique()
    qtd_vendas = df_ind3['NUMPED'].nunique()
    tm_cliente = faturamento / clientes_positivados
    
    ind3 = go.Figure(go.Indicator(
        mode = 'number',
        value = clientes_positivados,
        title = {"text": "Clientes Positivados"}
    ))
    ind3.update_layout(
        main_config,
        height=200,
        template=template_theme,
        margin=dict(t=10, b=10, l=10, r = 10)
    )
    return ind3

@app.callback(
    Output('indicator4', 'figure'),
    Input('dataset_vendas_completa', 'data'),
    Input('data_atual', 'data'),
    Input('dropdown-ano', 'value'),
    Input('dropdown-mes', 'value'),
    Input('dropdown-rca', 'value')

)
def indicator4 (dataset_vendas_completa, data_atual, ano_selecionado, mes_selecionado, rca_selecionado):
    
    df_ind4 = pd.DataFrame.from_dict(dataset_vendas_completa).reset_index()
    df_ind4['DATA'] = pd.to_datetime(df_ind4['DATA'], errors='coerce')  # Converter a coluna 'DATA' para datetime

    # Filtragem por ano
    if ano_selecionado != 'Todos':
        df_ind4 = df_ind4[df_ind4['DATA'].dt.year == ano_selecionado]
    
    # Filtragem por mês
    if mes_selecionado != 'Todos':
        df_ind4 = df_ind4[df_ind4['DATA'].dt.month == mes_selecionado]

    # Filtragem por rca
    if rca_selecionado != 'Todos':
        df_ind4 = df_ind4[df_ind4['CODUSUR'] == rca_selecionado]    
    
    faturamento = df_ind4['VALOR'].sum()
    clientes_positivados = df_ind4['CODCLIPRINC'].nunique()
    tm_cliente = faturamento / clientes_positivados
    
    
    
    
    ind4 = go.Figure(go.Indicator(
        mode = 'number',
        value = tm_cliente,
        number= {'prefix': 'R$'},
        title = {"text": "Ticket Medio Cliente"}
    ))
    ind4.update_layout(
        main_config,
        height=200,
        template=template_theme,
        margin=dict(t=10, b=10, l=10, r = 10)
    )
    return ind4

@app.callback(
    Output('indicator5', 'figure'),
    Input('dataset_vendas_completa', 'data'),
    Input('data_atual', 'data'),
    Input('dropdown-ano', 'value'),
    Input('dropdown-mes', 'value'),
    Input('dropdown-rca', 'value')

)
def indicator5 (dataset_vendas_completa, data_atual, ano_selecionado, mes_selecionado, rca_selecionado):
    
    df_ind5 = pd.DataFrame.from_dict(dataset_vendas_completa).reset_index()
    df_ind5['DATA'] = pd.to_datetime(df_ind5['DATA'], errors='coerce')  # Converter a coluna 'DATA' para datetime

    # Filtragem por ano
    if ano_selecionado != 'Todos':
        df_ind5 = df_ind5[df_ind5['DATA'].dt.year == ano_selecionado]
    
    # Filtragem por mês
    if mes_selecionado != 'Todos':
        df_ind5 = df_ind5[df_ind5['DATA'].dt.month == mes_selecionado]

    # Filtragem por rca
    if rca_selecionado != 'Todos':
        df_ind5 = df_ind5[df_ind5['CODUSUR'] == rca_selecionado]  
    
    prazo_medio_ponderado = (df_ind5['PRAZOMEDIO'] * df_ind5['VALOR']).sum() / df_ind5['VALOR'].sum()
    
    
    
    
    ind5 = go.Figure(go.Indicator(
        mode = 'number',
        value = prazo_medio_ponderado,
        title = {"text": "Prazo Médio"}
    ))
    ind5.update_layout(
        main_config,
        height=200,
        template=template_theme,
        margin=dict(t=10, b=10, l=10, r = 10)
    )
    return ind5

@app.callback(
    Output('indicator6', 'figure'),
    Input('dataset_vendas_completa', 'data'),
    Input('data_atual', 'data'),
    Input('dropdown-ano', 'value'),
    Input('dropdown-mes', 'value'),
    Input('dropdown-rca', 'value')
 
)
def indicator6 (dataset_vendas_completa, data_atual, ano_selecionado, mes_selecionado, rca_selecionado):
    
    df_ind6 = pd.DataFrame.from_dict(dataset_vendas_completa).reset_index()
    df_ind6['DATA'] = pd.to_datetime(df_ind6['DATA'], errors='coerce')  # Converter a coluna 'DATA' para datetime

    # Filtragem por ano
    if ano_selecionado != 'Todos':
        df_ind6 = df_ind6[df_ind6['DATA'].dt.year == ano_selecionado]
    
    # Filtragem por mês
    if mes_selecionado != 'Todos':
        df_ind6 = df_ind6[df_ind6['DATA'].dt.month == mes_selecionado]
    
    # Filtragem por rca
    if rca_selecionado != 'Todos':
        df_ind6 = df_ind6[df_ind6['CODUSUR'] == rca_selecionado]
 
    
    # Agrupamento para calcular o número de produtos únicos por pedido
    df_ind6 = df_ind6.groupby(['NUMPED'])['CODPRODPRINC'].nunique()
    qtd_vendas = df_ind6.count()
    qtd_produtos = df_ind6.sum()
    mix_medio = qtd_produtos / qtd_vendas
    
    ind6 = go.Figure(go.Indicator(
        mode = 'number',
        value = mix_medio,
        title = {"text": "Mix Por Pedido"}
    ))
    ind6.update_layout(
        main_config,
        height=200,
        template=template_theme,
        margin=dict(t=10, b=10, l=10, r = 10)
    )
    return ind6

@app.callback(
    Output('graph1', 'figure'),
    Input('dataset_venda_liq', 'data'),
    Input('data_atual', 'data'),
    Input('meta_ano','data')
)
def graph1(dataset_venda_liq, data_atual, meta_ano):
    if not dataset_venda_liq:
        raise PreventUpdate
   
    data_atual = datetime.fromisoformat(data_atual).date()
    
    inicial = data_atual.replace(month=1, day=1)
    final = data_atual.replace(month=12, day=31)
   
    dias_uteis_ano = calcular_dias_uteis(inicial, final, feriados)
    dias_uteis_to_date = calcular_dias_uteis(inicial, data_atual, feriados)
    sabados_ano = calcular_sabados(inicial, final, feriados)
    sabados_to_date = calcular_sabados(inicial, data_atual, feriados)
    
 
    # Gerar o range de dias úteis entre as datas fornecidas
    filtro_dias_uteis = pd.date_range(start=inicial, end=final, freq='B')

    df1 = pd.DataFrame.from_dict(dataset_venda_liq).reset_index()
    # Filtrar o DataFrame para incluir apenas os registros em dias úteis
    df1['DATA'] = pd.to_datetime(df1['DATA'], errors='coerce')

    df_semana = df1[df1['DATA'].isin(filtro_dias_uteis)]
    # Agora você pode somar a coluna 'VENDA_LIQ' com base nesse filtro
    
    total_vendas_semana = df_semana['VENDA_LIQ'].sum()

    # Gerar um intervalo de datas
    datas = pd.date_range(start=inicial, end=final, freq='D')
    # Filtrar apenas os sábados
    sabados = datas[datas.weekday == 5]
    df_sabado = df1[df1['DATA'].isin(sabados)]
    total_vendas_sabados = df_sabado['VENDA_LIQ'].sum()
    
    projecao_semana = (total_vendas_semana/dias_uteis_to_date)*dias_uteis_ano
    projecao_sabado = (total_vendas_sabados/sabados_to_date)*sabados_ano
    projecao_total = projecao_semana + projecao_sabado
    
    total_vendas = total_vendas_semana + total_vendas_sabados
    
    perc_atingido = (total_vendas/meta_ano)*100
    projecao_total_percent = (projecao_total/meta_ano)*100
    
    if projecao_total_percent >100:
        range_final = projecao_total_percent * 1.1
    else:
        range_final = 100

    
    
    fig1 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=perc_atingido,
        number={"suffix": "%", "valueformat": ",.2f"},
        title={"text": "Atingimento da meta do Ano"},
        gauge={
            'axis': {'range': [None, range_final], 
                     'tickwidth': 1, 
                     'tickcolor': "black",
                     'showticklabels': True,
                     'tickvals': [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]  # Marcas no eixo
                     },  # Ajuste o intervalo conforme necessário
            'bar': {'color': "darkgreen"},
            'bgcolor': "lightgray",
            'steps': [
                {'range': [0, 100], 'color': "white"},

            ],
            'threshold': {
                'line': {'color': "red", 'width': 7},
                'thickness': 0.95,
                'value': projecao_total_percent
            }
    }
    ))
    
    fig1.update_layout(
        main_config,
        height=400,
        template=template_theme,
        margin=dict(t=50, b=10, l=40, r = 40)
    )
    fig1.add_annotation(
        x=0.5, y=0,  # Posição do texto,  # Posição do texto
        text= f"Projeção: R${projecao_total:,.2f}",  # Quebra de linha com <br>
        showarrow=False,
        font=dict(size=25)
    ) 
    return fig1



@app.callback(
    Output('graph2', 'figure'),
    Input('dataset_venda_liq', 'data'),
    Input('dataset_metas_codusur', 'data'),
    Input('data_atual', 'data'),
    Input('meta_mes', 'data'),
    Input('dropdown-rca', 'value')
)
def graph2(dataset_venda_liq, dataset_metas_codusur, data_atual, meta_mes, rca_selecionado):
    if not dataset_venda_liq:
        raise PreventUpdate
   
    data_atual = datetime.fromisoformat(data_atual).date()
    inicial = data_atual.replace(day=1)
    proximo_mes = (inicial + timedelta(days=31)).replace(day=1)   
    final = proximo_mes - timedelta(days=1)
    ontem = data_atual - timedelta(days=1)
   
    dias_uteis_mes = calcular_dias_uteis(inicial, final, feriados)
    dias_uteis_mes_to_date = calcular_dias_uteis(inicial, data_atual, feriados)
   
    sabados_mes = calcular_sabados(inicial, final, feriados)
    sabados_to_mes_date = calcular_sabados(inicial, data_atual, feriados)
    
    # Gerar o range de dias úteis entre as datas fornecidas
    filtro_dias_uteis_mes = pd.date_range(start=inicial, end=final, freq='B')

    df2 = pd.DataFrame.from_dict(dataset_venda_liq).reset_index()
    # Filtrar o DataFrame para incluir apenas os registros em dias úteis
    
    # Filtragem por rca
    if rca_selecionado != 'Todos':
        df_metas_usuario = pd.DataFrame.from_dict(dataset_metas_codusur).reset_index()
        df2 = df2[df2['CODUSUR'] == rca_selecionado]
        df_metas_usuario = df_metas_usuario[df_metas_usuario['CODUSUR'] == rca_selecionado]   
        primeira_linha = df_metas_usuario.iloc[0]
        meta_mes = primeira_linha['META_MES']  

    
    
    df2['DATA'] = pd.to_datetime(df2['DATA'], errors='coerce')

    df_semana = df2[df2['DATA'].isin(filtro_dias_uteis_mes)]
    # Agora você pode somar a coluna 'VENDA_LIQ' com base nesse filtro
    
    total_vendas_semana = df_semana['VENDA_LIQ'].sum()
    if pd.isna(total_vendas_semana):
        total_vendas_semana = 0
    else:
        pass
    
    
    # Gerar um intervalo de datas
    datas = pd.date_range(start=inicial, end=final, freq='D')
    # Filtrar apenas os sábados
    sabados = datas[datas.weekday == 5]
    df_sabado = df2[df2['DATA'].isin(sabados)]
    total_vendas_sabados = df_sabado['VENDA_LIQ'].sum()
    

    projecao_semana = (total_vendas_semana / dias_uteis_mes_to_date * dias_uteis_mes) if dias_uteis_mes_to_date != 0 else 0
    projecao_sabado = (total_vendas_sabados / sabados_to_mes_date * sabados_mes) if sabados_to_mes_date != 0 else 0   
    projecao_total = projecao_semana+projecao_sabado
    total_vendas = total_vendas_semana + total_vendas_sabados
    
    perc_atingido = (total_vendas/meta_mes)*100
    projecao_total_percent = (projecao_total/meta_mes)*100
    
    if projecao_total_percent >100:
        range_final = projecao_total_percent * 1.1
    else:
        range_final = 100
    
    fig2 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=perc_atingido,
        number={"suffix": "%", "valueformat": ",.2f"},
        title={"text": "Atingimento da meta do Mês"},
        gauge={
            'axis': {'range': [None, range_final], 
                     'tickwidth': 1, 
                     'tickcolor': "black",
                     'showticklabels': True,
                     'tickvals': [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]  # Marcas no eixo
                     },  # Ajuste o intervalo conforme necessário
            'bar': {'color': "darkgreen"},
            'bgcolor': "lightgray",
            'steps': [
                {'range': [0, 100], 'color': "white"},

            ],
            'threshold': {
                'line': {'color': "red", 'width': 7},
                'thickness': 0.95,
                'value': projecao_total_percent
            }
    }
    ))
  
    fig2.update_layout(
        main_config,
        height=400,
        template=template_theme,
        margin=dict(t=50, b=10, l=40, r = 40)
    )
    
    fig2.add_annotation(
        x=0.5, y=0,  # Posição do texto
        text= f"Projeção:R$ {projecao_total:,.2f}",  # Quebra de linha com <br>
        showarrow=False,
        font=dict(size=25)
    )   


    return fig2

@app.callback(
    Output('graph3', 'figure'),
    Input('dataset_venda_liq', 'data'),
    Input('dataset_metas_codusur', 'data'),
    Input('data_atual', 'data'),
    Input('meta_semana', 'data'),
    Input('meta_sabado', 'data'),
    Input('dropdown-rca', 'value'))

def graph3(dataset_venda_liq, dataset_metas_codusur, data_atual, meta_semana, meta_sabado, rca_selecionado):
    if not dataset_venda_liq:
        raise PreventUpdate
    
    data_atual = datetime.fromisoformat(data_atual).date()
    inicial = data_atual.replace(day=1)
    proximo_mes = (inicial + timedelta(days=31)).replace(day=1)   
    final = proximo_mes - timedelta(days=1)
    ontem = data_atual - timedelta(days=1)
    

    
    # Gerar um intervalo de datas
    datas = pd.date_range(start=inicial, end=ontem, freq='D')
    datas_exceto_hoje = pd.date_range(start=inicial, end=ontem, freq='B')
    sabados_exceto_hoje = datas[datas.weekday == 5]

    df3 = pd.DataFrame.from_dict(dataset_venda_liq).reset_index()

    
    # Filtragem por rca
    if rca_selecionado != 'Todos':
        df_metas_usuario = pd.DataFrame.from_dict(dataset_metas_codusur).reset_index()
        df3 = df3[df3['CODUSUR'] == rca_selecionado]
        df_metas_usuario = df_metas_usuario[df_metas_usuario['CODUSUR'] == rca_selecionado]   
        primeira_linha = df_metas_usuario.iloc[0]
        meta_sabado = primeira_linha['META_SABADO']  
        meta_semana = primeira_linha['META_SEMANA']  

    df3['DATA'] = pd.to_datetime(df3['DATA'], errors='coerce')
    df_hoje = df3[df3['DATA'].dt.date == data_atual]

    
    if data_atual.weekday() == 5:
        df_sabado_exceto_hoje = df3[df3['DATA'].isin(sabados_exceto_hoje)]
        sabados_restantes = calcular_sabados(data_atual, final, feriados)
        total_vendas_sabados_exceto_hoje = df_sabado_exceto_hoje['VENDA_LIQ'].sum()
        meta_hoje = (meta_sabado - total_vendas_sabados_exceto_hoje) / sabados_restantes
              
    else:
        df_dias_uteis_exceto_hoje = df3[~df3['CODUSUR'].isin(rca_nao_controla)]
        df_dias_uteis_exceto_hoje = df3[df3['DATA'].isin(datas_exceto_hoje)]
        dias_uteis_restantes = calcular_dias_uteis(data_atual, final, feriados)
        total_vendas_dias_uteis_ate_ontem = df_dias_uteis_exceto_hoje['VENDA_LIQ'].sum()
        meta_hoje = (meta_semana - total_vendas_dias_uteis_ate_ontem) / dias_uteis_restantes
    
    
    
    total_vendas_hoje = df_hoje['VENDA_LIQ'].sum()
    perc_atingido_hoje = (total_vendas_hoje/meta_hoje)*100
    
    if perc_atingido_hoje >100:
        range_final = perc_atingido_hoje * 1.1
    else:
        range_final = 100
    
    fig3 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=perc_atingido_hoje,
        number={"suffix": "%", "valueformat": ",.2f"},
        title={"text": "Atingimento da meta do dia"},
        gauge={
            'axis': {'range': [None, range_final], 
                     'tickwidth': 1, 
                     'tickcolor': "black",
                     'showticklabels': True,
                     'tickvals': [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]  # Marcas no eixo
                     },  # Ajuste o intervalo conforme necessário
            'bar': {'color': "darkgreen"},
            'bgcolor': "lightgray",
            'steps': [
                {'range': [0, 100], 'color': "white"},

            ],
        }
    ))
    
    fig3.update_layout(
        main_config,
        height=400,
        template=template_theme,
        margin=dict(t=50, b=10, l=40, r = 40)
    )
    fig3.add_annotation(
        x=0.5, y=0,  # Posição do texto
        text= f"Meta de Hoje: R$ {meta_hoje:,.2f}",  # Quebra de linha com <br>
        showarrow=False,
        font=dict(size=25)
    )  

    return fig3

@app.callback(
    Output('graph4', 'figure'),
    Input('dataset_venda_liq', 'data'),
    Input('dataset_metas_codusur', 'data'),
    Input('data_atual', 'data')
)
def graph4(dataset_venda_liq, dataset_metas_codusur, data_atual):
    if not dataset_venda_liq:
        raise PreventUpdate
    
    df_metas_usuario = pd.DataFrame.from_dict(dataset_metas_codusur).reset_index()

    
    data_atual = datetime.fromisoformat(data_atual).date()
    inicial = data_atual.replace(day=1)
    proximo_mes = (inicial + timedelta(days=31)).replace(day=1)   
    final = proximo_mes - timedelta(days=1)
    ontem = data_atual - timedelta(days=1)
    
    
    # Gerar um intervalo de datas
    datas = pd.date_range(start=inicial, end=ontem, freq='D')
    datas_exceto_hoje = pd.date_range(start=inicial, end=ontem, freq='B')
    sabados_exceto_hoje = datas[datas.weekday == 5]

    df4 = pd.DataFrame.from_dict(dataset_venda_liq).reset_index()
    df4['DATA'] = pd.to_datetime(df4['DATA'], errors='coerce')
    df_hoje = df4[df4['DATA'].dt.date == data_atual]


    
    if data_atual.weekday() == 5:  # Se for sábado
        # Filtra as vendas dos sábados anteriores (exceto o sábado atual)
        df_sabado_exceto_hoje = df4[df4['DATA'].isin(sabados_exceto_hoje)]
        
        # Calcula os sábados restantes no mês a partir da data atual
        sabados_restantes = calcular_sabados(data_atual, final, feriados)
        
        # Calcula a venda líquida acumulada por CODUSUR nos sábados anteriores
        df_total_vendas_sabados_exceto_hoje = df_sabado_exceto_hoje.groupby('CODUSUR', as_index=False)['VENDA_LIQ'].sum()
        
        # Filtra apenas os resultados que estão em lista_rca
        df_total_vendas_sabados_exceto_hoje = df_total_vendas_sabados_exceto_hoje[~df_total_vendas_sabados_exceto_hoje['CODUSUR'].isin(rca_nao_controla)]
        
        # Mescla com o DataFrame de metas para calcular o META_HOJE para cada vendedor
        df_merged = pd.merge(df_metas_usuario, df_total_vendas_sabados_exceto_hoje, on='CODUSUR', suffixes=('_METAS', '_VENDAS'), how='left')
        
        # Calcula a meta de hoje para cada vendedor com base nos sábados restantes
        df_merged['META_HOJE'] = (df_merged['META_SABADO'] - df_merged['VENDA_LIQ']) / sabados_restantes
        
        # Mescla com o DataFrame `df_hoje` para incluir as vendas do dia atual
        df_merged = pd.merge(df_merged, df_hoje, on='CODUSUR', suffixes=('_MERGE', '_HOJE'), how='left')
        
        # Remove colunas desnecessárias e calcula o percentual de atingimento
        df_meta_hoje = df_merged.drop(['DATA', 'index'], axis=1)
        df_meta_hoje = df_meta_hoje[df_meta_hoje['META_SABADO'] != 0]

        
        df_meta_hoje.fillna(0, inplace=True)  # Substituir valores nulos por 0
        df_meta_hoje['META_HOJE']= (df_meta_hoje['META_SABADO']-df_meta_hoje['VENDA_LIQ_MERGE'])/sabados_restantes
        df_meta_hoje['PERC_ATINGIDO'] = (df_meta_hoje['VENDA_LIQ_HOJE'] / df_meta_hoje['META_HOJE']) * 100

              
    else:
        df_dias_uteis_exceto_hoje = df4[df4['DATA'].isin(datas_exceto_hoje)]
        dias_uteis_restantes = calcular_dias_uteis(data_atual, final, feriados)
        df_total_vendas_dias_uteis_exceto_hoje = df_dias_uteis_exceto_hoje.groupby('CODUSUR', as_index=False)['VENDA_LIQ'].sum()
        df_total_vendas_dias_uteis_exceto_hoje = df_total_vendas_dias_uteis_exceto_hoje[~df_total_vendas_dias_uteis_exceto_hoje['CODUSUR'].isin(rca_nao_controla)]

        df_merged = pd.merge(df_metas_usuario, df_total_vendas_dias_uteis_exceto_hoje, on='CODUSUR', suffixes=('_METAS', '_VENDAS'))
        df_merged['META_HOJE'] = (df_merged['META_SEMANA']-df_merged['VENDA_LIQ'])/dias_uteis_restantes
        df_merged = pd.merge(df_merged, df_hoje, on='CODUSUR', suffixes=('_MERGE', '_HOJE'), how='left')
        df_meta_hoje = df_merged.drop(['DATA'], axis=1)
        df_meta_hoje['PERC_ATINGIDO'] = (df_meta_hoje['VENDA_LIQ_HOJE']/df_meta_hoje['META_HOJE'])*100
        df_meta_hoje = df_meta_hoje.dropna(subset=['CODUSUR', 'PERC_ATINGIDO'])

    fig4 = go.Figure(go.Bar(
        x=df_meta_hoje['PERC_ATINGIDO'],  # Valores no eixo x (Percentual de atingimento)
        y=df_meta_hoje['CODUSUR'].astype(str),        # Valores no eixo y (Nomes dos vendedores)
        orientation='h',                  # Orientação horizontal
        text=[f'{p:.2f}%' for p in df_meta_hoje['PERC_ATINGIDO']],  # Exibir o percentual com 2 casas decimais
        textposition='auto', # Posição do texto
        width=0.8  
    ))

    # Adicionando título e labels
    fig4.update_layout(
        main_config,
        title='Percentual de Atingimento de Meta diária por Vendedor',
        xaxis_title='Percentual de Atingimento (%)',
        yaxis_title='Vendedores (RCA)',
        xaxis=dict(range=[0, 100]),  # Definindo o intervalo do eixo x de 0 a 100%
        height=600,
        template=template_theme,
        margin=dict(t=50, b=10, l=40, r = 40)
    )

    # Exibindo o gráfico
    return fig4


@app.callback(
    Output('graph5', 'figure'),
    Input('dataset_venda_liq', 'data'),
    Input('dropdown-periodo', 'value'),
    Input('dropdown-rca', 'value'),
    Input('data_atual', 'data')
)
def graph5(dataset_venda_liq, seleciona_periodo, rca_selecionado, data_atual):
    if not dataset_venda_liq:
        raise PreventUpdate
  
    df5 = pd.DataFrame.from_dict(dataset_venda_liq).reset_index()
    df5['DATA'] = pd.to_datetime(df5['DATA'], errors='coerce')
    
    # Filtragem por rca
    if rca_selecionado != 'Todos':
        df5 = df5[df5['CODUSUR'] == rca_selecionado]
    
    data_atual = datetime.fromisoformat(data_atual).date()
    
  # Agrupamento condicional baseado no valor do dropdown
    if seleciona_periodo == 'A':  # Agrupar por Ano
        df_grouped = df5.groupby(df5['DATA'].dt.year).agg({'VENDA_LIQ': 'sum'}).reset_index()
        df_grouped.columns = ['Ano', 'Faturamento']
        df_grouped['Ano'] = df_grouped['Ano'].astype(str)
        x_column = 'Ano'
    elif seleciona_periodo == 'M':  # Agrupar por Mês
        df_grouped = df5.groupby(df5['DATA'].dt.to_period('M')).agg({'VENDA_LIQ': 'sum'}).reset_index()
        df_grouped.columns = ['Mês', 'Faturamento']
        df_grouped['Mês'] = df_grouped['Mês'].astype(str)
        x_column = 'Mês'
    elif seleciona_periodo == 'D':  # Agrupar por Dia
        df_grouped = df5.groupby(df5['DATA'].dt.date).agg({'VENDA_LIQ': 'sum'}).reset_index()
        df_grouped.columns = ['Dia', 'Faturamento']
        # Converter date para string no formato 'YYYY-MM-DD'
        df_grouped['Dia'] = df_grouped['Dia'].astype(str)
        x_column = 'Dia'
    


    # Criar gráfico de linha usando plotly.express
    fig5 = px.line(
        df_grouped, 
        x=x_column,  # Coluna de tempo (Ano, Mês ou Dia)
        y='Faturamento',  # Coluna de faturamento
        title=f"Evolução do Faturamento por {'Ano' if seleciona_periodo == 'A' else 'Mês' if seleciona_periodo == 'M' else 'Dia'}",
        labels={x_column: 'Período', 'Faturamento': 'Faturamento'}  # Renomear eixos
    )
    fig5.update_layout(
        main_config,
        height=400,
        template=template_theme,
        margin=dict(t=80, b=10, l=40, r=40),  # Mantém esta definição de margem
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=7, label="7 d", step="day", stepmode="backward"),
                    dict(count=15, label="15 d", step="day", stepmode="backward"),
                    dict(count=1, label="1 m", step="month", stepmode="backward"),
                    dict(count=6, label="6 m", step="month", stepmode="backward"),
                    dict(count=1, label="1 a", step="year", stepmode="backward"),
                    dict(count=5, label="5 a", step="year", stepmode="backward"),
                    dict(label="Ytd", step="year", stepmode="todate"),  # Year to Date
                    dict(label="Mtd", step="month", stepmode="todate"),
                    dict(label="Todos", step="all")  # Exibir todos os dados
                ]),
                activecolor="#636EFA",  # Cor do botão ativo
                bgcolor="#303030"  # Cor de fundo dos botões
            ),
            rangeslider=dict(visible=False),  # Habilitar o range slider
            type='date'  # Tipo de dado no eixo X (datas)
        )
    )

    return fig5





if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8360, debug=True)

