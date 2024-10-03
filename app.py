import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import pytz
from datetime import datetime, timedelta
from dash.exceptions import PreventUpdate
from feriados import *
from metas import *
from function import *
from config import *

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])



# df_vendas = processar_dados(query_vendas)

# # Extraindo os anos únicos da coluna 'DATA' do df_vendas
# anos_vendas = df_vendas['DATA'].dt.year.unique()
# opcoes_anos = [{'label': str(ano), 'value': ano} for ano in sorted(anos_vendas, reverse=True)]

# meses_vendas = df_vendas['DATA'].dt.month.unique()
# opcoes_meses = [{'label': str(mes), 'value': mes} for mes in sorted(meses_vendas, reverse=True)]

# # Adicionar a opção "Todos" no dropdown
# opcoes_anos.insert(0, {'label': 'Todos', 'value': 'Todos'})
# opcoes_meses.insert(0, {'label': 'Todos', 'value': 'Todos'})



app.layout = html.Div([
    dbc.Container([
        dcc.Store(id='dataset_venda_liq', data={}),
        dcc.Store(id='data_atual', data={}),
        dcc.Interval(
            id='interval-component',
            interval=10*1000,
            n_intervals=0
        ),
        dbc.Row([
            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        # dbc.Row([
                        #     dbc.Col([
                        #         dcc.Dropdown(
                        #             id='dropdown-ano',
                        #             options=opcoes_anos,
                        #             value='Todos',  # Valor padrão
                        #             clearable=False,
                        #             style={'width': '100%', 'color': 'black'}
                        #         )
                        #     ], sm=12, md=6),
                        #     dbc.Col([
                        #         dcc.Dropdown(
                        #             id='dropdown-mes',
                        #             options=opcoes_meses,
                        #             value='Todos',  # Valor padrão
                        #             clearable=False,
                        #             style={'width': '100%', 'color': 'black'}
                        #         )
                        #     ], sm=12, md=6)
                        # ],className='g-2 my-auto', style={'margin-top': '7px'}),
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
                        ], className='g-2 my-auto', style={'margin-top': '7px'})
                    ])
                , style=tab_card)
            ], sm=12, lg=12),
        ], className='g-2 my-auto', style={'margin-top': '7px'}),
    ], fluid=True, style={'height': '100vh'})
])

@app.callback(
    Output('dataset_venda_liq', 'data'),
    Output('data_atual', 'data'),
    Input('interval-component', 'n_intervals')    
)

def update_data(n_intervals):
    tz = pytz.timezone('America/Sao_Paulo')
    data_atual = datetime.now(tz).date()
    
    # Processa os dados completos
    df_venda_liq_geral = venda_liquida()
   
    
    df_venda_liq_geral_store = df_venda_liq_geral.to_dict('records')
    
    return df_venda_liq_geral_store, data_atual

