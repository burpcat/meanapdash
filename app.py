import os
import base64
from datetime import datetime
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc  # MISSING IMPORT - needed for dbc.Card, dbc.Row, etc.
import plotly.graph_objects as go
from flask import Flask
from components.layout import create_layout
from data_processing.data_loader import (scan_graph_data_folder, 
                                        load_neuronal_activity_data, 
                                        load_network_metrics_data,
                                        load_node_cartography_data,
                                        load_mat_file)


from components.neuronal_activity import (
    create_half_violin_plot_by_group,
    create_half_violin_plot_by_age
)
from components.network_activity import (
    create_network_half_violin_plot_by_group,
    create_metrics_by_lag_plot,
    create_node_cartography_plot
)

server = Flask(__name__)
assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
os.makedirs(assets_dir, exist_ok=True)

# Initialize the app with Dashboard 1's configuration
app = dash.Dash(
    __name__,
    server=server,
    title="MEA-NAP Dashboard",
    suppress_callback_exceptions=True,
    assets_folder=assets_dir,
    external_stylesheets=[dbc.themes.BOOTSTRAP]  # ADDED - needed for dbc components
)

# Initialize app with empty data structures for dynamic loading (Dashboard 1 style)
app.data = {
    'info': {'groups': [], 'divs': {}, 'lags': []},
    'neuronal': {'groups': [], 'divs': []},
    'network': {'groups': [], 'divs': [], 'lags': []},
    'cartography': {'groups': [], 'divs': [], 'lags': []},
    'loaded': False  # Track if data has been loaded
}

def create_neuronal_metric_cards():
    """
    Create clickable metric cards for the neuronal activity dashboard
    These are the cards your callbacks are expecting to receive clicks from
    """
    
    # Card styling
    card_style = {
        'textAlign': 'center',
        'padding': '20px',
        'margin': '10px',
        'border': '2px solid #dee2e6',
        'borderRadius': '10px',
        'backgroundColor': '#f8f9fa',
        'cursor': 'pointer',
        'transition': 'all 0.3s ease',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'minHeight': '140px'
    }
    
    # Individual cards - these IDs MUST match your callback inputs
    cards = [
        # Mean Firing Rate Card
        dbc.Card([
            dbc.CardBody([
                html.H4("Mean Firing Rate", className="card-title", 
                       style={'color': '#007bff', 'marginBottom': '10px'}),
                html.P("Recording-level average firing rate across all active electrodes", 
                      className="card-text", style={'fontSize': '12px'}),
                html.I(className="fas fa-chart-line fa-2x", style={'color': '#007bff'})
            ])
        ], id="mean-firing-rate-card", style=card_style, className="metric-card"),
        
        # Active Electrodes Card  
        dbc.Card([
            dbc.CardBody([
                html.H4("Active Electrodes", className="card-title", 
                       style={'color': '#28a745', 'marginBottom': '10px'}),
                html.P("Number of electrodes with significant activity", 
                      className="card-text", style={'fontSize': '12px'}),
                html.I(className="fas fa-circle-nodes fa-2x", style={'color': '#28a745'})
            ])
        ], id="active-electrodes-card", style=card_style, className="metric-card"),
        
        # Network Burst Rate Card
        dbc.Card([
            dbc.CardBody([
                html.H4("Network Burst Rate", className="card-title", 
                       style={'color': '#ffc107', 'marginBottom': '10px'}),
                html.P("Frequency of network-wide bursting events", 
                      className="card-text", style={'fontSize': '12px'}),
                html.I(className="fas fa-wave-square fa-2x", style={'color': '#ffc107'})
            ])
        ], id="burst-rate-card", style=card_style, className="metric-card"),
        
        # Network Burst Length Card
        dbc.Card([
            dbc.CardBody([
                html.H4("Network Burst Length", className="card-title", 
                       style={'color': '#dc3545', 'marginBottom': '10px'}),
                html.P("Average duration of network burst events", 
                      className="card-text", style={'fontSize': '12px'}),
                html.I(className="fas fa-stopwatch fa-2x", style={'color': '#dc3545'})
            ])
        ], id="network-burst-card", style=card_style, className="metric-card"),
        
        # ISI Within Bursts Card
        dbc.Card([
            dbc.CardBody([
                html.H4("ISI Within Bursts", className="card-title", 
                       style={'color': '#6f42c1', 'marginBottom': '10px'}),
                html.P("Inter-spike interval during burst periods", 
                      className="card-text", style={'fontSize': '12px'}),
                html.I(className="fas fa-clock fa-2x", style={'color': '#6f42c1'})
            ])
        ], id="isi-within-burst-card", style=card_style, className="metric-card"),
        
        # ISI Outside Bursts Card
        dbc.Card([
            dbc.CardBody([
                html.H4("ISI Outside Bursts", className="card-title", 
                       style={'color': '#fd7e14', 'marginBottom': '10px'}),
                html.P("Inter-spike interval during non-burst periods", 
                      className="card-text", style={'fontSize': '12px'}),
                html.I(className="fas fa-history fa-2x", style={'color': '#fd7e14'})
            ])
        ], id="isi-outside-burst-card", style=card_style, className="metric-card"),
        
        # Fraction Spikes in Bursts Card
        dbc.Card([
            dbc.CardBody([
                html.H4("Fraction in Bursts", className="card-title", 
                       style={'color': '#20c997', 'marginBottom': '10px'}),
                html.P("Proportion of spikes occurring during bursts", 
                      className="card-text", style={'fontSize': '12px'}),
                html.I(className="fas fa-percentage fa-2x", style={'color': '#20c997'})
            ])
        ], id="fraction-spikes-card", style=card_style, className="metric-card")
    ]
    
    # Return the cards in a responsive grid
    return html.Div([
        html.H3("📊 Click on a Metric for Detailed Analysis", 
               style={'textAlign': 'center', 'marginBottom': '20px', 'color': '#2C3E50'}),
        dbc.Row([
            dbc.Col(card, width=12, md=6, lg=4) for card in cards
        ], className="g-3")  # g-3 adds gap between cards
    ])

