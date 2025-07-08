# components/layout.py - REFACTORED VERSION - Clean and Modular
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

# =============================================================================
# DROPDOWN CONFIGURATIONS - Centralized and organized
# =============================================================================

# Neuronal Node-Level Metrics (Electrode-Level)
NEURONAL_NODE_METRICS = [
    {'label': 'Mean Firing Rate Node', 'value': 'FR'},
    {'label': 'Mean Firing Rate Active Node', 'value': 'FRActive'},
    {'label': 'Unit Burst Rate (per minute)', 'value': 'channelBurstRate'},
    {'label': 'Unit within Burst Firing Rate', 'value': 'channelFRinBurst'},
    {'label': 'Unit Burst Duration', 'value': 'channelBurstDur'},
    {'label': 'Unit ISI within Burst', 'value': 'channelISIwithinBurst'},
    {'label': 'Unit ISI outside Burst', 'value': 'channeISIoutsideBurst'},  # Note: typo preserved from MEA-NAP
    {'label': 'Unit fraction for spikes in bursts', 'value': 'channelFracSpikesInBursts'}
]

# Neuronal Recording-Level Metrics
NEURONAL_RECORDING_METRICS = [
    {'label': 'Number of Active Electrodes', 'value': 'numActiveElec'},
    {'label': 'Mean Firing Rate', 'value': 'FRmean'},
    {'label': 'Median Firing Rate', 'value': 'FRmedian'},
    {'label': 'Network Burst Rate (per min)', 'value': 'NBurstRate'},
    {'label': 'Mean Network Burst Length (s)', 'value': 'meanNBstLengthS'},
    {'label': 'Mean ISI within Network Bursts (ms)', 'value': 'meanISIWithinNbursts_ms'},
    {'label': 'Mean ISI outside Network Bursts (ms)', 'value': 'meanISIoutsideNbursts_ms'},
    {'label': 'CV of Inter-Network-Burst Intervals', 'value': 'CVofINBI'},
    {'label': 'Fraction of Spikes in Network Bursts', 'value': 'fracInNburst'},
    {'label': 'Mean Channels in Network Bursts', 'value': 'meanNumChansInvolvedInNbursts'},
    {'label': 'Single Electrode Burst Rate (per min)', 'value': 'singleElecBurstRate'},
    {'label': 'Single Electrode Burst Duration (ms)', 'value': 'singleElecBurstDur'},
    {'label': 'Single Electrode ISI within Burst (ms)', 'value': 'singleElecISIwithinBurst'},
    {'label': 'Single Electrode ISI outside Burst (ms)', 'value': 'singleElecISIoutsideBurst'},
    {'label': 'Mean Fraction Spikes in Bursts per Electrode', 'value': 'meanFracSpikesInBurstsPerElec'}
]

# Plot Type Options
PLOT_TYPE_OPTIONS = [
    {'label': ' Violin Plot', 'value': 'violin'},
    {'label': ' Box Plot', 'value': 'box'},
    {'label': ' Bar Plot', 'value': 'bar'}
]

# Visualization Type Options
VISUALIZATION_TYPE_OPTIONS = [
    {'label': 'Half Violin Plot', 'value': 'violin'},
    {'label': 'Box Plot', 'value': 'box'},
    {'label': 'Bar Chart', 'value': 'bar'}
]

# =============================================================================
# LAYOUT COMPONENTS - Modular component builders
# =============================================================================

