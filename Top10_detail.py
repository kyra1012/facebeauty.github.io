import streamlit as st
import plotly.express as px
import styles
from data_processor import data_service


def show():
    st.markdown('<div class="section-header">🔝 Top 10 国家 (Top Countries)</div>', unsafe_allow_html=True)
    st.caption("上榜总人次最多的国家 / Countries with most total mentions.")

    top5 = data_service.get_country_stats().head(5)

    # 交互：点击柱子查看详情
    fig = px.bar(
        top5, x='Country_CN', y='Faces',
        text='Faces', color='Faces',
        color_continuous_scale=['#E1BEE7', '#BA68C8', '#8E24AA']
    )
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    fig.update_layout(
        xaxis_title="国家/地区", yaxis_title="上榜总人次",
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📊 详细数据")
    for idx, row in top5.iterrows():
        st.markdown(f"""
        <div class="interactive-row">
            <div style="display:flex; align-items:center;">
                <div style="background:#7E57C2; color:white; width:28px; height:28px; border-radius:50%; text-align:center; line-height:28px; font-weight:bold; margin-right:15px;">{idx + 1}</div>
                <span style="font-size:16px; font-weight:600; color:#453750;">{row['Country_CN']}</span>
                <span style="margin-left:auto; font-weight:bold; color:#EC407A;">{row['Faces']} 次</span>
            </div>
        </div>""", unsafe_allow_html=True)