# utils/metric_processors.py - CORRECTED VERSION
"""
MEA-NAP Metric Processors - 2B_GroupComparisons Method

CORRECTED to match exactly how MEA-NAP creates 2B_GroupComparisons:
- Node-level: Combine ALL electrode values from ALL recordings per group
- Recording-level: Calculate summary per recording, then group summaries
- Uses proper MEA-NAP aggregation methodology
"""

import numpy as np
from typing import Dict, List, Optional, Any
from utils.config import MEA_NAP_SETTINGS

# =============================================================================
# CONFIGURATION - User-specific settings
# =============================================================================

# Allow user to override active electrode threshold (0.01 Hz for conservative, 0.1 Hz for standard)
def get_active_threshold():
    """Get active electrode threshold - configurable for user's analysis"""
    return MEA_NAP_SETTINGS.get('active_electrode_threshold', 0.1)  # Default to 0.1 Hz

# =============================================================================
# NODE-LEVEL METRIC PROCESSORS (Electrode-Level Aggregation)
# =============================================================================
# These combine ALL electrode values from ALL recordings in each group
# Exactly matching MEA-NAP's "Unit XXX by Group" plots

def process_FR_metric(neuronal_data: Dict, groups: List[str], selected_divs: List[int]) -> Dict:
    """
    Process Mean Firing Rate (FR) metric - NODE-LEVEL aggregation
    
    MEA-NAP Method: Combine ALL electrode values from ALL recordings per group
    Each data point = one electrode from any recording in the group
    """
    print(f"📊 Processing FR metric (Node-level) for groups: {groups}")
    
    return _process_node_level_metric(neuronal_data, 'FR', groups, selected_divs)

def process_channelBurstRate_metric(neuronal_data: Dict, groups: List[str], selected_divs: List[int]) -> Dict:
    """Process Unit Burst Rate metric - NODE-LEVEL aggregation"""
    print(f"📊 Processing channelBurstRate metric (Node-level) for groups: {groups}")
    
    return _process_node_level_metric(neuronal_data, 'channelBurstRate', groups, selected_divs)

def process_channelFRinBurst_metric(neuronal_data: Dict, groups: List[str], selected_divs: List[int]) -> Dict:
    """Process Unit within Burst Firing Rate metric - NODE-LEVEL aggregation"""
    print(f"📊 Processing channelFRinBurst metric (Node-level) for groups: {groups}")
    
    return _process_node_level_metric(neuronal_data, 'channelFRinBurst', groups, selected_divs)

def process_channelBurstDur_metric(neuronal_data: Dict, groups: List[str], selected_divs: List[int]) -> Dict:
    """Process Unit Burst Duration metric - NODE-LEVEL aggregation"""
    print(f"📊 Processing channelBurstDur metric (Node-level) for groups: {groups}")
    
    return _process_node_level_metric(neuronal_data, 'channelBurstDur', groups, selected_divs)

def process_channelISIwithinBurst_metric(neuronal_data: Dict, groups: List[str], selected_divs: List[int]) -> Dict:
    """Process Unit ISI within Burst metric - NODE-LEVEL aggregation"""
    print(f"📊 Processing channelISIwithinBurst metric (Node-level) for groups: {groups}")
    
    return _process_node_level_metric(neuronal_data, 'channelISIwithinBurst', groups, selected_divs)

def process_channeISIoutsideBurst_metric(neuronal_data: Dict, groups: List[str], selected_divs: List[int]) -> Dict:
    """Process Unit ISI outside Burst metric - NODE-LEVEL aggregation"""
    print(f"📊 Processing channeISIoutsideBurst metric (Node-level) for groups: {groups}")
    
    return _process_node_level_metric(neuronal_data, 'channeISIoutsideBurst', groups, selected_divs)

def process_channelFracSpikesInBursts_metric(neuronal_data: Dict, groups: List[str], selected_divs: List[int]) -> Dict:
    """Process Unit fraction for spikes in bursts metric - NODE-LEVEL aggregation"""
    print(f"📊 Processing channelFracSpikesInBursts metric (Node-level) for groups: {groups}")
    
    return _process_node_level_metric(neuronal_data, 'channelFracSpikesInBursts', groups, selected_divs)

# def _process_node_level_metric(neuronal_data: Dict, metric: str, groups: List[str], selected_divs: List[int]) -> Dict:
#     """
#     Generic node-level processor following MEA-NAP 2B_GroupComparisons method
    
#     MEA-NAP Logic:
#     1. For each group, collect ALL electrode values from ALL recordings
#     2. Combine into one big array per group
#     3. Each data point represents one electrode (not one recording)
#     """
    
#     # Filter groups if specified
#     if groups:
#         groups_to_process = [g for g in groups if g in neuronal_data['groups']]
#     else:
#         groups_to_process = neuronal_data['groups']
    
