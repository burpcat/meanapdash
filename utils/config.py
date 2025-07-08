# utils/config.py - Updated with User-Configurable Active Threshold
"""
MEA-NAP Dashboard Configuration

Updated to match user's specific analysis parameters:
- Configurable active electrode threshold (0.01 Hz for conservative analysis)
- Proper MEA-NAP 2B_GroupComparisons methodology
"""

from typing import Dict, List, Any

# =============================================================================
# MEA-NAP SPECIFIC SETTINGS - Updated for User's Analysis
# =============================================================================

# MEA-NAP Data Processing Settings - User Configurable
MEA_NAP_SETTINGS = {
    # IMPORTANT: User's conservative setting vs MEA-NAP default
    'active_electrode_threshold': 0.01,    # User's setting: 0.01 Hz (conservative)
    # 'active_electrode_threshold': 0.1,   # MEA-NAP default: 0.1 Hz (standard)
    
    'burst_detection_threshold': 0.0,      # Minimum burst rate for valid bursts
    'min_electrode_count': 1,              # Minimum electrodes for valid recording
    'max_outlier_factor': 1.5,             # IQR factor for outlier detection
    'kde_bandwidth_factor': 1.06           # Scott's rule bandwidth factor
}

# Data Processing Method Configuration
DATA_PROCESSING_CONFIG = {
    'node_level_aggregation': 'combine_all_electrodes',     # MEA-NAP method: combine ALL electrodes per group
    'recording_level_aggregation': 'summary_per_recording', # MEA-NAP method: one summary per recording
    'filtering_method': 'mea_nap_standard',                 # Use MEA-NAP filtering criteria
    'active_threshold_source': 'user_configured'            # Use user's threshold, not MEA-NAP default
}

# =============================================================================
# METRIC DEFINITIONS - Same as before but with aggregation type info
# =============================================================================

# Neuronal Node-Level Metrics (Electrode-Level Aggregation)
NEURONAL_NODE_METRICS = [
    {'label': 'Mean Firing Rate Node', 'value': 'FR', 'aggregation': 'node_level'},
    {'label': 'Unit Burst Rate (per minute)', 'value': 'channelBurstRate', 'aggregation': 'node_level'},
    {'label': 'Unit within Burst Firing Rate', 'value': 'channelFRinBurst', 'aggregation': 'node_level'},
    {'label': 'Unit Burst Duration', 'value': 'channelBurstDur', 'aggregation': 'node_level'},
    {'label': 'Unit ISI within Burst', 'value': 'channelISIwithinBurst', 'aggregation': 'node_level'},
    {'label': 'Unit ISI outside Burst', 'value': 'channeISIoutsideBurst', 'aggregation': 'node_level'},
    {'label': 'Unit fraction for spikes in bursts', 'value': 'channelFracSpikesInBursts', 'aggregation': 'node_level'}
]

# Neuronal Recording-Level Metrics (Recording-Level Aggregation)
NEURONAL_RECORDING_METRICS = [
    {'label': 'Mean Firing Rate Active Node', 'value': 'FRActive', 'aggregation': 'recording_level'},
    {'label': 'Number of Active Electrodes', 'value': 'numActiveElec', 'aggregation': 'recording_level'},
    {'label': 'Mean Firing Rate', 'value': 'FRmean', 'aggregation': 'recording_level'},
    {'label': 'Median Firing Rate', 'value': 'FRmedian', 'aggregation': 'recording_level'},
    {'label': 'Network Burst Rate (per min)', 'value': 'NBurstRate', 'aggregation': 'recording_level'},
    {'label': 'Mean Network Burst Length (s)', 'value': 'meanNBstLengthS', 'aggregation': 'recording_level'},
    {'label': 'Mean ISI within Network Bursts (ms)', 'value': 'meanISIWithinNbursts_ms', 'aggregation': 'recording_level'},
    {'label': 'Mean ISI outside Network Bursts (ms)', 'value': 'meanISIoutsideNbursts_ms', 'aggregation': 'recording_level'},
    {'label': 'CV of Inter-Network-Burst Intervals', 'value': 'CVofINBI', 'aggregation': 'recording_level'},
    {'label': 'Fraction of Spikes in Network Bursts', 'value': 'fracInNburst', 'aggregation': 'recording_level'},
    {'label': 'Mean Channels in Network Bursts', 'value': 'meanNumChansInvolvedInNbursts', 'aggregation': 'recording_level'}
]

# Metric Labels with Units - Updated with aggregation info
METRIC_LABELS = {
    # Node-level metrics (electrode-level data)
    'FR': 'Firing Rate (Hz)',
    'channelBurstRate': 'Burst Rate (per minute)',
    'channelBurstDur': 'Burst Duration (ms)',
    'channelISIwithinBurst': 'ISI Within Burst (ms)',
    'channeISIoutsideBurst': 'ISI Outside Burst (ms)',
    'channelFracSpikesInBursts': 'Fraction Spikes in Bursts',
    'channelFRinBurst': 'Within-Burst Firing Rate (Hz)',
    
    # Recording-level metrics (one value per recording)
    'FRActive': f'Mean Active Firing Rate (>{MEA_NAP_SETTINGS["active_electrode_threshold"]} Hz)',
    'numActiveElec': f'Number of Active Electrodes (>{MEA_NAP_SETTINGS["active_electrode_threshold"]} Hz)',
    'FRmean': 'Mean Firing Rate (Hz)',
    'FRmedian': 'Median Firing Rate (Hz)',
    'NBurstRate': 'Network Burst Rate (per minute)',
    'meanNBstLengthS': 'Mean Network Burst Length (s)',
    'meanISIWithinNbursts_ms': 'Mean ISI Within Network Bursts (ms)',
    'meanISIoutsideNbursts_ms': 'Mean ISI Outside Network Bursts (ms)',
    'CVofINBI': 'CV of Inter-Network-Burst Intervals',
    'fracInNburst': 'Fraction of Spikes in Network Bursts'
}

# Human-Readable Metric Titles - Updated with aggregation clarity
METRIC_TITLES = {
    # Node-level (electrode-level) - matches MEA-NAP "Unit XXX by Group"
    'FR': 'Unit Firing Rate',  # Changed from "Mean Firing Rate Node" to match MEA-NAP
    'channelBurstRate': 'Unit Burst Rate',
    'channelFRinBurst': 'Unit within Burst Firing Rate',
    'channelBurstDur': 'Unit Burst Duration',
    'channelISIwithinBurst': 'Unit ISI within Burst',
    'channeISIoutsideBurst': 'Unit ISI outside Burst',
    'channelFracSpikesInBursts': 'Unit fraction for spikes in bursts',
    
    # Recording-level - matches MEA-NAP recording-level plots
    'FRActive': 'Mean Active Firing Rate',  # This is a calculated recording-level metric
    'numActiveElec': 'Number of Active Electrodes',
    'NBurstRate': 'Network Burst Rate',
    'FRmean': 'Mean Firing Rate',
    'FRmedian': 'Median Firing Rate',
    'meanNBstLengthS': 'Mean Network Burst Length',
    'meanISIWithinNbursts_ms': 'Mean ISI Within Network Bursts',
    'meanISIoutsideNbursts_ms': 'Mean ISI Outside Network Bursts',
    'CVofINBI': 'CV of Inter-Network-Burst Intervals',
    'fracInNburst': 'Fraction of Spikes in Network Bursts'
}

# Metric to Field Name Mapping (for special cases)
METRIC_FIELD_MAP = {
    'FRActive': 'FRActiveNode',  # Special case - calculated field
    'FR': 'FR',
    'channelBurstRate': 'channelBurstRate',
    'channelFRinBurst': 'channelFRinBurst',
    'channelBurstDur': 'channelBurstDur',
    'channelISIwithinBurst': 'channelISIwithinBurst',
    'channeISIoutsideBurst': 'channeISIoutsideBurst',
    'channelFracSpikesInBursts': 'channelFracSpikesInBursts',
    'numActiveElec': 'numActiveElec',
    'NBurstRate': 'NBurstRate',
    'FRmean': 'FRmean',
    'FRmedian': 'FRmedian'
}

# =============================================================================
# UI OPTIONS - Same as before
# =============================================================================

PLOT_TYPE_OPTIONS = [
    {'label': ' Violin Plot', 'value': 'violin'},
    {'label': ' Box Plot', 'value': 'box'},
    {'label': ' Bar Plot', 'value': 'bar'}
]

VISUALIZATION_TYPE_OPTIONS = [
    {'label': 'Half Violin Plot', 'value': 'violin'},
    {'label': 'Box Plot', 'value': 'box'},
    {'label': 'Bar Chart', 'value': 'bar'}
]

DEFAULT_VALUES = {
    'plot_type': 'violin',
    'visualization_type': 'violin',
    'node_metric': 'FR',
    'recording_metric': 'numActiveElec'
}

# =============================================================================
# VISUALIZATION SETTINGS - Same as before
# =============================================================================

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

PLOT_CONFIG = {
    'height': 500,
    'plot_bgcolor': 'white',
    'paper_bgcolor': 'white',
    'font_family': 'Arial',
    'font_size': 12,
    'font_color': 'black',
    'grid_color': 'rgba(200,200,200,0.5)',
    'line_color': 'black',
    'line_width': 1,
    'title_font_size': 16,
    'axis_font_size': 12
}

GRAPH_CONFIG = {
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
    'toImageButtonOptions': {
        'format': 'svg',
        'height': 600,
        'width': 800,
        'scale': 1
    }
}

# =============================================================================
# DATA QUALITY SETTINGS - Updated for user's conservative analysis
# =============================================================================

DATA_QUALITY = {
    'min_experiments_per_group': 1,        # Minimum experiments per group
    'min_electrodes_per_recording': 1,     # Minimum electrodes per recording
    'max_nan_percentage': 0.5,             # Maximum percentage of NaN values allowed
    'min_valid_values': 1,                 # Minimum valid values for plotting
    'expected_sparse_data': True           # Expect sparse data with conservative thresholds
}

# =============================================================================
# APPLICATION SETTINGS - Same as before
# =============================================================================

DASHBOARD_CONFIG = {
    'title': 'MEA-NAP Dashboard',
    'description': 'Interactive visualization of Microelectrode Array data from the MEA-NAP pipeline',
    'version': '2.0.0',
    'debug': True,
    'port': 8050,
    'host': '127.0.0.1'
}

EXPORT_CONFIG = {
    'default_format': 'svg',
    'supported_formats': ['svg', 'png', 'pdf'],
    'default_filename': 'mea_nap_visualization',
    'default_width': 800,
    'default_height': 600,
    'default_scale': 1
}

DATA_LOADING_CONFIG = {
    'experiment_mat_folder': 'ExperimentMatFiles',
    'supported_extensions': ['.mat'],
    'max_file_size_mb': 100,
    'timeout_seconds': 300
}

# =============================================================================
# VALIDATION SETTINGS - Same as before
# =============================================================================

VALID_ACTIVITY_TYPES = ['neuronal', 'network']
VALID_COMPARISON_TYPES = ['nodebygroup', 'nodebyage', 'recordingsbygroup', 'recordingsbyage']
VALID_NETWORK_COMPARISON_TYPES = ['nodebygroup', 'nodebyage', 'recordingsbygroup', 'recordingsbyage', 'graphmetricsbylag', 'nodecartography']

