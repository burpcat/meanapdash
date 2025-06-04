# components/network_activity.py
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from data_processing.utilities import calculate_half_violin_data

def create_network_half_violin_plot_by_group(data, metric, lag, title, level='node'):
    """
    Create a half violin plot for network metrics by group
    
    Parameters:
    -----------
    data : dict
        Dictionary with network data
    metric : str
        Metric to visualize (using MEA-NAP field names like 'ND', 'NS', 'Dens', etc.)
    lag : int
        Lag value
    title : str
        Plot title
    level : str
        'node' or 'network'
        
    Returns:
    --------
    plotly.graph_objs._figure.Figure
        Plotly figure object
    """
    print(f"\nDEBUG: Creating network half violin plot by group for metric: {metric}, lag: {lag}")
    
    # Debug the data structure
    for group in data['groups']:
        if group in data['by_group']:
            if lag in data['by_group'][group]:
                level_key = 'node_metrics' if level == 'node' else 'network_metrics'
                if level_key in data['by_group'][group][lag]:
                    metrics = list(data['by_group'][group][lag][level_key].keys())
                    print(f"Group {group}, lag {lag} has {level} metrics: {metrics}")
                    
                    if metric in data['by_group'][group][lag][level_key]:
                        values = data['by_group'][group][lag][level_key][metric]
                        print(f"  Found {len(values)} {metric} values for group {group}")
                        if values:
                            print(f"    Sample values: {values[:min(3, len(values))]}, type: {type(values[0]) if values else 'None'}")
                    else:
                        print(f"  Metric {metric} not found in group {group}")
    
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
        if group not in data['by_group']:
            print(f"Group {group} not found in data")
            continue
            
        if lag not in data['by_group'][group]:
            print(f"Lag {lag} not found in group {group}")
            continue
        
        level_key = 'node_metrics' if level == 'node' else 'network_metrics'
        group_data = data['by_group'][group][lag][level_key]
        
        if metric not in group_data:
            print(f"Metric {metric} not found in group {group} at lag {lag}")
            continue
        
        # Make sure we're working with a list
        values = group_data[metric]
        if isinstance(values, np.ndarray):
            values = values.tolist()
        elif not isinstance(values, list):
            values = [values]
            
        # Filter out NaN and inf values
        filtered_values = [v for v in values if v is not None and np.isfinite(v)]
        
        if not filtered_values:
            print(f"No valid values for group {group}")
            continue
            
        # Split values by DIV
        divs = sorted(data['divs'])
        
        # Try extracting experiment names if available
        exp_names = []
        if 'exp_names' in group_data:
            exp_names = group_data['exp_names']
        
        for div_idx, div in enumerate(divs):
            div_values = []
            
            if exp_names:
                # Filter values by DIV using experiment names
                for i, exp_name in enumerate(exp_names):
                    if i < len(filtered_values) and any(f'DIV{div}' in part for part in exp_name.split('_')):
                        div_values.append(filtered_values[i])
            else:
                # No experiment names - split values evenly across DIVs
                # (This is a fallback and may not be accurate)
                div_values = filtered_values
            
            if not div_values:
                continue
                
            # Calculate KDE data
            kde_data = calculate_half_violin_data(div_values)
            
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
    
    # Update y-axes with proper MEA-NAP metric labels
    metric_labels = {
        # Node-level metrics
        'ND': 'Node Degree',
        'NS': 'Node Strength', 
        'MEW': 'Mean Edge Weight',
        'Eloc': 'Local Efficiency',
        'BC': 'Betweenness Centrality',
        'PC': 'Participation Coefficient',
        'Z': 'Within-Module Z-score',
        'aveControl': 'Average Controllability',
        'modalControl': 'Modal Controllability',
        
        # Network-level metrics
        'aN': 'Active Nodes',
        'Dens': 'Network Density',
        'NDmean': 'Mean Node Degree',
        'NDtop25': 'Top 25% Node Degree',
        'sigEdgesMean': 'Mean Significant Edge Weight',
        'sigEdgesTop10': 'Top 10% Edge Weight',
        'NSmean': 'Mean Node Strength',
        'ElocMean': 'Mean Local Efficiency',
        'CC': 'Clustering Coefficient',
        'nMod': 'Number of Modules',
        'Q': 'Modularity',
        'PL': 'Path Length',
        'PCmean': 'Mean Participation Coefficient',
        'Eglob': 'Global Efficiency',
        'SW': 'Small-worldness Sigma',
        'SWw': 'Small-worldness Omega'
    }
    
    fig.update_yaxes(
        title_text=metric_labels.get(metric, metric),
        range=[0, max_y * 1.1] if max_y > 0 else None  # Add 10% padding if we have data
    )
    
    return fig

