import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
import styles
from data_processor import data_service


# ================= 0. 全局样式定义 (统一标题) =================
def inject_custom_css():
    st.markdown("""
    <style>
        /* 定义统一的主标题样式 */
        .section-header {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 20px; 
            font-weight: 700;
            color: #453750;
            margin-bottom: 5px;
            padding-top: 10px;
            border-left: 5px solid #7E57C2; /* 左侧紫色竖条装饰 */
            padding-left: 10px;
        }
        /* 定义统一的副标题样式 */
        .section-caption {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 13px;
            color: #787085;
            margin-bottom: 15px;
            margin-left: 15px; /* 对齐 */
        }
        /* 移除Streamlit默认的某些边距 */
        .block-container {
            padding-top: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)


# ================= 1. 地图 (保持不变) =================
def create_interactive_map():
    data = data_service.get_country_stats()
    if data.empty:
        st.warning("⚠️ 暂无地图数据")
        return go.Figure(), data

    fig = px.scatter_geo(
        data,
        locations="Country_EN",
        locationmode='country names',
        size="Faces",
        hover_name="Country_CN",
        hover_data={"Faces": True, "Rank": True, "Country_EN": False},
        labels={"Faces": "上榜总人次", "Rank": "全球排名"},
        projection="natural earth",
        color="Faces",
        color_continuous_scale=["#E1BEE7", "#BA68C8", "#8E24AA"],
        size_max=45,
    )
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},  # 极致边距
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        geo=dict(bgcolor='rgba(0,0,0,0)', showland=True, landcolor="#F5F5F5", showocean=True,
                 oceancolor="rgba(237, 241, 255, 0.4)", showcountries=True, countrycolor="rgba(200,200,200,0.5)",
                 showcoastlines=False, showframe=False, projection_scale=1.1),
        dragmode="pan"
    )
    return fig, data


# ================= 2. 明星排行 (保持不变) =================
def create_top_stars_chart():
    df = data_service.get_top_stars()
    if df.empty: return go.Figure()

    # 1. 翻转数据
    df_reversed = df.iloc[::-1].reset_index(drop=True)
    count = len(df_reversed)

    # 2. 视觉长度
    step = 5
    min_len = 55
    visual_lens = [min_len + (i * step) for i in range(count)]
    df_reversed['Visual_Len'] = visual_lens

    # 3. 莫兰迪粉色系
    morandi_pinks = [
        '#E6A3B5', '#E098AD', '#DA8DA5', '#D4829D', '#CE7795',
        '#C86C8D', '#C26185', '#BC567D', '#B64B75', '#B0406D'
    ]
    colors = morandi_pinks[:count]

    fig = px.bar(
        df_reversed,
        x='Visual_Len',
        y='Star',
        orientation='h',
        custom_data=['Mentions', 'Best_Rank', 'Avg_Rank']
    )

    fig.update_traces(
        marker_color=colors,
        width=0.82, # 保持之前的粗细
        text=df_reversed['Star'],
        textposition='inside',
        insidetextanchor='start',
        textfont=dict(color='white', size=13, family="Plus Jakarta Sans", weight='bold'),
        texttemplate='&nbsp;<b>%{text}</b>',
        hovertemplate=(
            '<b>%{y}</b><br>'
            '✨ 上榜次数: %{customdata[0]}<br>'
            '🏆 最高排名: Top %{customdata[1]}<br>'
            '📊 平均排名: %{customdata[2]}<extra></extra>'
        )
    )

    fig.update_layout(
        margin=dict(l=0, r=20, t=0, b=0),
        xaxis=dict(showticklabels=False, title=None, showgrid=False, range=[0, 105]),
        yaxis=dict(showticklabels=False, title=None, showgrid=False),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=480, # 保持之前的拉伸高度
        showlegend=False
    )
    return fig


# ================= 3. 东西方占比 (保持不变) =================
def create_pie_chart():
    east, west = data_service.get_region_ratio()
    if east == 0 and west == 0: return go.Figure()
    fig = go.Figure(data=[go.Pie(labels=['东方 (Oriental)', '西方 (Western)'], values=[east, west], hole=.6,
                                 marker=dict(colors=['#AB47BC', '#F06292']), textinfo='percent', pull=[0, 0])])
    fig.update_traces(hoverinfo='label+percent', textfont_size=16, marker=dict(line=dict(color='white', width=2)))
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=True,
                      legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350)
    return fig


# ================= 4. 历年趋势 (保持不变) =================
def create_trend_line():
    trend = data_service.get_yearly_trend()
    if not trend['years']: return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend['years'], y=trend['east'], mode='lines+markers', name='东方占比',
                             line=dict(shape='spline', width=4, color='#AB47BC'),
                             marker=dict(size=8, opacity=0.8, line=dict(width=2, color='white'))))
    fig.add_trace(go.Scatter(x=trend['years'], y=trend['west'], mode='lines+markers', name='西方占比',
                             line=dict(shape='spline', width=4, color='#F06292'),
                             marker=dict(size=8, opacity=0.8, line=dict(width=2, color='white'))))
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(255,255,255,0.4)',
                      xaxis=dict(showgrid=False, color='#787085', tickmode='linear'),
                      yaxis=dict(showgrid=True, gridcolor='rgba(200,200,200,0.2)', color='#787085', ticksuffix='%'),
                      legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1), height=350,
                      hovermode="x unified")
    return fig


# ================= 5. 美人时间轴 (保持不变) =================
def render_beauty_timeline():
    db_json = data_service.get_timeline_data()
    html_code = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><script src="https://cdn.tailwindcss.com"></script><link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet"><style>body {{ font-family: 'Plus Jakarta Sans', sans-serif; background: transparent; }} .beauty-scroll::-webkit-scrollbar {{ height: 4px; }} .beauty-scroll::-webkit-scrollbar-thumb {{ background: #D1C4E9; border-radius: 4px; }} .timeline-card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 20px rgba(126, 87, 194, 0.15); }}</style></head><body class="p-2"><div class="flex flex-col space-y-4"><div class="flex justify-between items-center px-1"><span class="text-sm font-bold text-[#7E57C2] uppercase">Yearly Top 10</span><select id="year-select" onchange="renderCards(this.value)" class="bg-white/80 border border-purple-200 text-[#4A148C] py-1 pl-4 pr-8 rounded-full font-bold text-sm outline-none cursor-pointer"></select></div><div id="card-container" class="beauty-scroll flex space-x-4 overflow-x-auto pb-4 px-1 snap-x snap-mandatory min-h-[280px] items-center"></div></div><script>const db = {db_json}; const years = Object.keys(db).sort((a,b)=>b-a); const select = document.getElementById('year-select'); years.forEach(y => {{ const opt = document.createElement('option'); opt.value = y; opt.innerText = y + "年"; select.appendChild(opt); }}); function renderCards(year) {{ const container = document.getElementById('card-container'); container.innerHTML = ''; if(!db[year]) return; db[year].forEach(item => {{ const card = document.createElement('div'); card.className = "timeline-card snap-start flex-none w-[160px] bg-white rounded-xl overflow-hidden shadow border border-purple-50 group"; card.innerHTML = `<div class="relative h-[200px] bg-gray-100"><img src="${{item.img}}" class="w-full h-full object-cover"><div class="absolute top-2 left-2 w-7 h-7 bg-white/90 rounded-full flex items-center justify-center font-bold text-[#7E57C2] text-xs">${{item.rank}}</div></div><div class="p-3"><h3 class="font-bold text-[#453750] truncate text-sm">${{item.name}}</h3><div class="mt-1"><span class="text-[10px] text-gray-500 bg-purple-50 px-2 py-0.5 rounded-full border border-purple-100">${{item.country}}</span></div></div>`; container.appendChild(card); }}); }} if(years.length>0) renderCards(years[0]);</script></body></html>"""
    components.html(html_code, height=360)


# ================= 6. 冠军展示 (保持不变) =================
def render_carousel():
    champ_data = data_service.get_champion_gallery()
    slides = ""
    for item in champ_data:
        img_src = data_service.get_image_base64(item['img_path'])
        desc = item['desc']
        slides += f"""<div class="swiper-slide"><img src="{img_src}" /><div class="slide-year">{item['year']}</div><div class="slide-desc">{desc}</div></div>"""
    if not slides: slides = "<div style='text-align:center; padding:50px; color:#666;'>暂无冠军图片数据</div>"
    html_code = f"""<!DOCTYPE html><html><head><meta charset="utf-8"/><link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css" /><style>body {{ margin:0; overflow:hidden; }} .swiper {{ width:100%; padding:40px 0 60px; }} .swiper-slide {{ width:240px; height:340px; border-radius:16px; overflow:hidden; opacity:0.5; transition:all 0.3s; box-shadow:0 10px 25px rgba(0,0,0,0.15); }} .swiper-slide-active {{ opacity:1; transform:scale(1.1); z-index:10; box-shadow:0 20px 40px rgba(126,87,194,0.35); }} .swiper-slide img {{ width:100%; height:100%; object-fit:cover; }} .slide-year {{ position:absolute; bottom:40px; width:100%; text-align:center; color:white; font-weight:bold; text-shadow:0 2px 4px rgba(0,0,0,0.5); font-family:sans-serif; font-size: 24px; }} .slide-desc {{ position:absolute; bottom:0; width:100%; padding:8px; background:rgba(0,0,0,0.7); color:#fff; font-size:12px; text-align:center; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font-family:sans-serif; }}</style></head><body><div class="swiper mySwiper"><div class="swiper-wrapper">{slides}</div><div class="swiper-pagination"></div></div><script src="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js"></script><script>var swiper = new Swiper(".mySwiper", {{ effect:"coverflow", grabCursor:true, centeredSlides:true, slidesPerView:"auto", loop:true, coverflowEffect:{{ rotate:0, stretch:0, depth:100, modifier:1, slideShadows:true }}, pagination:{{ el:".swiper-pagination" }}, autoplay:{{ delay:2500 }} }});</script></body></html>"""
    components.html(html_code, height=480)


# ================= 页面布局 =================
def show():
    inject_custom_css()  # 注入CSS
    st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

    # 左右分栏
    col_left, col_right = st.columns([2, 1], gap="large")

    with col_left:
        # 1. 地图模块 (无框，只有标题)
        st.markdown('<div class="section-header">🌏 全球上榜分布 (Global Distribution)</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-caption">不同国家上榜人数的热力分布概览 / Heatmap overview of ranked faces by country.</div>',
            unsafe_allow_html=True)
        fig_map, _ = create_interactive_map()
        st.plotly_chart(fig_map, use_container_width=True, config={'displayModeBar': False})

        st.markdown('<div style="height:30px;"></div>', unsafe_allow_html=True)

        # 2. 明星排行 (无框，只有标题)
        st.markdown('<div class="section-header">👑 最强常驻面孔 (Most Frequent Stars)</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-caption">近十年上榜次数最多的面孔排行 / Top stars with most appearances in the decade.</div>',
            unsafe_allow_html=True)
        st.plotly_chart(create_top_stars_chart(), use_container_width=True, config={'displayModeBar': False})

    with col_right:
        # 3. 占比模块 (无框)
        st.markdown('<div class="section-header">🧩 东西方占比 (East-West Ratio)</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-caption">东西方审美偏好比例 / Oriental vs Western aesthetic ratio.</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(create_pie_chart(), use_container_width=True, config={'displayModeBar': False})

        styles.draw_divider()

        # 4. 国家 Top 10
        st.markdown('<div class="section-header">🔝 Top 10 国家 (Top Countries)</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-caption">上榜总人次最多的国家 / Countries with most total mentions.</div>',
                    unsafe_allow_html=True)

        top10 = data_service.get_country_stats().head(10)
        for idx, row in top10.iterrows():
            st.markdown(f"""
            <div class="interactive-row" style="padding: 4px 0; border-bottom: 1px solid #eee;">
                <div style="display:flex; align-items:center;">
                    <div style="background:#7E57C2; color:white; width:20px; height:20px; border-radius:50%; text-align:center; line-height:18px; font-size:12px; font-weight:bold; margin-right:12px;">{idx + 1}</div>
                    <span style="font-size:15px; font-weight:600; color:#453750;">{row['Country_CN']}</span>
                </div>
                <div style="font-size:15px; font-weight:700; color:#7E57C2;">{row['Faces']} 次</div>
            </div>""", unsafe_allow_html=True)

    # 5. 趋势模块 (无框)
    styles.draw_divider()
    st.markdown('<div class="section-header">📈 审美趋势演变 (Trend Evolution)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-caption">近十年东西方占比变化趋势 / 10-year trend of East-West aesthetic shifts.</div>',
        unsafe_allow_html=True)
    st.plotly_chart(create_trend_line(), use_container_width=True, config={'displayModeBar': False})

    # 6. 时间轴模块 (无框)
    styles.draw_divider()
    st.markdown('<div class="section-header">✨ 历年 Top 10 (Yearly Top 10)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-caption">每年评选出的最美十张面孔 / Top 10 most beautiful faces of each year.</div>',
        unsafe_allow_html=True)
    render_beauty_timeline()

    # 7. 冠军轮播 (无框)
    styles.draw_divider()
    st.markdown('<div class="section-header">🏆 十年冠军巡礼 (Decade Champions)</div>',unsafe_allow_html=True)
    st.markdown(
        '<div class="section-caption">历年登顶冠军风采回顾 / A gallery of the 1 champion face from each year.</div>',
        unsafe_allow_html=True)
    render_carousel()


if __name__ == "__main__":
    show()