# data_processing/experiment_mat_loader.py - NEW FILE
"""
ExperimentMatFiles Data Loader for MEA-NAP Dashboard
Based on pipeline Claude's comprehensive guide
"""

import os
import numpy as np
import glob
import scipy.io as sio
from pathlib import Path
from data_processing.utilities import extract_div_value, safe_flatten_array
import re

def extract_group_name_robust(info_raw):
    """
    Robust group name extraction with multiple fallback methods
    Handles deeply nested MATLAB structures that cause numpy array string representations
    """
    
    print(f"🔍 Extracting group from: {type(info_raw['Grp'])}")
    
    extraction_methods = [
        # Method 1: Direct deep access (most common)
        lambda: str(info_raw['Grp'][0][0][0][0][0]),
        
        # Method 2: Iterative unwrapping
        lambda: unwrap_nested_array(info_raw['Grp']),
        
        # Method 3: Four-level extraction
        lambda: str(info_raw['Grp'][0][0][0][0]),
        
        # Method 4: Three-level extraction
        lambda: str(info_raw['Grp'][0][0][0]),
        
        # Method 5: Two-level extraction
        lambda: str(info_raw['Grp'][0][0]),
        
        # Method 6: Regex extraction from string representation
        lambda: extract_with_regex(str(info_raw['Grp'])),
        
        # Method 7: .item() chain
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

def unwrap_nested_array(nested_array):
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

def extract_with_regex(text):
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

def extract_field_name_robust(info_raw, field_name, field_type):
    """Extract experiment name or other text fields robustly"""
    
    print(f"🔍 Extracting {field_type} from: {type(info_raw[field_name])}")
    
    extraction_methods = [
        # Method 1: Direct deep access
        lambda: str(info_raw[field_name][0][0][0][0][0]),
        
        # Method 2: Iterative unwrapping
        lambda: unwrap_nested_array(info_raw[field_name]),
        
        # Method 3: Four-level extraction
        lambda: str(info_raw[field_name][0][0][0][0]),
        
        # Method 4: Three-level extraction
        lambda: str(info_raw[field_name][0][0][0]),
        
        # Method 5: Two-level extraction
        lambda: str(info_raw[field_name][0][0]),
        
        # Method 6: Regex extraction
        lambda: extract_with_regex(str(info_raw[field_name])),
        
        # Method 7: .item() chain
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

def extract_div_value_robust(info_raw):
    """Extract DIV value robustly, handling nested arrays and converting to int"""
    
    print(f"🔍 Extracting DIV from: {type(info_raw['DIV'])}")
    
    extraction_methods = [
        # Method 1: Direct deep access
        lambda: int(info_raw['DIV'][0][0][0][0][0]),
        
        # Method 2: Iterative unwrapping
        lambda: int(unwrap_nested_array(info_raw['DIV'])),
        
        # Method 3: Four-level extraction
        lambda: int(info_raw['DIV'][0][0][0][0]),
        
        # Method 4: Three-level extraction
        lambda: int(info_raw['DIV'][0][0][0]),
        
        # Method 5: Two-level extraction
        lambda: int(info_raw['DIV'][0][0]),
        
        # Method 6: Regex extraction from string
        lambda: int(re.search(r'(\d+)', str(info_raw['DIV'])).group(1)),
        
        # Method 7: .item() chain
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

def calculate_within_burst_firing_rate(ephys_data):
    """
    Calculate within-burst firing rate from ExperimentMatFiles data
    Based on Pipeline Claude's methodology:
    
    within_burst_FR = (spikes_in_bursts_per_sec) / (time_spent_in_bursts_per_sec)
    
    where:
    - spikes_in_bursts_per_sec = FR * frac_in_bursts
    - time_spent_in_bursts_per_sec = (burst_rate/60) * (burst_dur/1000)
    """
    
    # Extract required fields
    FR = ephys_data.get('FR', np.array([]))
    frac_in_bursts = ephys_data.get('channelFracSpikesInBursts', np.array([]))
    burst_rate = ephys_data.get('channelBurstRate', np.array([]))
    burst_dur = ephys_data.get('channelBurstDur', np.array([]))
    
    # Ensure all arrays are numpy arrays
    FR = np.array(FR)
    frac_in_bursts = np.array(frac_in_bursts)
    burst_rate = np.array(burst_rate)
    burst_dur = np.array(burst_dur)
    
    # Check array lengths match
    if not (len(FR) == len(frac_in_bursts) == len(burst_rate) == len(burst_dur)):
        print(f"  ⚠ Array length mismatch: FR={len(FR)}, frac={len(frac_in_bursts)}, rate={len(burst_rate)}, dur={len(burst_dur)}")
        return np.full_like(FR, np.nan)
    
    # Create valid data mask
    valid_mask = (
        (burst_rate > 0) & 
        (burst_dur > 0) & 
        (frac_in_bursts > 0) &
        (~np.isnan(FR)) &
        (~np.isnan(frac_in_bursts)) &
        (~np.isnan(burst_rate)) &
        (~np.isnan(burst_dur))
    )
    
    # Initialize output with NaN
    within_burst_fr = np.full_like(FR, np.nan, dtype=float)
    
    if np.any(valid_mask):
        # Calculate spikes in bursts per second
        spikes_in_bursts_per_sec = FR[valid_mask] * frac_in_bursts[valid_mask]
        
        # Calculate time spent in bursts per second
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

def find_experiment_mat_files(base_folder):
    """
    Find all ExperimentMatFiles in MEA-NAP output structure
    
    Args:
        base_folder: Path to MEA-NAP output (e.g., "OutputData07Jul2025")
    
    Returns:
        List of full paths to .mat files
    """
    
    # Look for ExperimentMatFiles folder
    experiment_mat_folder = os.path.join(base_folder, 'ExperimentMatFiles')
    
    if not os.path.exists(experiment_mat_folder):
        raise FileNotFoundError(f"ExperimentMatFiles folder not found in {base_folder}")
    
    # Find all .mat files
    mat_files = glob.glob(os.path.join(experiment_mat_folder, '*.mat'))
    
    if not mat_files:
        raise FileNotFoundError(f"No .mat files found in {experiment_mat_folder}")
    
    print(f"Found {len(mat_files)} experiment files:")
    for f in mat_files:
        print(f"  - {os.path.basename(f)}")
    
    return mat_files

def load_single_experiment_file(mat_file_path):
    """
    Load a single ExperimentMatFile and extract all data
    
    Args:
        mat_file_path: Full path to .mat file
        
    Returns:
        Dictionary with properly extracted data
    """
    
    try:
        # Load MATLAB file
        raw_data = sio.loadmat(mat_file_path)
        print(f"Loading: {os.path.basename(mat_file_path)}")
        
        # Initialize extracted data structure
        extracted_data = {}
        
        # EXTRACT EPHYS DATA (electrode and recording level)
        if 'Ephys' in raw_data:
            ephys_raw = raw_data['Ephys']
            extracted_data['Ephys'] = {}
            
            # Electrode-level metrics (arrays)
            electrode_fields = [
                'FR',                           # Firing rates
                'channelBurstRate',            # Burst rates per electrode
                'channelBurstDur',             # Burst durations per electrode  
                'channelISIwithinBurst',       # ISI within bursts per electrode
                'channeISIoutsideBurst',       # ISI outside bursts per electrode (typo in original)
                'channelFracSpikesInBursts'    # Fraction spikes in bursts per electrode
            ]
            
            for field in electrode_fields:
                try:
                    if field in ephys_raw.dtype.names:
                        # Extract array data: [0][0] gets the actual numpy array
                        array_data = ephys_raw[field][0][0]
                        if array_data.size > 0:
                            extracted_data['Ephys'][field] = array_data.flatten()
                        else:
                            extracted_data['Ephys'][field] = np.array([])
                        print(f"  ✓ {field}: {len(extracted_data['Ephys'][field])} values")
                    else:
                        print(f"  ⚠ {field}: not found")
                        extracted_data['Ephys'][field] = np.array([])
                except Exception as e:
                    print(f"  ✗ {field}: error - {e}")
                    extracted_data['Ephys'][field] = np.array([])
            
            # Recording-level metrics (scalars)
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
            
            for field in recording_fields:
                try:
                    if field in ephys_raw.dtype.names:
                        # Extract scalar data: [0][0][0][0] gets the actual value
                        scalar_data = ephys_raw[field][0][0]
                        if scalar_data.size > 0:
                            extracted_data['Ephys'][field] = float(scalar_data.flatten()[0])
                        else:
                            extracted_data['Ephys'][field] = np.nan
                        print(f"  ✓ {field}: {extracted_data['Ephys'][field]:.3f}")
                    else:
                        print(f"  ⚠ {field}: not found")
                        extracted_data['Ephys'][field] = np.nan
                except Exception as e:
                    print(f"  ✗ {field}: error - {e}")
                    extracted_data['Ephys'][field] = np.nan
        
        # EXTRACT INFO DATA (experiment metadata)
        if 'Info' in raw_data:
            info_raw = raw_data['Info']
            extracted_data['Info'] = {}
            
            # Extract experiment name - ROBUST EXTRACTION
            exp_name = extract_field_name_robust(info_raw, 'FN', 'experiment')
            extracted_data['Info']['FN'] = exp_name
            print(f"  ✓ Experiment: '{exp_name}'")
            
            # Extract group - ROBUST EXTRACTION with multiple fallback methods
            group = extract_group_name_robust(info_raw)
            extracted_data['Info']['Grp'] = [group]  # Keep as list for compatibility
            print(f"  ✓ Group: '{group}'")
            
            # Extract DIV (age) - ROBUST EXTRACTION
            div = extract_div_value_robust(info_raw)
            extracted_data['Info']['DIV'] = [div]
            print(f"  ✓ DIV: {div}")
        
        # EXTRACT SPATIAL DATA (coordinates and channels)
        if 'channels' in raw_data:
            try:
                channels_data = raw_data['channels'][0]
                extracted_data['channels'] = channels_data.flatten().astype(int)
                print(f"  ✓ Channels: {len(extracted_data['channels'])} electrodes")
            except:
                extracted_data['channels'] = np.array([])
                print(f"  ✗ Channels: not found")
        
        if 'coords' in raw_data:
            try:
                coords_data = raw_data['coords'][0]
                extracted_data['coords'] = coords_data.tolist()  # Convert to list of [x,y] pairs
                print(f"  ✓ Coordinates: {len(extracted_data['coords'])} positions")
            except:
                extracted_data['coords'] = []
                print(f"  ✗ Coordinates: not found")
        
        # CALCULATE MISSING FIELDS
        if 'Ephys' in extracted_data:
            # Calculate within-burst firing rate (critical missing field)
            within_burst_fr = calculate_within_burst_firing_rate(extracted_data['Ephys'])
            extracted_data['Ephys']['channelFRinBurst'] = within_burst_fr
            print(f"  ✓ channelFRinBurst: calculated for {len(within_burst_fr)} electrodes")
        
        return extracted_data
        
    except Exception as e:
        print(f"✗ Failed to load {mat_file_path}: {e}")
        return None

def load_all_experiment_data(base_folder):
    """
    Load all ExperimentMatFiles from MEA-NAP output
    
    Args:
        base_folder: Path to MEA-NAP output folder
        
    Returns:
        List of extracted experiment data dictionaries
    """
    
    # Find all .mat files
    mat_files = find_experiment_mat_files(base_folder)
    
    # Load each file
    all_experiments = []
    
    for mat_file in mat_files:
        experiment_data = load_single_experiment_file(mat_file)
        if experiment_data is not None:
            all_experiments.append(experiment_data)
    
    print(f"\n✓ Successfully loaded {len(all_experiments)} experiments")
    
    # Validation summary
    for exp in all_experiments:
        exp_name = exp['Info']['FN']
        group = exp['Info']['Grp'][0]
        div = exp['Info']['DIV'][0]
        n_electrodes = len(exp['channels']) if 'channels' in exp else 0
        
        # Check for burst data
        burst_rates = exp['Ephys']['channelBurstRate']
        n_non_nan = np.sum(~np.isnan(burst_rates)) if len(burst_rates) > 0 else 0
        
        print(f"  {exp_name} ({group}, DIV{div}): {n_electrodes} electrodes, {n_non_nan} with burst data")
    
    return all_experiments

def convert_to_dashboard_format(all_experiments):
    """
    Convert ExperimentMatFiles data to dashboard format
    
    Args:
        all_experiments: List from load_all_experiment_data()
        
    Returns:
        Dictionary in dashboard format
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
    
    # Recording-level metrics list
    recording_metrics = [
        'numActiveElec', 'FRmean', 'FRmedian', 'NBurstRate', 
        'meanNBstLengthS', 'CVofINBI', 'fracInNburst',
        'meanNumChansInvolvedInNbursts', 'meanISIWithinNbursts_ms', 
        'meanISIoutsideNbursts_ms', 'singleElecBurstRate', 
        'singleElecBurstDur', 'singleElecISIwithinBurst', 
        'singleElecISIoutsideBurst', 'meanFracSpikesInBurstsPerElec'
    ]
    
    # Electrode-level metrics list
    electrode_metrics = [
        'FR', 'channelBurstRate', 'channelBurstDur', 
        'channelISIwithinBurst', 'channeISIoutsideBurst', 
        'channelFracSpikesInBursts', 'channelFRinBurst'  # Added calculated field
    ]
    
    # Process each experiment
    for exp in all_experiments:
        exp_name = exp['Info']['FN']
        group_raw = exp['Info']['Grp'][0]
        div_raw = exp['Info']['DIV'][0]
        
        # Ensure group is a clean string
        group = str(group_raw).strip()
        
        # Ensure div is an integer
        if isinstance(div_raw, np.ndarray):
            if div_raw.size == 1:
                div = int(div_raw.item())
            else:
                div = int(div_raw[0])
        else:
            div = int(div_raw)
        
        print(f"Processing: {exp_name} ({group}, DIV{div})")
        print(f"  🔍 Group type: {type(group)}, Group value: '{group}'")
        
        # Add to by_experiment
        dashboard_data['neuronal']['by_experiment'][exp_name] = {
            'group': group,  # Now guaranteed to be a string
            'div': div,      # Now guaranteed to be an integer
            'activity': exp['Ephys']
        }
        
        # Update groups and divs lists
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
        
        # Initialize group data structure if needed
        if group not in dashboard_data['neuronal']['by_group']:
            dashboard_data['neuronal']['by_group'][group] = {
                'exp_names': []
            }
            # Add all metrics
            for metric in electrode_metrics + recording_metrics:
                dashboard_data['neuronal']['by_group'][group][metric] = []
        
        # Initialize div data structure if needed
        if div not in dashboard_data['neuronal']['by_div']:
            dashboard_data['neuronal']['by_div'][div] = {
                'exp_names': [],
                'groups': []
            }
            # Add all metrics
            for metric in electrode_metrics + recording_metrics:
                dashboard_data['neuronal']['by_div'][div][metric] = []
        
        # Add data to group aggregation
        dashboard_data['neuronal']['by_group'][group]['exp_names'].append(exp_name)
        
        # Add electrode-level data (individual values)
        for metric in electrode_metrics:
            if metric in exp['Ephys']:
                values = exp['Ephys'][metric]
                if len(values) > 0:
                    dashboard_data['neuronal']['by_group'][group][metric].extend(values)
        
        # Add recording-level data (one value per recording)
        for metric in recording_metrics:
            if metric in exp['Ephys']:
                value = exp['Ephys'][metric]
                if not np.isnan(value):
                    dashboard_data['neuronal']['by_group'][group][metric].append(value)
        
        # Add data to div aggregation
        dashboard_data['neuronal']['by_div'][div]['exp_names'].append(exp_name)
        dashboard_data['neuronal']['by_div'][div]['groups'].append(group)
        
        # Add electrode-level data to div
        for metric in electrode_metrics:
            if metric in exp['Ephys']:
                values = exp['Ephys'][metric]
                if len(values) > 0:
                    dashboard_data['neuronal']['by_div'][div][metric].extend(values)
        
        # Add recording-level data to div
        for metric in recording_metrics:
            if metric in exp['Ephys']:
                value = exp['Ephys'][metric]
                if not np.isnan(value):
                    dashboard_data['neuronal']['by_div'][div][metric].append(value)
    
    # Sort divs
    dashboard_data['neuronal']['divs'].sort()
    
    # Print summary
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
        print(f"     - FR values: {len(group_data['FR'])}")
        print(f"     - Burst rate values: {len(group_data['channelBurstRate'])}")
        print(f"     - Active electrodes: {len(group_data['numActiveElec'])}")
    
    return dashboard_data

def scan_experiment_mat_folder(base_folder):
    """
    Scan ExperimentMatFiles to create info structure compatible with existing dashboard
    
    Args:
        base_folder: Path to MEA-NAP output folder
        
    Returns:
        Dictionary with groups, experiments, divs, and lags info
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

def load_neuronal_activity_from_experiment_files(base_folder):
    """
    Load neuronal activity data from ExperimentMatFiles
    
    Args:
        base_folder: Path to MEA-NAP output folder
        
    Returns:
        Dictionary with neuronal activity data in dashboard format
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