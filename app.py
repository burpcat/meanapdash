import os
import base64
from datetime import datetime
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc 
import plotly.graph_objects as go
from flask import Flask
from components.layout import create_layout
import numpy as np

# UPDATED IMPORTS - Using ExperimentMatFiles loader
from data_processing.experiment_mat_loader import (
    scan_experiment_mat_folder, 
    load_neuronal_activity_from_experiment_files,
    load_all_experiment_data,
    convert_to_dashboard_format
)

# UTILS PACKAGE IMPORTS - New centralized approach
from utils import (
    process_metric,
    get_available_metrics,
    is_metric_available,
    get_metric_processor,
    get_metric_label,
    get_metric_title,
    get_metric_field_name,
    create_neuronal_visualization,
    validate_visualization_request,
    apply_mea_nap_styling,
    create_empty_plot,
    create_error_plot
)

# Keep existing visualization imports for backward compatibility
from components.neuronal_activity import (
    create_half_violin_plot_by_group,
    create_half_violin_plot_by_age
)
from components.network_activity import (
    create_network_half_violin_plot_by_group,
    create_metrics_by_lag_plot,
    create_node_cartography_plot
)

# Callback imports
from callbacks.network_callbacks import register_network_callbacks
from callbacks.neuronal_callbacks import register_neuronal_callbacks

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
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

# Initialize app with empty data structures for dynamic loading
app.data = {
    'info': {'groups': [], 'divs': {}, 'lags': [], 'experiments': {}},
    'neuronal': {'groups': [], 'divs': [], 'by_experiment': {}, 'by_group': {}},
    'network': {'groups': [], 'divs': [], 'lags': []},
    'cartography': {'groups': [], 'divs': [], 'lags': []},
    'loaded': False  # Track if data has been loaded
}

print("Registering callbacks...")
register_network_callbacks(app)
register_neuronal_callbacks(app)
print("Callbacks registered successfully!")

app.layout = create_layout(app)

# =============================================================================
# SIMPLIFIED NEURONAL VISUALIZATION FUNCTION - Now uses utils package
# =============================================================================

def create_neuronal_visualization_main(processed_data, metric, comparison, title, groups, selected_divs):
    """
    Main neuronal visualization function using utils package
    
    Args:
        processed_data: Data processed by metric-specific function
        metric: The metric name
        comparison: Type of comparison (nodebygroup, nodebyage, etc.)
        title: Plot title
        groups: Selected groups
        selected_divs: Selected DIVs
    
    Returns:
        Plotly figure
    """
    
    # Get the field name to use in the data
    field_name = get_metric_field_name(metric)
    
    # Route to appropriate visualization function
    if comparison in ['nodebygroup', 'recordingsbygroup']:
        return create_half_violin_plot_by_group(processed_data, field_name, title, groups, selected_divs)
    elif comparison in ['nodebyage', 'recordingsbyage']:
        return create_half_violin_plot_by_age(processed_data, field_name, title, groups, selected_divs)
    else:
        return create_error_plot(f"Unknown comparison type: {comparison}")

