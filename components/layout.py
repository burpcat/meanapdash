# components/layout.py
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

def create_layout(app):
    """
    Create the main layout of the dashboard with dynamic data loading capability
    
    Parameters:
    -----------
    app : dash.Dash
        The Dash application instance
        
    Returns:
    --------
    html.Div
        The main layout div
    """
    
    # Create the layout with dynamic data loading support
    return html.Div([
        # Header
        html.Div([
            html.H1('MEA-NAP Dashboard', style={'margin': '0'}),
            html.P("Interactive visualization of Microelectrode Array data from the MEA-NAP pipeline",
                   style={'margin': '0 0 15px 0'})
        ], className='header'),
        
        # Main content container
        html.Div([
            # Data loading section
            html.Div([
                html.H3('Data Loading', style={'marginTop': '0', 'marginBottom': '15px'}),
                html.Div([
                    html.Label('GraphData Directory:', style={'fontWeight': 'bold', 'marginRight': '10px'}),
                    dcc.Input(
                        id='data-dir-input', 
                        type='text', 
                        placeholder='/path/to/your/GraphData/folder',
                        value='',
                        className='data-input',
                        style={
                            'width': '500px',
                            'padding': '8px',
                            'marginRight': '10px',
                            'border': '1px solid #ccc',
                            'borderRadius': '4px'
                        }
                    ),
                    html.Button(
                        'Load Data', 
                        id='load-data-button',
                        n_clicks=0,
                        className='load-button',
                        style={
                            'padding': '8px 16px',
                            'backgroundColor': '#007bff',
                            'color': 'white',
                            'border': 'none',
                            'borderRadius': '4px',
                            'cursor': 'pointer'
                        }
                    )
                ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),
                
                # Status message
                html.Div(
                    id='status-message',
                    style={'minHeight': '25px'},
                    className=''
                )
            ], className='filter-container', style={'marginBottom': '20px'}),
            
            # Main dashboard content
            html.Div([
                # Tab organization
                html.Div([
                    # Main Tabs: Activity Type
                    dcc.Tabs(id='activity-tabs', value='neuronal', children=[
                        # Tab 1: Neuronal Activity
                        dcc.Tab(label='Neuronal Activity', value='neuronal', children=[
                            # Subtabs for Neuronal Activity
                            dcc.Tabs(id='neuronal-tabs', value='nodebygroup', children=[
                                dcc.Tab(label='Node By Group', value='nodebygroup'),
                                dcc.Tab(label='Node By Age', value='nodebyage'),
                                dcc.Tab(label='Recordings By Group', value='recordingsbygroup'),
                                dcc.Tab(label='Recordings By Age', value='recordingsbyage')
                            ])
                        ]),
                        
                        # Tab 2: Network Activity
                        dcc.Tab(label='Network Activity', value='network', children=[
                            # Subtabs for Network Activity
                            dcc.Tabs(id='network-tabs', value='nodebygroup', children=[
                                dcc.Tab(label='Node By Group', value='nodebygroup'),
                                dcc.Tab(label='Node By Age', value='nodebyage'),
                                dcc.Tab(label='Recordings By Group', value='recordingsbygroup'),
                                dcc.Tab(label='Recordings By Age', value='recordingsbyage'),
                                dcc.Tab(label='Graph Metrics By Lag', value='graphmetricsbylag'),
                                dcc.Tab(label='Node Cartography', value='nodecartography')
                            ])
                        ])
                    ], className='tab-container')
                ], className='filter-container'),
                
                # Filters and visualization container
                html.Div([
                    # Left column - filters
                    html.Div([
                        html.H3('Filters', style={'marginTop': '0', 'marginBottom': '15px'}),
                        
                        # Group selection
                        html.Div([
                            html.Label('Groups:', style={'fontWeight': 'bold'}),
                            dcc.Dropdown(
                                id='group-dropdown',
                                options=[],  # Will be populated after data loading
                                value=[],
                                multi=True,
                                placeholder="Load data first..."
                            )
                        ], style={'marginBottom': '15px'}),
                        
                        # DIV selection
                        html.Div([
                            html.Label('DIVs:', style={'fontWeight': 'bold'}),
                            dcc.Dropdown(
                                id='div-dropdown',
                                options=[],  # Will be populated after data loading
                                value=[],
                                multi=True,
                                placeholder="Load data first..."
                            )
                        ], style={'marginBottom': '15px'}),
                        
                        # Metric selection
                        html.Div([
                            html.Label('Metric:', style={'fontWeight': 'bold'}),
                            dcc.Dropdown(
                                id='metric-dropdown',
                                options=[],
                                value=None,
                                placeholder="Select analysis type first..."
                            )
                        ], style={'marginBottom': '15px'}),
                        
                        # Lag selection (conditionally displayed)
                        html.Div([
                            html.Label('Lag (ms):', style={'fontWeight': 'bold'}),
                            dcc.Dropdown(
                                id='lag-dropdown',
                                options=[],  # Will be populated after data loading
                                value=None,
                                placeholder="Load data first..."
                            )
                        ], id='lag-dropdown-container', style={'marginBottom': '15px', 'display': 'none'}),
                        
                        # Visualization type
                        html.Div([
                            html.Label('Visualization:', style={'fontWeight': 'bold'}),
                            dcc.RadioItems(
                                id='viz-type',
                                options=[
                                    {'label': 'Half Violin Plot', 'value': 'violin'},
                                    {'label': 'Box Plot', 'value': 'box'},
                                    {'label': 'Bar Chart', 'value': 'bar'}
                                ],
                                value='violin',
                                labelStyle={'display': 'block', 'marginBottom': '5px'}
                            )
                        ], style={'marginBottom': '15px'}),
                        
                        # Data info panel (shows after data is loaded)
                        html.Div(
                            id='data-info-panel',
                            style={'display': 'none'}
                        )
                    ], className='filter-sidebar'),
                    
                    # Right column - visualization
                    html.Div([
                        html.Div([
                            dcc.Graph(
                                id='visualization-graph',
                                style={'height': '100%', 'width': '100%'},
                                config={'displayModeBar': True, 'responsive': True},
                                figure={
                                    'data': [],
                                    'layout': {
                                        'title': 'Load data and select analysis options to generate visualization',
                                        'plot_bgcolor': 'white',
                                        'paper_bgcolor': 'white',
                                        'height': 600,
                                        'font': {'size': 14}
                                    }
                                }
                            )
                        ], className='graph-wrapper')
                    ], className='visualization-container main-content')
                ], className='flex-container')
            ]),
            
            # Hidden stores for state management
            dcc.Store(id='data-loaded-store', data=False),
            dcc.Store(id='current-comparison-store'),
            dcc.Store(id='data-store')
        ], className='dashboard-container')
    ])


def create_data_info_panel(groups, divs, lags, experiments_count):
    """
    Create an informational panel showing loaded data statistics
    
    Parameters:
    -----------
    groups : list
        List of groups
    divs : list
        List of DIVs
    lags : list
        List of lag values
    experiments_count : int
        Total number of experiments
        
    Returns:
    --------
    html.Div
        Data info panel
    """
    return html.Div([
        html.H4('Loaded Data Summary', style={'marginTop': '20px', 'marginBottom': '10px'}),
        html.Ul([
            html.Li(f"Groups: {len(groups)} ({', '.join(groups)})"),
            html.Li(f"DIVs: {len(divs)} ({', '.join(map(str, divs))})"),
            html.Li(f"Lag values: {len(lags)} ({', '.join(map(str, lags))} ms)"),
            html.Li(f"Total experiments: {experiments_count}")
        ], style={
            'fontSize': '12px',
            'color': '#666',
            'paddingLeft': '15px'
        })
    ], style={
        'backgroundColor': '#f8f9fa',
        'padding': '15px',
        'borderRadius': '8px',
        'border': '1px solid #dee2e6',
        'marginTop': '20px'
    })


def get_default_example_paths():
    """
    Get list of common example paths for the data directory input
    
    Returns:
    --------
    list
        List of example paths
    """
    return [
        "/path/to/GraphData",
        "/Volumes/GDrive/MEA_work/combined_data/output/div5053rec2/GraphData",
        "C:\\Data\\MEA\\GraphData",
        "~/Documents/MEA_Data/GraphData"
    ]