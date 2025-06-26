# components/layout.py
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

def create_neuronal_metric_cards():
    """
    Create clickable metric cards for the neuronal activity dashboard
    """
    card_style = {
        'textAlign': 'center',
        'padding': '20px',
        'margin': '10px',
        'border': '2px solid #dee2e6',
        'borderRadius': '10px',
        'backgroundColor': '#f8f9fa',
        'cursor': 'pointer',
        'transition': 'all 0.3s ease',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
    }
    
    hover_style = {
        'borderColor': '#007bff',
        'backgroundColor': '#e3f2fd',
        'transform': 'translateY(-2px)',
        'boxShadow': '0 4px 8px rgba(0,0,0,0.2)'
    }
    
    cards = [
        dbc.Card([
            dbc.CardBody([
                html.H4("Mean Firing Rate", className="card-title", style={'color': '#007bff'}),
                html.P("Click to view detailed analysis", className="card-text"),
                html.I(className="fas fa-chart-line fa-2x", style={'color': '#007bff'})
            ])
        ], id="mean-firing-rate-card", style=card_style, className="metric-card"),
        
        dbc.Card([
            dbc.CardBody([
                html.H4("Active Electrodes", className="card-title", style={'color': '#28a745'}),
                html.P("Click to view detailed analysis", className="card-text"),
                html.I(className="fas fa-circle-nodes fa-2x", style={'color': '#28a745'})
            ])
        ], id="active-electrodes-card", style=card_style, className="metric-card"),
        
        dbc.Card([
            dbc.CardBody([
                html.H4("Burst Rate", className="card-title", style={'color': '#ffc107'}),
                html.P("Click to view detailed analysis", className="card-text"),
                html.I(className="fas fa-wave-square fa-2x", style={'color': '#ffc107'})
            ])
        ], id="burst-rate-card", style=card_style, className="metric-card"),
        
        dbc.Card([
            dbc.CardBody([
                html.H4("Network Bursts", className="card-title", style={'color': '#dc3545'}),
                html.P("Click to view detailed analysis", className="card-text"),
                html.I(className="fas fa-project-diagram fa-2x", style={'color': '#dc3545'})
            ])
        ], id="network-burst-card", style=card_style, className="metric-card"),
        
        dbc.Card([
            dbc.CardBody([
                html.H4("ISI Within Bursts", className="card-title", style={'color': '#6f42c1'}),
                html.P("Click to view detailed analysis", className="card-text"),
                html.I(className="fas fa-stopwatch fa-2x", style={'color': '#6f42c1'})
            ])
        ], id="isi-within-burst-card", style=card_style, className="metric-card"),
        
        dbc.Card([
            dbc.CardBody([
                html.H4("ISI Outside Bursts", className="card-title", style={'color': '#fd7e14'}),
                html.P("Click to view detailed analysis", className="card-text"),
                html.I(className="fas fa-clock fa-2x", style={'color': '#fd7e14'})
            ])
        ], id="isi-outside-burst-card", style=card_style, className="metric-card"),
        
        dbc.Card([
            dbc.CardBody([
                html.H4("Fraction in Bursts", className="card-title", style={'color': '#20c997'}),
                html.P("Click to view detailed analysis", className="card-text"),
                html.I(className="fas fa-percentage fa-2x", style={'color': '#20c997'})
            ])
        ], id="fraction-spikes-card", style=card_style, className="metric-card")
    ]
    
    return html.Div([
        html.H3("Neuronal Activity Metrics", style={'textAlign': 'center', 'marginBottom': '20px'}),
        dbc.Row([
            dbc.Col(card, width=12, md=6, lg=4) for card in cards
        ], className="g-3")
    ])