def create_network_tab_content():
    """Placeholder for network tab content"""
    return html.Div([
        html.H3("Network Analysis"),
        html.P("Network analysis content will be added here...")
    ])

def create_cartography_tab_content():
    """Placeholder for cartography tab content"""
    return html.Div([
        html.H3("Node Cartography"),
        html.P("Node cartography content will be added here...")
    ])

def create_neuronal_tab_content():
    """Create the enhanced neuronal activity tab content"""
    return html.Div([
        # Hidden data stores - IMPORTANT: Add these for state management
        html.Div([
            dcc.Store(id="selected-metric-store", data=None),
        ], style={'display': 'none'}),
        
        # Control panel
        dbc.Card([
            dbc.CardHeader([
                html.H4([
                    html.I(className="fas fa-cogs", style={'marginRight': '10px'}),
                    "Analysis Controls"
                ], style={'margin': '0'})
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("📈 Plot Type:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                        dcc.RadioItems(
                            id="neuronal-plot-type",
                            options=[
                                {'label': ' 🎻 Violin Plot', 'value': 'violin'},
                                {'label': ' 📦 Box Plot', 'value': 'box'},
                                {'label': ' 📊 Bar Plot', 'value': 'bar'}
                            ],
                            value='violin',
                            inline=True,
                            labelStyle={'marginRight': '15px', 'cursor': 'pointer'}
                        )
                    ], width=12, md=4),
                    dbc.Col([
                        html.Label("🏷️ Select Groups:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                        dcc.Dropdown(
                            id="neuronal-group-filter",
                            placeholder="Select groups to display...",
                            multi=True
                        )
                    ], width=12, md=4),
                    dbc.Col([
                        html.Label("📅 Select DIVs:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                        dcc.Dropdown(
                            id="neuronal-div-filter",
                            placeholder="Select DIVs to display...",
                            multi=True
                        )
                    ], width=12, md=4)
                ])
            ])
        ], style={'marginBottom': '20px'}),
        
        # Clickable metric cards
        create_neuronal_metric_cards(),
        
        html.Hr(),
        
        # Detailed plot area
        dbc.Card([
            dbc.CardHeader([
                html.H4([
                    html.I(className="fas fa-chart-area", style={'marginRight': '10px'}),
                    html.Span(id="neuronal-detail-title", children="Select a metric card above to view detailed analysis")
                ], style={'margin': '0', 'color': '#2C3E50'})
            ]),
            dbc.CardBody([
                dcc.Graph(
                    id="neuronal-detail-plot",
                    style={'height': '600px'},
                    config={'displayModeBar': True, 'displaylogo': False}
                )
            ])
        ], style={'marginBottom': '20px'}),
        
        html.Hr(),
        
        # Traditional dropdown-based plots (your existing functionality)
        html.H3("🔧 Traditional Analysis Views", style={'marginTop': '30px', 'marginBottom': '20px', 'color': '#6c757d'}),
        dbc.Tabs([
            dbc.Tab(label="Electrode-Level by Group", tab_id="electrode-group"),
            dbc.Tab(label="Electrode-Level by Age", tab_id="electrode-age"),
            dbc.Tab(label="Recording-Level by Group", tab_id="recording-group"),
            dbc.Tab(label="Recording-Level by Age", tab_id="recording-age"),
        ], id="neuronal-subtabs", active_tab="electrode-group"),
        
        html.Div(id="neuronal-subtab-content", children=[
            html.P("Your existing dropdown-based plots will continue to work here.", 
                   style={'color': '#6c757d', 'fontStyle': 'italic', 'textAlign': 'center', 'marginTop': '20px'})
        ])
    ])

