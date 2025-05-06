# components/neuronal_activity.py
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from data_processing.utilities import calculate_half_violin_data

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
        
        for div_idx, div in enumerate(divs):
            div_data = []
            
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
            continue
            
        div_data = data['by_div'][div]
        
        if metric not in div_data:
            continue
        
        groups = data['groups']
        
        for group_idx, group in enumerate(groups):
            group_data = []
            
            # Find experiments for this DIV and group
            exp_indices = [i for i, g in enumerate(div_data['groups']) if g == group]
            
            for idx in exp_indices:
                exp_name = div_data['exp_names'][idx]
                exp_data = data['by_experiment'].get(exp_name, {})
                if 'activity' in exp_data and metric in exp_data['activity']:
                    group_data.extend(exp_data['activity'][metric])
            
            if not group_data:
                continue
                
            # Calculate KDE data
            kde_data = calculate_half_violin_data(group_data)
            
            # Update max_y for scaling
            max_y = max(max_y, max(kde_data['raw_data']) if kde_data['raw_data'].size > 0 else 0)
            
            # Add violin plot
            x_base = group_idx + 1
            color = colors[group_idx % len(colors)]
            
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
                    name=group,
                    legendgroup=group,
                    showlegend=(col == 1)  # Only show legend for first DIV
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
    for col in range(1, len(divs) + 1):
        groups = data['groups']
        fig.update_xaxes(
            tickvals=list(range(1, len(groups) + 1)),
            ticktext=groups,
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