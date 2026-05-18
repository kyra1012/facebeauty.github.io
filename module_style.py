# module_style.py
# 视觉模板文件：包含 CSS 和 HTML/JS 结构

def get_main_html(chart_data_json):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/echarts/map/js/world.js"></script>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css" />
        <script src="https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;700;900&display=swap" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&display=swap" rel="stylesheet">

        <style>
            :root {{
                --bg-gradient: transparent; 
                --text-color: #5D5D5D;
                --primary: #F48FB1; 
                --secondary: #CE93D8; 
                --btn-inactive: #E0E0E0;
                --btn-center: #E1BEE7; 
            }}
            body {{ margin: 0; padding: 0; background: var(--bg-gradient); font-family: 'Plus Jakarta Sans', 'Noto Sans SC', sans-serif; color: var(--text-color); overflow: hidden; width: 100%; height: 100vh; position: relative; user-select: none; }}

            /* ================= Loading ================= */
            #loader-overlay {{
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: transparent; z-index: 9999;
                display: flex; flex-direction: column; justify-content: center; align-items: center;
                transition: opacity 0.6s ease-out; pointer-events: none;
            }}
            .loader-spinner {{
                width: 50px; height: 50px; border: 4px solid rgba(244, 143, 177, 0.3);
                border-top: 4px solid #F48FB1; border-radius: 50%;
                animation: spin 1s linear infinite; margin-bottom: 20px;
                box-shadow: 0 0 20px rgba(255, 255, 255, 0.5); 
            }}
            .loader-text {{
                font-size: 18px; font-weight: 900; color: #880E4F; letter-spacing: 1px;
                animation: pulse 1.5s ease-in-out infinite;
                text-shadow: 0 2px 10px rgba(255, 255, 255, 0.8);
            }}
            @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            @keyframes pulse {{ 0%, 100% {{ opacity: 0.6; }} 50% {{ opacity: 1; }} }}

            #chart-map, #chart-pie {{ width: 100%; height: 100%; }}

            /* 背景圆环 */
            #orbit-wrapper {{ position: fixed; width: 680px; height: 680px; left: -515px; top: 50%; margin-top: -325px; z-index: 10; pointer-events: none; }}
            #orbit-ring {{ width: 100%; height: 100%; border-radius: 50%; border: 8px solid rgba(209, 196, 233, 0.15); position: relative; transform-origin: center center; transition: transform 0.8s cubic-bezier(0.2, 0.8, 0.2, 1); pointer-events: auto; }}

            #interaction-zone {{ position: fixed; top: 0; left: 0; width: 300px; height: 100%; z-index: 200; cursor: grab; }}

            /* 导航文字 */
            .nav-item {{ position: absolute; top: 50%; left: 50%; width: 325px; height: 0; transform-origin: left center; display: flex; align-items: center; justify-content: flex-end; cursor: pointer; }}
            .nav-content {{ position: absolute; right: -180px; width: 250px; display: flex; align-items: center; gap: 10px; transform-origin: -15px center; transition: all 0.3s; opacity: 0.5; }}
            .nav-item.active .nav-content {{ opacity: 1; transform: scale(1.05); }}
            .nav-text {{ font-size: 15px; font-weight: 700; color: var(--btn-inactive); white-space: nowrap; }}
            .nav-item.active .nav-text {{ color: var(--secondary); font-size: 22px; font-weight: 900; text-shadow: 0 2px 10px rgba(126, 87, 194, 0.1); }}
            .nav-dot {{ width: 8px; height: 8px; background: var(--btn-inactive); border-radius: 50%; transition: 0.3s; }}
            .nav-item.active .nav-dot {{ width: 16px; height: 16px; background: var(--primary); box-shadow: 0 0 0 5px rgba(248, 187, 208, 0.4); }}

            #inner-circle {{ position: fixed; width: 400px; height: 400px; background: rgba(255,255,255,0.4); backdrop-filter: blur(10px); border-radius: 50%; left: -405px; top: 50%; margin-top: -200px; z-index: 95; border: 1px solid rgba(255,255,255,0.5); pointer-events: none; }}
            #content-stage {{ position: absolute; top: 0; right: 0; bottom: 0; left: 140px; padding: 10px; display: flex; align-items: center; justify-content: center; }}

            .page-section {{ position: absolute; width: 95%; height: 95%; opacity: 0; transform: translateY(30px); transition: all 0.6s cubic-bezier(0.2, 0.8, 0.2, 1); pointer-events: none; visibility: hidden; display: flex; flex-direction: column; }}
            .page-section.active {{ opacity: 1; transform: translateY(0); pointer-events: all; visibility: visible; }}

            .chart-box {{ flex: 1; width: 100%; min-height: 400px; background: rgba(255,255,255,0.25); border-radius: 20px; padding: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.02); border: 1px solid rgba(255, 255, 255, 0.4); position: relative; }}
            .page-header {{ margin-bottom: 5px; flex-shrink: 0; display: flex; justify-content: space-between; align-items: flex-end; }}
            .page-title {{ font-size: 28px; font-weight: 900; color: var(--text-color); border-left: 6px solid var(--primary); padding-left: 15px; }}
            .page-sub {{ font-size: 13px; color: #9E9E9E; margin-left: 25px; margin-top: 5px; }}

            /* 气泡图相关 */
            #bubble-container {{ width: 100%; height: 100%; position: relative; overflow: hidden; }}
            .bubble {{ position: absolute; border-radius: 50%; display: flex; flex-direction: column; justify-content: center; align-items: center; color: #555; cursor: pointer; transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.27), box-shadow 0.3s ease, z-index 0s; animation: float 6s ease-in-out infinite; will-change: transform; border: 1px solid rgba(255,255,255,0.4); }}
            .bubble::after {{ content: ''; position: absolute; top: 8%; left: 10%; width: 50%; height: 35%; border-radius: 50%; background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0) 70%); transform: rotate(-45deg); opacity: 0.9; pointer-events: none; }}
            .bubble:hover {{ z-index: 9999 !important; animation-play-state: paused; transform: scale(1.15) !important; box-shadow: 0 0 0 8px rgba(255, 255, 255, 0.3), 0 0 40px rgba(255, 255, 255, 0.6), inset 0 0 20px rgba(255, 255, 255, 0.3); }}
            .bubble-rank {{ font-size: 12px; font-weight: 800; color: rgba(80, 80, 80, 0.5); margin-bottom: 2px; }}
            .bubble-name {{ font-size: 14px; font-weight: 800; color: #5d4037; pointer-events: none; z-index: 10; margin-bottom: 2px; }}
            .bubble-value {{ font-size: 18px; font-weight: 900; color: #333; pointer-events: none; z-index: 10; }}
            @keyframes float {{ 0% {{ transform: translateY(0px) rotate(0deg); }} 50% {{ transform: translateY(-8px) rotate(1deg); }} 100% {{ transform: translateY(0px) rotate(0deg); }} }}

            /* Swiper 通用 */
            .swiper {{ width: 100%; height: 100%; padding: 20px 0; }}

            /* ================= Page 5: 历年图鉴样式 ================= */
            #year-selector-container {{ position: absolute; right: 20px; top: 0px; display: flex; align-items: center; gap: 10px; z-index: 100; }}
            #year-label {{ font-size: 55px; font-weight: 900; color: #b6a6dd; line-height: 1; pointer-events: none; position: absolute; right: 95px; top: -10px; white-space: nowrap; transition: 0.5s; }}
            .year-btn {{ padding: 6px 12px; border-radius: 20px; border: 1px solid var(--secondary); background: rgba(255,255,255,0.5); color: var(--secondary); font-weight: 800; cursor: pointer; transition: 0.3s; font-size: 13px; }}
            .year-btn:hover {{ background: var(--secondary); color: #fff; }}

            #timeline-stage {{ width: 100%; height: 100%; position: relative; display: flex; justify-content: center; align-items: center; perspective: 1000px; overflow: hidden; }}
            .year-layer {{ position: absolute; width: 100%; height: 100%; top: 0; left: 0; opacity: 0; pointer-events: none; transform: translateY(50px) scale(0.95); transition: all 0.8s cubic-bezier(0.2, 0.8, 0.2, 1); }}
            .year-layer.active-year {{ opacity: 1; pointer-events: auto; transform: translateY(0) scale(1); }}
            .year-layer.prev-year {{ opacity: 0; transform: translateY(-50px) scale(0.95); }}
            .year-layer.next-year {{ opacity: 0; transform: translateY(50px) scale(0.95); }}

            .rank-card {{ position: absolute; background: #FFFFFF; border-radius: 12px; box-shadow: 0 10px 25px rgba(220, 190, 220, 0.25); overflow: hidden; display: flex; flex-direction: column; transform-origin: center; transition: transform 0.4s ease, box-shadow 0.4s ease; width: 135px; height: 180px; }}
            .rank-card:hover {{ z-index: 999 !important; box-shadow: 0 15px 35px rgba(244, 143, 177, 0.4); }}
            .card-img-box {{ width: 100%; height: 72%; position: relative; overflow: hidden; }}
            .card-img-box img {{ width: 100%; height: 100%; object-fit: cover; transition: 0.5s; }}
            .rank-card:hover .card-img-box img {{ transform: scale(1.05); }}
            .rank-badge {{ position: absolute; top: 8px; left: 8px; width: 24px; height: 24px; background: #FFFFFF; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 14px; font-weight: 900; color: #7E57C2; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }}
            .rank-badge.top3 {{ color: #EC407A; box-shadow: 0 2px 10px rgba(236, 64, 122, 0.3); }}
            .card-info {{ width: 100%; height: 28%; background: #fff; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 0 5px; box-sizing: border-box; }}
            .card-name {{ font-size: 13px; font-weight: 800; color: #453750; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%; line-height: 1.2; }}
            .card-sub {{ font-size: 10px; color: #9E9E9E; margin-top: 2px; display: flex; gap: 4px; align-items: center; }}
            .card-country-tag {{ padding: 1px 6px; background: #F3E5F5; border-radius: 8px; color: #8E24AA; font-weight: 700; font-size: 9px; }}
            .scroll-hint-overlay {{ position: absolute; bottom: 10px; right: 20px; font-size: 12px; color: #CE93D8; font-weight: 700; opacity: 0.6; pointer-events: none; animation: pulse 2s infinite; }}

            /* ========================================================= */
            /* Page 6: 冠军巡礼 (高级弧形舞台版) - CLEAN REVISED */
            /* ========================================================= */

            /* 核心视口：限制宽度，防止遮挡左侧旋钮 */
            #stage-viewport {{
                width: 82%; 
                height: 100%;
                margin: 0 auto; 
                position: relative;
                overflow: hidden; 
                display: flex; 
                flex-direction: column; 

                /* [修改点] 改为 flex-start 配合 padding-top 实现下移 */
                justify-content: flex-start; 
                padding-top: 20vh; /* 控制下移距离，调整此数值改变高度 */

                perspective: 1500px;
            }}

            /* 舞台地台 (光影效果) */
            #stage-floor {{
                position: absolute; 
                bottom: 80px; left: 50%; transform: translateX(-50%);
                width: 120%; height: 300px;
                background: radial-gradient(ellipse at center, rgba(244, 143, 177, 0.25) 0%, rgba(206, 147, 216, 0.05) 50%, transparent 70%);
                pointer-events: none;
                z-index: 0;
            }}

            /* Swiper 容器定制 */
            .champSwiper {{
                width: 100%;
                padding-top: 40px;
                padding-bottom: 60px;
                /* 让 slide 可以显示 3D 效果 */
                transform-style: preserve-3d; 
            }}

            /* 冠军卡片 (3:4 比例) */
            .champ-slide {{
                width: 240px;  /* 宽度 */
                height: 320px; /* 高度 3:4 */
                border-radius: 12px;
                background: #fff;
                position: relative;
                /* 倒影效果 (高级感来源) */
                -webkit-box-reflect: below 10px linear-gradient(transparent 60%, rgba(255,255,255,0.3));
                box-shadow: 0 10px 20px rgba(0,0,0,0.1);
                transition: 0.3s;
            }}

            .champ-img {{
                width: 100%; height: 100%;
                object-fit: cover;
                border-radius: 12px;
                display: block;
            }}

            /* 悬停效果 */
            .champ-slide:hover {{
                box-shadow: 0 0 25px rgba(244, 143, 177, 0.8);
                border: 2px solid #F8BBD0;
                z-index: 999; /* 悬停时层级最高 */
            }}

            /* 图片文字遮罩 */
            .champ-overlay {{
                position: absolute; bottom: 0; left: 0; width: 100%; height: 50%;
                background: linear-gradient(to top, rgba(69, 55, 80, 0.9) 0%, transparent 100%);
                border-bottom-left-radius: 12px; border-bottom-right-radius: 12px;
                display: flex; flex-direction: column; justify-content: flex-end;
                padding: 15px; box-sizing: border-box;
                pointer-events: none;
            }}
            .champ-year {{
                color: #F48FB1; font-size: 12px; font-weight: 900; letter-spacing: 2px;
                margin-bottom: 2px; text-transform: uppercase;
            }}
            .champ-text {{
                color: #fff; font-size: 15px; font-weight: 700;
                text-shadow: 0 2px 4px rgba(0,0,0,0.5);
                line-height: 1.2;
            }}

        </style>
    </head>
    <body>
        <div id="loader-overlay">
            <div class="loader-spinner"></div>
            <div class="loader-text">正在加载中，请稍等...</div>
        </div>

        <div id="interaction-zone"></div>
        <div id="orbit-wrapper"><div id="orbit-ring"></div></div>
        <div id="inner-circle"></div>

        <div id="content-stage">
            <div id="page-0" class="page-section active"><div class="page-header"><div class="page-title">全球分布</div><div class="page-sub">不同国家上榜人数分布概览</div></div><div class="chart-box" id="chart-map" style="background: none; box-shadow: none; border: none;"></div></div>
            <div id="page-1" class="page-section"><div class="page-header"><div class="page-title">霸榜国家</div><div class="page-sub">上榜总人次最多的 Top 10 国家</div></div><div class="chart-box" id="chart-top10" style="background: none; box-shadow: none; border: none;"><div id="bubble-container"></div></div></div>
            <div id="page-2" class="page-section"><div class="page-header"><div class="page-title">东西占比</div><div class="page-sub">全球百大面孔文化背景比例 (点击'其他'展开详细)</div></div><div class="chart-box" id="chart-pie" style="background: none; box-shadow: none; border: none;"></div></div>
            <div id="page-3" class="page-section"><div class="page-header"><div class="page-title">霸榜人物</div><div class="page-sub">近十年常驻面孔综合排名（排名按照上榜次数>最高名次>平均排名规则排序）</div></div><div class="chart-box" id="chart-bar" style="background: none; box-shadow: none; border: none;"></div></div>
            <div id="page-4" class="page-section"><div class="page-header"><div class="page-title">趋势折线</div><div class="page-sub">2016-2025年东西方审美占比变化</div></div><div class="chart-box" id="chart-line"></div></div>

            <div id="page-5" class="page-section">
                <div class="page-header">
                    <div>
                        <div class="page-title">历年图鉴</div>
                        <div class="page-sub">历年 Top 10 最美面孔展示 (在此区域上下滚动切换年份)</div>
                    </div>
                    <div id="year-selector-container">
                        <div id="year-label"></div>
                        <select id="year-select-dropdown" style="padding: 8px 15px; border-radius: 15px; border: 1px solid #D8b8d6; outline: none; color: #b6a6dd; font-weight: bold;">
                        </select>
                    </div>
                </div>
                <div class="chart-box" id="timeline-chart-box" style="background:none; box-shadow:none; border:none; position:relative;">
                    <div id="timeline-stage"></div>
                    <div class="scroll-hint-overlay">↕ 滚动鼠标或滑动切换年份 ↕</div>
                </div>
            </div>

            <div id="page-6" class="page-section">
                <div id="stage-viewport">

                    <div id="stage-floor"></div>

                    <div class="swiper champSwiper">
                        <div class="swiper-wrapper" id="champion-wrapper"></div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const data = {chart_data_json};

            // Loading 移除
            window.addEventListener('load', function() {{
                const loader = document.getElementById('loader-overlay');
                setTimeout(() => {{
                    if(loader) {{
                        loader.style.opacity = '0';
                        setTimeout(() => {{ loader.style.display = 'none'; }}, 600); 
                    }}
                }}, 500);
            }});

            const MENU_ITEMS = ["地图分布", "霸榜国家", "东西占比", "霸榜人物", "趋势折线", "历年图鉴", "冠军巡礼"];
            const TOTAL = MENU_ITEMS.length;
            const ANGLE_STEP = 360 / TOTAL; 
            let globalIndex = 0; 
            let charts = [];

            const rankMap = {{}};
            if (data.map) {{
                data.map.forEach(item => {{ if(item.cn_name && item.rank) {{ rankMap[item.cn_name] = item.rank; }} }});
            }}

            const ring = document.getElementById('orbit-ring');
            MENU_ITEMS.forEach((item, index) => {{
                const div = document.createElement('div');
                div.className = 'nav-item';
                div.innerHTML = `<div class="nav-content"><div class="nav-text">${{item}}</div><div class="nav-dot"></div></div>`;
                div.onclick = () => jumpToSpecificItem(index);
                div.style.transform = `rotate(${{index * ANGLE_STEP}}deg)`;
                const content = div.querySelector('.nav-content');
                content.style.transform = `rotate(${{-index * ANGLE_STEP}}deg)`;
                ring.appendChild(div);
            }});

            const navItems = document.querySelectorAll('.nav-item');
            const sections = document.querySelectorAll('.page-section');

            function updateRotation() {{
                const targetRingAngle = -1 * (globalIndex * ANGLE_STEP);
                ring.style.transform = `rotate(${{targetRingAngle}}deg)`;
                const activeIndex = ((globalIndex % TOTAL) + TOTAL) % TOTAL;
                navItems.forEach((item, i) => {{
                    const content = item.querySelector('.nav-content');
                    const totalAngle = targetRingAngle + (i * ANGLE_STEP);
                    content.style.transform = `rotate(${{-totalAngle}}deg)`;
                    if(i === activeIndex) item.classList.add('active'); else item.classList.remove('active');
                }});
                sections.forEach(sec => sec.classList.remove('active'));
                const activeSec = document.getElementById('page-' + activeIndex);
                if(activeSec) activeSec.classList.add('active');
                setTimeout(resizeCharts, 400);
            }}

            function jumpToSpecificItem(targetIndex) {{
                const currentIndex = ((globalIndex % TOTAL) + TOTAL) % TOTAL;
                let diff = targetIndex - currentIndex;
                if (diff > TOTAL / 2) diff -= TOTAL;
                if (diff < -TOTAL / 2) diff += TOTAL;
                globalIndex += diff;
                updateRotation();
            }}

            function renderBubbleChart() {{
                const container = document.getElementById('bubble-container');
                container.innerHTML = ''; 
                const items = data.top10.items;
                const maxVal = data.top10.max_val;
                const layout = [{{l: 25, t: 23}}, {{l: 55, t: 30}}, {{l: 10, t: 5}}, {{l: 75, t: 8}}, {{l: 45, t: 65}}, {{l: 10, t: 55}}, {{l: 75, t: 70}}, {{l: 55, t: 5}}, {{l: 25, t: 70}}, {{l: 85, t: 40}}];
                items.forEach((item, index) => {{
                    const val = item.value;
                    const size = 115 + (val / maxVal) * 250; 
                    const bubble = document.createElement('div');
                    bubble.className = 'bubble';
                    bubble.style.width = size + 'px';
                    bubble.style.height = size + 'px';
                    bubble.style.background = `radial-gradient(circle at 30% 30%, #FFFFFF 10%, ${{(item.color)}} 80%)`;
                    bubble.style.boxShadow = `0 15px 35px rgba(0,0,0,0.05), inset -10px -10px 20px rgba(0,0,0,0.02)`;
                    const pos = layout[index] || {{l: Math.random()*80, t: Math.random()*80}};
                    bubble.style.left = pos.l + '%';
                    bubble.style.top = pos.t + '%';
                    bubble.style.animationDelay = (Math.random() * 3) + 's';
                    bubble.style.animationDuration = (5 + Math.random() * 3) + 's';
                    const fontSizeScale = 0.8 + (val / maxVal) * 0.6;
                    bubble.innerHTML = `<div class="bubble-rank" style="transform:scale(${{fontSizeScale}})">No.${{item.rank}}</div><div class="bubble-name" style="transform:scale(${{fontSizeScale}})">${{item.name}}</div><div class="bubble-value" style="transform:scale(${{fontSizeScale}})">${{val}}</div>`;
                    container.appendChild(bubble);
                }});
            }}

            try {{
                const cMap = echarts.init(document.getElementById('chart-map'));
                cMap.setOption({{
                    tooltip: {{ trigger: 'item', backgroundColor: 'rgba(255, 255, 255, 0.95)', borderColor: '#7E57C2', textStyle: {{ color: '#453750' }}, formatter: function(params) {{ if (params.componentType === 'series') {{ const cnName = (params.data && params.data.cn_name) ? params.data.cn_name : params.name; if (params.data && params.data.has_data) {{ return `<div style="text-align:center; margin-bottom:5px; font-weight:bold; color:#EC407A; font-size:16px;">${{cnName}}</div>` + `<div style="font-size:12px; color:#666; line-height:1.5;">` + `🌍 排名: No.${{params.data.rank}}<br/>` + `✨ 上榜人次: ${{params.data.value}} 位` + `</div>`; }} else {{ return `<div style="text-align:center; font-weight:bold; color:#555;">${{cnName}}</div><div style="margin-top:5px; font-size:12px; color:#999;">很遗憾，该国家/地区<br>近十年暂时无上榜数据</div>`; }} }} return params.name; }} }}, 
                    visualMap: {{ type: 'continuous', min: 1, max: data.max_value || 50, left: 'left', bottom: '20px', text: ['人多', '人少'], inRange: {{ color: ['#FCE4EC', '#F48FB1', '#C2185B', '#880E4F'] }}, calculable: true, outOfRange: {{ color: ['rgba(255,255,255,0.2)'] }} }},
                    series: [{{ type: 'map', map: 'world', roam: true, zoom: 1.2, label: {{ show: false }}, itemStyle: {{ areaColor: 'rgba(255,255,255,0.5)', borderColor: '#FFFFFF' }}, emphasis: {{ label: {{ show: true, color: '#000', fontWeight: 'bold' }}, itemStyle: {{ areaColor: '#d9bde3' }} }}, data: data.map }}]
                }}); 
                charts.push(cMap);

                renderBubbleChart();

                const cPie = echarts.init(document.getElementById('chart-pie'));
                const colorEast = {{ type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{{ offset: 0, color: '#f5ebe9' }}, {{ offset: 1, color: '#ffd1d6' }}] }};
                const colorWestChild = {{ type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{{ offset: 0, color: '#F5f3f2' }}, {{ offset: 1, color: '#f2c7d2' }}] }};
                const colorWestParent = {{ type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{{ offset: 0, color: '#E1BEE7' }}, {{ offset: 1, color: '#F3E5F5' }}] }};
                const colorOther = {{ type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [ {{ offset: 0, color: '#faf9f6' }}, {{ offset: 1, color: '#d7e7d7' }} ] }};
                const colorEastChild = {{ type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{{ offset: 0, color: '#F5f3f2' }}, {{ offset: 1, color: '#f2c7d2' }}] }}; 

                function colorizeData(sourceData) {{ return sourceData.map(item => {{ let newItem = {{ ...item }}; if(item.name === '东方') {{ newItem.itemStyle = {{ color: colorEast, borderWidth: 2, borderColor: '#fff' }}; if(newItem.children) {{ newItem.children = newItem.children.map(c => ({{ ...c, itemStyle: {{ color: c.name==='其他'?colorOther:colorEastChild, borderWidth:1, borderColor:'#fff' }}, emphasis: {{ itemStyle: {{ color: '#FFF8E1', shadowBlur: 15, shadowColor: '#FFCDD2' }} }} }})); }} }} else if(item.name === '西方') {{ newItem.itemStyle = {{ color: colorWestParent, borderWidth: 2, borderColor: '#fff' }}; if(newItem.children) {{ newItem.children = newItem.children.map(c => ({{ ...c, itemStyle: {{ color: c.name==='其他'?colorOther:colorWestChild, borderWidth:1, borderColor:'#fff' }}, emphasis: {{ itemStyle: {{ color: '#FFF8E1', shadowBlur: 15, shadowColor: '#ba91b2' }} }} }})); }} }} return newItem; }}); }}

                const mainData = colorizeData(data.sunburst);
                let isDrilledDown = false;
                const getOption = (chartData) => ({{ tooltip: {{ trigger: 'item', enterable: true, confine: true, position: function (point, params, dom, rect, size) {{ return [point[0] + 20, point[1] + 20]; }}, backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#e0edfd', textStyle: {{ color: '#555' }}, formatter: function(params) {{ const name = params.name; let rankHtml = ''; if (rankMap[name]) {{ rankHtml = `<div style="margin-top:4px; font-size:12px; color:#888;">🏆 排名: No.${{rankMap[name]}}</div>`; }} return `<div style="text-align:center; font-weight:bold; color:${{params.color}}">${{name}}</div>` + `<div style="font-size:12px;">上榜: ${{params.value}} 人次</div>` + rankHtml; }} }}, series: [{{ type: 'sunburst', data: chartData, radius: ['20%', '90%'], sort: undefined, nodeClick: false, emphasis: {{ focus: 'none', scale: true, scaleSize: 10, itemStyle: {{ borderColor: '#fff', borderWidth: 2 }} }}, levels: [ {{}}, {{ r0: '20%', r: '45%', label: {{ rotate: 0, fontSize: 14, fontWeight: 'bold', color: '#68869A', formatter: function(params) {{ return params.name + '\\n' + params.value; }} }}, itemStyle: {{ borderRadius: 8, borderColor: '#fff', borderWidth: 2 }} }}, {{ r0: '46%', r: '90%', label: {{ align: 'right', fontSize: 11, fontWeight: 600, color: '#666', formatter: function(params) {{ return params.name + ' ' + params.value; }} }}, itemStyle: {{ borderRadius: 5, borderColor: '#fff', borderWidth: 1 }} }} ] }}] }});
                cPie.setOption(getOption(mainData));

                cPie.on('click', function(params) {{ 
                    if (params.name.includes('返回')) {{ cPie.setOption(getOption(mainData)); isDrilledDown = false; return; }} 
                    const allowedParents = ['东方', '西方']; 
                    const isOther = params.name.includes('其他'); 
                    if (!allowedParents.includes(params.name) && !isOther) {{ return; }} 
                    let targetChildren = []; 
                    let totalValue = 0; 
                    if (params.data.key && data.sunburst_details[params.data.key]) {{ targetChildren = data.sunburst_details[params.data.key]; totalValue = targetChildren.reduce((sum, item) => sum + item.value, 0); }} 
                    else if (params.data.children) {{ targetChildren = params.data.children; totalValue = params.value; }} 
                    if (targetChildren.length > 0) {{ 
                        const detailData = [{{ 
                            name: '返回\\nBack', 
                            value: totalValue, 
                            itemStyle: {{ color: '#dcf4f5' }}, 
                            label: {{ color: '#68869A', fontWeight: 'bold', fontSize: 14 }}, 
                            children: targetChildren.map(d => ({{ ...d, itemStyle: {{ color: d.name.includes('其他') ? colorOther : (params.name.includes('东方') ? colorEastChild : colorWestChild), borderWidth: 1, borderColor: '#fff' }}, label: {{ formatter: function(p) {{ return p.name + ' ' + p.value; }} }}, emphasis: {{ itemStyle: {{ color: '#FFF8E1', shadowBlur: 15, shadowColor: params.name.includes('东方') ? '#FFCDD2' : '#B2EBF2' }} }} }})) 
                        }}]; 
                        cPie.setOption({{ series: [{{ data: detailData, radius: [0, '90%'], levels: [ {{}}, {{ r0: '0%', r: '25%', label: {{ rotate: 0 }} }}, {{ r0: '25%', r: '100%', label: {{ align: 'right', color: '#555', formatter: function(p) {{ return p.name + ' ' + p.value; }} }} }} ] }}] }}); 
                        isDrilledDown = true; 
                    }} 
                }});
                charts.push(cPie);

                const cBar = echarts.init(document.getElementById('chart-bar'));
                const flowerData = data.bar_details.map(item => ({{ value: item.visual_val, name: item.name, detail: item }}));
                const petalColors = [
                    {{c1: '#de82a7', c2: '#f0c0d0'}}, {{c1: '#e18bad', c2: '#f2c5d6'}}, {{c1: '#e494b3', c2: '#f3cadb'}}, {{c1: '#e79db9', c2: '#f5cfe0'}}, {{c1: '#eaa7bf', c2: '#f6d4e5'}}, 
                    {{c1: '#edb0c5', c2: '#f7d9ea'}}, {{c1: '#f0b9cb', c2: '#f8deef'}}, {{c1: '#f3c2d1', c2: '#f9e3f4'}}, {{c1: '#f6cbd7', c2: '#fae8f9'}}, {{c1: '#f9d3e3', c2: '#fbf0fa'}}
                ];
                cBar.setOption({{
                    tooltip: {{
                        trigger: 'item', backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#D7CCC8', borderWidth: 1, padding: 15, textStyle: {{ color: '#5D4037', fontFamily: 'Plus Jakarta Sans' }}, extraCssText: 'box-shadow: 0 10px 30px rgba(215, 204, 200, 0.5); border-radius: 16px;',
                        formatter: function(params) {{ if (params.seriesIndex === 1) return ''; const d = params.data.detail; return `<div style="display:flex; align-items:center; margin-bottom:10px;"><div style="width:28px; height:28px; line-height:28px; text-align:center; border-radius:50%; background:#de82a7; color:#fff; font-weight:900; font-size:14px; margin-right:10px;">${{d.rank_sort}}</div><div style="font-size:18px; font-weight:900; color:#880E4F;">${{params.name}}</div></div>` + `<div style="font-size:13px; color:#795548; line-height:1.8;"><div>🌍 <b>${{d.country}}</b></div><div>🌸 累计上榜: <b style="color:#D81B60">${{d.value}}</b> 次</div><div>🏆 最高排名: <b style="color:#D81B60">No.${{d.best}}</b></div><div>📊 平均排名: <b>${{d.avg}}</b></div></div>`; }}
                    }},
                    series: [
                        {{ name: 'Petals', type: 'pie', radius: ['15%', '100%'], center: ['50%', '50%'], roseType: 'area', startAngle: 0, itemStyle: {{ borderRadius: [20, 100, 100, 20], borderColor: '#FFFFFF', borderWidth: 3, color: function(params) {{ const idx = params.dataIndex; const palette = petalColors[idx % petalColors.length]; return {{ type: 'radial', x: 0.5, y: 0.5, r: 1, colorStops: [{{ offset: 0, color: palette.c2 }}, {{ offset: 0.8, color: palette.c1 }}, {{ offset: 1, color: palette.c1 }}] }}; }}, shadowBlur: 15, shadowOffsetX: 2, shadowOffsetY: 5, shadowColor: 'rgba(180, 160, 150, 0.3)' }}, emphasis: {{ scale: true, scaleSize: 20, itemStyle: {{ shadowBlur: 40, shadowOffsetX: 10, shadowOffsetY: 10, shadowColor: 'rgba(140, 100, 100, 0.4)', borderColor: '#FFFDE7', borderWidth: 2 }}, label: {{ show: true, fontSize: 14, fontWeight: '900', color: '#b05c7c' }} }}, label: {{ show: true, position: 'inside', rotate: 'tangential', align: 'center', verticalAlign: 'middle', color: '#507047', fontWeight: 'bold', fontSize: 12, textShadowBlur: 2, textShadowColor: 'rgba(0,0,0,0.15)', formatter: function(params) {{ return params.name.length > 7 ? params.name.substring(0, 6) + '..' : params.name; }} }}, data: flowerData }},
                        {{ name: 'Pistil', type: 'pie', radius: ['0%', '15%'], center: ['50%', '50%'], itemStyle: {{ color: {{ type: 'radial', x: 0.4, y: 0.3, r: 1, colorStops: [{{ offset: 0, color: '#fffdf0' }}, {{ offset: 0.5, color: '#fbedbe' }}, {{ offset: 1, color: '#fdd835' }}] }}, shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.1)' }}, label: {{ show: false }}, tooltip: {{ show: false }}, silent: true, data: [{{ value: 1 }}] }}
                    ]
                }});
                charts.push(cBar);

                // =========================================================
                // [修复] 霸榜人物(花瓣图) 旋转逻辑 - 这里重新加回来了
                // =========================================================
                let isDraggingFlower = false; let lastFlowerAngle = 0; let currentFlowerStartAngle = 0;
                const flowerChartDom = document.getElementById('chart-bar');
                if(flowerChartDom) {{
                    flowerChartDom.addEventListener('mousedown', (e) => {{ 
                        isDraggingFlower = true; 
                        flowerChartDom.style.cursor = 'grabbing'; 
                        const rect = flowerChartDom.getBoundingClientRect(); 
                        const cx = rect.width / 2; 
                        const cy = rect.height / 2; 
                        lastFlowerAngle = Math.atan2(e.clientY - rect.top - cy, e.clientX - rect.left - cx) * 180 / Math.PI; 
                    }});
                    window.addEventListener('mousemove', (e) => {{ 
                        if (!isDraggingFlower) return; 
                        const rect = flowerChartDom.getBoundingClientRect(); 
                        const cx = rect.width / 2; 
                        const cy = rect.height / 2; 
                        const newAngle = Math.atan2(e.clientY - rect.top - cy, e.clientX - rect.left - cx) * 180 / Math.PI; 
                        const delta = newAngle - lastFlowerAngle; 
                        currentFlowerStartAngle -= delta; 
                        lastFlowerAngle = newAngle; 
                        // 重新获取实例并更新
                        const chartInstance = echarts.getInstanceByDom(flowerChartDom);
                        if(chartInstance) {{
                            chartInstance.setOption({{ series: [ {{ startAngle: currentFlowerStartAngle }}, {{ startAngle: currentFlowerStartAngle }} ], animation: false }}); 
                        }}
                    }});
                    window.addEventListener('mouseup', () => {{ 
                        if (isDraggingFlower) {{ 
                            isDraggingFlower = false; 
                            flowerChartDom.style.cursor = 'grab'; 
                            const chartInstance = echarts.getInstanceByDom(flowerChartDom);
                            if(chartInstance) chartInstance.setOption({{ animation: true }}); 
                        }} 
                    }});
                }}

                const cLine = echarts.init(document.getElementById('chart-line'));
                cLine.setOption({{
                    grid: {{ left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true, show: false }},
                    tooltip: {{ trigger: 'axis', backgroundColor: 'rgba(255, 255, 255, 0.85)', borderColor: '#fff', borderWidth: 1, padding: [12, 16], textStyle: {{ color: '#666', fontFamily: 'Plus Jakarta Sans', fontSize: 13 }}, extraCssText: 'backdrop-filter: blur(8px); box-shadow: 0 8px 25px rgba(220, 200, 220, 0.4); border-radius: 12px;', formatter: function(params) {{ var res = '<div style="margin-bottom:8px; font-weight:900; color:#5D4037;">📅 ' + params[0].axisValue + '</div>'; for (var i = 0; i < params.length; i++) {{ var dotColor = (params[i].seriesName === '东方') ? '#FF9A9E' : '#CE93D8'; res += '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; min-width:140px;">'; res += '<div style="font-size:12px; color:#888;"><span style="display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;background:' + dotColor + '"></span>' + params[i].seriesName + '</div>'; res += '<div style="font-weight:800; color:' + dotColor + '; font-size:14px;">' + params[i].value + '</div>'; res += '</div>'; }} return res; }} }},
                    legend: {{ top: '0%', right: '5%', icon: 'circle', itemGap: 25, textStyle: {{ color: '#9E9E9E', fontWeight: 'bold', fontFamily: 'Plus Jakarta Sans' }} }},
                    xAxis: {{ type: 'category', data: data.line.years, boundaryGap: false, axisLine: {{ show: false }}, axisTick: {{ show: false }}, axisLabel: {{ color: '#B0BEC5', fontWeight: 'bold', fontFamily: 'Plus Jakarta Sans', margin: 15 }} }},
                    yAxis: {{ type: 'value', splitLine: {{ show: true, lineStyle: {{ type: 'dashed', color: 'rgba(230, 230, 230, 0.8)' }} }}, axisLabel: {{ color: '#CFD8DC', fontFamily: 'Plus Jakarta Sans' }} }},
                    series: [
                        {{ name: '东方', type: 'line', smooth: 0.5, showSymbol: false, itemStyle: {{ color: '#FF9A9E', borderColor: '#fff', borderWidth: 2 }}, lineStyle: {{ width: 4, shadowColor: 'rgba(255, 154, 158, 0.4)', shadowBlur: 15, shadowOffsetY: 8, color: {{ type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{{ offset: 0, color: '#FF9A9E' }}, {{ offset: 1, color: '#FECFEF' }}] }} }}, areaStyle: {{ color: {{ type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{{ offset: 0, color: 'rgba(255, 154, 158, 0.4)' }}, {{ offset: 1, color: 'rgba(255, 255, 255, 0)' }}] }} }}, data: data.line.east, animationDuration: 2000, animationEasing: 'cubicOut' }},
                        {{ name: '西方', type: 'line', smooth: 0.5, showSymbol: false, itemStyle: {{ color: '#CE93D8', borderColor: '#fff', borderWidth: 2 }}, lineStyle: {{ width: 4, shadowColor: 'rgba(206, 147, 216, 0.4)', shadowBlur: 15, shadowOffsetY: 8, color: {{ type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{{ offset: 0, color: '#CE93D8' }}, {{ offset: 1, color: '#F3E5F5' }}] }} }}, areaStyle: {{ color: {{ type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{{ offset: 0, color: 'rgba(206, 147, 216, 0.4)' }}, {{ offset: 1, color: 'rgba(255, 255, 255, 0)' }}] }} }}, data: data.line.west, animationDuration: 2000, animationEasing: 'cubicOut', animationDelay: 200 }}
                    ]
                }});
                charts.push(cLine);
            }} catch(e) {{ console.error("Charts Init Error:", e); }}

            function resizeCharts() {{ charts.forEach(c => {{ try {{ c.resize(); }} catch(e) {{}} }}); }}
            window.onresize = resizeCharts;

            // =========================================================
            //  历年图鉴 (Timeline) 核心逻辑 
            // =========================================================

            const tlData = data.timeline_data || {{}};
            const tlYears = data.timeline_years || [];
            let currentTimelineIndex = 0; 

            // 配置数组：使用双花括号防止 Python 解析报错
            const layoutPositions = [
                {{ l: 50, t: 50, z: 30, scale: 1.4 }}, 
                {{ l: 35, t: 30, z: 20, scale: 1.4 }}, 
                {{ l: 65, t: 30, z: 20, scale: 1.4 }}, 
                {{ l: 35, t: 70, z: 20, scale: 1.4 }}, 
                {{ l: 65, t: 70, z: 20, scale: 1.4 }}, 
                {{ l: 50, t: 15, z: 10, scale: 1.2 }}, 
                {{ l: 50, t: 85, z: 10, scale: 1.2 }}, 
                {{ l: 20, t: 65, z: 10, scale: 1.2 }}, 
                {{ l: 20, t: 30, z: 10, scale: 1.2 }}, 
                {{ l: 79, t: 50, z: 5,  scale: 1.2 }}  
            ];

            const tlStage = document.getElementById('timeline-stage');
            const yearLabel = document.getElementById('year-label');
            const yearDropdown = document.getElementById('year-select-dropdown');

            if(tlYears.length > 0) {{
                tlYears.forEach((y, i) => {{
                    const op = document.createElement('option');
                    op.value = i;
                    op.text = y + "年";
                    yearDropdown.appendChild(op);
                }});
                yearDropdown.onchange = (e) => {{
                    const targetIdx = parseInt(e.target.value);
                    switchYear(targetIdx);
                }};

                tlYears.forEach((year, yIdx) => {{
                    const items = tlData[year] || [];
                    const layer = document.createElement('div');
                    layer.className = 'year-layer';
                    layer.id = 'year-layer-' + yIdx;

                    items.forEach((item, rIdx) => {{
                        if(rIdx >= 10) return;
                        const pos = layoutPositions[rIdx] || {{ l: 50, t: 50, z: 1, scale: 1 }};
                        const card = document.createElement('div');
                        card.className = 'rank-card';
                        card.style.left = `calc(${{pos.l}}% - 67px)`;
                        card.style.top = `calc(${{pos.t}}% - 90px)`;
                        card.style.zIndex = pos.z;
                        card.style.transform = `scale(${{pos.scale}})`;
                        card.dataset.scale = pos.scale; 

                        card.innerHTML = `
                            <div class="card-img-box"><img src="${{item.img}}" loading="lazy"></div>
                            <div class="rank-badge ${{rIdx < 3 ? 'top3' : ''}}">${{item.rank}}</div>
                            <div class="card-info">
                                <div class="card-name" title="${{item.name}}">${{item.name}}</div>
                                <div class="card-sub"><span class="card-country-tag">${{item.country}}</span><span>${{year}}</span></div>
                            </div>
                        `;
                        card.onmouseenter = function() {{ 
                            this.style.zIndex = 100; 
                            const baseScale = parseFloat(this.dataset.scale);
                            this.style.transform = `scale(${{baseScale * 1.1}})`;
                        }}
                        card.onmouseleave = function() {{ 
                            this.style.zIndex = pos.z; 
                            this.style.transform = `scale(${{this.dataset.scale}})`; 
                        }}
                        layer.appendChild(card);
                    }});
                    tlStage.appendChild(layer);
                }});

                switchYear(0, false);
            }}

            function switchYear(newIndex, animate = true) {{
                const oldIndex = currentTimelineIndex;
                currentTimelineIndex = newIndex;
                if(currentTimelineIndex >= tlYears.length) currentTimelineIndex = 0;
                if(currentTimelineIndex < 0) currentTimelineIndex = tlYears.length - 1;
                const actualIdx = currentTimelineIndex;
                const yearText = tlYears[actualIdx];
                yearLabel.innerText = yearText;
                yearDropdown.value = actualIdx;
                const layers = document.querySelectorAll('.year-layer');
                layers.forEach((layer, idx) => {{
                    layer.className = 'year-layer'; 
                    if(idx === actualIdx) {{ layer.classList.add('active-year'); }} 
                    else if (animate) {{ if (idx < actualIdx) layer.classList.add('prev-year'); else layer.classList.add('next-year'); }}
                }});
            }}

            const tlBox = document.getElementById('timeline-chart-box');
            let scrollCoolDown = false;
            tlBox.addEventListener('wheel', (e) => {{
                e.stopPropagation(); e.preventDefault();
                if(scrollCoolDown) return; scrollCoolDown = true;
                if (e.deltaY > 0) switchYear(currentTimelineIndex + 1); else switchYear(currentTimelineIndex - 1);
                setTimeout(() => {{ scrollCoolDown = false; }}, 800);
            }}, {{ passive: false }});

            // =========================================================
            //  冠军巡礼 (Champion Gallery) 初始化 - 弧形舞台版
            // =========================================================
            const chContainer = document.getElementById('champion-wrapper');
            if(data.champions) {{
                data.champions.forEach(c => {{
                    // 解析文字：拆分年份和名字
                    // 假设格式为 "2016年冠军：Jourdan Dunn (英国)"
                    let parts = c.text.split('：');
                    let yearStr = (c.year || 'YEAR') + " YEAR";
                    let nameStr = parts[1] || c.text;

                    chContainer.innerHTML += `
                    <div class="swiper-slide champ-slide">
                        <img class="champ-img" src="${{c.img}}">
                        <div class="champ-overlay">
                            <div class="champ-year">${{yearStr}}</div>
                            <div class="champ-text">${{nameStr}}</div>
                        </div>
                    </div>`;
                }});
            }}

            // Swiper 配置：高级弧形舞台效果
            new Swiper(".champSwiper", {{
                effect: "coverflow",   // 关键：使用封面流效果实现 3D
                grabCursor: true,
                centeredSlides: true,  // 关键：居中显示，形成对称弧形
                slidesPerView: "auto", // 自动适应宽度，配合 coverflow 使用
                loop: true,            // 循环播放
                speed: 600,
                // 核心参数：调整这里可以改变“弧度”和“距离”
                coverflowEffect: {{
                    rotate: 30,        // 侧面旋转角度 (制造弧形感)
                    stretch: 0,        // 图片间距拉伸
                    depth: 150,        // 深度 (制造前后层次)
                    modifier: 1,
                    slideShadows: false // 关闭自带阴影，使用我们 CSS 写的更美观
                }},
            }});

            let startY = 0; let isDragging = false; const zone = document.getElementById('interaction-zone');
            zone.addEventListener('mousedown', (e) => {{ isDragging = true; startY = e.clientY; zone.style.cursor = 'grabbing'; }});
            window.addEventListener('mouseup', (e) => {{ if (!isDragging) return; isDragging = false; zone.style.cursor = 'grab'; if (Math.abs(e.clientY - startY) > 50) {{ e.clientY - startY > 0 ? triggerPrev() : triggerNext(); }} }});
            zone.addEventListener('wheel', (e) => {{ e.preventDefault(); e.deltaY > 0 ? triggerNext() : triggerPrev(); }});
            function triggerNext() {{ globalIndex++; updateRotation(); }}
            function triggerPrev() {{ globalIndex--; updateRotation(); }}

            updateRotation();
        </script>
    </body>
    </html>
    """