#     # Create new data structure
#     processed_data = {
#         'by_group': {},
#         'by_experiment': neuronal_data.get('by_experiment', {}),
#         'by_div': {},
#         'groups': neuronal_data['groups'],
#         'divs': neuronal_data['divs']
#     }
    
#     # Initialize group data structure
#     for group in groups_to_process:
#         processed_data['by_group'][group] = {
#             metric: [],  # ALL electrode values from ALL recordings in this group
#             'exp_names': []  # Track which experiments contributed (for debugging)
#         }
    
#     # Initialize div data structure
#     for div in neuronal_data['divs']:
#         processed_data['by_div'][div] = {
#             metric: [],
#             'exp_names': [],
#             'groups': []
#         }
    
#     # Process each experiment - COMBINE ALL ELECTRODES per group
#     total_electrodes_processed = 0
    
#     for exp_name, exp_data in neuronal_data.get('by_experiment', {}).items():
#         if 'activity' not in exp_data or metric not in exp_data['activity']:
#             continue
            
#         # Get electrode array for this recording
#         electrode_values = exp_data['activity'][metric]
#         group = exp_data.get('group')
#         div = exp_data.get('div')
        
#         if isinstance(electrode_values, (list, np.ndarray)) and len(electrode_values) > 0:
#             # Filter valid values according to MEA-NAP methodology
#             valid_values = _filter_valid_values(electrode_values, metric)
            
#             if len(valid_values) > 0:
#                 # Add ALL electrode values to group (MEA-NAP method)
#                 if group and group in groups_to_process:
#                     processed_data['by_group'][group][metric].extend(valid_values)
#                     # Add exp_name for each electrode (for tracking)
#                     processed_data['by_group'][group]['exp_names'].extend([exp_name] * len(valid_values))
#                     total_electrodes_processed += len(valid_values)
                
#                 # Add to div data for age-based plotting
#                 if div and div in processed_data['by_div']:
#                     processed_data['by_div'][div][metric].extend(valid_values)
#                     processed_data['by_div'][div]['exp_names'].extend([exp_name] * len(valid_values))
#                     processed_data['by_div'][div]['groups'].extend([group] * len(valid_values))
    
#     print(f"   ✅ Node-level {metric}: {total_electrodes_processed} total electrodes processed")
    
#     # Print summary for debugging
#     for group in groups_to_process:
#         electrode_count = len(processed_data['by_group'][group][metric])
#         exp_count = len(set(processed_data['by_group'][group]['exp_names']))
#         print(f"      {group}: {electrode_count} electrodes from {exp_count} recordings")
    
#     return processed_data

# # v2 version
# def _process_node_level_metric(neuronal_data: Dict, metric: str, groups: List[str], selected_divs: List[int]) -> Dict:
#     """
#     FIXED: Generic node-level processor following MEA-NAP 2B_GroupComparisons method
    
#     MEA-NAP Logic:
#     1. For each group, collect ALL electrode values from ALL recordings
#     2. Combine into one big array per group
#     3. Each data point represents one electrode (not one recording)
#     """
    
#     # Filter groups if specified
#     if groups:
#         groups_to_process = [g for g in groups if g in neuronal_data['groups']]
#     else:
#         groups_to_process = neuronal_data['groups']
    
#     # Create new data structure
#     processed_data = {
#         'by_group': {},
#         'by_experiment': neuronal_data.get('by_experiment', {}),
#         'by_div': {},
#         'groups': neuronal_data['groups'],
#         'divs': neuronal_data['divs']
#     }
    
#     # Initialize group data structure
#     for group in groups_to_process:
#         processed_data['by_group'][group] = {
#             metric: [],  # ALL electrode values from ALL recordings in this group
#             'exp_names': []  # Track which experiments contributed (for debugging)
#         }
    
#     # Initialize div data structure
#     for div in neuronal_data['divs']:
#         processed_data['by_div'][div] = {
#             metric: [],
#             'exp_names': [],
#             'groups': []
#         }
    
#     # FIXED: Process each experiment with better error handling and field mapping
#     total_electrodes_processed = 0
    
#     for exp_name, exp_data in neuronal_data.get('by_experiment', {}).items():
#         # FIXED: Better field checking and mapping
#         activity_data = exp_data.get('activity', {})
        
#         # Check if the metric exists (with potential field name variations)
#         electrode_values = None
        
#         # Try exact field name first
#         if metric in activity_data:
#             electrode_values = activity_data[metric]
#         # Try common field name variations for channelFracSpikesInBursts
#         elif metric == 'channelFracSpikesInBursts':
#             # Try potential alternate field names
#             for alt_name in ['channelFracSpikesInBursts', 'fracSpikesInBursts', 'FracSpikesInBursts']:
#                 if alt_name in activity_data:
#                     electrode_values = activity_data[alt_name]
#                     print(f"📍 Found {metric} as {alt_name} in {exp_name}")
#                     break
        
#         if electrode_values is None:
#             print(f"⚠️ Missing {metric} in experiment {exp_name}")
#             print(f"   Available fields: {list(activity_data.keys())}")
#             continue
            
