# utils/data_helpers.py - Data Processing Utilities
"""
MEA-NAP Data Processing Utilities

This module contains utility functions for data processing, validation, and manipulation
used throughout the MEA-NAP dashboard. These functions handle common data operations
and ensure consistent data formatting.

Function Categories:
- Data Validation
- Data Filtering and Cleaning
- Data Structure Manipulation
- Statistical Calculations
- Data Formatting
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# DATA VALIDATION FUNCTIONS
# =============================================================================

def validate_data_structure(data: Dict, required_keys: List[str]) -> bool:
    """
    Validate that data dictionary has required keys
    
    Args:
        data: Data dictionary to validate
        required_keys: List of required keys
        
    Returns:
        bool: True if all required keys are present
    """
    return all(key in data for key in required_keys)

def validate_metric_data(data: Dict, metric: str, groups: List[str]) -> bool:
    """
    Validate that metric data is available for specified groups
    
    Args:
        data: Data dictionary
        metric: Metric name to validate
        groups: List of groups to check
        
    Returns:
        bool: True if metric data is available for all groups
    """
    if 'by_group' not in data:
        return False
        
    for group in groups:
        if group not in data['by_group']:
            return False
        if metric not in data['by_group'][group]:
            return False
        if not data['by_group'][group][metric]:
            return False
    
    return True

def validate_experiment_data(exp_data: Dict) -> bool:
    """
    Validate experiment data structure
    
    Args:
        exp_data: Experiment data dictionary
        
    Returns:
        bool: True if experiment data is valid
    """
    required_keys = ['group', 'div', 'activity']
    return validate_data_structure(exp_data, required_keys)

def is_valid_numeric_value(value: Any) -> bool:
    """
    Check if value is a valid numeric value (not NaN, not None, finite)
    
    Args:
        value: Value to check
        
    Returns:
        bool: True if value is valid numeric
    """
    if value is None:
        return False
    try:
        value = float(value)
        return np.isfinite(value)
    except (ValueError, TypeError):
        return False

# =============================================================================
# DATA FILTERING AND CLEANING FUNCTIONS
# =============================================================================

def clean_numeric_array(values: Union[List, np.ndarray]) -> np.ndarray:
    """
    Clean numeric array by removing NaN, infinite, and None values
    
    Args:
        values: Array of values to clean
        
    Returns:
        np.ndarray: Cleaned array
    """
    if not isinstance(values, np.ndarray):
        values = np.array(values)
    
    # Remove NaN, infinite, and None values
    mask = np.isfinite(values) & (values != None)
    return values[mask]

def filter_by_threshold(values: Union[List, np.ndarray], threshold: float, 
                       operation: str = 'greater') -> np.ndarray:
    """
    Filter values by threshold
    
    Args:
        values: Array of values to filter
        threshold: Threshold value
        operation: 'greater', 'less', 'greater_equal', 'less_equal'
        
    Returns:
        np.ndarray: Filtered array
    """
    values = clean_numeric_array(values)
    
    if operation == 'greater':
        return values[values > threshold]
    elif operation == 'less':
        return values[values < threshold]
    elif operation == 'greater_equal':
        return values[values >= threshold]
    elif operation == 'less_equal':
        return values[values <= threshold]
    else:
        raise ValueError(f"Unknown operation: {operation}")

def remove_outliers(values: Union[List, np.ndarray], method: str = 'iqr', 
                   factor: float = 1.5) -> Tuple[np.ndarray, np.ndarray]:
    """
    Remove outliers from data
    
    Args:
        values: Array of values
        method: 'iqr' or 'zscore'
        factor: Factor for outlier detection (1.5 for IQR, 3 for z-score)
        
    Returns:
        Tuple[np.ndarray, np.ndarray]: (clean_values, outliers)
    """
    values = clean_numeric_array(values)
    
    if len(values) < 4:
        return values, np.array([])
    
    if method == 'iqr':
        q25 = np.percentile(values, 25)
        q75 = np.percentile(values, 75)
        iqr = q75 - q25
        lower_bound = q25 - factor * iqr
        upper_bound = q75 + factor * iqr
        outlier_mask = (values < lower_bound) | (values > upper_bound)
    elif method == 'zscore':
        z_scores = np.abs(stats.zscore(values))
        outlier_mask = z_scores > factor
    else:
        raise ValueError(f"Unknown method: {method}")
    
    clean_values = values[~outlier_mask]
    outliers = values[outlier_mask]
    
    return clean_values, outliers

def filter_data_by_div(data: Dict, metric: str, target_div: int) -> Dict:
    """
    Filter data to include only experiments from a specific DIV
    
    Args:
        data: Data dictionary
        metric: Metric name
        target_div: Target DIV value
        
    Returns:
        Dict: Filtered data
    """
    filtered_data = {
        'by_group': {},
        'groups': data['groups'],
        'divs': [target_div]
    }
    
    for group in data['groups']:
        if group not in data['by_group']:
            continue
            
        group_data = data['by_group'][group]
        if metric not in group_data or 'exp_names' not in group_data:
            continue
        
        filtered_values = []
        filtered_exp_names = []
        
        for i, exp_name in enumerate(group_data['exp_names']):
            if f'DIV{target_div}' in exp_name:
                if i < len(group_data[metric]):
                    filtered_values.append(group_data[metric][i])
                    filtered_exp_names.append(exp_name)
        
        filtered_data['by_group'][group] = {
            metric: filtered_values,
            'exp_names': filtered_exp_names
        }
    
    return filtered_data

# =============================================================================
# DATA STRUCTURE MANIPULATION FUNCTIONS
# =============================================================================

def extract_div_from_experiment_name(exp_name: str) -> Optional[int]:
    """
    Extract DIV value from experiment name
    
    Args:
        exp_name: Experiment name string
        
    Returns:
        Optional[int]: DIV value if found, None otherwise
    """
    import re
    
    # Look for DIV followed by numbers
    match = re.search(r'DIV(\d+)', exp_name)
    if match:
        return int(match.group(1))
    
    # Look for patterns like "50" or "53" that might be DIV values
    parts = exp_name.split('_')
    for part in parts:
        if part.isdigit():
            div_val = int(part)
            if 40 <= div_val <= 100:  # Reasonable DIV range
                return div_val
    
    return None

def organize_data_by_div(data: Dict, metric: str) -> Dict:
    """
    Reorganize data by DIV instead of by group
    
    Args:
        data: Data dictionary
        metric: Metric name
        
    Returns:
        Dict: Data organized by DIV
    """
    div_data = {}
    
    for group in data['groups']:
        if group not in data['by_group']:
            continue
            
        group_data = data['by_group'][group]
        if metric not in group_data or 'exp_names' not in group_data:
            continue
        
        for i, exp_name in enumerate(group_data['exp_names']):
            div = extract_div_from_experiment_name(exp_name)
            if div is None:
                continue
                
            if div not in div_data:
                div_data[div] = {
                    'values': [],
                    'groups': [],
                    'exp_names': []
                }
            
            if i < len(group_data[metric]):
                div_data[div]['values'].append(group_data[metric][i])
                div_data[div]['groups'].append(group)
                div_data[div]['exp_names'].append(exp_name)
    
    return div_data

def flatten_electrode_data(data: Dict, metric: str) -> Dict:
    """
    Flatten electrode-level data from experiment structure
    
    Args:
        data: Data dictionary
        metric: Metric name
        
    Returns:
        Dict: Flattened data
    """
    flattened_data = {
        'by_group': {},
        'groups': data['groups'],
        'divs': data['divs']
    }
    
    for group in data['groups']:
        flattened_data['by_group'][group] = {
            metric: [],
            'exp_names': []
        }
    
    # Extract from experiment data
    for exp_name, exp_data in data.get('by_experiment', {}).items():
        if not validate_experiment_data(exp_data):
            continue
            
        group = exp_data['group']
        if group not in flattened_data['by_group']:
            continue
            
        if 'activity' in exp_data and metric in exp_data['activity']:
            electrode_values = exp_data['activity'][metric]
            if isinstance(electrode_values, (list, np.ndarray)):
                flattened_data['by_group'][group][metric].extend(electrode_values)
                # Add experiment name for each electrode
                for _ in electrode_values:
                    flattened_data['by_group'][group]['exp_names'].append(exp_name)
    
    return flattened_data

# =============================================================================
# STATISTICAL CALCULATION FUNCTIONS
# =============================================================================

def calculate_basic_stats(values: Union[List, np.ndarray]) -> Dict[str, float]:
    """
    Calculate basic statistics for a dataset
    
    Args:
        values: Array of values
        
    Returns:
        Dict: Dictionary with statistical measures
    """
    values = clean_numeric_array(values)
    
    if len(values) == 0:
        return {
            'count': 0,
            'mean': np.nan,
            'median': np.nan,
            'std': np.nan,
            'sem': np.nan,
            'min': np.nan,
            'max': np.nan,
            'q25': np.nan,
            'q75': np.nan
        }
    
    return {
        'count': len(values),
        'mean': np.mean(values),
        'median': np.median(values),
        'std': np.std(values, ddof=1) if len(values) > 1 else 0,
        'sem': stats.sem(values) if len(values) > 1 else 0,
        'min': np.min(values),
        'max': np.max(values),
        'q25': np.percentile(values, 25),
        'q75': np.percentile(values, 75)
    }

def calculate_active_electrodes(fr_values: Union[List, np.ndarray], 
                              threshold: float = 0.1) -> int:
    """
    Calculate number of active electrodes based on firing rate threshold
    
    Args:
        fr_values: Array of firing rate values
        threshold: Threshold for active electrodes (default: 0.1 Hz)
        
    Returns:
        int: Number of active electrodes
    """
    fr_values = clean_numeric_array(fr_values)
    active_electrodes = filter_by_threshold(fr_values, threshold, 'greater')
    return len(active_electrodes)

def calculate_active_electrode_mean(fr_values: Union[List, np.ndarray], 
                                  threshold: float = 0.1) -> float:
    """
    Calculate mean firing rate of active electrodes
    
    Args:
        fr_values: Array of firing rate values
        threshold: Threshold for active electrodes (default: 0.1 Hz)
        
    Returns:
        float: Mean firing rate of active electrodes
    """
    fr_values = clean_numeric_array(fr_values)
    active_electrodes = filter_by_threshold(fr_values, threshold, 'greater')
    
    if len(active_electrodes) == 0:
        return np.nan
    
    return np.mean(active_electrodes)

def calculate_confidence_interval(values: Union[List, np.ndarray], 
                                confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate confidence interval for data
    
    Args:
        values: Array of values
        confidence: Confidence level (default: 0.95)
        
    Returns:
        Tuple[float, float]: (lower_bound, upper_bound)
    """
    values = clean_numeric_array(values)
    
    if len(values) < 2:
        return np.nan, np.nan
    
    mean = np.mean(values)
    sem = stats.sem(values)
    
    # Use t-distribution for small samples
    dof = len(values) - 1
    t_value = stats.t.ppf((1 + confidence) / 2, dof)
    
    margin_error = t_value * sem
    return mean - margin_error, mean + margin_error

