# data_processing/utilities.py - CLEANED VERSION - Removed debug/verification functions
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