# data_processing/utilities.py
import numpy as np
from scipy import stats
import re

def calculate_half_violin_data(data_values, bandwidth=None):
    """
    Calculate kernel density estimation for half violin plots
    
    Parameters:
    -----------
    data_values : array-like
        Data values to calculate KDE
    bandwidth : float, optional
        Bandwidth for KDE
        
    Returns:
    --------
    dict
        Dictionary with KDE data
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

# def compute_recording_level_metrics(electrode_level_data):
#     """
#     Compute recording-level metrics from electrode-level data
    
#     Parameters:
#     -----------
#     electrode_level_data : dict
#         Dictionary with electrode-level metrics
        
#     Returns:
#     --------
#     dict
#         Dictionary with computed recording-level metrics
#     """
#     recording_metrics = {}
    
#     # Compute mean firing rate
#     if 'FR' in electrode_level_data and electrode_level_data['FR'] is not None:
#         fr_data = safe_flatten_array(electrode_level_data['FR'])
#         if len(fr_data) > 0:
#             fr_data = np.array(fr_data)
#             fr_data = fr_data[~np.isnan(fr_data)]  # Remove NaN values
#             if len(fr_data) > 0:
#                 recording_metrics['FRmean'] = float(np.mean(fr_data))
#                 recording_metrics['FRmedian'] = float(np.median(fr_data))
    
#     # Compute number of active electrodes
#     if 'FR' in electrode_level_data and electrode_level_data['FR'] is not None:
#         fr_data = safe_flatten_array(electrode_level_data['FR'])
#         if len(fr_data) > 0:
#             fr_data = np.array(fr_data)
#             # An electrode is considered active if FR > 0.1 Hz (this threshold can be adjusted)
#             recording_metrics['numActiveElec'] = int(np.sum(fr_data > 0.1))
    
#     # Compute burst rate metrics
#     if 'channelBurstRate' in electrode_level_data and electrode_level_data['channelBurstRate'] is not None:
#         burst_data = safe_flatten_array(electrode_level_data['channelBurstRate'])
#         if len(burst_data) > 0:
#             burst_data = np.array(burst_data)
#             burst_data = burst_data[~np.isnan(burst_data)]  # Remove NaN values
#             if len(burst_data) > 0:
#                 recording_metrics['NBurstRate'] = float(np.mean(burst_data))
    
#     # Compute network burst metrics if we have burst durations
#     if 'channelBurstDur' in electrode_level_data and electrode_level_data['channelBurstDur'] is not None:
#         burst_dur_data = safe_flatten_array(electrode_level_data['channelBurstDur'])
#         if len(burst_dur_data) > 0:
#             burst_dur_data = np.array(burst_dur_data)
#             burst_dur_data = burst_dur_data[~np.isnan(burst_dur_data)]  # Remove NaN values
#             if len(burst_dur_data) > 0:
#                 recording_metrics['meanNBstLengthS'] = float(np.mean(burst_dur_data)) / 1000.0  # Convert ms to s
    
#     # Compute ISI within bursts
#     if 'channelISIwithinBurst' in electrode_level_data and electrode_level_data['channelISIwithinBurst'] is not None:
#         isi_within_data = safe_flatten_array(electrode_level_data['channelISIwithinBurst'])
#         if len(isi_within_data) > 0:
#             isi_within_data = np.array(isi_within_data)
#             isi_within_data = isi_within_data[~np.isnan(isi_within_data)]  # Remove NaN values
#             if len(isi_within_data) > 0:
#                 recording_metrics['meanISIWithinNbursts_ms'] = float(np.mean(isi_within_data))
    
#     # Compute ISI outside bursts
#     if 'channeISIoutsideBurst' in electrode_level_data and electrode_level_data['channeISIoutsideBurst'] is not None:
#         isi_outside_data = safe_flatten_array(electrode_level_data['channeISIoutsideBurst'])
#         if len(isi_outside_data) > 0:
#             isi_outside_data = np.array(isi_outside_data)
#             isi_outside_data = isi_outside_data[~np.isnan(isi_outside_data)]  # Remove NaN values
#             if len(isi_outside_data) > 0:
#                 recording_metrics['meanISIoutsideNbursts_ms'] = float(np.mean(isi_outside_data))
    
#     # Compute fraction of spikes in bursts
#     if 'channelFracSpikesInBursts' in electrode_level_data and electrode_level_data['channelFracSpikesInBursts'] is not None:
#         frac_data = safe_flatten_array(electrode_level_data['channelFracSpikesInBursts'])
#         if len(frac_data) > 0:
#             frac_data = np.array(frac_data)
#             frac_data = frac_data[~np.isnan(frac_data)]  # Remove NaN values
#             if len(frac_data) > 0:
#                 recording_metrics['fracInNburst'] = float(np.mean(frac_data))
    
#     return recording_metrics