# data_processing/data_loader.py - FIXED VERSION
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
        
        # Process experiments within each group
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
                
                # Look for both nodeLevelMetrics and nodeMetrics patterns
                node_metric_files = (
                    glob.glob(os.path.join(exp_path, f"{exp}_nodeLevelMetrics_lag*.mat")) +
                    glob.glob(os.path.join(exp_path, f"{exp}_nodeMetrics_lag*.mat"))
                )
                
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
    recording_metrics_list = [
        'FRmean', 'FRmedian', 'numActiveElec', 'NBurstRate', 
        'meanNumChansInvolvedInNbursts', 'meanNBstLengthS',
        'meanISIWithinNbursts_ms', 'meanISIoutsideNbursts_ms',
        'CVofINBI', 'fracInNburst'
    ]
    
    # Initialize group data structures
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
        for metric in recording_metrics_list:
            compiled_data['by_group'][group][metric] = []
    
    # Initialize DIV data fields
    for div in compiled_data['divs']:
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
        for metric in recording_metrics_list:
            compiled_data['by_div'][div][metric] = []
    
    # Loop through groups and experiments
    files_loaded = 0
    files_with_errors = 0
    recording_files_found = 0
    recording_files_loaded = 0
    
    for group in data_info['groups']:
        for exp in data_info['experiments'][group]:
            # Look for both file types
            electrode_file = os.path.join(graph_data_folder, group, exp, f"{exp}_electrodeLevelActivity.mat")
            recording_file = os.path.join(graph_data_folder, group, exp, f"{exp}_recordingLevelActivity.mat")
            
            # Check which files exist
            electrode_file_exists = os.path.exists(electrode_file)
            recording_file_exists = os.path.exists(recording_file)
            
            # If recording file exists, load it first for recording-level metrics
            if recording_file_exists:
                recording_files_found += 1
                try:
                    recording_data = load_mat_file(recording_file)
                    recording_files_loaded += 1
                    
                    # Process recording data
                    recording_metrics = {}
                    
                    # Try to get the recordingLevelData struct
                    recording_struct = extract_matlab_struct_data(recording_data, 'recordingLevelData', recording_data)
                    
                    # Extract recording-level metrics
                    for metric in recording_metrics_list:
                        value = extract_matlab_struct_data(recording_struct, metric, None)
                        if value is not None:
                            recording_metrics[metric] = value
                    
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
                                for metric in recording_metrics_list:
                                    compiled_data['by_div'][div][metric] = []
                                
                            for metric, value in recording_metrics.items():
                                compiled_data['by_div'][div][metric].append(value)
                                
                            compiled_data['by_div'][div]['exp_names'].append(exp)
                            compiled_data['by_div'][div]['groups'].append(group)
                    
                except Exception as e:
                    print(f"Error loading {recording_file}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Now load electrode-level metrics if the file exists
            if electrode_file_exists:
                try:
                    files_loaded += 1
                    
                    act_data = load_mat_file(electrode_file)
                    
                    # Special handling for mat_struct objects
                    if 'electrodeLevelData' in act_data:
                        activity_struct = act_data['electrodeLevelData']
                        
                        # Check if it's a mat_struct
                        if hasattr(activity_struct, '_fieldnames'):
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
                            
                            # Try extracting these fields
                            for field in found_fields:
                                try:
                                    value = getattr(activity_struct, field)
                                    processed_data[field] = value
                                except Exception as e:
                                    print(f"Error extracting {field}: {e}")
                            
                            # Access fields directly using getattr
                            # First process electrode-level metrics
                            for metric in ['FR', 'channelBurstRate', 'channelBurstDur', 
                                         'channelISIwithinBurst', 'channeISIoutsideBurst', 
                                         'channelFracSpikesInBursts', 'channels']:
                                if hasattr(activity_struct, metric):
                                    processed_data[metric] = getattr(activity_struct, metric)
                            
                            # Then process recording-level metrics
                            for metric in recording_metrics_list:
                                if hasattr(activity_struct, metric):
                                    processed_data[metric] = getattr(activity_struct, metric)
                        else:
                            # Handle as a regular dictionary
                            processed_data = {}
                            # Extract electrode-level metrics
                            for metric in ['FR', 'channelBurstRate', 'channelBurstDur', 
                                         'channelISIwithinBurst', 'channeISIoutsideBurst', 
                                         'channelFracSpikesInBursts', 'channels']:
                                processed_data[metric] = extract_matlab_struct_data(activity_struct, metric, [])
                            
                            # Extract recording-level metrics
                            for metric in recording_metrics_list:
                                processed_data[metric] = extract_matlab_struct_data(activity_struct, metric, None)
                    else:
                        # No electrodeLevelData found, try old activityData name for backward compatibility
                        if 'activityData' in act_data:
                            activity_struct = act_data['activityData']
                            processed_data = {}
                            # Handle legacy structure same way
                            for metric in ['FR', 'channelBurstRate', 'channelBurstDur', 
                                         'channelISIwithinBurst', 'channeISIoutsideBurst', 
                                         'channelFracSpikesInBursts', 'channels']:
                                processed_data[metric] = extract_matlab_struct_data(activity_struct, metric, [])
                            
                            for metric in recording_metrics_list:
                                processed_data[metric] = extract_matlab_struct_data(activity_struct, metric, None)
                        else:
                            # No known structure found, use top level
                            processed_data = {}
                            for metric in ['FR', 'channelBurstRate', 'channelBurstDur', 
                                         'channelISIwithinBurst', 'channeISIoutsideBurst', 
                                         'channelFracSpikesInBursts', 'channels'] + recording_metrics_list:
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
                            for metric in recording_metrics_list:
                                compiled_data['by_div'][div][metric] = []
                        
                        # Add to DIV data - electrode level metrics
                        for metric in ['FR', 'channelBurstRate', 'channelBurstDur', 
                                      'channelISIwithinBurst', 'channeISIoutsideBurst', 
                                      'channelFracSpikesInBursts']:
                            if metric in processed_data and processed_data[metric] is not None:
                                compiled_data['by_div'][div][metric].extend(safe_flatten_array(processed_data[metric]))
                        
                        # Add to DIV data - recording level metrics
                        for metric in recording_metrics_list:
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
                            # Take MEAN per experiment, not all individual values
                            exp_mean = np.mean(safe_flatten_array(processed_data[metric]))
                            if not np.isnan(exp_mean):
                                compiled_data['by_group'][group][metric].append(exp_mean)
                    
                    # Add to group data - recording level metrics
                    for metric in recording_metrics_list:
                        if metric in processed_data and processed_data[metric] is not None:
                            compiled_data['by_group'][group][metric].append(processed_data[metric])
                    
                    compiled_data['by_group'][group]['exp_names'].append(exp)
                    if 'channels' in processed_data and processed_data['channels'] is not None:
                        compiled_data['by_group'][group]['channels'].extend(safe_flatten_array(processed_data['channels']))
                        
                except Exception as e:
                    files_with_errors += 1
                    print(f"Error loading {electrode_file}: {e}")
                    import traceback
                    traceback.print_exc()
    
    # Add final summary (simplified)
    print(f"\nNeuronal activity data loaded: {files_loaded} electrode files, {files_with_errors} errors")
    
    return compiled_data

def load_network_metrics_data(graph_data_folder, data_info):
    """
    Load network metrics data from GraphData folder with improved handling of MATLAB structures
    Uses correct MEA-NAP metric field names
    
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
    
    # Use correct MEA-NAP field names
    node_metrics_fields = ['ND', 'NS', 'MEW', 'Eloc', 'BC', 'PC', 'Z', 'aveControl', 'modalControl', 'channels']
    network_metrics_fields = ['aN', 'Dens', 'NDmean', 'NDtop25', 'sigEdgesMean', 'sigEdgesTop10', 
                             'NSmean', 'ElocMean', 'CC', 'nMod', 'Q', 'PL', 'PCmean', 'Eglob', 'SW', 'SWw']
    
    # Initialize data structures
    for group in data_info['groups']:
        compiled_data['by_group'][group] = {}
        for lag in data_info['lags']:
            compiled_data['by_group'][group][lag] = {
                'node_metrics': {field: [] for field in node_metrics_fields + ['exp_names']},
                'network_metrics': {field: [] for field in network_metrics_fields + ['exp_names']}
            }
    
    # Initialize data for divs and lags
    for div in compiled_data['divs']:
        compiled_data['by_div'][div] = {}
        for lag in data_info['lags']:
            compiled_data['by_div'][div][lag] = {
                'node_metrics': {field: [] for field in node_metrics_fields + ['exp_names', 'groups']},
                'network_metrics': {field: [] for field in network_metrics_fields + ['exp_names', 'groups']}
            }
    
    for lag in data_info['lags']:
        compiled_data['by_lag'][lag] = {
            'node_metrics': {field: [] for field in node_metrics_fields + ['exp_names', 'groups', 'divs']},
            'network_metrics': {field: [] for field in network_metrics_fields + ['exp_names', 'groups', 'divs']}
        }
    
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
                # Try both possible node file names
                node_files = [
                    os.path.join(graph_data_folder, group, exp, f"{exp}_nodeLevelMetrics_lag{lag}.mat"),
                    os.path.join(graph_data_folder, group, exp, f"{exp}_nodeMetrics_lag{lag}.mat")
                ]
                
                node_file = None
                for nf in node_files:
                    if os.path.exists(nf):
                        node_file = nf
                        break
                
                if node_file:
                    try:
                        # Load data for processing
                        node_data = load_mat_file(node_file)
                        
                        # Process the node metrics structure using our robust extraction function
                        processed_node_data = {}
                        
                        # Try multiple possible struct names
                        possible_struct_names = ['nodeLevelData', 'nodeMetrics', 'nodeData']
                        node_metrics_struct = node_data
                        
                        for struct_name in possible_struct_names:
                            temp_struct = extract_matlab_struct_data(node_data, struct_name, None)
                            if temp_struct is not None:
                                node_metrics_struct = temp_struct
                                break
                        
                        # Extract the metrics we care about using correct MEA-NAP field names
                        for metric in node_metrics_fields:
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
                            for metric in node_metrics_fields:
                                if metric in processed_node_data and metric != 'channels':
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
                
                # Try both possible network file names
                net_files = [
                    os.path.join(graph_data_folder, group, exp, f"{exp}_networkLevelMetrics_lag{lag}.mat"),
                    os.path.join(graph_data_folder, group, exp, f"{exp}_networkMetrics_lag{lag}.mat")
                ]
                
                net_file = None
                for nf in net_files:
                    if os.path.exists(nf):
                        net_file = nf
                        break
                
                if net_file:
                    try:
                        net_data = load_mat_file(net_file)
                        
                        # Process the network metrics structure using our robust extraction function
                        processed_net_data = {}
                        
                        # Try multiple possible struct names
                        possible_struct_names = ['networkLevelData', 'netMetrics', 'networkData']
                        net_metrics_struct = net_data
                        
                        for struct_name in possible_struct_names:
                            temp_struct = extract_matlab_struct_data(net_data, struct_name, None)
                            if temp_struct is not None:
                                net_metrics_struct = temp_struct
                                break
                        
                        # Extract the metrics we care about using correct MEA-NAP field names
                        for metric in network_metrics_fields:
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
                            for metric in network_metrics_fields:
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
    
    print(f"Network metrics data loaded for {len(data_info['lags'])} lag values")
    
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
    
    # Initialize data structures
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
                        for metric in ['Z', 'PC', 'roles']:  # Note: using Z and PC for cartography
                            processed_cart_data[metric] = extract_matlab_struct_data(cart_struct, metric, [])
                        
                        # Store by experiment
                        compiled_data['by_experiment'][exp]['lags'][lag] = processed_cart_data
                        
                        # Add to group and div aggregations
                        for target, target_group in [
                            (compiled_data['by_group'][group][lag], None),
                            (compiled_data['by_div'][div][lag], group)
                        ]:
                            # Map Z -> z and PC -> p for consistency
                            if 'Z' in processed_cart_data:
                                target['z'].extend(safe_flatten_array(processed_cart_data['Z']))
                            if 'PC' in processed_cart_data:
                                target['p'].extend(safe_flatten_array(processed_cart_data['PC']))
                            
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
    
    # Calculate role proportions
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
    
    print(f"Node cartography data loaded for {len(data_info['lags'])} lag values")
    
    return compiled_data