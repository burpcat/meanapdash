# data_processing/experiment_mat_loader.py - REFACTORED VERSION
"""
ExperimentMatFiles Data Loader for MEA-NAP Dashboard

REFACTORED to follow the same standards as other files:
- Separated concerns
- Moved data processing to utils
- Used configuration from utils/config
- Broke down long functions
- Improved error handling
- Better separation of loading vs processing

Based on pipeline Claude's comprehensive guide
"""

import os
import numpy as np
import glob
import scipy.io as sio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import re

# Import from utils package for consistency
from utils.config import MEA_NAP_SETTINGS, DATA_LOADING_CONFIG
from utils.data_helpers import clean_numeric_array, is_valid_numeric_value
from data_processing.utilities import safe_flatten_array

# =============================================================================
# CONFIGURATION - Moved to use utils/config
# =============================================================================

# These are now imported from utils.config.MEA_NAP_SETTINGS
ACTIVE_ELECTRODE_THRESHOLD = MEA_NAP_SETTINGS['active_electrode_threshold']
BURST_DETECTION_THRESHOLD = MEA_NAP_SETTINGS['burst_detection_threshold']
MIN_ELECTRODE_COUNT = MEA_NAP_SETTINGS['min_electrode_count']

# File handling configuration
EXPERIMENT_MAT_FOLDER = DATA_LOADING_CONFIG['experiment_mat_folder']
SUPPORTED_EXTENSIONS = DATA_LOADING_CONFIG['supported_extensions']
MAX_FILE_SIZE_MB = DATA_LOADING_CONFIG['max_file_size_mb']

# =============================================================================
# MATLAB STRUCTURE EXTRACTION - Separated into focused functions
# =============================================================================

def extract_group_name_robust(info_raw: Dict) -> str:
    """
    Robust group name extraction with multiple fallback methods
    Handles deeply nested MATLAB structures
    """
    print(f"🔍 Extracting group from: {type(info_raw['Grp'])}")
    
    extraction_methods = [
        lambda: str(info_raw['Grp'][0][0][0][0][0]),
        lambda: _unwrap_nested_array(info_raw['Grp']),
        lambda: str(info_raw['Grp'][0][0][0][0]),
        lambda: str(info_raw['Grp'][0][0][0]),
        lambda: str(info_raw['Grp'][0][0]),
        lambda: _extract_with_regex(str(info_raw['Grp'])),
        lambda: info_raw['Grp'][0][0][0].item() if hasattr(info_raw['Grp'][0][0][0], 'item') else None
    ]
    
    for i, method in enumerate(extraction_methods):
        try:
            result = method()
            if result and isinstance(result, str) and 'array' not in result and 'dtype' not in result:
                print(f"  ✓ Group extracted with method {i+1}: '{result}'")
                return result
        except Exception as e:
            print(f"  ⚠ Method {i+1} failed: {e}")
    
    print(f"  ❌ All extraction methods failed, using 'Unknown'")
    return "Unknown"

def extract_div_value_robust(info_raw: Dict) -> int:
    """Extract DIV value robustly, handling nested arrays and converting to int"""
    print(f"🔍 Extracting DIV from: {type(info_raw['DIV'])}")
    
    extraction_methods = [
        lambda: int(info_raw['DIV'][0][0][0][0][0]),
        lambda: int(_unwrap_nested_array(info_raw['DIV'])),
        lambda: int(info_raw['DIV'][0][0][0][0]),
        lambda: int(info_raw['DIV'][0][0][0]),
        lambda: int(info_raw['DIV'][0][0]),
        lambda: int(re.search(r'(\d+)', str(info_raw['DIV'])).group(1)),
        lambda: int(info_raw['DIV'][0][0][0].item()) if hasattr(info_raw['DIV'][0][0][0], 'item') else None
    ]
    
    for i, method in enumerate(extraction_methods):
        try:
            result = method()
            if result is not None and isinstance(result, int) and result > 0:
                print(f"  ✓ DIV extracted with method {i+1}: {result}")
                return result
        except Exception as e:
            print(f"  ⚠ Method {i+1} failed: {e}")
    
    print(f"  ❌ All extraction methods failed, using 0")
    return 0

