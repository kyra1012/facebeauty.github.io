import streamlit as st
import plotly.graph_objects as go
import styles
from data_processor import data_service

def show():
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">🧩 审美构成 (Composition)</div>', unsafe_allow_html=True)
        east, west = data_service.get_region_ratio()
        fig_pie = go.Figure(data=[go.Pie(labels=['东方', '西方'], values=[east, west], hole=.6, marker=dict(colors=['#AB47BC', '#F06292']), textinfo='percent')])
        fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">📈 趋势演变 (Trend)</div>', unsafe_allow_html=True)
        trend = data_service.get_yearly_trend()
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=trend['years'], y=trend['east'], mode='lines+markers', name='东方', line=dict(color='#AB47BC')))
        fig_line.add_trace(go.Scatter(x=trend['years'], y=trend['west'], mode='lines+markers', name='西方', line=dict(color='#F06292')))
        fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.05)', height=400)
        st.plotly_chart(fig_line, use_container_width=True)