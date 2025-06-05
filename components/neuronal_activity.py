# components/neuronal_activity.py
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from data_processing.utilities import calculate_half_violin_data, extract_div_value

def create_half_violin_plot_by_group(data, metric, title, selected_groups=None, selected_divs=None):
    """
    Create a half violin plot with individual data points, grouped by experimental condition
    """
    print(f"\nDEBUG: Creating half violin plot by group for metric: {metric}")
    print(f"Selected groups: {selected_groups}")
    print(f"Selected DIVs: {selected_divs}")
    
    # FILTER: Use only selected groups, or all if none selected
    if selected_groups:
        groups = [g for g in selected_groups if g in data['groups']]
    else:
        groups = data['groups']
    
    # FILTER: Use only selected DIVs, or all if none selected  
    if selected_divs:
        divs = [d for d in selected_divs if d in data['divs']]
    else:
        divs = sorted(data['divs'])
    
    print(f"Filtered to groups: {groups}")
    print(f"Filtered to DIVs: {divs}")
    
    if not groups:
        return go.Figure().update_layout(title="No groups selected or available")
    
    # Create figure with subplots for each SELECTED group only
    fig = make_subplots(rows=1, cols=len(groups), 
                        subplot_titles=[g for g in groups],
                        shared_yaxes=True)
    
    # Color palette
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
    fill_colors = ['rgba(31, 119, 180, 0.5)', 'rgba(255, 127, 14, 0.5)', 'rgba(44, 160, 44, 0.5)', 
                   'rgba(214, 39, 40, 0.5)', 'rgba(148, 103, 189, 0.5)', 'rgba(140, 86, 75, 0.5)', 
                   'rgba(227, 119, 194, 0.5)', 'rgba(127, 127, 127, 0.5)']
    
    max_y = 0
    
    # Process only SELECTED groups
    for col, group in enumerate(groups, 1):
        if group not in data['by_group']:
            continue
            
        group_data = data['by_group'][group]
        if metric not in group_data:
            continue
            
        is_recording_metric = metric in ['FRmean', 'FRmedian', 'numActiveElec', 'NBurstRate', 
                                'meanNumChansInvolvedInNbursts', 'meanNBstLengthS',
                                'meanISIWithinNbursts_ms', 'meanISIoutsideNbursts_ms',
                                'CVofINBI', 'fracInNburst']
        
        # Process only SELECTED DIVs
        for div_idx, div in enumerate(divs):
            div_data = []
    
            if is_recording_metric:
                exp_indices = []
                for i, exp_name in enumerate(group_data['exp_names']):
                    div_parts = [part for part in exp_name.split('_') if 'DIV' in part]
                    if div_parts and extract_div_value(div_parts[0]) == div:
                        exp_indices.append(i)
                
                if exp_indices and len(group_data[metric]) >= max(exp_indices) + 1:
                    div_data = [group_data[metric][i] for i in exp_indices if i < len(group_data[metric])]
                    flat_data = []
                    for item in div_data:
                        if isinstance(item, (list, np.ndarray)):
                            flat_data.extend(item)
                        else:
                            flat_data.append(item)
                    div_data = flat_data
            
            # Node-level metrics
            for exp_idx, exp_name in enumerate(group_data['exp_names']):
                if any(f'DIV{div}' in exp_name for div_part in exp_name.split('_')):
                    exp_data = data['by_experiment'].get(exp_name, {})
                    if 'activity' in exp_data and metric in exp_data['activity']:
                        div_data.extend(exp_data['activity'][metric])
            
            if not div_data:
                continue
                
            # Calculate KDE data
            kde_data = calculate_half_violin_data(div_data)
            max_y = max(max_y, max(kde_data['raw_data']) if kde_data['raw_data'].size > 0 else 0)
            
            # Plot styling
            x_base = div_idx + 1
            color = colors[div_idx % len(colors)]
            fill_color = fill_colors[div_idx % len(fill_colors)]
            
            # Add scatter points
            jitter = np.random.normal(0, 0.05, size=len(kde_data['raw_data']))
            fig.add_trace(
                go.Scatter(
                    x=[x_base + j for j in jitter],
                    y=kde_data['raw_data'],
                    mode='markers',
                    marker=dict(color=color, size=5, opacity=0.7),
                    name=f'DIV {div}',
                    legendgroup=f'DIV {div}',
                    showlegend=(col == 1)
                ),
                row=1, col=col
            )
            
            # Add violin
            fig.add_trace(
                go.Violin(
                    x=[x_base] * len(kde_data['x']),
                    y=kde_data['x'],
                    width=0.8,
                    side='positive',
                    line_color=color,
                    fillcolor=fill_color,
                    points=False,
                    meanline_visible=False,
                    opacity=0.5,
                    showlegend=False
                ),
                row=1, col=col
            )
            
            # Add mean line and error bars
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
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Update axes
    for col in range(1, len(groups) + 1):
        fig.update_xaxes(
            tickvals=list(range(1, len(divs) + 1)),
            ticktext=[f'DIV {div}' for div in divs],
            row=1, col=col
        )
    
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
        range=[0, max_y * 1.1]
    )
    
    return fig

