# components/network_activity.py - Enhanced Network Visualizations - VERIFIED
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from data_processing.utilities import calculate_half_violin_data

# Modern, accessible color palette (matching neuronal_activity.py)
MODERN_COLORS = {
    'age_50': '#FF6B6B',      # Coral red
    'age_53': '#4ECDC4',      # Teal
    'groups': [
        '#FF6B6B',  # Coral
        '#4ECDC4',  # Teal  
        '#45B7D1',  # Sky blue
        '#96CEB4',  # Mint green
        '#FFEAA7',  # Warm yellow
        '#DDA0DD',  # Plum
        '#98D8C8',  # Seafoam
        '#F7DC6F'   # Light gold
    ],
    'neutral': '#7F8C8D',
    'background': '#FAFAFA',
    'text': '#2C3E50'
}

def determine_plot_style(data_count):
    """Determine the best plot style based on data density"""
    if data_count == 0:
        return 'empty'
    elif data_count == 1:
        return 'single_point'
    elif data_count <= 3:
        return 'scatter_only'
    elif data_count <= 8:
        return 'box_plot'
    else:
        return 'violin_plot'

def create_enhanced_network_half_violin_plot_by_group(data, metric, lag, title, level='node'):
    """
    Create an enhanced half violin plot for network metrics by group with adaptive visualization
    """
    # print(f"\nDEBUG: Creating enhanced network half violin plot by group for metric: {metric}, lag: {lag}")
    
    groups = data['groups']
    divs = sorted(data['divs'])
    
    # Create figure with enhanced styling
    fig = make_subplots(
        rows=1, cols=len(groups), 
        subplot_titles=[f'<b>{g}</b>' for g in groups],
        shared_yaxes=True,
        horizontal_spacing=0.08
    )
    
    max_y = 0
    min_y = float('inf')
    legend_added = {'DIV 50': False, 'DIV 53': False}
    
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
        
        # Process metric values
        values = group_data[metric]
        if isinstance(values, np.ndarray):
            values = values.tolist()
        elif not isinstance(values, list):
            values = [values]
        
        # Filter out invalid values
        filtered_values = [v for v in values if v is not None and np.isfinite(v)]
        if not filtered_values:
            print(f"No valid values for group {group}")
            continue
        
        # Get experiment names for DIV filtering
        exp_names = group_data.get('exp_names', [])
        
        for div_idx, div in enumerate(divs):
            div_values = []
            
            if exp_names:
                # Filter values by DIV using experiment names
                for i, exp_name in enumerate(exp_names):
                    if i < len(filtered_values) and any(f'DIV{div}' in part for part in exp_name.split('_')):
                        div_values.append(filtered_values[i])
            else:
                # No experiment names - use all values (fallback)
                div_values = filtered_values
            
            if len(div_values) == 0:
                continue
            
            # Update y-axis range
            max_y = max(max_y, max(div_values))
            min_y = min(min_y, min(div_values))
            
            # Determine visualization style
            plot_style = determine_plot_style(len(div_values))
            color = MODERN_COLORS['age_50'] if div == 50 else MODERN_COLORS['age_53']
            div_label = f'DIV {div}'
            x_base = div_idx + 1
            
            if plot_style == 'single_point':
                # Single point with emphasis
                fig.add_trace(
                    go.Scatter(
                        x=[x_base],
                        y=div_values,
                        mode='markers',
                        marker=dict(
                            color=color,
                            size=14,
                            line=dict(width=2, color='white'),
                            opacity=0.9
                        ),
                        name=div_label,
                        legendgroup=div_label,
                        showlegend=not legend_added[div_label],
                        hovertemplate=f'{div_label}<br>Value: %{{y:.4f}}<extra></extra>'
                    ),
                    row=1, col=col
                )
                legend_added[div_label] = True
                
            elif plot_style == 'scatter_only':
                # Enhanced scatter for few points
                jitter = np.random.normal(0, 0.08, size=len(div_values))
                fig.add_trace(
                    go.Scatter(
                        x=[x_base + j for j in jitter],
                        y=div_values,
                        mode='markers',
                        marker=dict(
                            color=color,
                            size=10,
                            line=dict(width=1, color='white'),
                            opacity=0.8
                        ),
                        name=div_label,
                        legendgroup=div_label,
                        showlegend=not legend_added[div_label],
                        hovertemplate=f'{div_label}<br>Value: %{{y:.4f}}<extra></extra>'
                    ),
                    row=1, col=col
                )
                legend_added[div_label] = True
                
                # Add mean line
                mean_val = np.mean(div_values)
                fig.add_trace(
                    go.Scatter(
                        x=[x_base - 0.15, x_base + 0.15],
                        y=[mean_val, mean_val],
                        mode='lines',
                        line=dict(color=color, width=3),
                        showlegend=False,
                        hovertemplate=f'Mean: {mean_val:.4f}<extra></extra>'
                    ),
                    row=1, col=col
                )
                
            elif plot_style == 'box_plot':
                # Enhanced box plot for medium data
                fig.add_trace(
                    go.Box(
                        x=[div_label] * len(div_values),
                        y=div_values,
                        name=div_label,
                        legendgroup=div_label,
                        showlegend=not legend_added[div_label],
                        marker_color=color,
                        line_color=color,
                        fillcolor=color.replace(')', ', 0.3)').replace('rgb', 'rgba') if 'rgb' in color else color + '4D',
                        boxpoints='all',
                        jitter=0.3,
                        pointpos=-1.8 if div == 50 else 1.8,
                        hoverton='all'
                    ),
                    row=1, col=col
                )
                legend_added[div_label] = True
                
            else:  # violin_plot
                # Enhanced violin plot for rich data
                kde_data = calculate_half_violin_data(div_values)
                
                # Add individual points with smart jitter
                jitter = np.random.normal(0, 0.05, size=len(div_values))
                fig.add_trace(
                    go.Scatter(
                        x=[x_base + j for j in jitter],
                        y=div_values,
                        mode='markers',
                        marker=dict(
                            color=color,
                            size=6,
                            opacity=0.7,
                            line=dict(width=0.5, color='white')
                        ),
                        name=div_label,
                        legendgroup=div_label,
                        showlegend=not legend_added[div_label],
                        hovertemplate=f'{div_label}<br>Value: %{{y:.4f}}<extra></extra>'
                    ),
                    row=1, col=col
                )
                legend_added[div_label] = True
                
                # Add enhanced violin
                fig.add_trace(
                    go.Violin(
                        x=[x_base] * len(kde_data['x']),
                        y=kde_data['x'],
                        width=0.6,
                        side='positive',
                        line_color=color,
                        fillcolor=color.replace(')', ', 0.4)').replace('rgb', 'rgba') if 'rgb' in color else color + '66',
                        points=False,
                        meanline_visible=False,
                        showlegend=False,
                        hoverinfo='skip'
                    ),
                    row=1, col=col
                )
                
                # Enhanced mean and confidence interval
                mean_val = kde_data['mean']
                sem_val = kde_data['sem']
                
                # Mean line
                fig.add_trace(
                    go.Scatter(
                        x=[x_base - 0.2, x_base + 0.3],
                        y=[mean_val, mean_val],
                        mode='lines',
                        line=dict(color='#2C3E50', width=3),
                        showlegend=False,
                        hovertemplate=f'Mean: {mean_val:.4f}<extra></extra>'
                    ),
                    row=1, col=col
                )
                
                # Confidence interval
                fig.add_trace(
                    go.Scatter(
                        x=[x_base, x_base],
                        y=[mean_val - sem_val, mean_val + sem_val],
                        mode='lines',
                        line=dict(color='#2C3E50', width=2),
                        showlegend=False,
                        hovertemplate=f'95% CI<extra></extra>'
                    ),
                    row=1, col=col
                )
    
    # Enhanced layout with modern styling
    fig.update_layout(
        title=dict(
            text=f'<b>{title}</b>',
            x=0.5,
            font=dict(size=18, color=MODERN_COLORS['text'])
        ),
        height=650,
        plot_bgcolor='white',
        paper_bgcolor=MODERN_COLORS['background'],
        margin=dict(l=60, r=60, t=100, b=80),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.1)',
            borderwidth=1
        ),
        font=dict(
            family="Inter, system-ui, sans-serif",
            size=12,
            color=MODERN_COLORS['text']
        )
    )
    
    # Update x-axes with better styling
    for col in range(1, len(groups) + 1):
        fig.update_xaxes(
            tickvals=list(range(1, len(divs) + 1)),
            ticktext=[f'<b>DIV {div}</b>' for div in divs],
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor='rgba(0,0,0,0.1)',
            row=1, col=col
        )
    
    # Update y-axis with better styling
    y_range = max_y - min_y if min_y != float('inf') else max_y
    y_padding = y_range * 0.1 if y_range > 0 else max_y * 0.1
    
    fig.update_yaxes(
        title_text=get_network_metric_label(metric),
        title_font=dict(size=14, color=MODERN_COLORS['text']),
        range=[max(0, min_y - y_padding), max_y + y_padding] if min_y != float('inf') else [0, max_y * 1.1],
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(0,0,0,0.1)',
        showline=True,
        linewidth=1,
        linecolor='rgba(0,0,0,0.1)',
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor='rgba(0,0,0,0.2)'
    )
    
    return fig

