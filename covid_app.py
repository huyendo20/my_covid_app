import pandas as pd
import numpy as np
import plotly.express as px  # (version 4.7.0)
import plotly.graph_objects as go

import dash_bootstrap_components as dbc
import dash  # (version 1.12.0) pip install dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from plotly.subplots import make_subplots
from dash.exceptions import PreventUpdate
import datetime

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# ---------- Import and clean data (importing csv into pandas)
# df = pd.read_csv("intro_bees.csv")
df0 = pd.read_csv("data_cleaned.csv", parse_dates = ["date"])
# print(list(df0.columns))


df = df0.groupby(['iso_code','location','population'])[['total_cases', 'total_deaths']].max()
df.reset_index(inplace=True)
df['cases_per_100000']= 100000*df['total_cases']/df['population']
df['deaths_per_million']=1000000*df['total_deaths']/df['population']
# print(df[df['location']=='United States'])

df_time = df0.groupby(['iso_code','location','population',
    pd.Grouper(key="date", freq="M")])[['daily_cases','daily_deaths','daily_cases_per_100000','daily_deaths_per_1millions']].sum()
df_time.reset_index(inplace = True)
df_time['month_year'] = df_time['date'].dt.strftime('%Y-%m')
df_time = df_time.rename(columns={'daily_cases': "cases", 'daily_deaths': 'deaths',
    'daily_cases_per_100000': 'cases_per_100000','daily_deaths_per_1millions':'deaths_per_million'})



# ------------------------------------------------------------------------------
# App layout
app.layout = html.Div([
    dbc.Row(dbc.Col(html.H1("Covid 19 impact"),
                    #    width={'size': 6, 'offset': 3},
                        style={'color': '#002699', 'text-align': 'center', 'font-size': '18px', 'font-family':'verdana'},
                        ),
                ),
   
    dbc.Row([
        dbc.Col(
            dcc.Dropdown(id = 'world_map',
                        options =[
                            {"label": "Cases", "value": 'cases'},
                            {"label": "Deaths", "value": 'deaths'},
                            {"label": "Cases per 100 000", "value": "cases_per_100000"},
                            {"label": "Deaths per million", "value": "deaths_per_million"},],
                        multi = False,
                        value = 'cases',
                        style = {'width': "100%"}
                            ),
            width = {'size': 2, "offset": 0, 'order': 1}                
            ),
        dbc.Col(
            dcc.Dropdown(id = 'start_month',
                        options =[
                            {"label": month, "value": month} for month in np.sort(df_time['month_year'].unique())],
                        multi = False,
                        value = '2019-12',
                        style = {'width': "100%"}
                            ),
            width = {'size': 1, "offset": 1, 'order': 2}                
            ),
        dbc.Col(
            dcc.Dropdown(id = 'end_month',
                        options =[                            
                            {"label": month, "value": month} for month in np.sort(df_time['month_year'].unique())],
                        multi = False,
                        value = '2020-10',
                        style = {'width': "100%"}
                            ),
            width = {'size': 1, "offset": 0, 'order': 3}                
            ),
            
        dbc.Col(
            dcc.Dropdown(id = 'country',
                        options = [{"label": label, "value": label} for label in list(df['location'])],
                        multi = True,
                        value = ["France", "Italy"],
                        style = {'width': "100%"}
                            ),
            width = {'size': 3, "offset": 0, 'order': 4}
            ), 
        dbc.Col(
            dcc.Dropdown(id = 'variable',
                        options = [{"label": "Total cases", "value": "total_cases"},
                                  {"label": "Total deaths", "value": "total_deaths"},
                                  {"label": "Daily cases", "value": "daily_cases"},
                                  {"label": "Daily deaths", "value": "daily_deaths"},
                                  {"label": "Stringency", "value": "stringency_index"},
                                  {"label": "Daily cases per 100000", "value": "daily_cases_per_100000"},
                                  {"label": "Daily deaths per million", "value": "daily_deaths_per_1millions"},],
                        multi = True,
                        value = ["total_cases", "total_deaths"],
                        style = {"width": "100%"}
                            ),
            width = {"size": 4, "offset": 0, 'order': 5}            
            ),
        ]),
    
    dbc.Row([ 
        dbc.Col(
            html.Div(id='container_map', children = {}),
            width = {'size': 6, "offset": 0, 'order': 1}
            ),
        dbc.Col(
            html.Div(id='container_country', children = {}),
            width = {'size': 2, "offset": 0, 'order': 2}
            ),
        dbc.Col(
            html.Div(id='container_var', children = {}),
            width = {'size': 4, "offset": 0, 'order': 2}
            ),
        ]),
    
    html.Br(),



    dbc.Row([
        dbc.Col(html.Div([
            dcc.Graph(id='my_map', figure={}),
            dcc.Graph(id='world_chart', figure={})]
            ),
            width = {'size': 6, "offset": 0, 'order': 1}
                ),
        dbc.Col(html.Div(dcc.Graph(id='my_chart', figure={}, style = {'height' : '900px'})
            ), 
            width = {'size': 6, "offset": 0, 'order': 2}
            ),
        ]),   
    
    ])



# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    [Output(component_id = 'container_map', component_property='children'),
    Output(component_id = 'my_map', component_property='figure'),
    Output(component_id = 'world_chart', component_property='figure'),    
    Output(component_id='container_country', component_property='children'),
    Output(component_id='container_var', component_property='children'),
    Output(component_id='my_chart', component_property='figure')],
    [Input(component_id='world_map', component_property='value'),
    Input(component_id='country', component_property='value'),
    Input(component_id = 'variable', component_property = 'value'),
    Input(component_id = 'start_month', component_property = 'value'),
    Input(component_id = 'end_month', component_property = 'value')
    ]
)