# Create app layout using Dashboard 1's beautiful UI
app.layout = create_layout(app)

# Dashboard 1's dynamic data loading callback with Dashboard 2's robust data processing
@app.callback(
    [Output('data-dir-input', 'disabled'),
     Output('load-data-button', 'children'),
     Output('load-data-button', 'disabled'),
     Output('status-message', 'children'),
     Output('status-message', 'className'),
     Output('data-loaded-store', 'data')],
    [Input('load-data-button', 'n_clicks')],
    [State('data-dir-input', 'value')],
    prevent_initial_call=True
)
def load_data_dynamically(n_clicks, data_dir):
    """Load data dynamically using Dashboard 2's robust data processing"""
    if n_clicks is None or not data_dir:
        return False, 'Load Data', False, '', '', False
    
    # Validate directory exists
    if not os.path.exists(data_dir):
        return (
            False, 'Load Data', False,
            f"Error: Directory '{data_dir}' does not exist.",
            'status-error', False
        )
    
    try:
        print(f"Loading data from: {data_dir}")
        
        # Use Dashboard 2's robust data scanning
        print("Scanning GraphData folder...")
        data_info = scan_graph_data_folder(data_dir)
        print(f"Found {len(data_info['groups'])} groups, {sum(len(exps) for exps in data_info['experiments'].values())} experiments, and {len(data_info['lags'])} lag values")
        
        # Use Dashboard 2's robust data loading functions
        print("Loading neuronal activity data...")
        neuronal_data = load_neuronal_activity_data(data_dir, data_info)
        
        print("Loading network metrics data...")
        network_data = load_network_metrics_data(data_dir, data_info)
        
        print("Loading node cartography data...")
        cartography_data = load_node_cartography_data(data_dir, data_info)
        
        # Store data in app context (Dashboard 2 style)
        app.data = {
            'info': data_info,
            'neuronal': neuronal_data,
            'network': network_data,
            'cartography': cartography_data,
            'loaded': True
        }
        
        # Create success message
        total_divs = len(set(div for group_divs in data_info['divs'].values() for div in group_divs.keys()))
        success_msg = (
            f"Data loaded successfully! "
            f"Found {len(data_info['groups'])} groups, "
            f"{total_divs} DIVs, and "
            f"{len(data_info['lags'])} lag values."
        )
        
        return (
            True, 'Data Loaded ✓', True,
            success_msg,
            'status-success',
            True
        )
        
    except Exception as e:
        print(f"Error loading data: {e}")
        import traceback
        traceback.print_exc()
        
        return (
            False, 'Load Data', False,
            f"Error loading data: {str(e)}",
            'status-error',
            False
        )

