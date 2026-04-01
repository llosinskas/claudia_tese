import plotly.express as px 


def Grafico_linha(df, xlabel, ylabel, title, grid=True):

    df_num = df.select_dtypes(include=['number'])
    fig = px.line(
        df_num, 
        title = title , 
    )
    fig.update_traces(

        line = (dict(width=3))
    )
    fig.update_layout(
        font=dict(color='black', size=200, family='Arial'),)
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(color="black", size=20),
            x=0.4),
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend_title_font=dict(color='black', size=20,  family='Arial'),  
        legend_title_text='Legenda',
        
    )
    
    fig.update_legends(
        font=dict(color='black')
    )
    fig.update_xaxes(
        title_text=xlabel,
        title_font=dict(color='black'),
        tickfont=dict(color='black'),
        showgrid=True, gridcolor='grey', linecolor='black'
    )

    fig.update_yaxes(
        title_text=ylabel,
        title_font=dict(color='black'),
        tickfont=dict(color='black'),
        showgrid=True, gridcolor='grey', linecolor='black'
    )

    return fig
