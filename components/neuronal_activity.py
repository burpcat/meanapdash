# components/neuronal_activity.py - REFACTORED VERSION WITH Y-AXIS CONTROLS
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from data_processing.utilities import calculate_half_violin_data, extract_div_value
from utils.config import get_plot_color, get_plot_fill_color
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

def prepare_data_for_plotting(data, metric, groups, selected_divs, comparison_type='nodebygroup'):
    """
    Prepare data for plotting by extracting and organizing values by group and DIV
    
    MODIFIED: Removed the by_div routing - Node by Age now uses by_group structure
    
    Args:
        data: Processed data from metric processors
        metric: Metric field name
        groups: Selected groups
        selected_divs: Selected DIVs
        comparison_type: Type of comparison ('nodebygroup', 'nodebyage', etc.)
    """
    print(f"🔧 Preparing data for plotting: {metric} ({comparison_type})")
    
    # Filter DIVs
    if selected_divs:
        filtered_divs = [d for d in selected_divs if d in data['divs']]
    else:
        filtered_divs = sorted(data['divs'])
    
    # Filter groups
    if groups:
        filtered_groups = [g for g in groups if g in data['groups']]
    else:
        filtered_groups = data['groups']
    
    # ALL COMPARISONS now use by_group structure
    # The difference is in the visualization, not the data preparation
    print(f"   Using by_group data structure for all comparison types")
    
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
                    if f'DIV{div}' in exp_name:
                        if i < len(group_data[metric]):
                            value = group_data[metric][i]
                            if isinstance(value, (list, np.ndarray)):
                                div_values.extend(value)
                            else:
                                div_values.append(value)
                
                # If no DIV-specific data found, use all data (fallback)
                if len(div_values) == 0:
                    div_values = group_data[metric]
            else:
                # For electrode-level data, use all values
                div_values = group_data[metric]
            
            # Clean the data
            if isinstance(div_values, (list, np.ndarray)):
                if isinstance(div_values, np.ndarray):
                    div_values = div_values.tolist()
                clean_values = [v for v in div_values if v is not None and np.isfinite(v)]
            else:
                clean_values = [div_values] if div_values is not None and np.isfinite(div_values) else []
            
            plot_data[group][div] = clean_values
    
    return plot_data, filtered_groups, filtered_divs

def calculate_y_range(plot_data, y_range_mode='auto', y_min=None, y_max=None):
    """
    Calculate Y-axis range based on mode and user inputs
    
    Args:
        plot_data: Dictionary of plot data organized by group and DIV
        y_range_mode: 'auto' or 'manual'
        y_min: Manual minimum Y value
        y_max: Manual maximum Y value
        
    Returns:
        tuple: (y_min_final, y_max_final)
    """
    
    if y_range_mode == 'manual' and y_min is not None and y_max is not None:
        if y_min < y_max:
            print(f"   📊 Using manual Y-range: [{y_min}, {y_max}]")
            return y_min, y_max
        else:
            print(f"⚠️ Invalid Y-range: min({y_min}) >= max({y_max}), using auto range")
    
    # AUTO RANGE CALCULATION
    all_values = []
    for group in plot_data:
        for div in plot_data[group]:
            if isinstance(plot_data[group][div], list):
                all_values.extend(plot_data[group][div])
    
    if len(all_values) > 0:
        all_values = sorted(all_values)
        if len(all_values) > 1:
            p95 = np.percentile(all_values, 95)
            p5 = np.percentile(all_values, 5)
            y_max_auto = p95 * 1.2
            y_min_auto = max(0, p5 * 0.8)
        else:
            max_val = max(all_values)
            y_max_auto = max_val * 1.2
            y_min_auto = 0
    else:
        y_max_auto = 1
        y_min_auto = 0
    
    print(f"   📊 Using auto Y-range: [{y_min_auto:.2f}, {y_max_auto:.2f}]")
    return y_min_auto, y_max_auto

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
# PLOT TYPE FUNCTIONS - Individual plot creators WITH Y-AXIS SUPPORT
# =============================================================================

