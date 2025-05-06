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
    Load neuronal activity data from GraphData folder with improved handling of MATLAB structures
    
    Parameters:
    -----------
    graph_data_folder : str
        Path to the GraphData folder
    data_info : dict
        Information about groups and experiments from scan_graph_data_folder
        
    Returns:
    --------
    dict
        Dictionary with compiled neuronal activity data
    """
    compiled_data = {
        'by_experiment': {},  # Raw data indexed by experiment
        'by_group': {},       # Data aggregated by group
        'by_div': {},         # Data aggregated by DIV
        'groups': data_info['groups'],
        'divs': sorted(set(div for group_divs in data_info['divs'].values() for div in group_divs.keys()))
    }
    
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
        
        for exp in data_info['experiments'][group]:
            # Find the electrodeSpikeActivity file
            act_file = os.path.join(graph_data_folder, group, exp, f"{exp}_electrodeSpikeActivity.mat")
            if not os.path.exists(act_file):
                continue
                
            # Load the data
            try:
                act_data = load_mat_file(act_file)
                
                # Process activityData structure using our robust extraction function
                processed_data = {}
                
                # First try to get the activityData struct if present
                activity_struct = extract_matlab_struct_data(act_data, 'activityData', act_data)
                
                # Extract the metrics we care about
                for metric in ['FR', 'channelBurstRate', 'channelBurstDur', 
                              'channelISIwithinBurst', 'channeISIoutsideBurst', 
                              'channelFracSpikesInBursts', 'channels']:
                    processed_data[metric] = extract_matlab_struct_data(activity_struct, metric, [])
                
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
                    
                    # Add to DIV data
                    for metric in ['FR', 'channelBurstRate', 'channelBurstDur', 
                                  'channelISIwithinBurst', 'channeISIoutsideBurst', 
                                  'channelFracSpikesInBursts']:
                        if metric in processed_data:
                            compiled_data['by_div'][div][metric].extend(safe_flatten_array(processed_data[metric]))
                    
                    compiled_data['by_div'][div]['exp_names'].append(exp)
                    if 'channels' in processed_data:
                        compiled_data['by_div'][div]['channels'].extend(safe_flatten_array(processed_data['channels']))
                    compiled_data['by_div'][div]['groups'].append(group)
                
                # Add to group data
                for metric in ['FR', 'channelBurstRate', 'channelBurstDur', 
                              'channelISIwithinBurst', 'channeISIoutsideBurst', 
                              'channelFracSpikesInBursts']:
                    if metric in processed_data:
                        compiled_data['by_group'][group][metric].extend(safe_flatten_array(processed_data[metric]))
                
                compiled_data['by_group'][group]['exp_names'].append(exp)
                if 'channels' in processed_data:
                    compiled_data['by_group'][group]['channels'].extend(safe_flatten_array(processed_data['channels']))
                    
            except Exception as e:
                print(f"Error loading {act_file}: {e}")
    
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