# =============================================================================
# MAIN CALLBACKS - Simplified and clean using utils
# =============================================================================

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
    """Load data dynamically using ExperimentMatFiles approach"""
    if n_clicks is None or not data_dir:
        return False, 'Load Data', False, '', '', False
    
    # Validate directory exists
    if not os.path.exists(data_dir):
        return (
            False, 'Load Data', False,
            f"Error: Directory '{data_dir}' does not exist.",
            'status-error', False
        )
    
    # Check for ExperimentMatFiles folder
    exp_mat_folder = os.path.join(data_dir, 'ExperimentMatFiles')
    if not os.path.exists(exp_mat_folder):
        return (
            False, 'Load Data', False,
            f"Error: ExperimentMatFiles folder not found in '{data_dir}'. Please provide the MEA-NAP output folder.",
            'status-error', False
        )
    
    try:
        print(f"🔄 Loading data from ExperimentMatFiles: {data_dir}")
        
        # Step 1: Scan ExperimentMatFiles folder
        print("📁 Scanning ExperimentMatFiles folder...")
        data_info = scan_experiment_mat_folder(data_dir)
        print(f"✅ Found {len(data_info['groups'])} groups, {sum(len(exps) for exps in data_info['experiments'].values())} experiments")
        
        # Step 2: Load neuronal activity data
        print("📊 Loading neuronal activity data...")
        neuronal_data = load_neuronal_activity_from_experiment_files(data_dir)
        
        # Step 3: Initialize network and cartography data (empty for now)
        print("🌐 Initializing network data structures...")
        network_data = {
            'groups': neuronal_data['groups'],
            'divs': neuronal_data['divs'],
            'lags': [],  # No network data in ExperimentMatFiles
            'by_group': {},
            'by_experiment': {}
        }
        
        cartography_data = {
            'groups': neuronal_data['groups'],
            'divs': neuronal_data['divs'],
            'lags': [],  # No cartography data in ExperimentMatFiles
            'by_group': {},
            'by_experiment': {}
        }
        
        # Step 4: Store data in app context
        app.data = {
            'info': data_info,
            'neuronal': neuronal_data,
            'network': network_data,
            'cartography': cartography_data,
            'loaded': True
        }
        
        # Step 5: Debug output
        print(f"\n🎯 DASHBOARD DATA LOADED SUCCESSFULLY!")
        print(f"   📊 Groups: {app.data['neuronal']['groups']}")
        print(f"   📊 DIVs: {app.data['neuronal']['divs']}")
        print(f"   📄 Experiments: {len(app.data['neuronal']['by_experiment'])}")
        
        # Create success message
        total_divs = len(app.data['neuronal']['divs'])
        success_msg = (
            f"✅ ExperimentMatFiles loaded successfully! "
            f"Found {len(data_info['groups'])} groups, "
            f"{total_divs} DIVs, and "
            f"{len(app.data['neuronal']['by_experiment'])} experiments."
        )
        
        return (
            True, 'Data Loaded ✓', True,
            success_msg,
            'status-success',
            True
        )
        
    except Exception as e:
        print(f"❌ Error loading ExperimentMatFiles: {e}")
        import traceback
        traceback.print_exc()
        
        return (
            False, 'Load Data', False,
            f"Error loading ExperimentMatFiles: {str(e)}",
            'status-error',
            False
        )

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
        group_options = [{'label': group, 'value': group} for group in app.data['neuronal']['groups']]
        default_groups = app.data['neuronal']['groups'][:1] if app.data['neuronal']['groups'] else []
        
        # DIV options
        div_options = [{'label': f'DIV {div}', 'value': div} for div in app.data['neuronal']['divs']]
        default_divs = app.data['neuronal']['divs'][:1] if app.data['neuronal']['divs'] else []
        
        # Lag options (empty for ExperimentMatFiles)
        lag_options = []
        default_lag = None
        
        print(f"🔄 Dropdown options updated:")
        print(f"   Groups: {[g['label'] for g in group_options]}")
        print(f"   DIVs: {[d['label'] for d in div_options]}")
        
        return (
            group_options, default_groups,
            div_options, default_divs,
            lag_options, default_lag
        )
        
    except Exception as e:
        print(f"❌ Error updating dropdown options: {e}")
        return [], None, [], None, [], None

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
        groups = app.data['neuronal']['groups']
        divs = app.data['neuronal']['divs']
        total_experiments = len(app.data['neuronal']['by_experiment'])
        
        # Create info panel content
        panel_content = html.Div([
            html.H4('Loaded Data Summary', style={'marginTop': '0', 'marginBottom': '10px'}),
            html.Ul([
                html.Li(f"Groups: {len(groups)} ({', '.join(groups)})"),
                html.Li(f"DIVs: {len(divs)} ({', '.join(map(str, divs))})"),
                html.Li(f"Total experiments: {total_experiments}"),
                html.Li(f"Data source: ExperimentMatFiles")
            ], style={
                'fontSize': '12px',
                'color': '#666',
                'paddingLeft': '15px',
                'margin': '0'
            })
        ])
        
        return panel_content, {'display': 'block'}
        
    except Exception as e:
        print(f"❌ Error updating data info panel: {e}")
        return [], {'display': 'none'}

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
    
    # Hide lag dropdown for ExperimentMatFiles (no network data)
    lag_style = {'display': 'none', 'marginBottom': '15px'}
    
    return [lag_style]