# =============================================================================
# DATA FORMATTING FUNCTIONS
# =============================================================================

def format_data_for_plotting(data: Dict, metric: str, groups: List[str], 
                            selected_divs: List[int]) -> Dict:
    """
    Format data for plotting by organizing values by group and DIV
    
    Args:
        data: Data dictionary
        metric: Metric name
        groups: List of groups to include
        selected_divs: List of DIVs to include
        
    Returns:
        Dict: Formatted data ready for plotting
    """
    # Filter groups and DIVs
    filtered_groups = [g for g in groups if g in data['groups']] if groups else data['groups']
    filtered_divs = [d for d in selected_divs if d in data['divs']] if selected_divs else sorted(data['divs'])
    
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

def create_summary_table(data: Dict, metric: str, groups: List[str]) -> Dict:
    """
    Create summary statistics table for data
    
    Args:
        data: Data dictionary
        metric: Metric name
        groups: List of groups
        
    Returns:
        Dict: Summary statistics by group
    """
    summary = {}
    
    for group in groups:
        if group not in data['by_group']:
            continue
            
        group_data = data['by_group'][group]
        if metric not in group_data:
            continue
        
        values = group_data[metric]
        if isinstance(values, (list, np.ndarray)):
            summary[group] = calculate_basic_stats(values)
        else:
            summary[group] = calculate_basic_stats([values])
    
    return summary

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_data_info(data: Dict) -> Dict[str, Any]:
    """
    Get information about the data structure
    
    Args:
        data: Data dictionary
        
    Returns:
        Dict: Information about the data
    """
    info = {
        'groups': data.get('groups', []),
        'divs': data.get('divs', []),
        'total_experiments': len(data.get('by_experiment', {})),
        'available_metrics': []
    }
    
    # Find available metrics
    if 'by_group' in data:
        for group in data['by_group']:
            for metric in data['by_group'][group]:
                if metric not in ['exp_names'] and metric not in info['available_metrics']:
                    info['available_metrics'].append(metric)
    
    return info

