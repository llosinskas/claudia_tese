import plotly.express as px 

# Mapeamento de cores fixas por nome de curva (substring match, case-insensitive)
CORES_CURVAS = {
    'solar':            '#CC8400',   # amarelo escuro / dourado
    'recarga':          "#0FFF27",   # branco (recarga bateria) - ANTES de 'carga'
    'carga':            "#021A03",   # preto
    'bateria':          '#1565C0',   # azul escuro
    'diesel':           '#CC0000',   # vermelho
    'biogas':           '#2E7D32',   # verde escuro
    'biogás':           '#2E7D32',   # verde escuro (com acento)
    'concession':       '#7B1FA2',   # roxo (pega Concessionaria e Concessionária)
    'venda':            '#FF8C00',   # laranja
    'rede':             '#7B1FA2',   # roxo (grid/rede)
    'déficit':          '#B71C1C',   # vermelho escuro
    'deficit':          '#B71C1C',   # vermelho escuro
    'exporta':          '#FF6F00',   # laranja escuro
    'original':         '#616161',   # cinza escuro
    'otimizada':        '#00838F',   # teal
    'soc':              '#1565C0',   # azul (state of charge)
}


def _cor_para_curva(nome_trace):
    """Retorna a cor fixa se o nome do trace contiver uma palavra-chave conhecida."""
    nome_lower = nome_trace.lower()
    for chave, cor in CORES_CURVAS.items():
        if chave in nome_lower:
            return cor
    return None


def Grafico_linha(df, xlabel, ylabel, title, grid=True):

    df_num = df.select_dtypes(include=['number'])
    fig = px.line(
        df_num, 
        title = title , 
    )

    # Aplica cores fixas por nome de curva
    for trace in fig.data:
        cor = _cor_para_curva(trace.name)
        if cor:
            trace.line = dict(width=3, color=cor)
        else:
            trace.line = dict(width=3)
    fig.update_layout(
        font=dict(color='black', size=100 ),)
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(color="black", size=20),
            x=0.4),
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend_title_font=dict(color='black', size=20,  family='Arial'),  
        legend_title_text='',
        legend=dict(font=dict(size=20),orientation='h', yanchor='bottom', y=-0.5, xanchor='center', x=0.5),
    )
    
    fig.update_legends(
        font=dict(color='black')
    )
    fig.update_xaxes(
        title_text=xlabel,
        title_font=dict(color='black', size=20),
        tickfont=dict(color='black', size=20),  
        showgrid=True, gridcolor='grey', linecolor='black'
    )

    fig.update_yaxes(
        title_text=ylabel,
        title_font=dict(color='black', size=20),
        tickfont=dict(color='black', size=20),
        showgrid=True, gridcolor='grey', linecolor='black'
    )

    return fig