def create_metrics_by_lag_plot(data, group, metric):
    """
    Create line plots showing network metrics changing across lag values
    
    Parameters:
    -----------
    data : dict
        Dictionary with network data
    group : str
        Group to visualize
    metric : str
        Metric to visualize (using MEA-NAP field names)
        
    Returns:
    --------
    plotly.graph_objs._figure.Figure
        Plotly figure object
    """
    # Create figure
    fig = go.Figure()
    
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
    
    # Get data for the group
    if group not in data['by_group']:
        fig.update_layout(
            title=f"No data available for group {group}",
            height=600
        )
        return fig
    
    group_data = data['by_group'][group]
    divs = sorted(data['divs'])
    lags = sorted(data['lags'])
    
    # Determine if this is a node or network metric
    is_network_metric = metric in ['aN', 'Dens', 'NDmean', 'NDtop25', 'sigEdgesMean', 'sigEdgesTop10', 
                                  'NSmean', 'ElocMean', 'CC', 'nMod', 'Q', 'PL', 'PCmean', 'Eglob', 'SW', 'SWw']
    level_key = 'network_metrics' if is_network_metric else 'node_metrics'
    
    # For each DIV, plot metric across lags
    for div_idx, div in enumerate(divs):
        color = colors[div_idx % len(colors)]
        
        # Collect data points for this DIV
        x_values = []
        y_values = []
        y_errors = []
        
        for lag in lags:
            if lag in group_data and level_key in group_data[lag]:
                lag_data = group_data[lag][level_key]
                
                if metric in lag_data and 'exp_names' in lag_data:
                    # Find experiments for this DIV
                    div_values = []
                    for exp_idx, exp_name in enumerate(lag_data['exp_names']):
                        if any(f'DIV{div}' in part for part in exp_name.split('_')):
                            if exp_idx < len(lag_data[metric]):
                                div_values.append(lag_data[metric][exp_idx])
                    
                    if div_values:
                        # Filter out NaN values
                        div_values = [v for v in div_values if v is not None and np.isfinite(v)]
                        
                        if div_values:
                            x_values.append(lag)
                            y_values.append(np.mean(div_values))
                            y_errors.append(np.std(div_values) / np.sqrt(len(div_values)))  # SEM
        
        if x_values:
            # Add line plot
            fig.add_trace(
                go.Scatter(
                    x=x_values,
                    y=y_values,
                    mode='lines+markers',
                    name=f'DIV {div}',
                    line=dict(color=color, width=2),
                    error_y=dict(
                        type='data',
                        array=y_errors,
                        visible=True
                    )
                )
            )
    
    # Update layout with proper MEA-NAP metric labels
    metric_labels = {
        # Network-level metrics
        'aN': 'Active Nodes',
        'Dens': 'Network Density',
        'NDmean': 'Mean Node Degree',
        'NDtop25': 'Top 25% Node Degree',
        'sigEdgesMean': 'Mean Significant Edge Weight',
        'sigEdgesTop10': 'Top 10% Edge Weight',
        'NSmean': 'Mean Node Strength',
        'ElocMean': 'Mean Local Efficiency',
        'CC': 'Clustering Coefficient',
        'nMod': 'Number of Modules',
        'Q': 'Modularity',
        'PL': 'Path Length',
        'PCmean': 'Mean Participation Coefficient',
        'Eglob': 'Global Efficiency',
        'SW': 'Small-worldness Sigma',
        'SWw': 'Small-worldness Omega',
        
        # Node-level metrics
        'ND': 'Node Degree',
        'NS': 'Node Strength', 
        'MEW': 'Mean Edge Weight',
        'Eloc': 'Local Efficiency',
        'BC': 'Betweenness Centrality',
        'PC': 'Participation Coefficient',
        'Z': 'Within-Module Z-score',
        'aveControl': 'Average Controllability',
        'modalControl': 'Modal Controllability'
    }
    
    fig.update_layout(
        title=f"{metric_labels.get(metric, metric)} by Lag Value for Group {group}",
        xaxis_title="Lag (ms)",
        yaxis_title=metric_labels.get(metric, metric),
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
    
    return fig

def create_node_cartography_plot(data, group, lag, div=None):
    """
    Create node cartography plot
    
    Parameters:
    -----------
    data : dict
        Dictionary with node cartography data
    group : str
        Group to visualize
    lag : int
        Lag value
    div : int, optional
        DIV to visualize. If None, plots role proportions across DIVs
        
    Returns:
    --------
    plotly.graph_objs._figure.Figure
        Plotly figure object
    """
    if div is None:
        # Create role proportions plot
        fig = go.Figure()
        
        # Role colors
        role_colors = {
            'Peripheral': 'rgba(204, 230, 79, 0.7)',
            'Non-hub connector': 'rgba(148, 180, 71, 0.7)',
            'Non-hub kinless': 'rgba(94, 111, 31, 0.7)',
            'Provincial hub': 'rgba(51, 186, 242, 0.7)',
            'Connector hub': 'rgba(20, 108, 213, 0.7)',
            'Kinless hub': 'rgba(4, 60, 127, 0.7)'
        }
        
        # Get data for the group and lag
        if group not in data['by_group'] or lag not in data['by_group'][group]:
            fig.update_layout(
                title=f"No cartography data available for Group {group}, Lag {lag} ms",
                height=400
            )
            return fig
        
        group_data = data['by_group'][group][lag]
        divs = sorted(data['divs'])
        
        # For each role, plot proportion across DIVs
        for role, color in role_colors.items():
            # Collect data points for this role
            x_values = []
            y_values = []
            
            for div in divs:
                # Find experiments for this DIV
                div_props = []
                
                for exp_name in data['by_experiment']:
                    exp_data = data['by_experiment'][exp_name]
                    
                    # Check if this experiment matches the group and DIV
                    if exp_data.get('group') == group and exp_data.get('div') == div:
                        if 'lags' in exp_data and lag in exp_data['lags']:
                            cart_data = exp_data['lags'][lag]
                            
                            if 'roles' in cart_data:
                                roles = cart_data['roles']
                                if isinstance(roles, np.ndarray):
                                    roles = roles.flatten()
                                
                                total_nodes = len(roles)
                                role_count = sum(1 for r in roles if r == role)
                                
                                if total_nodes > 0:
                                    div_props.append(role_count / total_nodes)
                
                if div_props:
                    x_values.append(div)
                    y_values.append(np.mean(div_props))
            
            if x_values:
                # Add line plot
                fig.add_trace(
                    go.Scatter(
                        x=x_values,
                        y=y_values,
                        mode='lines+markers',
                        name=role,
                        line=dict(color=color, width=2)
                    )
                )
        
        # Update layout
        fig.update_layout(
            title=f"Node Role Proportions by Age for Group {group} (Lag: {lag} ms)",
            xaxis_title="DIV",
            yaxis_title="Proportion of Nodes",
            height=400,
            margin=dict(l=50, r=50, t=80, b=50),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            yaxis=dict(
                range=[0, 1]
            )
        )
        
        return fig
    
    else:
        # Create node cartography scatter plot for specific DIV
        fig = go.Figure()
        
        # Role colors
        role_colors = {
            'Peripheral': 'rgba(204, 230, 79, 0.7)',
            'Non-hub connector': 'rgba(148, 180, 71, 0.7)',
            'Non-hub kinless': 'rgba(94, 111, 31, 0.7)',
            'Provincial hub': 'rgba(51, 186, 242, 0.7)',
            'Connector hub': 'rgba(20, 108, 213, 0.7)',
            'Kinless hub': 'rgba(4, 60, 127, 0.7)'
        }
        
        # Initialize cart_data to avoid UnboundLocalError
        cart_data = {}
        found_data = False
        
        # Get experiments matching this group and DIV
        for exp_name in data['by_experiment']:
            exp_data = data['by_experiment'][exp_name]
            
            # Check if this experiment matches the group and DIV
            if exp_data.get('group') == group and exp_data.get('div') == div:
                if 'lags' in exp_data and lag in exp_data['lags']:
                    cart_data = exp_data['lags'][lag]
                    found_data = True
                    
                    # Use Z and PC (MEA-NAP field names) for scatter plot
                    if 'PC' in cart_data and 'Z' in cart_data and 'roles' in cart_data:
                        pc = cart_data['PC'].flatten() if isinstance(cart_data['PC'], np.ndarray) else [cart_data['PC']]
                        z = cart_data['Z'].flatten() if isinstance(cart_data['Z'], np.ndarray) else [cart_data['Z']]
                        roles = cart_data['roles'].flatten() if isinstance(cart_data['roles'], np.ndarray) else [cart_data['roles']]
                        
                        # Add data points by role
                        for role in set(roles):
                            if role in role_colors:
                                role_indices = [i for i, r in enumerate(roles) if r == role]
                                
                                if role_indices:
                                    fig.add_trace(
                                        go.Scatter(
                                            x=[pc[i] for i in role_indices],
                                            y=[z[i] for i in role_indices],
                                            mode='markers',
                                            name=role,
                                            marker=dict(
                                                color=role_colors[role],
                                                size=10,
                                                opacity=0.7
                                            )
                                        )
                                    )
        
        # Add boundaries if available AND data was found
        if found_data and 'boundaries' in cart_data:
            boundaries = cart_data['boundaries']
            
            # Horizontal line for hub boundary
            if 'hubBoundaryWMdDeg' in boundaries:
                z_boundary = boundaries['hubBoundaryWMdDeg']
                fig.add_shape(
                    type="line",
                    x0=0, x1=1,
                    y0=z_boundary, y1=z_boundary,
                    line=dict(color="black", width=1, dash="dash")
                )
                
                # Add text label
                fig.add_annotation(
                    x=0.02, y=z_boundary + 0.1,
                    text="Hub boundary",
                    showarrow=False,
                    font=dict(size=10)
                )
            
            # Vertical lines for participation coefficient boundaries
            for boundary, value in [
                ('periPartCoef', 'Peripheral / Non-hub connector'),
                ('nonHubconnectorPartCoef', 'Non-hub connector / Non-hub kinless'),
                ('proHubpartCoef', 'Provincial hub / Connector hub'),
                ('connectorHubPartCoef', 'Connector hub / Kinless hub')
            ]:
                if boundary in boundaries:
                    p_boundary = boundaries[boundary]
                    fig.add_shape(
                        type="line",
                        x0=p_boundary, x1=p_boundary,
                        y0=0, y1=4,  # Adjust as needed
                        line=dict(color="black", width=1, dash="dash")
                    )
        
        # Update layout
        fig.update_layout(
            title=f"Node Cartography for Group {group}, DIV {div} (Lag: {lag} ms)",
            xaxis_title="Participation Coefficient (PC)",
            yaxis_title="Within-module Degree Z-score (Z)",
            height=600,
            margin=dict(l=50, r=50, t=80, b=50),
            xaxis=dict(range=[0, 1]),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig