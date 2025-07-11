from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import numpy as np

# UTILS PACKAGE IMPORTS - No more circular imports
from utils import (
    process_metric,
    is_metric_available,
    get_metric_title,
    create_empty_plot,
    create_error_plot
)

from components.neuronal_activity import (
    create_half_violin_plot_by_group,
    create_half_violin_plot_by_age,
    analyze_burst_data_distribution
)

def register_neuronal_callbacks(app):
    """
    Register REFACTORED neuronal activity callbacks
    Now uses utils package directly - no circular imports
    """
    
    # =============================================================================
    # SHARED VISUALIZATION FUNCTION - No circular import
    # =============================================================================
    
    def create_neuronal_visualization_callback(processed_data, metric, comparison, title, groups, selected_divs):
        """
        Create neuronal visualization for callbacks
        This function is local to avoid circular imports
        """
        from utils.config import get_metric_field_name
        
        # Get the field name to use in the data
        field_name = get_metric_field_name(metric)
        
        # Route to appropriate visualization function
        if comparison in ['nodebygroup', 'recordingsbygroup']:
            return create_half_violin_plot_by_group(processed_data, field_name, title, groups, selected_divs)
        elif comparison in ['nodebyage', 'recordingsbyage']:
            return create_half_violin_plot_by_age(processed_data, field_name, title, groups, selected_divs)
        else:
            return create_error_plot(f"Unknown comparison type: {comparison}")
    
    # =============================================================================
    # TAB SWITCHING CALLBACKS - UI State Management Only
    # =============================================================================
    
    @app.callback(
        [Output("neuronal-node-group-dropdown", "style"),
         Output("neuronal-node-age-dropdown", "style"), 
         Output("neuronal-recording-group-dropdown", "style"),
         Output("neuronal-recording-age-dropdown", "style")],
        [Input("neuronal-tabs", "value")]
    )
    def toggle_metric_dropdowns(selected_tab):
        """Show/hide appropriate metric dropdown based on selected neuronal tab"""
        
        # Default style - hidden
        hidden_style = {'marginBottom': '15px', 'display': 'none'}
        visible_style = {'marginBottom': '15px', 'display': 'block'}
        
        if selected_tab == "nodebygroup":
            return visible_style, hidden_style, hidden_style, hidden_style
        elif selected_tab == "nodebyage":
            return hidden_style, visible_style, hidden_style, hidden_style  
        elif selected_tab == "recordingsbygroup":
            return hidden_style, hidden_style, visible_style, hidden_style
        elif selected_tab == "recordingsbyage":
            return hidden_style, hidden_style, hidden_style, visible_style
        else:
            return hidden_style, hidden_style, hidden_style, hidden_style
    
    @app.callback(
        [Output("neuronal-node-group-container", "style"),
         Output("neuronal-node-age-container", "style"),
         Output("neuronal-recording-group-container", "style"), 
         Output("neuronal-recording-age-container", "style")],
        [Input("neuronal-tabs", "value")]
    )
    def toggle_plot_containers(selected_tab):
        """Show/hide appropriate plot container based on selected neuronal tab"""
        
        # Default style - hidden
        hidden_style = {'display': 'none'}
        visible_style = {'display': 'block'}
        
        if selected_tab == "nodebygroup":
            return visible_style, hidden_style, hidden_style, hidden_style
        elif selected_tab == "nodebyage":
            return hidden_style, visible_style, hidden_style, hidden_style
        elif selected_tab == "recordingsbygroup":
            return hidden_style, hidden_style, visible_style, hidden_style
        elif selected_tab == "recordingsbyage":
            return hidden_style, hidden_style, hidden_style, visible_style
        else:
            return hidden_style, hidden_style, hidden_style, hidden_style

    # =============================================================================
    # INDIVIDUAL PLOT CALLBACKS - Now using utils package
    # =============================================================================
    
    @app.callback(
        Output("neuronal-node-group-plot", "figure"),
        [Input("neuronal-node-group-metric", "value"),
         Input("neuronal-plot-type", "value"),
         Input("group-dropdown", "value"),
         Input("div-dropdown", "value"),
         Input("data-loaded-store", "data")]
    )
    def update_neuronal_node_group_plot(metric, plot_type, groups, selected_divs, data_loaded):
        """Update node-by-group plot - now uses utils package"""
        
        if not data_loaded or not app.data.get('loaded') or not metric or not groups:
            return create_empty_plot("Please load data and select metric")
        
        try:
            # Check if we have a processor for this metric
            if not is_metric_available(metric):
                return create_error_plot(f'Metric "{metric}" not yet implemented')
            
            # Process the data using utils package
            processed_data = process_metric(metric, app.data['neuronal'], groups, selected_divs)

            # ADD DIAGNOSTIC FOR BURST METRICS
            if metric in ['channelBurstRate', 'channelFRinBurst', 'channelBurstDur']:
                analyze_burst_data_distribution(app.data['neuronal'], metric)

            # Create title using utils
            metric_title = get_metric_title(metric)
            title = f"{metric_title} by Group"
            
            # Create the visualization
            return create_neuronal_visualization_callback(processed_data, metric, 'nodebygroup', title, groups, selected_divs)
            
        except Exception as e:
            print(f"❌ Error in node-by-group plot: {e}")
            return create_error_plot(f'Error: {str(e)}')

    @app.callback(
        Output("neuronal-node-age-plot", "figure"),
        [Input("neuronal-node-age-metric", "value"),
         Input("neuronal-plot-type", "value"),
         Input("group-dropdown", "value"),
         Input("div-dropdown", "value"),
         Input("data-loaded-store", "data")]
    )
    def update_neuronal_node_age_plot(metric, plot_type, groups, selected_divs, data_loaded):
        """Update node-by-age plot - now uses utils package"""
        
        if not data_loaded or not app.data.get('loaded') or not metric or not groups:
            return create_empty_plot("Please load data and select metric")
        
        try:
            # Check if we have a processor for this metric
            if not is_metric_available(metric):
                return create_error_plot(f'Metric "{metric}" not yet implemented')
            
            # Process the data using utils package
            processed_data = process_metric(metric, app.data['neuronal'], groups, selected_divs)

            # ADD DIAGNOSTIC FOR BURST METRICS
            if metric in ['channelBurstRate', 'channelFRinBurst', 'channelBurstDur']:
                analyze_burst_data_distribution(app.data['neuronal'], metric)

            # Create title using utils
            metric_title = get_metric_title(metric)
            title = f"{metric_title} by Age"
            
            # Create the visualization
            return create_neuronal_visualization_callback(processed_data, metric, 'nodebyage', title, groups, selected_divs)
            
        except Exception as e:
            print(f"❌ Error in node-by-age plot: {e}")
            return create_error_plot(f'Error: {str(e)}')

    @app.callback(
        Output("neuronal-recording-group-plot", "figure"),
        [Input("neuronal-recording-group-metric", "value"),
         Input("neuronal-plot-type", "value"),
         Input("group-dropdown", "value"),
         Input("div-dropdown", "value"),
         Input("data-loaded-store", "data")]
    )
    def update_neuronal_recording_group_plot(metric, plot_type, groups, selected_divs, data_loaded):
        """Update recording-by-group plot - now uses utils package"""
        
        if not data_loaded or not app.data.get('loaded') or not metric or not groups:
            return create_empty_plot("Please load data and select metric")
        
        try:
            # Check if we have a processor for this metric
            if not is_metric_available(metric):
                return create_error_plot(f'Metric "{metric}" not yet implemented')
            
            # Process the data using utils package
            processed_data = process_metric(metric, app.data['neuronal'], groups, selected_divs)

            if metric in ['channelBurstRate', 'channelFRinBurst', 'channelBurstDur']:
                from components.neuronal_activity import analyze_burst_data_distribution
                analyze_burst_data_distribution(app.data['neuronal'], metric)

            # Create title using utils
            metric_title = get_metric_title(metric)
            title = f"{metric_title} by Group"
            
            # Create the visualization
            return create_neuronal_visualization_callback(processed_data, metric, 'recordingsbygroup', title, groups, selected_divs)
            
        except Exception as e:
            print(f"❌ Error in recording-by-group plot: {e}")
            return create_error_plot(f'Error: {str(e)}')

    @app.callback(
        Output("neuronal-recording-age-plot", "figure"),
        [Input("neuronal-recording-age-metric", "value"),
         Input("neuronal-plot-type", "value"),
         Input("group-dropdown", "value"),
         Input("div-dropdown", "value"),
         Input("data-loaded-store", "data")]
    )
    def update_neuronal_recording_age_plot(metric, plot_type, groups, selected_divs, data_loaded):
        """Update recording-by-age plot - now uses utils package"""
        
        if not data_loaded or not app.data.get('loaded') or not metric or not groups:
            return create_empty_plot("Please load data and select metric")
        
        try:
            # Check if we have a processor for this metric
            if not is_metric_available(metric):
                return create_error_plot(f'Metric "{metric}" not yet implemented')
            
            # Process the data using utils package
            processed_data = process_metric(metric, app.data['neuronal'], groups, selected_divs)

            # ADD DIAGNOSTIC FOR BURST METRICS
            if metric in ['channelBurstRate', 'channelFRinBurst', 'channelBurstDur']:
                analyze_burst_data_distribution(app.data['neuronal'], metric)

            # Create title using utils
            metric_title = get_metric_title(metric)
            title = f"{metric_title} by Age"
            
            # Create the visualization
            return create_neuronal_visualization_callback(processed_data, metric, 'recordingsbyage', title, groups, selected_divs)
            
        except Exception as e:
            print(f"❌ Error in recording-by-age plot: {e}")
            return create_error_plot(f'Error: {str(e)}')

    print("✅ Refactored neuronal callbacks registered successfully!")

# =============================================================================
# REMOVED UTILITY FUNCTIONS - Now in utils package
# =============================================================================

# All utility functions like calculate_active_electrodes_from_data have been
# moved to the utils package (utils/data_helpers.py) to avoid duplication
# and maintain a single source of truth for data processing functions.