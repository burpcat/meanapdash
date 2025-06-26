# callbacks/neuronal_callbacks.py - FIXED VERSION
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from data_processing.utilities import extract_div_value
from components.neuronal_activity import (
    create_half_violin_plot_by_group,
    create_half_violin_plot_by_age,
    create_box_plot_by_group,  
    create_bar_plot_by_group,
    create_box_plot_by_age,    # MISSING IMPORT - ADDED
    create_bar_plot_by_age     # MISSING IMPORT - ADDED
)
import numpy as np

def register_neuronal_callbacks(app):
    """
    Register all callbacks related to neuronal activity
    
    Parameters:
    -----------
    app : dash.Dash
        The Dash application instance
    """
    
    # NEW: Callback for clickable metric cards
    @app.callback(
        [Output("neuronal-detail-plot", "figure"),
         Output("neuronal-detail-title", "children")],
        [Input("mean-firing-rate-card", "n_clicks"),
         Input("active-electrodes-card", "n_clicks"),
         Input("burst-rate-card", "n_clicks"),
         Input("network-burst-card", "n_clicks"),
         Input("isi-within-burst-card", "n_clicks"),
         Input("isi-outside-burst-card", "n_clicks"),
         Input("fraction-spikes-card", "n_clicks")],
        [State("neuronal-plot-type", "value"),
         State("neuronal-group-filter", "value")]
    )
    def handle_metric_card_clicks(fr_clicks, active_clicks, burst_clicks, 
                                 nburst_clicks, isi_in_clicks, isi_out_clicks, 
                                 frac_clicks, plot_type, selected_groups):
        """Handle clicks on metric cards and show detailed plots"""
        import dash
        
        # Determine which card was clicked
        ctx = dash.callback_context
        if not ctx.triggered:
            return go.Figure(), "Select a metric to view details"
            
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # Map card IDs to metrics and titles
        card_to_metric = {
            "mean-firing-rate-card": ("FRmean", "Mean Firing Rate"),
            "active-electrodes-card": ("numActiveElec", "Number of Active Electrodes"),
            "burst-rate-card": ("NBurstRate", "Network Burst Rate"),
            "network-burst-card": ("meanNBstLengthS", "Mean Network Burst Length"),
            "isi-within-burst-card": ("meanISIWithinNbursts_ms", "Mean ISI Within Network Bursts"),
            "isi-outside-burst-card": ("meanISIoutsideNbursts_ms", "Mean ISI Outside Network Bursts"),
            "fraction-spikes-card": ("fracInNburst", "Fraction of Spikes in Network Bursts")
        }
        
        if button_id in card_to_metric:
            metric, title = card_to_metric[button_id]
            
            # Get data and create plot based on plot_type
            data = app.data['neuronal']
            
            if plot_type == "violin":
                fig = create_half_violin_plot_by_group(data, metric, f"{title} by Group", selected_groups)
            elif plot_type == "box":
                fig = create_box_plot_by_group(data, metric, f"{title} by Group", selected_groups)
            elif plot_type == "bar":
                fig = create_bar_plot_by_group(data, metric, f"{title} by Group", selected_groups)
            else:
                fig = create_half_violin_plot_by_group(data, metric, f"{title} by Group", selected_groups)
            
            return fig, f"Detailed View: {title}"
        
        return go.Figure(), "Select a metric to view details"
    
    # ENHANCED: Callback for electrode-level metrics by group with plot type
    @app.callback(
        Output("neuronal-node-group-plot", "figure"),
        [Input("neuronal-node-group-metric", "value"),
         Input("neuronal-plot-type", "value")]  # NEW: Plot type input
    )
    def update_neuronal_node_group_plot(metric, plot_type):
        if not metric:
            return go.Figure()
        
        # Get data
        data = app.data['neuronal']
        
        # Create figure based on plot type
        title = f"Electrode-Level {metric} by Group"
        
        if plot_type == "violin":
            return create_half_violin_plot_by_group(data, metric, title)
        elif plot_type == "box":
            return create_box_plot_by_group(data, metric, title)
        elif plot_type == "bar":
            return create_bar_plot_by_group(data, metric, title)
        else:
            # Default to violin
            return create_half_violin_plot_by_group(data, metric, title)
    
    # ENHANCED: Callback for electrode-level metrics by age with plot type
    @app.callback(
        Output("neuronal-node-age-plot", "figure"),
        [Input("neuronal-node-age-metric", "value"),
         Input("neuronal-plot-type", "value")]  # NEW: Plot type input
    )
    def update_neuronal_node_age_plot(metric, plot_type):
        if not metric:
            return go.Figure()
        
        # Get data
        data = app.data['neuronal']
        
        # Create figure based on plot type
        title = f"Electrode-Level {metric} by Age"
        
        if plot_type == "violin":
            return create_half_violin_plot_by_age(data, metric, title)
        elif plot_type == "box":
            return create_box_plot_by_age(data, metric, title)
        elif plot_type == "bar":
            return create_bar_plot_by_age(data, metric, title)
        else:
            # Default to violin
            return create_half_violin_plot_by_age(data, metric, title)
    
    # ENHANCED: Callback for recording-level metrics by group with plot type
    @app.callback(
        Output("neuronal-recording-group-plot", "figure"),
        [Input("neuronal-recording-group-metric", "value"),
         Input("neuronal-plot-type", "value")]  # NEW: Plot type input
    )
    def update_neuronal_recording_group_plot(metric, plot_type):
        if not metric:
            return go.Figure()
        
        # Get data
        data = app.data['neuronal']
        
        # Debug available metrics
        print(f"\nDEBUG: Searching for recording-level metric '{metric}' by group")
        
        # IMPORTANT CHANGE: Use the existing data structure
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
        
        # Copy metrics from the main data structure
        for group in data['groups']:
            if group in data['by_group'] and metric in data['by_group'][group]:
                # Copy the metric values
                values_to_copy = data['by_group'][group][metric]
                recording_data['by_group'][group][metric] = values_to_copy
                
                # Also need to get corresponding experiment names
                recording_data['by_group'][group]['exp_names'] = data['by_group'][group]['exp_names']
                
                print(f"  Copying {len(values_to_copy)} {metric} values for group {group}")
        
        # Create figure based on plot type
        title = f"Recording-Level {metric} by Group"
        
        if plot_type == "violin":
            return create_half_violin_plot_by_group(recording_data, metric, title)
        elif plot_type == "box":
            return create_box_plot_by_group(recording_data, metric, title)
        elif plot_type == "bar":
            return create_bar_plot_by_group(recording_data, metric, title)
        else:
            # Default to violin
            return create_half_violin_plot_by_group(recording_data, metric, title)
    
    # Callback for recording-level metrics by age with plot type
    @app.callback(
        Output("neuronal-recording-age-plot", "figure"),
        [Input("neuronal-recording-age-metric", "value"),
         Input("neuronal-plot-type", "value")]  # NEW: Plot type input
    )
    def update_neuronal_recording_age_plot(metric, plot_type):
        if not metric:
            return go.Figure()
        
        # Get data
        data = app.data['neuronal']
        
        print(f"\nDEBUG: Searching for recording-level metric '{metric}' by DIV")
        
        # Use the existing data structure
        recording_data = {
            'by_div': {},
            'by_experiment': {},
            'groups': data['groups'],
            'divs': data['divs']
        }
        
        # Initialize DIV data
        for div in data['divs']:
            recording_data['by_div'][div] = {
                metric: [],
                'exp_names': [],
                'groups': []
            }
        
        # Copy metrics from the main data structure
        for div in data['divs']:
            if div in data['by_div'] and metric in data['by_div'][div]:
                # Copy the metric values
                values_to_copy = data['by_div'][div][metric]
                recording_data['by_div'][div][metric] = values_to_copy
                
                # Also need to get corresponding experiment names and groups
                recording_data['by_div'][div]['exp_names'] = data['by_div'][div]['exp_names']
                recording_data['by_div'][div]['groups'] = data['by_div'][div]['groups']
                
                print(f"  Copying {len(values_to_copy)} {metric} values for DIV {div}")
        
        # Create figure based on plot type
        title = f"Recording-Level {metric} by Age"
        
        if plot_type == "violin":
            return create_half_violin_plot_by_age(recording_data, metric, title)
        elif plot_type == "box":
            return create_box_plot_by_age(recording_data, metric, title)
        elif plot_type == "bar":
            return create_bar_plot_by_age(recording_data, metric, title)
        else:
            # Default to violin
            return create_half_violin_plot_by_age(recording_data, metric, title)
        
    # NEW: Callback to show/hide appropriate metric dropdowns based on selected tab
    @app.callback(
        [Output("neuronal-node-group-dropdown", "style"),
         Output("neuronal-node-age-dropdown", "style"), 
         Output("neuronal-recording-group-dropdown", "style"),
         Output("neuronal-recording-age-dropdown", "style")],
        [Input("neuronal-tabs", "value")]
    )
    def toggle_metric_dropdowns(selected_tab):
        """Show/hide appropriate metric dropdown based on selected neuronal tab"""
        
        # Default style - hidden
        hidden_style = {'marginBottom': '15px', 'display': 'none'}
        visible_style = {'marginBottom': '15px', 'display': 'block'}
        
        if selected_tab == "nodebygroup":
            return visible_style, hidden_style, hidden_style, hidden_style
        elif selected_tab == "nodebyage":
            return hidden_style, visible_style, hidden_style, hidden_style  
        elif selected_tab == "recordingsbygroup":
            return hidden_style, hidden_style, visible_style, hidden_style
        elif selected_tab == "recordingsbyage":
            return hidden_style, hidden_style, hidden_style, visible_style
        else:
            return hidden_style, hidden_style, hidden_style, hidden_style
        
    # Callback to show/hide appropriate plot containers based on selected tab
    @app.callback(
        [Output("neuronal-node-group-container", "style"),
         Output("neuronal-node-age-container", "style"),
         Output("neuronal-recording-group-container", "style"), 
         Output("neuronal-recording-age-container", "style")],
        [Input("neuronal-tabs", "value")]
    )
    def toggle_plot_containers(selected_tab):
        """Show/hide appropriate plot container based on selected neuronal tab"""
        
        # Default style - hidden
        hidden_style = {'display': 'none'}
        visible_style = {'display': 'block'}
        
        if selected_tab == "nodebygroup":
            return visible_style, hidden_style, hidden_style, hidden_style
        elif selected_tab == "nodebyage":
            return hidden_style, visible_style, hidden_style, hidden_style
        elif selected_tab == "recordingsbygroup":
            return hidden_style, hidden_style, visible_style, hidden_style
        elif selected_tab == "recordingsbyage":
            return hidden_style, hidden_style, hidden_style, visible_style
        else:
            return hidden_style, hidden_style, hidden_style, hidden_style