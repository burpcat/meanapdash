# app.py
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import os
from data_processing.data_loader import (scan_graph_data_folder, 
                                        load_neuronal_activity_data, 
                                        load_network_metrics_data,
                                        load_node_cartography_data,
                                        load_mat_file)
from components.layout import create_layout
from callbacks.neuronal_callbacks import register_neuronal_callbacks
from callbacks.network_callbacks import register_network_callbacks
from data_processing.utilities import extract_matlab_struct_data
# Initialize the app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)
server = app.server  # For deployment

# Set the title
app.title = "MEA-NAP Dashboard"

# Load data
GRAPH_DATA_PATH = "/Volumes/GDrive/MEA_work/combined_data/output/div5053rec1/GraphData"  # Update with your GraphData path

# Scan GraphData folder
print("Scanning GraphData folder...")
data_info = scan_graph_data_folder(GRAPH_DATA_PATH)
print(f"Found {len(data_info['groups'])} groups, {sum(len(exps) for exps in data_info['experiments'].values())} experiments, and {len(data_info['lags'])} lag values")

# Check a sample node metrics file to verify structure
sample_node_files = []
for group in data_info['groups']:
    for exp in data_info['experiments'][group][:1]:  # Just check the first experiment in each group
        for lag in data_info['lags']:
            node_file = os.path.join(GRAPH_DATA_PATH, group, exp, f"{exp}_nodeMetrics_lag{lag}.mat")
            if os.path.exists(node_file):
                sample_node_files.append(node_file)
                break
        if sample_node_files:
            break
    if len(sample_node_files) >= 2:  # Limit to 2 files
        break

print(f"\nChecking {len(sample_node_files)} sample node metrics files...")
for file in sample_node_files:
    print(f"Examining: {file}")
    try:
        data = load_mat_file(file)
        print(f"  Keys: {list(data.keys())}")
        
        # Look for nodeMetrics field
        node_metrics = extract_matlab_struct_data(data, 'nodeMetrics', None)
        if node_metrics is not None:
            if hasattr(node_metrics, '_fieldnames'):
                print(f"  nodeMetrics found with fields: {node_metrics._fieldnames}")
            elif isinstance(node_metrics, dict):
                print(f"  nodeMetrics found with keys: {list(node_metrics.keys())}")
            else:
                print(f"  nodeMetrics found with type: {type(node_metrics)}")
        else:
            print("  nodeMetrics not found in file")
    except Exception as e:
        print(f"  Error loading file: {e}")

# Load neuronal activity data
print("Loading neuronal activity data...")
neuronal_data = load_neuronal_activity_data(GRAPH_DATA_PATH, data_info)

# Load neuronal activity data
print("Loading neuronal activity data...")
neuronal_data = load_neuronal_activity_data(GRAPH_DATA_PATH, data_info)

# Load network metrics data
print("Loading network metrics data...")
network_data = load_network_metrics_data(GRAPH_DATA_PATH, data_info)

# Load node cartography data
print("Loading node cartography data...")
cartography_data = load_node_cartography_data(GRAPH_DATA_PATH, data_info)

# Store data in app context
app.data = {
    'info': data_info,
    'neuronal': neuronal_data,
    'network': network_data,
    'cartography': cartography_data
}

# Add this after loading all data in app.py - after line 42
print("\nDEBUG: Checking available neuronal metrics")

# Check recording-level metrics
print("Recording-level metrics:")
for group in neuronal_data['by_group']:
    print(f"\nGroup: {group}")
    for metric in ['FRmean', 'FRmedian', 'numActiveElec', 'NBurstRate', 
                  'meanNumChansInvolvedInNbursts', 'meanNBstLengthS']:
        if metric in neuronal_data['by_group'][group]:
            data_values = neuronal_data['by_group'][group][metric]
            print(f"  {metric}: {len(data_values)} values, type: {type(data_values)} - Sample: {data_values[:2] if data_values else 'None'}")
        else:
            print(f"  {metric}: Not found in data")

# Create app layout
app.layout = create_layout(app)

# Register callbacks
register_neuronal_callbacks(app)
register_network_callbacks(app)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)