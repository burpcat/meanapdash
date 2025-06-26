# callbacks/network_callbacks.py - FIXED VERSION
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from data_processing.utilities import extract_div_value, safe_flatten_array
from components.network_activity import (
    create_network_half_violin_plot_by_group,
    create_metrics_by_lag_plot,
    create_node_cartography_plot
)

def register_network_callbacks(app):
    """
    Register all callbacks related to network activity
    
    Parameters:
    -----------
    app : dash.Dash
        The Dash application instance
    """
    
    # FIXED: Callback for node-level network metrics by group (fixed indentation)
    @app.callback(
        Output("network-node-group-plot", "figure"),
        [Input("network-node-group-metric", "value"),
         Input("network-node-group-lag", "value")]
    )
    def update_network_node_group_plot(metric, lag):
        if not metric or not lag:
            return go.Figure()
        
        # Get data
        data = app.data['network']
        
        # Debug available metrics and groups
        print(f"\nDEBUG: Searching for node-level network metric '{metric}' for lag {lag} by group")
        
        # Check data structure
        print(f"Network data structure has keys: {list(data.keys())}")
        print(f"Groups in data: {data['groups']}")
        print(f"Divs in data: {data['divs']}")
        print(f"Lags in data: {data['lags']}")
        
        # Check if data is organized by group and lag
        for group in data['groups']:
            if group in data['by_group']:
                if lag in data['by_group'][group]:
                    if 'node_metrics' in data['by_group'][group][lag]:
                        node_metrics = data['by_group'][group][lag]['node_metrics']
                        available_metrics = list(node_metrics.keys())
                        print(f"Group {group}, lag {lag} has node metrics: {available_metrics}")
                        if metric in node_metrics:
                            values = node_metrics[metric]
                            print(f"  Found {len(values)} values for {metric}")
                            if len(values) > 0:
                                print(f"    Sample: {values[:min(3, len(values))]} (type: {type(values[0])})")
                            else:
                                print(f"  Metric {metric} has 0 values in group {group}")
                        else:
                            print(f"  Metric {metric} not found in group {group}")
        
        # Create the data structure for plotting
        recording_data = {
            'by_group': {},
            'by_experiment': {},
            'groups': data['groups'],
            'divs': data['divs']
        }
        
        # Initialize group data
        for group in data['groups']:
            recording_data['by_group'][group] = {
                metric: [],
                'exp_names': []
            }
        
        # Copy data from the loaded structure
        for group in data['groups']:
            if group in data['by_group'] and lag in data['by_group'][group]:
                if 'node_metrics' in data['by_group'][group][lag] and metric in data['by_group'][group][lag]['node_metrics']:
                    # Copy metric values
                    values = data['by_group'][group][lag]['node_metrics'][metric]
                    recording_data['by_group'][group][metric] = values
                    
                    # Copy experiment names
                    recording_data['by_group'][group]['exp_names'] = data['by_group'][group][lag]['node_metrics']['exp_names']
                    
                    print(f"  Copied {len(values)} values for {group}")
        
        # Debug what's in the final data
        print(f"Final data for plotting:")
        for group in recording_data['by_group']:
            vals = recording_data['by_group'][group][metric]
            if vals:
                print(f"  Group {group}: {len(vals)} values")
                print(f"    Sample: {vals[:min(3, len(vals))]}")
            else:
                print(f"  Group {group}: No values")
        
        # If no group data is available, try to get data from individual experiments
        if all(len(recording_data['by_group'][group][metric]) == 0 for group in data['groups']):
            print("No group-level data found, trying to collect from experiments...")
            
            # Try to rebuild from experiments
            for exp_name, exp_data in data['by_experiment'].items():
                if 'group' in exp_data and 'lags' in exp_data and lag in exp_data['lags']:
                    group = exp_data['group']
                    if 'node_metrics' in exp_data['lags'][lag] and metric in exp_data['lags'][lag]['node_metrics']:
                        values = exp_data['lags'][lag]['node_metrics'][metric]
                        if values:
                            print(f"Found {len(safe_flatten_array(values))} {metric} values in {exp_name}")
                            recording_data['by_group'][group][metric].extend(safe_flatten_array(values))
                            recording_data['by_group'][group]['exp_names'].append(exp_name)
            
            # Debug what we found
            print("After collecting from experiments:")
            for group in recording_data['by_group']:
                vals = recording_data['by_group'][group][metric]
                if vals:
                    print(f"  Group {group}: {len(vals)} values")
                    print(f"    Sample: {vals[:min(3, len(vals))]}")
                else:
                    print(f"  Group {group}: Still no values")
        
        # Create figure
        title = f"Node-Level {metric} by Group (Lag {lag} ms)"
        return create_network_half_violin_plot_by_group(recording_data, metric, lag, title, level='node')
    
    # Callback for node-level network metrics by age
    @app.callback(
        Output("network-node-age-plot", "figure"),
        [Input("network-node-age-metric", "value"),
         Input("network-node-age-lag", "value")]
    )
    def update_network_node_age_plot(metric, lag):
        if not metric or not lag:
            return go.Figure()
        
        # Get data
        data = app.data['network']
        
        # Create figure for node metrics by DIV/age
        # This requires a slightly different approach than the by-group plots
        # We'll need to create a custom plotting function for this
        
        # For now, return an empty figure
        fig = go.Figure()
        fig.update_layout(
            title="Node-Level Network Metrics by Age - Coming soon",
            height=600
        )
        
        return fig
    
    # Callback for network-level metrics by group
    @app.callback(
        Output("network-recording-group-plot", "figure"),
        [Input("network-recording-group-metric", "value"),
         Input("network-recording-group-lag", "value")]
    )
    def update_network_recording_group_plot(metric, lag):
        if not metric or not lag:
            return go.Figure()
        
        # Get data
        data = app.data['network']
        
        # Create figure
        title = f"Network-Level {metric} by Group"
        return create_network_half_violin_plot_by_group(data, metric, lag, title, level='network')
    
    # Callback for network-level metrics by age
    @app.callback(
        Output("network-recording-age-plot", "figure"),
        [Input("network-recording-age-metric", "value"),
         Input("network-recording-age-lag", "value")]
    )
    def update_network_recording_age_plot(metric, lag):
        if not metric or not lag:
            return go.Figure()
        
        # Get data
        data = app.data['network']
        
        # Create figure for network metrics by DIV/age
        # This requires a slightly different approach than the by-group plots
        # We'll need to create a custom plotting function for this
        
        # For now, return an empty figure
        fig = go.Figure()
        fig.update_layout(
            title="Network-Level Metrics by Age - Coming soon",
            height=600
        )
        
        return fig
    
    # Callback for metrics by lag
    @app.callback(
        Output("network-lag-plot", "figure"),
        [Input("network-lag-group", "value"),
         Input("network-lag-metric", "value")]
    )
    def update_network_lag_plot(group, metric):
        if not group or not metric:
            return go.Figure()
        
        # Get data
        data = app.data['network']
        
        # Create figure
        return create_metrics_by_lag_plot(data, group, metric)
        
    
    # Callback for node cartography proportions plot
    @app.callback(
        Output("cartography-proportions-plot", "figure"),
        [Input("cartography-group", "value"),
         Input("cartography-lag", "value")]
    )
    def update_cartography_proportions_plot(group, lag):
        if not group or not lag:
            return go.Figure()
        
        # Get data
        data = app.data['cartography']
        
        # Create figure
        return create_node_cartography_plot(data, group, lag)
    
    # Callback for node cartography scatter plot
    @app.callback(
        Output("cartography-scatter-plot", "figure"),
        [Input("cartography-group", "value"),
         Input("cartography-lag", "value"),
         Input("cartography-div", "value")]
    )
    def update_cartography_scatter_plot(group, lag, div):
        if not group or not lag or not div:
            return go.Figure()
        
        # Get data
        data = app.data['cartography']
        
        # Create figure
        return create_node_cartography_plot(data, group, lag, div)