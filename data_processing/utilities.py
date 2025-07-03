# data_processing/utilities.py
import numpy as np
from scipy import stats
import re

def calculate_half_violin_data(data_values, bandwidth=None):
    """
    Calculate kernel density estimation for half violin plots with robust error handling
    """
    # Remove NaN values
    data_values = np.array(data_values)
    data_values = data_values[~np.isnan(data_values)]
    
    if len(data_values) <= 1:
        return {
            'x': [],
            'y': [],
            'raw_data': data_values,
            'mean': np.mean(data_values) if len(data_values) > 0 else np.nan,
            'median': np.median(data_values) if len(data_values) > 0 else np.nan,
            'std': np.std(data_values) if len(data_values) > 0 else np.nan,
            'sem': stats.sem(data_values) if len(data_values) > 0 else np.nan
        }
    
    # CHECK FOR LOW VARIANCE DATA (main fix for the KDE error)
    data_std = np.std(data_values)
    data_range = np.max(data_values) - np.min(data_values)
    
    # If all values are identical or nearly identical
    if data_std < 1e-10 or data_range < 1e-10:
        print(f"⚠️ WARNING: Low variance data detected (std={data_std:.2e}, range={data_range:.2e})")
        print(f"Values: {data_values[:10]}...")  # Show first 10 values
        
        # Return a simple point distribution instead of KDE
        mean_val = np.mean(data_values)
        return {
            'x': [mean_val - 0.1, mean_val, mean_val + 0.1],  # Small spread around mean
            'y': [0, len(data_values), 0],  # Simple triangle distribution
            'raw_data': data_values,
            'mean': mean_val,
            'median': np.median(data_values),
            'std': data_std,
            'sem': stats.sem(data_values)
        }
    
    # NORMAL KDE CALCULATION for data with variance
    try:
        # Calculate KDE
        if bandwidth is None:
            # Use Scott's rule for bandwidth selection
            bandwidth = 1.06 * np.std(data_values) * len(data_values) ** (-1/5)
        
        kde = stats.gaussian_kde(data_values, bw_method=bandwidth)
        x_min, x_max = np.min(data_values), np.max(data_values)
        # Extend range by 5% on each side
        x_range = x_max - x_min
        x_min -= 0.05 * x_range
        x_max += 0.05 * x_range
        
        x = np.linspace(x_min, x_max, 100)
        y = kde(x)
        
        return {
            'x': x,
            'y': y,
            'raw_data': data_values,
            'mean': np.mean(data_values),
            'median': np.median(data_values),
            'std': np.std(data_values),
            'sem': stats.sem(data_values)
        }
        
    except Exception as e:
        print(f"⚠️ KDE calculation failed: {e}")
        # Fallback to simple distribution
        mean_val = np.mean(data_values)
        std_val = np.std(data_values)
        
        return {
            'x': [mean_val - std_val, mean_val, mean_val + std_val],
            'y': [0, len(data_values), 0],
            'raw_data': data_values,
            'mean': mean_val,
            'median': np.median(data_values),
            'std': std_val,
            'sem': stats.sem(data_values)
        }

def extract_div_value(div_string):
    """
    Extract a DIV value from a string, handling complex formats
    
    Parameters:
    -----------
    div_string : str
        String containing DIV information, e.g. 'DIV20240816-24w-50'
        
    Returns:
    --------
    Union[int, str]
        Extracted DIV value (as int if possible, otherwise as string)
    """
    # Remove 'DIV' prefix
    div_str = div_string.replace('DIV', '')
    
    # Try to extract just the numeric part if it's a complex format
    numeric_match = re.search(r'(\d+)$', div_str)  # Match digits at the end
    if numeric_match:
        try:
            return int(numeric_match.group(1))
        except ValueError:
            pass
    
    # If no simple numeric extraction works, return the original string without DIV
    return div_str

def safe_flatten_array(array_data):
    """
    Safely flatten array data from MATLAB structures
    
    Parameters:
    -----------
    array_data : various
        Data from MATLAB file that needs to be flattened
        
    Returns:
    --------
    list
        Flattened data as a Python list
    """
    if array_data is None:
        return []
    
    # Special handling for structured arrays
    try:
        # Check if it's a structured array with nested fields
        if isinstance(array_data, np.ndarray) and array_data.dtype.kind == 'V':
            # For structured arrays, extract all fields and return as list
            result = []
            for item in array_data.flatten():
                # Get all field values and add to result
                try:
                    for field in item.dtype.names:
                        if item[field] is not None:
                            result.append(item[field])
                except:
                    pass
            return result
        
        # For normal numpy arrays
        elif isinstance(array_data, np.ndarray):
            if array_data.dtype.kind in ['O', 'S', 'U']:  # Object or string arrays
                return [item for item in array_data.flatten() if item is not None]
            else:
                return array_data.flatten().tolist()
                
        # For lists and tuples
        elif isinstance(array_data, (list, tuple)):
            return list(array_data)
            
        # For scalar values
        else:
            return [array_data]
            
    except Exception as e:
        # If all else fails, return as a single item list and log the error
        print(f"Warning when flattening array: {e}")
        return [array_data]
    
def extract_matlab_struct_data(struct_data, field_name, default=None):
    """
    Safely extract data from a MATLAB struct
    """
    try:
        # Check if it's a simple dict
        if isinstance(struct_data, dict) and field_name in struct_data:
            return struct_data[field_name]
            
        # Check if it's a numpy array with fields
        elif isinstance(struct_data, np.ndarray) and hasattr(struct_data, 'dtype') and struct_data.dtype.names:
            if field_name in struct_data.dtype.names:
                return struct_data[field_name]
                
        # Check if it's a matlab_objects.MatlabStructure (mat_struct)
        elif hasattr(struct_data, '__dict__') and field_name in struct_data.__dict__:
            return getattr(struct_data, field_name)
            
        # Check if it's a scipy.io.matlab.mio5_params.mat_struct
        elif hasattr(struct_data, '_fieldnames'):
            # This handles mat_struct objects from scipy.io.loadmat
            try:
                # First, see if we can get field names
                if hasattr(struct_data, 'dtype') and hasattr(struct_data.dtype, 'names'):
                    field_names = struct_data.dtype.names
                elif hasattr(struct_data, '_fieldnames'):
                    field_names = struct_data._fieldnames
                else:
                    field_names = []
                
                # Then check if our field is there
                if field_name in field_names:
                    return getattr(struct_data, field_name)
                elif hasattr(struct_data, field_name):
                    return getattr(struct_data, field_name)
            except:
                pass
                
        # Check if it's a numpy structured array element
        elif isinstance(struct_data, np.void) and field_name in struct_data.dtype.names:
            return struct_data[field_name]
            
    except Exception as e:
        print(f"Error extracting field {field_name}: {e}")
        
    return default