def extract_experiment_name_robust(info_raw: Dict) -> str:
    """Extract experiment name robustly"""
    return _extract_field_robust(info_raw, 'FN', 'experiment')

def _extract_field_robust(info_raw: Dict, field_name: str, field_type: str) -> str:
    """Generic robust field extraction"""
    print(f"🔍 Extracting {field_type} from: {type(info_raw[field_name])}")
    
    extraction_methods = [
        lambda: str(info_raw[field_name][0][0][0][0][0]),
        lambda: _unwrap_nested_array(info_raw[field_name]),
        lambda: str(info_raw[field_name][0][0][0][0]),
        lambda: str(info_raw[field_name][0][0][0]),
        lambda: str(info_raw[field_name][0][0]),
        lambda: _extract_with_regex(str(info_raw[field_name])),
        lambda: info_raw[field_name][0][0][0].item() if hasattr(info_raw[field_name][0][0][0], 'item') else None
    ]
    
    for i, method in enumerate(extraction_methods):
        try:
            result = method()
            if result and isinstance(result, str) and 'array' not in result and 'dtype' not in result:
                print(f"  ✓ {field_type} extracted with method {i+1}: '{result}'")
                return result
        except Exception as e:
            print(f"  ⚠ Method {i+1} failed: {e}")
    
    print(f"  ❌ All extraction methods failed, using 'Unknown'")
    return "Unknown"

def _unwrap_nested_array(nested_array: np.ndarray) -> Optional[str]:
    """Recursively unwrap nested numpy arrays to get to the string value"""
    current = nested_array
    max_depth = 20
    
    for depth in range(max_depth):
        if isinstance(current, np.ndarray):
            if current.size == 0:
                return None
            elif current.size == 1:
                try:
                    current = current.item()
                except:
                    current = current[0]
            else:
                current = current[0]
        elif isinstance(current, str):
            return current
        else:
            return str(current)
    
    return None

def _extract_with_regex(text: str) -> Optional[str]:
    """Extract group name using regex from string representation"""
    # Match common patterns like 'WM5050A' inside the string
    match = re.search(r"'([A-Za-z0-9_]+)'", text)
    if match:
        return match.group(1)
    
    # Match patterns without quotes
    match = re.search(r"([A-Za-z0-9_]{5,})", text)
    if match:
        return match.group(1)
    
    return None

# =============================================================================
# DATA EXTRACTION - Separated by data type
# =============================================================================

def extract_ephys_data(ephys_raw: Dict) -> Dict[str, Any]:
    """
    Extract ephys data from MATLAB structure
    Separated into electrode-level and recording-level extraction
    """
    print("📊 Extracting ephys data...")
    
    extracted_data = {}
    
    # Extract electrode-level data
    electrode_data = _extract_electrode_level_data(ephys_raw)
    extracted_data.update(electrode_data)
    
    # Extract recording-level data
    recording_data = _extract_recording_level_data(ephys_raw)
    extracted_data.update(recording_data)
    
    return extracted_data

def _extract_electrode_level_data(ephys_raw: Dict) -> Dict[str, np.ndarray]:
    """Extract electrode-level metrics (arrays)"""
    electrode_fields = [
        'FR',                           # Firing rates
        'channelBurstRate',            # Burst rates per electrode
        'channelBurstDur',             # Burst durations per electrode  
        'channelISIwithinBurst',       # ISI within bursts per electrode
        'channeISIoutsideBurst',       # ISI outside bursts per electrode (typo in original)
        'channelFracSpikesInBursts'    # Fraction spikes in bursts per electrode
    ]
    
    electrode_data = {}
    
    for field in electrode_fields:
        try:
            if field in ephys_raw.dtype.names:
                # Extract array data: [0][0] gets the actual numpy array
                array_data = ephys_raw[field][0][0]
                if array_data.size > 0:
                    electrode_data[field] = array_data.flatten()
                else:
                    electrode_data[field] = np.array([])
                print(f"  ✓ {field}: {len(electrode_data[field])} values")
            else:
                print(f"  ⚠ {field}: not found")
                electrode_data[field] = np.array([])
        except Exception as e:
            print(f"  ✗ {field}: error - {e}")
            electrode_data[field] = np.array([])
    
    return electrode_data