#         group = exp_data.get('group')
#         div = exp_data.get('div')
        
#         # FIXED: Better data validation and conversion
#         if electrode_values is not None:
#             # Convert to numpy array for consistent handling
#             if not isinstance(electrode_values, np.ndarray):
#                 electrode_values = np.array(electrode_values)
            
#             # Ensure it's a 1D array of electrode values
#             if electrode_values.ndim > 1:
#                 electrode_values = electrode_values.flatten()
            
#             if len(electrode_values) > 0:
#                 # FIXED: More robust filtering for channelFracSpikesInBursts specifically
#                 if metric == 'channelFracSpikesInBursts':
#                     # Remove NaN values
#                     valid_mask = ~np.isnan(electrode_values) & np.isfinite(electrode_values)
#                     valid_values = electrode_values[valid_mask]
                    
#                     # For fraction of spikes in bursts, values should be between 0 and 1
#                     # Also include 0 values (electrodes with no bursts)
#                     fraction_mask = (valid_values >= 0) & (valid_values <= 1)
#                     valid_values = valid_values[fraction_mask]
                    
#                     print(f"📊 {exp_name}: {len(electrode_values)} electrodes -> {len(valid_values)} valid fractions")
#                 else:
#                     # Use existing filter for other metrics
#                     valid_values = _filter_valid_values(electrode_values, metric)
                
#                 if len(valid_values) > 0:
#                     # Add ALL electrode values to group (MEA-NAP method)
#                     if group and group in groups_to_process:
#                         processed_data['by_group'][group][metric].extend(valid_values.tolist())
#                         # Add exp_name for each electrode (for tracking)
#                         processed_data['by_group'][group]['exp_names'].extend([exp_name] * len(valid_values))
#                         total_electrodes_processed += len(valid_values)
                    
#                     # Add to div data for age-based plotting
#                     if div and div in processed_data['by_div']:
#                         processed_data['by_div'][div][metric].extend(valid_values.tolist())
#                         processed_data['by_div'][div]['exp_names'].extend([exp_name] * len(valid_values))
#                         processed_data['by_div'][div]['groups'].extend([group] * len(valid_values))
#                 else:
#                     print(f"⚠️ No valid values for {metric} in {exp_name}")
#             else:
#                 print(f"⚠️ Empty electrode array for {metric} in {exp_name}")
    
#     print(f"   ✅ Node-level {metric}: {total_electrodes_processed} total electrodes processed")
    
#     # FIXED: Better summary reporting
#     for group in groups_to_process:
#         electrode_count = len(processed_data['by_group'][group][metric])
#         exp_count = len(set(processed_data['by_group'][group]['exp_names']))
#         print(f"      {group}: {electrode_count} electrodes from {exp_count} recordings")
        
#         # DIAGNOSTIC: Show expected vs actual
#         if electrode_count < 5:
#             print(f"         ⚠️ LOW ELECTRODE COUNT - Expected 16-80, got {electrode_count}")
#             print(f"         Values: {processed_data['by_group'][group][metric]}")
    
#     return processed_data

