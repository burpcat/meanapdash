# callbacks/network_callbacks.py
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from data_processing.utilities import extract_div_value
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
    
    # Callback for node-level network metrics by group
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
        
        # Create figure
        title = f"Node-Level {metric} by Group"
        return create_network_half_violin_plot_by_group(data, metric, lag, title, level='node')
    
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