def _extract_recording_level_data(ephys_raw: Dict) -> Dict[str, float]:
    """Extract recording-level metrics (scalars)"""
    recording_fields = [
        'numActiveElec',               # Number of active electrodes
        'FRmean',                      # Mean firing rate across electrodes
        'FRmedian',                    # Median firing rate  
        'NBurstRate',                  # Network burst rate
        'meanNBstLengthS',             # Mean network burst length
        'CVofINBI',                    # CV of inter-network-burst intervals
        'fracInNburst',                # Fraction of spikes in network bursts
        'meanNumChansInvolvedInNbursts', # Mean number of channels in network bursts
        'meanISIWithinNbursts_ms',     # Mean ISI within network bursts
        'meanISIoutsideNbursts_ms',    # Mean ISI outside network bursts
        'singleElecBurstRate',         # Single electrode burst rate
        'singleElecBurstDur',          # Single electrode burst duration
        'singleElecISIwithinBurst',    # Single electrode ISI within burst
        'singleElecISIoutsideBurst',   # Single electrode ISI outside burst
        'meanFracSpikesInBurstsPerElec' # Mean fraction spikes in bursts per electrode
    ]
    
    recording_data = {}
    
    for field in recording_fields:
        try:
            if field in ephys_raw.dtype.names:
                # Extract scalar data: [0][0][0][0] gets the actual value
                scalar_data = ephys_raw[field][0][0]
                if scalar_data.size > 0:
                    recording_data[field] = float(scalar_data.flatten()[0])
                else:
                    recording_data[field] = np.nan
                print(f"  ✓ {field}: {recording_data[field]:.3f}")
            else:
                print(f"  ⚠ {field}: not found")
                recording_data[field] = np.nan
        except Exception as e:
            print(f"  ✗ {field}: error - {e}")
            recording_data[field] = np.nan
    
    return recording_data

def extract_info_data(info_raw: Dict) -> Dict[str, Any]:
    """Extract experiment metadata"""
    print("📋 Extracting info data...")
    
    info_data = {
        'FN': extract_experiment_name_robust(info_raw),
        'Grp': [extract_group_name_robust(info_raw)],  # Keep as list for compatibility
        'DIV': [extract_div_value_robust(info_raw)]
    }
    
    return info_data

def extract_spatial_data(raw_data: Dict) -> Dict[str, Any]:
    """Extract spatial data (coordinates and channels)"""
    print("🗺️ Extracting spatial data...")
    
    spatial_data = {}
    
    # Extract channels
    if 'channels' in raw_data:
        try:
            channels_data = raw_data['channels'][0]
            spatial_data['channels'] = channels_data.flatten().astype(int)
            print(f"  ✓ Channels: {len(spatial_data['channels'])} electrodes")
        except Exception as e:
            spatial_data['channels'] = np.array([])
            print(f"  ✗ Channels: error - {e}")
    else:
        spatial_data['channels'] = np.array([])
        print(f"  ✗ Channels: not found")
    
    # Extract coordinates
    if 'coords' in raw_data:
        try:
            coords_data = raw_data['coords'][0]
            spatial_data['coords'] = coords_data.tolist()  # Convert to list of [x,y] pairs
            print(f"  ✓ Coordinates: {len(spatial_data['coords'])} positions")
        except Exception as e:
            spatial_data['coords'] = []
            print(f"  ✗ Coordinates: error - {e}")
    else:
        spatial_data['coords'] = []
        print(f"  ✗ Coordinates: not found")
    
    return spatial_data

# =============================================================================
# DATA PROCESSING - Moved to use utils functions where possible
# =============================================================================

