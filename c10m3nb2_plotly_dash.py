import pandas as pd
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go

# Load SpaceX launch data
spacex_data = pd.read_csv("datasets/spacex_launch_dash.csv")

# Get payload range values
payload_min = spacex_data['Payload Mass (kg)'].min()
payload_max = spacex_data['Payload Mass (kg)'].max()

# Get unique launch sites
launch_sites = spacex_data['Launch Site'].unique().tolist()

# Initialize Dash application
dashboard = dash.Dash(name=__name__)

# Define dashboard layout
dashboard.layout = html.Div([
    # Header
    html.Div([
        html.H1(
            'SpaceX Launch Dashboard',
            style={
                'color': '#2C3E50',
                'textAlign': 'center',
                'fontFamily': 'Arial',
                'fontSize': 42,
                'marginBottom': '20px',
                'marginTop': '10px'
            }
        )
    ]),
    
    # Launch site selection
    html.Div([
        html.Label('Select Launch Site:', style={'fontWeight': 'bold', 'marginRight': '10px'}),
        dcc.Dropdown(
            id='launch-site-selector',
            options=[{'label': 'All Launch Sites', 'value': 'ALL'}] + 
                    [{'label': site, 'value': site} for site in launch_sites],
            placeholder='Choose a launch site',
            value='ALL',
            style={'width': '80%', 'margin': 'auto'},
            clearable=False
        )
    ], style={'marginBottom': '25px', 'textAlign': 'center'}),
    
    # Success rate visualization
    html.Div([
        html.H3('Launch Success Rate', style={'textAlign': 'center'}),
        dcc.Graph(id='launch-success-chart')
    ], style={'marginBottom': '30px'}),
    
    # Payload selection
    html.Div([
        html.H3('Payload Range Selection (kg)', style={'textAlign': 'center'}),
        dcc.RangeSlider(
            id='payload-range-slider',
            min=0,
            max=10000,
            step=500,
            marks={
                0: '0 kg',
                2500: '2500 kg',
                5000: '5000 kg',
                7500: '7500 kg',
                10000: '10000 kg'
            },
            value=[payload_min, payload_max],
            tooltip={"placement": "bottom", "always_visible": True}
        )
    ], style={'margin': '0 auto', 'width': '80%', 'marginBottom': '30px'}),
    
    # Payload vs Success correlation
    html.Div([
        html.H3('Payload vs. Launch Success Correlation', style={'textAlign': 'center'}),
        dcc.Graph(id='payload-success-correlation')
    ])
], style={'backgroundColor': '#F8F9F9', 'padding': '20px', 'fontFamily': 'Arial'})

# Callback for updating the success rate chart
@dashboard.callback(
    Output('launch-success-chart', 'figure'),
    Input('launch-site-selector', 'value')
)
def update_success_chart(selected_site):
    if selected_site == 'ALL':
        # For all sites: Show success count by site
        success_counts = spacex_data.groupby('Launch Site')['class'].sum().reset_index()
        total_counts = spacex_data.groupby('Launch Site').size().reset_index(name='total')
        result_df = pd.merge(success_counts, total_counts, on='Launch Site')
        
        fig = px.pie(
            result_df,
            names='Launch Site',
            values='class',
            title='Launch Success Rate by Site',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
    else:
        # For specific site: Show success vs. failure
        site_data = spacex_data[spacex_data['Launch Site'] == selected_site]
        outcomes = site_data['class'].value_counts().reset_index()
        outcomes.columns = ['Outcome', 'Count']
        outcomes['Outcome'] = outcomes['Outcome'].map({1: "Success", 0: "Failure"})
        
        fig = px.pie(
            outcomes,
            names='Outcome',
            values='Count',
            title=f'Launch Outcomes for {selected_site}',
            color='Outcome',
            color_discrete_map={'Success': '#2ECC71', 'Failure': '#E74C3C'}
        )
    
    fig.update_layout(
        legend_title_text='',
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    
    return fig

# Callback for updating the payload-success correlation chart
@dashboard.callback(
    Output('payload-success-correlation', 'figure'),
    [Input('launch-site-selector', 'value'),
     Input('payload-range-slider', 'value')]
)
def update_correlation_chart(selected_site, payload_range):
    # Filter by payload range
    filtered_data = spacex_data[
        (spacex_data['Payload Mass (kg)'] >= payload_range[0]) &
        (spacex_data['Payload Mass (kg)'] <= payload_range[1])
    ]
    
    # Apply site filter if specific site selected
    if selected_site != 'ALL':
        filtered_data = filtered_data[filtered_data['Launch Site'] == selected_site]
    
    # Map class to text for better readability
    filtered_data['Outcome'] = filtered_data['class'].map({1: "Success", 0: "Failure"})
    
    # Create scatter plot
    fig = px.scatter(
        filtered_data,
        x='Payload Mass (kg)',
        y='Outcome',
        color='Booster Version Category',
        title=f'Payload Mass vs. Launch Outcome ({payload_range[0]}-{payload_range[1]} kg)',
        hover_data=['Launch Site', 'Payload Mass (kg)', 'Booster Version'],
        opacity=0.8,
        size_max=15
    )
    
    fig.update_layout(
        yaxis=dict(
            tickmode='array',
            tickvals=[0, 1],
            ticktext=["Failure", "Success"]
        ),
        xaxis_title="Payload Mass (kg)",
        yaxis_title="Launch Outcome",
        legend_title="Booster Version",
        plot_bgcolor='rgba(240, 240, 240, 0.5)'
    )
    
    return fig

# Run application
if __name__ == '__main__':
    dashboard.run_server(debug=True)