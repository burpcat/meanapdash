# components/neuronal_activity.py - REFACTORED VERSION - Simplified and Modular
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from data_processing.utilities import calculate_half_violin_data, extract_div_value
from utils.config import is_sparse_metric
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION - MEA-NAP MATLAB Style Colors and Settings
# =============================================================================

# MEA-NAP MATLAB color scheme
MATLAB_COLORS = {
    50: '#FFD700',    # Yellow for DIV 50
    53: '#8A2BE2',    # Purple for DIV 53
    'default': '#1f77b4'  # Default blue
}

MATLAB_FILL_COLORS = {
    50: 'rgba(255, 215, 0, 0.6)',      # Yellow with transparency
    53: 'rgba(138, 43, 226, 0.6)',    # Purple with transparency
    'default': 'rgba(31, 119, 180, 0.6)'  # Default blue with transparency
}

# Standard plot configuration
PLOT_CONFIG = {
    'height': 500,
    'plot_bgcolor': 'white',
    'paper_bgcolor': 'white',
    'font_family': 'Arial',
    'font_size': 12,
    'font_color': 'black',
    'grid_color': 'rgba(200,200,200,0.5)',
    'line_color': 'black',
    'line_width': 1
}

# =============================================================================
# UTILITY FUNCTIONS - Data Processing and Preparation
# =============================================================================

def prepare_data_for_plotting(data, metric, groups, selected_divs):
    """
    Prepare data for plotting by extracting and organizing values by group and DIV
    FIXED: Handle numpy array boolean comparisons properly
    """
    print(f"🔧 Preparing data for plotting: {metric}")
    
    # Filter groups and DIVs
    if groups:
        filtered_groups = [g for g in groups if g in data['groups']]
    else:
        filtered_groups = data['groups']
    
    if selected_divs:
        filtered_divs = [d for d in selected_divs if d in data['divs']]
    else:
        filtered_divs = sorted(data['divs'])
    
    # Organize data by group and DIV
    plot_data = {}
    
    for group in filtered_groups:
        if group not in data['by_group']:
            continue
            
        group_data = data['by_group'][group]
        if metric not in group_data:
            continue
        
        plot_data[group] = {}
        
        # For each DIV, extract the relevant data
        for div in filtered_divs:
            div_values = []
            
            # Check if this is recording-level data (has exp_names)
            if 'exp_names' in group_data and len(group_data['exp_names']) > 0:
                # Extract values for this specific DIV
                for i, exp_name in enumerate(group_data['exp_names']):
                    if any(f'DIV{div}' in part for part in exp_name.split('_')):
                        if i < len(group_data[metric]):
                            value = group_data[metric][i]
                            if isinstance(value, (list, np.ndarray)):
                                div_values.extend(value)
                            else:
                                div_values.append(value)
                
                # If no DIV-specific data found, use all data (fallback)
                if len(div_values) == 0:  # FIXED: use len() instead of not
                    div_values = group_data[metric]
            else:
                # For electrode-level data, use all values
                div_values = group_data[metric]
            
            # Clean the data - FIXED: Proper handling of arrays
            if isinstance(div_values, (list, np.ndarray)):
                if isinstance(div_values, np.ndarray):
                    div_values = div_values.tolist()  # Convert to list for consistency
                clean_values = [v for v in div_values if v is not None and np.isfinite(v)]
            else:
                clean_values = [div_values] if div_values is not None and np.isfinite(div_values) else []
            
            plot_data[group][div] = clean_values
    
    return plot_data, filtered_groups, filtered_divs

