# data_processing/data_loader.py
import os
import numpy as np
import glob
import scipy.io as sio
import h5py
import mat73
from data_processing.utilities import extract_div_value, safe_flatten_array, extract_matlab_struct_data
import re

def load_mat_file(file_path):
    """
    Load a MATLAB .mat file with robust handling of different formats
    """
    try:
        # Try loading with scipy.io first
        data = sio.loadmat(file_path, struct_as_record=False, squeeze_me=True)
        return data
    except NotImplementedError:
        # If that fails, try with mat73 for v7.3 MAT files
        try:
            return mat73.loadmat(file_path)
        except Exception as e:
            # If mat73 fails, try with h5py as a last resort
            try:
                f = h5py.File(file_path, 'r')
                data = {}
                for k, v in f.items():
                    data[k] = v[()]
                f.close()
                return data
            except Exception as e2:
                raise ValueError(f"Could not read MAT file: {file_path} - Errors: SIO/MAT73: {e}, H5PY: {e2}")
    except Exception as e:
        # Handle other exceptions
        raise ValueError(f"Error loading {file_path}: {e}")

def scan_graph_data_folder(graph_data_folder):
    """
    Scan the GraphData folder to identify all groups and experiments
    """
    info = {
        'groups': [],
        'experiments': {},
        'divs': {},
        'lags': set()
    }
    
    # Get all group folders
    group_folders = [f for f in os.listdir(graph_data_folder) 
                    if os.path.isdir(os.path.join(graph_data_folder, f))]
    
    for group in group_folders:
        info['groups'].append(group)
        info['experiments'][group] = []
        info['divs'][group] = {}
        
        group_path = os.path.join(graph_data_folder, group)
        exp_folders = [f for f in os.listdir(group_path) 
                      if os.path.isdir(os.path.join(group_path, f))]
        
        # FIX: This loop was properly indented - inside the group loop
        for exp in exp_folders:
            info['experiments'][group].append(exp)
            
            # Extract DIV from experiment name
            div_parts = [part for part in exp.split('_') if 'DIV' in part]
            if div_parts:
                # Use the helper function
                div = extract_div_value(div_parts[0])
                
                if div not in info['divs'][group]:
                    info['divs'][group][div] = []
                info['divs'][group][div].append(exp)
                
                # Check for lag values from node metrics files
                exp_path = os.path.join(group_path, exp)
                node_metric_files = glob.glob(os.path.join(exp_path, f"{exp}_nodeMetrics_lag*.mat"))
                
                for f in node_metric_files:
                    # Extract lag value from filename
                    lag_part = os.path.basename(f).split('_lag')[1].split('.')[0]
                    try:
                        lag = int(lag_part)
                        info['lags'].add(lag)
                    except ValueError:
                        continue
    
    # Convert lags to sorted list
    info['lags'] = sorted(list(info['lags']))
    
    return info

