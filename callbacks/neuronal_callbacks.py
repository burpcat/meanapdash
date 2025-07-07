# callbacks/neuronal_callbacks.py - CLEANED VERSION
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from data_processing.utilities import extract_div_value
from components.neuronal_activity import (
    create_half_violin_plot_by_group,
    create_half_violin_plot_by_age,
    create_box_plot_by_group,  
    create_bar_plot_by_group,
    create_box_plot_by_age,
    create_bar_plot_by_age
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
    
    # Callback for clickable metric cards
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
        
        # Map card IDs to metrics and titles with corrected field names
        card_to_metric = {
            "mean-firing-rate-card": ("FRActiveNode", "Mean Firing Rate Active Node"),
            "active-electrodes-card": ("CALCULATED_ACTIVE_ELEC", "Number of Active Electrodes"),
            "burst-rate-card": ("NBurstRate", "Network Burst Rate"),
            "network-burst-card": ("meanNBstLengthS", "Mean Network Burst Length"),
            "isi-within-burst-card": ("meanISIWithinNbursts_ms", "Mean ISI Within Network Bursts"),
            "isi-outside-burst-card": ("meanISIoutsideNbursts_ms", "Mean ISI Outside Network Bursts"),
            "fraction-spikes-card": ("fracInNburst", "Fraction of Spikes in Network Bursts")
        }
        
        if button_id in card_to_metric:
            metric, title = card_to_metric[button_id]
            
            # Get data
            data = app.data['neuronal']
            
            # Special handling for Mean Firing Rate Active Node
            if metric == "FRActiveNode":
                print("🔥 Calculating Mean Firing Rate Active Node from electrode data...")
                calculated_data = calculate_mean_firing_rate_active_node_by_group(data, selected_groups)
                
                if plot_type == "violin":
                    fig = create_half_violin_plot_by_group(calculated_data, "FRActiveNode", f"{title} by Group", selected_groups)
                elif plot_type == "box":
                    fig = create_box_plot_by_group(calculated_data, "FRActiveNode", f"{title} by Group", selected_groups)
                elif plot_type == "bar":
                    fig = create_bar_plot_by_group(calculated_data, "FRActiveNode", f"{title} by Group", selected_groups)
                else:
                    fig = create_half_violin_plot_by_group(calculated_data, "FRActiveNode", f"{title} by Group", selected_groups)
                
                return fig, f"Detailed View: {title}"
            
            # Special handling for Active Electrodes
            elif metric == "CALCULATED_ACTIVE_ELEC":
                print("🔢 Calculating Active Electrodes from FR data...")
                calculated_data = calculate_active_electrodes_from_data(data, selected_groups)
                
                if plot_type == "violin":
                    fig = create_half_violin_plot_by_group(calculated_data, "numActiveElec", f"{title} by Group", selected_groups)
                elif plot_type == "box":
                    fig = create_box_plot_by_group(calculated_data, "numActiveElec", f"{title} by Group", selected_groups)
                elif plot_type == "bar":
                    fig = create_bar_plot_by_group(calculated_data, "numActiveElec", f"{title} by Group", selected_groups)
                else:
                    fig = create_half_violin_plot_by_group(calculated_data, "numActiveElec", f"{title} by Group", selected_groups)
                
                return fig, f"Detailed View: {title}"
            
            # Normal handling for other metrics
            else:
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
    
    # Callback for electrode-level metrics by group with plot type
    @app.callback(
        Output("neuronal-node-group-plot", "figure"),
        [Input("neuronal-node-group-metric", "value"),
         Input("neuronal-plot-type", "value")]
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
            return create_half_violin_plot_by_group(data, metric, title)
    
    # Callback for electrode-level metrics by age with plot type
    @app.callback(
        Output("neuronal-node-age-plot", "figure"),
        [Input("neuronal-node-age-metric", "value"),
         Input("neuronal-plot-type", "value")]
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
            return create_half_violin_plot_by_age(data, metric, title)
    
    # Callback for recording-level metrics by group with plot type
    @app.callback(
        Output("neuronal-recording-group-plot", "figure"),
        [Input("neuronal-recording-group-metric", "value"),
         Input("neuronal-plot-type", "value")]
    )
    def update_neuronal_recording_group_plot(metric, plot_type):
        if not metric:
            return go.Figure()
        
        # Get data
        data = app.data['neuronal']
        
        # Create data structure for recording-level metrics
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
                values_to_copy = data['by_group'][group][metric]
                recording_data['by_group'][group][metric] = values_to_copy
                recording_data['by_group'][group]['exp_names'] = data['by_group'][group]['exp_names']
        
        # Create figure based on plot type
        title = f"Recording-Level {metric} by Group"
        
        if plot_type == "violin":
            return create_half_violin_plot_by_group(recording_data, metric, title)
        elif plot_type == "box":
            return create_box_plot_by_group(recording_data, metric, title)
        elif plot_type == "bar":
            return create_bar_plot_by_group(recording_data, metric, title)
        else:
            return create_half_violin_plot_by_group(recording_data, metric, title)
    
    # Callback for recording-level metrics by age with plot type
    @app.callback(
        Output("neuronal-recording-age-plot", "figure"),
        [Input("neuronal-recording-age-metric", "value"),
         Input("neuronal-plot-type", "value")]
    )
    def update_neuronal_recording_age_plot(metric, plot_type):
        if not metric:
            return go.Figure()
        
        # Get data
        data = app.data['neuronal']
        
        # Create data structure for recording-level metrics by age
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
                values_to_copy = data['by_div'][div][metric]
                recording_data['by_div'][div][metric] = values_to_copy
                recording_data['by_div'][div]['exp_names'] = data['by_div'][div]['exp_names']
                recording_data['by_div'][div]['groups'] = data['by_div'][div]['groups']
        
        # Create figure based on plot type
        title = f"Recording-Level {metric} by Age"
        
        if plot_type == "violin":
            return create_half_violin_plot_by_age(recording_data, metric, title)
        elif plot_type == "box":
            return create_box_plot_by_age(recording_data, metric, title)
        elif plot_type == "bar":
            return create_bar_plot_by_age(recording_data, metric, title)
        else:
            return create_half_violin_plot_by_age(recording_data, metric, title)
        
    # Callback to show/hide appropriate metric dropdowns based on selected tab
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

def calculate_active_electrodes_from_data(neuronal_data, selected_groups=None):
    """
    Calculate number of active electrodes per recording from FR data
    Following pipeline specification: active = FR > 0.1 Hz
    """
    print("🔢 Calculating active electrodes from firing rate data...")
    
    # Create new data structure for active electrode counts
    calculated_data = {
        'by_group': {},
        'by_experiment': {},
        'groups': neuronal_data['groups'],
        'divs': neuronal_data['divs']
    }
    
    # Filter groups if specified
    if selected_groups:
        groups_to_process = [g for g in selected_groups if g in neuronal_data['groups']]
    else:
        groups_to_process = neuronal_data['groups']
    
    # Initialize group data
    for group in groups_to_process:
        calculated_data['by_group'][group] = {
            'numActiveElec': [],
            'exp_names': []
        }
    
    # Calculate active electrodes from experiment data
    for exp_name, exp_data in neuronal_data.get('by_experiment', {}).items():
        if 'activity' in exp_data and 'FR' in exp_data['activity']:
            # Get FR array for this experiment
            fr_values = exp_data['activity']['FR']
            
            if isinstance(fr_values, (list, np.ndarray)) and len(fr_values) > 0:
                # Count electrodes with FR > 0.1 Hz (pipeline specification)
                fr_array = np.array(fr_values)
                valid_fr = fr_array[~np.isnan(fr_array)]
                valid_fr = valid_fr[np.isfinite(valid_fr)]
                active_count = int(np.sum(valid_fr > 0.1))
                
                # Add to group data
                group = exp_data.get('group')
                if group in groups_to_process:
                    calculated_data['by_group'][group]['numActiveElec'].append(active_count)
                    calculated_data['by_group'][group]['exp_names'].append(exp_name)
    
    return calculated_data

def calculate_mean_firing_rate_active_node_by_group(neuronal_data, selected_groups=None):
    """
    Calculate Mean Firing Rate Active Node by Group following MEA-NAP methodology:
    1. Filter electrodes with FR > 0.1 Hz (active threshold)
    2. Calculate recording-level mean of active electrodes only
    3. Group recording-level means by experimental group
    """
    print("🔥 Calculating Mean Firing Rate Active Node by Group...")
    
    # Create new data structure for recording-level means
    calculated_data = {
        'by_group': {},
        'by_experiment': {},
        'groups': neuronal_data['groups'],
        'divs': neuronal_data['divs']
    }
    
    # Filter groups if specified
    if selected_groups:
        groups_to_process = [g for g in selected_groups if g in neuronal_data['groups']]
    else:
        groups_to_process = neuronal_data['groups']
    
    # Initialize group data
    for group in groups_to_process:
        calculated_data['by_group'][group] = {
            'FRActiveNode': [],  # Recording-level means of active nodes
            'exp_names': []
        }
    
    # Process each experiment to calculate recording-level active node means
    for exp_name, exp_data in neuronal_data.get('by_experiment', {}).items():
        if 'activity' in exp_data and 'FR' in exp_data['activity']:
            # Get FR array for this recording
            fr_values = exp_data['activity']['FR']
            
            if isinstance(fr_values, (list, np.ndarray)) and len(fr_values) > 0:
                # Convert to numpy array and clean data
                fr_array = np.array(fr_values)
                valid_fr = fr_array[~np.isnan(fr_array)]
                valid_fr = valid_fr[np.isfinite(valid_fr)]
                valid_fr = valid_fr[valid_fr >= 0]  # Remove negative values
                
                # Filter for ACTIVE electrodes (> 0.1 Hz threshold)
                active_electrodes = valid_fr[valid_fr > 0.1]
                
                if len(active_electrodes) > 0:
                    # Calculate recording-level mean of active electrodes
                    recording_mean_active = np.mean(active_electrodes)
                    
                    # Add to group data
                    group = exp_data.get('group')
                    if group in groups_to_process:
                        calculated_data['by_group'][group]['FRActiveNode'].append(recording_mean_active)
                        calculated_data['by_group'][group]['exp_names'].append(exp_name)
    
    return calculated_data