import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from pathlib import Path

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Mission Governance Explorer",
    page_icon="🛡️",
    layout="wide"
)

# --- CUSTOM CSS STYLING ---
st.markdown("""
<style>
    /* Base theme colors */
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    /* Responsive fluid container that fills available space but expands/scrolls cleanly */
    .block-container { 
        max-width: 100% !important; 
        min-height: 100vh;
        padding-top: 0.8rem; 
        padding-bottom: 1rem; 
        padding-left: 1.2rem; 
        padding-right: 1.2rem; 
    }
    
    /* Restored Button Styling */
    div.stButton > button { 
        background-color: #1F77B4; 
        color: white; 
        border-radius: 4px; 
        width: 100%;
        border: none;
        font-weight: 600;
    }
    div.stButton > button:hover {
        background-color: #2980b9;
    }
    
    /* Restored Metric Card Styling */
    .metric-card { 
        background-color: #161B22; 
        padding: 12px; 
        border-radius: 8px; 
        border: 1px solid #30363D; 
        text-align: center; 
    }
    
    /* Clean applet branding adjustments */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data
def load_data():
    nodes_df = pd.read_csv("AI_Mission_Governance_Nodes_v0_1.csv")
    rels_df = pd.read_csv("AI_Mission_Governance_Relationships_v0_1.csv")
    summary_df = pd.read_csv("scenario_summary.csv")
    return nodes_df, rels_df, summary_df

nodes_df, rels_df, summary_df = load_data()

# --- SESSION STATE INITIALIZATION ---
if 'active_scenario' not in st.session_state:
    st.session_state['active_scenario'] = 1  # Default to Scenario 1
if 'selected_node_id' not in st.session_state:
    st.session_state['selected_node_id'] = None

active_scen_order = st.session_state['active_scenario']
current_summary = summary_df[summary_df['Scenario_Order'] == active_scen_order].iloc[0]
baseline_summary = summary_df[summary_df['Scenario_Order'] == 1].iloc[0]

# =========================================================================
# ZONE 1: TOP CONTROL BAR & GLOBAL KPI METRICS
# =========================================================================
st.markdown("### 🛡️ AI Mission Governance Explorer — Analytical Decision Dashboard")

scenario_names = {
    1: "S1: Traditional Automation",
    2: "S2: Generative AI",
    3: "S3: Agentic AI",
    4: "S4: Multi-Agent AI",
    5: "S5: Autonomous Ecosystem"
}

cols_nav = st.columns(5)
for i, (scen_num, scen_label) in enumerate(scenario_names.items()):
    with cols_nav[i]:
        btn_type = "primary" if active_scen_order == scen_num else "secondary"
        if st.button(scen_label, key=f"btn_scen_{scen_num}", type=btn_type, use_container_width=True):
            st.session_state['active_scenario'] = scen_num
            st.rerun()

st.markdown("---")

# KPI Metric Cards
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

resp_diff = int(current_summary['Mission_Response_Time_Sec'] - baseline_summary['Mission_Response_Time_Sec'])
esc_diff = int(current_summary['Human_Escalation_Count'] - baseline_summary['Human_Escalation_Count'])
gov_diff = int(current_summary['Peak_Human_Oversight_Load_Pct'] - baseline_summary['Peak_Human_Oversight_Load_Pct'])
it_diff = int(current_summary['Peak_IT_System_Load_Pct'] - baseline_summary['Peak_IT_System_Load_Pct'])

with kpi1:
    st.metric("Mission Response Time", f"{current_summary['Mission_Response_Time_Sec']} sec", f"{resp_diff}s vs S1", delta_color="inverse")
with kpi2:
    st.metric("Human Escalation Count", f"{current_summary['Human_Escalation_Count']}", f"{esc_diff} vs S1", delta_color="inverse")
with kpi3:
    st.metric("Peak Human Oversight Load", f"{current_summary['Peak_Human_Oversight_Load_Pct']}%", f"{gov_diff}% vs S1", delta_color="inverse")
with kpi4:
    st.metric("Peak IT System Load", f"{current_summary['Peak_IT_System_Load_Pct']}%", f"{it_diff}% vs S1", delta_color="normal")

st.markdown("---")

# =========================================================================
# ZONE 2 & 3: CENTRAL TOPOLOGY GRAPH (65%) & INSPECTION PANEL (35%)
# =========================================================================
col_graph, col_inspect = st.columns([65, 35])

# Filter nodes and relationships active in the selected scenario
active_nodes = nodes_df[
    (nodes_df['Scenario_Start_Order'] <= active_scen_order) & 
    (nodes_df['Scenario_End_Order'] >= active_scen_order)
]

active_rels = rels_df[
    (rels_df['Scenario_Start_Order'] <= active_scen_order) & 
    (rels_df['Scenario_End_Order'] >= active_scen_order)
]

with col_graph:
    st.markdown(f"#### 🌐 Governance Topology Map — {current_summary['Scenario_Name']}")
    st.caption("Click any node below or select from dropdown to trace command & escalation pathways.")

    # Build NetworkX Graph for Layout & Positioning
    G = nx.DiGraph()
    for _, node in active_nodes.iterrows():
        G.add_node(node['ID'], label=node['Label'], layer=node['Layer_Order'], type=node['Governance_Layer'])
    for _, rel in active_rels.iterrows():
        if rel['Source_ID'] in G.nodes and rel['Target_ID'] in G.nodes:
            G.add_edge(rel['Source_ID'], rel['Target_ID'], type=rel['Type'])

    # Hierarchical layout mapping (Layer_Order -> Y axis)
    pos = {}
    layer_counts = active_nodes['Layer_Order'].value_counts().to_dict()
    layer_current_idx = {l: 0 for l in layer_counts.keys()}

    for node_id, data in G.nodes(data=True):
        layer = data['layer']
        total_in_layer = layer_counts.get(layer, 1)
        idx = layer_current_idx[layer]
        layer_current_idx[layer] += 1
        
        # X spread across layer, Y structured by governance tier
        x_pos = (idx + 1) / (total_in_layer + 1)
        y_pos = 6 - layer  # Layers 1 to 5
        pos[node_id] = (x_pos, y_pos)

    # Plotly Network Rendering
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1.5, color='#888888'),
        hoverinfo='none',
        mode='lines'
    )

    node_x, node_y, node_text, node_color = [], [], [], []
    selected_node = st.session_state['selected_node_id']

    for node_id in G.nodes():
        x, y = pos[node_id]
        node_x.append(x)
        node_y.append(y)
        node_data = active_nodes[active_nodes['ID'] == node_id].iloc[0]
        
        node_text.append(f"<b>{node_data['Label']}</b><br>Layer: {node_data['Governance_Layer']}")
        
        # Color highlighting based on selection & criticality
        if node_id == selected_node:
            node_color.append('#FF4B4B') # Selected Red Highlight
        else:
            node_color.append('#2ECC71' if node_data['Criticality'] == 'Low' else '#F1C40F')

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=[active_nodes[active_nodes['ID'] == nid]['Label'].values[0] for nid in G.nodes()],
        textposition="top center",
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color=node_color,
            size=18,
            line=dict(width=2, color='#FFFFFF')
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=20,r=20,t=20),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    plot_bgcolor='#0E1117',
                    paper_bgcolor='#0E1117',
                    height=450
                ))

    selected_point = st.plotly_chart(fig, use_container_width=True, on_select="rerun")
    
    # Handle Plotly click selection if captured
    node_ids_list = list(G.nodes())
    if selected_point and isinstance(selected_point, dict) and "selection" in selected_point and "point_indices" in selected_point["selection"]:
        indices = selected_point["selection"]["point_indices"]
        if indices:
            clicked_idx = indices[0]
            if clicked_idx < len(node_ids_list):
                st.session_state['selected_node_id'] = node_ids_list[clicked_idx]

with col_inspect:
    st.markdown("#### 🔍 Entity Inspection Panel")
    
    node_options = {row['ID']: f"{row['ID']} - {row['Label']} ({row['Governance_Layer']})" for _, row in active_nodes.iterrows()}
    
    selected_dropdown = st.selectbox(
        "Select Node for Inspection",
        options=list(node_options.keys()),
        format_func=lambda x: node_options[x],
        index=list(node_options.keys()).index(st.session_state['selected_node_id']) if st.session_state['selected_node_id'] in node_options else 0
    )
    
    if selected_dropdown != st.session_state['selected_node_id']:
        st.session_state['selected_node_id'] = selected_dropdown
        st.rerun()

    sel_id = st.session_state['selected_node_id']
    if sel_id and sel_id in active_nodes['ID'].values:
        node_row = active_nodes[active_nodes['ID'] == sel_id].iloc[0]
        
        st.markdown(f"**Entity Name:** {node_row['Label']}")
        st.markdown(f"**ID:** `{node_row['ID']}` | **Category:** {node_row['Governance_Layer']}")
        st.markdown(f"**Type:** {node_row['Type']} ({node_row['Human_or_AI']})")
        st.markdown(f"**Description:** {node_row['Description']}")
        
        st.markdown("---")
        st.markdown("**Simulated Operational Load:**")
        
        sim_load = min(100, int(current_summary['Peak_Human_Oversight_Load_Pct'] + (10 if node_row['Governance_Layer'] == current_summary['Bottleneck_Type'] else -10)))
        sim_load = max(10, sim_load)
        
        st.progress(sim_load / 100, text=f"Oversight / Processing Demand: {sim_load}%")
        
        incoming = active_rels[active_rels['Target_ID'] == sel_id]
        outgoing = active_rels[active_rels['Source_ID'] == sel_id]
        
        st.markdown(f"**Connected Pathways:** {len(incoming)} Incoming, {len(outgoing)} Outgoing")
        
        if st.button("Clear Selection"):
            st.session_state['selected_node_id'] = None
            st.rerun()
    else:
        st.info("Select a node from the network map or dropdown above to inspect detailed governance metrics and active links.")

st.markdown("---")

# =========================================================================
# ZONE 4: BOTTOM CROSS-SCENARIO COMPARATIVE ANALYTICS DASHBOARD
# =========================================================================
st.markdown("#### 📊 Cross-Scenario Comparative Analytics (S1 — S5)")

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    fig_resp = go.Figure()
    fig_resp.add_trace(go.Scatter(
        x=summary_df['Scenario_Name'],
        y=summary_df['Mission_Response_Time_Sec'],
        mode='lines+markers',
        name='Response Time (s)',
        line=dict(color='#1F77B4', width=3),
        marker=dict(size=10)
    ))
    fig_resp.update_layout(
        title="Mission Response Time Trend (Seconds)",
        xaxis_title="Autonomy Scenario",
        yaxis_title="Seconds",
        plot_bgcolor='#0E1117',
        paper_bgcolor='#0E1117',
        font=dict(color='white'),
        height=320,
        margin=dict(t=30, b=30, l=30, r=30)
    )
    st.plotly_chart(fig_resp, use_container_width=True)

with col_chart2:
    fig_load = go.Figure()
    fig_load.add_trace(go.Bar(
        x=summary_df['Scenario_Name'],
        y=summary_df['Peak_Human_Oversight_Load_Pct'],
        name='Human Oversight Load (%)',
        marker_color='#2ECC71'
    ))
    fig_load.add_trace(go.Bar(
        x=summary_df['Scenario_Name'],
        y=summary_df['Peak_IT_System_Load_Pct'],
        name='IT System Load (%)',
        marker_color='#E74C3C'
    ))
    fig_load.update_layout(
        barmode='group',
        title="Human Oversight vs. IT System Workload Trade-off",
        xaxis_title="Autonomy Scenario",
        yaxis_title="Peak Load Percentage (%)",
        plot_bgcolor='#0E1117',
        paper_bgcolor='#0E1117',
        font=dict(color='white'),
        height=320,
        margin=dict(t=30, b=30, l=30, r=30)
    )
    st.plotly_chart(fig_load, use_container_width=True)