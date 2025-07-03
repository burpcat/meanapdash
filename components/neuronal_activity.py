# components/neuronal_activity.py - MEA-NAP MATLAB Style + Data Rich - VERIFIED
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
    Create MEA-NAP MATLAB style violin plot with comprehensive statistics
    """

    def debug_plot_data(data, metric, title, selected_groups=None, selected_divs=None):
        """Debug function to print what data is being passed to plotting functions"""
        print(f"\n🎨 DEBUG PLOT DATA for {metric}:")
        print(f"Title: {title}")
        print(f"Selected groups: {selected_groups}")
        print(f"Selected divs: {selected_divs}")
        
        if selected_groups:
            groups = [g for g in selected_groups if g in data['groups']]
        else:
            groups = data['groups']
        
        print(f"Filtered groups: {groups}")
        
        for group in groups:
            if group not in data['by_group']:
                print(f"❌ Group {group} not in data['by_group']")
                continue
                
            group_data = data['by_group'][group]
            if metric not in group_data:
                print(f"❌ Metric {metric} not in group {group}")
                print(f"   Available in {group}: {list(group_data.keys())}")
                continue
            
            values = group_data[metric]
            print(f"✅ Group {group}: {type(values)} with {len(values) if isinstance(values, list) else 1} values")
            
            if isinstance(values, list):
                valid_values = [v for v in values if v is not None and not (isinstance(v, float) and np.isnan(v))]
                print(f"   Valid values: {len(valid_values)}/{len(values)}")
                if valid_values:
                    print(f"   Sample: {valid_values[:3]}")
                else:
                    print(f"   ❌ NO VALID VALUES after filtering!")
    # print(f"\nDEBUG: Creating MEA-NAP style violin plot by group for metric: {metric}")

    debug_plot_data(data, metric, title, selected_groups, selected_divs)
    
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
    
    # Create figure - MEA-NAP style
    fig = make_subplots(
        rows=1, cols=len(groups), 
        subplot_titles=[f'<b>{g}</b>' for g in groups],
        shared_yaxes=True,
        horizontal_spacing=0.08
    )
    
    # MEA-NAP MATLAB color scheme
    matlab_colors = {
        50: '#FFD700',  # Yellow for DIV 50
        53: '#8A2BE2'   # Purple for DIV 53
    }
    
    matlab_fill_colors = {
        50: 'rgba(255, 215, 0, 0.6)',    # Yellow with transparency
        53: 'rgba(138, 43, 226, 0.6)'   # Purple with transparency
    }
    
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
            
            # MEA-NAP styling
            x_base = div_idx + 1
            violin_color = matlab_colors.get(div, '#1f77b4')
            fill_color = matlab_fill_colors.get(div, 'rgba(31, 119, 180, 0.6)')
            
            # Black dots for regular data (MEA-NAP style)
            regular_data = [x for x in div_data if x not in stats_info['outliers']]
            outlier_data = stats_info['outliers']
            
            # Regular points - BLACK like MEA-NAP (smaller, no outline)
            if regular_data:
                jitter = np.random.normal(0, 0.02, size=len(regular_data))  # Less jitter
                fig.add_trace(
                    go.Scatter(
                        x=[x_base + j for j in jitter],
                        y=regular_data,
                        mode='markers',
                        marker=dict(
                            color='black',  # Black dots like MEA-NAP
                            size=3,  # Smaller dots
                            opacity=0.6  # More transparent
                        ),
                        name=f'DIV {div}',
                        legendgroup=f'DIV {div}',
                        showlegend=(col == 1),
                        hovertemplate=f'DIV {div}: %{{y:.2f}}<extra></extra>'
                    ),
                    row=1, col=col
                )
            
            # Outlier points (keep red for identification)
            if outlier_data:
                jitter_out = np.random.normal(0, 0.03, size=len(outlier_data))
                fig.add_trace(
                    go.Scatter(
                        x=[x_base + j for j in jitter_out],
                        y=outlier_data,
                        mode='markers',
                        marker=dict(
                            color='red', 
                            size=5, 
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
            
            # Full violin (both sides) - MEA-NAP style (thinner)
            fig.add_trace(
                go.Violin(
                    x=[x_base] * len(kde_data['x']),
                    y=kde_data['x'],
                    width=0.6,  # Thinner violin
                    side='both',  # Full violin like MEA-NAP
                    line_color=violin_color,
                    fillcolor=fill_color,
                    points=False,
                    meanline_visible=False,
                    showlegend=False,
                    hoverinfo='skip'
                ),
                row=1, col=col
            )
            
            # Black mean dot - prominent like MEA-NAP
            fig.add_trace(
                go.Scatter(
                    x=[x_base],
                    y=[stats_info['mean']],
                    mode='markers',
                    marker=dict(
                        color='black',
                        size=8,
                        opacity=1.0
                    ),
                    showlegend=False,
                    hovertemplate=f'Mean: {stats_info["mean"]:.2f}<extra></extra>'
                ),
                row=1, col=col
            )
            
            # Sample size annotation - simpler like MEA-NAP
            fig.add_annotation(
                x=x_base,
                y=max_y * 1.05,
                text=f'n={stats_info["n"]}',
                showarrow=False,
                font=dict(size=10, color='black'),
                row=1, col=col
            )
        
        all_group_stats[group] = group_div_stats
    
    # MEA-NAP MATLAB style layout
    fig.update_layout(
        title=dict(
            text=f'<b>{title}</b>',
            x=0.5,
            font=dict(size=16, color='black')
        ),
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=30, t=80, b=60),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12)
        ),
        font=dict(family="Arial", size=12, color='black')
    )
    
    # Clean axes - MEA-NAP style
    for col in range(1, len(groups) + 1):
        fig.update_xaxes(
            tickvals=list(range(1, len(divs) + 1)),
            ticktext=[str(div) for div in divs],  # Just numbers like MEA-NAP
            title_text="Age" if col == len(groups)//2 + 1 else "",  # Center title
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(200,200,200,0.5)',
            linecolor='black',
            linewidth=1,
            row=1, col=col
        )
    
    # Y-axis - MEA-NAP style with dynamic labels
    metric_labels = {
        'FR': 'mean_firing_rate_node',
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
        range=[0, max_y * 1.1],
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(200,200,200,0.5)',
        linecolor='black',
        linewidth=1,
        zeroline=True,
        zerolinecolor='rgba(200,200,200,0.8)',
        zerolinewidth=1
    )
    
    return fig

def create_half_violin_plot_by_age(data, metric, title, selected_groups=None, selected_divs=None):
    """
    Create MEA-NAP MATLAB style violin plot by age with comprehensive statistics
    """
    # print(f"\nDEBUG: Creating MEA-NAP style violin plot by age for metric: {metric}")
    
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
    
    # Create figure with subplots for each GROUP (like MEA-NAP Image 3)
    fig = make_subplots(
        rows=1, cols=len(groups), 
        subplot_titles=[f'<b>{group}</b>' for group in groups],
        shared_yaxes=True,
        horizontal_spacing=0.12
    )
    
    # MEA-NAP colors
    matlab_colors = {
        50: '#FFD700',  # Yellow for DIV 50
        53: '#8A2BE2'   # Purple for DIV 53
    }
    
    matlab_fill_colors = {
        50: 'rgba(255, 215, 0, 0.7)',
        53: 'rgba(138, 43, 226, 0.7)'
    }
    
    max_y = 0
    all_div_stats = {}
    
    # Process each GROUP (like MEA-NAP layout)
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
        
        # Process each DIV within this group
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
            
            # MEA-NAP style plotting - Age on x-axis
            x_base = div  # Use actual DIV number (50, 53) for x-position
            color = matlab_colors.get(div, '#1f77b4')
            fill_color = matlab_fill_colors.get(div, 'rgba(31, 119, 180, 0.7)')
            
            # Enhanced scatter with outliers
            regular_data = [x for x in div_data if x not in stats_info['outliers']]
            outlier_data = stats_info['outliers']
            
            # Regular points - BLACK like MEA-NAP (smaller, cleaner)
            if regular_data:
                jitter = np.random.normal(0, 0.2, size=len(regular_data))
                fig.add_trace(
                    go.Scatter(
                        x=[x_base + j for j in jitter],
                        y=regular_data,
                        mode='markers',
                        marker=dict(
                            color='black',  # Black dots like MEA-NAP
                            size=3,
                            opacity=0.6
                        ),
                        name=f'DIV {div}',
                        legendgroup=f'DIV {div}',
                        showlegend=(col == 1),
                        hovertemplate=f'DIV {div}: %{{y:.2f}}<extra></extra>'
                    ),
                    row=1, col=col
                )
            
            # Outliers (keep red)
            if outlier_data:
                jitter_out = np.random.normal(0, 0.3, size=len(outlier_data))
                fig.add_trace(
                    go.Scatter(
                        x=[x_base + j for j in jitter_out],
                        y=outlier_data,
                        mode='markers',
                        marker=dict(color='red', size=5, opacity=0.8, 
                                  line=dict(width=1, color='darkred')),
                        showlegend=False,
                        hovertemplate=f'<b>DIV {div} - OUTLIER</b><br>Value: %{{y:.3f}}<extra></extra>'
                    ),
                    row=1, col=col
                )
            
            # Full violin (both sides) - exactly like MEA-NAP
            fig.add_trace(
                go.Violin(
                    x=[x_base] * len(kde_data['x']),
                    y=kde_data['x'],
                    width=2.5,  # Slightly narrower
                    side='both',
                    line_color=color,
                    fillcolor=fill_color,
                    points=False,
                    meanline_visible=False,
                    showlegend=False,
                    hoverinfo='skip'
                ),
                row=1, col=col
            )
            
            # Black mean dot - MEA-NAP style
            fig.add_trace(
                go.Scatter(
                    x=[x_base],
                    y=[stats_info['mean']],
                    mode='markers',
                    marker=dict(
                        color='black',
                        size=8,
                        opacity=1.0
                    ),
                    showlegend=False,
                    hovertemplate=f'Mean: {stats_info["mean"]:.2f}<extra></extra>'
                ),
                row=1, col=col
            )
            
            # Sample size annotation
            fig.add_annotation(
                x=x_base,
                y=max_y * 1.05,
                text=f'n={stats_info["n"]}',
                showarrow=False,
                font=dict(size=10, color='black'),
                row=1, col=col
            )
        
        all_div_stats[group] = group_div_stats
    
    # MEA-NAP style layout - matches Image 3
    fig.update_layout(
        title=dict(
            text=f'<b>{title}</b>',
            x=0.5,
            font=dict(size=16, color='black')
        ),
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=30, t=80, b=60),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        font=dict(family="Arial", size=12, color='black')
    )
    
    # X-axes - Age style like MEA-NAP Image 3
    for col in range(1, len(groups) + 1):
        fig.update_xaxes(
            tickvals=divs,
            ticktext=[str(div) for div in divs],
            title_text="Age" if col == len(groups)//2 + 1 else "",
            range=[min(divs) - 2, max(divs) + 2],  # Give space around violins
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(200,200,200,0.5)',
            linecolor='black',
            linewidth=1,
            row=1, col=col
        )
    
    # Y-axis - MEA-NAP style with dynamic labels
    metric_labels = {
        'FR': 'mean_firing_rate_node',
        'FRmean': 'Mean Firing Rate (Hz)',
        'FRmedian': 'Median Firing Rate (Hz)',
        'numActiveElec': 'Number of Active Electrodes',
        'NBurstRate': 'Network Burst Rate (per minute)',
        'channelISIwithinBurst': 'Unit ISI Within Burst (ms)',
        'channeISIoutsideBurst': 'Unit ISI Outside Burst (ms)',
        'channelFracSpikesInBursts': 'Unit Fraction of Spikes in Bursts',
        'channelBurstRate': 'Burst Rate (per minute)',
        'channelBurstDur': 'Burst Duration (ms)'
    }
    
    fig.update_yaxes(
        title_text=metric_labels.get(metric, metric),
        range=[0, max_y * 1.1],
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(200,200,200,0.5)',
        linecolor='black',
        linewidth=1,
        zeroline=True,
        zerolinecolor='rgba(200,200,200,0.8)',
        zerolinewidth=1
    )
    
    return fig

def create_box_plot_by_group(data, metric, title, selected_groups=None, selected_divs=None):
    """
    Create MEA-NAP style box plot by group
    """
    # print(f"\nDEBUG: Creating box plot by group for metric: {metric}")
    
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
    
    # Create figure
    fig = make_subplots(
        rows=1, cols=len(groups), 
        subplot_titles=[f'<b>{g}</b>' for g in groups],
        shared_yaxes=True,
        horizontal_spacing=0.08
    )
    
    # MEA-NAP colors
    matlab_colors = {
        50: '#FFD700',  # Yellow for DIV 50
        53: '#8A2BE2'   # Purple for DIV 53
    }
    
    max_y = 0
    
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
            
            # Filter valid data
            div_data = [d for d in div_data if d is not None and np.isfinite(d)]
            if not div_data:
                continue
                
            max_y = max(max_y, max(div_data))
            
            # Create box plot
            color = matlab_colors.get(div, '#1f77b4')
            
            fig.add_trace(
                go.Box(
                    y=div_data,
                    name=f'DIV {div}',
                    legendgroup=f'DIV {div}',
                    showlegend=(col == 1),
                    marker_color=color,
                    line_color=color,
                    fillcolor=color.replace(')', ', 0.3)').replace('rgb', 'rgba') if 'rgb' in color else color + '4D',
                    boxpoints='outliers',  # Show outliers
                    notched=True,  # Show confidence interval
                    x=[f'DIV {div}'] * len(div_data)
                ),
                row=1, col=col
            )
    
    # Layout
    fig.update_layout(
        title=dict(
            text=f'<b>{title}</b>',
            x=0.5,
            font=dict(size=16, color='black')
        ),
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=30, t=80, b=60),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        font=dict(family="Arial", size=12, color='black')
    )
    
    # Update axes
    for col in range(1, len(groups) + 1):
        fig.update_xaxes(
            tickvals=[f'DIV {div}' for div in divs],
            ticktext=[str(div) for div in divs],
            title_text="Age" if col == len(groups)//2 + 1 else "",
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(200,200,200,0.5)',
            linecolor='black',
            linewidth=1,
            row=1, col=col
        )
    
    # Y-axis
    metric_labels = {
        'FR': 'Firing Rate (Hz)',
        'FRmean': 'Mean Firing Rate (Hz)',
        'FRmedian': 'Median Firing Rate (Hz)',
        'numActiveElec': 'Number of Active Electrodes',
        'NBurstRate': 'Network Burst Rate (per minute)',
        'channelISIwithinBurst': 'ISI Within Burst (ms)',
        'channeISIoutsideBurst': 'ISI Outside Burst (ms)',
        'channelFracSpikesInBursts': 'Fraction Spikes in Bursts',
        'channelBurstRate': 'Burst Rate (per minute)',
        'channelBurstDur': 'Burst Duration (ms)'
    }
    
    fig.update_yaxes(
        title_text=metric_labels.get(metric, metric),
        range=[0, max_y * 1.1],
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(200,200,200,0.5)',
        linecolor='black',
        linewidth=1,
        zeroline=True,
        zerolinecolor='rgba(200,200,200,0.8)',
        zerolinewidth=1
    )
    
    return fig

def create_bar_plot_by_group(data, metric, title, selected_groups=None, selected_divs=None):
    """
    Create MEA-NAP style bar plot by group (showing means with error bars)
    """
    # print(f"\nDEBUG: Creating bar plot by group for metric: {metric}")
    
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
    
    # Create figure
    fig = go.Figure()
    
    # MEA-NAP colors
    matlab_colors = {
        50: '#FFD700',  # Yellow for DIV 50
        53: '#8A2BE2'   # Purple for DIV 53
    }
    
    # Process data for bar plot
    x_labels = []
    y_means = []
    y_errors = []
    colors = []
    
    for group in groups:
        if group not in data['by_group']:
            continue
            
        group_data = data['by_group'][group]
        if metric not in group_data:
            continue
            
        is_recording_metric = metric in ['FRmean', 'FRmedian', 'numActiveElec', 'NBurstRate', 
                                'meanNumChansInvolvedInNbursts', 'meanNBstLengthS',
                                'meanISIWithinNbursts_ms', 'meanISIoutsideNbursts_ms',
                                'CVofINBI', 'fracInNburst']
        
        # Process each DIV
        for div in divs:
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
            
            # Filter valid data
            div_data = [d for d in div_data if d is not None and np.isfinite(d)]
            if not div_data:
                continue
            
            # Calculate mean and SEM
            mean_val = np.mean(div_data)
            sem_val = np.std(div_data) / np.sqrt(len(div_data)) if len(div_data) > 1 else 0
            
            x_labels.append(f'{group}\nDIV {div}')
            y_means.append(mean_val)
            y_errors.append(sem_val)
            colors.append(matlab_colors.get(div, '#1f77b4'))
    
    # Create bar plot
    fig.add_trace(
        go.Bar(
            x=x_labels,
            y=y_means,
            error_y=dict(
                type='data',
                array=y_errors,
                visible=True,
                color='black',
                thickness=2,
                width=4
            ),
            marker_color=colors,
            marker_line=dict(color='black', width=1),
            opacity=0.8,
            hovertemplate='%{x}<br>Mean: %{y:.3f}<br>SEM: %{error_y.array:.3f}<extra></extra>'
        )
    )
    
    # Layout
    fig.update_layout(
        title=dict(
            text=f'<b>{title}</b>',
            x=0.5,
            font=dict(size=16, color='black')
        ),
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=30, t=80, b=60),
        xaxis_title="<b>Group / Age</b>",
        yaxis_title=f"<b>Mean {metric}</b>",
        font=dict(family="Arial", size=12, color='black'),
        showlegend=False
    )
    
    # Update axes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(200,200,200,0.5)',
        linecolor='black',
        linewidth=1
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(200,200,200,0.5)',
        linecolor='black',
        linewidth=1,
        zeroline=True,
        zerolinecolor='rgba(200,200,200,0.8)',
        zerolinewidth=1
    )
    
    return fig

def create_box_plot_by_age(data, metric, title, selected_groups=None, selected_divs=None):
    """
    Create MEA-NAP style box plot by age (similar to create_box_plot_by_group but organized by DIV)
    """
    # print(f"\nDEBUG: Creating box plot by age for metric: {metric}")
    
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
    
    # Create figure with subplots for each GROUP
    fig = make_subplots(
        rows=1, cols=len(groups), 
        subplot_titles=[f'<b>{group}</b>' for group in groups],
        shared_yaxes=True,
        horizontal_spacing=0.12
    )
    
    # MEA-NAP colors
    matlab_colors = {
        50: '#FFD700',  # Yellow for DIV 50
        53: '#8A2BE2'   # Purple for DIV 53
    }
    
    max_y = 0
    
    # Process each GROUP
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
        
        # Process each DIV within this group
        for div in divs:
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
            
            # Filter valid data
            div_data = [d for d in div_data if d is not None and np.isfinite(d)]
            if not div_data:
                continue
                
            max_y = max(max_y, max(div_data))
            
            # Create box plot
            color = matlab_colors.get(div, '#1f77b4')
            
            fig.add_trace(
                go.Box(
                    y=div_data,
                    name=f'DIV {div}',
                    legendgroup=f'DIV {div}',
                    showlegend=(col == 1),
                    marker_color=color,
                    line_color=color,
                    fillcolor=color.replace(')', ', 0.3)').replace('rgb', 'rgba') if 'rgb' in color else color + '4D',
                    boxpoints='outliers',
                    notched=True,
                    x=[div] * len(div_data)  # Use DIV number for x-position
                ),
                row=1, col=col
            )
    
    # Layout
    fig.update_layout(
        title=dict(
            text=f'<b>{title}</b>',
            x=0.5,
            font=dict(size=16, color='black')
        ),
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=30, t=80, b=60),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        font=dict(family="Arial", size=12, color='black')
    )
    
    # X-axes
    for col in range(1, len(groups) + 1):
        fig.update_xaxes(
            tickvals=divs,
            ticktext=[str(div) for div in divs],
            title_text="Age" if col == len(groups)//2 + 1 else "",
            range=[min(divs) - 2, max(divs) + 2],
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(200,200,200,0.5)',
            linecolor='black',
            linewidth=1,
            row=1, col=col
        )
    
    # Y-axis
    metric_labels = {
        'FR': 'Firing Rate (Hz)',
        'FRmean': 'Mean Firing Rate (Hz)',
        'FRmedian': 'Median Firing Rate (Hz)',
        'numActiveElec': 'Number of Active Electrodes',
        'NBurstRate': 'Network Burst Rate (per minute)',
        'channelISIwithinBurst': 'ISI Within Burst (ms)',
        'channeISIoutsideBurst': 'ISI Outside Burst (ms)',
        'channelFracSpikesInBursts': 'Fraction Spikes in Bursts',
        'channelBurstRate': 'Burst Rate (per minute)',
        'channelBurstDur': 'Burst Duration (ms)'
    }
    
    fig.update_yaxes(
        title_text=metric_labels.get(metric, metric),
        range=[0, max_y * 1.1],
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(200,200,200,0.5)',
        linecolor='black',
        linewidth=1,
        zeroline=True,
        zerolinecolor='rgba(200,200,200,0.8)',
        zerolinewidth=1
    )
    
    return fig

def create_bar_plot_by_age(data, metric, title, selected_groups=None, selected_divs=None):
    """
    Create MEA-NAP style bar plot by age (showing means with error bars)
    """
    # print(f"\nDEBUG: Creating bar plot by age for metric: {metric}")
    
    # Similar to create_bar_plot_by_group but organized by age
    # Implementation follows the same pattern as create_bar_plot_by_group
    # but iterates through DIVs first, then groups
    
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
    fig = go.Figure()
    
    # MEA-NAP colors
    matlab_colors = {
        50: '#FFD700',  # Yellow for DIV 50
        53: '#8A2BE2'   # Purple for DIV 53
    }
    
    # Process data for bar plot (organized by DIV, then group)
    x_labels = []
    y_means = []
    y_errors = []
    colors = []
    
    for div in divs:
        for group in groups:
            if group not in data['by_group']:
                continue
                
            group_data = data['by_group'][group]
            if metric not in group_data:
                continue
                
            is_recording_metric = metric in ['FRmean', 'FRmedian', 'numActiveElec', 'NBurstRate', 
                                    'meanNumChansInvolvedInNbursts', 'meanNBstLengthS',
                                    'meanISIWithinNbursts_ms', 'meanISIoutsideNbursts_ms',
                                    'CVofINBI', 'fracInNburst']
            
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
            
            # Filter valid data
            div_data = [d for d in div_data if d is not None and np.isfinite(d)]
            if not div_data:
                continue
            
            # Calculate mean and SEM
            mean_val = np.mean(div_data)
            sem_val = np.std(div_data) / np.sqrt(len(div_data)) if len(div_data) > 1 else 0
            
            x_labels.append(f'DIV {div}\n{group}')
            y_means.append(mean_val)
            y_errors.append(sem_val)
            colors.append(matlab_colors.get(div, '#1f77b4'))
    
    # Create bar plot
    fig.add_trace(
        go.Bar(
            x=x_labels,
            y=y_means,
            error_y=dict(
                type='data',
                array=y_errors,
                visible=True,
                color='black',
                thickness=2,
                width=4
            ),
            marker_color=colors,
            marker_line=dict(color='black', width=1),
            opacity=0.8,
            hovertemplate='%{x}<br>Mean: %{y:.3f}<br>SEM: %{error_y.array:.3f}<extra></extra>'
        )
    )
    
    # Layout
    fig.update_layout(
        title=dict(
            text=f'<b>{title}</b>',
            x=0.5,
            font=dict(size=16, color='black')
        ),
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=60, r=30, t=80, b=60),
        xaxis_title="<b>Age / Group</b>",
        yaxis_title=f"<b>Mean {metric}</b>",
        font=dict(family="Arial", size=12, color='black'),
        showlegend=False
    )
    
    # Update axes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(200,200,200,0.5)',
        linecolor='black',
        linewidth=1
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(200,200,200,0.5)',
        linecolor='black',
        linewidth=1,
        zeroline=True,
        zerolinecolor='rgba(200,200,200,0.8)',
        zerolinewidth=1
    )
    
    return fig