def create_plot_type_selector():
    """
    Create plot type selector component
    """
    return html.Div([
        html.Label("Plot Type:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
        dcc.RadioItems(
            id="neuronal-plot-type",
            options=[
                {'label': ' Violin Plot', 'value': 'violin'},
                {'label': ' Box Plot', 'value': 'box'},
                {'label': ' Bar Plot', 'value': 'bar'}
            ],
            value='violin',
            inline=True,
            style={'marginBottom': '15px'},
            labelStyle={'marginRight': '15px', 'cursor': 'pointer'}
        )
    ])

def create_network_plot_type_selector():
    """
    Create plot type selector for network metrics
    """
    return html.Div([
        html.Label("Plot Type:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
        dcc.RadioItems(
            id="network-plot-type",
            options=[
                {'label': ' Violin Plot', 'value': 'violin'},
                {'label': ' Box Plot', 'value': 'box'},
                {'label': ' Bar Plot', 'value': 'bar'}
            ],
            value='violin',
            inline=True,
            style={'marginBottom': '15px'},
            labelStyle={'marginRight': '15px', 'cursor': 'pointer'}
        )
    ])

def create_detailed_plot_container():
    """
    Create container for detailed metric plots
    """
    return html.Div([
        html.Div(id="neuronal-detail-title", children="Select a metric to view details", 
                style={'fontSize': '1.2em', 'fontWeight': 'bold', 'marginBottom': '10px'}),
        dcc.Graph(id="neuronal-detail-plot", style={'height': '600px'})
    ])

def create_filter_controls():
    """
    Create filter controls for groups and DIVs
    """
    return html.Div([
        html.Div([
            html.Label("Select Groups:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
            dcc.Dropdown(
                id="neuronal-group-filter",
                placeholder="Select groups to display...",
                multi=True,
                style={'marginBottom': '15px'}
            )
        ]),
        
        html.Div([
            html.Label("Select DIVs:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
            dcc.Dropdown(
                id="neuronal-div-filter",
                placeholder="Select DIVs to display...",
                multi=True,
                style={'marginBottom': '15px'}
            )
        ])
    ])

# EXAMPLE OF HOW TO INTEGRATE INTO YOUR MAIN LAYOUT
def create_enhanced_neuronal_layout():
    """
    Enhanced neuronal activity layout with all necessary components
    """
    return html.Div([
        # Header
        html.Div([
            html.H2("MEA-NAP Neuronal Activity Analysis", 
                   style={'textAlign': 'center', 'color': '#2C3E50', 'marginBottom': '30px'})
        ]),
        
        # Control panel
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        create_plot_type_selector()
                    ], width=12, md=4),
                    dbc.Col([
                        create_filter_controls()
                    ], width=12, md=8)
                ])
            ])
        ], style={'marginBottom': '20px'}),
        
        # Metric cards
        create_neuronal_metric_cards(),
        
        html.Hr(),
        
        # Detailed plot area
        dbc.Card([
            dbc.CardBody([
                create_detailed_plot_container()
            ])
        ], style={'marginTop': '20px'}),
        
        html.Hr(),
        
        # Standard plots (existing functionality)
        dbc.Tabs([
            dbc.Tab(label="Electrode-Level by Group", tab_id="electrode-group"),
            dbc.Tab(label="Electrode-Level by Age", tab_id="electrode-age"),
            dbc.Tab(label="Recording-Level by Group", tab_id="recording-group"),
            dbc.Tab(label="Recording-Level by Age", tab_id="recording-age"),
        ], id="neuronal-tabs", active_tab="electrode-group"),
        
        html.Div(id="neuronal-tab-content")
    ])