def create_violin_plot_by_group(plot_data, filtered_groups, filtered_divs, metric, title, neuronal_data=None,
                                y_range_mode='auto', y_min=None, y_max=None):
    """
    Create violin plot that matches MEA-NAP behavior with proper colors and Y-axis controls
    
    MEA-NAP Logic: Node by Group uses AGE-BASED colors (viridis colormap)
    """
    
    fig = make_subplots(
        rows=1, cols=len(filtered_groups), 
        subplot_titles=[f'<b>{g}</b>' for g in filtered_groups],
        shared_yaxes=True,
        horizontal_spacing=0.08
    )
    
    max_y = 0
    total_data_points = 0
    groups_with_data = set()
    
    for col, group in enumerate(filtered_groups, 1):
        group_has_data = False
        
        if group not in plot_data:
            continue
            
        for div_idx, div in enumerate(filtered_divs):
            if div not in plot_data[group]:
                continue
                
            div_values = plot_data[group][div]
            
            # Handle empty data
            if not isinstance(div_values, list) or len(div_values) == 0:
                continue
            
            group_has_data = True
            groups_with_data.add(group)
            
            # Track statistics
            try:
                current_max = max(div_values)
                max_y = max(max_y, current_max)
                total_data_points += len(div_values)
            except (ValueError, TypeError):
                continue
            
            # MEA-NAP COLORS: Age-based (X-axis shows ages)
            if neuronal_data:
                color = get_plot_color('nodebygroup', neuronal_data, div)
                fill_color = get_plot_fill_color('nodebygroup', neuronal_data, div)
            else:
                # Fallback to legacy colors
                color = MATLAB_COLORS.get(div, MATLAB_COLORS['default'])
                fill_color = MATLAB_FILL_COLORS.get(div, MATLAB_FILL_COLORS['default'])
            
            x_base = div_idx + 1
            
            # MEA-NAP APPROACH: ALWAYS SHOW VIOLIN + INDIVIDUAL POINTS
            
            # 1. INDIVIDUAL DATA POINTS (LEFT side with jitter)
            jitter_width = 0.15
            jitter = np.random.uniform(-jitter_width, 0, size=len(div_values))  # LEFT side only
            
            fig.add_trace(
                go.Scatter(
                    x=[x_base + j for j in jitter],
                    y=div_values,
                    mode='markers',
                    marker=dict(
                        color=color,
                        size=6,  # MEA-NAP size scaled down for Plotly
                        opacity=0.8,
                        line=dict(width=1, color='black')
                    ),
                    name=f'DIV {div}',
                    legendgroup=f'DIV {div}',
                    showlegend=(col == 1),
                    hovertemplate=f'<b>{group} - DIV {div}</b><br>Value: %{{y:.3f}}<br>Electrode %{{pointNumber}}<br>n={len(div_values)}<extra></extra>'
                ),
                row=1, col=col
            )
            
            # 2. HALF VIOLIN PLOT (RIGHT side) - ALWAYS SHOWN like MEA-NAP
            if len(div_values) >= 2:  # MEA-NAP minimum: n > 1
                try:
                    # Use our existing KDE calculation but improve it
                    kde_data = calculate_half_violin_data(div_values)
                    x_data = kde_data.get('x')
                    y_data = kde_data.get('y')
                    
                    if x_data is not None and y_data is not None and len(x_data) > 0:
                        if isinstance(x_data, np.ndarray):
                            x_data = x_data.tolist()
                        if isinstance(y_data, np.ndarray):
                            y_data = y_data.tolist()
                        
                        # MEA-NAP specification: violin on RIGHT side of x-axis center
                        violin_width = 0.3
                        max_density = max(y_data) if len(y_data) > 0 else 1
                        scaled_density = [(d / max_density) * violin_width for d in y_data]
                        violin_x = [x_base + 0.1 + d for d in scaled_density]  # RIGHT side: +0.1 offset
                        
                        # Create filled violin shape
                        fig.add_trace(
                            go.Scatter(
                                x=violin_x + [x_base + 0.1] * len(violin_x),  # Close the shape
                                y=x_data + x_data[::-1],  # Mirror for closing
                                fill='toself',
                                fillcolor=fill_color,
                                line=dict(color=color, width=1),
                                mode='lines',
                                showlegend=False,
                                hoverinfo='skip'
                            ),
                            row=1, col=col
                        )
                
                except Exception as e:
                    print(f"⚠️ Violin plot failed for {group} DIV {div} (n={len(div_values)}): {e}")
                    # Continue without violin - individual points still shown
            
            # 3. MEAN INDICATOR (CENTER) - MEA-NAP specification
            try:
                mean_value = np.mean(div_values)
                fig.add_trace(
                    go.Scatter(
                        x=[x_base],
                        y=[mean_value],
                        mode='markers',
                        marker=dict(
                            color='black',  # MEA-NAP: pure black
                            size=12,  # MEA-NAP: size 100 scaled down for Plotly
                            opacity=1.0,
                            line=dict(width=2, color='black')
                        ),
                        showlegend=False,
                        hovertemplate=f'<b>Mean: {mean_value:.3f}</b><br>n={len(div_values)} electrodes<extra></extra>'
                    ),
                    row=1, col=col
                )
                
                # 4. ERROR BARS (SEM, not std) - MEA-NAP specification
                if len(div_values) > 1:
                    sem_value = np.std(div_values) / np.sqrt(len(div_values))
                    fig.add_trace(
                        go.Scatter(
                            x=[x_base, x_base],
                            y=[mean_value - sem_value, mean_value + sem_value],
                            mode='lines',
                            line=dict(color='black', width=3),  # MEA-NAP: 3px width
                            showlegend=False,
                            hoverinfo='skip'
                        ),
                        row=1, col=col
                    )
                
            except Exception as e:
                print(f"⚠️ Mean calculation failed for {group} DIV {div}: {e}")
    
    # Add "No Data" annotations for completely empty groups
    for col, group in enumerate(filtered_groups, 1):
        if group not in groups_with_data:
            y_center = (max_y / 2) if max_y > 0 else 0.5
            fig.add_annotation(
                x=1.5,
                y=y_center,
                text="<b>No Data</b>",
                showarrow=False,
                font=dict(size=16, color='lightgray'),
                row=1, col=col
            )
    
    # Layout matching MEA-NAP style
    fig.update_layout(
        title=dict(text=f'<b>{title}</b>', x=0.5, font=dict(size=16, color='black')),
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Arial', size=12, color='black'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(b=60, t=100, l=60, r=60)
    )
    
    # APPLY Y-AXIS CONTROLS
    y_min_final, y_max_final = calculate_y_range(plot_data, y_range_mode, y_min, y_max)
    
    # Update axes
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
        range=[y_min_final, y_max_final],  # USE CALCULATED Y-RANGE
        showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.5)',
        linecolor='black', linewidth=1,
        zeroline=True, zerolinecolor='rgba(200,200,200,0.5)'
    )
    
    print(f"   ✅ Created MEA-NAP style plot: {total_data_points} data points across {len(filtered_groups)} groups")
    print(f"   📊 Y-axis range: [{y_min_final:.2f}, {y_max_final:.2f}] ({'manual' if y_range_mode == 'manual' else 'auto'})")
    
    return fig