def get_metric_label(metric):
    """Get proper metric labels with units"""
    metric_labels = {
        'FR': 'Firing Rate (Hz)',
        'FRActiveNode': 'Mean Firing Rate Active Node (Hz)',
        'channelBurstRate': 'Burst Rate (per minute)',
        'channelBurstDur': 'Burst Duration (ms)',
        'channelISIwithinBurst': 'ISI Within Burst (ms)',
        'channeISIoutsideBurst': 'ISI Outside Burst (ms)',
        'channelFracSpikesInBursts': 'Fraction Spikes in Bursts',
        'channelFRinBurst': 'Within-Burst Firing Rate (Hz)',
        'numActiveElec': 'Number of Active Electrodes',
        'FRmean': 'Mean Firing Rate (Hz)',
        'FRmedian': 'Median Firing Rate (Hz)',
        'NBurstRate': 'Network Burst Rate (per minute)',
        'meanNumChansInvolvedInNbursts': 'Mean Channels in Network Bursts',
        'meanNBstLengthS': 'Mean Network Burst Length (s)',
        'meanISIWithinNbursts_ms': 'Mean ISI Within Network Bursts (ms)',
        'meanISIoutsideNbursts_ms': 'Mean ISI Outside Network Bursts (ms)',
        'CVofINBI': 'CV of Inter-Network-Burst Intervals',
        'fracInNburst': 'Fraction of Spikes in Network Bursts'
    }
    
    return metric_labels.get(metric, metric)

# =============================================================================
# PLOT TYPE FUNCTIONS - Individual plot creators
# =============================================================================