def _process_node_level_metric(neuronal_data: Dict, metric: str, groups: List[str], selected_divs: List[int]) -> Dict:
    """
    ENHANCED DIAGNOSTIC VERSION: Generic node-level processor following MEA-NAP 2B_GroupComparisons method
    
    MEA-NAP Logic:
    1. For each group, collect ALL electrode values from ALL recordings
    2. Combine into one big array per group
    3. Each data point represents one electrode (not one recording)
    """
    
    print(f"🚨 EMERGENCY DIAGNOSTIC: Starting {metric} processing")
    
    # Filter groups if specified
    if groups:
        groups_to_process = [g for g in groups if g in neuronal_data['groups']]
    else:
        groups_to_process = neuronal_data['groups']
    
    # Create new data structure
    processed_data = {
        'by_group': {},
        'by_experiment': neuronal_data.get('by_experiment', {}),
        'by_div': {},
        'groups': neuronal_data['groups'],
        'divs': neuronal_data['divs']
    }
    
    # Initialize group data structure
    for group in groups_to_process:
        processed_data['by_group'][group] = {
            metric: [],  # ALL electrode values from ALL recordings in this group
            'exp_names': []  # Track which experiments contributed (for debugging)
        }
    
    # Initialize div data structure
    for div in neuronal_data['divs']:
        processed_data['by_div'][div] = {
            metric: [],
            'exp_names': [],
            'groups': []
        }
    
    # ENHANCED DIAGNOSTIC: Process each experiment with detailed logging
    total_electrodes_processed = 0
    field_detection_log = {}  # Track field detection across experiments
    
    for exp_name, exp_data in neuronal_data.get('by_experiment', {}).items():
        print(f"📊 DIAGNOSTIC: Processing experiment {exp_name}")
        
        # ENHANCED: Better field checking and mapping
        activity_data = exp_data.get('activity', {})
        
        # Log available fields for this experiment (first 3 only to avoid spam)
        if len(field_detection_log) < 3:
            available_fields = list(activity_data.keys())
            field_detection_log[exp_name] = available_fields
            print(f"   Available fields in {exp_name}: {available_fields}")
        
        # Check if the metric exists (with potential field name variations)
        electrode_values = None
        field_used = None
        
        # APPLY ENHANCED FIELD DETECTION TO ALL METRICS (not just channelFracSpikesInBursts)
        field_variations = get_field_variations(metric)  # Get potential alternate names
        
        # Try each potential field name
        for alt_name in field_variations:
            if alt_name in activity_data:
                electrode_values = activity_data[alt_name]
                field_used = alt_name
                if field_used != metric:  # Only log if we found an alternate
                    print(f"📍 FIELD MAPPING: Found {metric} as '{alt_name}' in {exp_name}")
                break
        
        if electrode_values is None:
            print(f"⚠️ MISSING FIELD: {metric} not found in {exp_name}")
            print(f"   Tried variations: {field_variations}")
            continue
            
        group = exp_data.get('group')
        div = exp_data.get('div')
        
        # ENHANCED: Better data validation and conversion
        if electrode_values is not None:
            # Convert to numpy array for consistent handling
            if not isinstance(electrode_values, np.ndarray):
                electrode_values = np.array(electrode_values)
            
            # Ensure it's a 1D array of electrode values
            if electrode_values.ndim > 1:
                electrode_values = electrode_values.flatten()
            
            print(f"   Raw electrode array: {len(electrode_values)} values")
            
            if len(electrode_values) > 0:
                # APPLY METRIC-SPECIFIC FILTERING (enhanced for all metrics)
                valid_values = apply_enhanced_filtering(electrode_values, metric, exp_name)
                
                if len(valid_values) > 0:
                    # Add ALL electrode values to group (MEA-NAP method)
                    if group and group in groups_to_process:
                        processed_data['by_group'][group][metric].extend(valid_values.tolist())
                        # Add exp_name for each electrode (for tracking)
                        processed_data['by_group'][group]['exp_names'].extend([exp_name] * len(valid_values))
                        total_electrodes_processed += len(valid_values)
                        print(f"   ✅ Added {len(valid_values)} valid electrodes to group {group}")
                    
                    # Add to div data for age-based plotting
                    if div and div in processed_data['by_div']:
                        processed_data['by_div'][div][metric].extend(valid_values.tolist())
                        processed_data['by_div'][div]['exp_names'].extend([exp_name] * len(valid_values))
                        processed_data['by_div'][div]['groups'].extend([group] * len(valid_values))
                else:
                    print(f"⚠️ No valid values after filtering in {exp_name}")
                    print(f"   Raw range: {np.min(electrode_values):.3f} to {np.max(electrode_values):.3f}")
                    print(f"   NaN count: {np.sum(np.isnan(electrode_values))}")
            else:
                print(f"⚠️ Empty electrode array for {metric} in {exp_name}")
    
    print(f"🔍 FINAL DIAGNOSTIC SUMMARY for {metric}:")
    print(f"   Total electrodes processed: {total_electrodes_processed}")
    
    # ENHANCED: Better summary reporting with diagnostic info
    for group in groups_to_process:
        electrode_count = len(processed_data['by_group'][group][metric])
        exp_count = len(set(processed_data['by_group'][group]['exp_names']))
        print(f"   📊 {group}: {electrode_count} electrodes from {exp_count} recordings")
        
        # DIAGNOSTIC: Show expected vs actual and value ranges
        if electrode_count == 0:
            print(f"         🚨 ZERO ELECTRODES - Check field mapping and filtering!")
        elif electrode_count < 5:
            print(f"         ⚠️ LOW ELECTRODE COUNT - Expected 16-80, got {electrode_count}")
            values = processed_data['by_group'][group][metric]
            print(f"         Values: {values}")
        else:
            values = processed_data['by_group'][group][metric]
            print(f"         ✅ GOOD COUNT - Range: {min(values):.3f} to {max(values):.3f}")
    
    return processed_data


def get_field_variations(metric: str) -> List[str]:
    """
    Get potential field name variations for each metric
    Based on common MEA-NAP field naming patterns
    """
    variations = {
        'channelFracSpikesInBursts': ['channelFracSpikesInBursts', 'fracSpikesInBursts', 'FracSpikesInBursts'],
        'channelBurstRate': ['channelBurstRate', 'burstRate', 'BurstRate', 'channel_burst_rate'],
        'channelFRinBurst': ['channelFRinBurst', 'FRinBurst', 'FR_in_burst', 'channel_FR_in_burst'],
        'channelBurstDur': ['channelBurstDur', 'burstDur', 'BurstDur', 'burst_duration', 'channel_burst_dur'],
        'channelISIwithinBurst': ['channelISIwithinBurst', 'ISIwithinBurst', 'ISI_within_burst', 'channel_ISI_within_burst'],
        'channeISIoutsideBurst': ['channeISIoutsideBurst', 'channelISIoutsideBurst', 'ISIoutsideBurst', 'ISI_outside_burst'],
        'FR': ['FR', 'firing_rate', 'firingRate', 'channel_FR']
    }
    
    # Return the variations for this metric, or just the metric itself if no variations defined
    return variations.get(metric, [metric])


