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
    # def handle_metric_card_clicks(fr_clicks, active_clicks, burst_clicks, 
    #                              nburst_clicks, isi_in_clicks, isi_out_clicks, 
    #                              frac_clicks, plot_type, selected_groups):
    #     """Handle clicks on metric cards and show detailed plots"""
    #     import dash
        
    #     # Determine which card was clicked
    #     ctx = dash.callback_context
    #     if not ctx.triggered:
    #         return go.Figure(), "Select a metric to view details"
            
    #     button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
    #     # Map card IDs to metrics and titles
    #     card_to_metric = {
    #         "mean-firing-rate-card": ("FRmean", "Mean Firing Rate"),
    #         "active-electrodes-card": ("numActiveElec", "Number of Active Electrodes"),
    #         "burst-rate-card": ("NBurstRate", "Network Burst Rate"),
    #         "network-burst-card": ("meanNBstLengthS", "Mean Network Burst Length"),
    #         "isi-within-burst-card": ("meanISIWithinNbursts_ms", "Mean ISI Within Network Bursts"),
    #         "isi-outside-burst-card": ("meanISIoutsideNbursts_ms", "Mean ISI Outside Network Bursts"),
    #         "fraction-spikes-card": ("fracInNburst", "Fraction of Spikes in Network Bursts")
    #     }
        
    #     if button_id in card_to_metric:
    #         metric, title = card_to_metric[button_id]
            
    #         # Get data and create plot based on plot_type
    #         data = app.data['neuronal']
            
    #         if plot_type == "violin":
    #             fig = create_half_violin_plot_by_group(data, metric, f"{title} by Group", selected_groups)
    #         elif plot_type == "box":
    #             fig = create_box_plot_by_group(data, metric, f"{title} by Group", selected_groups)
    #         elif plot_type == "bar":
    #             fig = create_bar_plot_by_group(data, metric, f"{title} by Group", selected_groups)
    #         else:
    #             fig = create_half_violin_plot_by_group(data, metric, f"{title} by Group", selected_groups)
            
    #         return fig, f"Detailed View: {title}"
        
    #     return go.Figure(), "Select a metric to view details"
    def handle_metric_card_clicks_debug(fr_clicks, active_clicks, burst_clicks, 
                             nburst_clicks, isi_in_clicks, isi_out_clicks, 
                             frac_clicks, plot_type, selected_groups):
        """DEBUG VERSION: Handle clicks on metric cards and show detailed plots"""
        import dash
        
        # Determine which card was clicked
        ctx = dash.callback_context
        if not ctx.triggered:
            return go.Figure(), "Select a metric to view details"
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        print(f"\n🔍 DEBUG: {button_id} was clicked!")
        print(f"Plot type: {plot_type}")
        print(f"Selected groups: {selected_groups}")
        
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
            print(f"🎯 Mapped to metric: {metric}")
            
            # DEBUG: Check if app.data exists and is loaded
            if not hasattr(app, 'data'):
                print("❌ app.data doesn't exist!")
                return go.Figure(), "Error: No app data"
            
            if not app.data.get('loaded'):
                print("❌ Data not loaded!")
                return go.Figure(), "Error: Data not loaded"
            
            print("✅ Data is loaded")
            
            # DEBUG: Check neuronal data structure
            data = app.data['neuronal']
            print(f"📊 Neuronal data keys: {list(data.keys())}")
            print(f"Groups in data: {data.get('groups', [])}")
            
            # DEBUG: Check if metric exists in data
            if 'by_group' not in data:
                print("❌ 'by_group' not found in neuronal data!")
                return go.Figure(), "Error: by_group missing"
            
            by_group = data['by_group']
            print(f"🏷️ Groups available: {list(by_group.keys())}")
            
            # Check metric availability across all groups
            metric_found = False
            for group_name, group_data in by_group.items():
                if metric in group_data:
                    values = group_data[metric]
                    value_count = len(values) if isinstance(values, list) else 1
                    print(f"✅ Metric '{metric}' found in group '{group_name}': {value_count} values")
                    if isinstance(values, list) and len(values) > 0:
                        print(f"   Sample values: {values[:3]}")
                    metric_found = True
                else:
                    available_fields = list(group_data.keys())
                    print(f"❌ Metric '{metric}' NOT found in group '{group_name}'")
                    print(f"   Available fields: {available_fields[:10]}...")  # Show first 10
            
            if not metric_found:
                return go.Figure().update_layout(title=f"❌ Metric '{metric}' not found in any group data"), f"Error: {title}"
            
            # DEBUG: Try creating the plot with debugging
            try:
                print(f"🎨 Attempting to create {plot_type} plot...")
                
                if plot_type == "violin":
                    print("📊 Calling create_half_violin_plot_by_group...")
                    fig = create_half_violin_plot_by_group(data, metric, f"{title} by Group", selected_groups)
                    print("✅ Violin plot created successfully!")
                elif plot_type == "box":
                    print("📦 Calling create_box_plot_by_group...")
                    fig = create_box_plot_by_group(data, metric, f"{title} by Group", selected_groups)
                    print("✅ Box plot created successfully!")
                elif plot_type == "bar":
                    print("📊 Calling create_bar_plot_by_group...")
                    fig = create_bar_plot_by_group(data, metric, f"{title} by Group", selected_groups)
                    print("✅ Bar plot created successfully!")
                else:
                    print("🎻 Defaulting to violin plot...")
                    fig = create_half_violin_plot_by_group(data, metric, f"{title} by Group", selected_groups)
                    print("✅ Default violin plot created successfully!")
                
                return fig, f"Detailed View: {title}"
            
            except Exception as e:
                print(f"💥 ERROR in plot creation: {str(e)}")
                import traceback
                traceback.print_exc()
                
                error_fig = go.Figure().update_layout(
                    title=f"Error creating {title} plot: {str(e)}",
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )
                return error_fig, f"Error: {title}"
        
        print("❓ Unknown button clicked")
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
        # print(f"\nDEBUG: Searching for recording-level metric '{metric}' by group")
        
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
        
        # print(f"\nDEBUG: Searching for recording-level metric '{metric}' by DIV")
        
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
        
def calculate_active_electrodes_from_data(neuronal_data, selected_groups=None):
    """
    Calculate number of active electrodes per recording from FR data
    Following pipeline Claude's specification: active = FR > 0.1 Hz
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
                    
                    print(f"  {exp_name} (group {group}): {active_count} active electrodes from {len(valid_fr)} total")
    
    # Debug output
    for group in groups_to_process:
        active_counts = calculated_data['by_group'][group]['numActiveElec']
        if active_counts:
            print(f"📊 Group {group}: {len(active_counts)} recordings, active electrode counts: {active_counts}")
        else:
            print(f"❌ Group {group}: No active electrode data calculated")
    
    return calculated_data