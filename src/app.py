
import pandas as pd
import numpy as np
from sodapy import Socrata
from dash import Dash, dcc, html, Input, Output, callback, dash_table
import plotly.express as px
import dash_bootstrap_components as dbc
import dash_auth


#read NYC open data
data_url='data.cityofnewyork.us'    # The Host Name for the API endpoint (the https:// part will be added automatically)
data_set='uip8-fykc'    # The data set at the API endpoint (311 data in this case)
app_token='qhW5Sl8E8hKe4rxqJ9WfG00Oc'  # The app token created in the prior steps
client = Socrata(data_url,app_token)      # Create th
# e client to point to the API endpoint
# Set the timeout to 60 seconds
client.timeout = 90
# Retrieve the first 2000 results returned as JSON object from the API
# The SoDaPy library converts this JSON object to a Python list of dictionaries
results = client.get(data_set, limit=2000)
# Convert the list of dictionaries to a Pandas data frame
df = pd.DataFrame.from_records(results)
# Save the data frame to a CSV file
#df.to_csv("C:/Users/Biu9/PycharmProjects/open_datasets/my_311_data_.csv")
df = df[['arrest_date', 'arrest_boro', 'jurisdiction_code', 'perp_sex', 'perp_race', 'age_group', 'pd_desc']]

#rename values for nyc boroughs and perpetrator sex
mapping_boro = {'B':'Bronx','M':'Manhattan','K':'Brooklyng', 'S':'Staten Island', 'Q':'Queens'}
df['arrest_boro'] = df['arrest_boro'].map(mapping_boro)
mapping_sex = {'M':'Male','F':'Female','U':'Unknown'}
df['perp_sex'] = df['perp_sex'].map(mapping_sex)

# Preparing your data for usage *******************************************
df["arrest_date"] = pd.to_datetime(df["arrest_date"])
# Using pandas DataFrame.reset_index()
dff = df.groupby(['arrest_date', 'arrest_boro', 'perp_sex', 'perp_race', 'age_group', 'pd_desc'])['jurisdiction_code'].agg('count').reset_index(name='counts')

# Use size().reset_index() method
dff.rename({'arrest_date':'date_of_arrest'},axis=1, inplace=True)
dff.rename({'arrest_boro':'location'},axis=1, inplace=True)
dff.rename({'perp_sex':'sex'},axis=1, inplace=True)
dff.rename({'perp_race':'race'},axis=1, inplace=True)
df2 = dff.groupby(['date_of_arrest', 'location', 'race']).size().reset_index(name='counts')

stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = Dash(__name__, external_stylesheets=stylesheets)
server = app.server

# auth = dash_auth.BasicAuth(
#     app,
#     {'nyc':'crimen',
#      'nycapp':'arresto'}
# )

app.layout = html.Div([

    html.H4('New York Police Department Arrest Dasboard', style={"textAlign": "center"}
            ),

    dcc.Dropdown(id='dpdn2', value=['Bronx', 'Manhattan'], multi=True,
                 options=[{'label': x, 'value': x} for x in
                          df2.location.unique()]),

    #     dcc.Dropdown(id='dpdn2', multi=True,
    #                  options=[{"label": x, "value": x}
    #                     for x in sorted(df2["location"].unique())],
    #                  value=["Bronx","Manhattan","Brooklyng"]),

    html.Div([
        dcc.Graph(id='pie-graph', figure={}, className='five columns'),
        dcc.Graph(id='my-graph', figure={}, clickData=None, hoverData=None,
                  # I assigned None for tutorial purposes. By defualt, these are None, unless you specify otherwise.
                  config={
                      'staticPlot': False,  # True, False
                      'scrollZoom': True,  # True, False
                      'doubleClick': 'reset',  # 'reset', 'autosize' or 'reset+autosize', False
                      'showTips': False,  # True, False
                      'displayModeBar': True,  # True, False, 'hover'
                      'watermark': True,
                      # 'modeBarButtonsToRemove': ['pan2d','select2d'],
                  },
                  className='five columns'
                  )
    ])
])


@app.callback(
    Output(component_id='my-graph', component_property='figure'),
    Input(component_id='dpdn2', component_property='value'),
)
def update_graph(boro_chosen):
    dff = df2[df2.location.isin(boro_chosen)]
    fig = px.line(data_frame=dff, x='date_of_arrest', y='counts', color='race',
                  custom_data=['location'])
    fig.update_traces(mode='lines+markers')
    return fig


# Dash version 1.16.0 or higher
@app.callback(
    Output(component_id='pie-graph', component_property='figure'),
    Input(component_id='my-graph', component_property='hoverData'),
    Input(component_id='my-graph', component_property='clickData'),
    Input(component_id='my-graph', component_property='selectedData'),
    Input(component_id='dpdn2', component_property='value')
)
def update_side_graph(hov_data, clk_data, slct_data, boro_chosen):
    if hov_data is None:
        dff2 = dff[dff.location.isin(boro_chosen)]
        # dff2 = dff2[dff2.arrest_date == 1952]
        print(dff2)
        fig2 = px.pie(data_frame=dff2, values='counts', names='location',
                      title='Counts for 2023')
        return fig2
    else:
        print(f'hover data: {hov_data}')
        # print(hov_data['points'][0]['customdata'][0])
        # print(f'click data: {clk_data}')
        # print(f'selected data: {slct_data}')
        dff2 = df2[df2.location.isin(boro_chosen)]
        hov_date = hov_data['points'][0]['x']
        dff2 = dff2[dff2.date_of_arrest == hov_date]
        fig2 = px.pie(data_frame=dff2, values='counts', names='location', title=f'Counts for: {hov_date}')
        return fig2


if __name__ == '__main__':
    app.run_server(debug=False)