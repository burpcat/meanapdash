# components/layout.py
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

def create_layout(app):
    """
    Create the main layout of the dashboard
    
    Parameters:
    -----------
    app : dash.Dash
        The Dash application instance
        
    Returns:
    --------
    html.Div
        The main layout div
    """
    # Extract unique values for filters
    groups = app.data['info']['groups']
    divs = sorted(set(div for group_divs in app.data['info']['divs'].values() for div in group_divs.keys()))
    lags = app.data['info']['lags']
    
    # Create the layout
    return html.Div([
        # Header
        dbc.Navbar(
            dbc.Container([
                html.A(
                    dbc.Row([
                        dbc.Col(dbc.NavbarBrand("MEA-NAP Dashboard", className="ms-2")),
                    ], align="center"),
                ),
            ]),
            color="dark",
            dark=True,
            className="mb-4",
        ),
        
        # Main content
        dbc.Container([
            # Tabs for different visualization types
            dbc.Tabs([
                # 2B_GroupComparisons tabs
                
                # Node by Group tab (2B_1)
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            html.H4("Neuronal Activity: Electrode-Level Metrics by Group", className="mt-3"),
                            dbc.Card([
                                dbc.CardBody([
                                    # Controls for selecting metrics
                                    html.P("Select Metric:"),
                                    dcc.Dropdown(
                                        id="neuronal-node-group-metric",
                                        options=[
                                            {"label": "Firing Rate (Hz)", "value": "FR"},
                                            {"label": "Burst Rate (per minute)", "value": "channelBurstRate"},
                                            {"label": "Burst Duration (ms)", "value": "channelBurstDur"},
                                            {"label": "ISI Within Burst (ms)", "value": "channelISIwithinBurst"},
                                            {"label": "ISI Outside Burst (ms)", "value": "channeISIoutsideBurst"},
                                            {"label": "Fraction Spikes in Bursts", "value": "channelFracSpikesInBursts"}
                                        ],
                                        value="FR"
                                    ),
                                    
                                    # Visualizations
                                    dcc.Graph(id="neuronal-node-group-plot", style={"height": "600px"})
                                ])
                            ])
                        ], width=12)
                    ])
                ], label="Neuronal: Node by Group"),
                
                # Node by Age tab (2B_2)
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            html.H4("Neuronal Activity: Electrode-Level Metrics by Age", className="mt-3"),
                            dbc.Card([
                                dbc.CardBody([
                                    # Controls for selecting metrics
                                    html.P("Select Metric:"),
                                    dcc.Dropdown(
                                        id="neuronal-node-age-metric",
                                        options=[
                                            {"label": "Firing Rate (Hz)", "value": "FR"},
                                            {"label": "Burst Rate (per minute)", "value": "channelBurstRate"},
                                            {"label": "Burst Duration (ms)", "value": "channelBurstDur"},
                                            {"label": "ISI Within Burst (ms)", "value": "channelISIwithinBurst"},
                                            {"label": "ISI Outside Burst (ms)", "value": "channeISIoutsideBurst"},
                                            {"label": "Fraction Spikes in Bursts", "value": "channelFracSpikesInBursts"}
                                        ],
                                        value="FR"
                                    ),
                                    
                                    # Visualizations
                                    dcc.Graph(id="neuronal-node-age-plot", style={"height": "600px"})
                                ])
                            ])
                        ], width=12)
                    ])
                ], label="Neuronal: Node by Age"),
                
                # Recording by Group tab (2B_3)
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            html.H4("Neuronal Activity: Recording-Level Metrics by Group", className="mt-3"),
                            dbc.Card([
                                dbc.CardBody([
                                    # Controls for selecting metrics
                                    html.P("Select Metric:"),
                                    dcc.Dropdown(
                                        id="neuronal-recording-group-metric",
                                        options=[
                                            {"label": "Number of Active Electrodes", "value": "numActiveElec"},
                                            {"label": "Mean Firing Rate (Hz)", "value": "FRmean"},
                                            {"label": "Network Burst Rate (per minute)", "value": "NBurstRate"},
                                            {"label": "Mean Network Burst Length (s)", "value": "meanNBstLengthS"},
                                            {"label": "Mean ISI Within Network Burst (ms)", "value": "meanISIWithinNbursts_ms"},
                                            {"label": "Mean ISI Outside Network Burst (ms)", "value": "meanISIoutsideNbursts_ms"}
                                        ],
                                        value="FRmean"
                                    ),
                                    
                                    # Visualizations
                                    dcc.Graph(id="neuronal-recording-group-plot", style={"height": "600px"})
                                ])
                            ])
                        ], width=12)
                    ])
                ], label="Neuronal: Recording by Group"),
                
                # Recording by Age tab (2B_4)
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            html.H4("Neuronal Activity: Recording-Level Metrics by Age", className="mt-3"),
                            dbc.Card([
                                dbc.CardBody([
                                    # Controls for selecting metrics
                                    html.P("Select Metric:"),
                                    dcc.Dropdown(
                                        id="neuronal-recording-age-metric",
                                        options=[
                                            {"label": "Number of Active Electrodes", "value": "numActiveElec"},
                                            {"label": "Mean Firing Rate (Hz)", "value": "FRmean"},
                                            {"label": "Network Burst Rate (per minute)", "value": "NBurstRate"},
                                            {"label": "Mean Network Burst Length (s)", "value": "meanNBstLengthS"},
                                            {"label": "Mean ISI Within Network Burst (ms)", "value": "meanISIWithinNbursts_ms"},
                                            {"label": "Mean ISI Outside Network Burst (ms)", "value": "meanISIoutsideNbursts_ms"}
                                        ],
                                        value="FRmean"
                                    ),
                                    
                                    # Visualizations
                                    dcc.Graph(id="neuronal-recording-age-plot", style={"height": "600px"})
                                ])
                            ])
                        ], width=12)
                    ])
                ], label="Neuronal: Recording by Age"),
                
                # 4B_GroupComparisons tabs
                
                # Node by Group tab (4B_1)
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            html.H4("Network Activity: Node-Level Metrics by Group", className="mt-3"),
                            dbc.Card([
                                dbc.CardBody([
                                    # Controls for selecting metrics and lag
                                    dbc.Row([
                                        dbc.Col([
                                            html.P("Select Metric:"),
                                            dcc.Dropdown(
                                                id="network-node-group-metric",
                                                options=[
                                                    {"label": "Degree", "value": "degree"},
                                                    {"label": "Strength", "value": "strength"},
                                                    {"label": "Clustering", "value": "clustering"},
                                                    {"label": "Betweenness Centrality", "value": "betweenness"},
                                                    {"label": "Local Efficiency", "value": "efficiency_local"},
                                                    {"label": "Participation Coefficient", "value": "participation"}
                                                ],
                                                value="degree"
                                            )
                                        ], width=8),
                                        dbc.Col([
                                            html.P("Select Lag:"),
                                            dcc.Dropdown(
                                                id="network-node-group-lag",
                                                options=[{"label": f"{lag} ms", "value": lag} for lag in lags],
                                                value=lags[0] if lags else None
                                            )
                                        ], width=4)
                                    ]),
                                    
                                    # Visualizations
                                    dcc.Graph(id="network-node-group-plot", style={"height": "600px"})
                                ])
                            ])
                        ], width=12)
                    ])
                ], label="Network: Node by Group"),
                
                # Node by Age tab (4B_2)
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            html.H4("Network Activity: Node-Level Metrics by Age", className="mt-3"),
                            dbc.Card([
                                dbc.CardBody([
                                    # Controls for selecting metrics and lag
                                    dbc.Row([
                                        dbc.Col([
                                            html.P("Select Metric:"),
                                            dcc.Dropdown(
                                                id="network-node-age-metric",
                                                options=[
                                                    {"label": "Degree", "value": "degree"},
                                                    {"label": "Strength", "value": "strength"},
                                                    {"label": "Clustering", "value": "clustering"},
                                                    {"label": "Betweenness Centrality", "value": "betweenness"},
                                                    {"label": "Local Efficiency", "value": "efficiency_local"},
                                                    {"label": "Participation Coefficient", "value": "participation"}
                                                ],
                                                value="degree"
                                            )
                                        ], width=8),
                                        dbc.Col([
                                            html.P("Select Lag:"),
                                            dcc.Dropdown(
                                                id="network-node-age-lag",
                                                options=[{"label": f"{lag} ms", "value": lag} for lag in lags],
                                                value=lags[0] if lags else None
                                            )
                                        ], width=4)
                                    ]),
                                    
                                    # Visualizations
                                    dcc.Graph(id="network-node-age-plot", style={"height": "600px"})
                                ])
                            ])
                        ], width=12)
                    ])
                ], label="Network: Node by Age"),
                
                # Network by Group tab (4B_3)
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            html.H4("Network Activity: Network-Level Metrics by Group", className="mt-3"),
                            dbc.Card([
                                dbc.CardBody([
                                    # Controls for selecting metrics and lag
                                    dbc.Row([
                                        dbc.Col([
                                            html.P("Select Metric:"),
                                            dcc.Dropdown(
                                                id="network-recording-group-metric",
                                                options=[
                                                    {"label": "Density", "value": "density"},
                                                    {"label": "Global Efficiency", "value": "efficiency_global"},
                                                    {"label": "Modularity", "value": "modularity"},
                                                    {"label": "Small-worldness", "value": "smallworldness"}
                                                ],
                                                value="density"
                                            )
                                        ], width=8),
                                        dbc.Col([
                                            html.P("Select Lag:"),
                                            dcc.Dropdown(
                                                id="network-recording-group-lag",
                                                options=[{"label": f"{lag} ms", "value": lag} for lag in lags],
                                                value=lags[0] if lags else None
                                            )
                                        ], width=4)
                                    ]),
                                    
                                    # Visualizations
                                    dcc.Graph(id="network-recording-group-plot", style={"height": "600px"})
                                ])
                            ])
                        ], width=12)
                    ])
                ], label="Network: Recording by Group"),
                
                # Network by Age tab (4B_4)
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            html.H4("Network Activity: Network-Level Metrics by Age", className="mt-3"),
                            dbc.Card([
                                dbc.CardBody([
                                    # Controls for selecting metrics and lag
                                    dbc.Row([
                                        dbc.Col([
                                            html.P("Select Metric:"),
                                            dcc.Dropdown(
                                                id="network-recording-age-metric",
                                                options=[
                                                    {"label": "Density", "value": "density"},
                                                    {"label": "Global Efficiency", "value": "efficiency_global"},
                                                    {"label": "Modularity", "value": "modularity"},
                                                    {"label": "Small-worldness", "value": "smallworldness"}
                                                ],
                                                value="density"
                                            )
                                        ], width=8),
                                        dbc.Col([
                                            html.P("Select Lag:"),
                                            dcc.Dropdown(
                                                id="network-recording-age-lag",
                                                options=[{"label": f"{lag} ms", "value": lag} for lag in lags],
                                                value=lags[0] if lags else None
                                            )
                                        ], width=4)
                                    ]),
                                    
                                    # Visualizations
                                    dcc.Graph(id="network-recording-age-plot", style={"height": "600px"})
                                ])
                            ])
                        ], width=12)
                    ])
                ], label="Network: Recording by Age"),
                
                # Metrics by Lag tab (4B_5)
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            html.H4("Network Activity: Metrics by Lag", className="mt-3"),
                            dbc.Card([
                                dbc.CardBody([
                                    # Controls for selecting groups and metrics
                                    dbc.Row([
                                        dbc.Col([
                                            html.P("Select Group:"),
                                            dcc.Dropdown(
                                                id="network-lag-group",
                                                options=[{"label": g, "value": g} for g in groups],
                                                value=groups[0] if groups else None
                                            )
                                        ], width=4),
                                        dbc.Col([
                                            html.P("Select Metric:"),
                                            dcc.Dropdown(
                                                id="network-lag-metric",
                                                options=[
                                                    {"label": "Density", "value": "density"},
                                                    {"label": "Global Efficiency", "value": "efficiency_global"},
                                                    {"label": "Modularity", "value": "modularity"},
                                                    {"label": "Small-worldness", "value": "smallworldness"}
                                                ],
                                                value="density"
                                            )
                                        ], width=8)
                                    ]),
                                    
                                    # Visualizations
                                    dcc.Graph(id="network-lag-plot", style={"height": "600px"})
                                ])
                            ])
                        ], width=12)
                    ])
                ], label="Network: Metrics by Lag"),
                
                # Node Cartography tab (4B_6)
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            html.H4("Network Activity: Node Cartography", className="mt-3"),
                            dbc.Card([
                                dbc.CardBody([
                                    # Controls for selecting groups, ages, and lags
                                    dbc.Row([
                                        dbc.Col([
                                            html.P("Select Group:"),
                                            dcc.Dropdown(
                                                id="cartography-group",
                                                options=[{"label": g, "value": g} for g in groups],
                                                value=groups[0] if groups else None
                                            )
                                        ], width=4),
                                        dbc.Col([
                                            html.P("Select Lag:"),
                                            dcc.Dropdown(
                                                id="cartography-lag",
                                                options=[{"label": f"{lag} ms", "value": lag} for lag in lags],
                                                value=lags[0] if lags else None
                                            )
                                        ], width=4)
                                    ]),
                                    
                                    # Node cartography role proportions
                                    html.H5("Node Role Proportions by Age", className="mt-3"),
                                    dcc.Graph(id="cartography-proportions-plot", style={"height": "400px"}),
                                    
                                    # Node cartography scatter plot
                                    html.H5("Node Cartography Scatter Plot", className="mt-3"),
                                    dcc.Dropdown(
                                        id="cartography-div",
                                        options=[{"label": f"DIV {div}", "value": div} for div in divs],
                                        value=divs[0] if divs else None,
                                        className="mb-2"
                                    ),
                                    dcc.Graph(id="cartography-scatter-plot", style={"height": "600px"})
                                ])
                            ])
                        ], width=12)
                    ])
                ], label="Node Cartography")
                
            ], id="main-tabs"),
        ], fluid=True),
        
        # Footer
        html.Footer([
            html.P("MEA-NAP Dashboard - Built to visualize 2B_GroupComparisons and 4B_GroupComparisons data"),
            html.P("© 2023")
        ], className="footer mt-5 py-3 bg-light text-center")
    ])