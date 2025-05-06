# callbacks/neuronal_callbacks.py
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from data_processing.utilities import extract_div_value
from components.neuronal_activity import (
    create_half_violin_plot_by_group,
    create_half_violin_plot_by_age
)

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
        
        # For recording-level metrics, we need to extract from the experiment data
        # Create a new data structure specifically for recording-level metrics
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
        
        # Extract recording-level metrics from experiments
        for exp_name, exp_data in data['by_experiment'].items():
            if 'group' in exp_data:
                group = exp_data['group']
                
                # Check if metric exists in this experiment
                if 'activity' in exp_data and metric in exp_data['activity']:
                    metric_value = exp_data['activity'][metric]
                    recording_data['by_group'][group][metric].append(metric_value)
                    recording_data['by_group'][group]['exp_names'].append(exp_name)
                    
                    recording_data['by_experiment'][exp_name] = {
                        'group': group,
                        'activity': {
                            metric: metric_value
                        }
                    }
        
        # Create figure
        title = f"Recording-Level {metric} by Group"
        return create_half_violin_plot_by_group(recording_data, metric, title)
    
    # Callback for recording-level metrics by age
    @app.callback(
        Output("neuronal-recording-age-plot", "figure"),
        [Input("neuronal-recording-age-metric", "value")]
    )
    def update_neuronal_recording_age_plot(metric):
        if not metric:
            return go.Figure()
        
        # Get data
        data = app.data['neuronal']
        
        # For recording-level metrics, we need to extract from the experiment data
        # Create a new data structure specifically for recording-level metrics
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
        
        # Extract recording-level metrics from experiments
        for exp_name, exp_data in data['by_experiment'].items():
            if 'group' in exp_data:
                group = exp_data['group']
                
                # Extract DIV
                div_parts = [part for part in exp_name.split('_') if 'DIV' in part]
                if div_parts:
                    div = extract_div_value(div_parts[0])
                    
                    # Check if metric exists in this experiment
                    if 'activity' in exp_data and metric in exp_data['activity']:
                        metric_value = exp_data['activity'][metric]
                        recording_data['by_div'][div][metric].append(metric_value)
                        recording_data['by_div'][div]['exp_names'].append(exp_name)
                        recording_data['by_div'][div]['groups'].append(group)
                        
                        recording_data['by_experiment'][exp_name] = {
                            'group': group,
                            'div': div,
                            'activity': {
                                metric: metric_value
                            }
                        }
        
        # Create figure
        title = f"Recording-Level {metric} by Age"
        return create_half_violin_plot_by_age(recording_data, metric, title)