def create_violin_plot_by_group(plot_data, filtered_groups, filtered_divs, metric, title):
    """Create violin plot that properly handles sparse data and displays graphs correctly"""
    
    fig = make_subplots(
        rows=1, cols=len(filtered_groups), 
        subplot_titles=[f'<b>{g}</b>' for g in filtered_groups],
        shared_yaxes=True,
        horizontal_spacing=0.08
    )
    
    max_y = 0
    is_sparse_metric_flag = is_sparse_metric(metric)
    total_data_points = 0
    
    # Track which groups have data for empty group handling
    groups_with_data = set()
    
    for col, group in enumerate(filtered_groups, 1):
        group_has_data = False
        
        if group not in plot_data:
            continue
            
        for div_idx, div in enumerate(filtered_divs):
            if div not in plot_data[group]:
                continue
                
            div_values = plot_data[group][div]
            # FIXED: Handle empty data properly
            if not isinstance(div_values, list) or len(div_values) == 0:
                continue
            
            # Mark this group as having data
            group_has_data = True
            groups_with_data.add(group)
            
            # FIXED: Safe max calculation
            try:
                current_max = max(div_values)
                max_y = max(max_y, current_max)
                total_data_points += len(div_values)
            except (ValueError, TypeError):
                continue
            
            # Get colors
            color = MATLAB_COLORS.get(div, MATLAB_COLORS['default'])
            fill_color = MATLAB_FILL_COLORS.get(div, MATLAB_FILL_COLORS['default'])
            
            x_base = div_idx + 1
            
            # ENHANCED SPARSE DATA HANDLING
            if len(div_values) <= 2:
                # VERY SPARSE: Large, prominent dots
                jitter = np.random.normal(0, 0.08, size=len(div_values))
                fig.add_trace(
                    go.Scatter(
                        x=[x_base + j for j in jitter],
                        y=div_values,
                        mode='markers',
                        marker=dict(
                            color=color,
                            size=12,  # Large dots
                            opacity=0.9,
                            line=dict(width=3, color='black'),
                            symbol='diamond'  # Diamond shape for visibility
                        ),
                        name=f'DIV {div}',
                        legendgroup=f'DIV {div}',
                        showlegend=(col == 1),
                        hovertemplate=f'<b>{group} - DIV {div}</b><br>Value: %{{y:.3f}}<br>n={len(div_values)}<extra></extra>'
                    ),
                    row=1, col=col
                )
                
                # Add sample size annotation
                fig.add_annotation(
                    x=x_base,
                    y=max(div_values) + max_y * 0.02,
                    text=f'<b>n={len(div_values)}</b>',
                    showarrow=False,
                    font=dict(size=11, color='darkred'),
                    yshift=15,
                    row=1, col=col
                )
                
            elif len(div_values) <= 5:
                # SPARSE: Medium dots with more spacing
                jitter = np.random.normal(0, 0.06, size=len(div_values))
                fig.add_trace(
                    go.Scatter(
                        x=[x_base + j for j in jitter],
                        y=div_values,
                        mode='markers',
                        marker=dict(
                            color=color,
                            size=10,  # Medium dots
                            opacity=0.8,
                            line=dict(width=2, color='black'),
                            symbol='circle'
                        ),
                        name=f'DIV {div}',
                        legendgroup=f'DIV {div}',
                        showlegend=(col == 1),
                        hovertemplate=f'<b>{group} - DIV {div}</b><br>Value: %{{y:.3f}}<br>n={len(div_values)}<extra></extra>'
                    ),
                    row=1, col=col
                )
                
                # Add sample size annotation
                fig.add_annotation(
                    x=x_base,
                    y=max(div_values) + max_y * 0.02,
                    text=f'n={len(div_values)}',
                    showarrow=False,
                    font=dict(size=10, color='gray'),
                    yshift=12,
                    row=1, col=col
                )
            
            else:
                # NORMAL DATA: Standard visualization with individual points
                jitter = np.random.normal(0, 0.04, size=len(div_values))
                fig.add_trace(
                    go.Scatter(
                        x=[x_base + j for j in jitter],
                        y=div_values,
                        mode='markers',
                        marker=dict(color='black', size=4, opacity=0.6),
                        name=f'DIV {div}',
                        legendgroup=f'DIV {div}',
                        showlegend=(col == 1),
                        hovertemplate=f'<b>{group} - DIV {div}</b><br>Value: %{{y:.3f}}<br>n={len(div_values)}<extra></extra>'
                    ),
                    row=1, col=col
                )
                
                # Add violin for rich data
                if len(div_values) >= 4:
                    try:
                        kde_data = calculate_half_violin_data(div_values)
                        x_data = kde_data.get('x')
                        if x_data is not None and hasattr(x_data, '__len__') and len(x_data) > 0:
                            if isinstance(x_data, np.ndarray):
                                x_data = x_data.tolist()
                            
                            fig.add_trace(
                                go.Violin(
                                    x=[x_base] * len(x_data),
                                    y=x_data,
                                    width=0.6,
                                    side='both',
                                    line_color=color,
                                    fillcolor=fill_color,
                                    points=False,
                                    meanline_visible=False,
                                    showlegend=False,
                                    hoverinfo='skip'
                                ),
                                row=1, col=col
                            )
                    except Exception as e:
                        print(f"⚠️ Violin plot failed for {group} DIV {div}: {e}")
            
            # Add mean indicator (always visible)
            try:
                mean_value = np.mean(div_values)
                fig.add_trace(
                    go.Scatter(
                        x=[x_base],
                        y=[mean_value],
                        mode='markers',
                        marker=dict(
                            color='white',  # White center
                            size=8 if len(div_values) <= 5 else 6,
                            opacity=1.0,
                            line=dict(width=2, color='black')  # Black outline
                        ),
                        showlegend=False,
                        hovertemplate=f'<b>Mean: {mean_value:.3f}</b><br>n={len(div_values)}<extra></extra>'
                    ),
                    row=1, col=col
                )
            except Exception as e:
                print(f"⚠️ Mean calculation failed for {group} DIV {div}: {e}")
    
    # NEW: Add "No Data" annotations for empty groups
    for col, group in enumerate(filtered_groups, 1):
        if group not in groups_with_data:
            # Calculate y position for "No Data" text
            y_center = (max_y / 2) if max_y > 0 else 0.5
            
            fig.add_annotation(
                x=1.5,  # Center between DIV positions
                y=y_center,
                text="<b>No Data</b>",
                showarrow=False,
                font=dict(size=16, color='lightgray'),
                row=1, col=col
            )
    
    # FIXED: Better layout with proper spacing and titles
    annotations = []
    if is_sparse_metric_flag and total_data_points > 0:
        annotations.append(
            dict(
                text="Note: Sparse data is expected for burst metrics due to conservative detection settings",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.5, y=-0.15,
                font=dict(size=10, color='gray'),
                align="center"
            )
        )
    
    fig.update_layout(
        title=dict(text=f'<b>{title}</b>', x=0.5, font=dict(size=16, color='black')),
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Arial', size=12, color='black'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        annotations=annotations,
        margin=dict(b=100 if is_sparse_metric_flag else 60, t=100, l=60, r=60)  # INCREASED top margin for titles
    )
    
    # FIXED: Better axis handling with outlier detection
    # Collect all values to detect outliers
    all_values = []
    for group in plot_data:
        for div in plot_data[group]:
            all_values.extend(plot_data[group][div])
    
    # Calculate reasonable y-axis range (exclude extreme outliers)
    if len(all_values) > 0:
        all_values = sorted(all_values)
        if len(all_values) > 2:
            # Use 95th percentile as max to handle outliers
            p95 = np.percentile(all_values, 95)
            p5 = np.percentile(all_values, 5)
            y_max = p95 * 1.2
            y_min = max(0, p5 * 0.8)
        else:
            y_max = max_y * 1.15
            y_min = 0
    else:
        y_max = 1
        y_min = 0
    
    for col in range(1, len(filtered_groups) + 1):
        fig.update_xaxes(
            tickvals=list(range(1, len(filtered_divs) + 1)),
            ticktext=[str(div) for div in filtered_divs],
            title_text="Age" if col == len(filtered_groups)//2 + 1 else "",
            showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.5)',
            linecolor='black', linewidth=1,
            range=[0.5, len(filtered_divs) + 0.5],
            row=1, col=col
        )
    
    fig.update_yaxes(
        title_text=get_metric_label(metric),
        range=[y_min, y_max],
        showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.5)',
        linecolor='black', linewidth=1,
        zeroline=True, zerolinecolor='rgba(200,200,200,0.5)'
    )
    
    # Add outlier warning if needed
    if len(all_values) > 0 and max_y > y_max:
        outlier_count = len([v for v in all_values if v > y_max])
        fig.add_annotation(
            text=f"⚠️ {outlier_count} extreme outlier(s) excluded from y-axis scale",
            showarrow=False,
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            font=dict(size=9, color='orange'),
            align="left"
        )
    
    return fig