def check_data_quality(data: Dict, metric: str) -> Dict[str, Any]:
    """
    Check data quality for a specific metric
    
    Args:
        data: Data dictionary
        metric: Metric name
        
    Returns:
        Dict: Data quality report
    """
    quality_report = {
        'metric': metric,
        'groups_with_data': [],
        'total_values': 0,
        'valid_values': 0,
        'nan_values': 0,
        'groups_stats': {}
    }
    
    for group in data.get('groups', []):
        if group not in data['by_group']:
            continue
            
        group_data = data['by_group'][group]
        if metric not in group_data:
            continue
        
        values = group_data[metric]
        if isinstance(values, (list, np.ndarray)):
            values = np.array(values)
            total_count = len(values)
            valid_count = np.sum(np.isfinite(values))
            nan_count = total_count - valid_count
        else:
            total_count = 1
            valid_count = 1 if is_valid_numeric_value(values) else 0
            nan_count = 1 - valid_count
        
        if valid_count > 0:
            quality_report['groups_with_data'].append(group)
        
        quality_report['total_values'] += total_count
        quality_report['valid_values'] += valid_count
        quality_report['nan_values'] += nan_count
        
        quality_report['groups_stats'][group] = {
            'total': total_count,
            'valid': valid_count,
            'nan': nan_count,
            'valid_percentage': (valid_count / total_count * 100) if total_count > 0 else 0
        }
    
    return quality_report