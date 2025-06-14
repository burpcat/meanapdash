# # components/neuronal_activity.py
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# import numpy as np
# from data_processing.utilities import calculate_half_violin_data, extract_div_value

# def create_half_violin_plot_by_group(data, metric, title, selected_groups=None, selected_divs=None):
#     """
#     Create a half violin plot with individual data points, grouped by experimental condition
#     """
#     print(f"\nDEBUG: Creating half violin plot by group for metric: {metric}")
#     print(f"Selected groups: {selected_groups}")
#     print(f"Selected DIVs: {selected_divs}")
    
#     # FILTER: Use only selected groups, or all if none selected
#     if selected_groups:
#         groups = [g for g in selected_groups if g in data['groups']]
#     else:
#         groups = data['groups']
    
#     # FILTER: Use only selected DIVs, or all if none selected  
#     if selected_divs:
#         divs = [d for d in selected_divs if d in data['divs']]
#     else:
#         divs = sorted(data['divs'])
    
#     print(f"Filtered to groups: {groups}")
#     print(f"Filtered to DIVs: {divs}")
    
#     if not groups:
#         return go.Figure().update_layout(title="No groups selected or available")
    
#     # Create figure with subplots for each SELECTED group only
#     fig = make_subplots(rows=1, cols=len(groups), 
#                         subplot_titles=[g for g in groups],
#                         shared_yaxes=True)
    
#     # Color palette
#     colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
#     fill_colors = ['rgba(31, 119, 180, 0.5)', 'rgba(255, 127, 14, 0.5)', 'rgba(44, 160, 44, 0.5)', 
#                    'rgba(214, 39, 40, 0.5)', 'rgba(148, 103, 189, 0.5)', 'rgba(140, 86, 75, 0.5)', 
#                    'rgba(227, 119, 194, 0.5)', 'rgba(127, 127, 127, 0.5)']
    
#     max_y = 0
    
#     # Process only SELECTED groups
#     for col, group in enumerate(groups, 1):
#         if group not in data['by_group']:
#             continue
            
#         group_data = data['by_group'][group]
#         if metric not in group_data:
#             continue
            
#         is_recording_metric = metric in ['FRmean', 'FRmedian', 'numActiveElec', 'NBurstRate', 
#                                 'meanNumChansInvolvedInNbursts', 'meanNBstLengthS',
#                                 'meanISIWithinNbursts_ms', 'meanISIoutsideNbursts_ms',
#                                 'CVofINBI', 'fracInNburst']
        
#         # Process only SELECTED DIVs
#         for div_idx, div in enumerate(divs):
#             div_data = []
    
#             if is_recording_metric:
#                 exp_indices = []
#                 for i, exp_name in enumerate(group_data['exp_names']):
#                     div_parts = [part for part in exp_name.split('_') if 'DIV' in part]
#                     if div_parts and extract_div_value(div_parts[0]) == div:
#                         exp_indices.append(i)
                
#                 if exp_indices and len(group_data[metric]) >= max(exp_indices) + 1:
#                     div_data = [group_data[metric][i] for i in exp_indices if i < len(group_data[metric])]
#                     flat_data = []
#                     for item in div_data:
#                         if isinstance(item, (list, np.ndarray)):
#                             flat_data.extend(item)
#                         else:
#                             flat_data.append(item)
#                     div_data = flat_data
            
#             # Node-level metrics
#             for exp_idx, exp_name in enumerate(group_data['exp_names']):
#                 if any(f'DIV{div}' in exp_name for div_part in exp_name.split('_')):
#                     exp_data = data['by_experiment'].get(exp_name, {})
#                     if 'activity' in exp_data and metric in exp_data['activity']:
#                         div_data.extend(exp_data['activity'][metric])
            
#             if not div_data:
#                 continue
                
#             # Calculate KDE data
#             kde_data = calculate_half_violin_data(div_data)
#             max_y = max(max_y, max(kde_data['raw_data']) if kde_data['raw_data'].size > 0 else 0)
            
#             # Plot styling
#             x_base = div_idx + 1
#             color = colors[div_idx % len(colors)]
#             fill_color = fill_colors[div_idx % len(fill_colors)]
            
#             # Add scatter points
#             jitter = np.random.normal(0, 0.05, size=len(kde_data['raw_data']))
#             fig.add_trace(
#                 go.Scatter(
#                     x=[x_base + j for j in jitter],
#                     y=kde_data['raw_data'],
#                     mode='markers',
#                     marker=dict(color=color, size=5, opacity=0.7),
#                     name=f'DIV {div}',
#                     legendgroup=f'DIV {div}',
#                     showlegend=(col == 1)
#                 ),
#                 row=1, col=col
#             )
            