def create_violin_plot_by_age(plot_data, filtered_groups, filtered_divs, metric, title):
    """Create violin plot organized by age (DIV)"""
    
    fig = make_subplots(
        rows=1, cols=len(filtered_groups), 
        subplot_titles=[f'<b>{group}</b>' for group in filtered_groups],
        shared_yaxes=True,
        horizontal_spacing=0.12
    )
    
    max_y = 0
    
    for col, group in enumerate(filtered_groups, 1):
        if group not in plot_data:
            continue
            
        for div in filtered_divs:
            if div not in plot_data[group]:
                continue
                
            div_values = plot_data[group][div]
            if len(div_values) == 0:
                continue
            
            max_y = max(max_y, max(div_values))
            
            # Get colors
            color = MATLAB_COLORS.get(div, MATLAB_COLORS['default'])
            fill_color = MATLAB_FILL_COLORS.get(div, MATLAB_FILL_COLORS['default'])
            
            x_base = div  # Use actual DIV number for x-position
            
            # Add individual points
            jitter = np.random.normal(0, 0.2, size=len(div_values))
            fig.add_trace(
                go.Scatter(
                    x=[x_base + j for j in jitter],
                    y=div_values,
                    mode='markers',
                    marker=dict(color='black', size=3, opacity=0.6),
                    name=f'DIV {div}',
                    legendgroup=f'DIV {div}',
                    showlegend=(col == 1),
                    hovertemplate=f'DIV {div}: %{{y:.2f}}<extra></extra>'
                ),
                row=1, col=col
            )
            
            # Add violin if we have enough data
            if len(div_values) > 3:
                kde_data = calculate_half_violin_data(div_values)
                fig.add_trace(
                    go.Violin(
                        x=[x_base] * len(kde_data['x']),
                        y=kde_data['x'],
                        width=2.5,
                        side='both',
                        line_color=color,
                        fillcolor=fill_color,
                        points=False,
                        meanline_visible=False,
                        showlegend=False,
                        hoverinfo='skip'
                    ),
                    row=1, col=col
                )
            
            # Add mean dot
            fig.add_trace(
                go.Scatter(
                    x=[x_base],
                    y=[np.mean(div_values)],
                    mode='markers',
                    marker=dict(color='black', size=8, opacity=1.0),
                    showlegend=False,
                    hovertemplate=f'Mean: {np.mean(div_values):.2f}<extra></extra>'
                ),
                row=1, col=col
            )
    
    # Update layout
    fig.update_layout(
        title=dict(text=f'<b>{title}</b>', x=0.5, font=dict(size=16, color='black')),
        height=PLOT_CONFIG['height'],
        plot_bgcolor=PLOT_CONFIG['plot_bgcolor'],
        paper_bgcolor=PLOT_CONFIG['paper_bgcolor'],
        font=dict(family=PLOT_CONFIG['font_family'], size=PLOT_CONFIG['font_size'], color=PLOT_CONFIG['font_color']),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Update axes
    for col in range(1, len(filtered_groups) + 1):
        fig.update_xaxes(
            tickvals=filtered_divs,
            ticktext=[str(div) for div in filtered_divs],
            title_text="Age" if col == len(filtered_groups)//2 + 1 else "",
            range=[min(filtered_divs) - 2, max(filtered_divs) + 2],
            showgrid=True, gridwidth=1, gridcolor=PLOT_CONFIG['grid_color'],
            linecolor=PLOT_CONFIG['line_color'], linewidth=PLOT_CONFIG['line_width'],
            row=1, col=col
        )
    
    fig.update_yaxes(
        title_text=get_metric_label(metric),
        range=[0, max_y * 1.1] if max_y > 0 else [0, 1],
        showgrid=True, gridwidth=1, gridcolor=PLOT_CONFIG['grid_color'],
        linecolor=PLOT_CONFIG['line_color'], linewidth=PLOT_CONFIG['line_width'],
        zeroline=True, zerolinecolor=PLOT_CONFIG['grid_color']
    )
    
    return fig

def create_box_plot_by_group(plot_data, filtered_groups, filtered_divs, metric, title):
    """Create box plot organized by group"""
    
    fig = make_subplots(
        rows=1, cols=len(filtered_groups), 
        subplot_titles=[f'<b>{g}</b>' for g in filtered_groups],
        shared_yaxes=True,
        horizontal_spacing=0.08
    )
    
    max_y = 0
    
    for col, group in enumerate(filtered_groups, 1):
        if group not in plot_data:
            continue
            
        for div in filtered_divs:
            if div not in plot_data[group]:
                continue
                
            div_values = plot_data[group][div]
            if len(div_values) == 0:
                continue
            
            max_y = max(max_y, max(div_values))
            
            # Get colors
            color = MATLAB_COLORS.get(div, MATLAB_COLORS['default'])
            
            fig.add_trace(
                go.Box(
                    y=div_values,
                    name=f'DIV {div}',
                    legendgroup=f'DIV {div}',
                    showlegend=(col == 1),
                    marker_color=color,
                    line_color=color,
                    fillcolor=color.replace(')', ', 0.3)').replace('rgb', 'rgba') if 'rgb' in color else color + '4D',
                    boxpoints='outliers',
                    notched=True,
                    x=[f'DIV {div}'] * len(div_values)
                ),
                row=1, col=col
            )
    
    # Update layout
    fig.update_layout(
        title=dict(text=f'<b>{title}</b>', x=0.5, font=dict(size=16, color='black')),
        height=PLOT_CONFIG['height'],
        plot_bgcolor=PLOT_CONFIG['plot_bgcolor'],
        paper_bgcolor=PLOT_CONFIG['paper_bgcolor'],
        font=dict(family=PLOT_CONFIG['font_family'], size=PLOT_CONFIG['font_size'], color=PLOT_CONFIG['font_color']),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Update axes
    for col in range(1, len(filtered_groups) + 1):
        fig.update_xaxes(
            tickvals=[f'DIV {div}' for div in filtered_divs],
            ticktext=[str(div) for div in filtered_divs],
            title_text="Age" if col == len(filtered_groups)//2 + 1 else "",
            showgrid=True, gridwidth=1, gridcolor=PLOT_CONFIG['grid_color'],
            linecolor=PLOT_CONFIG['line_color'], linewidth=PLOT_CONFIG['line_width'],
            row=1, col=col
        )
    
    fig.update_yaxes(
        title_text=get_metric_label(metric),
        range=[0, max_y * 1.1] if max_y > 0 else [0, 1],
        showgrid=True, gridwidth=1, gridcolor=PLOT_CONFIG['grid_color'],
        linecolor=PLOT_CONFIG['line_color'], linewidth=PLOT_CONFIG['line_width'],
        zeroline=True, zerolinecolor=PLOT_CONFIG['grid_color']
    )
    
    return fig

def create_bar_plot_by_group(plot_data, filtered_groups, filtered_divs, metric, title):
    """Create bar plot organized by group (showing means with error bars)"""
    
    fig = go.Figure()
    
    # Process data for bar plot
    x_labels = []
    y_means = []
    y_errors = []
    colors = []
    
    for group in filtered_groups:
        if group not in plot_data:
            continue
            
        for div in filtered_divs:
            if div not in plot_data[group]:
                continue
                
            div_values = plot_data[group][div]
            if len(div_values) == 0:
                continue
            
            # Calculate mean and SEM
            mean_val = np.mean(div_values)
            sem_val = np.std(div_values) / np.sqrt(len(div_values)) if len(div_values) > 1 else 0
            
            x_labels.append(f'{group}\nDIV {div}')
            y_means.append(mean_val)
            y_errors.append(sem_val)
            colors.append(MATLAB_COLORS.get(div, MATLAB_COLORS['default']))
    
    # Create bar plot
    fig.add_trace(
        go.Bar(
            x=x_labels,
            y=y_means,
            error_y=dict(type='data', array=y_errors, visible=True, color='black', thickness=2, width=4),
            marker_color=colors,
            marker_line=dict(color='black', width=1),
            opacity=0.8,
            hovertemplate='%{x}<br>Mean: %{y:.3f}<br>SEM: %{error_y.array:.3f}<extra></extra>'
        )
    )
    
    # Update layout
    fig.update_layout(
        title=dict(text=f'<b>{title}</b>', x=0.5, font=dict(size=16, color='black')),
        height=PLOT_CONFIG['height'],
        plot_bgcolor=PLOT_CONFIG['plot_bgcolor'],
        paper_bgcolor=PLOT_CONFIG['paper_bgcolor'],
        xaxis_title="<b>Group / Age</b>",
        yaxis_title=f"<b>Mean {get_metric_label(metric)}</b>",
        font=dict(family=PLOT_CONFIG['font_family'], size=PLOT_CONFIG['font_size'], color=PLOT_CONFIG['font_color']),
        showlegend=False
    )
    
    # Update axes
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=PLOT_CONFIG['grid_color'], linecolor=PLOT_CONFIG['line_color'], linewidth=PLOT_CONFIG['line_width'])
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=PLOT_CONFIG['grid_color'], linecolor=PLOT_CONFIG['line_color'], linewidth=PLOT_CONFIG['line_width'], zeroline=True, zerolinecolor=PLOT_CONFIG['grid_color'])
    
    return fig