def calculate_missing_fields(ephys_data: Dict) -> Dict[str, Any]:
    """
    Calculate missing fields using standardized functions
    This function now uses utils where possible
    """
    print("🧮 Calculating missing fields...")
    
    calculated_fields = {}
    
    # Calculate within-burst firing rate (critical missing field)
    within_burst_fr = calculate_within_burst_firing_rate(ephys_data)
    calculated_fields['channelFRinBurst'] = within_burst_fr
    print(f"  ✓ channelFRinBurst: calculated for {len(within_burst_fr)} electrodes")
    
    return calculated_fields

def calculate_within_burst_firing_rate(ephys_data: Dict) -> np.ndarray:
    """
    Calculate within-burst firing rate from ExperimentMatFiles data
    
    This function could potentially be moved to utils/data_helpers.py
    but keeping it here for now due to MEA-NAP specific methodology
    """
    print("🔥 Calculating within-burst firing rate...")
    
    # Extract required fields using utils functions for validation
    FR = clean_numeric_array(ephys_data.get('FR', np.array([])))
    frac_in_bursts = clean_numeric_array(ephys_data.get('channelFracSpikesInBursts', np.array([])))
    burst_rate = clean_numeric_array(ephys_data.get('channelBurstRate', np.array([])))
    burst_dur = clean_numeric_array(ephys_data.get('channelBurstDur', np.array([])))
    
    # Check array lengths match
    if not (len(FR) == len(frac_in_bursts) == len(burst_rate) == len(burst_dur)):
        print(f"  ⚠ Array length mismatch: FR={len(FR)}, frac={len(frac_in_bursts)}, rate={len(burst_rate)}, dur={len(burst_dur)}")
        return np.full_like(FR, np.nan)
    
    # Create valid data mask using utils validation
    valid_mask = np.array([
        (br > BURST_DETECTION_THRESHOLD and bd > 0 and fib > 0 and 
         is_valid_numeric_value(fr) and is_valid_numeric_value(fib) and 
         is_valid_numeric_value(br) and is_valid_numeric_value(bd))
        for fr, fib, br, bd in zip(FR, frac_in_bursts, burst_rate, burst_dur)
    ])
    
    # Initialize output with NaN
    within_burst_fr = np.full_like(FR, np.nan, dtype=float)
    
    if np.any(valid_mask):
        # Calculate using MEA-NAP methodology
        spikes_in_bursts_per_sec = FR[valid_mask] * frac_in_bursts[valid_mask]
        bursts_per_second = burst_rate[valid_mask] / 60.0  # Convert from per minute
        burst_duration_sec = burst_dur[valid_mask] / 1000.0  # Convert from ms
        time_in_bursts_per_sec = bursts_per_second * burst_duration_sec
        
        # Avoid division by very small numbers
        time_mask = time_in_bursts_per_sec > 1e-10
        
        if np.any(time_mask):
            valid_indices = np.where(valid_mask)[0]
            final_valid_indices = valid_indices[time_mask]
            
            within_burst_fr[final_valid_indices] = (
                spikes_in_bursts_per_sec[time_mask] / time_in_bursts_per_sec[time_mask]
            )
    
    valid_calculations = np.sum(~np.isnan(within_burst_fr))
    print(f"    Valid calculations: {valid_calculations}/{len(within_burst_fr)}")
    
    if valid_calculations > 0:
        valid_values = within_burst_fr[~np.isnan(within_burst_fr)]
        print(f"    Range: {np.min(valid_values):.3f} - {np.max(valid_values):.3f} Hz")
    
    return within_burst_fr

# =============================================================================
# FILE OPERATIONS - Separated and simplified
# =============================================================================