def create_half_violin_plot_by_age(data, metric, title, selected_groups=None, selected_divs=None):
    """
    Create a half violin plot with individual data points, grouped by age/DIV
    """
    print(f"\nDEBUG: Creating half violin plot by age for metric: {metric}")
    print(f"Selected groups: {selected_groups}")
    print(f"Selected DIVs: {selected_divs}")
    
    # FILTER: Use only selected DIVs
    if selected_divs:
        divs = [d for d in selected_divs if d in data['divs']]
    else:
        divs = sorted(data['divs'])
    
    # FILTER: Use only selected groups  
    if selected_groups:
        groups = [g for g in selected_groups if g in data['groups']]
    else:
        groups = data['groups']
    
    print(f"Filtered to DIVs: {divs}")
    print(f"Filtered to groups: {groups}")
    
    if not divs:
        return go.Figure().update_layout(title="No DIVs selected or available")
    
    # Create figure with subplots for each SELECTED DIV only
    fig = make_subplots(rows=1, cols=len(divs), 
                        subplot_titles=[f'DIV {div}' for div in divs],
                        shared_yaxes=True)
    
    # FIXED: Group-specific colors so you can tell cell lines apart
    group_colors = {}
    group_fill_colors = {}
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
    fill_colors = ['rgba(31, 119, 180, 0.5)', 'rgba(255, 127, 14, 0.5)', 'rgba(44, 160, 44, 0.5)', 
                   'rgba(214, 39, 40, 0.5)', 'rgba(148, 103, 189, 0.5)', 'rgba(140, 86, 75, 0.5)', 
                   'rgba(227, 119, 194, 0.5)', 'rgba(127, 127, 127, 0.5)']
    
    for i, group in enumerate(groups):
        group_colors[group] = colors[i % len(colors)]
        group_fill_colors[group] = fill_colors[i % len(fill_colors)]
    
    max_y = 0
    
    # Process only SELECTED DIVs
    for col, div in enumerate(divs, 1):
        if div not in data['by_div']:
            continue
            
        div_data = data['by_div'][div]
        if metric not in div_data:
            continue
        
        # Get all values for this DIV
        metric_values = div_data[metric]
        if isinstance(metric_values, np.ndarray):
            metric_values = metric_values.tolist()
        elif not isinstance(metric_values, list):
            metric_values = [metric_values]
            
        # FIXED: Group the data by cell line so we can color-code them
        group_data_for_div = {}
        
        # Try to extract group information for each data point
        if 'groups' in div_data and len(div_data['groups']) == len(metric_values):
            # We have group info for each data point
            for i, group in enumerate(div_data['groups']):
                if group in groups:  # Only include selected groups
                    if group not in group_data_for_div:
                        group_data_for_div[group] = []
                    
                    val = metric_values[i]
                    if isinstance(val, (list, np.ndarray)):
                        if len(val) > 0:
                            group_data_for_div[group].append(float(np.mean(val)))
                    elif val is not None and not np.isnan(val):
                        group_data_for_div[group].append(float(val))
        else:
            # No group info available, treat as single group
            flat_values = []
            for val in metric_values:
                if isinstance(val, (list, np.ndarray)):
                    if len(val) > 0:
                        flat_values.append(float(np.mean(val)))
                elif val is not None and not np.isnan(val):
                    flat_values.append(float(val))
            
            if flat_values:
                group_data_for_div['All Groups'] = flat_values
                if 'All Groups' not in group_colors:
                    group_colors['All Groups'] = colors[0]
                    group_fill_colors['All Groups'] = fill_colors[0]
        
        # Plot each group separately with different colors
        x_offset = 0
        for group_name, group_values in group_data_for_div.items():
            if not group_values:
                continue
                
            # Calculate KDE data
            kde_data = calculate_half_violin_data(group_values)
            max_y = max(max_y, max(kde_data['raw_data']) if kde_data['raw_data'].size > 0 else 0)
            
            x_base = 1 + x_offset
            color = group_colors[group_name]
            fill_color = group_fill_colors[group_name]
            
            # Add scatter points
            jitter = np.random.normal(0, 0.05, size=len(kde_data['raw_data']))
            fig.add_trace(
                go.Scatter(
                    x=[x_base + j for j in jitter],
                    y=kde_data['raw_data'],
                    mode='markers',
                    marker=dict(color=color, size=5, opacity=0.7),
                    name=group_name,
                    showlegend=(col == 1),  # Only show legend for first subplot
                    hovertemplate=f'{group_name}<br>Value: %{{y:.3f}}<extra></extra>'
                ),
                row=1, col=col
            )
            
            # Add violin
            fig.add_trace(
                go.Violin(
                    x=[x_base] * len(kde_data['x']),
                    y=kde_data['x'],
                    width=0.6,
                    side='positive',
                    line_color=color,
                    fillcolor=fill_color,
                    points=False,
                    meanline_visible=False,
                    opacity=0.5,
                    showlegend=False
                ),
                row=1, col=col
            )
            
            # Add mean line and error bars
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
            
            x_offset += 0.5  # Offset for multiple groups within same DIV
    
    # Update layout
    fig.update_layout(
        title=title,
        height=600,
        margin=dict(l=50, r=50, t=80, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        showlegend=True
    )
    
    # Update axes
    for col in range(1, len(divs) + 1):
        fig.update_xaxes(
            tickvals=[1],
            ticktext=["Groups"],
            row=1, col=col
        )
    
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
        range=[0, max_y * 1.1] if max_y > 0 else None
    )
    
    return fig