@app.callback(
    Output('visualization-graph', 'figure'),
    [Input('group-dropdown', 'value'),
     Input('div-dropdown', 'value'),
     Input('viz-type', 'value'),
     Input('lag-dropdown', 'value'),
     Input('current-comparison-store', 'data'),
     Input('data-loaded-store', 'data'),
     # Metric dropdown inputs
     Input('neuronal-node-group-metric', 'value'),
     Input('neuronal-recording-group-metric', 'value'),
     Input('neuronal-node-age-metric', 'value'),
     Input('neuronal-recording-age-metric', 'value')],
    prevent_initial_call=True
)
def update_visualization(groups, selected_divs, viz_type, lag, current_selection, data_loaded,
                        node_group_metric, recording_group_metric, node_age_metric, recording_age_metric):
    """REFACTORED visualization callback - now uses utils package"""
    
    # Check if data has been loaded
    if not data_loaded or not app.data.get('loaded'):
        return create_empty_plot('Please load data first using the "Load Data" button above')
    
    # Check if we have groups and current selection
    if not groups or not current_selection:
        return create_empty_plot('Please select at least one group')
    
    activity = current_selection.get('activity')
    comparison = current_selection.get('comparison')
    
    if not activity or not comparison:
        return create_empty_plot('No activity or comparison type selected')
    
    # DEBUG: Print what we're trying to visualize
    print(f"\n🎨 VISUALIZATION REQUEST:")
    print(f"   Activity: {activity}")
    print(f"   Comparison: {comparison}")
    print(f"   Groups: {groups}")
    print(f"   DIVs: {selected_divs}")
    
    # DYNAMIC METRIC SELECTION based on current tab
    metric = None
    if activity == 'neuronal':
        if comparison == 'nodebygroup':
            metric = node_group_metric or 'FR'
        elif comparison == 'recordingsbygroup':
            metric = recording_group_metric or 'numActiveElec'
        elif comparison == 'nodebyage':
            metric = node_age_metric or 'FR'
        elif comparison == 'recordingsbyage':
            metric = recording_age_metric or 'numActiveElec'
    
    # If no metric selected, use defaults
    if not metric:
        metric = 'FR'
    
    print(f"   Metric: {metric}")
    
    # VALIDATE VISUALIZATION REQUEST using utils
    validation = validate_visualization_request(metric, comparison, groups, selected_divs)
    if not validation['is_valid']:
        error_msg = '; '.join(validation['errors'])
        return create_error_plot(error_msg)
    
    try:
        # NEURONAL ACTIVITY HANDLING using utils package
        if activity == 'neuronal':
            # Check if we have a processor for this metric
            if not is_metric_available(metric):
                return create_error_plot(f'Metric "{metric}" not yet implemented')
            
            # Process the data using the utils package
            processed_data = process_metric(metric, app.data['neuronal'], groups, selected_divs)
            
            # Create the title using utils
            metric_title = get_metric_title(metric)
            
            if comparison in ['nodebygroup', 'recordingsbygroup']:
                title = f"{metric_title} by Group"
            elif comparison in ['nodebyage', 'recordingsbyage']:
                title = f"{metric_title} by Age"
            else:
                title = f"{metric_title}"
            
            # Create the visualization using the main function
            return create_neuronal_visualization_main(processed_data, metric, comparison, title, groups, selected_divs)
                
        elif activity == 'network':
            # Network activity - not available in ExperimentMatFiles
            return create_empty_plot("Network metrics not available in ExperimentMatFiles")
        
        # Default fallback
        return create_empty_plot("Visualization not yet implemented for this combination")
        
    except Exception as e:
        print(f"❌ Error in visualization: {e}")
        import traceback
        traceback.print_exc()
        return create_error_plot(f'Error: {str(e)}')