#             # Add violin
#             fig.add_trace(
#                 go.Violin(
#                     x=[x_base] * len(kde_data['x']),
#                     y=kde_data['x'],
#                     width=0.8,
#                     side='positive',
#                     line_color=color,
#                     fillcolor=fill_color,
#                     points=False,
#                     meanline_visible=False,
#                     opacity=0.5,
#                     showlegend=False
#                 ),
#                 row=1, col=col
#             )
            
#             # Add mean line and error bars
#             fig.add_trace(
#                 go.Scatter(
#                     x=[x_base - 0.3, x_base + 0.3],
#                     y=[kde_data['mean'], kde_data['mean']],
#                     mode='lines',
#                     line=dict(color='black', width=2),
#                     showlegend=False
#                 ),
#                 row=1, col=col
#             )
            
#             fig.add_trace(
#                 go.Scatter(
#                     x=[x_base, x_base],
#                     y=[kde_data['mean'] - kde_data['sem'], kde_data['mean'] + kde_data['sem']],
#                     mode='lines',
#                     line=dict(color='black', width=1),
#                     showlegend=False
#                 ),
#                 row=1, col=col
#             )
    
#     # Update layout
#     fig.update_layout(
#         title=title,
#         height=600,
#         margin=dict(l=50, r=50, t=80, b=50),
#         legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
#     )
    
#     # Update axes
#     for col in range(1, len(groups) + 1):
#         fig.update_xaxes(
#             tickvals=list(range(1, len(divs) + 1)),
#             ticktext=[f'DIV {div}' for div in divs],
#             row=1, col=col
#         )
    
#     metric_labels = {
#         'FR': 'Firing Rate (Hz)',
#         'channelBurstRate': 'Burst Rate (per minute)',
#         'channelBurstDur': 'Burst Duration (ms)',
#         'channelISIwithinBurst': 'ISI Within Burst (ms)',
#         'channeISIoutsideBurst': 'ISI Outside Burst (ms)',
#         'channelFracSpikesInBursts': 'Fraction Spikes in Bursts'
#     }
    
#     fig.update_yaxes(
#         title_text=metric_labels.get(metric, metric),
#         range=[0, max_y * 1.1]
#     )
    
#     return fig

# def create_half_violin_plot_by_age(data, metric, title, selected_groups=None, selected_divs=None):
#     """
#     Create a half violin plot with individual data points, grouped by age/DIV
#     """
#     print(f"\nDEBUG: Creating half violin plot by age for metric: {metric}")
#     print(f"Selected groups: {selected_groups}")
#     print(f"Selected DIVs: {selected_divs}")
    
#     # FILTER: Use only selected DIVs
#     if selected_divs:
#         divs = [d for d in selected_divs if d in data['divs']]
#     else:
#         divs = sorted(data['divs'])
    
#     # FILTER: Use only selected groups  
#     if selected_groups:
#         groups = [g for g in selected_groups if g in data['groups']]
#     else:
#         groups = data['groups']
    
#     print(f"Filtered to DIVs: {divs}")
#     print(f"Filtered to groups: {groups}")
    
#     if not divs:
#         return go.Figure().update_layout(title="No DIVs selected or available")
    
#     # Create figure with subplots for each SELECTED DIV only
#     fig = make_subplots(rows=1, cols=len(divs), 
#                         subplot_titles=[f'DIV {div}' for div in divs],
#                         shared_yaxes=True)
    
#     # FIXED: Group-specific colors so you can tell cell lines apart
#     group_colors = {}
#     group_fill_colors = {}
#     colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
#     fill_colors = ['rgba(31, 119, 180, 0.5)', 'rgba(255, 127, 14, 0.5)', 'rgba(44, 160, 44, 0.5)', 
#                    'rgba(214, 39, 40, 0.5)', 'rgba(148, 103, 189, 0.5)', 'rgba(140, 86, 75, 0.5)', 
#                    'rgba(227, 119, 194, 0.5)', 'rgba(127, 127, 127, 0.5)']
    
#     for i, group in enumerate(groups):
#         group_colors[group] = colors[i % len(colors)]
#         group_fill_colors[group] = fill_colors[i % len(fill_colors)]
    
#     max_y = 0
    
#     # Process only SELECTED DIVs
#     for col, div in enumerate(divs, 1):
#         if div not in data['by_div']:
#             continue
            
#         div_data = data['by_div'][div]
#         if metric not in div_data:
#             continue
        
#         # Get all values for this DIV
#         metric_values = div_data[metric]
#         if isinstance(metric_values, np.ndarray):
#             metric_values = metric_values.tolist()
#         elif not isinstance(metric_values, list):
#             metric_values = [metric_values]
            
#         # FIXED: Group the data by cell line so we can color-code them
#         group_data_for_div = {}
        
