import streamlit as st
import json
import pandas as pd
import os
import streamlit.components.v1 as components
from data_processor import data_service
import module_style
import importlib

# 强制重载样式模块
importlib.reload(module_style)


def show():
    # ================= 0. 动态获取路由与 UID =================
    current_uid = st.session_state.get("current_user_id", "guest")
    if current_uid != "guest":
        # 如果已登录，跳转链接死死绑定当前的 uid
        target_url = f"/?page=审美趋势&sub_view=dashboard&uid={current_uid}"
    else:
        target_url = "/?page=审美趋势&sub_view=dashboard"

    # ================= 1. 页面基础配置 =================
    st.markdown(f"""
        <style>
            .block-container {{ padding: 0 !important; max-width: 100% !important; }}
            footer {{display: none;}}
            iframe {{ height: 95vh !important; }}

            /* 导航旋钮 */
            #native-center-btn {{ 
                position: absolute; top: 450px; width: 110px; height: 110px; 
                background: #E1BEE7; border-radius: 50%; left: -25px; margin-top: -55px; 
                z-index: 999999; display: flex; justify-content: flex-end; align-items: center; 
                padding-right: 15px; box-sizing: border-box; 
                box-shadow: 5px 0 20px rgba(209, 196, 233, 0.4); 
                border: 3px solid #fff; transition: transform 0.2s, background 0.2s; 
                text-decoration: none !important; cursor: pointer;
            }}
            #native-center-btn:hover {{ transform: scale(1.05); background: #E8D3FC; }}
            #native-center-btn:active {{ background: #FFFFFF !important; transform: scale(0.95); }}
            #native-center-text {{ text-align: center; line-height: 1.2; color: #fff; font-weight: 900; font-size: 20px; width: 70px; font-family: 'Plus Jakarta Sans', sans-serif; }}
        </style>

        <a id="native-center-btn" href="{target_url}" target="_self">
            <div id="native-center-text">导航<br>旋钮</div>
        </a>
    """, unsafe_allow_html=True)

    # ================= 2. 数据准备区域 (严格恢复原逻辑) =================

    # --- 2.1 地图名称标准化 ---
    def normalize_name(name):
        n = name.strip().lower()
        if n in ['usa', 'united states of america', 'us', 'america']: return 'United States'
        if n in ['china', 'people\'s republic of china', 'prc']: return 'China'
        if n in ['uk', 'united kingdom', 'great britain']: return 'United Kingdom'
        if n in ['russia', 'russian federation']: return 'Russia'
        if n in ['south korea', 'korea, rep.', 'republic of korea', 'korea']: return 'Korea'
        if n in ['north korea', 'dem. rep. korea', 'dprk', 'korea, dem. rep.']: return 'Dem. Rep. Korea'
        if n in ['chad']: return 'Chad'
        if n in ['greenland']: return 'Greenland'
        if n in ['congo', 'republic of the congo']: return 'Congo'
        if n in ['dr congo', 'democratic republic of the congo', 'dem. rep. congo']: return 'Dem. Rep. Congo'
        return name.strip()

    csv_path = r"C:\Users\86153\Desktop\FaceBeautyProject\dataset\csv\country_mapping.csv"
    name_map_cn = {}
    if os.path.exists(csv_path):
        try:
            mapping_df = pd.read_csv(csv_path, encoding='utf-8')
            name_map_cn = dict(zip(mapping_df['ECharts_Name'], mapping_df['CN_Name']))
        except:
            try:
                mapping_df = pd.read_csv(csv_path, encoding='gbk')
                name_map_cn = dict(zip(mapping_df['ECharts_Name'], mapping_df['CN_Name']))
            except:
                pass

    name_map_cn.update({
        "Dem. Rep. Korea": "朝鲜", "Korea": "韩国", "United States": "美国", "United Kingdom": "英国",
        "Russian Federation": "俄罗斯", "Vietnam": "越南", "Lao PDR": "老挝", "Côte d'Ivoire": "科特迪瓦",
        "Czech Rep.": "捷克", "Central African Rep.": "中非共和国", "Dominican Rep.": "多米尼加",
        "French Guiana": "法属圭亚那", "Eq. Guinea": "赤道几内亚", "Falkland Is.": "福克兰群岛",
        "Chad": "乍得", "Greenland": "格陵兰", "Congo": "刚果(布)", "Dem. Rep. Congo": "刚果(金)"
    })

    stats_df = data_service.get_country_stats()
    max_count = int(stats_df['Faces'].max()) if not stats_df.empty else 50

    stats_dict = {}
    for _, row in stats_df.iterrows():
        raw_name = row['Country_EN']
        std_name = normalize_name(raw_name)
        stats_dict[std_name] = {'faces': int(row['Faces']), 'rank': row['Rank']}

    # --- 2.2 构建地图数据 (恢复灰度逻辑) ---
    map_data = []
    base_countries = set(name_map_cn.keys()) | set(stats_dict.keys())

    for echarts_name in base_countries:
        cn_name = name_map_cn.get(echarts_name, echarts_name)
        if echarts_name in stats_dict:
            info = stats_dict[echarts_name]
            map_data.append({
                "name": echarts_name, "value": info['faces'], "cn_name": cn_name, "rank": info['rank'], "has_data": True
            })
        else:
            # 【恢复】这里确保了没数据的国家显示为灰色
            map_data.append({
                "name": echarts_name, "value": 0, "cn_name": cn_name, "rank": "-", "has_data": False,
                "itemStyle": {"areaColor": "#EEEEEE", "borderColor": "#FFFFFF", "color": "#EEEEEE"}
            })

    # --- 2.3 Top 10 气泡数据 (恢复布局所需数据) ---
    top10_df = stats_df.head(10)
    cream_colors = ['#FFC4C4', '#E1BEE7', '#C8E6C9', '#FFF9C4', '#B3E5FC', '#FFCCBC', '#D7CCC8', '#F0F4C3', '#E0E0E0',
                    '#B2DFDB']
    bubble_items = []
    for i, (_, row) in enumerate(top10_df.iterrows()):
        bubble_items.append({
            "name": row['Country_CN'],
            "value": int(row['Faces']),
            "rank": i + 1,
            "color": cream_colors[i % len(cream_colors)]
        })

    # --- 2.4 旭日图数据 (恢复完整逻辑) ---
    east_keywords = ['中国', '韩国', '日本', '泰国', '越南', '菲律宾', '台湾', '马来西亚', '印度', '新加坡', '老挝',
                     '缅甸', '柬埔寨', '朝鲜', '蒙古', '印尼']

    east_items = []
    west_items = []

    for _, row in stats_df.iterrows():
        c_name = row['Country_CN']
        c_val = int(row['Faces'])
        node = {"name": c_name, "value": c_val}
        is_east = False
        for k in east_keywords:
            if k in c_name:
                is_east = True;
                break
        if is_east:
            east_items.append(node)
        else:
            west_items.append(node)

    details_map = {}

    def process_group(items, region_name):
        items.sort(key=lambda x: x['value'], reverse=True)
        main = []
        others = []
        for item in items:
            if item['value'] > 10:
                main.append(item)
            else:
                others.append(item)

        if others:
            total = sum(i['value'] for i in others)
            key = f"其他({region_name})"
            main.append({"name": "其他", "value": total, "key": key})
            details_map[key] = others

        return main

    final_east = process_group(east_items, "东方")
    final_west = process_group(west_items, "西方")

    sunburst_data = [
        {"name": "东方", "children": final_east},
        {"name": "西方", "children": final_west}
    ]

    # --- 2.5 【新增】花朵图详细数据 ---
    raw_df = data_service.df
    COL_NAME = '姓名'
    COL_COUNTRY = '国家/地区'
    COL_RANK = '排名'

    # 获取 Top Stars
    rank_df_simple = data_service.get_top_stars()
    top_names = rank_df_simple['Star'].head(10).tolist()

    # 视觉大小：No.1=100 ... No.10=55
    visual_steps = [100, 95, 90, 85, 80, 75, 70, 65, 60, 55]

    bar_details_list = []
    for i, name in enumerate(top_names):
        star_records = raw_df[raw_df[COL_NAME] == name]
        if not star_records.empty:
            country_en = star_records[COL_COUNTRY].iloc[0]
            country_cn = name_map_cn.get(normalize_name(country_en), country_en)
            best_rank = int(star_records[COL_RANK].min())
            avg_rank = round(star_records[COL_RANK].mean(), 1)
            mentions = int(len(star_records))

            bar_details_list.append({
                "rank_sort": i + 1,
                "name": name,
                "value": mentions,
                "visual_val": visual_steps[i],  # 视觉权重
                "country": country_cn,
                "best": best_rank,
                "avg": avg_rank
            })

    bar_details_list.sort(key=lambda x: x['rank_sort'])

    # --- 2.6 其他常规数据 (修改：Timeline 按年份分组) ---
    rank_df = data_service.get_top_stars().iloc[::-1]
    trend = data_service.get_yearly_trend()

    timeline_raw = json.loads(data_service.get_timeline_data())
    # 重构 timeline 数据结构为 { "2023": [items...], "2024": [items...] }
    timeline_grouped = {}

    # 确保年份排序
    sorted_years = sorted(timeline_raw.keys(), reverse=True)

    for year in sorted_years:
        items = timeline_raw[year]
        # 确保按排名排序 1-10
        items.sort(key=lambda x: int(x['rank']))
        # 只取前10
        items = items[:10]

        processed_items = []
        for item in items:
            img = item['img'] if item['img'] else ""
            # 如果是本地路径需要转 base64，如果是 URL 则保持（此处假设 data_service 已处理或前端能读取）
            processed_items.append({
                "name": item['name'],
                "rank": item['rank'],
                "country": item['country'],
                "img": img
            })
        timeline_grouped[str(year)] = processed_items

    champions_raw = data_service.get_champion_gallery()
    champions = []
    champions_raw.sort(key=lambda x: x['year'])

    for c in champions_raw:
        img = c['img_path']
        if not img.startswith('data:') and not img.startswith('http'):
            img = data_service.get_image_base64(img)

            display_text = f"{c['year']}年冠军：{c['desc']}"

            champions.append({
                "year": str(c['year']),
                "text": display_text,  # 专门用于显示的完整文字
                "img": img
            })

    chart_data = {
        "map": map_data,
        "max_value": max_count,
        "top10": {"items": bubble_items, "max_val": int(top10_df['Faces'].max())},
        "sunburst": sunburst_data,
        "sunburst_details": details_map,
        "bar": {"names": rank_df['Star'].tolist(), "values": [int(x) for x in rank_df['Mentions']]},
        "bar_details": bar_details_list,
        "line": {"years": [str(y) for y in trend['years']], "east": [float(x) for x in trend['east']],
                 "west": [float(x) for x in trend['west']]},
        # 修改这里：传递分组后的 timeline 数据和年份列表
        "timeline_data": timeline_grouped,
        "timeline_years": sorted_years,
        "champions": champions
    }

    chart_data_json = json.dumps(chart_data, ensure_ascii=False)

    # 获取 HTML 字符串
    html_code = module_style.get_main_html(chart_data_json)

    # 渲染组件
    components.html(html_code, height=950, scrolling=False)