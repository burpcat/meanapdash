# utils/__init__.py - MEA-NAP Utils Package
"""
MEA-NAP Dashboard Utilities Package

This package contains utility modules for the MEA-NAP dashboard:
- metric_processors: Metric-specific processing functions
- config: Centralized configuration constants
- data_helpers: Data processing and validation utilities
- visualization_helpers: Visualization utilities and styling

Example usage:
    from utils import process_metric, get_metric_label, NEURONAL_NODE_METRICS
    from utils.metric_processors import process_FRActive_metric
    from utils.config import MATLAB_COLORS, PLOT_CONFIG
    from utils.data_helpers import clean_numeric_array, calculate_basic_stats
    from utils.visualization_helpers import apply_mea_nap_styling
"""

__version__ = "2.0.0"
__author__ = "MEA-NAP Dashboard Team"

# =============================================================================
# CORE IMPORTS - Most commonly used functions
# =============================================================================

# Metric Processing
from .metric_processors import (
    NEURONAL_METRIC_PROCESSORS,
    get_available_metrics,
    is_metric_available,
    get_metric_processor,
    process_metric,
    get_electrode_level_metrics,
    get_recording_level_metrics,
    is_electrode_level_metric,
    is_recording_level_metric
)

# Configuration
from .config import (
    NEURONAL_NODE_METRICS,
    NEURONAL_RECORDING_METRICS,
    METRIC_LABELS,
    METRIC_TITLES,
    METRIC_FIELD_MAP,
    PLOT_TYPE_OPTIONS,
    VISUALIZATION_TYPE_OPTIONS,
    MATLAB_COLORS,
    MATLAB_FILL_COLORS,
    PLOT_CONFIG,
    GRAPH_CONFIG,
    MEA_NAP_SETTINGS,
    DEFAULT_VALUES,
    get_metric_label,
    get_metric_title,
    get_metric_field_name,
    get_matlab_color,
    get_matlab_fill_color,
    is_electrode_level_metric as config_is_electrode_level_metric,
    is_recording_level_metric as config_is_recording_level_metric,
    validate_activity_type,
    validate_comparison_type,
    get_graph_config,
    get_default_metric
)

# Data Helpers
from .data_helpers import (
    validate_data_structure,
    validate_metric_data,
    validate_experiment_data,
    is_valid_numeric_value,
    clean_numeric_array,
    filter_by_threshold,
    remove_outliers,
    calculate_basic_stats,
    calculate_active_electrodes,
    calculate_active_electrode_mean,
    calculate_confidence_interval,
    format_data_for_plotting,
    create_summary_table,
    get_data_info,
    check_data_quality
)

# Visualization Helpers
from .visualization_helpers import (
    apply_mea_nap_styling,
    create_subplot_layout,
    update_subplot_axes,
    update_age_based_axes,
    prepare_violin_data,
    organize_plot_data,
    add_individual_points,
    add_violin_shape,
    add_mean_indicator,
    add_sample_size_annotation,
    generate_export_filename,
    create_empty_plot,
    create_error_plot,
    get_div_color_scheme,
    determine_plot_type,
    calculate_plot_dimensions,
    validate_plot_data
)

# =============================================================================
# CONVENIENCE FUNCTIONS - High-level interface
# =============================================================================

def get_all_metrics():
    """Get all available metrics grouped by type"""
    return {
        'node_metrics': [opt['value'] for opt in NEURONAL_NODE_METRICS],
        'recording_metrics': [opt['value'] for opt in NEURONAL_RECORDING_METRICS],
        'electrode_level': get_electrode_level_metrics(),
        'recording_level': get_recording_level_metrics()
    }

def get_metric_info(metric: str):
    """Get comprehensive information about a metric"""
    return {
        'name': metric,
        'label': get_metric_label(metric),
        'title': get_metric_title(metric),
        'field_name': get_metric_field_name(metric),
        'is_electrode_level': is_electrode_level_metric(metric),
        'is_recording_level': is_recording_level_metric(metric),
        'is_available': is_metric_available(metric)
    }

