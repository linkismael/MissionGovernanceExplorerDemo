import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from pathlib import Path

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Mission Governance Explorer",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- COMPACT RESPONSIVE CSS STYLING ---
st.markdown("""
<style>
/* --- HIDE STREAMLIT TOP HEADER BAR & WHITE STRIP --- */
    header[data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
/* --- Background of overall dashboard colors --- */
    .stApp { background-color: #FFFFFF; color: #0E1117; }
    .block-container { 
        max-width: 100% !important; 
        padding-top: 1rem; 
        padding-bottom: 0.5rem; 
        padding-left: 1.5rem; 
        padding-right: 1.5rem; 
    }
/* --- color scenario tabs --- */
    /* Uniform Button Styling */
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
/* --- color for data tabs --- */
    /* --- TABS: Same color background, Red frame around active --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: #0E1117;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        background-color: #161B22 !important;
        border-radius: 6px;
        color: #C9D1D9 !important;
        font-weight: 600;
        font-size: 13px;
        border: 1px solid #30363D !important;
        padding: 0px 18px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #161B22 !important;
        border: 2px solid #FF4B4B !important;
        box-shadow: none !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- ROBUST DATA LOADING ---
BASE_DIR = Path(__file__).resolve().parent

@st.cache_data
def load_data():
    nodes_path = BASE_DIR / "data" / "AI_Mission_Governance_Nodes_v0_1.csv"
    rels_path = BASE_DIR / "data" / "AI_Mission_Governance_Relationships_v0_1.csv"
    summary_path = BASE_DIR / "scenario_summary.csv"
    
    if not nodes_path.exists():
        nodes_path = BASE_DIR / "AI_Mission_Governance_Nodes_v0_1.csv"
    if not rels_path.exists():
        rels_path = BASE_DIR / "AI_Mission_Governance_Relationships_v0_1.csv"
    if not summary_path.exists():
        summary_path = BASE_DIR / "scenario_summary.csv"

    nodes_df = pd.read_csv(nodes_path)
    rels_df = pd.read_csv(rels_path)
    summary_df = pd.read_csv(summary_path)
    return nodes_df, rels_df, summary_df

nodes_df, rels_df, summary_df = load_data()

# --- SESSION STATE INITIALIZATION ---
if 'active_scenario' not in st.session_state:
    st.session_state['active_scenario'] = 1
if 'selected_node_id' not in st.session_state:
    st.session_state['selected_node_id'] = None

active_scen_order = st.session_state['active_scenario']
current_summary = summary_df[summary_df['Scenario_Order'] == active_scen_order].iloc[0]
baseline_summary = summary_df[summary_df['Scenario_Order'] == 1].iloc[0]

# =========================================================================
# ZONE 1: TOP CONTROL BAR & GLOBAL KPI METRICS (Persistent across tabs)
# =========================================================================
# --- ZONE 1: TOP CONTROL BAR & GLOBAL KPI METRICS ---
st.markdown("## 🛡️ AI Mission Governance Explorer")

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
        is_active = (active_scen_order == scen_num)
        
        # Red accent indicator frame/bar for active scenario
        if is_active:
            st.markdown("<div style='height: 3px; background-color: #FF4B4B; border-radius: 2px; margin-bottom: 2px;'></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='height: 3px; background-color: transparent; margin-bottom: 2px;'></div>", unsafe_allow_html=True)
            
        if st.button(scen_label, key=f"btn_scen_{scen_num}"):
            if active_scen_order != scen_num:
                st.session_state['active_scenario'] = scen_num
                st.rerun()



# KPI Metric Cards
k1, k2, k3, k4 = st.columns(4)

resp_diff = int(current_summary['Mission_Response_Time_Sec'] - baseline_summary['Mission_Response_Time_Sec'])
esc_diff = int(current_summary['Human_Escalation_Count'] - baseline_summary['Human_Escalation_Count'])
gov_diff = int(current_summary['Peak_Human_Oversight_Load_Pct'] - baseline_summary['Peak_Human_Oversight_Load_Pct'])
it_diff = int(current_summary['Peak_IT_System_Load_Pct'] - baseline_summary['Peak_IT_System_Load_Pct'])

with k1:
    st.markdown(f"<span style='color: #161B22; font-size: 15px;'>Response:</span> <b style='color: #161B22; font-size: 15px;'>{current_summary['Mission_Response_Time_Sec']}s</b> <span style='color: #161B22; font-size: 15px;'>({resp_diff:+d}s)</span>", unsafe_allow_html=True)
with k2:
    st.markdown(f"<span style='color: #161B22; font-size: 15px;'>Escalations:</span> <b style='color: #161B22; font-size: 15px;'>{current_summary['Human_Escalation_Count']}</b> <span style='color: #161B22; font-size: 15px;'>({esc_diff:+d})</span>", unsafe_allow_html=True)
with k3:
    st.markdown(f"<span style='color: #161B22; font-size: 15px;'>Oversight Load:</span> <b style='color: #161B22; font-size: 15px;'>{current_summary['Peak_Human_Oversight_Load_Pct']}%</b> <span style='color: #161B22; font-size: 15px;'>({gov_diff:+d}%)</span>", unsafe_allow_html=True)
with k4:
    st.markdown(f"<span style='color: #161B22; font-size: 15px;'>IT Load:</span> <b style='color: #161B22; font-size: 15px;'>{current_summary['Peak_IT_System_Load_Pct']}%</b> <span style='color: #161B22; font-size: 15px;'>({it_diff:+d}%)</span>", unsafe_allow_html=True)


# =========================================================================
# TABBED ARCHITECTURE TO ELIMINATE VERTICAL SCROLLING -- 
# =========================================================================
tab_topology, tab_analytics = st.tabs(["🗺️ Governance Topology & Inspection", "📊 Cross-Scenario Comparative Analytics"])

active_nodes = nodes_df[
    (nodes_df['Scenario_Start_Order'] <= active_scen_order) & 
    (nodes_df['Scenario_End_Order'] >= active_scen_order)
]

active_rels = rels_df[
    (rels_df['Scenario_Start_Order'] <= active_scen_order) & 
    (rels_df['Scenario_End_Order'] >= active_scen_order)
]

with tab_topology:
    col_graph, col_inspect = st.columns([70, 30])

    with col_graph:
        st.markdown(f"#### 🌐︎ Topology Map — {current_summary['Scenario_Name']}")
        
        G = nx.DiGraph()
        for _, node in active_nodes.iterrows():
            G.add_node(node['ID'], label=node['Label'], layer=node['Layer_Order'], type=node['Governance_Layer'])
        for _, rel in active_rels.iterrows():
            if rel['Source_ID'] in G.nodes and rel['Target_ID'] in G.nodes:
                G.add_edge(rel['Source_ID'], rel['Target_ID'], type=rel['Type'])

        pos = {}
        layer_counts = active_nodes['Layer_Order'].value_counts().to_dict()
        layer_current_idx = {l: 0 for l in layer_counts.keys()}

        for node_id, data in G.nodes(data=True):
            layer = data['layer']
            total_in_layer = layer_counts.get(layer, 1)
            idx = layer_current_idx[layer]
            layer_current_idx[layer] += 1
            
            x_pos = (idx + 1) / (total_in_layer + 1)
            y_pos = 6 - layer
            pos[node_id] = (x_pos, y_pos)

        edge_x, edge_y = [], []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1.2, color='#777777'),
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
            
            if node_id == selected_node:
                node_color.append('#9C27B0')  # Purple for selected node
            elif node_data.get('Criticality') == 'High':
                node_color.append('#E74C3C')  # Red for High
            elif node_data.get('Criticality') == 'Medium':
                node_color.append('#F1C40F')  # Yellow for Medium
            else:
                node_color.append('#2ECC71')  # Green for Low (and default fallback)

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=[active_nodes[active_nodes['ID'] == nid]['Label'].values[0] for nid in G.nodes()],
            textposition="top center",
            hoverinfo='text',
            marker=dict(
                showscale=False,
                color=node_color,
                size=14,
                line=dict(width=2, color='#FFFFFF')
            )
            
        )

        fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        hovermode='closest',
                        autosize=True,
                        margin=dict(b=10, l=10, r=10, t=10),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 1]),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0.3, 5.7]),
                        plot_bgcolor='#FFFFFF',
                        paper_bgcolor='#0E1117',
                        height=540  # Perfectly proportioned to fit standard screens without scrolling
                    ))

        selected_point = st.plotly_chart(fig, use_container_width=True, on_select="rerun")
        
        node_ids_list = list(G.nodes())
        if selected_point and isinstance(selected_point, dict) and "selection" in selected_point and "point_indices" in selected_point["selection"]:
            indices = selected_point["selection"]["point_indices"]
            if indices:
                clicked_idx = indices[0]
                if clicked_idx < len(node_ids_list):
                    st.session_state['selected_node_id'] = node_ids_list[clicked_idx]

    with col_inspect:
        st.markdown("#### 🔍 Entity Inspection")
        
        node_options = {row['ID']: f"{row['ID']} - {row['Label']} ({row['Governance_Layer']})" for _, row in active_nodes.iterrows()}
        
        selected_dropdown = st.selectbox(
            "Select Node",
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
            
            st.markdown(f"**Entity:** {node_row['Label']}")
            st.markdown(f"**ID:** `{node_row['ID']}` | **Layer:** {node_row['Governance_Layer']}")
            st.markdown(f"**Type:** {node_row['Type']} ({node_row['Human_or_AI']})")
            st.markdown(f"**Desc:** {node_row['Description']}")
            
            st.markdown("---")
            sim_load = min(100, int(current_summary['Peak_Human_Oversight_Load_Pct'] + (10 if node_row['Governance_Layer'] == current_summary['Bottleneck_Type'] else -10)))
            sim_load = max(10, sim_load)
            
            st.progress(sim_load / 100, text=f"Oversight Demand: {sim_load}%")
            
            incoming = active_rels[active_rels['Target_ID'] == sel_id]
            outgoing = active_rels[active_rels['Source_ID'] == sel_id]
            st.markdown(f"**Pathways:** {len(incoming)} In, {len(outgoing)} Out")
            
            if st.button("Clear Selection"):
                st.session_state['selected_node_id'] = None
                st.rerun()
        else:
            st.info("Select a node from the map or dropdown to inspect its pathways.")

with tab_analytics:
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
            autosize=True,
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            font=dict(color='white'),
            height=400,
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
            autosize=True,
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            font=dict(color='white'),
            height=400,
            margin=dict(t=30, b=30, l=30, r=30)
        )
        st.plotly_chart(fig_load, use_container_width=True)

st.markdown("""
<div style='display: flex; justify-content: center; gap: 25px; background-color: #white; padding: 8px; border-radius: 6px; border: 1px solid #30363D; margin-top: 5px; font-size: 12px; color: #161B22;'>
    <span><span style='color: #2ECC71; font-size: 14px;'>●</span> <b>Low Criticality</b></span>
    <span><span style='color: #F1C40F; font-size: 14px;'>●</span> <b>Medium Criticality</b></span>
    <span><span style='color: #E74C3C; font-size: 14px;'>●</span> <b>High Criticality</b></span>
    <span><span style='color: #9C27B0; font-size: 14px;'>●</span> <b>Selected Node</b></span>
</div>
""", unsafe_allow_html=True)
# Deployment build sync - Oct 2026