# =============================================================================
# MAIN VISUALIZATION FUNCTIONS - Public API
# =============================================================================

def create_half_violin_plot_by_group(data, metric, title, selected_groups=None, selected_divs=None):
    """
    Create MEA-NAP style violin plot organized by group
    
    Args:
        data: Processed data from metric-specific functions
        metric: Metric field name to plot
        title: Plot title
        selected_groups: List of groups to include
        selected_divs: List of DIVs to include
        
    Returns:
        Plotly figure
    """
    
    # Prepare data for plotting
    plot_data, filtered_groups, filtered_divs = prepare_data_for_plotting(data, metric, selected_groups, selected_divs)
    
    # Create violin plot
    return create_violin_plot_by_group(plot_data, filtered_groups, filtered_divs, metric, title)

def create_half_violin_plot_by_age(data, metric, title, selected_groups=None, selected_divs=None):
    """
    Create MEA-NAP style violin plot organized by age
    
    Args:
        data: Processed data from metric-specific functions
        metric: Metric field name to plot
        title: Plot title
        selected_groups: List of groups to include
        selected_divs: List of DIVs to include
        
    Returns:
        Plotly figure
    """
    
    # Prepare data for plotting
    plot_data, filtered_groups, filtered_divs = prepare_data_for_plotting(data, metric, selected_groups, selected_divs)
    
    # Create violin plot
    return create_violin_plot_by_age(plot_data, filtered_groups, filtered_divs, metric, title)