# Dashboard 1's dropdown update callback
@app.callback(
    [Output('group-dropdown', 'options'),
     Output('group-dropdown', 'value'),
     Output('div-dropdown', 'options'),
     Output('div-dropdown', 'value'),
     Output('lag-dropdown', 'options'),
     Output('lag-dropdown', 'value')],
    [Input('data-loaded-store', 'data')],
    prevent_initial_call=True
)
def update_dropdown_options(data_loaded):
    """Update dropdown options after data is loaded"""
    if not data_loaded or not app.data.get('loaded'):
        return [], None, [], None, [], None
    
    try:
        # Group options
        group_options = [{'label': group, 'value': group} for group in app.data['info']['groups']]
        default_groups = app.data['info']['groups'][:1] if app.data['info']['groups'] else []
        
        # DIV options
        all_divs = sorted(set(div for group_divs in app.data['info']['divs'].values() for div in group_divs.keys()))
        div_options = [{'label': f'DIV {div}', 'value': div} for div in all_divs]
        default_divs = all_divs[:1] if all_divs else []
        
        # Lag options
        lag_options = [{'label': f'{lag} ms', 'value': lag} for lag in app.data['info']['lags']]
        default_lag = app.data['info']['lags'][0] if app.data['info']['lags'] else None
        
        return (
            group_options, default_groups,
            div_options, default_divs,
            lag_options, default_lag
        )
        
    except Exception as e:
        print(f"Error updating dropdown options: {e}")
        return [], None, [], None, [], None

# Dashboard 1's data info panel callback
@app.callback(
    [Output('data-info-panel', 'children'),
     Output('data-info-panel', 'style')],
    [Input('data-loaded-store', 'data')],
    prevent_initial_call=True
)
def update_data_info_panel(data_loaded):
    """Update the data info panel after data is loaded"""
    if not data_loaded or not app.data.get('loaded'):
        return [], {'display': 'none'}
    
    try:
        # Get data statistics
        info = app.data['info']
        groups = info['groups']
        all_divs = sorted(set(div for group_divs in info['divs'].values() for div in group_divs.keys()))
        lags = info['lags']
        
        # Count total experiments
        total_experiments = sum(len(exps) for exps in info['experiments'].values())
        
        # Create info panel content
        panel_content = html.Div([
            html.H4('Loaded Data Summary', style={'marginTop': '0', 'marginBottom': '10px'}),
            html.Ul([
                html.Li(f"Groups: {len(groups)} ({', '.join(groups)})"),
                html.Li(f"DIVs: {len(all_divs)} ({', '.join(map(str, all_divs))})"),
                html.Li(f"Lag values: {len(lags)} ({', '.join(map(str, lags))} ms)"),
                html.Li(f"Total experiments: {total_experiments}")
            ], style={
                'fontSize': '12px',
                'color': '#666',
                'paddingLeft': '15px',
                'margin': '0'
            })
        ])
        
        return panel_content, {'display': 'block'}
        
    except Exception as e:
        print(f"Error updating data info panel: {e}")
        return [], {'display': 'none'}

# Dashboard 1's tab tracking callback
@app.callback(
    Output('current-comparison-store', 'data'),
    [Input('neuronal-tabs', 'value'),
     Input('network-tabs', 'value'),
     Input('activity-tabs', 'value')]
)
def store_current_comparison(neuronal_tab, network_tab, activity_tab):
    """Store the currently selected tab combination"""
    comparison_tab = neuronal_tab if activity_tab == 'neuronal' else network_tab
    return {
        'activity': activity_tab,
        'comparison': comparison_tab
    }

# Dashboard 1's metric options callback with Dashboard 2's metric definitions
@app.callback(
    [Output('lag-dropdown-container', 'style')],
    [Input('current-comparison-store', 'data')],
    prevent_initial_call=True
)
def update_metric_options(current_selection):
    """Update the metric dropdown based on the current activity and comparison tabs"""
    if not current_selection:
        return [{'display': 'none'}]
    
    activity = current_selection.get('activity')
    comparison = current_selection.get('comparison')
    
    if not activity or not comparison:
        return [{'display': 'none'}]
    
    # Get metrics based on activity and comparison (matching your file structure)
    if activity == 'neuronal':
        if comparison in ['nodebygroup', 'nodebyage']:
            # Electrode-level neuronal metrics (matching 1_NodeByGroup & 2_NodeByAge)
            show_lag = False
        else:  # recordingsbygroup, recordingsbyage
            # Recording-level neuronal metrics (matching 3_RecordingsByGroup)
            show_lag = False
    else:  # network
        if comparison in ['nodebygroup', 'nodebyage']:
            # Node-level network metrics (Dashboard 2 MEA-NAP field names)
            show_lag = True
        elif comparison in ['recordingsbygroup', 'recordingsbyage']:
            # Network-level metrics (Dashboard 2 MEA-NAP field names)
            show_lag = True
        elif comparison == 'graphmetricsbylag':
            show_lag = False  # No lag dropdown for lag comparison
        elif comparison == 'nodecartography':
            show_lag = True
    
    # Show/hide lag dropdown
    lag_style = {'display': 'block' if show_lag else 'none', 'marginBottom': '15px'}
    
    return [lag_style]