# Export visualization callback (unchanged)
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
     State('export-filename-input', 'value'),
     State('neuronal-node-group-metric', 'value'),
     State('neuronal-recording-group-metric', 'value'),
     State('neuronal-node-age-metric', 'value'),
     State('neuronal-recording-age-metric', 'value')],
    prevent_initial_call=True
)
def export_visualization(svg_clicks, png_clicks, pdf_clicks, figure, 
                        groups, selected_divs, lag, current_selection, 
                        custom_filename, node_group_metric, recording_group_metric, 
                        node_age_metric, recording_age_metric):
    """Export the current visualization in the selected format"""
    
    # Determine which button was clicked
    ctx = dash.callback_context
    if not ctx.triggered:
        return None, ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Check if we have a figure to export
    if not figure or not figure.get('data'):
        return None, "No visualization to export. Please generate a plot first."
    
    # Get current metric for filename
    activity = current_selection.get('activity') if current_selection else None
    comparison = current_selection.get('comparison') if current_selection else None
    
    metric = None
    if activity == 'neuronal' and comparison:
        if comparison == 'nodebygroup':
            metric = node_group_metric
        elif comparison == 'recordingsbygroup':
            metric = recording_group_metric
        elif comparison == 'nodebyage':
            metric = node_age_metric
        elif comparison == 'recordingsbyage':
            metric = recording_age_metric
    
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
        
        # Generate filename with metric using utils (if available)
        if not custom_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_parts = ["MEA-NAP"]
            
            if current_selection:
                if activity:
                    filename_parts.append(activity)
                if comparison:
                    filename_parts.append(comparison)
            
            if groups:
                filename_parts.append(f"group-{groups[0]}")
            
            if selected_divs:
                filename_parts.append(f"DIV{selected_divs[0]}")
            
            if metric:
                filename_parts.append(metric)
            
            filename_parts.append(timestamp)
            filename = "_".join(filename_parts)
        else:
            filename = custom_filename
        
        filename = f"{filename}.{export_format}"
        
        # Export logic
        if export_format == "svg":
            svg_bytes = fig.to_image(format="svg", width=800, height=600, scale=1)
            return (
                dict(content=svg_bytes.decode('utf-8'), filename=filename, type=mime_type),
                f"✓ SVG exported successfully as {filename}"
            )
        elif export_format == "png":
            png_bytes = fig.to_image(format="png", width=800, height=600, scale=2)
            return (
                dict(content=base64.b64encode(png_bytes).decode('utf-8'), filename=filename, type=mime_type, base64=True),
                f"✓ PNG exported successfully as {filename}"
            )
        elif export_format == "pdf":
            pdf_bytes = fig.to_image(format="pdf", width=800, height=600, scale=1)
            return (
                dict(content=base64.b64encode(pdf_bytes).decode('utf-8'), filename=filename, type=mime_type, base64=True),
                f"✓ PDF exported successfully as {filename}"
            )
        
    except Exception as e:
        return None, f"Export failed: {str(e)}"
    
    return None, ""

@app.callback(
    Output("export-status", "children", allow_duplicate=True),
    [Input("export-status", "children")],
    prevent_initial_call=True
)
def clear_export_status(status_message):
    """Clear export status message after a few seconds"""
    if status_message and "✓" in status_message:
        return status_message
    return status_message

# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=8050)