def create_box_plot_by_group(data, metric, title, selected_groups=None, selected_divs=None):
    """
    Create MEA-NAP style box plot organized by group
    
    Args:
        data: Processed data from metric-specific functions
        metric: Metric field name to plot
        title: Plot title
        selected_groups: List of groups to include
        selected_divs: List of DIVs to include
        
    Returns:
        Plotly figure
    """
    
    # Prepare data for plotting
    plot_data, filtered_groups, filtered_divs = prepare_data_for_plotting(data, metric, selected_groups, selected_divs)
    
    # Create box plot
    return create_box_plot_by_group(plot_data, filtered_groups, filtered_divs, metric, title)

def create_bar_plot_by_group(data, metric, title, selected_groups=None, selected_divs=None):
    """
    Create MEA-NAP style bar plot organized by group
    
    Args:
        data: Processed data from metric-specific functions
        metric: Metric field name to plot
        title: Plot title
        selected_groups: List of groups to include
        selected_divs: List of DIVs to include
        
    Returns:
        Plotly figure
    """
    
    # Prepare data for plotting
    plot_data, filtered_groups, filtered_divs = prepare_data_for_plotting(data, metric, selected_groups, selected_divs)
    
    # Create bar plot
    return create_bar_plot_by_group(plot_data, filtered_groups, filtered_divs, metric, title)

