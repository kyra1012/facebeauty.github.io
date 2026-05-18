import streamlit as st
import styles
from data_processor import data_service
import streamlit.components.v1 as components
import json


def show():
    st.markdown('<div class="section-header">✨ 历年 Top 10 巡礼 (Yearly Gallery)</div>', unsafe_allow_html=True)
    st.caption("滑动查看每一年的前十名最美面孔 / Top 10 most beautiful faces of each year.")

    # 复用之前的时间轴逻辑，但这里是全屏展示
    db_json = data_service.get_timeline_data()

    html_code = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Plus Jakarta Sans', sans-serif; background: transparent; }}
            .beauty-scroll::-webkit-scrollbar {{ height: 6px; }}
            .beauty-scroll::-webkit-scrollbar-thumb {{ background: #EC407A; border-radius: 4px; }}
            .timeline-card {{ width: 200px; margin-right: 20px; transition: transform 0.3s; }}
            .timeline-card:hover {{ transform: translateY(-10px); }}
        </style>
    </head>
    <body class="p-4">
        <div class="flex justify-between items-center mb-4">
            <span class="text-lg font-bold text-[#7E57C2]">选择年份:</span>
            <select id="year-select" onchange="renderCards(this.value)" class="border-2 border-purple-200 text-[#4A148C] py-2 px-4 rounded-full font-bold outline-none cursor-pointer"></select>
        </div>
        <div id="card-container" class="beauty-scroll flex overflow-x-auto pb-8 snap-x snap-mandatory min-h-[350px] items-center"></div>

        <script>
            const db = {db_json};
            const years = Object.keys(db).sort((a,b)=>b-a);
            const select = document.getElementById('year-select');
            years.forEach(y => {{
                const opt = document.createElement('option'); opt.value = y; opt.innerText = y + "年"; select.appendChild(opt);
            }});

            function renderCards(year) {{
                const container = document.getElementById('card-container');
                container.innerHTML = '';
                if(!db[year]) return;

                db[year].forEach(item => {{
                    const card = document.createElement('div');
                    card.className = "timeline-card snap-start flex-none bg-white rounded-2xl overflow-hidden shadow-lg border border-pink-100 group";
                    card.innerHTML = `
                        <div class="relative h-[260px] bg-gray-100">
                            <img src="${{item.img}}" class="w-full h-full object-cover">
                            <div class="absolute top-2 left-2 w-8 h-8 bg-pink-500 text-white rounded-full flex items-center justify-center font-bold shadow-md">${{item.rank}}</div>
                        </div>
                        <div class="p-4 text-center">
                            <h3 class="font-bold text-gray-800 truncate text-lg">${{item.name}}</h3>
                            <div class="mt-1 text-sm text-purple-600 bg-purple-50 inline-block px-3 py-1 rounded-full">${{item.country}}</div>
                        </div>`;
                    container.appendChild(card);
                }});
            }}
            renderCards(years[0]);
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=600)