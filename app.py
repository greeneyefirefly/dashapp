# -*- coding: utf-8 -*-
"""
@author: Samantha Deokinanan
CUNY SPS MSDS DATA 608: Module 4

Build a dash app for a arborist studying the health of various tree species (as defined by the variable ‘spc_common’) across each borough (defined by the variable ‘borough’). This arborist would like to answer the following two questions for each species and in each borough:

1. What proportion of trees are in good, fair, or poor health according to the ‘health’ variable?

2. Are stewards (steward activity measured by the ‘steward’ variable) having an impact on the health of trees?
"""

# Import modules
import dash
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objs as go
import pandas as pd
import numpy as np

# Import data
url = ('https://data.cityofnewyork.us/resource/nwxe-4ae8.json?$limit=5000' +\
        ' &$select=spc_common,boroname,health,steward,count(tree_id)' +\
        '&$group=spc_common,boroname,health,steward').replace(' ', '%20')
nyctrees = pd.read_json(url)

# Data tidying
nyctrees = nyctrees.dropna()
nyctrees['spc_common'] = nyctrees['spc_common'].str.title()
nyctrees['spc_common'] = nyctrees['spc_common'].replace(["'Schubert' Chokecherry"], 'Schubert Chokecherry')
nyctrees['steward'] = nyctrees['steward'].replace('None', '0') \
    .replace('1or2', '1-2') \
        .replace('3or4', '3-4') \
            .replace('4orMore', '4+')

# Dropdown selections
borough = np.sort(nyctrees['boroname'].unique())
species = np.sort(nyctrees['spc_common'].unique())

# Dash application
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets = external_stylesheets)
server = app.server

app.layout = html.Div([
    html.H3('Trees in NYC'),
    html.P('By Samantha Deokinanan'),
    html.P('''
           Street tree data is from the TreesCount! 2015 Street Tree Census, conducted by volunteers and staff organized by NYC Parks & Recreation and partner organizations. The graphs below highlight the proportion of healthy trees along the streets of NYC. By selecting a borough and species of tree, the graph on the left will highlight the overall health conditions of the species, while the graph on the right will highlight the overall health conditions of the species by stewardship.
           '''),
    html.Label('Select a borough: '),
    dcc.Dropdown(id = 'borough_selection',
                   options=[{'label': i, 'value': i} for i in borough],
                   value = borough[0],
                   style={'height': '35px', 'width': '150px'}),
    html.Label('Select a tree species: '),
    dcc.Dropdown(id = 'species_selection',
                 options=[{'label': i, 'value': i} for i in species],
                 value = species[0],
                 style={'height': '35px', 'width': '300px'}),
    html.Div([
        html.Div(
          dcc.Graph(id = 'health_proportion'),
                    className="six columns",
                    style={"margin": 0, 'display': 'inline-block'}),
        html.Div(
          dcc.Graph(id = 'stewards_health'),
                    className="six columns",
                    style={"margin": 0, 'display': 'inline-block'}),
        ], className = "row")
    ], style = {'columnCount': 1})


@app.callback(
    Output('health_proportion', 'figure'),
    [Input('borough_selection', 'value'), Input('species_selection', 'value')])

def health_prop(borough, species):
    df = nyctrees[(nyctrees['boroname'] == borough) &
                  (nyctrees['spc_common'] == species)]

    health_prop = (round(df.groupby('health').sum()['count_tree_id']/sum(df['count_tree_id']),2)).reset_index()

    for i in ['Fair','Good','Poor']:
        if all(i != health_prop['health']):
            health_prop.loc[2] = [i, 0]

    health_prop['health'] = pd.Categorical(health_prop['health'], ['Good','Fair','Poor'])
    health_prop = health_prop.sort_values('health')
    
    return {
        'data': [go.Bar(
        x = health_prop['health'],
        y = health_prop['count_tree_id'],
        marker_color = ['#109618','#FFA15A','#990099'])
        ],
        'layout': go.Layout(
            title = f'Health of {species} Trees in {borough}',
            yaxis = {'title':'Proportion (%)', 'tickformat':'0%'},
            xaxis = {'title':'Tree Health Condition',
                     'categoryarray': ['Good', 'Fair', 'Poor'], 
                     'categoryorder':"array"}
        )
    }

@app.callback(
     Output('stewards_health', 'figure'),
    [Input('borough_selection', 'value'), Input('species_selection', 'value')])

def stewardship(borough, species):
    df = nyctrees[(nyctrees['boroname'] == borough) &
                  (nyctrees['spc_common'] == species)]

    steward_health = pd.merge(df,
                            pd.DataFrame(df.groupby('steward').sum()['count_tree_id']),
                            on = 'steward')
    
    steward_health['steward_p'] = round(steward_health['count_tree_id_x'] / steward_health['count_tree_id_y'], 2)
    
    categories = ['0','1-2', '3-4', '4+']
    
    hover = (steward_health.pivot(columns = 'steward', index = 'health', values = 'count_tree_id_x'))\
        .reindex(columns = categories, fill_value = 0)\
            .reset_index().fillna(0)
    
    steward_health = (steward_health.pivot(columns = 'steward', index = 'health', values = 'steward_p'))\
        .reindex(columns = categories, fill_value = 0)\
            .reset_index().fillna(0)
                  
    trace1 = go.Bar(
        x = categories,
        y = steward_health.loc[1].drop('health'),
        text = hover.loc[1].drop('health'),
        marker_color = '#109618',
        name = 'Good')

    trace2 = go.Bar(
        x = categories,
        y = steward_health.loc[0].drop('health'),
        text = hover.loc[0].drop('health'),
        marker_color = '#FFA15A',
        name = 'Fair')

    trace3 = go.Bar(
        x = categories,
        y = steward_health.loc[2].drop('health'),
        text = hover.loc[2].drop('health'),
        marker_color = '#990099',
        name = 'Poor')
    
    return {
        'data': [trace1, trace2, trace3],
        'layout': go.Layout(
            title = f'Health of {species} Trees in {borough} by Stewardship',
            yaxis = {'title':'Proportion (%)', 
                     'tickformat':'0%'},
            xaxis = {'title':'Number of Stewardship'},
            barmode = 'stack'
        )
    }
 
if __name__ == '__main__':
    app.run_server()
    
    