def create_enhanced_metrics_by_lag_plot(data, group, metric):
    """
    Create enhanced line plots showing network metrics changing across lag values
    """
    # Create figure with modern styling
    fig = go.Figure()
    
    # Get data for the group
    if group not in data['by_group']:
        fig.update_layout(
            title=f"<b>No data available for group {group}</b>",
            height=600,
            plot_bgcolor='white',
            paper_bgcolor=MODERN_COLORS['background'],
            font=dict(family="Inter, system-ui, sans-serif", color=MODERN_COLORS['text'])
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
        color = MODERN_COLORS['groups'][div_idx % len(MODERN_COLORS['groups'])]
        
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
                    
                    if len(div_values) > 0:
                        # Filter out NaN values
                        div_values = [v for v in div_values if v is not None and np.isfinite(v)]
                        
                        if len(div_values) > 0:
                            x_values.append(lag)
                            y_values.append(np.mean(div_values))
                            y_errors.append(np.std(div_values) / np.sqrt(len(div_values)))  # SEM
        
        if x_values:
            # Add enhanced line plot
            fig.add_trace(
                go.Scatter(
                    x=x_values,
                    y=y_values,
                    mode='lines+markers',
                    name=f'DIV {div}',
                    line=dict(color=color, width=3),
                    marker=dict(
                        color=color,
                        size=8,
                        line=dict(width=1, color='white')
                    ),
                    error_y=dict(
                        type='data',
                        array=y_errors,
                        visible=True,
                        color=color,
                        thickness=2,
                        width=4
                    ),
                    hovertemplate=f'DIV {div}<br>Lag: %{{x}} ms<br>Value: %{{y:.4f}}<extra></extra>'
                )
            )
    
    # Enhanced layout
    fig.update_layout(
        title=dict(
            text=f'<b>{get_network_metric_label(metric)} by Lag Value for Group {group}</b>',
            x=0.5,
            font=dict(size=18, color=MODERN_COLORS['text'])
        ),
        xaxis_title="<b>Lag (ms)</b>",
        yaxis_title=f"<b>{get_network_metric_label(metric)}</b>",
        height=650,
        plot_bgcolor='white',
        paper_bgcolor=MODERN_COLORS['background'],
        margin=dict(l=60, r=60, t=100, b=80),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.1)',
            borderwidth=1
        ),
        font=dict(
            family="Inter, system-ui, sans-serif",
            size=12,
            color=MODERN_COLORS['text']
        )
    )
    
    # Enhanced axes styling
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(0,0,0,0.1)',
        showline=True,
        linewidth=1,
        linecolor='rgba(0,0,0,0.1)'
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(0,0,0,0.1)',
        showline=True,
        linewidth=1,
        linecolor='rgba(0,0,0,0.1)',
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor='rgba(0,0,0,0.2)'
    )
    
    return fig