def apply_enhanced_filtering(electrode_values: np.ndarray, metric: str, exp_name: str) -> np.ndarray:
    """
    Apply enhanced filtering for each metric type with detailed logging
    """
    print(f"     🔧 Filtering {len(electrode_values)} values for {metric}")
    
    # Remove NaN and infinite values first
    initial_count = len(electrode_values)
    valid_mask = ~np.isnan(electrode_values) & np.isfinite(electrode_values)
    valid_values = electrode_values[valid_mask]
    nan_count = initial_count - len(valid_values)
    
    if nan_count > 0:
        print(f"     Removed {nan_count} NaN/infinite values")
    
    if len(valid_values) == 0:
        print(f"     ⚠️ All values were NaN/infinite!")
        return np.array([])
    
    # Apply metric-specific filtering with enhanced logging
    if metric == 'channelFracSpikesInBursts':
        # Fraction values should be between 0 and 1
        before_count = len(valid_values)
        fraction_mask = (valid_values >= 0) & (valid_values <= 1)
        valid_values = valid_values[fraction_mask]
        filtered_count = before_count - len(valid_values)
        if filtered_count > 0:
            print(f"     Filtered {filtered_count} values outside [0,1] range")
            
    elif metric in ['FR', 'channelBurstRate', 'channelBurstDur', 'channelFRinBurst']:
        # These should be >= 0
        before_count = len(valid_values)
        valid_values = valid_values[valid_values >= 0]
        filtered_count = before_count - len(valid_values)
        if filtered_count > 0:
            print(f"     Filtered {filtered_count} negative values")
            
    elif metric in ['channelISIwithinBurst', 'channeISIoutsideBurst']:
        # ISI must be positive (> 0)
        before_count = len(valid_values)
        valid_values = valid_values[valid_values > 0]
        filtered_count = before_count - len(valid_values)
        if filtered_count > 0:
            print(f"     Filtered {filtered_count} non-positive ISI values")
    
    print(f"     ✅ Final: {len(valid_values)} valid values")
    if len(valid_values) > 0:
        print(f"     Range: {np.min(valid_values):.3f} to {np.max(valid_values):.3f}")
    
    return valid_values

# =============================================================================
# RECORDING-LEVEL METRIC PROCESSORS (Recording-Level Aggregation)
# =============================================================================
# These calculate one summary per recording, then group the summaries
# Exactly matching MEA-NAP's recording-level plots

def process_FRActive_metric(neuronal_data: Dict, groups: List[str], selected_divs: List[int]) -> Dict:
    """
    Process Mean Firing Rate Active Node metric - RECORDING-LEVEL aggregation
    
    MEA-NAP Method:
    1. For each recording: Calculate mean FR of active electrodes (FR > threshold)
    2. Group these recording-level means by experimental group
    3. Each data point = one recording's summary
    """
    print(f"🔥 Processing FRActive metric (Recording-level) for groups: {groups}")
    
    return _process_recording_level_active_metric(neuronal_data, groups, selected_divs)

def process_numActiveElec_metric(neuronal_data: Dict, groups: List[str], selected_divs: List[int]) -> Dict:
    """
    Process Number of Active Electrodes metric - RECORDING-LEVEL aggregation
    
    MEA-NAP Method:
    1. For each recording: Count electrodes with FR > threshold
    2. Group these counts by experimental group
    3. Each data point = one recording's active electrode count
    """
    print(f"📊 Processing numActiveElec metric (Recording-level) for groups: {groups}")
    
    return _process_recording_level_count_metric(neuronal_data, groups, selected_divs)

def process_NBurstRate_metric(neuronal_data: Dict, groups: List[str], selected_divs: List[int]) -> Dict:
    """Process Network Burst Rate metric - RECORDING-LEVEL aggregation"""
    print(f"📊 Processing NBurstRate metric (Recording-level) for groups: {groups}")
    
    return _process_recording_level_scalar_metric(neuronal_data, 'NBurstRate', groups, selected_divs)

def process_FRmean_metric(neuronal_data: Dict, groups: List[str], selected_divs: List[int]) -> Dict:
    """Process Mean Firing Rate metric - RECORDING-LEVEL aggregation"""
    print(f"📊 Processing FRmean metric (Recording-level) for groups: {groups}")
    
    return _process_recording_level_scalar_metric(neuronal_data, 'FRmean', groups, selected_divs)