@app.callback(
    Output('graph1', 'figure'),
    Input('dataset_venda_liq', 'data'),
    Input('data_atual', 'data')
)
def graph1(dataset_venda_liq, data_atual):
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
    
    perc_atingido = (total_vendas/meta_anual_empresa)*100
    projecao_total_percent = (projecao_total/meta_anual_empresa)*100
    
    
    
    fig1 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=perc_atingido,
        number={"suffix": "%", "valueformat": ",.2f"},
        title={"text": "Atingimento da meta do Ano"},
        gauge={
            'axis': {'range': [None, 100], 
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
        text= f"Projeção: {projecao_total_percent:.2f}%",  # Quebra de linha com <br>
        showarrow=False,
        font=dict(size=25)
    ) 
    return fig1



@app.callback(
    Output('graph2', 'figure'),
    Input('dataset_venda_liq', 'data'),
    Input('data_atual', 'data')
)
def graph2(dataset_venda_liq, data_atual):
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
    
    perc_atingido = (total_vendas/meta_mensal_empresa)*100
    projecao_total_percent = (projecao_total/meta_mensal_empresa)*100
    
    fig2 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=perc_atingido,
        number={"suffix": "%", "valueformat": ",.2f"},
        title={"text": "Atingimento da meta do Mês"},
        gauge={
            'axis': {'range': [None, 100], 
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
        text= f"Projeção: {projecao_total_percent:.2f}%",  # Quebra de linha com <br>
        showarrow=False,
        font=dict(size=25)
    )   


    return fig2

@app.callback(
    Output('graph3', 'figure'),
    Input('dataset_venda_liq', 'data'),
    Input('data_atual', 'data')
)
def graph3(dataset_venda_liq, data_atual):
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
    df3['DATA'] = pd.to_datetime(df3['DATA'], errors='coerce')
    df_hoje = df3[df3['DATA'].dt.date == data_atual]




  
    if data_atual.weekday() == 5:
        df_sabado_exceto_hoje = df3[df3['DATA'].isin(sabados_exceto_hoje)]
        sabados_restantes = calcular_sabados(data_atual, final, feriados)
        total_vendas_sabados_exceto_hoje = df_sabado_exceto_hoje['VENDA_LIQ'].sum()
        meta_hoje = ( meta_mensal_sabados - total_vendas_sabados_exceto_hoje) / sabados_restantes
              
    else:
        df_dias_uteis_exceto_hoje = df3[df3['DATA'].isin(datas_exceto_hoje)]
        dias_uteis_restantes = calcular_dias_uteis(data_atual, final, feriados)
        total_vendas_dias_uteis_ate_ontem = df_dias_uteis_exceto_hoje['VENDA_LIQ'].sum()
        meta_hoje = (meta_mensal_dias_uteis - total_vendas_dias_uteis_ate_ontem) / dias_uteis_restantes
 
    
    total_vendas_hoje = df_hoje['VENDA_LIQ'].sum()
    perc_atingido_hoje = (total_vendas_hoje/meta_hoje)*100
    
    fig3 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=perc_atingido_hoje,
        number={"suffix": "%", "valueformat": ",.2f"},
        title={"text": "Atingimento da meta do dia"},
        gauge={
            'axis': {'range': [None, 100], 
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

    return fig3

@app.callback(
    Output('graph4', 'figure'),
    Input('dataset_venda_liq', 'data'),
    Input('data_atual', 'data')
)
def graph4(dataset_venda_liq, data_atual):
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

    df4 = pd.DataFrame.from_dict(dataset_venda_liq).reset_index()
    df4['DATA'] = pd.to_datetime(df4['DATA'], errors='coerce')
    df_hoje = df4[df4['DATA'].dt.date == data_atual]

    df_metas = pd.read_csv(csv_url)

  
    if data_atual.weekday() == 5:
        df_sabado_exceto_hoje = df4[df4['DATA'].isin(sabados_exceto_hoje)]
        sabados_restantes = calcular_sabados(data_atual, final, feriados)
        total_vendas_sabados_exceto_hoje = df_sabado_exceto_hoje['VENDA_LIQ'].sum()
        meta_hoje = ( meta_mensal_sabados - total_vendas_sabados_exceto_hoje) / sabados_restantes
              
    else:
        df_dias_uteis_exceto_hoje = df4[df4['DATA'].isin(datas_exceto_hoje)]
        dias_uteis_restantes = calcular_dias_uteis(data_atual, final, feriados)
        total_vendas_dias_uteis_exceto_hoje = df_dias_uteis_exceto_hoje.groupby('CODUSUR', as_index=False)['VENDA_LIQ'].sum()

        meta_hoje = (meta_mensal_dias_uteis - total_vendas_dias_uteis_exceto_hoje) / dias_uteis_restantes
 
    
    total_vendas_hoje = df_hoje['VENDA_LIQ'].sum()
    perc_atingido_hoje = (total_vendas_hoje/meta_hoje)*100
    vendedores = ['vendas01','vendas02']
    # Criando o gráfico de barras horizontal
    fig4 = go.Figure(go.Bar(
        x=perc_atingido_hoje,  # Percentual de atingimento
        y=vendedores,  # Nomes dos vendedores
        orientation='h',  # Orientação horizontal
        text=[f'{p}%' for p in perc_atingido_hoje],  # Exibir o percentual nas barras
        textposition='auto'  # Posição do texto
    ))

    # Adicionando título e labels
    fig4.update_layout(
        title='Percentual de Atingimento de Meta por Vendedor',
        xaxis_title='Percentual de Atingimento (%)',
        yaxis_title='Vendedores',
        xaxis=dict(range=[0, 100]),  # Definindo o intervalo do eixo x de 0 a 100%
    )
    fig4.show()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8350, debug=True)

