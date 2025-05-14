# callbacks/neuronal_callbacks.py
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from data_processing.utilities import extract_div_value
from components.neuronal_activity import (
    create_half_violin_plot_by_group,
    create_half_violin_plot_by_age
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
    
    # Callback for electrode-level metrics by group
    @app.callback(
        Output("neuronal-node-group-plot", "figure"),
        [Input("neuronal-node-group-metric", "value")]
    )
    def update_neuronal_node_group_plot(metric):
        if not metric:
            return go.Figure()
        
        # Get data
        data = app.data['neuronal']
        
        # Create figure
        title = f"Electrode-Level {metric} by Group"
        return create_half_violin_plot_by_group(data, metric, title)
    
    # Callback for electrode-level metrics by age
    @app.callback(
        Output("neuronal-node-age-plot", "figure"),
        [Input("neuronal-node-age-metric", "value")]
    )
    def update_neuronal_node_age_plot(metric):
        if not metric:
            return go.Figure()
        
        # Get data
        data = app.data['neuronal']
        
        # Create figure
        title = f"Electrode-Level {metric} by Age"
        return create_half_violin_plot_by_age(data, metric, title)
    
    # Callback for recording-level metrics by group
    @app.callback(
        Output("neuronal-recording-group-plot", "figure"),
        [Input("neuronal-recording-group-metric", "value")]
    )
    def update_neuronal_recording_group_plot(metric):
        if not metric:
            return go.Figure()
        
        # Get data
        data = app.data['neuronal']
        
        # Debug available metrics
        print(f"\nDEBUG: Searching for recording-level metric '{metric}' by group")
        
        # Debug what metrics are available in by_group
        for group in data['groups']:
            if group in data['by_group']:
                group_metrics = [m for m in data['by_group'][group].keys() 
                                if m not in ['exp_names', 'channels', 'FR', 'channelBurstRate', 
                                            'channelBurstDur', 'channelISIwithinBurst', 
                                            'channeISIoutsideBurst', 'channelFracSpikesInBursts']]
                print(f"Group {group} has metrics: {group_metrics}")
                
                if metric in data['by_group'][group]:
                    metric_values = data['by_group'][group][metric]
                    print(f"  Metric {metric} has {len(metric_values)} values directly in group data")
        
        # IMPORTANT CHANGE: Use the existing data structure instead of creating a new one
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
        
        # Here's the key fix: directly copy metrics from the main data structure
        for group in data['groups']:
            if group in data['by_group'] and metric in data['by_group'][group]:
                # Copy the metric values
                values_to_copy = data['by_group'][group][metric]
                recording_data['by_group'][group][metric] = values_to_copy
                
                # Also need to get corresponding experiment names
                recording_data['by_group'][group]['exp_names'] = data['by_group'][group]['exp_names']
                
                # Debug what's being copied
                print(f"  Copying {len(values_to_copy)} {metric} values for group {group}")
                if values_to_copy:
                    print(f"    First few values: {values_to_copy[:min(3, len(values_to_copy))]}")
        
        # Debug what's in final recording_data
        print(f"Final recording_data for plotting:")
        for group in recording_data['by_group']:
            print(f"  Group {group}: {len(recording_data['by_group'][group][metric])} values for {metric}")
            if recording_data['by_group'][group][metric]:
                samples = recording_data['by_group'][group][metric][:min(3, len(recording_data['by_group'][group][metric]))]
                print(f"    Sample values: {samples}")
        
        # Create figure
        title = f"Recording-Level {metric} by Group"
        return create_half_violin_plot_by_group(recording_data, metric, title)
    
    # Modified callback for recording-level metrics by age
    @app.callback(
        Output("neuronal-recording-age-plot", "figure"),
        [Input("neuronal-recording-age-metric", "value")]
    )
    def update_neuronal_recording_age_plot(metric):
        if not metric:
            return go.Figure()
        
        # Get data
        data = app.data['neuronal']
        
        print(f"\nDEBUG: Searching for recording-level metric '{metric}' by DIV")
        
        # Check if metric exists in by_div structure
        divs_with_metric = []
        for div in data['divs']:
            if div in data['by_div']:
                div_metrics = [m for m in data['by_div'][div].keys() 
                            if m not in ['exp_names', 'groups', 'channels', 'FR', 'channelBurstRate', 
                                        'channelBurstDur', 'channelISIwithinBurst', 
                                        'channeISIoutsideBurst', 'channelFracSpikesInBursts']]
                print(f"  DIV {div} has metrics: {div_metrics}")
                
                if metric in data['by_div'][div]:
                    metric_values = data['by_div'][div][metric]
                    divs_with_metric.append(div)
                    print(f"  DIV {div} has {len(metric_values)} values for {metric}")
                    if metric_values:
                        print(f"    First few values: {metric_values[:min(3, len(metric_values))]}")
        
        if not divs_with_metric:
            print(f"  Metric {metric} not found in any DIV")
        
        # Use the existing data structure instead of creating a new one
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
        
        # Here's the key fix: directly copy metrics from the main data structure
        for div in data['divs']:
            if div in data['by_div'] and metric in data['by_div'][div]:
                # Copy the metric values
                values_to_copy = data['by_div'][div][metric]
                recording_data['by_div'][div][metric] = values_to_copy
                
                # Also need to get corresponding experiment names and groups
                recording_data['by_div'][div]['exp_names'] = data['by_div'][div]['exp_names']
                recording_data['by_div'][div]['groups'] = data['by_div'][div]['groups']
                
                # Debug what's being copied
                print(f"  Copying {len(values_to_copy)} {metric} values for DIV {div}")
                if values_to_copy:
                    print(f"    First few values: {values_to_copy[:min(3, len(values_to_copy))]}")
        
        # Debug what's in final DIV data
        print(f"Final DIV data for plotting:")
        for div in recording_data['by_div']:
            print(f"  DIV {div}: {len(recording_data['by_div'][div][metric])} values for {metric}")
            if recording_data['by_div'][div][metric]:
                samples = recording_data['by_div'][div][metric][:min(3, len(recording_data['by_div'][div][metric]))]
                print(f"    Sample values: {samples}")
        
        # Create figure
        title = f"Recording-Level {metric} by Age"
        return create_half_violin_plot_by_age(recording_data, metric, title)