def verify_all_metrics(compiled_data):
    """
    Comprehensive verification of all metrics in the loaded data
    
    Parameters:
    -----------
    compiled_data : dict
        The compiled data from load_neuronal_activity_data or load_network_metrics_data
        
    Returns:
    --------
    dict
        Report of metric availability and issues
    """
    report = {
        'neuronal_metrics': {
            'electrode_level': {
                'expected': ['FR', 'channelBurstRate', 'channelBurstDur', 
                           'channelISIwithinBurst', 'channeISIoutsideBurst', 
                           'channelFracSpikesInBursts'],
                'found': [],
                'missing': [],
                'data_counts': {}
            },
            'recording_level': {
                'expected': ['FRmean', 'FRmedian', 'numActiveElec', 'NBurstRate', 
                           'meanNumChansInvolvedInNbursts', 'meanNBstLengthS',
                           'meanISIWithinNbursts_ms', 'meanISIoutsideNbursts_ms',
                           'CVofINBI', 'fracInNburst'],
                'found': [],
                'missing': [],
                'data_counts': {}
            }
        },
        'network_metrics': {
            'node_level': {
                'expected': ['ND', 'NS', 'MEW', 'Eloc', 'BC', 'PC', 'Z', 'aveControl', 'modalControl'],
                'found': [],
                'missing': [],
                'data_counts': {}
            },
            'network_level': {
                'expected': ['aN', 'Dens', 'NDmean', 'NDtop25', 'sigEdgesMean', 'sigEdgesTop10', 
                           'NSmean', 'ElocMean', 'CC', 'nMod', 'Q', 'PL', 'PCmean', 'Eglob', 'SW', 'SWw'],
                'found': [],
                'missing': [],
                'data_counts': {}
            }
        },
        'data_structure_issues': [],
        'recommendations': []
    }
    
    print("=== COMPREHENSIVE METRIC VERIFICATION ===\n")
    
    # Check neuronal metrics
    if 'neuronal' in compiled_data or 'by_group' in compiled_data:
        data_to_check = compiled_data.get('neuronal', compiled_data)
        
        print("1. NEURONAL METRICS VERIFICATION")
        print("-" * 40)
        
        # Check electrode-level metrics
        print("\nA. Electrode-Level Metrics:")
        for metric in report['neuronal_metrics']['electrode_level']['expected']:
            found_in_groups = 0
            total_values = 0
            
            for group in data_to_check.get('groups', []):
                if group in data_to_check.get('by_group', {}):
                    if metric in data_to_check['by_group'][group]:
                        found_in_groups += 1
                        values = data_to_check['by_group'][group][metric]
                        if isinstance(values, list):
                            total_values += len(values)
                        elif values is not None:
                            total_values += 1
            
            if found_in_groups > 0:
                report['neuronal_metrics']['electrode_level']['found'].append(metric)
                report['neuronal_metrics']['electrode_level']['data_counts'][metric] = total_values
                print(f"  ✓ {metric}: Found in {found_in_groups} groups, {total_values} total values")
            else:
                report['neuronal_metrics']['electrode_level']['missing'].append(metric)
                print(f"  ✗ {metric}: NOT FOUND")
        
        # Check recording-level metrics
        print("\nB. Recording-Level Metrics:")
        for metric in report['neuronal_metrics']['recording_level']['expected']:
            found_in_groups = 0
            total_values = 0
            
            for group in data_to_check.get('groups', []):
                if group in data_to_check.get('by_group', {}):
                    if metric in data_to_check['by_group'][group]:
                        found_in_groups += 1
                        values = data_to_check['by_group'][group][metric]
                        if isinstance(values, list):
                            total_values += len(values)
                        elif values is not None:
                            total_values += 1
            
            if found_in_groups > 0:
                report['neuronal_metrics']['recording_level']['found'].append(metric)
                report['neuronal_metrics']['recording_level']['data_counts'][metric] = total_values
                print(f"  ✓ {metric}: Found in {found_in_groups} groups, {total_values} total values")
            else:
                report['neuronal_metrics']['recording_level']['missing'].append(metric)
                print(f"  ✗ {metric}: NOT FOUND")
        
        # Check for unexpected metrics
        print("\nC. Additional Metrics Found:")
        all_expected = (report['neuronal_metrics']['electrode_level']['expected'] + 
                       report['neuronal_metrics']['recording_level']['expected'] + 
                       ['exp_names', 'channels'])  # Known non-metric fields
        
        for group in data_to_check.get('groups', []):
            if group in data_to_check.get('by_group', {}):
                for field in data_to_check['by_group'][group].keys():
                    if field not in all_expected:
                        print(f"  ? {field}: Unexpected metric found in group {group}")
    
    # Check network metrics
    if 'network' in compiled_data:
        data_to_check = compiled_data['network']
        
        print("\n\n2. NETWORK METRICS VERIFICATION")
        print("-" * 40)
        
        # Check node-level metrics
        print("\nA. Node-Level Network Metrics:")
        for lag in data_to_check.get('lags', []):
            print(f"\n  Lag {lag} ms:")
            for metric in report['network_metrics']['node_level']['expected']:
                found_in_groups = 0
                total_values = 0
                
                for group in data_to_check.get('groups', []):
                    if (group in data_to_check.get('by_group', {}) and 
                        lag in data_to_check['by_group'][group] and
                        'node_metrics' in data_to_check['by_group'][group][lag]):
                        
                        if metric in data_to_check['by_group'][group][lag]['node_metrics']:
                            found_in_groups += 1
                            values = data_to_check['by_group'][group][lag]['node_metrics'][metric]
                            if isinstance(values, list):
                                total_values += len(values)
                            elif values is not None:
                                total_values += 1
                
                if found_in_groups > 0:
                    if metric not in report['network_metrics']['node_level']['found']:
                        report['network_metrics']['node_level']['found'].append(metric)
                    report['network_metrics']['node_level']['data_counts'][f"{metric}_lag{lag}"] = total_values
                    print(f"    ✓ {metric}: Found in {found_in_groups} groups, {total_values} total values")
                else:
                    if metric not in report['network_metrics']['node_level']['missing']:
                        report['network_metrics']['node_level']['missing'].append(metric)
                    print(f"    ✗ {metric}: NOT FOUND")
        
        # Check network-level metrics
        print("\nB. Network-Level Metrics:")
        for lag in data_to_check.get('lags', []):
            print(f"\n  Lag {lag} ms:")
            for metric in report['network_metrics']['network_level']['expected']:
                found_in_groups = 0
                total_values = 0
                
                for group in data_to_check.get('groups', []):
                    if (group in data_to_check.get('by_group', {}) and 
                        lag in data_to_check['by_group'][group] and
                        'network_metrics' in data_to_check['by_group'][group][lag]):
                        
                        if metric in data_to_check['by_group'][group][lag]['network_metrics']:
                            found_in_groups += 1
                            values = data_to_check['by_group'][group][lag]['network_metrics'][metric]
                            if isinstance(values, list):
                                total_values += len(values)
                            elif values is not None:
                                total_values += 1
                
                if found_in_groups > 0:
                    if metric not in report['network_metrics']['network_level']['found']:
                        report['network_metrics']['network_level']['found'].append(metric)
                    report['network_metrics']['network_level']['data_counts'][f"{metric}_lag{lag}"] = total_values
                    print(f"    ✓ {metric}: Found in {found_in_groups} groups, {total_values} total values")
                else:
                    if metric not in report['network_metrics']['network_level']['missing']:
                        report['network_metrics']['network_level']['missing'].append(metric)
                    print(f"    ✗ {metric}: NOT FOUND")
    
    # Generate recommendations
    print("\n\n3. RECOMMENDATIONS")
    print("-" * 20)
    
    # Missing neuronal metrics
    if report['neuronal_metrics']['electrode_level']['missing']:
        print(f"\n⚠️  Missing electrode-level metrics: {report['neuronal_metrics']['electrode_level']['missing']}")
        report['recommendations'].append("Check electrode-level data loading in load_neuronal_activity_data()")
    
    if report['neuronal_metrics']['recording_level']['missing']:
        print(f"⚠️  Missing recording-level metrics: {report['neuronal_metrics']['recording_level']['missing']}")
        report['recommendations'].append("Check recording-level data loading - ensure both electrodeLevelActivity.mat and recordingLevelActivity.mat are being loaded")
    
    # Missing network metrics
    if report['network_metrics']['node_level']['missing']:
        print(f"⚠️  Missing node-level network metrics: {report['network_metrics']['node_level']['missing']}")
        report['recommendations'].append("Check node metrics file loading in load_network_metrics_data()")
    
    if report['network_metrics']['network_level']['missing']:
        print(f"⚠️  Missing network-level metrics: {report['network_metrics']['network_level']['missing']}")
        report['recommendations'].append("Check network metrics file loading in load_network_metrics_data()")
    
    # Data structure issues
    data_structure_issues = []
    
    # Check if data is properly organized
    if 'neuronal' in compiled_data or 'by_group' in compiled_data:
        data_to_check = compiled_data.get('neuronal', compiled_data)
        if not data_to_check.get('groups'):
            data_structure_issues.append("No groups found in neuronal data")
        if not data_to_check.get('divs'):
            data_structure_issues.append("No DIVs found in neuronal data")
    
    if 'network' in compiled_data:
        if not compiled_data['network'].get('lags'):
            data_structure_issues.append("No lags found in network data")
    
    if data_structure_issues:
        print(f"\n🔧 Data structure issues: {data_structure_issues}")
        report['data_structure_issues'] = data_structure_issues
    
    print(f"\n✅ Verification complete. Found {len(report['neuronal_metrics']['electrode_level']['found'])} electrode-level and {len(report['neuronal_metrics']['recording_level']['found'])} recording-level neuronal metrics.")
    
    return report

