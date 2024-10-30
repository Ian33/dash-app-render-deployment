# Import relevant libraries
import pandas as pd
from sodapy import Socrata
import requests
import base64
from urllib.parse import urlencode
from datetime import datetime, timedelta
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State

# in render The "Start Command" should be updated as follows: $gunicorn app:server
# Create the Dash app
app = dash.Dash(__name__)
server = app.server

# Dash Layout
app.layout = html.Div([
    html.H1("Battery Voltage Status of Sites"),
    dcc.Graph(id='battery-graph'),
    html.Button('Refresh Data', id='refresh-button', n_clicks=0),
    dcc.Store(id = 'metadata'), # store site metadata
    dcc.Store(id = 'gagers'), # store gager list
    dcc.Store(id = 'telemetry'), # store telemetry

])
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
        print(f"Failed to retrieve data: {response.status_code}")
        df, gager_list = pd.DataFrame().to_json(orient="split"), []
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
        print(f"Failed to retrieve data: {response.status_code}")
        df = pd.DataFrame()
        df = df.to_json(orient="split")
    return df


@app.callback(
    Output('battery-graph', 'figure'),
    Input('metadata', 'data'),
    Input('telemetry', 'data'),
    Input('refresh-button', 'n_clicks')
)
def create_battery_graph(metadata, telemetry, n_clicks):
    metadata = pd.read_json(metadata, orient="split")
    
    telemetry = pd.read_json(telemetry, orient="split")
  
    battery_site_status = metadata.merge(telemetry, on="site")


    battery_site_status["longitude"] = battery_site_status["longitude"].astype(float)
    battery_site_status["latitude"] = battery_site_status["latitude"].astype(float)
    battery_site_status["battery_volts"] = battery_site_status["battery_volts"].astype(float)
    
    battery_site_status['color_category'] = "grey"
    battery_site_status.loc[battery_site_status["battery_volts"] < 11.5, 'color_category'] = "< 11.5"
    battery_site_status.loc[(battery_site_status["battery_volts"] >= 11.5) & (battery_site_status["battery_volts"] < 12.0), 'color_category'] = "< 12"
    battery_site_status.loc[(battery_site_status["battery_volts"] >= 12.0) & (battery_site_status["battery_volts"] < 12.3), 'color_category'] = "< 12.3"
    battery_site_status.loc[(battery_site_status["battery_volts"] >= 12.3) & (battery_site_status["battery_volts"] < 12.5), 'color_category'] = "< 12.5"
    battery_site_status.loc[battery_site_status["battery_volts"] >= 12.5, 'color_category'] = "12.5 +"
    
    fig = px.scatter_map(battery_site_status,
                          lat=battery_site_status["latitude"],
                          lon=battery_site_status["longitude"],
                          color="color_category",
                          color_discrete_map={
                              "grey": "grey",
                              "< 11.5": "red",
                              "< 12": "darkred",
                              "< 12.3": "darkorange",
                              "< 12.5": "orange",
                              "12.5 +": "blue",
                          },
                          hover_name="site",
                          hover_data={"battery_volts": True, "latitude": False, "longitude": False, "color_category": False},
                          zoom=9)
    return fig



if __name__ == '__main__':
    app.run_server(debug=False)