# =============================================================================
# MAIN VISUALIZATION FUNCTIONS WITH Y-AXIS SUPPORT - Public API
# =============================================================================

def create_half_violin_plot_by_group(data, metric, title, selected_groups=None, selected_divs=None,
                                     y_range_mode='auto', y_min=None, y_max=None):
    """
    Create MEA-NAP style violin plot organized by group with proper color scheme and Y-axis controls
    
    Args:
        data: Processed data from metric processors
        metric: Metric field name to plot
        title: Plot title
        selected_groups: List of groups to include
        selected_divs: List of DIVs to include
        y_range_mode: 'auto' or 'manual'
        y_min: Manual minimum Y value
        y_max: Manual maximum Y value
        
    Returns:
        Plotly figure
    """
    
    # Prepare data for plotting
    plot_data, filtered_groups, filtered_divs = prepare_data_for_plotting(data, metric, selected_groups, selected_divs)
    
    # Create violin plot with neuronal data for color determination and Y-axis controls
    return create_violin_plot_by_group(plot_data, filtered_groups, filtered_divs, metric, title, neuronal_data=data,
                                      y_range_mode=y_range_mode, y_min=y_min, y_max=y_max)

def create_half_violin_plot_by_age(data, metric, title, selected_groups=None, selected_divs=None,
                                  y_range_mode='auto', y_min=None, y_max=None):
    """
    Create MEA-NAP style violin plot organized by age with Y-axis controls
    Shows separate subplot for each age, with groups compared within each age
    
    MEA-NAP Logic: X-axis shows groups → Colors represent groups (group colors)
    """
    print(f"🎨 Creating MEA-NAP style violin plot by age for {metric}")
    
    # Prepare data using by_group structure
    plot_data, filtered_groups, filtered_divs = prepare_data_for_plotting(
        data, metric, selected_groups, selected_divs, 'nodebygroup'
    )
    
    # Create subplots - one for each DIV/age
    fig = make_subplots(
        rows=1, cols=len(filtered_divs), 
        subplot_titles=[f'<b>Age{div}</b>' for div in filtered_divs],
        shared_yaxes=True,
        horizontal_spacing=0.08
    )
    
    max_y = 0
    total_data_points = 0
    
    # For each DIV (age), create a group comparison subplot
    for col, div in enumerate(filtered_divs, 1):
        div_has_data = False
        
        # Within this DIV, show all groups on X-axis
        for group_idx, group in enumerate(filtered_groups):
            if group not in plot_data or div not in plot_data[group]:
                continue
                
            div_values = plot_data[group][div]
            if not isinstance(div_values, list) or len(div_values) == 0:
                continue
            
            div_has_data = True
            
            # Track statistics
            try:
                current_max = max(div_values)
                max_y = max(max_y, current_max)
                total_data_points += len(div_values)
            except (ValueError, TypeError):
                continue
            
            # MEA-NAP COLORS: Group-based (X-axis shows groups)
            color = get_plot_color('nodebyage', data, group)
            fill_color = get_plot_fill_color('nodebyage', data, group)
            
            x_base = group_idx + 1  # X-position for this group
            
            # MEA-NAP APPROACH: ALWAYS SHOW VIOLIN + INDIVIDUAL POINTS
            
            # 1. INDIVIDUAL DATA POINTS (LEFT side with jitter)
            jitter_width = 0.15
            jitter = np.random.uniform(-jitter_width, 0, size=len(div_values))  # LEFT side only
            
            fig.add_trace(
                go.Scatter(
                    x=[x_base + j for j in jitter],
                    y=div_values,
                    mode='markers',
                    marker=dict(
                        color=color,
                        size=6,  # MEA-NAP size scaled for Plotly
                        opacity=0.8,
                        line=dict(width=1, color='black')
                    ),
                    name=f'{group}',
                    legendgroup=f'{group}',
                    showlegend=(col == 1),  # Only show legend for first subplot
                    hovertemplate=f'<b>{group} - DIV {div}</b><br>Value: %{{y:.3f}}<br>Electrode %{{pointNumber}}<br>n={len(div_values)}<extra></extra>'
                ),
                row=1, col=col
            )
            
            # 2. HALF VIOLIN PLOT (RIGHT side) - ALWAYS SHOWN like MEA-NAP
            if len(div_values) >= 2:  # MEA-NAP minimum: n > 1
                try:
                    # Use our existing KDE calculation
                    kde_data = calculate_half_violin_data(div_values)
                    x_data = kde_data.get('x')
                    y_data = kde_data.get('y')
                    
                    if x_data is not None and y_data is not None and len(x_data) > 0:
                        if isinstance(x_data, np.ndarray):
                            x_data = x_data.tolist()
                        if isinstance(y_data, np.ndarray):
                            y_data = y_data.tolist()
                        
                        # MEA-NAP specification: violin on RIGHT side of x-axis center
                        violin_width = 0.3
                        max_density = max(y_data) if len(y_data) > 0 else 1
                        scaled_density = [(d / max_density) * violin_width for d in y_data]
                        violin_x = [x_base + 0.1 + d for d in scaled_density]  # RIGHT side: +0.1 offset
                        
                        # Create filled violin shape
                        fig.add_trace(
                            go.Scatter(
                                x=violin_x + [x_base + 0.1] * len(violin_x),  # Close the shape
                                y=x_data + x_data[::-1],  # Mirror for closing
                                fill='toself',
                                fillcolor=fill_color,
                                line=dict(color=color, width=1),
                                mode='lines',
                                showlegend=False,
                                hoverinfo='skip'
                            ),
                            row=1, col=col
                        )
                
                except Exception as e:
                    print(f"⚠️ Violin plot failed for {group} DIV {div} (n={len(div_values)}): {e}")
                    # Continue without violin - individual points still shown
            
            # 3. MEAN INDICATOR (CENTER) - MEA-NAP specification
            try:
                mean_value = np.mean(div_values)
                fig.add_trace(
                    go.Scatter(
                        x=[x_base],
                        y=[mean_value],
                        mode='markers',
                        marker=dict(
                            color='black',  # MEA-NAP: pure black
                            size=12,  # MEA-NAP size scaled for Plotly
                            opacity=1.0,
                            line=dict(width=2, color='black')
                        ),
                        showlegend=False,
                        hovertemplate=f'<b>Mean: {mean_value:.3f}</b><br>n={len(div_values)} electrodes<extra></extra>'
                    ),
                    row=1, col=col
                )
                
                # 4. ERROR BARS (SEM, not std) - MEA-NAP specification
                if len(div_values) > 1:
                    sem_value = np.std(div_values) / np.sqrt(len(div_values))
                    fig.add_trace(
                        go.Scatter(
                            x=[x_base, x_base],
                            y=[mean_value - sem_value, mean_value + sem_value],
                            mode='lines',
                            line=dict(color='black', width=3),  # MEA-NAP: 3px width
                            showlegend=False,
                            hoverinfo='skip'
                        ),
                        row=1, col=col
                    )
                
            except Exception as e:
                print(f"⚠️ Mean calculation failed for {group} DIV {div}: {e}")
        
        # Update x-axis for this subplot to show group names
        fig.update_xaxes(
            tickvals=list(range(1, len(filtered_groups) + 1)),
            ticktext=filtered_groups,
            title_text="Group" if col == len(filtered_divs)//2 + 1 else "",
            showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.5)',
            linecolor='black', linewidth=1,
            range=[0.5, len(filtered_groups) + 0.5],
            row=1, col=col
        )
        
        # Add "No Data" annotation for empty age subplots
        if not div_has_data:
            y_center = 0.5  # Will be adjusted after Y-range calculation
            fig.add_annotation(
                x=len(filtered_groups) / 2 + 0.5,
                y=y_center,
                text="<b>No Data</b>",
                showarrow=False,
                font=dict(size=16, color='lightgray'),
                row=1, col=col
            )
    
    # Layout matching MEA-NAP style
    annotations = []
    annotations.append(
        dict(
            text="Node by Age: Group comparisons within each age (MEA-NAP colors by group)",
            showarrow=False,
            xref="paper", yref="paper",
            x=0.5, y=1.05,
            font=dict(size=10, color='blue'),
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
        margin=dict(b=60, t=120, l=60, r=60)
    )
    
    # APPLY Y-AXIS CONTROLS
    y_min_final, y_max_final = calculate_y_range(plot_data, y_range_mode, y_min, y_max)
    
    # Y-axis (shared across all subplots)
    fig.update_yaxes(
        title_text=f"<b>{get_metric_label(metric)}</b>",
        range=[y_min_final, y_max_final],  # USE CALCULATED Y-RANGE
        showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.5)',
        linecolor='black', linewidth=1,
        zeroline=True, zerolinecolor='rgba(200,200,200,0.5)'
    )
    
    print(f"   ✅ Created MEA-NAP style Node by Age plot: {total_data_points} total data points across {len(filtered_divs)} age subplots")
    print(f"   📊 Y-axis range: [{y_min_final:.2f}, {y_max_final:.2f}] ({'manual' if y_range_mode == 'manual' else 'auto'})")
    
    return fig