def debug_specific_metric(compiled_data, metric_name, data_type='neuronal'):
    """
    Debug a specific metric that's not working
    
    Parameters:
    -----------
    compiled_data : dict
        The compiled data
    metric_name : str
        Name of the metric to debug
    data_type : str
        'neuronal' or 'network'
    """
    print(f"\n=== DEBUGGING METRIC: {metric_name} ({data_type}) ===")
    
    if data_type == 'neuronal':
        data_to_check = compiled_data.get('neuronal', compiled_data)
        
        print(f"\n1. Checking by_group structure:")
        for group in data_to_check.get('groups', []):
            if group in data_to_check.get('by_group', {}):
                group_data = data_to_check['by_group'][group]
                if metric_name in group_data:
                    values = group_data[metric_name]
                    print(f"  Group {group}: {type(values)} with {len(values) if isinstance(values, list) else 1} values")
                    if isinstance(values, list) and len(values) > 0:
                        print(f"    Sample values: {values[:3]}")
                else:
                    print(f"  Group {group}: {metric_name} NOT FOUND")
                    print(f"    Available metrics: {list(group_data.keys())}")
        
        print(f"\n2. Checking by_experiment structure:")
        experiment_count = 0
        for exp_name, exp_data in data_to_check.get('by_experiment', {}).items():
            if 'activity' in exp_data and metric_name in exp_data['activity']:
                values = exp_data['activity'][metric_name]
                experiment_count += 1
                if experiment_count <= 3:  # Show first 3 experiments
                    print(f"  Experiment {exp_name}: {type(values)} with value {values}")
        
        if experiment_count == 0:
            print(f"  {metric_name} not found in any experiment")
        else:
            print(f"  {metric_name} found in {experiment_count} experiments")
    
    elif data_type == 'network':
        data_to_check = compiled_data.get('network', {})
        
        print(f"\n1. Checking network structure for metric {metric_name}:")
        for lag in data_to_check.get('lags', []):
            print(f"\n  Lag {lag}:")
            found_in_groups = 0
            
            for group in data_to_check.get('groups', []):
                if (group in data_to_check.get('by_group', {}) and 
                    lag in data_to_check['by_group'][group]):
                    
                    lag_data = data_to_check['by_group'][group][lag]
                    
                    # Check node metrics
                    if 'node_metrics' in lag_data and metric_name in lag_data['node_metrics']:
                        values = lag_data['node_metrics'][metric_name]
                        found_in_groups += 1
                        print(f"    Group {group} (node): {len(values) if isinstance(values, list) else 1} values")
                    
                    # Check network metrics
                    if 'network_metrics' in lag_data and metric_name in lag_data['network_metrics']:
                        values = lag_data['network_metrics'][metric_name]
                        found_in_groups += 1
                        print(f"    Group {group} (network): {len(values) if isinstance(values, list) else 1} values")
            
            if found_in_groups == 0:
                print(f"    {metric_name} not found in any group for lag {lag}")
    
    print(f"\n=== END DEBUG FOR {metric_name} ===\n")

# ADD THIS TO THE END OF load_neuronal_activity_data() in data_loader.py
def run_verification_after_loading():
    """
    Add this call at the end of your data loading functions
    """
    print("\n" + "="*60)
    print("RUNNING AUTOMATIC METRIC VERIFICATION")
    print("="*60)
    
    # This would be called from your main app after loading data
    # Example:
    # report = verify_all_metrics(compiled_data)
    # 
    # # If specific metrics are missing, debug them:
    # for missing_metric in report['neuronal_metrics']['recording_level']['missing']:
    #     debug_specific_metric(compiled_data, missing_metric, 'neuronal')
    
    pass