#         # Try to extract group information for each data point
#         if 'groups' in div_data and len(div_data['groups']) == len(metric_values):
#             # We have group info for each data point
#             for i, group in enumerate(div_data['groups']):
#                 if group in groups:  # Only include selected groups
#                     if group not in group_data_for_div:
#                         group_data_for_div[group] = []
                    
#                     val = metric_values[i]
#                     if isinstance(val, (list, np.ndarray)):
#                         if len(val) > 0:
#                             group_data_for_div[group].append(float(np.mean(val)))
#                     elif val is not None and not np.isnan(val):
#                         group_data_for_div[group].append(float(val))
#         else:
#             # No group info available, treat as single group
#             flat_values = []
#             for val in metric_values:
#                 if isinstance(val, (list, np.ndarray)):
#                     if len(val) > 0:
#                         flat_values.append(float(np.mean(val)))
#                 elif val is not None and not np.isnan(val):
#                     flat_values.append(float(val))
            
#             if flat_values:
#                 group_data_for_div['All Groups'] = flat_values
#                 if 'All Groups' not in group_colors:
#                     group_colors['All Groups'] = colors[0]
#                     group_fill_colors['All Groups'] = fill_colors[0]
        
#         # Plot each group separately with different colors
#         x_offset = 0
#         for group_name, group_values in group_data_for_div.items():
#             if not group_values:
#                 continue
                
#             # Calculate KDE data
#             kde_data = calculate_half_violin_data(group_values)
#             max_y = max(max_y, max(kde_data['raw_data']) if kde_data['raw_data'].size > 0 else 0)
            
#             x_base = 1 + x_offset
#             color = group_colors[group_name]
#             fill_color = group_fill_colors[group_name]
            
#             # Add scatter points
#             jitter = np.random.normal(0, 0.05, size=len(kde_data['raw_data']))
#             fig.add_trace(
#                 go.Scatter(
#                     x=[x_base + j for j in jitter],
#                     y=kde_data['raw_data'],
#                     mode='markers',
#                     marker=dict(color=color, size=5, opacity=0.7),
#                     name=group_name,
#                     showlegend=(col == 1),  # Only show legend for first subplot
#                     hovertemplate=f'{group_name}<br>Value: %{{y:.3f}}<extra></extra>'
#                 ),
#                 row=1, col=col
#             )
            
#             # Add violin
#             fig.add_trace(
#                 go.Violin(
#                     x=[x_base] * len(kde_data['x']),
#                     y=kde_data['x'],
#                     width=0.6,
#                     side='positive',
#                     line_color=color,
#                     fillcolor=fill_color,
#                     points=False,
#                     meanline_visible=False,
#                     opacity=0.5,
#                     showlegend=False
#                 ),
#                 row=1, col=col
#             )
            
#             # Add mean line and error bars
#             fig.add_trace(
#                 go.Scatter(
#                     x=[x_base - 0.3, x_base + 0.3],
#                     y=[kde_data['mean'], kde_data['mean']],
#                     mode='lines',
#                     line=dict(color='black', width=2),
#                     showlegend=False
#                 ),
#                 row=1, col=col
#             )
            
#             fig.add_trace(
#                 go.Scatter(
#                     x=[x_base, x_base],
#                     y=[kde_data['mean'] - kde_data['sem'], kde_data['mean'] + kde_data['sem']],
#                     mode='lines',
#                     line=dict(color='black', width=1),
#                     showlegend=False
#                 ),
#                 row=1, col=col
#             )
            
#             x_offset += 0.5  # Offset for multiple groups within same DIV
    
#     # Update layout
#     fig.update_layout(
#         title=title,
#         height=600,
#         margin=dict(l=50, r=50, t=80, b=50),
#         legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
#         showlegend=True
#     )
    
#     # Update axes
#     for col in range(1, len(divs) + 1):
#         fig.update_xaxes(
#             tickvals=[1],
#             ticktext=["Groups"],
#             row=1, col=col
#         )
    
#     metric_labels = {
#         'FRmean': 'Mean Firing Rate (Hz)',
#         'FRmedian': 'Median Firing Rate (Hz)',
#         'numActiveElec': 'Number of Active Electrodes',
#         'NBurstRate': 'Network Burst Rate (per minute)',
#         'meanNBstLengthS': 'Mean Network Burst Length (s)',
#         'meanISIWithinNbursts_ms': 'Mean ISI Within Network Bursts (ms)',
#         'meanISIoutsideNbursts_ms': 'Mean ISI Outside Network Bursts (ms)',
#         'meanNumChansInvolvedInNbursts': 'Mean Channels in Network Bursts',
#         'CVofINBI': 'CV of Inter-Network Burst Intervals'
#     }
    
#     fig.update_yaxes(
#         title_text=metric_labels.get(metric, metric),
#         range=[0, max_y * 1.1] if max_y > 0 else None
#     )
    
#     return fig

# data rich export
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from data_processing.utilities import calculate_half_violin_data, extract_div_value
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

