# app.py - Merged Dashboard with Dashboard 1 UI + Dashboard 2 Functionality
import os
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
from flask import Flask

# Import Dashboard 2's robust data processing
from data_processing.data_loader import (scan_graph_data_folder, 
                                        load_neuronal_activity_data, 
                                        load_network_metrics_data,
                                        load_node_cartography_data,
                                        load_mat_file)

# Import Dashboard 1's beautiful layout
from components.layout import create_layout

# Import Dashboard 2's working visualization functions
from components.neuronal_activity import (
    create_half_violin_plot_by_group,
    create_half_violin_plot_by_age
)
from components.network_activity import (
    create_network_half_violin_plot_by_group,
    create_metrics_by_lag_plot,
    create_node_cartography_plot
)

# Create Flask server
server = Flask(__name__)

# Create assets folder if it doesn't exist
assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
os.makedirs(assets_dir, exist_ok=True)

# Initialize the app with Dashboard 1's configuration
app = dash.Dash(
    __name__,
    server=server,
    title="MEA-NAP Dashboard",
    suppress_callback_exceptions=True,
    assets_folder=assets_dir
)

# Initialize app with empty data structures for dynamic loading (Dashboard 1 style)
app.data = {
    'info': {'groups': [], 'divs': {}, 'lags': []},
    'neuronal': {'groups': [], 'divs': []},
    'network': {'groups': [], 'divs': [], 'lags': []},
    'cartography': {'groups': [], 'divs': [], 'lags': []},
    'loaded': False  # Track if data has been loaded
}

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
    [Output('metric-dropdown', 'options'),
     Output('metric-dropdown', 'value'),
     Output('lag-dropdown-container', 'style')],
    [Input('current-comparison-store', 'data')],
    prevent_initial_call=True
)
def update_metric_options(current_selection):
    """Update the metric dropdown based on the current activity and comparison tabs"""
    if not current_selection:
        return [], None, {'display': 'none'}
    
    activity = current_selection.get('activity')
    comparison = current_selection.get('comparison')
    
    if not activity or not comparison:
        return [], None, {'display': 'none'}
    
    # Get metrics based on activity and comparison (matching your file structure)
    if activity == 'neuronal':
        if comparison in ['nodebygroup', 'nodebyage']:
            # Electrode-level neuronal metrics (matching 1_NodeByGroup & 2_NodeByAge)
            metrics = [
                {'label': 'Mean Firing Rate Node', 'value': 'FR'},
                {'label': 'Mean Firing Rate Active Node', 'value': 'FR'},  # Note: same backend field
                {'label': 'Unit Burst Rate (per minute)', 'value': 'channelBurstRate'},
                {'label': 'Unit Within-Burst Firing Rate (Hz)', 'value': 'channelBurstRate'},  # Related metric
                {'label': 'Unit Burst Duration (ms)', 'value': 'channelBurstDur'},
                {'label': 'Unit ISI Within Burst (ms)', 'value': 'channelISIwithinBurst'},
                {'label': 'Unit ISI Outside Burst (ms)', 'value': 'channeISIoutsideBurst'},
                {'label': 'Unit Fraction of Spikes in Bursts', 'value': 'channelFracSpikesInBursts'}
            ]
            default_metric = 'FR'
            show_lag = False
        else:  # recordingsbygroup, recordingsbyage
            # Recording-level neuronal metrics (matching 3_RecordingsByGroup)
            metrics = [
                {'label': 'Number of Active Electrodes', 'value': 'numActiveElec'},
                {'label': 'Mean Firing Rate (Hz)', 'value': 'FRmean'},
                {'label': 'Median Firing Rate (Hz)', 'value': 'FRmedian'},
                {'label': 'Network Burst Rate (per minute)', 'value': 'NBurstRate'},
                {'label': 'Mean Number of Channels Involved in Network Bursts', 'value': 'meanNumChansInvolvedInNbursts'},
                {'label': 'Mean Network Burst Length (s)', 'value': 'meanNBstLengthS'},
                {'label': 'Mean ISI Within Network Burst (ms)', 'value': 'meanISIWithinNbursts_ms'},
                {'label': 'Mean ISI Outside Network Bursts (ms)', 'value': 'meanISIoutsideNbursts_ms'},
                {'label': 'Coefficient of Variation of Inter Network Burst Intervals', 'value': 'CVofINBI'},
                {'label': 'Fraction of Bursts in Network Bursts', 'value': 'fracInNburst'},
                {'label': 'Single-Electrode Burst Rate (per minute)', 'value': 'channelBurstRate'},
                {'label': 'Single-Electrode Average Burst Duration (ms)', 'value': 'channelBurstDur'},
                {'label': 'Single-Electrode Average ISI Within Burst (ms)', 'value': 'channelISIwithinBurst'},
                {'label': 'Single-Electrode Average ISI Outside Burst (ms)', 'value': 'channeISIoutsideBurst'},
                {'label': 'Mean Fraction of Spikes in Bursts per Electrode', 'value': 'channelFracSpikesInBursts'}
            ]
            default_metric = 'FRmean'
            show_lag = False
    else:  # network
        if comparison in ['nodebygroup', 'nodebyage']:
            # Node-level network metrics (Dashboard 2 MEA-NAP field names)
            metrics = [
                {'label': 'Node Degree', 'value': 'ND'},
                {'label': 'Node Strength', 'value': 'NS'},
                {'label': 'Betweenness Centrality', 'value': 'BC'},
                {'label': 'Local Efficiency', 'value': 'Eloc'},
                {'label': 'Participation Coefficient', 'value': 'PC'},
                {'label': 'Within-Module Z-Score', 'value': 'Z'}
            ]
            default_metric = 'ND'
            show_lag = True
        elif comparison in ['recordingsbygroup', 'recordingsbyage']:
            # Network-level metrics (Dashboard 2 MEA-NAP field names)
            metrics = [
                {'label': 'Network Density', 'value': 'Dens'},
                {'label': 'Global Efficiency', 'value': 'Eglob'},
                {'label': 'Modularity', 'value': 'Q'},
                {'label': 'Clustering Coefficient', 'value': 'CC'},
                {'label': 'Small-worldness Sigma', 'value': 'SW'}
            ]
            default_metric = 'Dens'
            show_lag = True
        elif comparison == 'graphmetricsbylag':
            metrics = [
                {'label': 'Network Density', 'value': 'Dens'},
                {'label': 'Global Efficiency', 'value': 'Eglob'},
                {'label': 'Modularity', 'value': 'Q'},
                {'label': 'Clustering Coefficient', 'value': 'CC'}
            ]
            default_metric = 'Dens'
            show_lag = False  # No lag dropdown for lag comparison
        elif comparison == 'nodecartography':
            metrics = []  # No metric selection for cartography
            default_metric = None
            show_lag = True
    
    # Show/hide lag dropdown
    lag_style = {'display': 'block' if show_lag else 'none', 'marginBottom': '15px'}
    
    return metrics, default_metric, lag_style

# Main visualization callback bridging Dashboard 1 UI with Dashboard 2 functionality
@app.callback(
    Output('visualization-graph', 'figure'),
    [Input('group-dropdown', 'value'),
     Input('div-dropdown', 'value'),
     Input('metric-dropdown', 'value'),
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
                return create_half_violin_plot_by_group(app.data['neuronal'], metric, title)
            elif comparison in ['nodebyage']:
                title = f"Electrode-Level {metric} by Age"
                return create_half_violin_plot_by_age(app.data['neuronal'], metric, title)
            elif comparison in ['recordingsbygroup']:
                title = f"Recording-Level {metric} by Group"
                return create_half_violin_plot_by_group(app.data['neuronal'], metric, title)
            elif comparison in ['recordingsbyage']:
                title = f"Recording-Level {metric} by Age"
                return create_half_violin_plot_by_age(app.data['neuronal'], metric, title)
                
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

# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=8050)