def process_FRmedian_metric(neuronal_data: Dict, groups: List[str], selected_divs: List[int]) -> Dict:
    """Process Median Firing Rate metric - RECORDING-LEVEL aggregation"""
    print(f"📊 Processing FRmedian metric (Recording-level) for groups: {groups}")
    
    return _process_recording_level_scalar_metric(neuronal_data, 'FRmedian', groups, selected_divs)

def _process_recording_level_active_metric(neuronal_data: Dict, groups: List[str], selected_divs: List[int]) -> Dict:
    """
    Recording-level processor for active electrode metrics
    
    MEA-NAP Logic:
    1. For each recording: Calculate mean of active electrodes only
    2. Group these recording-level means
    3. Each data point = one recording
    """
    
    # Filter groups if specified
    if groups:
        groups_to_process = [g for g in groups if g in neuronal_data['groups']]
    else:
        groups_to_process = neuronal_data['groups']
    
    # Create data structure
    processed_data = {
        'by_group': {},
        'by_experiment': neuronal_data.get('by_experiment', {}),
        'by_div': {},
        'groups': neuronal_data['groups'],
        'divs': neuronal_data['divs']
    }
    
    # Initialize structures
    for group in groups_to_process:
        processed_data['by_group'][group] = {
            'FRActiveNode': [],  # Recording-level means
            'exp_names': []
        }
    
    for div in neuronal_data['divs']:
        processed_data['by_div'][div] = {
            'FRActiveNode': [],
            'exp_names': [],
            'groups': []
        }
    
    # Process each recording
    active_threshold = get_active_threshold()
    processed_recordings = 0
    
    for exp_name, exp_data in neuronal_data.get('by_experiment', {}).items():
        if 'activity' not in exp_data or 'FR' not in exp_data['activity']:
            continue
            
        # Get FR array for this recording
        fr_values = exp_data['activity']['FR']
        group = exp_data.get('group')
        div = exp_data.get('div')
        
        if isinstance(fr_values, (list, np.ndarray)) and len(fr_values) > 0:
            # Calculate recording-level mean of active electrodes (MEA-NAP method)
            fr_array = np.array(fr_values)
            valid_fr = fr_array[~np.isnan(fr_array) & np.isfinite(fr_array) & (fr_array >= 0)]
            active_electrodes = valid_fr[valid_fr > active_threshold]
            
            if len(active_electrodes) > 0:
                recording_mean_active = np.mean(active_electrodes)
                
                # Add recording-level summary to group
                if group and group in groups_to_process:
                    processed_data['by_group'][group]['FRActiveNode'].append(recording_mean_active)
                    processed_data['by_group'][group]['exp_names'].append(exp_name)
                    processed_recordings += 1
                
                # Add to div data
                if div and div in processed_data['by_div']:
                    processed_data['by_div'][div]['FRActiveNode'].append(recording_mean_active)
                    processed_data['by_div'][div]['exp_names'].append(exp_name)
                    processed_data['by_div'][div]['groups'].append(group)
    
    print(f"   ✅ Recording-level FRActive: {processed_recordings} recordings processed")
    print(f"      Using active threshold: {active_threshold} Hz")
    
    return processed_data

def _process_recording_level_count_metric(neuronal_data: Dict, groups: List[str], selected_divs: List[int]) -> Dict:
    """Recording-level processor for counting metrics (like numActiveElec)"""
    
    # Filter groups if specified
    if groups:
        groups_to_process = [g for g in groups if g in neuronal_data['groups']]
    else:
        groups_to_process = neuronal_data['groups']
    
    # Create data structure
    processed_data = {
        'by_group': {},
        'by_experiment': neuronal_data.get('by_experiment', {}),
        'by_div': {},
        'groups': neuronal_data['groups'],
        'divs': neuronal_data['divs']
    }
    
    # Initialize structures
    for group in groups_to_process:
        processed_data['by_group'][group] = {
            'numActiveElec': [],  # Recording-level counts
            'exp_names': []
        }
    
    for div in neuronal_data['divs']:
        processed_data['by_div'][div] = {
            'numActiveElec': [],
            'exp_names': [],
            'groups': []
        }
    
    # Process each recording
    active_threshold = get_active_threshold()
    processed_recordings = 0
    
    for exp_name, exp_data in neuronal_data.get('by_experiment', {}).items():
        if 'activity' not in exp_data or 'FR' not in exp_data['activity']:
            continue
            
        # Get FR array for this recording
        fr_values = exp_data['activity']['FR']
        group = exp_data.get('group')
        div = exp_data.get('div')
        
        if isinstance(fr_values, (list, np.ndarray)) and len(fr_values) > 0:
            # Count active electrodes for this recording (MEA-NAP method)
            fr_array = np.array(fr_values)
            valid_fr = fr_array[~np.isnan(fr_array) & np.isfinite(fr_array) & (fr_array >= 0)]
            active_count = int(np.sum(valid_fr > active_threshold))
            
            # Add recording-level count to group
            if group and group in groups_to_process:
                processed_data['by_group'][group]['numActiveElec'].append(active_count)
                processed_data['by_group'][group]['exp_names'].append(exp_name)
                processed_recordings += 1
            
            # Add to div data
            if div and div in processed_data['by_div']:
                processed_data['by_div'][div]['numActiveElec'].append(active_count)
                processed_data['by_div'][div]['exp_names'].append(exp_name)
                processed_data['by_div'][div]['groups'].append(group)
    
    print(f"   ✅ Recording-level numActiveElec: {processed_recordings} recordings processed")
    print(f"      Using active threshold: {active_threshold} Hz")
    
    return processed_data

