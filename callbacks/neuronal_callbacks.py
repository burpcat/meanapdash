# components/neuronal_callbacks.py - REFACTORED VERSION WITH Y-AXIS CONTROLS
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
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
    analyze_burst_data_distribution,
    create_recording_level_violin_plot_by_group,
    create_recording_level_violin_plot_by_age,
    create_half_violin_plot_by_age_recording_level,
    create_half_violin_plot_by_group_recording_level,
    create_box_plot_by_group,
    create_bar_plot_by_group,
    create_box_plot_by_age,
    create_bar_plot_by_age,
    create_box_plot_by_group_recording_level,
    create_bar_plot_by_group_recording_level,
    create_box_plot_by_age_recording_level,
    create_bar_plot_by_age_recording_level
)

def register_neuronal_callbacks(app):
    """
    Register REFACTORED neuronal activity callbacks with Y-AXIS support
    Now uses utils package directly - no circular imports
    """
    
    # =============================================================================
    # SHARED VISUALIZATION FUNCTION WITH Y-AXIS SUPPORT
    # =============================================================================
    
    def create_neuronal_visualization_callback(processed_data, metric, comparison, title, groups, selected_divs, 
                                         plot_type='violin', y_range_mode='auto', y_min=None, y_max=None):
        """
        UPDATED: Create neuronal visualization with PLOT TYPE ROUTING and Y-axis support
        """
        from utils.config import get_metric_field_name
        
        # Get the field name to use in the data
        field_name = get_metric_field_name(metric)
        
        # Route to appropriate visualization function based on COMPARISON + PLOT TYPE
        if comparison == 'nodebygroup':
            if plot_type == 'violin':
                return create_half_violin_plot_by_group(processed_data, field_name, title, groups, selected_divs,
                                                    y_range_mode=y_range_mode, y_min=y_min, y_max=y_max)
            elif plot_type == 'box':
                return create_box_plot_by_group(processed_data, field_name, title, groups, selected_divs,
                                            y_range_mode=y_range_mode, y_min=y_min, y_max=y_max)
            elif plot_type == 'bar':
                return create_bar_plot_by_group(processed_data, field_name, title, groups, selected_divs,
                                            y_range_mode=y_range_mode, y_min=y_min, y_max=y_max)
                
        elif comparison == 'nodebyage':
            if plot_type == 'violin':
                return create_half_violin_plot_by_age(processed_data, field_name, title, groups, selected_divs,
                                                    y_range_mode=y_range_mode, y_min=y_min, y_max=y_max)
            elif plot_type == 'box':
                return create_box_plot_by_age(processed_data, field_name, title, groups, selected_divs,
                                            y_range_mode=y_range_mode, y_min=y_min, y_max=y_max)
            elif plot_type == 'bar':
                return create_bar_plot_by_age(processed_data, field_name, title, groups, selected_divs,
                                            y_range_mode=y_range_mode, y_min=y_min, y_max=y_max)
                
        elif comparison == 'recordingsbygroup':
            if plot_type == 'violin':
                return create_half_violin_plot_by_group_recording_level(processed_data, field_name, title, groups, selected_divs,
                                                                    y_range_mode=y_range_mode, y_min=y_min, y_max=y_max)
            elif plot_type == 'box':
                return create_box_plot_by_group_recording_level(processed_data, field_name, title, groups, selected_divs,
                                                            y_range_mode=y_range_mode, y_min=y_min, y_max=y_max)
            elif plot_type == 'bar':
                return create_bar_plot_by_group_recording_level(processed_data, field_name, title, groups, selected_divs,
                                                            y_range_mode=y_range_mode, y_min=y_min, y_max=y_max)
                
        elif comparison == 'recordingsbyage':
            if plot_type == 'violin':
                return create_half_violin_plot_by_age_recording_level(processed_data, field_name, title, groups, selected_divs,
                                                                    y_range_mode=y_range_mode, y_min=y_min, y_max=y_max)
            elif plot_type == 'box':
                return create_box_plot_by_age_recording_level(processed_data, field_name, title, groups, selected_divs,
                                                            y_range_mode=y_range_mode, y_min=y_min, y_max=y_max)
            elif plot_type == 'bar':
                return create_bar_plot_by_age_recording_level(processed_data, field_name, title, groups, selected_divs,
                                                            y_range_mode=y_range_mode, y_min=y_min, y_max=y_max)
        
        # Fallback for unknown combination
        return create_error_plot(f"Unknown comparison/plot type: {comparison}/{plot_type}")
    
    # =============================================================================
    # Y-AXIS CONTROL CALLBACKS - NEW ADDITIONS
    # =============================================================================
    
    @app.callback(
        Output("manual-y-controls", "style"),
        [Input("y-axis-mode", "value")]
    )
    def toggle_manual_y_controls(mode):
        """Show/hide manual Y-axis controls based on mode selection"""
        if mode == 'manual':
            return {'display': 'block'}
        else:
            return {'display': 'none'}

    @app.callback(
        [Output("y-min-input", "value"),
         Output("y-max-input", "value")],
        [Input("preset-0-1", "n_clicks"),
         Input("preset-0-10", "n_clicks"), 
         Input("preset-0-100", "n_clicks"),
         Input("preset-reset", "n_clicks")],
        prevent_initial_call=True
    )
    def handle_y_axis_presets(preset_0_1, preset_0_10, preset_0_100, preset_reset):
        """Handle Y-axis preset button clicks"""
        from dash import callback_context
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == "preset-0-1":
            return 0, 1
        elif button_id == "preset-0-10":
            return 0, 10
        elif button_id == "preset-0-100":
            return 0, 100
        elif button_id == "preset-reset":
            return 0, 10
        raise PreventUpdate

    @app.callback(
        [Output("y-min-input", "style"),
         Output("y-max-input", "style")],
        [Input("y-min-input", "value"),
         Input("y-max-input", "value")]
    )
    def validate_y_axis_inputs(y_min, y_max):
        """Validate Y-axis inputs and provide visual feedback"""
        min_style = {'width': '100%', 'marginBottom': '5px'}
        max_style = {'width': '100%', 'marginBottom': '5px'}
        
        if y_min is not None and y_max is not None:
            if y_min >= y_max:
                min_style['borderColor'] = 'red'
                max_style['borderColor'] = 'red'
            else:
                min_style['borderColor'] = 'green'
                max_style['borderColor'] = 'green'
        
        return min_style, max_style
    
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
    # INDIVIDUAL PLOT CALLBACKS WITH Y-AXIS SUPPORT - Updated versions
    # =============================================================================
    
    @app.callback(
    Output("neuronal-node-group-plot", "figure"),
    [Input("neuronal-node-group-metric", "value"),
     Input("plot-type-selector", "value"),  # CHANGED from "neuronal-plot-type"
     Input("group-dropdown", "value"),
     Input("div-dropdown", "value"),
     Input("data-loaded-store", "data"),
     Input("y-axis-mode", "value"),
     Input("y-min-input", "value"),
     Input("y-max-input", "value")]
)
    def update_neuronal_node_group_plot(metric, plot_type, groups, selected_divs, data_loaded, 
                                       y_axis_mode, y_min, y_max):
        """Update node-by-group plot with Y-axis controls"""
        
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
            
            # Create the visualization with Y-axis parameters        
            return create_neuronal_visualization_callback(processed_data, metric, 'nodebygroup', title, groups, selected_divs,
                                                 plot_type=plot_type, y_range_mode=y_axis_mode, y_min=y_min, y_max=y_max)
            
        except Exception as e:
            print(f"❌ Error in node-by-group plot: {e}")
            return create_error_plot(f'Error: {str(e)}')

    @app.callback(
        Output("neuronal-node-age-plot", "figure"),
        [Input("neuronal-node-age-metric", "value"),
         Input("plot-type-selector", "value"),
         Input("group-dropdown", "value"),
         Input("div-dropdown", "value"),
         Input("data-loaded-store", "data"),
         # NEW Y-AXIS INPUTS:
         Input("y-axis-mode", "value"),
         Input("y-min-input", "value"),
         Input("y-max-input", "value")]
    )
    def update_neuronal_node_age_plot(metric, plot_type, groups, selected_divs, data_loaded, 
                                     y_axis_mode, y_min, y_max):
        """Update node-by-age plot with Y-axis controls"""
        
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
            
            # Create the visualization with Y-axis parameters
            return create_neuronal_visualization_callback(processed_data, metric, 'nodebyage', title, groups, selected_divs,plot_type=plot_type,
                                                         y_range_mode=y_axis_mode, y_min=y_min, y_max=y_max)
            
        except Exception as e:
            print(f"❌ Error in node-by-age plot: {e}")
            return create_error_plot(f'Error: {str(e)}')

    @app.callback(
        Output("neuronal-recording-group-plot", "figure"),
        [Input("neuronal-recording-group-metric", "value"),
         Input("group-dropdown", "value"),
         Input("div-dropdown", "value"),
         Input("plot-type-selector", "value"),
         Input("data-loaded-store", "data"),
         # NEW Y-AXIS INPUTS:
         Input("y-axis-mode", "value"),
         Input("y-min-input", "value"),
         Input("y-max-input", "value")]
    )
    def update_neuronal_recording_group_plot(metric, groups, selected_divs, plot_type, data_loaded, 
                                           y_axis_mode, y_min, y_max):
        """Update recording-by-group plot with Y-axis controls"""
        
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
            
            # Create the visualization with Y-axis parameters
            return create_neuronal_visualization_callback(processed_data, metric, 'recordingsbygroup', title, groups, selected_divs,plot_type=plot_type,
                                                         y_range_mode=y_axis_mode, y_min=y_min, y_max=y_max)
            
        except Exception as e:
            print(f"❌ Error in recording-by-group plot: {e}")
            return create_error_plot(f'Error: {str(e)}')

    @app.callback(
        Output("neuronal-recording-age-plot", "figure"),
        [Input("neuronal-recording-age-metric", "value"),
         Input("group-dropdown", "value"),
         Input("div-dropdown", "value"),
         Input("plot-type-selector", "value"),
         Input("data-loaded-store", "data"),
         # NEW Y-AXIS INPUTS:
         Input("y-axis-mode", "value"),
         Input("y-min-input", "value"),
         Input("y-max-input", "value")]
    )
    def update_neuronal_recording_age_plot(metric, groups, selected_divs, plot_type, data_loaded, 
                                         y_axis_mode, y_min, y_max):
        """Update recording-by-age plot with Y-axis controls"""
        
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
            
            # Create the visualization with Y-axis parameters
            return create_neuronal_visualization_callback(processed_data, metric, 'recordingsbyage', title, groups, selected_divs,plot_type=plot_type,
                                                         y_range_mode=y_axis_mode, y_min=y_min, y_max=y_max)
            
        except Exception as e:
            print(f"❌ Error in recording-by-age plot: {e}")
            return create_error_plot(f'Error: {str(e)}')

    print("✅ Refactored neuronal callbacks with Y-axis support registered successfully!")

# =============================================================================
# REMOVED UTILITY FUNCTIONS - Now in utils package
# =============================================================================

# All utility functions like calculate_active_electrodes_from_data have been
# moved to the utils package (utils/data_helpers.py) to avoid duplication
# and maintain a single source of truth for data processing functions.