def load_neuronal_activity_data(graph_data_folder, data_info):
    """
    Load neuronal activity data from GraphData folder
    """
    compiled_data = {
        'by_experiment': {},  # Raw data indexed by experiment
        'by_group': {},       # Data aggregated by group
        'by_div': {},         # Data aggregated by DIV
        'groups': data_info['groups'],
        'divs': sorted(set(div for group_divs in data_info['divs'].values() for div in group_divs.keys()))
    }
    
    # Add recording level metrics fields
    recording_metrics = [
        'FRmean', 'FRmedian', 'numActiveElec', 'NBurstRate', 
        'meanNumChansInvolvedInNbursts', 'meanNBstLengthS',
        'meanISIWithinNbursts_ms', 'meanISIoutsideNbursts_ms',
        'CVofINBI', 'fracInNburst'
    ]
    
    # Loop through groups and experiments
    for group in data_info['groups']:
        compiled_data['by_group'][group] = {
            'FR': [],               # Firing rates
            'channelBurstRate': [], # Burst rates
            'channelBurstDur': [],  # Burst durations
            'channelISIwithinBurst': [],  # ISI within bursts
            'channeISIoutsideBurst': [],  # ISI outside bursts
            'channelFracSpikesInBursts': [],  # Fraction of spikes in bursts
            'exp_names': [],        # Experiment names for reference
            'channels': []          # Channel IDs
        }
        
        # Add recording level metrics
        for metric in recording_metrics:
            compiled_data['by_group'][group][metric] = []
    
    # Initialize DIV data fields too
    for div in compiled_data['divs']:
        if div not in compiled_data['by_div']:
            compiled_data['by_div'][div] = {
                'FR': [],
                'channelBurstRate': [],
                'channelBurstDur': [],
                'channelISIwithinBurst': [],
                'channeISIoutsideBurst': [],
                'channelFracSpikesInBursts': [],
                'exp_names': [],
                'channels': [],
                'groups': []
            }
            
            # Add recording level metrics
            for metric in recording_metrics:
                compiled_data['by_div'][div][metric] = []
    
    # Loop through groups and experiments
    files_loaded = 0
    files_with_errors = 0
    recording_files_found = 0
    recording_files_loaded = 0
    
    print("\nDEBUG: Looking for recordingSpikeActivity.mat and electrodeSpikeActivity.mat files")
    
    for group in data_info['groups']:
        for exp in data_info['experiments'][group]:
            # Look for both file types
            electrode_file = os.path.join(graph_data_folder, group, exp, f"{exp}_electrodeSpikeActivity.mat")
            recording_file = os.path.join(graph_data_folder, group, exp, f"{exp}_recordingSpikeActivity.mat")
            
            # Check which files exist
            electrode_file_exists = os.path.exists(electrode_file)
            recording_file_exists = os.path.exists(recording_file)
            
            print(f"\nExperiment: {exp} (Group: {group})")
            print(f"  electrodeSpikeActivity.mat exists: {electrode_file_exists}")
            print(f"  recordingSpikeActivity.mat exists: {recording_file_exists}")
            
            # If recording file exists, load it first for recording-level metrics
            if recording_file_exists:
                recording_files_found += 1
                try:
                    print(f"Loading recording file: {recording_file}")
                    recording_data = load_mat_file(recording_file)
                    recording_files_loaded += 1
                    
                    # Debug the structure
                    print(f"  Keys in recording file: {list(recording_data.keys())}")
                    
                    # Process recording data
                    recording_metrics = {}
                    
                    # Try to get the recordingData struct if present
                    recording_struct = extract_matlab_struct_data(recording_data, 'recordingData', recording_data)
                    
                    # Extract recording-level metrics
                    recording_level_metrics = [
                        'FRmean', 'FRmedian', 'numActiveElec', 'NBurstRate', 
                        'meanNumChansInvolvedInNbursts', 'meanNBstLengthS',
                        'meanISIWithinNbursts_ms', 'meanISIoutsideNbursts_ms',
                        'CVofINBI', 'fracInNburst'
                    ]
                    
                    print("  Looking for recording-level metrics in recordingData:")
                    for metric in recording_level_metrics:
                        value = extract_matlab_struct_data(recording_struct, metric, None)
                        if value is not None:
                            recording_metrics[metric] = value
                            print(f"    Found {metric} = {value}")
                        else:
                            print(f"    Metric {metric} not found")
                    
                    # Store recording-level metrics in the experiment data
                    if recording_metrics:
                        if exp not in compiled_data['by_experiment']:
                            compiled_data['by_experiment'][exp] = {
                                'group': group,
                                'activity': {}
                            }
                        compiled_data['by_experiment'][exp]['activity'].update(recording_metrics)
                        
                        # Add to group aggregations
                        for metric, value in recording_metrics.items():
                            if metric not in compiled_data['by_group'][group]:
                                compiled_data['by_group'][group][metric] = []
                            compiled_data['by_group'][group][metric].append(value)
                            
                        # Extract DIV
                        div_parts = [part for part in exp.split('_') if 'DIV' in part]
                        if div_parts:
                            div = extract_div_value(div_parts[0])
                            
                            # Add to DIV aggregations
                            if div not in compiled_data['by_div']:
                                compiled_data['by_div'][div] = {
                                    'exp_names': [],
                                    'groups': []
                                }
                                
                                # Add recording level metrics
                                for metric in recording_level_metrics:
                                    compiled_data['by_div'][div][metric] = []
                                
                            for metric, value in recording_metrics.items():
                                compiled_data['by_div'][div][metric].append(value)
                                
                            compiled_data['by_div'][div]['exp_names'].append(exp)
                            compiled_data['by_div'][div]['groups'].append(group)
                    
                except Exception as e:
                    print(f"  Error loading {recording_file}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Now load electrode-level metrics if the file exists
            if electrode_file_exists:
                try:
                    print(f"Loading file: {electrode_file}")
                    files_loaded += 1
                    
                    act_data = load_mat_file(electrode_file)
                    
                    # Debug the structure
                    print(f"Keys in loaded file: {list(act_data.keys())}")
                    
                    # Special handling for mat_struct objects
                    if 'activityData' in act_data:
                        activity_struct = act_data['activityData']
                        
                        # Debug info: Check if it's a mat_struct
                        if hasattr(activity_struct, '_fieldnames'):
                            print(f"activityData is a mat_struct with fields: {activity_struct._fieldnames}")
                            # Create processed data from mat_struct fields
                            processed_data = {}

                            # Check if any field name contains these substrings
                            recording_level_substrings = ['mean', 'median', 'Active', 'Burst', 'network']
                            found_fields = []
                            for field in activity_struct._fieldnames:
                                for substring in recording_level_substrings:
                                    if substring.lower() in field.lower():
                                        found_fields.append(field)
                                        break
                            
                            if found_fields:
                                print(f"Potential recording-level metrics found: {found_fields}")
                                # Try extracting these fields
                                for field in found_fields:
                                    try:
                                        value = getattr(activity_struct, field)
                                        print(f"  {field} = {value} (type: {type(value)})")
                                        # Add it to processed_data if it's not already there
                                        processed_data[field] = value
                                    except Exception as e:
                                        print(f"  Error extracting {field}: {e}")
                            
                            # Access fields directly using getattr
                            # First process electrode-level metrics
                            for metric in ['FR', 'channelBurstRate', 'channelBurstDur', 
                                         'channelISIwithinBurst', 'channeISIoutsideBurst', 
                                         'channelFracSpikesInBursts', 'channels']:
                                if hasattr(activity_struct, metric):
                                    processed_data[metric] = getattr(activity_struct, metric)
                                    print(f"Extracted electrode-level metric: {metric}, type: {type(processed_data[metric])}")
                            
                            # Then process recording-level metrics
                            for metric in recording_metrics:
                                if hasattr(activity_struct, metric):
                                    processed_data[metric] = getattr(activity_struct, metric)
                                    print(f"Extracted recording-level metric: {metric} = {processed_data[metric]}")
                        else:
                            # Handle as a regular dictionary
                            processed_data = {}
                            # Extract electrode-level metrics
                            for metric in ['FR', 'channelBurstRate', 'channelBurstDur', 
                                         'channelISIwithinBurst', 'channeISIoutsideBurst', 
                                         'channelFracSpikesInBursts', 'channels']:
                                processed_data[metric] = extract_matlab_struct_data(activity_struct, metric, [])
                            
                            # Extract recording-level metrics
                            for metric in recording_metrics:
                                processed_data[metric] = extract_matlab_struct_data(activity_struct, metric, None)
                                if processed_data[metric] is not None:
                                    print(f"Found recording-level metric: {metric} = {processed_data[metric]}")
                    else:
                        # No activityData found, use top level
                        processed_data = {}
                        for metric in ['FR', 'channelBurstRate', 'channelBurstDur', 
                                     'channelISIwithinBurst', 'channeISIoutsideBurst', 
                                     'channelFracSpikesInBursts', 'channels'] + recording_metrics:
                            processed_data[metric] = extract_matlab_struct_data(act_data, metric, None)
                    
                    # Store data by experiment
                    compiled_data['by_experiment'][exp] = {
                        'group': group,
                        'activity': processed_data
                    }
                    
                    # Extract DIV
                    div_parts = [part for part in exp.split('_') if 'DIV' in part]
                    if div_parts:
                        div = extract_div_value(div_parts[0])
                        print(f"Extracted DIV: {div} from {div_parts[0]}")
                        
                        # Initialize DIV data if needed
                        if div not in compiled_data['by_div']:
                            compiled_data['by_div'][div] = {
                                'FR': [],
                                'channelBurstRate': [],
                                'channelBurstDur': [],
                                'channelISIwithinBurst': [],
                                'channeISIoutsideBurst': [],
                                'channelFracSpikesInBursts': [],
                                'exp_names': [],
                                'channels': [],
                                'groups': []
                            }
                            
                            # Add recording level metrics
                            for metric in recording_metrics:
                                compiled_data['by_div'][div][metric] = []
                        
                        # Add to DIV data - electrode level metrics
                        for metric in ['FR', 'channelBurstRate', 'channelBurstDur', 
                                      'channelISIwithinBurst', 'channeISIoutsideBurst', 
                                      'channelFracSpikesInBursts']:
                            if metric in processed_data and processed_data[metric] is not None:
                                compiled_data['by_div'][div][metric].extend(safe_flatten_array(processed_data[metric]))
                        
                        # Add to DIV data - recording level metrics
                        for metric in recording_metrics:
                            if metric in processed_data and processed_data[metric] is not None:
                                compiled_data['by_div'][div][metric].append(processed_data[metric])
                        
                        compiled_data['by_div'][div]['exp_names'].append(exp)
                        if 'channels' in processed_data and processed_data['channels'] is not None:
                            compiled_data['by_div'][div]['channels'].extend(safe_flatten_array(processed_data['channels']))
                        compiled_data['by_div'][div]['groups'].append(group)
                    
                    # Add to group data - electrode level metrics
                    for metric in ['FR', 'channelBurstRate', 'channelBurstDur', 
                                  'channelISIwithinBurst', 'channeISIoutsideBurst', 
                                  'channelFracSpikesInBursts']:
                        if metric in processed_data and processed_data[metric] is not None:
                            compiled_data['by_group'][group][metric].extend(safe_flatten_array(processed_data[metric]))
                    
                    # Add to group data - recording level metrics
                    for metric in recording_metrics:
                        if metric in processed_data and processed_data[metric] is not None:
                            compiled_data['by_group'][group][metric].append(processed_data[metric])
                    
                    compiled_data['by_group'][group]['exp_names'].append(exp)
                    if 'channels' in processed_data and processed_data['channels'] is not None:
                        compiled_data['by_group'][group]['channels'].extend(safe_flatten_array(processed_data['channels']))
                    
                    # Print electrode-level metrics status
                    print("  Electrode-level metrics were processed.")
                    if exp in compiled_data['by_experiment']:
                        print(f"  Activity metrics now available for {exp}: {list(compiled_data['by_experiment'][exp]['activity'].keys())}")
                        
                except Exception as e:
                    files_with_errors += 1
                    print(f"Error loading {electrode_file}: {e}")
                    import traceback
                    traceback.print_exc()

    # Add summary stats at the end
    print(f"\nNeuronal activity data summary:")
    print(f"  Found {recording_files_found} recordingSpikeActivity.mat files")
    print(f"  Successfully loaded {recording_files_loaded} recording files")
    print(f"  Found and loaded {files_loaded} electrodeSpikeActivity.mat files")
    print(f"  {files_with_errors} files had loading errors")
    
    # Check which recording-level metrics are available in the compiled data
    print("\nRecording-level metrics available in at least one experiment:")
    for metric in recording_metrics:
        has_values = False
        for group in compiled_data['by_group']:
            if compiled_data['by_group'][group][metric]:
                has_values = True
                break
        if has_values:
            print(f"- {metric}")
    
    print("\nDEBUG: Checking recording-level metrics by DIV")
    for div in compiled_data['divs']:
        if div in compiled_data['by_div']:
            div_metrics = [m for m in compiled_data['by_div'][div].keys() 
                        if m not in ['exp_names', 'groups', 'channels', 'FR', 'channelBurstRate', 
                                    'channelBurstDur', 'channelISIwithinBurst', 
                                    'channeISIoutsideBurst', 'channelFracSpikesInBursts']]
            
            # Only report if there are actual recording metrics
            if div_metrics:
                print(f"  DIV {div} has recording metrics: {div_metrics}")
                
                # Check a couple key metrics
                for key_metric in ['FRmean', 'NBurstRate']:
                    if key_metric in compiled_data['by_div'][div]:
                        values = compiled_data['by_div'][div][key_metric]
                        print(f"    {key_metric}: {len(values)} values")
                        if values:
                            print(f"      First few values: {values[:min(3, len(values))]}")
    
    return compiled_data

def load_network_metrics_data(graph_data_folder, data_info):
    """
    Load network metrics data from GraphData folder with improved handling of MATLAB structures
    
    Parameters:
    -----------
    graph_data_folder : str
        Path to the GraphData folder
    data_info : dict
        Information about groups and experiments from scan_graph_data_folder
        
    Returns:
    --------
    dict
        Dictionary with compiled network metrics data
    """
    compiled_data = {
        'by_experiment': {},  # Raw data indexed by experiment
        'by_group': {},       # Data aggregated by group
        'by_div': {},         # Data aggregated by DIV
        'by_lag': {},         # Data aggregated by lag
        'groups': data_info['groups'],
        'divs': sorted(set(div for group_divs in data_info['divs'].values() for div in group_divs.keys())),
        'lags': data_info['lags']
    }
    
    # Initialize data structures
    for group in data_info['groups']:
        compiled_data['by_group'][group] = {}
        for lag in data_info['lags']:
            compiled_data['by_group'][group][lag] = {
                'node_metrics': {
                    'degree': [],
                    'strength': [],
                    'clustering': [],
                    'betweenness': [],
                    'efficiency_local': [],
                    'participation': [],
                    'control_average': [],
                    'control_modal': [],
                    'channels': [],
                    'exp_names': []
                },
                'network_metrics': {
                    'density': [],
                    'efficiency_global': [],
                    'modularity': [],
                    'smallworldness': [],
                    'exp_names': []
                }
            }
    
    # Initialize data for divs and lags (as before)
    for div in compiled_data['divs']:
        compiled_data['by_div'][div] = {}
        for lag in data_info['lags']:
            compiled_data['by_div'][div][lag] = {
                'node_metrics': {
                    'degree': [],
                    'strength': [],
                    'clustering': [],
                    'betweenness': [],
                    'efficiency_local': [],
                    'participation': [],
                    'control_average': [],
                    'control_modal': [],
                    'channels': [],
                    'exp_names': [],
                    'groups': []
                },
                'network_metrics': {
                    'density': [],
                    'efficiency_global': [],
                    'modularity': [],
                    'smallworldness': [],
                    'exp_names': [],
                    'groups': []
                }
            }
    
    for lag in data_info['lags']:
        compiled_data['by_lag'][lag] = {
            'node_metrics': {
                'degree': [],
                'strength': [],
                'clustering': [],
                'betweenness': [],
                'efficiency_local': [],
                'participation': [],
                'control_average': [],
                'control_modal': [],
                'channels': [],
                'exp_names': [],
                'groups': [],
                'divs': []
            },
            'network_metrics': {
                'density': [],
                'efficiency_global': [],
                'modularity': [],
                'smallworldness': [],
                'exp_names': [],
                'groups': [],
                'divs': []
            }
        }
    
    # Loop through groups and experiments
    for group in data_info['groups']:
        for exp in data_info['experiments'][group]:
            # Extract DIV
            div_parts = [part for part in exp.split('_') if 'DIV' in part]
            if not div_parts:
                continue
                
            div = extract_div_value(div_parts[0])
            compiled_data['by_experiment'][exp] = {
                'group': group,
                'div': div,
                'lags': {}
            }
            
            # Process each lag value
            for lag in data_info['lags']:
                # Node metrics
                node_file = os.path.join(graph_data_folder, group, exp, f"{exp}_nodeMetrics_lag{lag}.mat")
                if os.path.exists(node_file):
                    try:
                        node_data = load_mat_file(node_file)
                        
                        # Process the nodeMetrics structure using our robust extraction function
                        processed_node_data = {}
                        
                        # First try to get the nodeMetrics struct if present
                        node_metrics_struct = extract_matlab_struct_data(node_data, 'nodeMetrics', node_data)
                        
                        # Extract the metrics we care about
                        for metric in ['degree', 'strength', 'clustering', 'betweenness',
                                      'efficiency_local', 'participation', 'control_average', 
                                      'control_modal', 'channels']:
                            processed_node_data[metric] = extract_matlab_struct_data(node_metrics_struct, metric, [])
                        
                        # Store by experiment
                        compiled_data['by_experiment'][exp]['lags'][lag] = {
                            'node_metrics': processed_node_data
                        }
                        
                        # Add to group, div, and lag aggregations
                        for target, target_dict in [
                            (compiled_data['by_group'][group][lag]['node_metrics'], None),
                            (compiled_data['by_div'][div][lag]['node_metrics'], group),
                            (compiled_data['by_lag'][lag]['node_metrics'], (group, div))
                        ]:
                            for metric in ['degree', 'strength', 'clustering', 'betweenness',
                                          'efficiency_local', 'participation', 'control_average', 
                                          'control_modal']:
                                if metric in processed_node_data:
                                    target[metric].extend(safe_flatten_array(processed_node_data[metric]))
                            
                            target['exp_names'].append(exp)
                            if 'channels' in processed_node_data:
                                target['channels'].extend(safe_flatten_array(processed_node_data['channels']))
                            
                            # Add group if needed
                            if target_dict is not None:
                                if isinstance(target_dict, tuple):
                                    target['groups'].append(target_dict[0])
                                    target['divs'].append(target_dict[1])
                                else:
                                    target['groups'].append(target_dict)
                    
                    except Exception as e:
                        print(f"Error loading {node_file}: {e}")
                
                # Network metrics
                net_file = os.path.join(graph_data_folder, group, exp, f"{exp}_networkMetrics_lag{lag}.mat")
                if os.path.exists(net_file):
                    try:
                        net_data = load_mat_file(net_file)
                        
                        # Process the netMetrics structure using our robust extraction function
                        processed_net_data = {}
                        
                        # First try to get the netMetrics struct if present
                        net_metrics_struct = extract_matlab_struct_data(net_data, 'netMetrics', net_data)
                        
                        # Extract the metrics we care about
                        for metric in ['density', 'efficiency_global', 'modularity', 'smallworldness']:
                            processed_net_data[metric] = extract_matlab_struct_data(net_metrics_struct, metric, [])
                        
                        # Store by experiment
                        if lag in compiled_data['by_experiment'][exp]['lags']:
                            compiled_data['by_experiment'][exp]['lags'][lag]['network_metrics'] = processed_net_data
                        else:
                            compiled_data['by_experiment'][exp]['lags'][lag] = {
                                'network_metrics': processed_net_data
                            }
                        
                        # Add to group, div, and lag aggregations
                        for target, target_dict in [
                            (compiled_data['by_group'][group][lag]['network_metrics'], None),
                            (compiled_data['by_div'][div][lag]['network_metrics'], group),
                            (compiled_data['by_lag'][lag]['network_metrics'], (group, div))
                        ]:
                            for metric in ['density', 'efficiency_global', 'modularity', 'smallworldness']:
                                if metric in processed_net_data:
                                    target[metric].extend(safe_flatten_array(processed_net_data[metric]))
                            
                            target['exp_names'].append(exp)
                            
                            # Add group and div if needed
                            if target_dict is not None:
                                if isinstance(target_dict, tuple):
                                    target['groups'].append(target_dict[0])
                                    target['divs'].append(target_dict[1])
                                else:
                                    target['groups'].append(target_dict)
                    
                    except Exception as e:
                        print(f"Error loading {net_file}: {e}")
    
    return compiled_data

def load_node_cartography_data(graph_data_folder, data_info):
    """
    Load node cartography data from GraphData folder with improved handling of MATLAB structures
    
    Parameters:
    -----------
    graph_data_folder : str
        Path to the GraphData folder
    data_info : dict
        Information about groups and experiments from scan_graph_data_folder
        
    Returns:
    --------
    dict
        Dictionary with compiled node cartography data
    """
    compiled_data = {
        'by_experiment': {},  # Raw data indexed by experiment
        'by_group': {},       # Data aggregated by group
        'by_div': {},         # Data aggregated by DIV
        'groups': data_info['groups'],
        'divs': sorted(set(div for group_divs in data_info['divs'].values() for div in group_divs.keys())),
        'lags': data_info['lags']
    }
    
    # Initialize data structures (as before)
    for group in data_info['groups']:
        compiled_data['by_group'][group] = {}
        for lag in data_info['lags']:
            compiled_data['by_group'][group][lag] = {
                'z': [],
                'p': [],
                'nodal_roles': [],
                'role_counts': {
                    'Peripheral': 0,
                    'Non-hub connector': 0,
                    'Non-hub kinless': 0,
                    'Provincial hub': 0,
                    'Connector hub': 0,
                    'Kinless hub': 0
                },
                'exp_names': []
            }
    
    for div in compiled_data['divs']:
        compiled_data['by_div'][div] = {}
        for lag in data_info['lags']:
            compiled_data['by_div'][div][lag] = {
                'z': [],
                'p': [],
                'nodal_roles': [],
                'role_counts': {
                    'Peripheral': 0,
                    'Non-hub connector': 0,
                    'Non-hub kinless': 0,
                    'Provincial hub': 0,
                    'Connector hub': 0,
                    'Kinless hub': 0
                },
                'exp_names': [],
                'groups': []
            }
    
    # Loop through groups and experiments
    for group in data_info['groups']:
        for exp in data_info['experiments'][group]:
            # Extract DIV
            div_parts = [part for part in exp.split('_') if 'DIV' in part]
            if not div_parts:
                continue
                
            div = extract_div_value(div_parts[0])
            compiled_data['by_experiment'][exp] = {
                'group': group,
                'div': div,
                'lags': {}
            }
            
            # Process each lag value
            for lag in data_info['lags']:
                # Node cartography
                cart_file = os.path.join(graph_data_folder, group, exp, f"{exp}_nodeCartography_lag{lag}.mat")
                if os.path.exists(cart_file):
                    try:
                        cart_data = load_mat_file(cart_file)
                        
                        # Process cartographyData structure using our robust extraction function
                        processed_cart_data = {}
                        
                        # First try to get the cartographyData struct if present
                        cart_struct = extract_matlab_struct_data(cart_data, 'cartographyData', cart_data)
                        
                        # Extract the metrics we care about
                        for metric in ['z', 'p', 'roles']:
                            processed_cart_data[metric] = extract_matlab_struct_data(cart_struct, metric, [])
                        
                        # Store by experiment
                        compiled_data['by_experiment'][exp]['lags'][lag] = processed_cart_data
                        
                        # Add to group and div aggregations
                        for target, target_group in [
                            (compiled_data['by_group'][group][lag], None),
                            (compiled_data['by_div'][div][lag], group)
                        ]:
                            for metric in ['z', 'p']:
                                if metric in processed_cart_data:
                                    target[metric].extend(safe_flatten_array(processed_cart_data[metric]))
                            
                            # Add nodal roles and count them
                            if 'roles' in processed_cart_data:
                                roles = safe_flatten_array(processed_cart_data['roles'])
                                
                                target['nodal_roles'].extend(roles)
                                
                                # Count roles
                                for role in target['role_counts'].keys():
                                    target['role_counts'][role] += sum(1 for r in roles if str(r) == str(role))
                            
                            target['exp_names'].append(exp)
                            
                            # Add group if needed
                            if target_group is not None:
                                target['groups'].append(target_group)
                    
                    except Exception as e:
                        print(f"Error loading {cart_file}: {e}")
    
    # Calculate role proportions (as before)
    for group in data_info['groups']:
        for lag in data_info['lags']:
            group_data = compiled_data['by_group'][group][lag]
            total_roles = sum(group_data['role_counts'].values())
            
            if total_roles > 0:
                group_data['role_proportions'] = {
                    role: count / total_roles 
                    for role, count in group_data['role_counts'].items()
                }
            else:
                group_data['role_proportions'] = {role: 0 for role in group_data['role_counts']}
    
    for div in compiled_data['divs']:
        for lag in data_info['lags']:
            div_data = compiled_data['by_div'][div][lag]
            total_roles = sum(div_data['role_counts'].values())
            
            if total_roles > 0:
                div_data['role_proportions'] = {
                    role: count / total_roles 
                    for role, count in div_data['role_counts'].items()
                }
            else:
                div_data['role_proportions'] = {role: 0 for role in div_data['role_counts']}
    
    return compiled_data