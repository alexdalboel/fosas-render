from flask import Flask
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_leaflet as dl
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np

# Initialize the Flask app
server = Flask(__name__)

# Initialize the Dash app
app = dash.Dash(__name__, server=server)

# Load the data
df = pd.read_csv('fosas_with_url.csv')

# Add the new entry to the DataFrame
valle_de_los_caidos = {
    'Provincia': 'General Reference',
    'Municipio': 'Valle de los Caídos',
    'TIPO_FOSA': 'Reference',
    'NUMERO_PERSONAS_FOSA': df[df['ESTADO_ACTUAL'] == 'TRASLADADA AL VALLE DE LOS CAÍDOS']['NUMERO_PERSONAS_FOSA'].sum(),
    'Latitude': 40.521035,
    'Longitude': -15.857079,
    'URL': 'https://es.wikipedia.org/wiki/Valle_de_los_Ca%C3%ADdos',
    'NUMERO_REGISTRO': 'Valle de los Caídos',
    'OBSERVACIONES': df[df['ESTADO_ACTUAL'] == 'TRASLADADA AL VALLE DE LOS CAÍDOS']['NUMERO_PERSONAS_FOSA'].sum(),
    'ESTADO_ACTUAL': 'TRASLADADA AL VALLE DE LOS CAIDOS',
    'NUMERO_PERSONAS_FOSA_RANGE': None  # Optional
}

# Append this new entry to the DataFrame
df = pd.concat([df, pd.DataFrame([valle_de_los_caidos])], ignore_index=True)


# Handle missing NUMERO_PERSONAS_FOSA by setting a default size
default_size = 10  # Base size for circles with missing data
df['NUMERO_PERSONAS_FOSA'] = df['NUMERO_PERSONAS_FOSA'].fillna(default_size)

# Define the ranges for "Number of people"
bins = [0, 5, 10, 30, 60, 100, float('inf')]
labels = ['0-5', '5-10', '10-30', '30-60', '60-100', '+100']
df['NUMERO_PERSONAS_FOSA_RANGE'] = pd.cut(df['NUMERO_PERSONAS_FOSA'], bins=bins, labels=labels, include_lowest=True)

# Helper function to generate circle markers based on a filtered DataFrame
def generate_markers(filtered_df):
    return [
        dl.CircleMarker(
            center=[row['Latitude'], row['Longitude']],
            radius=min(row['NUMERO_PERSONAS_FOSA'] / 100, 150),  # Maximum size for circles
            color='#E66100',
            fill=True,
            fillColor='#5D3A9B',
            fillOpacity=0.6,
            children=[
                dl.Tooltip(row['NUMERO_REGISTRO']),
                dl.Popup([
                    html.H4('More Information'),
                    html.A('15mpedia link', href=row['URL'], target='_blank'),
                    html.Div(
                        style={
                            'max-height': '150px',  # Set maximum height
                            'overflow-y': 'auto',  # Enable vertical scrolling
                            'margin-top': '10px',  # Add some spacing
                        },
                        children=html.P(row['OBSERVACIONES']) if not pd.isna(row['OBSERVACIONES']) else html.P('No observations available.')
                    )
                ])
            ]
        ) for _, row in filtered_df.iterrows()
    ]



app.layout = html.Div([
    html.Link(
        href='https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap',
        rel='stylesheet'
    ),
    html.H1('Mass graves from the Spanish Civil War', style={'font-family': 'Roboto, sans-serif', 'text-align': 'center'}),
    
    html.Div(
        style={'display': 'flex', 'justify-content': 'space-between'},
        children=[
            # Map container 
            html.Div(
                style={'flex': '5', 'margin-right': '20px'},
                children=[
                    dl.Map(
                        style={'width': '100%', 'height': '400px'},
                        center=[40.4168, -3.7038],  # Centered on Spain
                        zoom=6,
                        id='map',
                        children=[
                            dl.TileLayer(),
                            dl.FeatureGroup(id='feature-group')
                        ]
                    )
                ]
            ),
            # Dropdowns container 
            html.Div(
                style={'flex': '3'},
                children=[
                    html.Label('Filter by Autonomous Community:', style={'font-family': 'Roboto, sans-serif'}),
                    dcc.Dropdown(
                        id='province-dropdown',
                        options=[{'label': str(prov), 'value': str(prov)} for prov in sorted(df['ComAutonom'].dropna().unique())],
                        placeholder='Select a province',
                        style={'margin-bottom': '20px', 'font-family': 'Roboto, sans-serif'}
                    ),
                    html.Label('Filter by Municipality:', style={'font-family': 'Roboto, sans-serif'}),
                    dcc.Dropdown(
                        id='municipality-dropdown',
                        options=[{'label': str(mun), 'value': str(mun)} for mun in sorted(df['Municipio'].dropna().unique())],
                        placeholder='Select a municipality',
                        style={'margin-bottom': '20px', 'font-family': 'Roboto, sans-serif'}
                    ),
                    html.Label('Filter by mass grave type:', style={'font-family': 'Roboto, sans-serif'}),
                    dcc.Dropdown(
                        id='type-dropdown',
                        options=[{'label': str(ftype), 'value': str(ftype)} for ftype in sorted(df['TIPO_FOSA'].dropna().unique())],
                        placeholder='Select a mass grave type',
                        style={'margin-bottom': '20px', 'font-family': 'Roboto, sans-serif'}
                    ),

                    html.Label('Filter by Number of People:', style={'font-family': 'Roboto, sans-serif'}),
                    dcc.Dropdown(
                        id='people-dropdown',
                        options=[{'label': label, 'value': label} for label in labels],
                        placeholder='Select a range',
                        style={'margin-bottom': '20px', 'font-family': 'Roboto, sans-serif'}
                    )
                ]
            )
        ]
    )
])

# Callback to update the map based on dropdown filters
@app.callback(
    Output('feature-group', 'children'),
    [Input('province-dropdown', 'value'),
     Input('municipality-dropdown', 'value'),
     Input('type-dropdown', 'value'),
     Input('people-dropdown', 'value')]
)
def update_map(selected_province, selected_municipality, selected_type, selected_people):
    # Apply filters
    filtered_df = df.copy()
    if selected_province:
        filtered_df = filtered_df[filtered_df['ComAutonom'] == selected_province]
    if selected_municipality:
        filtered_df = filtered_df[filtered_df['Municipio'] == selected_municipality]
    if selected_type:
        filtered_df = filtered_df[filtered_df['TIPO_FOSA'] == selected_type]
    if selected_people:
        filtered_df = filtered_df[filtered_df['NUMERO_PERSONAS_FOSA_RANGE'] == selected_people]
    
    # Generate and return updated markers
    return generate_markers(filtered_df)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