def create_data_loading_section():
    """Create the data loading section"""
    return html.Div([
        html.H3('Data Loading', style={'marginTop': '0', 'marginBottom': '15px'}),
        html.Div([
            html.Label('ExperimentMatFiles Directory:', style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.Input(
                id='data-dir-input', 
                type='text', 
                placeholder='/path/to/your/MEA-NAP/output/folder',
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
    ], className='filter-container', style={'marginBottom': '20px'})

def create_tab_system():
    """Create the main tab system"""
    return html.Div([
        dcc.Tabs(id='activity-tabs', value='neuronal', children=[
            # Neuronal Activity Tab
            dcc.Tab(label='Neuronal Activity', value='neuronal', children=[
                dcc.Tabs(id='neuronal-tabs', value='nodebygroup', children=[
                    dcc.Tab(label='Node By Group', value='nodebygroup'),
                    dcc.Tab(label='Node By Age', value='nodebyage'),
                    dcc.Tab(label='Recordings By Group', value='recordingsbygroup'),
                    dcc.Tab(label='Recordings By Age', value='recordingsbyage')
                ])
            ]),
            
            # Network Activity Tab
            dcc.Tab(label='Network Activity', value='network', children=[
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
    ], className='filter-container')

def create_filter_sidebar():
    """Create the filter sidebar with all controls"""
    return html.Div([
        html.H3('Filters', style={'marginTop': '0', 'marginBottom': '15px'}),
        
        # Group selection
        html.Div([
            html.Label('Groups:', style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='group-dropdown',
                options=[],
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
                options=[],
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
                options=PLOT_TYPE_OPTIONS,
                value='violin',
                inline=True,
                style={'marginBottom': '15px'},
                labelStyle={'marginRight': '15px', 'cursor': 'pointer'}
            )
        ], style={'marginBottom': '20px'}),
        
        # Metric dropdown sections
        create_metric_dropdown_section('neuronal-node-group', 'Node By Group Metric:', NEURONAL_NODE_METRICS, 'FR'),
        create_metric_dropdown_section('neuronal-node-age', 'Node By Age Metric:', NEURONAL_NODE_METRICS, 'FR'),
        create_metric_dropdown_section('neuronal-recording-group', 'Recording By Group Metric:', NEURONAL_RECORDING_METRICS, 'numActiveElec'),
        create_metric_dropdown_section('neuronal-recording-age', 'Recording By Age Metric:', NEURONAL_RECORDING_METRICS, 'numActiveElec'),
        
        # Lag selection (for network metrics)
        html.Div([
            html.Label('Lag (ms):', style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='lag-dropdown',
                options=[],
                value=None,
                placeholder="Load data first..."
            )
        ], id='lag-dropdown-container', style={'marginBottom': '15px', 'display': 'none'}),
        
        # Visualization type
        html.Div([
            html.Label('Visualization:', style={'fontWeight': 'bold'}),
            dcc.RadioItems(
                id='viz-type',
                options=VISUALIZATION_TYPE_OPTIONS,
                value='violin',
                labelStyle={'display': 'block', 'marginBottom': '5px'}
            )
        ], style={'marginBottom': '15px'}),
        
        # Data info panel
        html.Div(
            id='data-info-panel',
            style={'display': 'none'}
        )
    ], className='filter-sidebar')

def create_metric_dropdown_section(dropdown_id, label, options, default_value):
    """Create a metric dropdown section"""
    return html.Div([
        html.Label(label, style={'fontWeight': 'bold'}),
        dcc.Dropdown(
            id=f'{dropdown_id}-metric',
            options=options,
            value=default_value,
            placeholder="Select metric..."
        )
    ], id=f'{dropdown_id}-dropdown', style={'marginBottom': '15px'})

def create_main_visualization_area():
    """Create the main visualization area"""
    return html.Div([
        # Main visualization graph
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
        
        # Individual plot containers (for separate tab plots)
        create_individual_plot_containers(),
        
        # Export controls
        create_export_controls()
        
    ], className='visualization-container main-content')

def create_individual_plot_containers():
    """Create individual plot containers for different tabs"""
    return html.Div([
        # Node By Group Plot
        html.Div([
            dcc.Graph(
                id='neuronal-node-group-plot',
                config=get_standard_graph_config('neuronal_node_by_group'),
                style={'height': '600px'}
            )
        ], id='neuronal-node-group-container', style={'display': 'none'}),
        
        # Node By Age Plot
        html.Div([
            dcc.Graph(
                id='neuronal-node-age-plot',
                config=get_standard_graph_config('neuronal_node_by_age'),
                style={'height': '600px'}
            )
        ], id='neuronal-node-age-container', style={'display': 'none'}),
        
        # Recording By Group Plot
        html.Div([
            dcc.Graph(
                id='neuronal-recording-group-plot',
                config=get_standard_graph_config('neuronal_recording_by_group'),
                style={'height': '600px'}
            )
        ], id='neuronal-recording-group-container', style={'display': 'none'}),
        
        # Recording By Age Plot
        html.Div([
            dcc.Graph(
                id='neuronal-recording-age-plot',
                config=get_standard_graph_config('neuronal_recording_by_age'),
                style={'height': '600px'}
            )
        ], id='neuronal-recording-age-container', style={'display': 'none'})
    ], className='graph-wrapper')

def get_standard_graph_config(filename_base):
    """Get standard graph configuration"""
    return {
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
        'toImageButtonOptions': {
            'format': 'svg',
            'filename': filename_base,
            'height': 600,
            'width': 800,
            'scale': 1
        }
    }

def create_export_controls():
    """Create export controls section"""
    return html.Div([
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
    })

def create_data_stores():
    """Create hidden data stores for state management"""
    return html.Div([
        dcc.Store(id='data-loaded-store', data=False),
        dcc.Store(id='current-comparison-store'),
        dcc.Store(id='data-store')
    ])

# =============================================================================
# MAIN LAYOUT CREATION FUNCTION
# =============================================================================

def create_layout(app):
    """
    Create the main layout of the dashboard - Clean and modular
    
    Args:
        app: The Dash application instance
        
    Returns:
        html.Div: The main layout div
    """
    
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
            create_data_loading_section(),
            
            # Tab system
            create_tab_system(),
            
            # Main dashboard content
            html.Div([
                # Filters and visualization container
                html.Div([
                    # Left sidebar - filters
                    create_filter_sidebar(),
                    
                    # Right area - visualization
                    create_main_visualization_area()
                ], className='flex-container')
            ]),

            # Hidden data stores
            create_data_stores()
        ], className='dashboard-container')
    ])

# =============================================================================
# UTILITY FUNCTIONS FOR LAYOUT CONFIGURATION
# =============================================================================

def get_neuronal_node_metrics():
    """Get neuronal node-level metric options"""
    return NEURONAL_NODE_METRICS

def get_neuronal_recording_metrics():
    """Get neuronal recording-level metric options"""
    return NEURONAL_RECORDING_METRICS

def get_plot_type_options():
    """Get plot type options"""
    return PLOT_TYPE_OPTIONS

def get_visualization_type_options():
    """Get visualization type options"""
    return VISUALIZATION_TYPE_OPTIONS

# =============================================================================
# METRIC VALIDATION FUNCTIONS
# =============================================================================

def validate_metric(metric, metric_type):
    """
    Validate that a metric is available for the given type
    
    Args:
        metric: The metric value to validate
        metric_type: 'node' or 'recording'
        
    Returns:
        bool: True if metric is valid, False otherwise
    """
    if metric_type == 'node':
        valid_metrics = [opt['value'] for opt in NEURONAL_NODE_METRICS]
    elif metric_type == 'recording':
        valid_metrics = [opt['value'] for opt in NEURONAL_RECORDING_METRICS]
    else:
        return False
    
    return metric in valid_metrics

def get_metric_label(metric):
    """
    Get the human-readable label for a metric
    
    Args:
        metric: The metric value
        
    Returns:
        str: Human-readable label
    """
    # Search in node metrics
    for opt in NEURONAL_NODE_METRICS:
        if opt['value'] == metric:
            return opt['label']
    
    # Search in recording metrics
    for opt in NEURONAL_RECORDING_METRICS:
        if opt['value'] == metric:
            return opt['label']
    
    return metric  # Return original if not found