# CALLBACK TO POPULATE FILTER OPTIONS
def create_filter_population_callback(app):
    """
    Callback to populate filter dropdown options based on loaded data
    """
    @app.callback(
        [Output("neuronal-group-filter", "options"),
         Output("neuronal-div-filter", "options")],
        [Input("data-loaded-trigger", "children")]  # Trigger when data is loaded
    )
    def populate_filter_options(trigger):
        if not hasattr(app, 'data') or 'neuronal' not in app.data:
            return [], []
        
        neuronal_data = app.data['neuronal']
        
        # Group options
        group_options = [{'label': group, 'value': group} for group in neuronal_data.get('groups', [])]
        
        # DIV options
        div_options = [{'label': f'DIV {div}', 'value': div} for div in sorted(neuronal_data.get('divs', []))]
        
        return group_options, div_options

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
                        
                        # DIV selection (FIXED: Removed duplicate)
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

                        # Plot type selection
                        html.Div([
                            html.Label('Plot Type:', style={'fontWeight': 'bold'}),
                            dcc.RadioItems(
                                id='neuronal-plot-type',
                                options=[
                                    {'label': ' Violin Plot', 'value': 'violin'},
                                    {'label': ' Box Plot', 'value': 'box'},
                                    {'label': ' Bar Plot', 'value': 'bar'}
                                ],
                                value='violin',
                                inline=True,
                                style={'marginBottom': '15px'},
                                labelStyle={'marginRight': '15px', 'cursor': 'pointer'}
                            )
                        ], style={'marginBottom': '20px'}),
                        
                        # Neuronal Node By Group metrics dropdown
                        html.Div([
                            html.Label('Metric:', style={'fontWeight': 'bold'}),
                            dcc.Dropdown(
                                id='neuronal-node-group-metric',
                                options=[
                                    {'label': 'Mean Firing Rate Node By Group', 'value': 'FR'},
                                    {'label': 'Mean Firing Rate Active Node By Group', 'value': 'FRActive'},
                                    {'label': 'Unit Burst Rate (per minute) by Group', 'value': 'channelBurstRate'},
                                    {'label': 'Unit within Burst Firing Rate by Group', 'value': 'channelFRinBurst'},
                                    {'label': 'Unit Burst Duration by Group', 'value': 'channelBurstDur'},
                                    {'label': 'Unit ISI within Burst by Group', 'value': 'channelISIwithinBurst'},
                                    {'label': 'Unit ISI outside Burst by Group', 'value': 'channeISIoutsideBurst'},
                                    {'label': 'Unit fraction for spikes in bursts by Group', 'value': 'channelFracSpikesInBursts'}
                                ],
                                value='FR',
                                placeholder="Select metric..."
                            )
                        ], id='neuronal-node-group-dropdown', style={'marginBottom': '15px'}),

                        # Neuronal Node By Age metrics dropdown  
                        html.Div([
                            html.Label('Metric:', style={'fontWeight': 'bold'}),
                            dcc.Dropdown(
                                id='neuronal-node-age-metric',
                                options=[
                                    {'label': 'Mean Firing Rate', 'value': 'FR'},
                                    {'label': 'Mean Firing Rate Active Node', 'value': 'FRActive'},
                                    {'label': 'Unit Burst Rate (per minute)', 'value': 'channelBurstRate'}, 
                                    {'label': 'Unit within Burst Firing Rate', 'value': 'channelFRinBurst'},
                                    {'label': 'Unit Burst Duration', 'value': 'channelBurstDur'},
                                    {'label': 'Unit ISI within Burst', 'value': 'channelISIwithinBurst'},
                                    {'label': 'Unit ISI outside Burst', 'value': 'channeISIoutsideBurst'},
                                    {'label': 'Unit fraction of spikes in bursts', 'value': 'channelFracSpikesInBursts'}
                                ],
                                value='FR',
                                placeholder="Select metric..."
                            )
                        ], id='neuronal-node-age-dropdown', style={'marginBottom': '15px'}),

                        # Neuronal Recording By Group metrics dropdown
                        html.Div([
                            html.Label('Metric:', style={'fontWeight': 'bold'}),
                            dcc.Dropdown(
                                id='neuronal-recording-group-metric',
                                options=[
                                    {'label': 'Number of Active Electrodes by Group', 'value': 'numActiveElec'},
                                    {'label': 'Mean Firing Rate (Hz) by Group', 'value': 'FRmean'},
                                    {'label': 'Median Firing Rate (Hz) by Group', 'value': 'FRmedian'},
                                    {'label': 'Network Burst Rate (per min) by Group', 'value': 'NBurstRate'},
                                    {'label': 'Mean Number of Channels involved in network Bursts by Group', 'value': 'meanNumChansInvolvedInNbursts'},
                                    {'label': 'Mean Network Burst Length (s) by Group', 'value': 'meanNBstLengthS'},
                                    {'label': 'Mean ISI within Network Burst (ms)', 'value': 'meanISIWithinNbursts_ms'},
                                    {'label': 'Mean ISI outside network bursts (ms)', 'value': 'meanISIoutsideNbursts_ms'},
                                    {'label': 'Coefficient of variation of inter network burst intervals by Group', 'value': 'CVofINBI'},
                                    {'label': 'Fraction of Bursts in network Bursts by Group', 'value': 'fracInNburst'},
                                    {'label': 'Single electrode burst rate (per minute) by Group', 'value': 'singleElecBurstRate'},
                                    {'label': 'Single electrode average burst duration (ms) by Group', 'value': 'singleElecBurstDur'},
                                    {'label': 'Single electrode average ISI within burst(ms) by Group', 'value': 'singleElecISIwithinBurst'},
                                    {'label': 'Single electrode average ISI outside burst (ms) by Group', 'value': 'singleElecISIoutsideBurst'},
                                    {'label': 'Mean fraction of spikes in bursts per electrode by Group', 'value': 'meanFracSpikesInBurstsPerElec'}
                                ],
                                value='numActiveElec',
                                placeholder="Select metric..."
                            )
                        ], id='neuronal-recording-group-dropdown', style={'marginBottom': '15px'}),

                        # Neuronal Recording By Age metrics dropdown
                        html.Div([
                            html.Label('Metric:', style={'fontWeight': 'bold'}),
                            dcc.Dropdown(
                                id='neuronal-recording-age-metric',
                                options=[
                                    {'label': 'Number of Active Electrodes by Age', 'value': 'numActiveElec'},
                                    {'label': 'Mean Firing Rate (Hz) by Age', 'value': 'FRmean'},
                                    {'label': 'Median Firing Rate (Hz) by Age', 'value': 'FRmedian'},
                                    {'label': 'Network Burst Rate (per min) by Age', 'value': 'NBurstRate'},
                                    {'label': 'Mean Number of Channels involved in network Bursts by Age', 'value': 'meanNumChansInvolvedInNbursts'},
                                    {'label': 'Mean Network Burst Length (s) by Age', 'value': 'meanNBstLengthS'},
                                    {'label': 'Mean ISI within Network Burst (ms)', 'value': 'meanISIWithinNbursts_ms'},
                                    {'label': 'Mean ISI outside network bursts (ms)', 'value': 'meanISIoutsideNbursts_ms'},
                                    {'label': 'Coefficient of variation of inter network burst intervals by Age', 'value': 'CVofINBI'},
                                    {'label': 'Fraction of Bursts in network Bursts by Age', 'value': 'fracInNburst'},
                                    {'label': 'Single electrode burst rate (per minute) by Age', 'value': 'singleElecBurstRate'},
                                    {'label': 'Single electrode average burst duration (ms) by Age', 'value': 'singleElecBurstDur'},
                                    {'label': 'Single electrode average ISI within burst(ms) by Age', 'value': 'singleElecISIwithinBurst'},
                                    {'label': 'Single electrode average ISI outside burst (ms) by Age', 'value': 'singleElecISIoutsideBurst'},
                                    {'label': 'Mean fraction of spikes in bursts per electrode by Age', 'value': 'meanFracSpikesInBurstsPerElec'}
                                ],
                                value='numActiveElec',
                                placeholder="Select metric..."
                            )
                        ], id='neuronal-recording-age-dropdown', style={'marginBottom': '15px'}),
                        
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
                        # Main visualization graph (ADDED: was missing)
                        dcc.Graph(
                            id='visualization-graph',
                            config={
                                'displayModeBar': True,
                                'displaylogo': False,
                                'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
                                'toImageButtonOptions': {
                                    'format': 'svg',
                                    'filename': 'mea_nap_visualization',
                                    'height': 600,
                                    'width': 800,
                                    'scale': 1
                                }
                            },
                            style={'height': '600px', 'marginBottom': '20px'}
                        ),
                        
                        # Plot containers for different tabs
                        html.Div([
                            # Node By Group Plot
                            html.Div([
                                dcc.Graph(
                                    id='neuronal-node-group-plot',
                                    config={
                                        'displayModeBar': True,
                                        'displaylogo': False,
                                        'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
                                        'toImageButtonOptions': {
                                            'format': 'svg',
                                            'filename': 'neuronal_node_by_group',
                                            'height': 600,
                                            'width': 800,
                                            'scale': 1
                                        }
                                    },
                                    style={'height': '600px'}
                                )
                            ], id='neuronal-node-group-container', style={'display': 'none'}),
                            
                            # Node By Age Plot  
                            html.Div([
                                dcc.Graph(
                                    id='neuronal-node-age-plot',
                                    config={
                                        'displayModeBar': True,
                                        'displaylogo': False,
                                        'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
                                        'toImageButtonOptions': {
                                            'format': 'svg',
                                            'filename': 'neuronal_node_by_age',
                                            'height': 600,
                                            'width': 800,
                                            'scale': 1
                                        }
                                    },
                                    style={'height': '600px'}
                                )
                            ], id='neuronal-node-age-container', style={'display': 'none'}),
                            
                            # Recording By Group Plot
                            html.Div([
                                dcc.Graph(
                                    id='neuronal-recording-group-plot',
                                    config={
                                        'displayModeBar': True,
                                        'displaylogo': False,
                                        'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
                                        'toImageButtonOptions': {
                                            'format': 'svg',
                                            'filename': 'neuronal_recording_by_group',
                                            'height': 600,
                                            'width': 800,
                                            'scale': 1
                                        }
                                    },
                                    style={'height': '600px'}
                                )
                            ], id='neuronal-recording-group-container', style={'display': 'none'}),
                            
                            # Recording By Age Plot
                            html.Div([
                                dcc.Graph(
                                    id='neuronal-recording-age-plot',
                                    config={
                                        'displayModeBar': True,
                                        'displaylogo': False,
                                        'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
                                        'toImageButtonOptions': {
                                            'format': 'svg',
                                            'filename': 'neuronal_recording_by_age',
                                            'height': 600,
                                            'width': 800,
                                            'scale': 1
                                        }
                                    },
                                    style={'height': '600px'}
                                )
                            ], id='neuronal-recording-age-container', style={'display': 'none'})
                        ], className='graph-wrapper'),
                        
                        # Export controls section
                        html.Div([
                            html.H5("Export Visualization", style={'marginBottom': '10px'}),
                            html.Div([
                                html.Button(
                                    "Export SVG", 
                                    id="export-svg-btn",
                                    className="btn btn-outline-primary",
                                    style={'marginRight': '10px', 'marginBottom': '5px'}
                                ),
                                html.Button(
                                    "Export PNG", 
                                    id="export-png-btn",
                                    className="btn btn-outline-secondary",
                                    style={'marginRight': '10px', 'marginBottom': '5px'}
                                ),
                                html.Button(
                                    "Export PDF", 
                                    id="export-pdf-btn",
                                    className="btn btn-outline-success",
                                    style={'marginRight': '10px', 'marginBottom': '5px'}
                                ),
                            ], style={'display': 'flex', 'flexWrap': 'wrap'}),
                            
                            # Filename input
                            html.Div([
                                html.Label("Filename (optional):", style={'fontSize': '12px', 'marginRight': '10px'}),
                                dcc.Input(
                                    id='export-filename-input',
                                    type='text',
                                    placeholder='Enter custom filename...',
                                    style={'width': '200px', 'marginRight': '10px'}
                                ),
                            ], style={'marginTop': '10px', 'alignItems': 'center', 'display': 'flex'}),
                            
                            # Export status
                            html.Div(id="export-status", style={'marginTop': '10px', 'fontSize': '12px'}),
                            
                            # Download component
                            dcc.Download(id="download-visualization"),
                            
                        ], style={
                            'border': '1px solid #ddd',
                            'borderRadius': '5px',
                            'padding': '15px',
                            'marginTop': '20px',
                            'backgroundColor': '#f8f9fa'
                        }),
                        
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