# Metric Validation - Updated to reflect aggregation types
NODE_LEVEL_METRICS = [
    'FR', 'channelBurstRate', 'channelFRinBurst', 
    'channelBurstDur', 'channelISIwithinBurst', 'channeISIoutsideBurst', 
    'channelFracSpikesInBursts'
]

RECORDING_LEVEL_METRICS = [
    'FRActive', 'numActiveElec', 'NBurstRate', 'FRmean', 'FRmedian', 'meanNBstLengthS',
    'meanISIWithinNbursts_ms', 'meanISIoutsideNbursts_ms', 'CVofINBI',
    'fracInNburst', 'meanNumChansInvolvedInNbursts'
]

# =============================================================================
# HELPER FUNCTIONS - Updated with aggregation info
# =============================================================================

def get_metric_label(metric: str) -> str:
    """Get the human-readable label for a metric"""
    return METRIC_LABELS.get(metric, metric)

def get_metric_title(metric: str) -> str:
    """Get the human-readable title for a metric"""
    return METRIC_TITLES.get(metric, metric)

def get_metric_field_name(metric: str) -> str:
    """Get the field name for a metric (handles special cases)"""
    return METRIC_FIELD_MAP.get(metric, metric)

def is_node_level_metric(metric: str) -> bool:
    """Check if metric uses node-level (electrode-level) aggregation"""
    return metric in NODE_LEVEL_METRICS

def is_recording_level_metric(metric: str) -> bool:
    """Check if metric uses recording-level aggregation"""
    return metric in RECORDING_LEVEL_METRICS

def get_matlab_color(div: int) -> str:
    """Get MEA-NAP MATLAB color for a DIV"""
    return MATLAB_COLORS.get(div, MATLAB_COLORS['default'])

def get_matlab_fill_color(div: int) -> str:
    """Get MEA-NAP MATLAB fill color for a DIV"""
    return MATLAB_FILL_COLORS.get(div, MATLAB_FILL_COLORS['default'])

def validate_activity_type(activity: str) -> bool:
    """Validate activity type"""
    return activity in VALID_ACTIVITY_TYPES

def validate_comparison_type(comparison: str, activity: str = 'neuronal') -> bool:
    """Validate comparison type for given activity"""
    if activity == 'neuronal':
        return comparison in VALID_COMPARISON_TYPES
    elif activity == 'network':
        return comparison in VALID_NETWORK_COMPARISON_TYPES
    return False

def get_graph_config(filename: str = None) -> Dict[str, Any]:
    """Get graph configuration with optional custom filename"""
    config = GRAPH_CONFIG.copy()
    if filename:
        config['toImageButtonOptions']['filename'] = filename
    return config

def get_default_metric(metric_type: str) -> str:
    """Get default metric for a given type"""
    if metric_type in ['node', 'electrode']:
        return DEFAULT_VALUES['node_metric']
    elif metric_type in ['recording', 'network']:
        return DEFAULT_VALUES['recording_metric']
    return DEFAULT_VALUES['node_metric']

def get_active_electrode_threshold() -> float:
    """Get the configured active electrode threshold"""
    return MEA_NAP_SETTINGS['active_electrode_threshold']

def get_aggregation_type(metric: str) -> str:
    """Get the aggregation type for a metric"""
    if is_node_level_metric(metric):
        return 'node_level'
    elif is_recording_level_metric(metric):
        return 'recording_level'
    else:
        return 'unknown'

def get_metric_info(metric: str) -> Dict[str, Any]:
    """Get comprehensive information about a metric"""
    return {
        'name': metric,
        'label': get_metric_label(metric),
        'title': get_metric_title(metric),
        'field_name': get_metric_field_name(metric),
        'aggregation_type': get_aggregation_type(metric),
        'is_node_level': is_node_level_metric(metric),
        'is_recording_level': is_recording_level_metric(metric)
    }

# Backward compatibility aliases
ELECTRODE_LEVEL_METRICS = NODE_LEVEL_METRICS
is_electrode_level_metric = is_node_level_metric