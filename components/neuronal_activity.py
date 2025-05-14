# components/neuronal_activity.py
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from data_processing.utilities import calculate_half_violin_data, extract_div_value

def create_half_violin_plot_by_group(data, metric, title):
    """
    Create a half violin plot with individual data points, grouped by experimental condition
    
    Parameters:
    -----------
    data : dict
        Dictionary with neuronal data
    metric : str
        Metric to visualize
    title : str
        Plot title
        
    Returns:
    --------
    plotly.graph_objs._figure.Figure
        Plotly figure object
    """

    print(f"\nDEBUG: Creating half violin plot by group for metric: {metric}")
    print(f"Available metrics in data['by_group']:")
    
    # Check the first group's available metrics
    if data['groups']:
        first_group = data['groups'][0]
        if first_group in data['by_group']:
            print(f"Metrics in {first_group}: {list(data['by_group'][first_group].keys())}")
        
    # Check if our target metric exists in each group
    for group in data['groups']:
        if group not in data['by_group']:
            print(f"Group {group} not found in data")
            continue
            
        if metric not in data['by_group'][group]:
            print(f"Metric {metric} not found in group {group}")
        else:
            metric_values = data['by_group'][group][metric]
            print(f"Group {group}, metric {metric}: {len(metric_values)} values")
            if metric_values:
                print(f"  Sample value: {metric_values[0]}, type: {type(metric_values[0])}")
                if isinstance(metric_values[0], (list, np.ndarray)):
                    print(f"  Is array with shape: {np.shape(metric_values[0])}")


    # Create figure with subplots for each group
    groups = data['groups']
    fig = make_subplots(rows=1, cols=len(groups), 
                        subplot_titles=[g for g in groups],
                        shared_yaxes=True)
    
    # Color palette
    colors = [
        '#1f77b4',  # blue
        '#ff7f0e',  # orange
        '#2ca02c',  # green
        '#d62728',  # red
        '#9467bd',  # purple
        '#8c564b',  # brown
        '#e377c2',  # pink
        '#7f7f7f',  # gray
    ]
    
    # Maximum y value for scaling
    max_y = 0
    
    # Create half violin plots for each group
    for col, group in enumerate(groups, 1):
        group_data = data['by_group'][group]
        
        if metric not in group_data:
            continue
            
        metric_data = group_data[metric]
        divs = sorted(data['divs'])

        is_recording_metric = metric in ['FRmean', 'FRmedian', 'numActiveElec', 'NBurstRate', 
                                'meanNumChansInvolvedInNbursts', 'meanNBstLengthS',
                                'meanISIWithinNbursts_ms', 'meanISIoutsideBursts_ms',
                                'CVofINBI', 'fracInNburst']
        
        for div_idx, div in enumerate(divs):
            div_data = []
    
            # Find experiments for this group and DIV
            if is_recording_metric:
                # For recording metrics, extract by matching DIV in experiment name
                exp_indices = []
                for i, exp_name in enumerate(group_data['exp_names']):
                    # Use extract_div_value to properly handle complex DIV formats
                    div_parts = [part for part in exp_name.split('_') if 'DIV' in part]
                    if div_parts and extract_div_value(div_parts[0]) == div:
                        exp_indices.append(i)
                
                # Add the data if we found matching experiments
                if exp_indices and len(group_data[metric]) >= max(exp_indices) + 1:
                    div_data = [group_data[metric][i] for i in exp_indices if i < len(group_data[metric])]
                    # Make sure we don't have nested arrays
                    flat_data = []
                    for item in div_data:
                        if isinstance(item, (list, np.ndarray)):
                            flat_data.extend(item)
                        else:
                            flat_data.append(item)
                    div_data = flat_data
                    print(f"Recording-level metric {metric}: Found {len(div_data)} values for DIV {div}")
            
            # Find experiments for this group and DIV
            for exp_idx, exp_name in enumerate(group_data['exp_names']):
                if any(f'DIV{div}' in exp_name for div_part in exp_name.split('_')):
                    # Extract corresponding data for this experiment
                    exp_data = data['by_experiment'].get(exp_name, {})
                    if 'activity' in exp_data and metric in exp_data['activity']:
                        div_data.extend(exp_data['activity'][metric])
            
            if not div_data:
                continue
                
            # Calculate KDE data
            kde_data = calculate_half_violin_data(div_data)
            
            # Update max_y for scaling
            max_y = max(max_y, max(kde_data['raw_data']) if kde_data['raw_data'].size > 0 else 0)
            
            # Add violin plot
            x_base = div_idx + 1
            color = colors[div_idx % len(colors)]
            
            # Add scatter points with jitter
            jitter = np.random.normal(0, 0.05, size=len(kde_data['raw_data']))
            fig.add_trace(
                go.Scatter(
                    x=[x_base + j for j in jitter],
                    y=kde_data['raw_data'],
                    mode='markers',
                    marker=dict(
                        color=color,
                        size=5,
                        opacity=0.7
                    ),
                    name=f'DIV {div}',
                    legendgroup=f'DIV {div}',
                    showlegend=(col == 1)  # Only show legend for first group
                ),
                row=1, col=col
            )
            
            # Add half violin
            fig.add_trace(
                go.Violin(
                    x=[x_base] * len(kde_data['x']),
                    y=kde_data['x'],
                    width=0.8,
                    side='positive',
                    line_color=color,
                    fillcolor=color,
                    points=False,
                    meanline_visible=False,
                    opacity=0.5,
                    showlegend=False
                ),
                row=1, col=col
            )
            
            # Add mean line
            fig.add_trace(
                go.Scatter(
                    x=[x_base - 0.3, x_base + 0.3],
                    y=[kde_data['mean'], kde_data['mean']],
                    mode='lines',
                    line=dict(color='black', width=2),
                    showlegend=False
                ),
                row=1, col=col
            )
            
            # Add error bar (SEM)
            fig.add_trace(
                go.Scatter(
                    x=[x_base, x_base],
                    y=[kde_data['mean'] - kde_data['sem'], kde_data['mean'] + kde_data['sem']],
                    mode='lines',
                    line=dict(color='black', width=1),
                    showlegend=False
                ),
                row=1, col=col
            )
    
    # Update layout
    fig.update_layout(
        title=title,
        height=600,
        margin=dict(l=50, r=50, t=80, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update x-axes
    for col in range(1, len(groups) + 1):
        divs = sorted(data['divs'])
        fig.update_xaxes(
            tickvals=list(range(1, len(divs) + 1)),
            ticktext=[f'DIV {div}' for div in divs],
            row=1, col=col
        )
    
    # Update y-axes
    metric_labels = {
        'FR': 'Firing Rate (Hz)',
        'channelBurstRate': 'Burst Rate (per minute)',
        'channelBurstDur': 'Burst Duration (ms)',
        'channelISIwithinBurst': 'ISI Within Burst (ms)',
        'channeISIoutsideBurst': 'ISI Outside Burst (ms)',
        'channelFracSpikesInBursts': 'Fraction Spikes in Bursts'
    }
    
    fig.update_yaxes(
        title_text=metric_labels.get(metric, metric),
        range=[0, max_y * 1.1]  # Add 10% padding
    )
    
    return fig

def create_half_violin_plot_by_age(data, metric, title):
    """
    Create a half violin plot with individual data points, grouped by age/DIV
    
    Parameters:
    -----------
    data : dict
        Dictionary with neuronal data
    metric : str
        Metric to visualize
    title : str
        Plot title
        
    Returns:
    --------
    plotly.graph_objs._figure.Figure
        Plotly figure object
    """
    print(f"\nDEBUG: Creating half violin plot by age for metric: {metric}")
    
    # Debug print the structure of data
    for div in data['divs']:
        if div in data['by_div']:
            print(f"DIV {div} available metrics: {list(data['by_div'][div].keys())}")
            if metric in data['by_div'][div]:
                metric_values = data['by_div'][div][metric]
                print(f"  DIV {div} has {len(metric_values)} values for {metric}")
                if metric_values:
                    print(f"    Sample values: {metric_values[:min(3, len(metric_values))]}")
                    if isinstance(metric_values[0], (list, np.ndarray)):
                        print(f"    Warning: Values are nested arrays/lists")
    
    # Create figure with subplots for each DIV
    divs = sorted(data['divs'])
    fig = make_subplots(rows=1, cols=len(divs), 
                        subplot_titles=[f'DIV {div}' for div in divs],
                        shared_yaxes=True)
    
    # Color palette
    colors = [
        '#1f77b4',  # blue
        '#ff7f0e',  # orange
        '#2ca02c',  # green
        '#d62728',  # red
        '#9467bd',  # purple
        '#8c564b',  # brown
        '#e377c2',  # pink
        '#7f7f7f',  # gray
    ]
    
    # Maximum y value for scaling
    max_y = 0
    
    # Create half violin plots for each age
    for col, div in enumerate(divs, 1):
        if div not in data['by_div']:
            print(f"DIV {div} not found in data")
            continue
            
        div_data = data['by_div'][div]
        
        if metric not in div_data:
            print(f"Metric {metric} not found in DIV {div}")
            continue
        
        # Make sure we're working with a list
        metric_values = div_data[metric]
        if isinstance(metric_values, np.ndarray):
            metric_values = metric_values.tolist()
        elif not isinstance(metric_values, list):
            metric_values = [metric_values]
            
        groups = data['groups']
        
        # Try with direct plotting of all values first
        if metric_values and len(metric_values) > 0:
            # Ensure we're working with flat numeric values
            flat_values = []
            for val in metric_values:
                if isinstance(val, (list, np.ndarray)):
                    if len(val) > 0:
                        # Take mean value for arrays
                        flat_values.append(float(np.mean(val)))
                elif val is not None and not np.isnan(val):
                    flat_values.append(float(val))
            
            if flat_values:
                # Calculate KDE data for all values together
                kde_data = calculate_half_violin_data(flat_values)
                
                # Add violin plot
                x_base = 1
                color = colors[0]
                
                # Add scatter points with jitter
                jitter = np.random.normal(0, 0.05, size=len(kde_data['raw_data']))
                fig.add_trace(
                    go.Scatter(
                        x=[x_base + j for j in jitter],
                        y=kde_data['raw_data'],
                        mode='markers',
                        marker=dict(
                            color=color,
                            size=5,
                            opacity=0.7
                        ),
                        name=f'DIV {div}',
                        showlegend=False
                    ),
                    row=1, col=col
                )
                
                # Add half violin
                fig.add_trace(
                    go.Violin(
                        x=[x_base] * len(kde_data['x']),
                        y=kde_data['x'],
                        width=0.8,
                        side='positive',
                        line_color=color,
                        fillcolor=color,
                        points=False,
                        meanline_visible=False,
                        opacity=0.5,
                        showlegend=False
                    ),
                    row=1, col=col
                )
                
                # Add mean line
                fig.add_trace(
                    go.Scatter(
                        x=[x_base - 0.3, x_base + 0.3],
                        y=[kde_data['mean'], kde_data['mean']],
                        mode='lines',
                        line=dict(color='black', width=2),
                        showlegend=False
                    ),
                    row=1, col=col
                )
                
                # Add error bar (SEM)
                fig.add_trace(
                    go.Scatter(
                        x=[x_base, x_base],
                        y=[kde_data['mean'] - kde_data['sem'], kde_data['mean'] + kde_data['sem']],
                        mode='lines',
                        line=dict(color='black', width=1),
                        showlegend=False
                    ),
                    row=1, col=col
                )
                
                # Update max_y
                max_y = max(max_y, max(kde_data['raw_data']) if kde_data['raw_data'].size > 0 else 0)
    
    # Update layout
    fig.update_layout(
        title=title,
        height=600,
        margin=dict(l=50, r=50, t=80, b=50),
        showlegend=False
    )
    
    # Update x-axes
    for col in range(1, len(divs) + 1):
        fig.update_xaxes(
            tickvals=[1],
            ticktext=["All Groups"],
            row=1, col=col
        )
    
    # Update y-axes
    metric_labels = {
        'FRmean': 'Mean Firing Rate (Hz)',
        'FRmedian': 'Median Firing Rate (Hz)',
        'numActiveElec': 'Number of Active Electrodes',
        'NBurstRate': 'Network Burst Rate (per minute)',
        'meanNBstLengthS': 'Mean Network Burst Length (s)',
        'meanISIWithinNbursts_ms': 'Mean ISI Within Network Bursts (ms)',
        'meanISIoutsideNbursts_ms': 'Mean ISI Outside Network Bursts (ms)',
        'meanNumChansInvolvedInNbursts': 'Mean Channels in Network Bursts',
        'CVofINBI': 'CV of Inter-Network Burst Intervals'
    }
    
    fig.update_yaxes(
        title_text=metric_labels.get(metric, metric),
        range=[0, max_y * 1.1] if max_y > 0 else None  # Add 10% padding if we have data
    )
    
    return fig