def find_experiment_mat_files(base_folder: str) -> List[str]:
    """Find all ExperimentMatFiles in MEA-NAP output structure"""
    print(f"🔍 Searching for experiment files in: {base_folder}")
    
    # Look for ExperimentMatFiles folder
    experiment_mat_folder = os.path.join(base_folder, EXPERIMENT_MAT_FOLDER)
    
    if not os.path.exists(experiment_mat_folder):
        raise FileNotFoundError(f"ExperimentMatFiles folder not found in {base_folder}")
    
    # Find all .mat files
    mat_files = []
    for ext in SUPPORTED_EXTENSIONS:
        pattern = os.path.join(experiment_mat_folder, f'*{ext}')
        mat_files.extend(glob.glob(pattern))
    
    if not mat_files:
        raise FileNotFoundError(f"No .mat files found in {experiment_mat_folder}")
    
    print(f"Found {len(mat_files)} experiment files:")
    for f in mat_files:
        print(f"  - {os.path.basename(f)}")
    
    return mat_files

def validate_file_size(file_path: str) -> bool:
    """Validate file size against configuration limits"""
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    
    if file_size_mb > MAX_FILE_SIZE_MB:
        print(f"⚠️ Warning: File {os.path.basename(file_path)} is {file_size_mb:.1f}MB (limit: {MAX_FILE_SIZE_MB}MB)")
        return False
    
    return True

# =============================================================================
# MAIN LOADING FUNCTIONS - Refactored to be more focused
# =============================================================================

def load_single_experiment_file(mat_file_path: str) -> Optional[Dict]:
    """
    Load a single ExperimentMatFile - REFACTORED to be more focused
    
    This function now has a single responsibility: loading one file
    It delegates extraction and processing to specialized functions
    """
    print(f"📂 Loading: {os.path.basename(mat_file_path)}")
    
    # Validate file
    if not validate_file_size(mat_file_path):
        print(f"⚠️ Skipping large file: {os.path.basename(mat_file_path)}")
        return None
    
    try:
        # Load MATLAB file
        raw_data = sio.loadmat(mat_file_path)
        
        # Initialize extracted data structure
        extracted_data = {}
        
        # Extract different types of data using specialized functions
        if 'Ephys' in raw_data:
            extracted_data['Ephys'] = extract_ephys_data(raw_data['Ephys'])
            
            # Calculate missing fields
            calculated_fields = calculate_missing_fields(extracted_data['Ephys'])
            extracted_data['Ephys'].update(calculated_fields)
        
        if 'Info' in raw_data:
            extracted_data['Info'] = extract_info_data(raw_data['Info'])
        
        # Extract spatial data
        spatial_data = extract_spatial_data(raw_data)
        extracted_data.update(spatial_data)
        
        return extracted_data
        
    except Exception as e:
        print(f"✗ Failed to load {mat_file_path}: {e}")
        return None

def load_all_experiment_data(base_folder: str) -> List[Dict]:
    """
    Load all ExperimentMatFiles from MEA-NAP output
    REFACTORED to be more focused on orchestration
    """
    print(f"🔄 Loading all experiments from: {base_folder}")
    
    try:
        # Find all .mat files
        mat_files = find_experiment_mat_files(base_folder)
        
        # Load each file
        all_experiments = []
        
        for mat_file in mat_files:
            experiment_data = load_single_experiment_file(mat_file)
            if experiment_data is not None:
                all_experiments.append(experiment_data)
        
        print(f"\n✓ Successfully loaded {len(all_experiments)} experiments")
        
        # Validation summary using utils functions
        _print_validation_summary(all_experiments)
        
        return all_experiments
        
    except Exception as e:
        print(f"❌ Error loading experiments: {e}")
        raise

def _print_validation_summary(all_experiments: List[Dict]) -> None:
    """Print validation summary of loaded experiments"""
    print("\n📊 Validation Summary:")
    
    for exp in all_experiments:
        exp_name = exp['Info']['FN']
        group = exp['Info']['Grp'][0]
        div = exp['Info']['DIV'][0]
        n_electrodes = len(exp['channels']) if 'channels' in exp else 0
        
        # Check for burst data using utils validation
        burst_rates = exp['Ephys']['channelBurstRate']
        n_valid_bursts = len(clean_numeric_array(burst_rates))
        
        print(f"  {exp_name} ({group}, DIV{div}): {n_electrodes} electrodes, {n_valid_bursts} with burst data")