def calculate_detailed_stats(data):
    """Calculate comprehensive statistics for data interpretation"""
    data = np.array(data)
    n = len(data)
    
    if n == 0:
        return None
    
    stats_dict = {
        'n': n,
        'mean': np.mean(data),
        'median': np.median(data),
        'std': np.std(data, ddof=1) if n > 1 else 0,
        'sem': np.std(data, ddof=1) / np.sqrt(n) if n > 1 else 0,
        'q25': np.percentile(data, 25),
        'q75': np.percentile(data, 75),
        'min': np.min(data),
        'max': np.max(data),
        'cv': (np.std(data, ddof=1) / np.mean(data) * 100) if np.mean(data) != 0 and n > 1 else 0
    }
    
    # 95% Confidence interval for mean
    if n > 1:
        ci = stats.t.interval(0.95, n-1, loc=stats_dict['mean'], scale=stats_dict['sem'])
        stats_dict['ci_lower'] = ci[0]
        stats_dict['ci_upper'] = ci[1]
    else:
        stats_dict['ci_lower'] = stats_dict['mean']
        stats_dict['ci_upper'] = stats_dict['mean']
    
    # Outlier detection (IQR method)
    if n > 4:
        iqr = stats_dict['q75'] - stats_dict['q25']
        outlier_threshold_lower = stats_dict['q25'] - 1.5 * iqr
        outlier_threshold_upper = stats_dict['q75'] + 1.5 * iqr
        outliers = data[(data < outlier_threshold_lower) | (data > outlier_threshold_upper)]
        stats_dict['n_outliers'] = len(outliers)
        stats_dict['outliers'] = outliers.tolist()
    else:
        stats_dict['n_outliers'] = 0
        stats_dict['outliers'] = []
    
    return stats_dict

def perform_statistical_test(group1_data, group2_data, group1_name, group2_name):
    """Perform appropriate statistical test between two groups"""
    if len(group1_data) < 3 or len(group2_data) < 3:
        return None
    
    try:
        # Test for normality (if n > 8)
        if len(group1_data) > 8 and len(group2_data) > 8:
            _, p1 = stats.shapiro(group1_data)
            _, p2 = stats.shapiro(group2_data)
            normal = (p1 > 0.05) and (p2 > 0.05)
        else:
            normal = True  # Assume normal for small samples
        
        # Choose appropriate test
        if normal:
            # t-test for normal data
            stat, p_value = stats.ttest_ind(group1_data, group2_data)
            test_name = "t-test"
        else:
            # Mann-Whitney U for non-normal data
            stat, p_value = stats.mannwhitneyu(group1_data, group2_data, alternative='two-sided')
            test_name = "Mann-Whitney U"
        
        # Effect size (Cohen's d)
        pooled_std = np.sqrt(((len(group1_data) - 1) * np.var(group1_data, ddof=1) + 
                             (len(group2_data) - 1) * np.var(group2_data, ddof=1)) / 
                            (len(group1_data) + len(group2_data) - 2))
        cohens_d = (np.mean(group1_data) - np.mean(group2_data)) / pooled_std if pooled_std > 0 else 0
        
        # Interpret effect size
        if abs(cohens_d) < 0.2:
            effect_size = "negligible"
        elif abs(cohens_d) < 0.5:
            effect_size = "small"
        elif abs(cohens_d) < 0.8:
            effect_size = "medium"
        else:
            effect_size = "large"
        
        return {
            'test_name': test_name,
            'p_value': p_value,
            'statistic': stat,
            'cohens_d': cohens_d,
            'effect_size': effect_size,
            'significant': p_value < 0.05,
            'comparison': f"{group1_name} vs {group2_name}"
        }
    except:
        return None

