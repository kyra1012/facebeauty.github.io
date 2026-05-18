import streamlit as st
import plotly.graph_objects as go
import styles
from data_processor import data_service


def show():
    # 强制重置 .block-container 的样式，覆盖 Control_module 的全屏设置
    # 恢复正常的内边距和最大宽度，确保页面看起来“正常”
    st.markdown("""
        <style>
            .block-container {
                padding-top: 2rem !important;
                padding-bottom: 4rem !important;
                padding-left: 3rem !important;
                padding-right: 3rem !important;
                max-width: 100% !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # ================= 1. 标题区 =================
    st.markdown('<div class="section-header">🌏 全球审美分布 (Global Distribution)</div>', unsafe_allow_html=True)
    st.caption("3D 交互地球仪：拖拽可旋转查看全球数据，滚轮缩放查看细节。")

    # ================= 2. 数据准备 =================
    data = data_service.get_country_stats()

    # ================= 3. 构建 3D 地球仪 (Orthographic) =================
    fig = go.Figure()

    # 添加数据层 (气泡散点)
    fig.add_trace(go.Scattergeo(
        locations=data['Country_EN'],  # 匹配用的英文名
        locationmode='country names',
        text=data['Country_CN'],  # 悬停显示的中文名
        mode='markers',  # 散点模式

        # 气泡样式配置
        marker=dict(
            size=data['Faces'],  # 大小取决于上榜次数
            sizemode='area',  # 面积映射
            sizeref=2. * max(data['Faces']) / (50. ** 2),  # 缩放系数
            sizemin=4,  # 最小尺寸

            color=data['Faces'],  # 颜色映射
            colorscale='Purples',  # 品牌紫色系
            showscale=True,  # 显示颜色条
            colorbar=dict(
                title='上榜人次',
                thickness=15,
                len=0.6,
                x=0.9,
                tickfont=dict(color='#7E57C2')
            ),
            line=dict(width=1, color='rgba(255,255,255,0.9)')  # 描边
        ),

        # 自定义悬停提示 (HTML)
        hovertemplate=(
                "<b>%{text}</b><br>" +
                "🏆 全球排名: No.%{customdata[0]}<br>" +
                "✨ 上榜人次: %{marker.color}<br>" +
                "<extra></extra>"
        ),
        customdata=data[['Rank']]  # 传入排名数据
    ))

    # 配置地球仪外观
    fig.update_layout(
        height=700,
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',

        geo=dict(
            projection_type="orthographic",  # 3D 球体投影

            showland=True,
            landcolor="#F7F5FA",  # 陆地颜色

            showocean=True,
            oceancolor="rgba(209, 196, 233, 0.3)",  # 海洋颜色

            showcountries=True,
            countrycolor="rgba(126, 87, 194, 0.3)",  # 国界线

            showlakes=True,
            lakecolor="rgba(209, 196, 233, 0.3)",

            bgcolor='rgba(0,0,0,0)',  # 背景透明

            # 初始视角 (聚焦亚洲)
            projection_rotation=dict(lon=80, lat=20, roll=0),

            # 经纬网格
            lataxis_showgrid=True,
            lonaxis_showgrid=True,
            lataxis_gridcolor="rgba(0,0,0,0.05)",
            lonaxis_gridcolor="rgba(0,0,0,0.05)"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # ================= 4. 数据明细表 =================
    styles.draw_divider()
    st.markdown('<div class="section-header">📋 数据明细列表</div>', unsafe_allow_html=True)

    # 整理表格数据
    display_df = data[['Rank', 'Country_CN', 'Faces', 'Country_EN']].sort_values('Rank')
    display_df.columns = ['排名', '国家/地区', '上榜人次', 'English Name']

    st.dataframe(
        display_df,
        use_container_width=True,
        height=500,
        hide_index=True,
        column_config={
            "排名": st.column_config.NumberColumn(format="No. %d"),
            "上榜人次": st.column_config.ProgressColumn(
                format="%d 次",
                min_value=0,
                max_value=int(data['Faces'].max()),
            )
        }
    )