def update_graph(option_case, option_country, option_variable, start_time, end_time):
    if option_case is None or start_time is None or end_time is None:
        raise PreventUpdate
    else:
        container1 = "Impact in the world during a certain timeline."

        dff = df_time.copy()
        dff = dff[(dff['date']>= pd.to_datetime(start_time)) & (dff['date']< pd.to_datetime(end_time))]
        dff = dff.groupby(['iso_code','location','population'])[['cases', 'deaths', 'cases_per_100000', 'deaths_per_million']].sum()
        dff.reset_index(inplace=True)

        
        # World map.
        fig1 = px.choropleth(
            data_frame=dff,
            locations='iso_code',
            scope='world',
            color=option_case,
            hover_name='location',
            color_continuous_scale=px.colors.sequential.YlOrRd
        )
        fig1.update_layout(title=dict(font=dict(size=28),x=0.5,xanchor='center'),
                          margin=dict(l=10, r=10, t=10, b=0))

        
    #Chart to compare chosen countries on certain properties.
    if len(option_country)==0 or len(option_variable)==0:
        raise PreventUpdate
    elif len(option_country) == 4:
        option_country = option_country[:3]
    else:
        container2 = "Please choose less than 4 countries"
        container3 = "Please choose characters"

        dff = df0.copy()
        dff = dff[dff['location'].isin(list(option_country))]
        #date_axis = dff[dff["location"] == "France"]["date"]
    
        # Plotly chart
        col = len(option_variable)
        font = dict(size=24, family='verdana', color='#0052cc')
        fig2 = make_subplots(rows=col, cols=1, shared_xaxes=False,
            subplot_titles=['{}'.format(var.capitalize().replace('_', ' ')) for var in option_variable])
        colours = ["#730099", "#009933", "#0099e6" ]
        for i, var in enumerate(option_variable): 
            show_legend = False
            if i == 0:
                show_legend = True 
            for j, country in enumerate(option_country):
                fig2.add_trace(go.Scatter(x=dff[dff["location"]==country]["date"], y=dff[dff["location"]==country][var],
                    name = '{}'.format(country), showlegend = show_legend, line = dict(color = colours[j]),
                        ), 
                    row=i+1, col=1
                    )
        for i in fig2.layout.annotations:
            i["font"] = font
            
                # fig2.update_xaxes(title_text = '{}'.format(var.capitalize().replace('_', ' ')),
                #     title_font=dict(size=24, family='verdana', color='#0052cc'),
                #      row=i+1, col=1)

        #fig2.update_layout(title=dict(font=dict(size=28),x=0.5,xanchor='center'),
         #                 margin=dict(l=10, r=10, t=10, b=10))
        
        fig2.update_layout(margin=dict(l=10, r=10, t=40, b=10))

        fig2.update_layout(legend ={'x': 0, 'y': 1} )

        

        
    dff = df0.copy()
    dff = dff.groupby(['date'])[['total_cases', 'total_deaths', "daily_cases", "daily_deaths"]].sum()
    dff.reset_index(inplace=True)

    
    fig3 = go.Figure()

    fig3.add_trace(go.Scatter(
        x = dff["date"], y = dff["total_cases"],
        name="Total cases", line_color = "#1f77b4"
    ))


    fig3.add_trace(go.Scatter(
        x = dff["date"], y = dff["total_deaths"], name = " Total deaths",
        yaxis="y2", line_color = "#4633FF"
    ))

    fig3.add_trace(go.Scatter(
        x = dff["date"], y = dff["daily_cases"], name = "Daily cases",
        yaxis="y3", line_color = "#FFA533"
    ))

    fig3.add_trace(go.Scatter(
        x = dff["date"], y = dff["daily_deaths"], name = "Daily deaths",
        yaxis="y4", line_color = "#820A2F"
    ))

    fig3.update_layout(
        xaxis=dict(
        domain=[0.05, 0.9]
            ),
        yaxis=dict(
            title="Total cases",
            titlefont=dict(
                color="#1f77b4"
            ),
            tickfont=dict(
                color="#1f77b4"
            )
        ),
        yaxis2=dict(
            title="Total deaths",
            titlefont=dict(
                color="#4633FF"
            ),
            tickfont=dict(
                color="#4633FF"
            ),
            anchor="free",
            overlaying="y",
            side="left",
            position=0.025
        ),
        yaxis3=dict(
            title="Daily cases",
            titlefont=dict(
                color="#FFA533"
            ),
            tickfont=dict(
                color="#FFA533 "
            ),
            anchor="x",
            overlaying="y",
            side="right"
        ),
        yaxis4=dict(
            title="Daily deaths",
            titlefont=dict(
                color="#820A2F"
            ),
            tickfont=dict(
                color="#820A2F"
            ),
            anchor="free",
            overlaying="y",
            side="right",
            position=0.925
        )
    )

    fig3.update_layout(title=dict(font=dict(size=28),x=0.5,xanchor='center'),
                          margin=dict(l=1, r=1, t=5, b=5))
    fig3.update_layout(legend ={'x': 0.1, 'y': 1} )

    



    return container1, fig1, fig3, container2, container3, fig2


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)
    # above line give error http://x86_64-conda_cos6-linux-gnu:8050/
    #app.run_server(host='127.0.0.1', port='8050', debug=True)