def create_half_violin_plot_by_group(data, metric, title, selected_groups=None, selected_divs=None):
    """
    Create a data-rich half violin plot with comprehensive statistics
    """
    print(f"\nDEBUG: Creating enhanced half violin plot by group for metric: {metric}")
    
    # Filter data
    if selected_groups:
        groups = [g for g in selected_groups if g in data['groups']]
    else:
        groups = data['groups']
    
    if selected_divs:
        divs = [d for d in selected_divs if d in data['divs']]
    else:
        divs = sorted(data['divs'])
    
    if not groups:
        return go.Figure().update_layout(title="No groups selected or available")
    
    # Create figure with more space for annotations
    fig = make_subplots(
        rows=1, cols=len(groups), 
        subplot_titles=[f'<b>{g}</b>' for g in groups],
        shared_yaxes=True,
        horizontal_spacing=0.12
    )
    
    # Enhanced color palette
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
    fill_colors = ['rgba(31, 119, 180, 0.3)', 'rgba(255, 127, 14, 0.3)', 'rgba(44, 160, 44, 0.3)', 
                   'rgba(214, 39, 40, 0.3)', 'rgba(148, 103, 189, 0.3)', 'rgba(140, 86, 75, 0.3)', 
                   'rgba(227, 119, 194, 0.3)', 'rgba(127, 127, 127, 0.3)']
    
    max_y = 0
    all_group_stats = {}  # Store stats for comparison
    
    # Process each group
    for col, group in enumerate(groups, 1):
        if group not in data['by_group']:
            continue
            
        group_data = data['by_group'][group]
        if metric not in group_data:
            continue
            
        is_recording_metric = metric in ['FRmean', 'FRmedian', 'numActiveElec', 'NBurstRate', 
                                'meanNumChansInvolvedInNbursts', 'meanNBstLengthS',
                                'meanISIWithinNbursts_ms', 'meanISIoutsideNbursts_ms',
                                'CVofINBI', 'fracInNburst']
        
        group_div_stats = {}
        
        # Process each DIV
        for div_idx, div in enumerate(divs):
            div_data = []
    
            if is_recording_metric:
                exp_indices = []
                for i, exp_name in enumerate(group_data['exp_names']):
                    div_parts = [part for part in exp_name.split('_') if 'DIV' in part]
                    if div_parts and extract_div_value(div_parts[0]) == div:
                        exp_indices.append(i)
                
                if exp_indices and len(group_data[metric]) >= max(exp_indices) + 1:
                    div_data = [group_data[metric][i] for i in exp_indices if i < len(group_data[metric])]
                    flat_data = []
                    for item in div_data:
                        if isinstance(item, (list, np.ndarray)):
                            flat_data.extend(item)
                        else:
                            flat_data.append(item)
                    div_data = flat_data
            
            # Node-level metrics
            for exp_idx, exp_name in enumerate(group_data['exp_names']):
                if any(f'DIV{div}' in exp_name for div_part in exp_name.split('_')):
                    exp_data = data['by_experiment'].get(exp_name, {})
                    if 'activity' in exp_data and metric in exp_data['activity']:
                        div_data.extend(exp_data['activity'][metric])
            
            if not div_data:
                continue
            
            # Calculate comprehensive statistics
            stats_info = calculate_detailed_stats(div_data)
            if not stats_info:
                continue
                
            group_div_stats[div] = {'data': div_data, 'stats': stats_info}
            
            # Calculate KDE data
            kde_data = calculate_half_violin_data(div_data)
            max_y = max(max_y, stats_info['max'])
            
            # Plot styling
            x_base = div_idx + 1
            color = colors[div_idx % len(colors)]
            fill_color = fill_colors[div_idx % len(fill_colors)]
            
            # Enhanced scatter points with outlier highlighting
            regular_data = [x for x in div_data if x not in stats_info['outliers']]
            outlier_data = stats_info['outliers']
            
            # Regular points
            if regular_data:
                jitter = np.random.normal(0, 0.04, size=len(regular_data))
                fig.add_trace(
                    go.Scatter(
                        x=[x_base + j for j in jitter],
                        y=regular_data,
                        mode='markers',
                        marker=dict(color=color, size=5, opacity=0.7),
                        name=f'DIV {div}',
                        legendgroup=f'DIV {div}',
                        showlegend=(col == 1),
                        hovertemplate=(
                            f'<b>DIV {div}</b><br>' +
                            f'Value: %{{y:.3f}}<br>' +
                            f'<i>n = {stats_info["n"]}</i>' +
                            '<extra></extra>'
                        )
                    ),
                    row=1, col=col
                )
            
            # Outlier points (highlighted)
            if outlier_data:
                jitter_out = np.random.normal(0, 0.04, size=len(outlier_data))
                fig.add_trace(
                    go.Scatter(
                        x=[x_base + j for j in jitter_out],
                        y=outlier_data,
                        mode='markers',
                        marker=dict(
                            color='red', 
                            size=6, 
                            opacity=0.8,
                            line=dict(width=1, color='darkred')
                        ),
                        name=f'DIV {div} Outliers',
                        legendgroup=f'DIV {div}',
                        showlegend=False,
                        hovertemplate=(
                            f'<b>DIV {div} - OUTLIER</b><br>' +
                            f'Value: %{{y:.3f}}<br>' +
                            f'<i>Outside 1.5×IQR</i>' +
                            '<extra></extra>'
                        )
                    ),
                    row=1, col=col
                )
            
            # Enhanced violin with better transparency
            fig.add_trace(
                go.Violin(
                    x=[x_base] * len(kde_data['x']),
                    y=kde_data['x'],
                    width=0.7,
                    side='positive',
                    line_color=color,
                    fillcolor=fill_color,
                    points=False,
                    meanline_visible=False,
                    showlegend=False,
                    hoverinfo='skip'
                ),
                row=1, col=col
            )
            
            # Mean line (thicker)
            fig.add_trace(
                go.Scatter(
                    x=[x_base - 0.25, x_base + 0.35],
                    y=[stats_info['mean'], stats_info['mean']],
                    mode='lines',
                    line=dict(color='black', width=3),
                    showlegend=False,
                    hovertemplate=f'Mean: {stats_info["mean"]:.3f}<extra></extra>'
                ),
                row=1, col=col
            )
            
            # Median line (different style)
            fig.add_trace(
                go.Scatter(
                    x=[x_base - 0.25, x_base + 0.35],
                    y=[stats_info['median'], stats_info['median']],
                    mode='lines',
                    line=dict(color='darkblue', width=2, dash='dash'),
                    showlegend=False,
                    hovertemplate=f'Median: {stats_info["median"]:.3f}<extra></extra>'
                ),
                row=1, col=col
            )
            
            # 95% Confidence interval
            fig.add_trace(
                go.Scatter(
                    x=[x_base + 0.4, x_base + 0.4],
                    y=[stats_info['ci_lower'], stats_info['ci_upper']],
                    mode='lines',
                    line=dict(color='red', width=3),
                    showlegend=False,
                    hovertemplate=f'95% CI: [{stats_info["ci_lower"]:.3f}, {stats_info["ci_upper"]:.3f}]<extra></extra>'
                ),
                row=1, col=col
            )
            
            # Sample size annotation - center
            fig.add_annotation(
                x=x_base,
                y=max_y * 0.95,
                text=f'<b>n={stats_info["n"]}</b>',
                showarrow=False,
                font=dict(size=10, color=color),
                row=1, col=col
            )
            
            # CV annotation (if meaningful)
            if stats_info['cv'] > 0:
                fig.add_annotation(
                    x=x_base,
                    y=max_y * 0.05,
                    text=f'CV: {stats_info["cv"]:.1f}%',
                    showarrow=False,
                    font=dict(size=8, color='gray'),
                    row=1, col=col
                )
        
        all_group_stats[group] = group_div_stats
    
    # Add statistical comparisons between DIVs within each group
    for col, group in enumerate(groups, 1):
        if group in all_group_stats and len(divs) == 2:
            div1, div2 = divs[0], divs[1]
            if div1 in all_group_stats[group] and div2 in all_group_stats[group]:
                data1 = all_group_stats[group][div1]['data']
                data2 = all_group_stats[group][div2]['data']
                
                test_result = perform_statistical_test(data1, data2, f'DIV {div1}', f'DIV {div2}')
                
                if test_result:
                    # Add significance annotation
                    y_pos = max_y * 0.85
                    
                    if test_result['significant']:
                        sig_text = '***' if test_result['p_value'] < 0.001 else ('**' if test_result['p_value'] < 0.01 else '*')
                        color_sig = 'red'
                    else:
                        sig_text = 'ns'
                        color_sig = 'gray'
                    
                    # Significance line and text
                    fig.add_shape(
                        type="line",
                        x0=1, y0=y_pos, x1=2, y1=y_pos,
                        line=dict(color=color_sig, width=1),
                        row=1, col=col
                    )
                    
                    fig.add_annotation(
                        x=1.5,
                        y=y_pos + max_y * 0.02,
                        text=f'<b>{sig_text}</b><br>p={test_result["p_value"]:.3f}<br>d={test_result["cohens_d"]:.2f}',
                        showarrow=False,
                        font=dict(size=9, color=color_sig),
                        row=1, col=col
                    )
    
    # Enhanced layout
    fig.update_layout(
        title=dict(
            text=f'<b>{title}</b><br><sub>Mean (solid), Median (dashed), 95% CI (red), Outliers (red dots)</sub>',
            x=0.5
        ),
        height=700,  # Taller for annotations
        margin=dict(l=60, r=60, t=120, b=80),
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1
        ),
        font=dict(size=11)
    )
    
    # Enhanced axes
    for col in range(1, len(groups) + 1):
        fig.update_xaxes(
            tickvals=list(range(1, len(divs) + 1)),
            ticktext=[f'<b>DIV {div}</b>' for div in divs],
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.2)',
            row=1, col=col
        )
    
    metric_labels = {
        'FR': 'Firing Rate (Hz)',
        'channelBurstRate': 'Burst Rate (per minute)',
        'channelBurstDur': 'Burst Duration (ms)',
        'channelISIwithinBurst': 'ISI Within Burst (ms)',
        'channeISIoutsideBurst': 'ISI Outside Burst (ms)',
        'channelFracSpikesInBursts': 'Fraction Spikes in Bursts',
        'FRmean': 'Mean Firing Rate (Hz)',
        'FRmedian': 'Median Firing Rate (Hz)',
        'numActiveElec': 'Number of Active Electrodes'
    }
    
    fig.update_yaxes(
        title_text=metric_labels.get(metric, metric),
        range=[0, max_y * 1.15],  # Extra space for annotations
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.2)'
    )
    
    return fig

