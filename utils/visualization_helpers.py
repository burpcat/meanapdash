# utils/visualization_helpers.py - Visualization Utilities
"""
MEA-NAP Visualization Utilities

This module contains utility functions for creating and customizing visualizations
in the MEA-NAP dashboard. These functions handle common visualization tasks,
styling, and formatting.

Function Categories:
- Plot Styling and Configuration
- Data Preparation for Plots
- Statistical Visualization Helpers
- Export and Formatting Utilities
- Color and Theme Management
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from utils.config import (
    MATLAB_COLORS, MATLAB_FILL_COLORS, PLOT_CONFIG, METRIC_LABELS,
    get_matlab_color, get_matlab_fill_color, get_metric_label
)
from utils.data_helpers import clean_numeric_array, calculate_basic_stats
from data_processing.utilities import calculate_half_violin_data

# =============================================================================
# PLOT STYLING AND CONFIGURATION
# =============================================================================

def apply_mea_nap_styling(fig: go.Figure, title: str = "", 
                         y_axis_title: str = "", height: int = 500) -> go.Figure:
    """
    Apply MEA-NAP MATLAB-style formatting to a figure
    
    Args:
        fig: Plotly figure object
        title: Plot title
        y_axis_title: Y-axis title
        height: Plot height
        
    Returns:
        go.Figure: Styled figure
    """
    fig.update_layout(
        title=dict(
            text=f'<b>{title}</b>',
            x=0.5,
            font=dict(size=PLOT_CONFIG['title_font_size'], color=PLOT_CONFIG['font_color'])
        ),
        height=height,
        plot_bgcolor=PLOT_CONFIG['plot_bgcolor'],
        paper_bgcolor=PLOT_CONFIG['paper_bgcolor'],
        font=dict(
            family=PLOT_CONFIG['font_family'],
            size=PLOT_CONFIG['font_size'],
            color=PLOT_CONFIG['font_color']
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update y-axis
    if y_axis_title:
        fig.update_yaxes(
            title_text=y_axis_title,
            showgrid=True,
            gridwidth=PLOT_CONFIG['line_width'],
            gridcolor=PLOT_CONFIG['grid_color'],
            linecolor=PLOT_CONFIG['line_color'],
            linewidth=PLOT_CONFIG['line_width'],
            zeroline=True,
            zerolinecolor=PLOT_CONFIG['grid_color']
        )
    
    return fig

def create_subplot_layout(groups: List[str], shared_yaxes: bool = True) -> go.Figure:
    """
    Create subplot layout for group-based visualizations
    
    Args:
        groups: List of group names
        shared_yaxes: Whether to share y-axes across subplots
        
    Returns:
        go.Figure: Figure with subplot layout
    """
    return make_subplots(
        rows=1, cols=len(groups),
        subplot_titles=[f'<b>{g}</b>' for g in groups],
        shared_yaxes=shared_yaxes,
        horizontal_spacing=0.08 if len(groups) > 1 else 0
    )

def update_subplot_axes(fig: go.Figure, divs: List[int], num_groups: int, 
                       y_axis_title: str = "", max_y: float = 1.0) -> go.Figure:
    """
    Update axes for subplots with consistent styling
    
    Args:
        fig: Plotly figure object
        divs: List of DIV values
        num_groups: Number of groups (columns)
        y_axis_title: Y-axis title
        max_y: Maximum y-value for range setting
        
    Returns:
        go.Figure: Figure with updated axes
    """
    # Update x-axes for each subplot
    for col in range(1, num_groups + 1):
        fig.update_xaxes(
            tickvals=list(range(1, len(divs) + 1)),
            ticktext=[str(div) for div in divs],
            title_text="Age" if col == num_groups // 2 + 1 else "",
            showgrid=True,
            gridwidth=PLOT_CONFIG['line_width'],
            gridcolor=PLOT_CONFIG['grid_color'],
            linecolor=PLOT_CONFIG['line_color'],
            linewidth=PLOT_CONFIG['line_width'],
            row=1, col=col
        )
    
    # Update y-axis
    fig.update_yaxes(
        title_text=y_axis_title,
        range=[0, max_y * 1.1] if max_y > 0 else [0, 1],
        showgrid=True,
        gridwidth=PLOT_CONFIG['line_width'],
        gridcolor=PLOT_CONFIG['grid_color'],
        linecolor=PLOT_CONFIG['line_color'],
        linewidth=PLOT_CONFIG['line_width'],
        zeroline=True,
        zerolinecolor=PLOT_CONFIG['grid_color']
    )
    
    return fig

def update_age_based_axes(fig: go.Figure, divs: List[int], num_groups: int, 
                         y_axis_title: str = "", max_y: float = 1.0) -> go.Figure:
    """
    Update axes for age-based visualizations
    
    Args:
        fig: Plotly figure object
        divs: List of DIV values
        num_groups: Number of groups (columns)
        y_axis_title: Y-axis title
        max_y: Maximum y-value for range setting
        
    Returns:
        go.Figure: Figure with updated axes
    """
    # Update x-axes for age-based plots
    for col in range(1, num_groups + 1):
        fig.update_xaxes(
            tickvals=divs,
            ticktext=[str(div) for div in divs],
            title_text="Age" if col == num_groups // 2 + 1 else "",
            range=[min(divs) - 2, max(divs) + 2] if divs else [0, 100],
            showgrid=True,
            gridwidth=PLOT_CONFIG['line_width'],
            gridcolor=PLOT_CONFIG['grid_color'],
            linecolor=PLOT_CONFIG['line_color'],
            linewidth=PLOT_CONFIG['line_width'],
            row=1, col=col
        )
    
    # Update y-axis
    fig.update_yaxes(
        title_text=y_axis_title,
        range=[0, max_y * 1.1] if max_y > 0 else [0, 1],
        showgrid=True,
        gridwidth=PLOT_CONFIG['line_width'],
        gridcolor=PLOT_CONFIG['grid_color'],
        linecolor=PLOT_CONFIG['line_color'],
        linewidth=PLOT_CONFIG['line_width'],
        zeroline=True,
        zerolinecolor=PLOT_CONFIG['grid_color']
    )
    
    return fig

# =============================================================================
# DATA PREPARATION FOR PLOTS
# =============================================================================

def prepare_violin_data(values: Union[List, np.ndarray], 
                       min_points: int = 4) -> Dict[str, Any]:
    """
    Prepare data for violin plots with appropriate fallback handling
    
    Args:
        values: Array of values
        min_points: Minimum points required for violin plot
        
    Returns:
        Dict: Prepared data with plot type recommendation
    """
    clean_values = clean_numeric_array(values)
    
    if len(clean_values) == 0:
        return {
            'values': [],
            'plot_type': 'empty',
            'kde_data': None,
            'stats': None
        }
    elif len(clean_values) == 1:
        return {
            'values': clean_values,
            'plot_type': 'single_point',
            'kde_data': None,
            'stats': calculate_basic_stats(clean_values)
        }
    elif len(clean_values) < min_points:
        return {
            'values': clean_values,
            'plot_type': 'scatter',
            'kde_data': None,
            'stats': calculate_basic_stats(clean_values)
        }
    else:
        kde_data = calculate_half_violin_data(clean_values)
        return {
            'values': clean_values,
            'plot_type': 'violin',
            'kde_data': kde_data,
            'stats': calculate_basic_stats(clean_values)
        }

def organize_plot_data(data: Dict, metric: str, groups: List[str], 
                      divs: List[int]) -> Dict[str, Dict[int, List[float]]]:
    """
    Organize data for plotting by group and DIV
    
    Args:
        data: Data dictionary
        metric: Metric name
        groups: List of groups
        divs: List of DIVs
        
    Returns:
        Dict: Organized data structure {group: {div: [values]}}
    """
    plot_data = {}
    
    for group in groups:
        if group not in data['by_group']:
            continue
            
        group_data = data['by_group'][group]
        if metric not in group_data:
            continue
        
        plot_data[group] = {}
        
        # For each DIV, extract the relevant data
        for div in divs:
            div_values = []
            
            # Check if this is recording-level data (has exp_names)
            if 'exp_names' in group_data and group_data['exp_names']:
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
            plot_data[group][div] = clean_numeric_array(div_values).tolist()
    
    return plot_data

# =============================================================================
# STATISTICAL VISUALIZATION HELPERS
# =============================================================================

def add_individual_points(fig: go.Figure, x_base: float, values: List[float], 
                         div: int, col: int, showlegend: bool = True) -> go.Figure:
    """
    Add individual data points to a plot with MEA-NAP styling
    
    Args:
        fig: Plotly figure object
        x_base: Base x-position
        values: List of values
        div: DIV value (for color coding)
        col: Column number (for subplot)
        showlegend: Whether to show legend
        
    Returns:
        go.Figure: Figure with added points
    """
    if not values:
        return fig
    
    # Add jitter for better visualization
    jitter = np.random.normal(0, 0.02, size=len(values))
    
    fig.add_trace(
        go.Scatter(
            x=[x_base + j for j in jitter],
            y=values,
            mode='markers',
            marker=dict(
                color='black',  # MEA-NAP style: black dots
                size=3,
                opacity=0.6
            ),
            name=f'DIV {div}',
            legendgroup=f'DIV {div}',
            showlegend=showlegend,
            hovertemplate=f'DIV {div}: %{{y:.2f}}<extra></extra>'
        ),
        row=1, col=col
    )
    
    return fig

def add_violin_shape(fig: go.Figure, x_base: float, kde_data: Dict, 
                    div: int, col: int) -> go.Figure:
    """
    Add violin shape to a plot
    
    Args:
        fig: Plotly figure object
        x_base: Base x-position
        kde_data: KDE data from calculate_half_violin_data
        div: DIV value (for color coding)
        col: Column number (for subplot)
        
    Returns:
        go.Figure: Figure with added violin
    """
    color = get_matlab_color(div)
    fill_color = get_matlab_fill_color(div)
    
    fig.add_trace(
        go.Violin(
            x=[x_base] * len(kde_data['x']),
            y=kde_data['x'],
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
    
    return fig

def add_mean_indicator(fig: go.Figure, x_base: float, mean_value: float, 
                      col: int) -> go.Figure:
    """
    Add mean indicator to a plot
    
    Args:
        fig: Plotly figure object
        x_base: Base x-position
        mean_value: Mean value
        col: Column number (for subplot)
        
    Returns:
        go.Figure: Figure with added mean indicator
    """
    fig.add_trace(
        go.Scatter(
            x=[x_base],
            y=[mean_value],
            mode='markers',
            marker=dict(
                color='black',
                size=8,
                opacity=1.0
            ),
            showlegend=False,
            hovertemplate=f'Mean: {mean_value:.2f}<extra></extra>'
        ),
        row=1, col=col
    )
    
    return fig

def add_sample_size_annotation(fig: go.Figure, x_base: float, sample_size: int, 
                              max_y: float, col: int) -> go.Figure:
    """
    Add sample size annotation to a plot
    
    Args:
        fig: Plotly figure object
        x_base: Base x-position
        sample_size: Sample size
        max_y: Maximum y-value for positioning
        col: Column number (for subplot)
        
    Returns:
        go.Figure: Figure with added annotation
    """
    fig.add_annotation(
        x=x_base,
        y=max_y * 1.05,
        text=f'n={sample_size}',
        showarrow=False,
        font=dict(size=10, color='black'),
        row=1, col=col
    )
    
    return fig

# =============================================================================
# EXPORT AND FORMATTING UTILITIES
# =============================================================================

def generate_export_filename(metric: str, comparison: str, groups: List[str], 
                            divs: List[int], custom_filename: str = None) -> str:
    """
    Generate appropriate filename for export
    
    Args:
        metric: Metric name
        comparison: Comparison type
        groups: List of groups
        divs: List of DIVs
        custom_filename: Custom filename if provided
        
    Returns:
        str: Generated filename
    """
    if custom_filename:
        return custom_filename
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    filename_parts = ["MEA-NAP"]
    
    if metric:
        filename_parts.append(metric)
    
    if comparison:
        filename_parts.append(comparison)
    
    if groups:
        filename_parts.append(f"group-{groups[0]}")
    
    if divs:
        filename_parts.append(f"DIV{divs[0]}")
    
    filename_parts.append(timestamp)
    
    return "_".join(filename_parts)

def create_empty_plot(title: str = "No data available") -> go.Figure:
    """
    Create an empty plot with informative message
    
    Args:
        title: Title for the empty plot
        
    Returns:
        go.Figure: Empty figure with message
    """
    fig = go.Figure()
    fig.update_layout(
        title=title,
        height=PLOT_CONFIG['height'],
        plot_bgcolor=PLOT_CONFIG['plot_bgcolor'],
        paper_bgcolor=PLOT_CONFIG['paper_bgcolor'],
        font=dict(
            family=PLOT_CONFIG['font_family'],
            size=PLOT_CONFIG['font_size'],
            color=PLOT_CONFIG['font_color']
        ),
        annotations=[
            dict(
                text="No data available for the selected criteria",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                font=dict(size=14, color='gray')
            )
        ]
    )
    return fig

def create_error_plot(error_message: str) -> go.Figure:
    """
    Create an error plot with error message
    
    Args:
        error_message: Error message to display
        
    Returns:
        go.Figure: Error figure with message
    """
    fig = go.Figure()
    fig.update_layout(
        title="Error",
        height=PLOT_CONFIG['height'],
        plot_bgcolor=PLOT_CONFIG['plot_bgcolor'],
        paper_bgcolor=PLOT_CONFIG['paper_bgcolor'],
        font=dict(
            family=PLOT_CONFIG['font_family'],
            size=PLOT_CONFIG['font_size'],
            color=PLOT_CONFIG['font_color']
        ),
        annotations=[
            dict(
                text=f"Error: {error_message}",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                font=dict(size=14, color='red')
            )
        ]
    )
    return fig

# =============================================================================
# COLOR AND THEME MANAGEMENT
# =============================================================================

def get_div_color_scheme(divs: List[int]) -> Dict[int, Dict[str, str]]:
    """
    Get color scheme for a list of DIVs
    
    Args:
        divs: List of DIV values
        
    Returns:
        Dict: Color scheme mapping {div: {'color': str, 'fill': str}}
    """
    color_scheme = {}
    
    for div in divs:
        color_scheme[div] = {
            'color': get_matlab_color(div),
            'fill': get_matlab_fill_color(div)
        }
    
    return color_scheme

def create_color_legend(divs: List[int]) -> List[go.Scatter]:
    """
    Create color legend traces for DIVs
    
    Args:
        divs: List of DIV values
        
    Returns:
        List[go.Scatter]: Legend traces
    """
    legend_traces = []
    
    for div in divs:
        legend_traces.append(
            go.Scatter(
                x=[None],
                y=[None],
                mode='markers',
                marker=dict(
                    color=get_matlab_color(div),
                    size=10
                ),
                name=f'DIV {div}',
                legendgroup=f'DIV {div}',
                showlegend=True
            )
        )
    
    return legend_traces

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def determine_plot_type(values: List[float]) -> str:
    """
    Determine the best plot type based on data characteristics
    
    Args:
        values: List of values
        
    Returns:
        str: Recommended plot type
    """
    if len(values) == 0:
        return 'empty'
    elif len(values) == 1:
        return 'single_point'
    elif len(values) < 4:
        return 'scatter'
    else:
        return 'violin'

def calculate_plot_dimensions(num_groups: int, base_width: int = 800) -> Tuple[int, int]:
    """
    Calculate appropriate plot dimensions based on number of groups
    
    Args:
        num_groups: Number of groups
        base_width: Base width for single group
        
    Returns:
        Tuple[int, int]: (width, height)
    """
    width = max(base_width, num_groups * 300)
    height = PLOT_CONFIG['height']
    
    return width, height

def validate_plot_data(data: Dict, metric: str, groups: List[str]) -> bool:
    """
    Validate that plot data is available and sufficient
    
    Args:
        data: Data dictionary
        metric: Metric name
        groups: List of groups
        
    Returns:
        bool: True if data is valid for plotting
    """
    if not data or 'by_group' not in data:
        return False
    
    for group in groups:
        if group not in data['by_group']:
            continue
        
        group_data = data['by_group'][group]
        if metric not in group_data:
            continue
        
        values = group_data[metric]
        if isinstance(values, (list, np.ndarray)) and len(values) > 0:
            return True
        elif not isinstance(values, (list, np.ndarray)) and values is not None:
            return True
    
    return False