# Main visualization callback bridging Dashboard 1 UI with Dashboard 2 functionality
@app.callback(
    Output('visualization-graph', 'figure'),
    [Input('group-dropdown', 'value'),
     Input('div-dropdown', 'value'),
     Input('viz-type', 'value'),
     Input('lag-dropdown', 'value'),
     Input('current-comparison-store', 'data'),
     Input('data-loaded-store', 'data')],
    prevent_initial_call=True
)
def update_visualization(groups, selected_divs, metric, viz_type, lag, current_selection, data_loaded):
    """Generate visualizations using Dashboard 2's robust visualization functions"""
    
    # Check if data has been loaded
    if not data_loaded or not app.data.get('loaded'):
        return go.Figure().update_layout(
            title='Please load data first using the "Load Data" button above',
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=14)
        )
    
    # Check if we have groups and current selection
    if not groups or not current_selection:
        return go.Figure().update_layout(
            title='Please select at least one group',
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
    
    activity = current_selection.get('activity')
    comparison = current_selection.get('comparison')
    
    if not activity or not comparison:
        return go.Figure().update_layout(
            title='No activity or comparison type selected',
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
    
    try:
        # Route to appropriate Dashboard 2 visualization functions
        if comparison == 'nodecartography':
            # Node cartography visualization
            if not groups or not selected_divs:
                return go.Figure().update_layout(title='Please select group and DIV for node cartography')
            
            return create_node_cartography_plot(app.data['cartography'], groups[0], lag, selected_divs[0])
            
        elif comparison == 'graphmetricsbylag':
            # Metrics by lag visualization
            if not groups or not metric:
                return go.Figure().update_layout(title='Please select group and metric')
            
            return create_metrics_by_lag_plot(app.data['network'], groups[0], metric)
            
        elif activity == 'neuronal':
            # Neuronal activity visualizations using Dashboard 2's functions
            if comparison in ['nodebygroup']:
                title = f"Electrode-Level {metric} by Group"
                return create_half_violin_plot_by_group(app.data['neuronal'], metric, title, groups, selected_divs)
            elif comparison in ['nodebyage']:
                title = f"Electrode-Level {metric} by Age"
                return create_half_violin_plot_by_age(app.data['neuronal'], metric, title, groups, selected_divs)
            elif comparison in ['recordingsbygroup']:
                title = f"Recording-Level {metric} by Group"
                return create_half_violin_plot_by_group(app.data['neuronal'], metric, title, groups, selected_divs)
            elif comparison in ['recordingsbyage']:
                title = f"Recording-Level {metric} by Age"
                return create_half_violin_plot_by_age(app.data['neuronal'], metric, title, groups, selected_divs)
                
        elif activity == 'network':
            # Network activity visualizations using Dashboard 2's functions
            if comparison in ['nodebygroup']:
                title = f"Node-Level {metric} by Group (Lag {lag}ms)"
                return create_network_half_violin_plot_by_group(app.data['network'], metric, lag, title, level='node')
            elif comparison in ['nodebyage']:
                # For now, return placeholder - can implement later
                return go.Figure().update_layout(title="Node-Level Network Metrics by Age - Coming soon")
            elif comparison in ['recordingsbygroup']:
                title = f"Network-Level {metric} by Group"
                return create_network_half_violin_plot_by_group(app.data['network'], metric, lag, title, level='network')
            elif comparison in ['recordingsbyage']:
                # For now, return placeholder - can implement later
                return go.Figure().update_layout(title="Network-Level Metrics by Age - Coming soon")
        
        # Default fallback
        return go.Figure().update_layout(title="Visualization not yet implemented for this combination")
        
    except Exception as e:
        print(f"Error in visualization: {e}")
        import traceback
        traceback.print_exc()
        return go.Figure().update_layout(title=f'Error: {str(e)}')
    
# Export visualization callback
@app.callback(
    [Output("download-visualization", "data"), 
     Output("export-status", "children")],
    [Input("export-svg-btn", "n_clicks"),
     Input("export-png-btn", "n_clicks"),
     Input("export-pdf-btn", "n_clicks")],
    [State('visualization-graph', 'figure'),
     State('group-dropdown', 'value'),
     State('div-dropdown', 'value'),
     State('lag-dropdown', 'value'),
     State('current-comparison-store', 'data'),
     State('export-filename-input', 'value')],
    prevent_initial_call=True
)
def export_visualization(svg_clicks, png_clicks, pdf_clicks, figure, 
                        groups, selected_divs, metric, lag, current_selection, 
                        custom_filename):
    """Export the current visualization in the selected format"""
    
    # Determine which button was clicked
    ctx = dash.callback_context
    if not ctx.triggered:
        return None, ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Check if we have a figure to export
    if not figure or not figure.get('data'):
        return None, "No visualization to export. Please generate a plot first."
    
    # Determine export format
    if button_id == "export-svg-btn":
        export_format = "svg"
        mime_type = "image/svg+xml"
    elif button_id == "export-png-btn":
        export_format = "png"
        mime_type = "image/png"
    elif button_id == "export-pdf-btn":
        export_format = "pdf"
        mime_type = "application/pdf"
    else:
        return None, "Unknown export format"
    
    try:
        # Create plotly figure object
        fig = go.Figure(figure)
        
        # Optimize figure for export
        fig.update_layout(
            # Ensure good resolution and clean appearance
            font=dict(family="Arial, sans-serif", size=12),
            plot_bgcolor='white',
            paper_bgcolor='white',
            # Add some padding for better appearance
            margin=dict(l=60, r=60, t=80, b=60)
        )
        
        # Generate descriptive filename if none provided
        if not custom_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Build filename based on current selections
            filename_parts = ["MEA-NAP"]
            
            # Add activity type and comparison
            if current_selection:
                activity = current_selection.get('activity')
                comparison = current_selection.get('comparison')
                if activity:
                    filename_parts.append(activity)
                if comparison:
                    filename_parts.append(comparison)
            
            # Add groups
            if groups:
                if len(groups) == 1:
                    filename_parts.append(f"group-{groups[0]}")
                else:
                    filename_parts.append(f"{len(groups)}-groups")
            
            # Add DIVs
            if selected_divs:
                if len(selected_divs) == 1:
                    filename_parts.append(f"DIV{selected_divs[0]}")
                else:
                    filename_parts.append(f"{len(selected_divs)}-DIVs")
            
            # Add metric
            if metric:
                filename_parts.append(metric)
            
            # Add lag if applicable
            if lag and current_selection and current_selection.get('activity') == 'network':
                filename_parts.append(f"lag{lag}ms")
            
            # Add timestamp
            filename_parts.append(timestamp)
            
            filename = "_".join(filename_parts)
        else:
            filename = custom_filename
        
        # Add file extension
        filename = f"{filename}.{export_format}"
        
        # Export the figure
        if export_format == "svg":
            # Export as SVG
            svg_bytes = fig.to_image(format="svg", width=800, height=600, scale=1)
            return (
                dict(
                    content=svg_bytes.decode('utf-8'), 
                    filename=filename, 
                    type=mime_type
                ),
                f"✓ SVG exported successfully as {filename}"
            )
            
        elif export_format == "png":
            # Export as PNG with high quality
            png_bytes = fig.to_image(format="png", width=800, height=600, scale=2)
            png_b64 = base64.b64encode(png_bytes).decode()
            return (
                dict(
                    content=png_b64, 
                    filename=filename, 
                    base64=True
                ),
                f"✓ PNG exported successfully as {filename}"
            )
            
        elif export_format == "pdf":
            # Export as PDF
            pdf_bytes = fig.to_image(format="pdf", width=800, height=600)
            pdf_b64 = base64.b64encode(pdf_bytes).decode()
            return (
                dict(
                    content=pdf_b64, 
                    filename=filename, 
                    base64=True
                ),
                f"✓ PDF exported successfully as {filename}"
            )
    
    except Exception as e:
        error_msg = f"Export failed: {str(e)}"
        print(f"Export error: {e}")
        import traceback
        traceback.print_exc()
        return None, error_msg
    
    return None, ""


# Optional: Add a callback to clear export status after a delay
@app.callback(
    Output("export-status", "children", allow_duplicate=True),
    [Input("export-status", "children")],
    prevent_initial_call=True
)
def clear_export_status(status_message):
    """Clear export status message after a few seconds"""
    if status_message and "✓" in status_message:
        # Use a clientside callback or JavaScript to clear after delay
        # For now, just return the message (it will stay visible)
        return status_message
    return status_message

# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=8050)