def create_enhanced_node_cartography_plot(data, group, lag, div=None):
    """
    Create enhanced node cartography plot with modern styling
    """
    if div is None:
        # Create role proportions plot
        fig = go.Figure()
        
        # Enhanced role colors
        role_colors = {
            'Peripheral': '#FF6B6B',
            'Non-hub connector': '#4ECDC4',
            'Non-hub kinless': '#45B7D1',
            'Provincial hub': '#96CEB4',
            'Connector hub': '#FFEAA7',
            'Kinless hub': '#DDA0DD'
        }
        
        # Get data for the group and lag
        if group not in data['by_group'] or lag not in data['by_group'][group]:
            fig.update_layout(
                title=f"<b>No cartography data available for Group {group}, Lag {lag} ms</b>",
                height=500,
                plot_bgcolor='white',
                paper_bgcolor=MODERN_COLORS['background'],
                font=dict(family="Inter, system-ui, sans-serif", color=MODERN_COLORS['text'])
            )
            return fig
        
        group_data = data['by_group'][group][lag]
        divs = sorted(data['divs'])
        
        # For each role, plot proportion across DIVs
        for role, color in role_colors.items():
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
                # Add enhanced line plot
                fig.add_trace(
                    go.Scatter(
                        x=x_values,
                        y=y_values,
                        mode='lines+markers',
                        name=role,
                        line=dict(color=color, width=3),
                        marker=dict(
                            color=color,
                            size=8,
                            line=dict(width=1, color='white')
                        ),
                        hovertemplate=f'{role}<br>DIV: %{{x}}<br>Proportion: %{{y:.3f}}<extra></extra>'
                    )
                )
        
        # Enhanced layout
        fig.update_layout(
            title=dict(
                text=f'<b>Node Role Proportions by Age for Group {group} (Lag: {lag} ms)</b>',
                x=0.5,
                font=dict(size=18, color=MODERN_COLORS['text'])
            ),
            xaxis_title="<b>DIV</b>",
            yaxis_title="<b>Proportion of Nodes</b>",
            height=500,
            plot_bgcolor='white',
            paper_bgcolor=MODERN_COLORS['background'],
            margin=dict(l=60, r=60, t=100, b=80),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='rgba(0,0,0,0.1)',
                borderwidth=1
            ),
            yaxis=dict(range=[0, 1]),
            font=dict(
                family="Inter, system-ui, sans-serif",
                size=12,
                color=MODERN_COLORS['text']
            )
        )
        
        return fig
    
    else:
        # Create node cartography scatter plot for specific DIV
        # Implementation would be similar but for scatter plot
        # For brevity, returning placeholder
        fig = go.Figure()
        fig.update_layout(
            title=f"<b>Node Cartography Scatter Plot - Coming Soon</b>",
            height=600,
            plot_bgcolor='white',
            paper_bgcolor=MODERN_COLORS['background'],
            font=dict(family="Inter, system-ui, sans-serif", color=MODERN_COLORS['text'])
        )
        return fig

def get_network_metric_label(metric):
    """Get proper network metric labels with units"""
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
    
    return metric_labels.get(metric, metric)

# Update function names for compatibility
create_network_half_violin_plot_by_group = create_enhanced_network_half_violin_plot_by_group
create_metrics_by_lag_plot = create_enhanced_metrics_by_lag_plot
create_node_cartography_plot = create_enhanced_node_cartography_plot