# =============================================================================
# DASHBOARD FORMAT CONVERSION - Refactored to use utils
# =============================================================================

def convert_to_dashboard_format(all_experiments: List[Dict]) -> Dict:
    """
    Convert ExperimentMatFiles data to dashboard format
    REFACTORED to use utils package for data processing
    """
    print("\n🔄 Converting to dashboard format...")
    
    # Initialize dashboard data structure
    dashboard_data = {
        'neuronal': {
            'by_experiment': {},
            'by_group': {},
            'by_div': {},
            'groups': [],
            'divs': []
        },
        'info': {
            'groups': [],
            'divs': {},
            'experiments': {}
        }
    }
    
    # Get metric lists from utils metric processors
    from utils.metric_processors import get_recording_level_metrics, get_electrode_level_metrics
    recording_level_metrics = get_recording_level_metrics()
    electrode_level_metrics = get_electrode_level_metrics()
    
    # Process each experiment using focused functions
    for exp in all_experiments:
        _process_single_experiment(exp, dashboard_data, recording_level_metrics, electrode_level_metrics)
    
    # Sort divs using utils functions
    dashboard_data['neuronal']['divs'].sort()
    
    # Print summary using utils functions
    _print_conversion_summary(dashboard_data)
    
    return dashboard_data

def _process_single_experiment(exp: Dict, dashboard_data: Dict, 
                             recording_metrics: List[str], electrode_metrics: List[str]) -> None:
    """Process a single experiment into dashboard format"""
    exp_name = exp['Info']['FN']
    group_raw = exp['Info']['Grp'][0]
    div_raw = exp['Info']['DIV'][0]
    
    # Clean group and div using utils validation
    group = str(group_raw).strip()
    div = int(div_raw) if isinstance(div_raw, (int, float)) else int(div_raw.item() if hasattr(div_raw, 'item') else div_raw)
    
    print(f"Processing: {exp_name} ({group}, DIV{div})")
    
    # Add to by_experiment
    dashboard_data['neuronal']['by_experiment'][exp_name] = {
        'group': group,
        'div': div,
        'activity': exp['Ephys']
    }
    
    # Update groups and divs lists
    _update_groups_and_divs(dashboard_data, group, div, exp_name)
    
    # Add to group and div aggregations
    _add_to_aggregations(dashboard_data, group, div, exp_name, exp['Ephys'], 
                        recording_metrics, electrode_metrics)

def _update_groups_and_divs(dashboard_data: Dict, group: str, div: int, exp_name: str) -> None:
    """Update groups and divs lists"""
    if group not in dashboard_data['neuronal']['groups']:
        dashboard_data['neuronal']['groups'].append(group)
        dashboard_data['info']['groups'].append(group)
        dashboard_data['info']['experiments'][group] = []
        dashboard_data['info']['divs'][group] = {}
    
    if div not in dashboard_data['neuronal']['divs']:
        dashboard_data['neuronal']['divs'].append(div)
        
    # Add to info structure
    dashboard_data['info']['experiments'][group].append(exp_name)
    if div not in dashboard_data['info']['divs'][group]:
        dashboard_data['info']['divs'][group][div] = []
    dashboard_data['info']['divs'][group][div].append(exp_name)

def _add_to_aggregations(dashboard_data: Dict, group: str, div: int, exp_name: str, 
                        ephys_data: Dict, recording_metrics: List[str], electrode_metrics: List[str]) -> None:
    """Add experiment data to group and div aggregations"""
    # Initialize structures if needed
    if group not in dashboard_data['neuronal']['by_group']:
        dashboard_data['neuronal']['by_group'][group] = {'exp_names': []}
        for metric in electrode_metrics + recording_metrics:
            dashboard_data['neuronal']['by_group'][group][metric] = []
    
    if div not in dashboard_data['neuronal']['by_div']:
        dashboard_data['neuronal']['by_div'][div] = {'exp_names': [], 'groups': []}
        for metric in electrode_metrics + recording_metrics:
            dashboard_data['neuronal']['by_div'][div][metric] = []
    
    # Add experiment to aggregations
    dashboard_data['neuronal']['by_group'][group]['exp_names'].append(exp_name)
    dashboard_data['neuronal']['by_div'][div]['exp_names'].append(exp_name)
    dashboard_data['neuronal']['by_div'][div]['groups'].append(group)
    
    # Add data using utils validation
    _add_metric_data_to_aggregations(dashboard_data, group, div, ephys_data, 
                                   recording_metrics, electrode_metrics)