def _process_recording_level_scalar_metric(neuronal_data: Dict, metric: str, groups: List[str], selected_divs: List[int]) -> Dict:
    """Recording-level processor for scalar metrics (already calculated per recording)"""
    
    # Filter groups if specified
    if groups:
        groups_to_process = [g for g in groups if g in neuronal_data['groups']]
    else:
        groups_to_process = neuronal_data['groups']
    
    # Create data structure
    processed_data = {
        'by_group': {},
        'by_experiment': neuronal_data.get('by_experiment', {}),
        'by_div': {},
        'groups': neuronal_data['groups'],
        'divs': neuronal_data['divs']
    }
    
    # Initialize structures
    for group in groups_to_process:
        processed_data['by_group'][group] = {
            metric: [],  # Recording-level values
            'exp_names': []
        }
    
    for div in neuronal_data['divs']:
        processed_data['by_div'][div] = {
            metric: [],
            'exp_names': [],
            'groups': []
        }
    
    # Process each recording
    processed_recordings = 0
    
    for exp_name, exp_data in neuronal_data.get('by_experiment', {}).items():
        if 'activity' not in exp_data or metric not in exp_data['activity']:
            continue
            
        # Get scalar value for this recording
        value = exp_data['activity'][metric]
        group = exp_data.get('group')
        div = exp_data.get('div')
        
        if not np.isnan(value) and np.isfinite(value):
            # Add recording-level value to group
            if group and group in groups_to_process:
                processed_data['by_group'][group][metric].append(value)
                processed_data['by_group'][group]['exp_names'].append(exp_name)
                processed_recordings += 1
            
            # Add to div data
            if div and div in processed_data['by_div']:
                processed_data['by_div'][div][metric].append(value)
                processed_data['by_div'][div]['exp_names'].append(exp_name)
                processed_data['by_div'][div]['groups'].append(group)
    
    print(f"   ✅ Recording-level {metric}: {processed_recordings} recordings processed")
    
    return processed_data

# =============================================================================
# UTILITY FUNCTIONS - MEA-NAP filtering methodology
# =============================================================================

def _filter_valid_values(values: np.ndarray, metric: str) -> np.ndarray:
    """
    Filter values according to MEA-NAP methodology
    
    This matches the filtering logic from pipeline Claude's analysis
    """
    # Convert to numpy array
    values = np.array(values)
    
    # Remove NaN and infinite values
    valid = values[~np.isnan(values)]
    valid = valid[np.isfinite(valid)]
    
    # Apply metric-specific filtering (from pipeline Claude's specification)
    if metric == 'FR':
        valid = valid[valid >= 0]
    elif metric in ['channelBurstRate', 'channelBurstDur']:
        valid = valid[valid >= 0]
    elif metric in ['channelISIwithinBurst', 'channeISIoutsideBurst']:
        valid = valid[valid > 0]  # ISI must be positive
    elif metric == 'channelFracSpikesInBursts':
        valid = valid[(valid >= 0) & (valid <= 1)]  # Fraction between 0 and 1
    elif metric == 'channelFRinBurst':
        valid = valid[valid >= 0]
    
    return valid

# =============================================================================
# METRIC REGISTRY - Updated with corrected processors
# =============================================================================

NEURONAL_METRIC_PROCESSORS = {
    # Node-level metrics (electrode-level aggregation)
    'FR': process_FR_metric,
    'channelBurstRate': process_channelBurstRate_metric,
    'channelFRinBurst': process_channelFRinBurst_metric,
    'channelBurstDur': process_channelBurstDur_metric,
    'channelISIwithinBurst': process_channelISIwithinBurst_metric,
    'channeISIoutsideBurst': process_channeISIoutsideBurst_metric,
    'channelFracSpikesInBursts': process_channelFracSpikesInBursts_metric,
    
    # Recording-level metrics (recording-level aggregation)
    'FRActive': process_FRActive_metric,
    'numActiveElec': process_numActiveElec_metric,
    'NBurstRate': process_NBurstRate_metric,
    'FRmean': process_FRmean_metric,
    'FRmedian': process_FRmedian_metric
}

# =============================================================================
# UTILITY FUNCTIONS - Same as before
# =============================================================================

