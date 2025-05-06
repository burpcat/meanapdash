# app.py
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import os

from data_processing.data_loader import (scan_graph_data_folder, 
                                        load_neuronal_activity_data, 
                                        load_network_metrics_data,
                                        load_node_cartography_data)
from components.layout import create_layout
from callbacks.neuronal_callbacks import register_neuronal_callbacks
from callbacks.network_callbacks import register_network_callbacks

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
GRAPH_DATA_PATH = "/Volumes/GDrive/MEA_work/combined_data/output/div5053/GraphData"  # Update with your GraphData path

# Scan GraphData folder
print("Scanning GraphData folder...")
data_info = scan_graph_data_folder(GRAPH_DATA_PATH)
print(f"Found {len(data_info['groups'])} groups, {sum(len(exps) for exps in data_info['experiments'].values())} experiments, and {len(data_info['lags'])} lag values")

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

# Create app layout
app.layout = create_layout(app)

# Register callbacks
register_neuronal_callbacks(app)
register_network_callbacks(app)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)