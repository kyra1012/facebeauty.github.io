import streamlit as st
import plotly.express as px
import styles
from data_processor import data_service

def show():
    st.markdown('<div class="section-header">👑 明星榜单详情 (Ranking Detail)</div>', unsafe_allow_html=True)

    # 交互组件：筛选前N名
    limit = st.slider("显示前多少名 (Top N)", min_value=5, max_value=20, value=10, key="rank_slider")

    df = data_service.get_top_stars()
    df_show = df.head(limit).iloc[::-1].reset_index(drop=True)

    # 视觉长度计算
    count = len(df_show)
    step = 100 / count / 2
    visual_lens = [50 + (i * step) for i in range(count)]
    df_show['Visual_Len'] = visual_lens

    morandi_pinks = ['#E6A3B5', '#E098AD', '#DA8DA5', '#D4829D', '#CE7795', '#C86C8D', '#C26185', '#BC567D', '#B64B75', '#B0406D']
    colors = morandi_pinks[-count:] if count <= 10 else (['#E6A3B5'] * (count-10) + morandi_pinks)

    fig = px.bar(
        df_show, x='Visual_Len', y='Star', orientation='h',
        custom_data=['Mentions', 'Best_Rank', 'Avg_Rank']
    )
    fig.update_traces(
        marker_color=colors, width=0.6,
        text=df_show['Star'], textposition='inside', insidetextanchor='start',
        textfont=dict(color='white', size=14, weight='bold'),
        texttemplate='&nbsp;<b>%{text}</b>',
        hovertemplate='<b>%{y}</b><br>✨ 次数: %{customdata[0]}<br>🏆 最好: Top %{customdata[1]}<extra></extra>'
    )
    fig.update_layout(
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(showticklabels=False, showgrid=False),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=50 + (count * 40),
        margin=dict(l=0,r=0,t=0,b=0)
    )
    st.plotly_chart(fig, use_container_width=True)