# Import relevant libraries
import pandas as pd
from sodapy import Socrata
import requests
import base64
from urllib.parse import urlencode
from datetime import datetime, timedelta
import plotly.express as px
#import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from io import StringIO
# .venv\Scripts\activate
# pip install -r requirements.txt


app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],)
app.title = "Site Viewer"
server = app.server



"""app.layout = html.Div(children = [html.Div(className = "row", children = html.Div(html.H1("Battery Voltage Status of Sites"),)), 
                                  html.Div(className = "graph", children = html.Div(dcc.Graph(id='battery-graph'),)),
                                  html.Div(className = "row", children = html.Div(html.Button('Refresh Data', id='refresh-button', n_clicks=0))),
                                  dcc.Store(id = 'metadata'), # store site metadata
                                  dcc.Store(id = 'gagers'), # store gager list
                                  dcc.Store(id = 'telemetry'), # store telemetry
                                  dcc.Store(id = 'last_discharge_data'), # stores last data value
                                  ],)"""

app.layout = html.Div(
    children=[
        html.Div(
            className="row",
            children=[
                # Column for user controls
                html.Div(
                    className="four columns div-user-controls",
                    children=[
                        html.H2("Telemetered Sites"),
                        html.P("""displays basic infomation for telemetered sites based on Socrata copy of gData"""),
                        html.Button('Refresh Data', id='refresh-button', n_clicks=0),
                        #html.Div(className="div-for-dropdown",children=[dcc.DatePickerSingle(id="date-picker",style={"border": "0px solid black"},)],),
                        # Change to side-by-side for mobile layout
                        html.Div(
                            className="row",
                            children=[
                                html.P("""select a parameter"""),
                                #html.Div(className="div-for-dropdown",children=[dcc.Dropdown(id="parameter",options=[{"label": "Discharge", "value": "discharge"},{"label": "Battery Volts", "value": "battery_volts"},],value="battery_volts",clearable=False,),],),
                                #html.Div(className="div-for-dropdown",children=[dcc.Dropdown(id="bar-selector",multi=True,)],),
                            ],
                        ),
                        html.P(id="total-rides"),
                        html.P(id="total-rides-selection"),
                        html.P(id="date-value"),
                    ],
                ),
                # Column for app graphs and plots
                html.Div(className="eight columns div-for-charts bg-grey",children=[
                    dcc.Graph(id='battery-graph'),
                    #dcc.Graph(id="histogram"),
                    ],),
            ],
        ),
        dcc.Store(id = 'metadata'), # store site metadata
        dcc.Store(id = 'gagers'), # store gager list
        dcc.Store(id = 'telemetry'), # store telemetry
        dcc.Store(id = 'last_discharge_data'), # stores last data value
    ]
)
# Define the layout of the dashboard
@app.callback(
    Output('metadata', 'data'),
    Output('gagers', 'data'),
    Input('refresh-button', 'n_clicks')
)
# Define functions as in your original code
def site_metadata(n_clicks):
    """reads site meta data, returns sites and gager list"""
    socrata_api_id = "37ja57noqzsdkkeo5ox34pfzm"
    socrata_api_secret = "4i1u1tyb6mfivhnw2fqhhsrim675gurrw8g1zegdwomix9xj91"
    socrata_database_id = "g7er-dgc7"
    dataset_url = f"https://data.kingcounty.gov/resource/{socrata_database_id}.json"
    socrataUserPw = (f"{socrata_api_id}:{socrata_api_secret}").encode('utf-8')
    base64AuthToken = base64.b64encode(socrataUserPw)
    headers = {'accept': '*/*', 'Authorization': 'Basic ' + base64AuthToken.decode('utf-8')}
    response = requests.get(dataset_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
       
        gager_list = df["gager"].drop_duplicates().tolist()
        df = df.to_json(orient="split")
    else:
        return dash.no_update 
    return df, gager_list


@app.callback(
    Output('telemetry', 'data'),
    Input('refresh-button', 'n_clicks')
)
def telemetry_status(n_clicks):
    socrata_api_id = "37ja57noqzsdkkeo5ox34pfzm"
    socrata_api_secret = "4i1u1tyb6mfivhnw2fqhhsrim675gurrw8g1zegdwomix9xj91"
    socrata_database_id = "gzfg-8xtp"
    dataset_url = f"https://data.kingcounty.gov/resource/{socrata_database_id}.json"
    socrataUserPw = (f"{socrata_api_id}:{socrata_api_secret}").encode('utf-8')
    base64AuthToken = base64.b64encode(socrataUserPw)
    headers = {'accept': '*/*', 'Authorization': 'Basic ' + base64AuthToken.decode('utf-8')}

    today = datetime.now()
    yesterday = today - timedelta(days=1)
    query_params = {
        "$select": "site, datetime, battery_volts",
        "$where": f"datetime >= '{yesterday.strftime('%Y-%m-%d')}' AND datetime < '{today.strftime('%Y-%m-%d')}'"
    }
    encoded_query = urlencode(query_params)
    dataset_url = f"{dataset_url}?{encoded_query}"
    
    response = requests.get(dataset_url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        df = df.to_json(orient="split")
    else:
        return dash.no_update
    return df



@app.callback(
    Output('last_discharge_data', 'data'),
    Input('refresh-button', 'n_clicks'),
    Input('metadata', 'data'),
)
def last_data(n_clicks, metadata):
    metadata = pd.read_json(StringIO(metadata), orient="split")
    site_list = metadata["site"].tolist()
    
    
    #dataset_url = f"https://data.kingcounty.gov/resource/{socrata_database_id}.json"
    #client = Socrata("data.kingcounty.gov", None)
   
    #results = client.get(
    #    "hkim-5ysi",
    #    select="site_id, MAX(datetime) AS datetime, corrected_data",
    #    where="parameter='discharge",
    #    group="site_id")

    socrata_api_id = "37ja57noqzsdkkeo5ox34pfzm"
    socrata_api_secret = "4i1u1tyb6mfivhnw2fqhhsrim675gurrw8g1zegdwomix9xj91"
    socrata_database_id = "hkim-5ysi"
    dataset_url = f"https://data.kingcounty.gov/resource/{socrata_database_id}.json"
    socrataUserPw = (f"{socrata_api_id}:{socrata_api_secret}").encode('utf-8')
    base64AuthToken = base64.b64encode(socrataUserPw)
    headers = {'accept': '*/*', 'Authorization': 'Basic ' + base64AuthToken.decode('utf-8')}

  
    today = datetime.now()
    yesterday = today - timedelta(days=2)
    query_params = {
        "$select": "site_id as site, MAX(datetime) as last_log",
        "$group": "site"
        
    }
    
    #"$where": f"last_log >= '{yesterday.strftime('%Y-%m-%d')}' AND last_log < '{today.strftime('%Y-%m-%d')}'"
    #"$where": f"datetime >= '{yesterday.strftime('%Y-%m-%d')}' AND datetime < '{today.strftime('%Y-%m-%d')}'"
    encoded_query = urlencode(query_params)
    dataset_url = f"{dataset_url}?{encoded_query}"
    
    response = requests.get(dataset_url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        
        df = pd.DataFrame(data)
        
        df["last_log"] = pd.to_datetime(df['last_log'])
        df["last_log"]  = df["last_log"].dt.strftime('%Y-%m-%d %H:%M')
        
      
        df = df.to_json(orient="split")
        return df
    else:
        return dash.no_update
  


@app.callback(
    Output('battery-graph', 'figure'),
    Input('metadata', 'data'),
    Input('telemetry', 'data'),
    Input('last_discharge_data', 'data'),
    Input('refresh-button', 'n_clicks')
)
def create_battery_graph(metadata, telemetry, last_discharge_data, n_clicks):
    metadata = pd.read_json(StringIO(metadata), orient="split")
    
    telemetry = pd.read_json(StringIO(telemetry), orient="split")
    
    last_discharge_data = pd.read_json(StringIO(last_discharge_data), orient="split")
    
    battery_site_status = metadata.merge(telemetry, on="site")
    battery_site_status = battery_site_status.merge(last_discharge_data, on="site", how = "left")
    battery_site_status = battery_site_status.fillna("")
    
  
    battery_site_status["longitude"] = battery_site_status["longitude"].astype(float)
    battery_site_status["latitude"] = battery_site_status["latitude"].astype(float)
    battery_site_status["battery_volts"] = battery_site_status["battery_volts"].astype(float)
    
    battery_site_status['color_category'] = "grey"
    battery_site_status.loc[battery_site_status["battery_volts"] < 11.5, 'color_category'] = "< 11.5"
    battery_site_status.loc[(battery_site_status["battery_volts"] >= 11.5) & (battery_site_status["battery_volts"] < 12.0), 'color_category'] = "< 12"
    battery_site_status.loc[(battery_site_status["battery_volts"] >= 12.0) & (battery_site_status["battery_volts"] < 12.3), 'color_category'] = "< 12.3"
    battery_site_status.loc[(battery_site_status["battery_volts"] >= 12.3) & (battery_site_status["battery_volts"] < 12.5), 'color_category'] = "< 12.5"
    battery_site_status.loc[battery_site_status["battery_volts"] >= 12.5, 'color_category'] = "12.5 +"
    
    #fig = px.scatter(battery_site_status, y="latitude", x="longitude", color="battery_volts")
                          
    #color_discrete_map={
    #                         "grey": "grey",
    #                      "< 11.5": "red",
    #                      "< 12": "darkred",
    #                      "< 12.3": "darkorange",
    #                      "< 12.5": "orange",
    #                         "12.5 +": "blue",
    #                     },
    fig = px.scatter_map(battery_site_status,
                         lat=battery_site_status["latitude"],
                         lon=battery_site_status["longitude"],
                         color=battery_site_status["color_category"],
                         hover_name="site",
                         hover_data={"last_log": True, "battery_volts": True, "latitude": False, "longitude": False, "color_category": False},
                          zoom=9)

    fig.update_layout(
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=0,  # Position at the bottom
        xanchor="center",
        x=0.5  # Center horizontally
    ),
    autosize=True,
    margin=dict(l=0, r=0, t=0, b=0),
    #mapbox_style="open-street-map"  # Add map style if not already defined
)
    return fig



if __name__ == '__main__':
    app.run_server(debug=False)