def create_half_violin_plot_by_age(data, metric, title, selected_groups=None, selected_divs=None):
    """
    Create a data-rich half violin plot grouped by age/DIV with group comparisons
    """
    print(f"\nDEBUG: Creating enhanced half violin plot by age for metric: {metric}")
    
    # Filter data
    if selected_divs:
        divs = [d for d in selected_divs if d in data['divs']]
    else:
        divs = sorted(data['divs'])
    
    if selected_groups:
        groups = [g for g in selected_groups if g in data['groups']]
    else:
        groups = data['groups']
    
    if not divs:
        return go.Figure().update_layout(title="No DIVs selected or available")
    
    # Create figure
    fig = make_subplots(
        rows=1, cols=len(divs), 
        subplot_titles=[f'<b>DIV {div}</b>' for div in divs],
        shared_yaxes=True,
        horizontal_spacing=0.15
    )
    
    # Group-specific colors
    group_colors = {}
    group_fill_colors = {}
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
    fill_colors = ['rgba(31, 119, 180, 0.3)', 'rgba(255, 127, 14, 0.3)', 'rgba(44, 160, 44, 0.3)', 
                   'rgba(214, 39, 40, 0.3)', 'rgba(148, 103, 189, 0.3)', 'rgba(140, 86, 75, 0.3)', 
                   'rgba(227, 119, 194, 0.3)', 'rgba(127, 127, 127, 0.3)']
    
    for i, group in enumerate(groups):
        group_colors[group] = colors[i % len(colors)]
        group_fill_colors[group] = fill_colors[i % len(fill_colors)]
    
    max_y = 0
    all_div_stats = {}
    
    # Process each DIV
    for col, div in enumerate(divs, 1):
        if div not in data['by_div']:
            continue
            
        div_data = data['by_div'][div]
        if metric not in div_data:
            continue
        
        metric_values = div_data[metric]
        if isinstance(metric_values, np.ndarray):
            metric_values = metric_values.tolist()
        elif not isinstance(metric_values, list):
            metric_values = [metric_values]
            
        # Group the data by cell line
        group_data_for_div = {}
        
        if 'groups' in div_data and len(div_data['groups']) == len(metric_values):
            for i, group in enumerate(div_data['groups']):
                if group in groups:
                    if group not in group_data_for_div:
                        group_data_for_div[group] = []
                    
                    val = metric_values[i]
                    if isinstance(val, (list, np.ndarray)):
                        if len(val) > 0:
                            group_data_for_div[group].append(float(np.mean(val)))
                    elif val is not None and not np.isnan(val):
                        group_data_for_div[group].append(float(val))
        else:
            # Fallback
            flat_values = []
            for val in metric_values:
                if isinstance(val, (list, np.ndarray)):
                    if len(val) > 0:
                        flat_values.append(float(np.mean(val)))
                elif val is not None and not np.isnan(val):
                    flat_values.append(float(val))
            
            if flat_values:
                group_data_for_div['All Groups'] = flat_values
        
        div_group_stats = {}
        
        # Plot each group with enhanced statistics
        x_offset = 0
        for group_name, group_values in group_data_for_div.items():
            if not group_values:
                continue
            
            # Calculate comprehensive statistics
            stats_info = calculate_detailed_stats(group_values)
            if not stats_info:
                continue
            
            div_group_stats[group_name] = {'data': group_values, 'stats': stats_info}
                
            kde_data = calculate_half_violin_data(group_values)
            max_y = max(max_y, stats_info['max'])
            
            x_base = 1 + x_offset
            color = group_colors.get(group_name, colors[0])
            fill_color = group_fill_colors.get(group_name, fill_colors[0])
            
            # Enhanced scatter with outliers
            regular_data = [x for x in group_values if x not in stats_info['outliers']]
            outlier_data = stats_info['outliers']
            
            # Regular points
            if regular_data:
                jitter = np.random.normal(0, 0.04, size=len(regular_data))
                fig.add_trace(
                    go.Scatter(
                        x=[x_base + j for j in jitter],
                        y=regular_data,
                        mode='markers',
                        marker=dict(color=color, size=5, opacity=0.7),
                        name=group_name,
                        showlegend=(col == 1),
                        hovertemplate=(
                            f'<b>{group_name}</b><br>' +
                            f'Value: %{{y:.3f}}<br>' +
                            f'<i>n = {stats_info["n"]}</i><br>' +
                            f'Mean: {stats_info["mean"]:.3f}<br>' +
                            f'CV: {stats_info["cv"]:.1f}%' +
                            '<extra></extra>'
                        )
                    ),
                    row=1, col=col
                )
            
            # Outliers
            if outlier_data:
                jitter_out = np.random.normal(0, 0.04, size=len(outlier_data))
                fig.add_trace(
                    go.Scatter(
                        x=[x_base + j for j in jitter_out],
                        y=outlier_data,
                        mode='markers',
                        marker=dict(color='red', size=6, opacity=0.8, 
                                  line=dict(width=1, color='darkred')),
                        showlegend=False,
                        hovertemplate=f'<b>{group_name} - OUTLIER</b><br>Value: %{{y:.3f}}<extra></extra>'
                    ),
                    row=1, col=col
                )
            
            # Enhanced violin
            fig.add_trace(
                go.Violin(
                    x=[x_base] * len(kde_data['x']),
                    y=kde_data['x'],
                    width=0.5,
                    side='positive',
                    line_color=color,
                    fillcolor=fill_color,
                    points=False,
                    meanline_visible=False,
                    showlegend=False,
                    hoverinfo='skip'
                ),
                row=1, col=col
            )
            
            # Mean and median lines
            fig.add_trace(
                go.Scatter(
                    x=[x_base - 0.2, x_base + 0.25],
                    y=[stats_info['mean'], stats_info['mean']],
                    mode='lines',
                    line=dict(color='black', width=3),
                    showlegend=False,
                    hovertemplate=f'{group_name} Mean: {stats_info["mean"]:.3f}<extra></extra>'
                ),
                row=1, col=col
            )
            
            fig.add_trace(
                go.Scatter(
                    x=[x_base - 0.2, x_base + 0.25],
                    y=[stats_info['median'], stats_info['median']],
                    mode='lines',
                    line=dict(color='darkblue', width=2, dash='dash'),
                    showlegend=False,
                    hovertemplate=f'{group_name} Median: {stats_info["median"]:.3f}<extra></extra>'
                ),
                row=1, col=col
            )
            
            # Sample size and CV annotations
            fig.add_annotation(
                x=x_base,
                y=max_y * (0.9 - x_offset * 0.1),
                text=f'<b>n={stats_info["n"]}</b>',
                showarrow=False,
                font=dict(size=10, color=color),
                row=1, col=col
            )
            
            x_offset += 0.6
        
        all_div_stats[div] = div_group_stats
    
    # Add statistical comparisons between groups within each DIV
    for col, div in enumerate(divs, 1):
        if div in all_div_stats:
            group_names = list(all_div_stats[div].keys())
            if len(group_names) >= 2:
                # Compare first two groups
                group1, group2 = group_names[0], group_names[1]
                data1 = all_div_stats[div][group1]['data']
                data2 = all_div_stats[div][group2]['data']
                
                test_result = perform_statistical_test(data1, data2, group1, group2)
                
                if test_result:
                    y_pos = max_y * 0.85
                    
                    if test_result['significant']:
                        sig_text = '***' if test_result['p_value'] < 0.001 else ('**' if test_result['p_value'] < 0.01 else '*')
                        color_sig = 'red'
                    else:
                        sig_text = 'ns'
                        color_sig = 'gray'
                    
                    fig.add_annotation(
                        x=1.3,
                        y=y_pos,
                        text=f'<b>{sig_text}</b><br>p={test_result["p_value"]:.3f}<br>d={test_result["cohens_d"]:.2f}',
                        showarrow=False,
                        font=dict(size=9, color=color_sig),
                        row=1, col=col
                    )
    
    # Enhanced layout
    fig.update_layout(
        title=dict(
            text=f'<b>{title}</b><br><sub>Colors = Cell Lines, Mean (solid), Median (dashed), Outliers (red)</sub>',
            x=0.5
        ),
        height=700,
        margin=dict(l=60, r=60, t=120, b=80),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        showlegend=True,
        font=dict(size=11)
    )
    
    # Update axes
    for col in range(1, len(divs) + 1):
        fig.update_xaxes(
            tickvals=[1.3],
            ticktext=["<b>Cell Lines</b>"],
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.2)',
            row=1, col=col
        )
    
    metric_labels = {
        'FRmean': 'Mean Firing Rate (Hz)',
        'FRmedian': 'Median Firing Rate (Hz)',
        'numActiveElec': 'Number of Active Electrodes',
        'NBurstRate': 'Network Burst Rate (per minute)',
        'meanNBstLengthS': 'Mean Network Burst Length (s)',
        'meanISIWithinNbursts_ms': 'Mean ISI Within Network Bursts (ms)',
        'meanISIoutsideNbursts_ms': 'Mean ISI Outside Network Bursts (ms)',
        'meanNumChansInvolvedInNbursts': 'Mean Channels in Network Bursts',
        'CVofINBI': 'CV of Inter-Network Burst Intervals'
    }
    
    fig.update_yaxes(
        title_text=metric_labels.get(metric, metric),
        range=[0, max_y * 1.15],
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.2)'
    )
    
    return fig