def get_available_metrics() -> List[str]:
    """Get list of all available metrics"""
    return list(NEURONAL_METRIC_PROCESSORS.keys())

def is_metric_available(metric: str) -> bool:
    """Check if a metric processor is available"""
    return metric in NEURONAL_METRIC_PROCESSORS

def get_metric_processor(metric: str):
    """Get the processor function for a metric"""
    if not is_metric_available(metric):
        raise KeyError(f"Metric '{metric}' is not available. Available metrics: {get_available_metrics()}")
    
    return NEURONAL_METRIC_PROCESSORS[metric]

def process_metric(metric: str, neuronal_data: Dict, groups: List[str], selected_divs: List[int]) -> Dict:
    """Process a metric using its registered processor"""
    processor = get_metric_processor(metric)
    return processor(neuronal_data, groups, selected_divs)

# =============================================================================
# METRIC CATEGORIES - Updated to reflect aggregation types
# =============================================================================

NODE_LEVEL_METRICS = [
    'FR', 'channelBurstRate', 'channelFRinBurst', 
    'channelBurstDur', 'channelISIwithinBurst', 'channeISIoutsideBurst', 
    'channelFracSpikesInBursts'
]

RECORDING_LEVEL_METRICS = [
    'FRActive', 'numActiveElec', 'NBurstRate', 'FRmean', 'FRmedian'
]

def get_node_level_metrics() -> List[str]:
    """Get list of node-level (electrode-level) metrics"""
    return NODE_LEVEL_METRICS.copy()

def get_recording_level_metrics() -> List[str]:
    """Get list of recording-level metrics"""
    return RECORDING_LEVEL_METRICS.copy()

def is_node_level_metric(metric: str) -> bool:
    """Check if metric uses node-level aggregation"""
    return metric in NODE_LEVEL_METRICS

def is_recording_level_metric(metric: str) -> bool:
    """Check if metric uses recording-level aggregation"""
    return metric in RECORDING_LEVEL_METRICS

# Backward compatibility aliases
get_electrode_level_metrics = get_node_level_metrics
is_electrode_level_metric = is_node_level_metric

# =============================================================================
# RECORDING-LEVEL METRIC PROCESSOR FACTORY
# =============================================================================

def create_recording_level_processor(metric_name):
    """Create a processor for recording-level metrics"""
    def process_recording_metric(neuronal_data, groups, selected_divs):
        print(f"📊 Processing {metric_name} metric (Recording-level)")
        
        # Filter groups
        if groups:
            groups_to_process = [g for g in groups if g in neuronal_data['groups']]
        else:
            groups_to_process = neuronal_data['groups']
        
        # Create data structure
        processed_data = {
            'by_group': {},
            'by_experiment': neuronal_data.get('by_experiment', {}),
            'groups': neuronal_data['groups'],
            'divs': neuronal_data['divs']
        }
        
        # Initialize structures
        for group in groups_to_process:
            processed_data['by_group'][group] = {
                metric_name: [],
                'exp_names': []
            }
        
        # Process each recording
        processed_recordings = 0
        
        for exp_name, exp_data in neuronal_data.get('by_experiment', {}).items():
            if 'recording_metrics' not in exp_data:
                # Import the function if not already done
                from data_processing.experiment_mat_loader import extract_recording_level_metrics
                exp_data['recording_metrics'] = extract_recording_level_metrics(exp_data)
            
            recording_metrics = exp_data['recording_metrics']
            group = exp_data.get('group')
            
            if metric_name in recording_metrics and not np.isnan(recording_metrics[metric_name]):
                if group and group in groups_to_process:
                    processed_data['by_group'][group][metric_name].append(recording_metrics[metric_name])
                    processed_data['by_group'][group]['exp_names'].append(exp_name)
                    processed_recordings += 1
        
        print(f"   ✅ Recording-level {metric_name}: {processed_recordings} recordings processed")
        return processed_data
    
    return process_recording_metric

# Add all missing recording-level processors
MISSING_RECORDING_METRICS = [
    'meanNBstLengthS',
    'meanISIWithinNbursts_ms', 
    'meanISIoutsideNbursts_ms',
    'CVofINBI',
    'fracInNburst',
    'meanNumChansInvolvedInNbursts',
    'singleElecBurstRate',
    'singleElecBurstDur',
    'singleElecISIwithinBurst',
    'singleElecISIoutsideBurst',
    'meanFracSpikesInBurstsPerElec',
    'channelAveBurstRate',
    'channelAveBurstDur',
    'channelAveISIwithinBurst',
    'channelAveISIoutsideBurst',
    'channelAveFracSpikesInBursts',
    'numNbursts',
    'FRstd',
    'FRsem',
    'FRiqr'
]

# Add processors for missing metrics
for metric in MISSING_RECORDING_METRICS:
    if metric not in NEURONAL_METRIC_PROCESSORS:
        NEURONAL_METRIC_PROCESSORS[metric] = create_recording_level_processor(metric)