# Age-based versions (aliases for consistency)
def create_box_plot_by_age(data, metric, title, selected_groups=None, selected_divs=None):
    """Create box plot organized by age - same as by_group but different organization"""
    # For simplicity, reuse the by_group function since the organization is similar
    return create_box_plot_by_group(data, metric, title, selected_groups, selected_divs)

def create_bar_plot_by_age(data, metric, title, selected_groups=None, selected_divs=None):
    """Create bar plot organized by age - same as by_group but different organization"""
    # For simplicity, reuse the by_group function since the organization is similar
    return create_bar_plot_by_group(data, metric, title, selected_groups, selected_divs)

def analyze_burst_data_distribution(data, metric='channelBurstRate'):
    """Analyze the distribution of burst data across groups"""
    print(f"\n📊 BURST DATA ANALYSIS for {metric}:")
    
    if 'by_group' not in data:
        print("No group data found")
        return
    
    for group in data['groups']:
        if group not in data['by_group']:
            continue
            
        group_data = data['by_group'][group]
        if metric not in group_data:
            continue
        
        values = group_data[metric]
        if isinstance(values, (list, np.ndarray)):
            valid_values = [v for v in values if v is not None and np.isfinite(v) and v > 0]
            total_values = len(values)
            zero_values = len([v for v in values if v == 0])
            
            print(f"  {group}:")
            print(f"    Total values: {total_values}")
            print(f"    Valid (>0) values: {len(valid_values)}")
            print(f"    Zero values: {zero_values}")
            print(f"    NaN values: {total_values - len(valid_values) - zero_values}")
            
            if len(valid_values) > 0:
                print(f"    Range: {min(valid_values):.2f} - {max(valid_values):.2f}")
                print(f"    Mean: {np.mean(valid_values):.2f}")
            else:
                print(f"    No valid burst data detected")