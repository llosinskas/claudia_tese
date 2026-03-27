import matplotlib.pyplot as plt 
import pandas as pd 
import numpy as np 
import mplcursors as mpl
import plotly.graph_objects as go
import plotly.express as px 



def Grafico_linha(df, xlabel, ylabel, title, grid=True):
    #fig, ax = plt.subplots()
    #df.plot(ax = ax)
    #ax.grid(grid)
    #ax.set_title(title)
    #ax.set_xlabel(xlabel)
    #ax.set_ylabel(ylabel)
    #cursor = mpl.cursor(ax, hover=True)
    df_num = df.select_dtypes(include=['number'])
    fig = px.line(
        df_num, 
        title = title 
    )
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(color="black", size=20),
              
            x=0.4),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black'),
        
    #legend=dict(orientation='h', yanchor='bottom', y=1.05, xanchor='center', x=0.5)
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