def _add_metric_data_to_aggregations(dashboard_data: Dict, group: str, div: int, 
                                   ephys_data: Dict, recording_metrics: List[str], 
                                   electrode_metrics: List[str]) -> None:
    """Add metric data to aggregations using utils validation"""
    # Add electrode-level data (individual values)
    for metric in electrode_metrics:
        if metric in ephys_data:
            values = clean_numeric_array(ephys_data[metric])
            if len(values) > 0:
                dashboard_data['neuronal']['by_group'][group][metric].extend(values)
                dashboard_data['neuronal']['by_div'][div][metric].extend(values)
    
    # Add recording-level data (one value per recording)
    for metric in recording_metrics:
        if metric in ephys_data:
            value = ephys_data[metric]
            if is_valid_numeric_value(value):
                dashboard_data['neuronal']['by_group'][group][metric].append(value)
                dashboard_data['neuronal']['by_div'][div][metric].append(value)

def _print_conversion_summary(dashboard_data: Dict) -> None:
    """Print conversion summary using utils functions"""
    print(f"\n✅ Dashboard format conversion complete:")
    print(f"   📊 Groups: {dashboard_data['neuronal']['groups']}")
    print(f"   📊 DIVs: {dashboard_data['neuronal']['divs']}")
    print(f"   📄 Experiments: {len(dashboard_data['neuronal']['by_experiment'])}")
    
    # Print data availability summary
    print(f"\n📋 Data availability summary:")
    for group in dashboard_data['neuronal']['groups']:
        group_data = dashboard_data['neuronal']['by_group'][group]
        print(f"   {group}:")
        print(f"     - Experiments: {len(group_data['exp_names'])}")
        print(f"     - FR values: {len(clean_numeric_array(group_data.get('FR', [])))}")
        print(f"     - Burst rate values: {len(clean_numeric_array(group_data.get('channelBurstRate', [])))}")
        print(f"     - Active electrodes: {len(clean_numeric_array(group_data.get('numActiveElec', [])))}")

# =============================================================================
# HIGH-LEVEL INTERFACE FUNCTIONS - Kept simple and focused
# =============================================================================

def scan_experiment_mat_folder(base_folder: str) -> Dict:
    """
    Scan ExperimentMatFiles to create info structure
    REFACTORED to be a simple orchestrator
    """
    print(f"🔍 Scanning ExperimentMatFiles in: {base_folder}")
    
    try:
        # Load all experiment data
        all_experiments = load_all_experiment_data(base_folder)
        
        # Convert to dashboard format
        dashboard_data = convert_to_dashboard_format(all_experiments)
        
        # Extract info structure
        info = dashboard_data['info']
        info['lags'] = []  # ExperimentMatFiles don't have network lags
        
        return info
        
    except Exception as e:
        print(f"❌ Error scanning ExperimentMatFiles: {e}")
        raise

def load_neuronal_activity_from_experiment_files(base_folder: str) -> Dict:
    """
    Load neuronal activity data from ExperimentMatFiles
    REFACTORED to be a simple orchestrator
    """
    print(f"📊 Loading neuronal activity from ExperimentMatFiles...")
    
    try:
        # Load all experiment data
        all_experiments = load_all_experiment_data(base_folder)
        
        # Convert to dashboard format  
        dashboard_data = convert_to_dashboard_format(all_experiments)
        
        return dashboard_data['neuronal']
        
    except Exception as e:
        print(f"❌ Error loading neuronal activity: {e}")
        raise