def get_visualization_config(metric: str, comparison: str, groups: list, divs: list):
    """Get complete visualization configuration for a metric"""
    return {
        'metric_info': get_metric_info(metric),
        'colors': get_div_color_scheme(divs),
        'plot_config': PLOT_CONFIG,
        'title': f"{get_metric_title(metric)} by {comparison.replace('by', ' by ').title()}",
        'y_axis_title': get_metric_label(metric),
        'filename': generate_export_filename(metric, comparison, groups, divs)
    }

def validate_visualization_request(metric: str, comparison: str, groups: list, divs: list):
    """Validate a visualization request"""
    errors = []
    
    if not is_metric_available(metric):
        errors.append(f"Metric '{metric}' is not available")
    
    if not validate_comparison_type(comparison):
        errors.append(f"Comparison type '{comparison}' is not valid")
    
    if not groups:
        errors.append("At least one group must be selected")
    
    if not divs:
        errors.append("At least one DIV must be selected")
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors
    }

# =============================================================================
# NEURONAL VISUALIZATION FUNCTION - Added to utils package
# =============================================================================

def create_neuronal_visualization(processed_data, metric, comparison, title, groups, selected_divs):
    """
    Create neuronal visualization using processed data
    
    This function routes to the appropriate visualization based on comparison type.
    It's been moved to the utils package to avoid circular imports.
    
    Args:
        processed_data: Data processed by metric-specific function
        metric: The metric name
        comparison: Type of comparison (nodebygroup, nodebyage, etc.)
        title: Plot title
        groups: Selected groups
        selected_divs: Selected DIVs
    
    Returns:
        Plotly figure
    """
    # Import here to avoid circular imports
    from components.neuronal_activity import (
        create_half_violin_plot_by_group,
        create_half_violin_plot_by_age
    )
    
    # Get the field name to use in the data
    field_name = get_metric_field_name(metric)
    
    # Route to appropriate visualization function
    if comparison in ['nodebygroup', 'recordingsbygroup']:
        return create_half_violin_plot_by_group(processed_data, field_name, title, groups, selected_divs)
    elif comparison in ['nodebyage', 'recordingsbyage']:
        return create_half_violin_plot_by_age(processed_data, field_name, title, groups, selected_divs)
    else:
        return create_error_plot(f"Unknown comparison type: {comparison}")

# =============================================================================
# PACKAGE METADATA
# =============================================================================

__all__ = [
    # Core functions
    'process_metric',
    'get_available_metrics',
    'is_metric_available',
    'get_metric_processor',
    'create_neuronal_visualization',
    
    # Configuration
    'NEURONAL_NODE_METRICS',
    'NEURONAL_RECORDING_METRICS',
    'METRIC_LABELS',
    'METRIC_TITLES',
    'MATLAB_COLORS',
    'PLOT_CONFIG',
    'get_metric_label',
    'get_metric_title',
    'get_metric_field_name',
    'get_matlab_color',
    
    # Data helpers
    'clean_numeric_array',
    'validate_data_structure',
    'calculate_basic_stats',
    'format_data_for_plotting',
    
    # Visualization helpers
    'apply_mea_nap_styling',
    'create_subplot_layout',
    'organize_plot_data',
    'create_empty_plot',
    'create_error_plot',
    
    # Convenience functions
    'get_all_metrics',
    'get_metric_info',
    'get_visualization_config',
    'validate_visualization_request'
]

# =============================================================================
# PACKAGE INFORMATION
# =============================================================================

def get_package_info():
    """Get information about the utils package"""
    return {
        'name': 'MEA-NAP Utils',
        'version': __version__,
        'author': __author__,
        'description': 'Utility functions for MEA-NAP dashboard',
        'modules': {
            'metric_processors': 'Metric-specific processing functions',
            'config': 'Centralized configuration constants',
            'data_helpers': 'Data processing and validation utilities',
            'visualization_helpers': 'Visualization utilities and styling'
        },
        'available_metrics': len(get_available_metrics()),
        'electrode_level_metrics': len(get_electrode_level_metrics()),
        'recording_level_metrics': len(get_recording_level_metrics())
    }

# Print package info when imported (for debugging)
if __name__ == '__main__':
    import json
    print("MEA-NAP Utils Package Information:")
    print(json.dumps(get_package_info(), indent=2))