def create_recording_level_violin_plot_by_group(data, metric, title, selected_groups=None, selected_divs=None,
                                               y_range_mode='auto', y_min=None, y_max=None):
    """
    Create recording-level violin plot organized by group with MEA-NAP colors and Y-axis controls
    Recording by Group: X-axis shows ages → Colors represent ages (viridis)
    """
    print(f"🎭 Creating RECORDING-LEVEL violin plot by group for {metric}")
    
    # Prepare data for plotting
    plot_data, filtered_groups, filtered_divs = prepare_data_for_plotting(
        data, metric, selected_groups, selected_divs, 'recordingsbygroup'
    )
    
    # Create subplots - one for each group
    fig = make_subplots(
        rows=1, cols=len(filtered_groups), 
        subplot_titles=[f'<b>{g}</b>' for g in filtered_groups],
        shared_yaxes=True,
        horizontal_spacing=0.08
    )
    
    max_y = 0
    total_recordings = 0
    groups_with_data = set()
    
    for col, group in enumerate(filtered_groups, 1):
        group_has_data = False
        
        if group not in plot_data:
            continue
            
        for div_idx, div in enumerate(filtered_divs):
            if div not in plot_data[group]:
                continue
                
            recording_values = plot_data[group][div]
            
            if not isinstance(recording_values, list) or len(recording_values) == 0:
                continue
            
            group_has_data = True
            groups_with_data.add(group)
            
            try:
                current_max = max(recording_values)
                max_y = max(max_y, current_max)
                total_recordings += len(recording_values)
            except (ValueError, TypeError):
                continue
            
            # MEA-NAP COLORS: Age-based for Recording by Group (X-axis shows ages)
            color = get_plot_color('recordingsbygroup', data, div)
            fill_color = get_plot_fill_color('recordingsbygroup', data, div)
            
            x_base = div_idx + 1
            
            # Recording-level visualization (fewer points, more prominent)
            if len(recording_values) == 1:
                fig.add_trace(
                    go.Scatter(
                        x=[x_base],
                        y=recording_values,
                        mode='markers',
                        marker=dict(
                            color=color,
                            size=16,
                            opacity=0.9,
                            line=dict(width=3, color='black'),
                            symbol='star'
                        ),
                        name=f'DIV {div}',
                        legendgroup=f'DIV {div}',
                        showlegend=(col == 1),
                        hovertemplate=f'<b>{group} - DIV {div}</b><br>Value: %{{y:.3f}}<br>Single Recording<extra></extra>'
                    ),
                    row=1, col=col
                )
                
            elif len(recording_values) <= 3:
                jitter = np.random.normal(0, 0.12, size=len(recording_values))
                fig.add_trace(
                    go.Scatter(
                        x=[x_base + j for j in jitter],
                        y=recording_values,
                        mode='markers',
                        marker=dict(
                            color=color,
                            size=14,
                            opacity=0.9,
                            line=dict(width=2, color='black'),
                            symbol='diamond'
                        ),
                        name=f'DIV {div}',
                        legendgroup=f'DIV {div}',
                        showlegend=(col == 1),
                        hovertemplate=f'<b>{group} - DIV {div}</b><br>Value: %{{y:.3f}}<br>Recording %{{pointNumber}}<br>n={len(recording_values)}<extra></extra>'
                    ),
                    row=1, col=col
                )
                
            else:
                jitter = np.random.normal(0, 0.06, size=len(recording_values))
                fig.add_trace(
                    go.Scatter(
                        x=[x_base + j for j in jitter],
                        y=recording_values,
                        mode='markers',
                        marker=dict(
                            color='black',
                            size=8,
                            opacity=0.8,
                            line=dict(width=1, color='black')
                        ),
                        name=f'DIV {div}',
                        legendgroup=f'DIV {div}',
                        showlegend=(col == 1),
                        hovertemplate=f'<b>{group} - DIV {div}</b><br>Value: %{{y:.3f}}<br>Recording %{{pointNumber}}<br>n={len(recording_values)}<extra></extra>'
                    ),
                    row=1, col=col
                )
                
                # Add violin if enough recordings
                if len(recording_values) >= 4:
                    try:
                        kde_data = calculate_half_violin_data(recording_values)
                        x_data = kde_data.get('x')
                        if x_data is not None and len(x_data) > 0:
                            if isinstance(x_data, np.ndarray):
                                x_data = x_data.tolist()
                            
                            fig.add_trace(
                                go.Violin(
                                    x=[x_base] * len(x_data),
                                    y=x_data,
                                    width=0.8,
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
            
            # Add mean indicator
            try:
                mean_value = np.mean(recording_values)
                fig.add_trace(
                    go.Scatter(
                        x=[x_base],
                        y=[mean_value],
                        mode='markers',
                        marker=dict(
                            color='red',
                            size=10,
                            opacity=1.0,
                            line=dict(width=2, color='black'),
                            symbol='x'
                        ),
                        showlegend=False,
                        hovertemplate=f'<b>Mean: {mean_value:.3f}</b><br>n={len(recording_values)} recordings<extra></extra>'
                    ),
                    row=1, col=col
                )
            except Exception as e:
                print(f"⚠️ Mean calculation failed for {group} DIV {div}: {e}")
    
    # Add "No Data" annotations for empty groups
    for col, group in enumerate(filtered_groups, 1):
        if group not in groups_with_data:
            y_center = 0.5  # Will be adjusted after Y-range calculation
            fig.add_annotation(
                x=1.5,
                y=y_center,
                text="<b>No Recordings</b>",
                showarrow=False,
                font=dict(size=16, color='lightgray'),
                row=1, col=col
            )
    
    # Layout
    annotations = []
    annotations.append(
        dict(
            text="Recording-Level by Group: Age comparisons (MEA-NAP colors by age)",
            showarrow=False,
            xref="paper", yref="paper",
            x=0.5, y=1.05,
            font=dict(size=10, color='blue'),
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
        margin=dict(b=80, t=120, l=60, r=60)
    )
    
    # APPLY Y-AXIS CONTROLS
    y_min_final, y_max_final = calculate_y_range(plot_data, y_range_mode, y_min, y_max)
    
    # Update axes
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
        range=[y_min_final, y_max_final],  # USE CALCULATED Y-RANGE
        showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.5)',
        linecolor='black', linewidth=1,
        zeroline=True, zerolinecolor='rgba(200,200,200,0.5)'
    )
    
    print(f"   ✅ Created RECORDING-LEVEL plot: {total_recordings} recordings across {len(filtered_groups)} groups")
    print(f"   📊 Y-axis range: [{y_min_final:.2f}, {y_max_final:.2f}] ({'manual' if y_range_mode == 'manual' else 'auto'})")
    
    return fig

def create_recording_level_violin_plot_by_age(data, metric, title, selected_groups=None, selected_divs=None,
                                             y_range_mode='auto', y_min=None, y_max=None):
    """
    Create recording-level violin plot by age with MEA-NAP colors and Y-axis controls
    Recording by Age: X-axis shows groups → Colors represent groups (group colors)
    """
    print(f"🎭 Creating RECORDING-LEVEL violin plot by age for {metric}")
    
    # Prepare data using by_group structure
    plot_data, filtered_groups, filtered_divs = prepare_data_for_plotting(
        data, metric, selected_groups, selected_divs, 'recordingsbygroup'
    )
    
    # Create subplots - one for each DIV/age
    fig = make_subplots(
        rows=1, cols=len(filtered_divs), 
        subplot_titles=[f'<b>Age{div}</b>' for div in filtered_divs],
        shared_yaxes=True,
        horizontal_spacing=0.08
    )
    
    max_y = 0
    total_recordings = 0
    
    # For each DIV (age), create a group comparison subplot
    for col, div in enumerate(filtered_divs, 1):
        div_has_data = False
        
        # Within this DIV, show all groups on X-axis
        for group_idx, group in enumerate(filtered_groups):
            if group not in plot_data or div not in plot_data[group]:
                continue
                
            recording_values = plot_data[group][div]
            if not isinstance(recording_values, list) or len(recording_values) == 0:
                continue
            
            div_has_data = True
            
            try:
                current_max = max(recording_values)
                max_y = max(max_y, current_max)
                total_recordings += len(recording_values)
            except (ValueError, TypeError):
                continue
            
            # MEA-NAP COLORS: Group-based for Recording by Age (X-axis shows groups)
            color = get_plot_color('recordingsbyage', data, group)
            fill_color = get_plot_fill_color('recordingsbyage', data, group)
            
            x_base = group_idx + 1
            
            # Recording-level visualization (same logic as byGroup but with group colors)
            if len(recording_values) == 1:
                fig.add_trace(
                    go.Scatter(
                        x=[x_base],
                        y=recording_values,
                        mode='markers',
                        marker=dict(
                            color=color,
                            size=16,
                            opacity=0.9,
                            line=dict(width=3, color='black'),
                            symbol='star'
                        ),
                        name=f'{group}',
                        legendgroup=f'{group}',
                        showlegend=(col == 1),
                        hovertemplate=f'<b>{group} - DIV {div}</b><br>Value: %{{y:.3f}}<br>Single Recording<extra></extra>'
                    ),
                    row=1, col=col
                )
                
            elif len(recording_values) <= 3:
                jitter = np.random.normal(0, 0.12, size=len(recording_values))
                fig.add_trace(
                    go.Scatter(
                        x=[x_base + j for j in jitter],
                        y=recording_values,
                        mode='markers',
                        marker=dict(
                            color=color,
                            size=14,
                            opacity=0.9,
                            line=dict(width=2, color='black'),
                            symbol='diamond'
                        ),
                        name=f'{group}',
                        legendgroup=f'{group}',
                        showlegend=(col == 1),
                        hovertemplate=f'<b>{group} - DIV {div}</b><br>Value: %{{y:.3f}}<br>n={len(recording_values)}<extra></extra>'
                    ),
                    row=1, col=col
                )
                
            else:
                jitter = np.random.normal(0, 0.06, size=len(recording_values))
                fig.add_trace(
                    go.Scatter(
                        x=[x_base + j for j in jitter],
                        y=recording_values,
                        mode='markers',
                        marker=dict(color='black', size=8, opacity=0.8),
                        name=f'{group}',
                        legendgroup=f'{group}',
                        showlegend=(col == 1),
                        hovertemplate=f'<b>{group} - DIV {div}</b><br>Value: %{{y:.3f}}<br>n={len(recording_values)}<extra></extra>'
                    ),
                    row=1, col=col
                )
                
                # Add violin if enough data
                if len(recording_values) >= 4:
                    try:
                        kde_data = calculate_half_violin_data(recording_values)
                        x_data = kde_data.get('x')
                        if x_data is not None and len(x_data) > 0:
                            if isinstance(x_data, np.ndarray):
                                x_data = x_data.tolist()
                            
                            fig.add_trace(
                                go.Violin(
                                    x=[x_base] * len(x_data),
                                    y=x_data,
                                    width=0.8,
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
            
            # Add mean indicator
            try:
                mean_value = np.mean(recording_values)
                fig.add_trace(
                    go.Scatter(
                        x=[x_base],
                        y=[mean_value],
                        mode='markers',
                        marker=dict(
                            color='red',
                            size=10,
                            opacity=1.0,
                            line=dict(width=2, color='black'),
                            symbol='x'
                        ),
                        showlegend=False,
                        hovertemplate=f'<b>Mean: {mean_value:.3f}</b><br>n={len(recording_values)} recordings<extra></extra>'
                    ),
                    row=1, col=col
                )
            except Exception as e:
                print(f"⚠️ Mean calculation failed for {group} DIV {div}: {e}")
        
        # Update x-axis for this subplot
        fig.update_xaxes(
            tickvals=list(range(1, len(filtered_groups) + 1)),
            ticktext=filtered_groups,
            title_text="Group" if col == len(filtered_divs)//2 + 1 else "",
            showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.5)',
            linecolor='black', linewidth=1,
            range=[0.5, len(filtered_groups) + 0.5],
            row=1, col=col
        )
        
        # Add "No Data" annotation for empty age subplots
        if not div_has_data:
            y_center = 0.5  # Will be adjusted after Y-range calculation
            fig.add_annotation(
                x=len(filtered_groups) / 2 + 0.5,
                y=y_center,
                text="<b>No Recordings</b>",
                showarrow=False,
                font=dict(size=16, color='lightgray'),
                row=1, col=col
            )
    
    # Layout
    annotations = []
    annotations.append(
        dict(
            text="Recording-Level by Age: Group comparisons within each age (MEA-NAP colors by group)",
            showarrow=False,
            xref="paper", yref="paper",
            x=0.5, y=1.05,
            font=dict(size=10, color='blue'),
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
        margin=dict(b=60, t=120, l=60, r=60)
    )
    
    # APPLY Y-AXIS CONTROLS
    y_min_final, y_max_final = calculate_y_range(plot_data, y_range_mode, y_min, y_max)
    
    # Update y-axis
    fig.update_yaxes(
        title_text=f"<b>{get_metric_label(metric)}</b>",
        range=[y_min_final, y_max_final],  # USE CALCULATED Y-RANGE
        showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.5)',
        linecolor='black', linewidth=1,
        zeroline=True, zerolinecolor='rgba(200,200,200,0.5)'
    )
    
    print(f"   ✅ Created RECORDING-LEVEL by age plot: {total_recordings} recordings across {len(filtered_divs)} age subplots")
    print(f"   📊 Y-axis range: [{y_min_final:.2f}, {y_max_final:.2f}] ({'manual' if y_range_mode == 'manual' else 'auto'})")
    
    return fig

# WRAPPER FUNCTIONS FOR RECORDING LEVEL PLOTS WITH Y-AXIS SUPPORT
def create_half_violin_plot_by_group_recording_level(data, metric, title, selected_groups=None, selected_divs=None,
                                                    y_range_mode='auto', y_min=None, y_max=None):
    """
    Wrapper function for recording-level by group plots with Y-axis controls
    """
    return create_recording_level_violin_plot_by_group(data, metric, title, selected_groups, selected_divs,
                                                      y_range_mode=y_range_mode, y_min=y_min, y_max=y_max)

def create_half_violin_plot_by_age_recording_level(data, metric, title, selected_groups=None, selected_divs=None,
                                                  y_range_mode='auto', y_min=None, y_max=None):
    """
    Wrapper function for recording-level by age plots with Y-axis controls
    """
    return create_recording_level_violin_plot_by_age(data, metric, title, selected_groups, selected_divs,
                                                    y_range_mode=y_range_mode, y_min=y_min, y_max=y_max)

# ANALYSIS FUNCTION (unchanged)
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
